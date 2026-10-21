"""Geometry Validator for evaluating mesh distance, surface adherence, and evidence tags."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .adapters.base import BaseAdapter, NormalizedMeridian, NormalizedPoint
from .coordinate_registry import CoordinateRegistry


@dataclass
class PointValidationResult:
    code: str
    name_zh: str
    source: str
    canonical_coords: List[float]
    normal: Optional[List[float]]
    surface_distance_mm: float
    is_floating: bool  # > 5.0 mm above surface
    is_penetrating: bool  # < -2.0 mm below surface
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
    mean_surface_offset_mm: float
    max_surface_offset_mm: float
    point_results: List[PointValidationResult]
    path_discontinuities: List[Dict[str, Any]] = field(default_factory=list)


class GeometryValidator:
    """Validator measuring skin clearance, ray intersection errors, and classifying evidence."""

    MAX_SURFACE_TOLERANCE_MM = 5.0
    MIN_SURFACE_TOLERANCE_MM = -2.0
    MAX_PATH_STEP_MM = 25.0

    def __init__(self):
        pass

    def validate_point(self, point: NormalizedPoint, landmark: Optional[Any] = None) -> PointValidationResult:
        coords = point.canonical_position
        has_coords = any(abs(c) > 0.0001 for c in coords)

        if not has_coords:
            return PointValidationResult(
                code=point.code,
                name_zh=point.name_zh,
                source=point.source,
                canonical_coords=coords,
                normal=point.normal,
                surface_distance_mm=0.0,
                is_floating=False,
                is_penetrating=False,
                discontinuity_warning=None,
                evidence_tag="UNVERIFIED",
                details="No 3D coordinates authored in catalog entry.",
            )

        offset = point.surface_distance_mm
        is_floating = offset > self.MAX_SURFACE_TOLERANCE_MM
        is_penetrating = offset < self.MIN_SURFACE_TOLERANCE_MM

        # Evidence classification
        details_list = []
        if landmark is not None:
            dist_to_lm = CoordinateRegistry.euclidean_distance(coords, landmark.canonical_coords)
            details_list.append(f"Landmark dist: {dist_to_lm:.1f}mm ({landmark.skeletal_anchor})")
            if dist_to_lm <= 20.0 and not is_floating and not is_penetrating:
                tag = "ANATOMY_REVIEWED"
            elif not is_floating and not is_penetrating:
                tag = "GEOMETRY_VERIFIED"
            else:
                tag = "UNVERIFIED"
                if is_floating:
                    details_list.append(f"Floating ({offset:.1f}mm > {self.MAX_SURFACE_TOLERANCE_MM}mm)")
                if is_penetrating:
                    details_list.append(f"Penetrating ({offset:.1f}mm < {self.MIN_SURFACE_TOLERANCE_MM}mm)")
        else:
            if not is_floating and not is_penetrating:
                tag = "GEOMETRY_VERIFIED"
            else:
                tag = "UNVERIFIED"
                if is_floating:
                    details_list.append(f"Floating ({offset:.1f}mm)")
                if is_penetrating:
                    details_list.append(f"Penetrating ({offset:.1f}mm)")

        if point.status == "ANATOMY_REVIEWED":
            tag = "ANATOMY_REVIEWED"

        return PointValidationResult(
            code=point.code,
            name_zh=point.name_zh,
            source=point.source,
            canonical_coords=coords,
            normal=point.normal,
            surface_distance_mm=offset,
            is_floating=is_floating,
            is_penetrating=is_penetrating,
            discontinuity_warning=None,
            evidence_tag=tag,
            details="; ".join(details_list) if details_list else "Conforms to surface tolerance.",
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
                        "warning": f"Step distance {step:.1f}mm exceeds max smooth step {self.MAX_PATH_STEP_MM}mm",
                    })
        return discontinuities

    def validate_source(self, adapter: BaseAdapter) -> SourceValidationSummary:
        src = adapter.get_source_name()
        points = adapter.extract_points()
        meridians = adapter.extract_meridians()

        results: List[PointValidationResult] = []
        offsets: List[float] = []
        floating = 0
        penetrating = 0
        geom_count = 0
        anat_count = 0
        unver_count = 0

        for code, pt in points.items():
            lm = CoordinateRegistry.get_landmark(code)
            res = self.validate_point(pt, lm)
            results.append(res)

            if any(abs(c) > 0.0001 for c in pt.canonical_position):
                offsets.append(res.surface_distance_mm)
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

        mean_off = sum(offsets) / len(offsets) if offsets else 0.0
        max_off = max(offsets) if offsets else 0.0

        return SourceValidationSummary(
            source_name=src,
            total_points=len(points),
            geometry_verified_count=geom_count,
            anatomy_reviewed_count=anat_count,
            unverified_count=unver_count,
            floating_count=floating,
            penetrating_count=penetrating,
            mean_surface_offset_mm=round(mean_off, 2),
            max_surface_offset_mm=round(max_off, 2),
            point_results=results,
            path_discontinuities=all_discontinuities,
        )
