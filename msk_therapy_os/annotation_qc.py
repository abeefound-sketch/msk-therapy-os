"""MSK-Therapy-OS P10.5 Independent Annotation Quality Control (QC) Engine

Implements double-blind independent annotation validation, inter-observer discrepancy detection,
and third-reviewer adjudication workflows.

Key Verification Rules:
1. Double-blind assignment: Primary Observer A and Secondary Observer B independently place landmarks.
2. Inter-observer distance calculation:
   d = sqrt((x_A - x_B)^2 + (y_A - y_B)^2 + (z_A - z_B)^2)
3. Discrepancy flags:
   - For Cranial osseous points: d > 3.0 mm triggers adjudication.
   - For Abdominal / Extremity soft-tissue points: d > 5.0 mm triggers adjudication.
4. Model blindness: Neither observer may be presented with model-predicted coordinates.
5. Third-reviewer adjudication: An independent senior clinician resolves flagged discrepancies.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AnnotationQCStatus(str, Enum):
    CONCORDANT_APPROVED = "CONCORDANT_APPROVED"
    DISCREPANCY_FLAGGED = "DISCREPANCY_FLAGGED"
    ADJUDICATED_RESOLVED = "ADJUDICATED_RESOLVED"
    REJECTED_UNRESOLVABLE = "REJECTED_UNRESOLVABLE"


@dataclass
class RawLandmarkCoordinate:
    observer_id: str
    observer_qualification: str
    lps_coordinates_mm: Tuple[float, float, float]
    timestamp_utc: str
    is_blinded: bool = True
    confidence_score: float = 1.0


@dataclass
class AdjudicationRecord:
    adjudicator_id: str
    resolved_lps_coordinates_mm: Tuple[float, float, float]
    resolution_method: str  # "CENTROID_OF_OBSERVERS", "OBSERVER_A_PREFERRED", "OBSERVER_B_PREFERRED", "MANUAL_CORRECTION"
    clinical_rationale: str
    timestamp_utc: str
    adjudicator_coi_screened: bool = True


@dataclass
class LandmarkAnnotationPair:
    pair_id: str
    subject_id: str
    cohort_id: str
    landmark_id: str
    observer_a_coord: RawLandmarkCoordinate
    observer_b_coord: RawLandmarkCoordinate
    inter_observer_distance_mm: float
    discrepancy_threshold_mm: float
    qc_status: AnnotationQCStatus
    adjudication: Optional[AdjudicationRecord] = None
    final_consensus_lps_mm: Optional[Tuple[float, float, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["qc_status"] = self.qc_status.value
        return d


class AnnotationQualityControlEngine:
    """Evaluates double-blind landmark pairs, flags inter-observer variance, and manages adjudication."""

    DEFAULT_THRESHOLDS = {
        "CRANIAL_OSSEOUS": 3.0,     # e.g., Nasion, Inion, Mastoid
        "EXTREMITY_SKELETAL": 4.0,  # e.g., Radial styloid, Tibial tuberosity
        "SOFT_TISSUE_FASCIAL": 5.0, # e.g., Abdominal midline, tendon junctions
    }

    @staticmethod
    def compute_euclidean_distance(
        p1: Tuple[float, float, float],
        p2: Tuple[float, float, float]
    ) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    @classmethod
    def process_annotation_pair(
        cls,
        subject_id: str,
        cohort_id: str,
        landmark_id: str,
        coord_a: RawLandmarkCoordinate,
        coord_b: RawLandmarkCoordinate,
        landmark_category: str = "CRANIAL_OSSEOUS",
        custom_threshold_mm: Optional[float] = None,
    ) -> LandmarkAnnotationPair:
        """Processes double-blind annotations from Observers A and B."""
        if coord_a.observer_id == coord_b.observer_id:
            raise ValueError("Observers A and B must be distinct individuals for double-blind verification.")

        if not (coord_a.is_blinded and coord_b.is_blinded):
            raise PermissionError("Unblinded annotations are invalid: Model predictions cannot be shown to observers.")

        dist = cls.compute_euclidean_distance(coord_a.lps_coordinates_mm, coord_b.lps_coordinates_mm)
        threshold = custom_threshold_mm or cls.DEFAULT_THRESHOLDS.get(landmark_category, 4.0)

        pair_id = f"QC-{subject_id}-{landmark_id}"

        if dist <= threshold:
            # Automatic consensus is the midpoint centroid
            consensus = (
                round((coord_a.lps_coordinates_mm[0] + coord_b.lps_coordinates_mm[0]) / 2.0, 3),
                round((coord_a.lps_coordinates_mm[1] + coord_b.lps_coordinates_mm[1]) / 2.0, 3),
                round((coord_a.lps_coordinates_mm[2] + coord_b.lps_coordinates_mm[2]) / 2.0, 3),
            )
            status = AnnotationQCStatus.CONCORDANT_APPROVED
            adj = None
        else:
            # Exceeds threshold: must be adjudicated by senior reviewer
            consensus = None
            status = AnnotationQCStatus.DISCREPANCY_FLAGGED
            adj = None

        return LandmarkAnnotationPair(
            pair_id=pair_id,
            subject_id=subject_id,
            cohort_id=cohort_id,
            landmark_id=landmark_id,
            observer_a_coord=coord_a,
            observer_b_coord=coord_b,
            inter_observer_distance_mm=round(dist, 3),
            discrepancy_threshold_mm=threshold,
            qc_status=status,
            adjudication=adj,
            final_consensus_lps_mm=consensus,
        )

    @classmethod
    def adjudicate_discrepancy(
        cls,
        pair: LandmarkAnnotationPair,
        adjudicator_id: str,
        resolved_coords: Tuple[float, float, float],
        resolution_method: str,
        clinical_rationale: str,
        coi_screened: bool = True,
    ) -> LandmarkAnnotationPair:
        """Executes third-reviewer clinical adjudication for flagged inter-observer discrepancies."""
        if pair.qc_status != AnnotationQCStatus.DISCREPANCY_FLAGGED:
            raise ValueError(f"Cannot adjudicate: Pair status is currently {pair.qc_status.value}.")

        if adjudicator_id in (pair.observer_a_coord.observer_id, pair.observer_b_coord.observer_id):
            raise PermissionError("Adjudicator must be an independent third party, distinct from Observers A and B.")

        if not coi_screened:
            raise PermissionError("Adjudicator must have signed non-conflict of interest declaration.")

        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        adj_rec = AdjudicationRecord(
            adjudicator_id=adjudicator_id,
            resolved_lps_coordinates_mm=resolved_coords,
            resolution_method=resolution_method,
            clinical_rationale=clinical_rationale,
            timestamp_utc=now_utc,
            adjudicator_coi_screened=coi_screened,
        )

        pair.adjudication = adj_rec
        pair.final_consensus_lps_mm = resolved_coords
        pair.qc_status = AnnotationQCStatus.ADJUDICATED_RESOLVED
        return pair

    @staticmethod
    def generate_qc_summary_report(pairs: List[LandmarkAnnotationPair]) -> Dict[str, Any]:
        """Calculates cohort-level inter-observer reliability metrics."""
        total = len(pairs)
        if total == 0:
            return {"total_evaluated": 0}

        distances = [p.inter_observer_distance_mm for p in pairs]
        mean_inter_obs_mm = sum(distances) / total
        max_dist_mm = max(distances)

        status_counts = {s.value: 0 for s in AnnotationQCStatus}
        for p in pairs:
            status_counts[p.qc_status.value] += 1

        concordance_rate = (status_counts[AnnotationQCStatus.CONCORDANT_APPROVED.value] +
                            status_counts[AnnotationQCStatus.ADJUDICATED_RESOLVED.value]) / total

        return {
            "total_landmarks_evaluated": total,
            "mean_inter_observer_distance_mm": round(mean_inter_obs_mm, 3),
            "max_inter_observer_distance_mm": round(max_dist_mm, 3),
            "status_distribution": status_counts,
            "overall_consensus_concordance_rate": round(concordance_rate, 4),
            "unresolved_discrepancies": status_counts[AnnotationQCStatus.DISCREPANCY_FLAGGED.value],
        }
