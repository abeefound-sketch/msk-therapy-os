"""Comparison Engine for evaluating acupoint coordinates, pathways, and source agreement."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .adapters.base import BaseAdapter, NormalizedMeridian, NormalizedPoint
from .coordinate_registry import CoordinateRegistry


@dataclass
class PointComparisonResult:
    code: str
    name_zh: str
    canonical_coords: Optional[List[float]]
    positions_by_source: Dict[str, List[float]]
    distance_to_landmark_mm: Dict[str, float]
    inter_source_pairwise_distances_mm: Dict[str, float]
    mean_error_mm: float
    max_error_mm: float
    agreement_status: str  # CONVERGENT (<15mm), DEVIATING (15-35mm), DISCREPANT (>35mm)


@dataclass
class ScenarioComparisonReport:
    scenario_name: str
    target_codes: List[str]
    point_results: List[PointComparisonResult]
    overall_mean_error_mm: float
    source_rankings: List[Tuple[str, float]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComparisonEngine:
    """Engine comparing acupuncture coordinates and meridian trajectories across upstreams."""

    def __init__(self, adapters: List[BaseAdapter]):
        self.adapters = adapters
        self.points_by_source: Dict[str, Dict[str, NormalizedPoint]] = {}
        self.meridians_by_source: Dict[str, Dict[str, NormalizedMeridian]] = {}
        self._load_data()

    def _load_data(self) -> None:
        for ad in self.adapters:
            src = ad.get_source_name()
            self.points_by_source[src] = ad.extract_points()
            self.meridians_by_source[src] = ad.extract_meridians()

    def _find_point_in_source(self, code: str, pts: Dict[str, NormalizedPoint]) -> Optional[NormalizedPoint]:
        """Find a point by exact code, or right-side code (_R), or base code."""
        if code in pts:
            return pts[code]
        if f"{code}_R" in pts:
            return pts[f"{code}_R"]
        if f"{code}_L" in pts:
            return pts[f"{code}_L"]
        for p in pts.values():
            if p.extra.get("base_code") == code:
                return p
        return None

    def compare_point(self, code: str) -> PointComparisonResult:
        """Compare a single acupuncture point across all available sources and landmarks."""
        landmark = CoordinateRegistry.get_landmark(code)
        canonical = landmark.canonical_coords if landmark else None
        name_zh = landmark.name_zh if landmark else code

        positions: Dict[str, List[float]] = {}
        dist_to_landmark: Dict[str, float] = {}

        for src, pts in self.points_by_source.items():
            pt = self._find_point_in_source(code, pts)
            if pt is not None:
                pos = pt.canonical_position
                if any(abs(c) > 0.0001 for c in pos):
                    positions[src] = pos
                    if not name_zh or name_zh == code:
                        name_zh = pt.name_zh
                    if canonical:
                        dist_to_landmark[src] = CoordinateRegistry.euclidean_distance(pos, canonical)

        # Calculate pairwise distances between sources
        pairwise: Dict[str, float] = {}
        src_keys = list(positions.keys())
        for i in range(len(src_keys)):
            for j in range(i + 1, len(src_keys)):
                s1, s2 = src_keys[i], src_keys[j]
                d = CoordinateRegistry.euclidean_distance(positions[s1], positions[s2])
                pairwise[f"{s1} vs {s2}"] = round(d, 2)

        errors = list(dist_to_landmark.values())
        mean_err = sum(errors) / len(errors) if errors else 0.0
        max_err = max(errors) if errors else 0.0

        if errors:
            if max_err <= 15.0:
                agreement = "CONVERGENT"
            elif max_err <= 35.0:
                agreement = "DEVIATING"
            else:
                agreement = "DISCREPANT"
        else:
            agreement = "NO_LANDMARK"

        return PointComparisonResult(
            code=code,
            name_zh=name_zh,
            canonical_coords=canonical,
            positions_by_source=positions,
            distance_to_landmark_mm={k: round(v, 2) for k, v in dist_to_landmark.items()},
            inter_source_pairwise_distances_mm=pairwise,
            mean_error_mm=round(mean_err, 2),
            max_error_mm=round(max_err, 2),
            agreement_status=agreement,
        )

    def compare_scenario(self, codes: Optional[List[str]] = None, name: str = "Neck-Shoulder Reference Scenario") -> ScenarioComparisonReport:
        if codes is None:
            codes = CoordinateRegistry.get_neck_shoulder_scenario_codes()

        results: List[PointComparisonResult] = []
        source_errors: Dict[str, List[float]] = {}

        for c in codes:
            res = self.compare_point(c)
            results.append(res)
            for src, err in res.distance_to_landmark_mm.items():
                source_errors.setdefault(src, []).append(err)

        total_errors: List[float] = []
        source_rankings: List[Tuple[str, float]] = []

        for src, errs in source_errors.items():
            mean_s_err = sum(errs) / len(errs)
            source_rankings.append((src, round(mean_s_err, 2)))
            total_errors.extend(errs)

        source_rankings.sort(key=lambda x: x[1])
        overall_mean = sum(total_errors) / len(total_errors) if total_errors else 0.0

        return ScenarioComparisonReport(
            scenario_name=name,
            target_codes=codes,
            point_results=results,
            overall_mean_error_mm=round(overall_mean, 2),
            source_rankings=source_rankings,
            metadata={
                "total_points_compared": len(codes),
                "active_sources": list(self.points_by_source.keys()),
            },
        )
