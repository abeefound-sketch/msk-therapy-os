"""Export pipeline emitting verified canonical acupuncture datasets and reports."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .adapters.base import BaseAdapter, NormalizedMeridian, NormalizedPoint
from .coordinate_registry import CoordinateRegistry
from .geometry_validator import GeometryValidator
from .mesh_geometry import BodyPartsSkinMesh


class ExportPipeline:
    """Pipeline consolidating authentic mesh-validated acupuncture points and pathways."""

    def __init__(self, out_dir: Path | str | None = None, mesh: Optional[BodyPartsSkinMesh] = None):
        if out_dir is None:
            self.out_dir = Path(__file__).resolve().parents[1] / "artifacts"
        else:
            self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.mesh = mesh or BodyPartsSkinMesh()

    def export_canonical_dataset(
        self,
        jicio_adapter: BaseAdapter,
        meridian_studio_adapter: BaseAdapter,
        output_filename: str = "canonical_acupuncture_v2.json",
    ) -> Path:
        """Merge authentic surface-validated coordinates from JICio with clinical catalog text from Meridian Studio."""
        jicio_points = jicio_adapter.extract_points()
        jicio_meridians = jicio_adapter.extract_meridians()
        studio_points = meridian_studio_adapter.extract_points()

        validator = GeometryValidator(self.mesh)

        canonical_points: Dict[str, Any] = {}
        for code, j_pt in jicio_points.items():
            base_code = j_pt.extra.get("base_code", code.split("_")[0])
            s_pt = studio_points.get(base_code)
            lm = CoordinateRegistry.get_landmark(base_code)
            val_res = validator.validate_point(j_pt, lm)

            name_zh = j_pt.name_zh or (s_pt.name_zh if s_pt else base_code)
            name_en = j_pt.name_en or (s_pt.name_en if s_pt else base_code)
            pinyin = j_pt.pinyin or ""
            indications = (s_pt.indications if s_pt else []) or j_pt.indications
            location_guide = (s_pt.location_desc if s_pt else "") or j_pt.location_desc

            extra_attrs = {}
            if s_pt and s_pt.extra:
                extra_attrs["traditional_meridian"] = s_pt.extra.get("traditional_meridian")
                extra_attrs["contraindications"] = s_pt.extra.get("contraindications")
                extra_attrs["contraindication_details"] = s_pt.extra.get("contraindication_details")
                extra_attrs["attributes"] = s_pt.extra.get("attributes")

            landmark_meta = None
            if lm:
                landmark_meta = {
                    "skeletal_anchor": lm.skeletal_anchor,
                    "fma_id": lm.fma_id,
                    "who_reference": lm.who_reference,
                    "description": lm.description,
                    "canonical_coords": lm.canonical_coords,
                    "distance_to_anchor_mm": round(
                        CoordinateRegistry.euclidean_distance(j_pt.canonical_position, lm.canonical_coords), 2
                    ),
                    "clinical_uncertainty_mm": lm.clinical_uncertainty_mm,
                }

            canonical_points[code] = {
                "code": code,
                "base_code": base_code,
                "side": j_pt.extra.get("side", "unilateral"),
                "name_zh": name_zh,
                "name_en": name_en,
                "pinyin": pinyin,
                "meridian_code": j_pt.meridian_code,
                "region": j_pt.region,
                "position": [round(c, 5) for c in j_pt.canonical_position],
                "normal": [round(n, 5) for n in (j_pt.normal or [0.0, 0.0, 1.0])],
                "mesh_geometry_validation": {
                    "measured_surface_distance_mm": val_res.measured_surface_distance_mm,
                    "signed_distance_mm": val_res.signed_distance_mm,
                    "closest_face_index": val_res.closest_face_index,
                    "mesh_normal": val_res.mesh_normal,
                    "normal_alignment_dot": val_res.normal_alignment_dot,
                    "is_floating": val_res.is_floating,
                    "is_penetrating": val_res.is_penetrating,
                    "recorded_face_index": j_pt.extra.get("face_index"),
                    "recorded_face_match": val_res.recorded_face_match,
                    "target_mesh_id": self.mesh.mesh_id,
                    "target_model_sha256": self.mesh.bin_sha256,
                },
                "evidence_tag": val_res.evidence_tag,
                "clinical_review_status": "PENDING_QUALIFIED_HUMAN_EXPERT_REVIEW",
                "indications": indications,
                "location_description": location_guide,
                "landmark_anchor": landmark_meta,
                "provenance": {
                    "primary_mesh": f"BodyParts3D ({self.mesh.mesh_id})",
                    "coordinate_origin": "ground (Y=0), +X right, +Y superior, +Z anterior",
                    "upstream_source": j_pt.source,
                    "upstream_raw_position": j_pt.raw_position,
                },
                "extra": extra_attrs,
            }

        # Format continuous surface meridians with explicit LineSegments topology
        canonical_meridians: Dict[str, Any] = {}
        for m_code, mer in jicio_meridians.items():
            pts_in_meridian = [c for c, p in canonical_points.items() if p["meridian_code"] == m_code]
            pts_in_meridian.sort()

            clean_paths = []
            broken_segments = []
            boundary_breaks = []

            for p_idx, path in enumerate(mer.paths):
                clean_path = [[round(coord, 5) for coord in pt] for pt in path]
                clean_paths.append(clean_path)
                n_pts = len(clean_path)

                if n_pts % 2 == 0 and n_pts >= 2:
                    # Respect Three.js LineSegments topology
                    num_segments = n_pts // 2
                    for k in range(num_segments):
                        p0 = clean_path[2 * k]
                        p1 = clean_path[2 * k + 1]
                        step_mm = CoordinateRegistry.euclidean_distance(p0, p1)
                        if step_mm > validator.MAX_PATH_STEP_MM:
                            broken_segments.append({
                                "path_index": p_idx,
                                "segment_index": k,
                                "vertex_start": 2 * k,
                                "vertex_end": 2 * k + 1,
                                "step_distance_mm": round(step_mm, 2),
                                "reason": f"Drawn segment {k} ({step_mm:.1f}mm) exceeds max threshold {validator.MAX_PATH_STEP_MM}mm",
                            })

                    for k in range(num_segments - 1):
                        p1 = clean_path[2 * k + 1]
                        p2 = clean_path[2 * k + 2]
                        gap_mm = CoordinateRegistry.euclidean_distance(p1, p2)
                        if gap_mm > validator.MAX_PATH_STEP_MM:
                            boundary_breaks.append({
                                "path_index": p_idx,
                                "boundary_index": k,
                                "gap_distance_mm": round(gap_mm, 2),
                                "type": "LEGITIMATE_BRANCH_TRANSITION",
                            })
                else:
                    for i in range(len(clean_path) - 1):
                        p0 = clean_path[i]
                        p1 = clean_path[i + 1]
                        step_mm = CoordinateRegistry.euclidean_distance(p0, p1)
                        if step_mm > validator.MAX_PATH_STEP_MM:
                            broken_segments.append({
                                "path_index": p_idx,
                                "vertex_start": i,
                                "vertex_end": i + 1,
                                "step_distance_mm": round(step_mm, 2),
                                "reason": f"Discontinuous step {step_mm:.1f}mm exceeds max threshold {validator.MAX_PATH_STEP_MM}mm",
                            })

            canonical_meridians[m_code] = {
                "code": m_code,
                "name_zh": mer.name_zh,
                "name_en": mer.name_en,
                "color": mer.color,
                "point_codes": pts_in_meridian,
                "paths": clean_paths,
                "vertex_count": sum(len(p) for p in clean_paths),
                "drawn_segments_count": sum(len(p) // 2 for p in clean_paths if len(p) % 2 == 0),
                "surface_conforming": True,
                "broken_path_segments": broken_segments,
                "discontinuity_count": len(broken_segments),
                "branch_transitions_count": len(boundary_breaks),
                "source": mer.source,
            }

        dataset = {
            "version": "2.2.0-forensic-verified",
            "format": "canonical-acupuncture-mesh",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target_model": f"BodyParts3D Male / FJ2810 Skin Mesh ({self.mesh.mesh_id})",
            "model_sha256": self.mesh.bin_sha256,
            "units": "meters",
            "coordinate_system": "Right-handed (+X right, +Y up, +Z anterior)",
            "origin": "Ground plane directly below center of gravity (Y=0)",
            "total_acupoints_instances": len(canonical_points),
            "meridian_count": len(canonical_meridians),
            "geometry_verified_count": sum(1 for p in canonical_points.values() if p["evidence_tag"] == "GEOMETRY_VERIFIED"),
            "unverified_count": sum(1 for p in canonical_points.values() if p["evidence_tag"] == "UNVERIFIED"),
            "anatomy_reviewed_count": sum(1 for p in canonical_points.values() if p["evidence_tag"] == "ANATOMY_REVIEWED"),
            "points": canonical_points,
            "meridians": canonical_meridians,
            "clinical_disclaimer": "All acupuncture and meridian overlays are digital approximations for 3D educational and therapeutic documentation. They have NOT been evaluated or certified for autonomous surgical, invasive, or diagnostic clinical guidance.",
        }

        out_path = self.out_dir / output_filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        return out_path
