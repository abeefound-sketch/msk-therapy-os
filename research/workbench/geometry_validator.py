"""Authentic Geometry Validator measuring point-to-triangle distance against BodyParts3D mesh."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .adapters.base import BaseAdapter, NormalizedMeridian, NormalizedPoint
from .coordinate_registry import CoordinateRegistry
from .mesh_geometry import BodyPartsSkinMesh


@dataclass
class PointValidationResult:
    code: str
    name_zh: str
    source: str
    canonical_coords: List[float]
    normal: Optional[List[float]]
    measured_surface_distance_mm: float
    signed_distance_mm: float
    closest_face_index: int
    mesh_normal: List[float]
    normal_alignment_dot: Optional[float]
    is_floating: bool  # > 5.0 mm
    is_penetrating: bool  # < -2.0 mm
    is_normal_inverted: bool  # dot < 0.0
    recorded_face_match: Optional[bool]
    discontinuity_warning: Optional[str]
    evidence_tag: str  # GEOMETRY_VERIFIED | ANATOMY_REVIEWED | UNVERIFIED
    details: str


@dataclass
class SourceValidationSummary:
    source_name: str
    total_points: int
    geometry_verified_count: int
    anatomy_reviewed_count: int
    unverified_count: int
    floating_count: int
    penetrating_count: int
    mean_measured_distance_mm: float
    max_measured_distance_mm: float
    point_results: List[PointValidationResult]
    path_discontinuities: List[Dict[str, Any]] = field(default_factory=list)


class GeometryValidator:
    """Validator performing real mathematical point-to-triangle distance queries against FJ2810 mesh."""

    MAX_SURFACE_TOLERANCE_MM = 5.0
    MIN_SURFACE_TOLERANCE_MM = -2.0
    MAX_PATH_STEP_MM = 25.0

    def __init__(self, mesh: Optional[BodyPartsSkinMesh] = None):
        if mesh is None:
            try:
                self.mesh = BodyPartsSkinMesh()
            except Exception:
                self.mesh = None
        else:
            self.mesh = mesh

    def validate_point(self, point: NormalizedPoint, landmark: Optional[Any] = None) -> PointValidationResult:
        coords = point.canonical_position
        has_coords = any(abs(c) > 0.0001 for c in coords)

        if not has_coords or self.mesh is None:
            return PointValidationResult(
                code=point.code,
                name_zh=point.name_zh,
                source=point.source,
                canonical_coords=coords,
                normal=point.normal,
                measured_surface_distance_mm=0.0,
                signed_distance_mm=0.0,
                closest_face_index=-1,
                mesh_normal=[0.0, 0.0, 1.0],
                normal_alignment_dot=None,
                is_floating=False,
                is_penetrating=False,
                is_normal_inverted=False,
                recorded_face_match=None,
                discontinuity_warning=None,
                evidence_tag="UNVERIFIED",
                details="No 3D coordinates authored or mesh unavailable.",
            )

        recorded_face = point.extra.get("face_index")
        query_res = self.mesh.query_point(coords, point.normal, recorded_face)

        dist_mm = query_res["distance_mm"]
        signed_mm = query_res["signed_distance_mm"]
        norm_dot = query_res["normal_alignment_dot"]
        closest_face = query_res["closest_face_index"]
        mesh_norm = query_res["mesh_face_normal"]
        face_match = query_res["recorded_face_match"]

        is_floating = dist_mm > self.MAX_SURFACE_TOLERANCE_MM
        is_penetrating = signed_mm < self.MIN_SURFACE_TOLERANCE_MM
        is_inverted = (norm_dot is not None and norm_dot < 0.0)

        details_parts = []
        details_parts.append(f"Mesh dist: {dist_mm:.2f}mm (signed: {signed_mm:.2f}mm)")

        if is_floating:
            details_parts.append(f"FLOATING (> {self.MAX_SURFACE_TOLERANCE_MM}mm)")
        if is_penetrating:
            details_parts.append(f"PENETRATING (< {self.MIN_SURFACE_TOLERANCE_MM}mm)")
        if is_inverted:
            details_parts.append(f"INVERTED_NORMAL (dot={norm_dot:.2f})")
        if face_match is False:
            details_parts.append(f"FACE_INDEX_MISMATCH (recorded {recorded_face} vs true {closest_face})")

        # Determine Evidence Tag
        # Rule: ANATOMY_REVIEWED requires documented qualified expert review
        # Rule: GEOMETRY_VERIFIED requires real distance within tolerance and outward normal
        # Rule: Never equate surface adherence with clinical accuracy
        if point.status == "ANATOMY_REVIEWED" and not is_floating and not is_penetrating and not is_inverted:
            tag = "ANATOMY_REVIEWED"
            details_parts.append("Clinically reviewed & geometrically verified.")
        elif not is_floating and not is_penetrating and not is_inverted:
            tag = "GEOMETRY_VERIFIED"
            details_parts.append("Meets mesh surface tolerance; pending qualified clinical review.")
        else:
            tag = "UNVERIFIED"
            details_parts.append("Failed surface tolerance or unreviewed approximation.")

        return PointValidationResult(
            code=point.code,
            name_zh=point.name_zh,
            source=point.source,
            canonical_coords=coords,
            normal=point.normal,
            measured_surface_distance_mm=dist_mm,
            signed_distance_mm=signed_mm,
            closest_face_index=closest_face,
            mesh_normal=mesh_norm,
            normal_alignment_dot=norm_dot,
            is_floating=is_floating,
            is_penetrating=is_penetrating,
            is_normal_inverted=is_inverted,
            recorded_face_match=face_match,
            discontinuity_warning=None,
            evidence_tag=tag,
            details="; ".join(details_parts),
        )

    def validate_meridian_paths(self, meridian: NormalizedMeridian) -> List[Dict[str, Any]]:
        discontinuities = []
        for p_idx, path in enumerate(meridian.paths):
            for i in range(len(path) - 1):
                p0 = path[i]
                p1 = path[i + 1]
                step = CoordinateRegistry.euclidean_distance(p0, p1)
                if step > self.MAX_PATH_STEP_MM:
                    discontinuities.append({
                        "meridian": meridian.code,
                        "path_index": p_idx,
                        "vertex_index": i,
                        "step_distance_mm": round(step, 2),
                        "p0": p0,
                        "p1": p1,
                        "warning": f"Discontinuous step {step:.1f}mm exceeds max smooth step {self.MAX_PATH_STEP_MM}mm",
                    })
        return discontinuities

    def validate_source(self, adapter: BaseAdapter) -> SourceValidationSummary:
        src = adapter.get_source_name()
        points = adapter.extract_points()
        meridians = adapter.extract_meridians()

        results: List[PointValidationResult] = []
        distances: List[float] = []
        floating = 0
        penetrating = 0
        geom_count = 0
        anat_count = 0
        unver_count = 0

        for code, pt in points.items():
            # Match base landmark
            base_c = pt.extra.get("base_code", code)
            lm = CoordinateRegistry.get_landmark(base_c)
            res = self.validate_point(pt, lm)
            results.append(res)

            if any(abs(c) > 0.0001 for c in pt.canonical_position):
                distances.append(res.measured_surface_distance_mm)
                if res.is_floating:
                    floating += 1
                if res.is_penetrating:
                    penetrating += 1

            if res.evidence_tag == "ANATOMY_REVIEWED":
                anat_count += 1
            elif res.evidence_tag == "GEOMETRY_VERIFIED":
                geom_count += 1
            else:
                unver_count += 1

        all_discontinuities: List[Dict[str, Any]] = []
        for m in meridians.values():
            all_discontinuities.extend(self.validate_meridian_paths(m))

        mean_dist = sum(distances) / len(distances) if distances else 0.0
        max_dist = max(distances) if distances else 0.0

        return SourceValidationSummary(
            source_name=src,
            total_points=len(points),
            geometry_verified_count=geom_count,
            anatomy_reviewed_count=anat_count,
            unverified_count=unver_count,
            floating_count=floating,
            penetrating_count=penetrating,
            mean_measured_distance_mm=round(mean_dist, 2),
            max_measured_distance_mm=round(max_dist, 2),
            point_results=results,
            path_discontinuities=all_discontinuities,
        )
