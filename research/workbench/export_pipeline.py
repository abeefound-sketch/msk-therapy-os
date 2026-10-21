"""Export pipeline emitting versioned canonical acupuncture datasets and reports."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .adapters.base import BaseAdapter, NormalizedMeridian, NormalizedPoint
from .coordinate_registry import CoordinateRegistry
from .geometry_validator import GeometryValidator


class ExportPipeline:
    """Pipeline consolidating research discoveries into canonical datasets."""

    def __init__(self, out_dir: Path | str | None = None):
        if out_dir is None:
            self.out_dir = Path(__file__).resolve().parents[1] / "artifacts"
        else:
            self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def export_canonical_dataset(
        self,
        jicio_adapter: BaseAdapter,
        meridian_studio_adapter: BaseAdapter,
        output_filename: str = "canonical_acupuncture_v2.json",
    ) -> Path:
        """Merge high-precision surface-baked coordinates from JICio with rich clinical text from Meridian Studio."""
        jicio_points = jicio_adapter.extract_points()
        jicio_meridians = jicio_adapter.extract_meridians()
        studio_points = meridian_studio_adapter.extract_points()

        validator = GeometryValidator()

        canonical_points: Dict[str, Any] = {}
        # Merge by standard international code (e.g. LU1, GV14, GB21)
        for code, j_pt in jicio_points.items():
            s_pt = studio_points.get(code)
            lm = CoordinateRegistry.get_landmark(code)
            val_res = validator.validate_point(j_pt, lm)

            # Combine clinical annotations
            name_zh = j_pt.name_zh or (s_pt.name_zh if s_pt else code)
            name_en = j_pt.name_en or (s_pt.name_en if s_pt else code)
            pinyin = j_pt.pinyin or ""
            indications = (s_pt.indications if s_pt else []) or j_pt.indications
            location_guide = (s_pt.location_desc if s_pt else "") or j_pt.location_desc

            extra_attrs = {}
            if s_pt and s_pt.extra:
                extra_attrs["traditional_meridian"] = s_pt.extra.get("traditional_meridian")
                extra_attrs["contraindications"] = s_pt.extra.get("contraindications")
                extra_attrs["contraindication_details"] = s_pt.extra.get("contraindication_details")
                extra_attrs["attributes"] = s_pt.extra.get("attributes")
            if j_pt.extra:
                extra_attrs["mesh_id"] = j_pt.extra.get("mesh_id", "FJ2810")
                extra_attrs["face_index"] = j_pt.extra.get("face_index")

            landmark_meta = None
            if lm:
                landmark_meta = {
                    "skeletal_anchor": lm.skeletal_anchor,
                    "description": lm.description,
                    "canonical_coords": lm.canonical_coords,
                    "distance_to_anchor_mm": round(
                        CoordinateRegistry.euclidean_distance(j_pt.canonical_position, lm.canonical_coords), 2
                    ),
                }

            canonical_points[code] = {
                "code": code,
                "name_zh": name_zh,
                "name_en": name_en,
                "pinyin": pinyin,
                "meridian_code": j_pt.meridian_code,
                "region": j_pt.region,
                "position": [round(c, 5) for c in j_pt.canonical_position],
                "normal": [round(n, 5) for n in (j_pt.normal or [0.0, 0.0, 1.0])],
                "surface_offset_mm": j_pt.surface_distance_mm,
                "evidence_tag": val_res.evidence_tag,
                "indications": indications,
                "location_description": location_guide,
                "landmark_anchor": landmark_meta,
                "provenance": {
                    "primary_mesh": "BodyParts3D (FJ2810)",
                    "coordinate_origin": "ground (Y=0), +X right, +Y superior, +Z anterior",
                    "upstream_source": j_pt.source,
                },
                "extra": extra_attrs,
            }

        # Format continuous surface meridians
        canonical_meridians: Dict[str, Any] = {}
        for m_code, mer in jicio_meridians.items():
            pts_in_meridian = [c for c, p in canonical_points.items() if p["meridian_code"] == m_code]
            pts_in_meridian.sort()

            # Clean and round path coordinates
            clean_paths = []
            for path in mer.paths:
                clean_path = [[round(coord, 5) for coord in pt] for pt in path]
                clean_paths.append(clean_path)

            canonical_meridians[m_code] = {
                "code": m_code,
                "name_zh": mer.name_zh,
                "name_en": mer.name_en,
                "color": mer.color,
                "point_codes": pts_in_meridian,
                "paths": clean_paths,
                "vertex_count": sum(len(p) for p in clean_paths),
                "surface_conforming": True,
                "source": mer.source,
            }

        dataset = {
            "version": "2.0.0",
            "format": "canonical-acupuncture-mesh",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target_model": "BodyParts3D Male / FJ2810 Skin Mesh",
            "units": "meters",
            "coordinate_system": "Right-handed (+X right, +Y up, +Z anterior)",
            "origin": "Ground plane directly below center of gravity (Y=0)",
            "point_count": len(canonical_points),
            "meridian_count": len(canonical_meridians),
            "points": canonical_points,
            "meridians": canonical_meridians,
            "disclaimer": "This dataset provides educational and 3D visual approximations. Not validated for autonomous surgical or invasive clinical guidance.",
        }

        out_path = self.out_dir / output_filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        return out_path
