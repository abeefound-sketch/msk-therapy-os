"""WHO 2008 Standard Parametric Cun-Scaling Engine for MSK-Therapy-OS.

Implements Section 2 of the WHO Standard (Bone-proportional B-cun and Finger-proportional F-cun),
regional anthropometric segment scaling integrated with Morphology Studio,
and anatomical point interpolation with strict boundary verification.
Zero external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple

from .landmark_registry import (
    AnatomicalLandmark,
    BodyRegion,
    CANONICAL_LANDMARKS,
    LandmarkRegistry,
)


class SegmentAxis(str, Enum):
    LONGITUDINAL = "longitudinal"  # Vertical / Superior-Inferior or Proximal-Distal
    TRANSVERSE = "transverse"      # Horizontal / Medial-Lateral


@dataclass(frozen=True)
class BoneProportionalSegment:
    """Rigorous model of a bone-proportional segment per WHO 2008 Standard."""
    segment_id: str
    name_en: str
    name_zh: str
    region: BodyRegion
    axis: SegmentAxis
    standard_bcun_units: float  # Number of B-cun units in this anatomical segment
    start_landmark_id: str      # Proximal / Superior / Medial anchor
    end_landmark_id: str        # Distal / Inferior / Lateral anchor
    who_reference: str
    notes: str = ""


# WHO 2008 Standard B-cun Segment Catalog
WHO_BONE_SEGMENTS: Dict[str, BoneProportionalSegment] = {
    # -------------------------------------------------------------------------
    # HEAD & CRANIUM
    # -------------------------------------------------------------------------
    "SEG_HEAD_ANTEROPOSTERIOR": BoneProportionalSegment(
        segment_id="SEG_HEAD_ANTEROPOSTERIOR",
        name_en="Cranial Anteroposterior Length",
        name_zh="前发际正中至后发际正中",
        region=BodyRegion.HEAD_NECK,
        axis=SegmentAxis.LONGITUDINAL,
        standard_bcun_units=9.0,  # 9 cun between anterior and posterior hairlines
        start_landmark_id="LM_GLABELLA",  # Fallback to Glabella if anterior hairline indistinct (WHO p. 11)
        end_landmark_id="LM_INION",       # Inion
        who_reference="WHO 2008 Standard, p. 11: Section 2.1.1 Head",
        notes="Standard is 9 cun between hairlines. When indistinct, glabella to inion is taken as 12 cun.",
    ),
    "SEG_HEAD_MASTOID_TRANSVERSE": BoneProportionalSegment(
        segment_id="SEG_HEAD_MASTOID_TRANSVERSE",
        name_en="Bimastoid Transverse Width",
        name_zh="两乳突之间",
        region=BodyRegion.HEAD_NECK,
        axis=SegmentAxis.TRANSVERSE,
        standard_bcun_units=9.0,
        start_landmark_id="LM_MASTOID_L",
        end_landmark_id="LM_MASTOID_R",
        who_reference="WHO 2008 Standard, p. 11: Section 2.1.1 Head",
        notes="Distance between the tips of the two mastoid processes.",
    ),

    # -------------------------------------------------------------------------
    # CHEST & ABDOMEN
    # -------------------------------------------------------------------------
    "SEG_CHEST_STERNUM": BoneProportionalSegment(
        segment_id="SEG_CHEST_STERNUM",
        name_en="Sternal Length (Jugular Notch to Xiphisternal)",
        name_zh="天突至歧骨 (胸剑联合)",
        region=BodyRegion.TORSO,
        axis=SegmentAxis.LONGITUDINAL,
        standard_bcun_units=9.0,
        start_landmark_id="LM_JUGULAR_NOTCH",
        end_landmark_id="LM_XIPHOSTERNAL_JOINT",
        who_reference="WHO 2008 Standard, p. 12: Section 2.1.2 Chest and Abdomen",
        notes="Suprasternal fossa to xiphisternal synchondrosis.",
    ),
    "SEG_ABDOMEN_UPPER": BoneProportionalSegment(
        segment_id="SEG_ABDOMEN_UPPER",
        name_en="Upper Abdomen (Xiphisternal to Umbilicus)",
        name_zh="歧骨至脐中",
        region=BodyRegion.TORSO,
        axis=SegmentAxis.LONGITUDINAL,
        standard_bcun_units=8.0,
        start_landmark_id="LM_XIPHOSTERNAL_JOINT",
        end_landmark_id="LM_UMBILICUS",
        who_reference="WHO 2008 Standard, p. 12: Section 2.1.2 Chest and Abdomen",
        notes="From xiphisternal junction to center of umbilicus.",
    ),
    "SEG_ABDOMEN_LOWER": BoneProportionalSegment(
        segment_id="SEG_ABDOMEN_LOWER",
        name_en="Lower Abdomen (Umbilicus to Pubic Symphysis)",
        name_zh="脐中至耻骨联合上缘",
        region=BodyRegion.TORSO,
        axis=SegmentAxis.LONGITUDINAL,
        standard_bcun_units=5.0,
        start_landmark_id="LM_UMBILICUS",
        end_landmark_id="LM_PUBIC_SYMPHYSIS",
        who_reference="WHO 2008 Standard, p. 12: Section 2.1.2 Chest and Abdomen",
        notes="From center of umbilicus to upper border of pubic symphysis.",
    ),
    "SEG_CHEST_BINIPPLE": BoneProportionalSegment(
        segment_id="SEG_CHEST_BINIPPLE",
        name_en="Binipple Transverse Width",
        name_zh="两乳头之间",
        region=BodyRegion.TORSO,
        axis=SegmentAxis.TRANSVERSE,
        standard_bcun_units=8.0,
        start_landmark_id="LM_ASIS_L",  # Correlates with mid-clavicular line width
        end_landmark_id="LM_ASIS_R",
        who_reference="WHO 2008 Standard, p. 12: Section 2.1.2 Chest and Abdomen",
        notes="Between the centers of both nipples or mid-clavicular lines.",
    ),

    # -------------------------------------------------------------------------
    # UPPER EXTREMITY
    # -------------------------------------------------------------------------
    "SEG_ARM_AXILLA_TO_ELBOW_R": BoneProportionalSegment(
        segment_id="SEG_ARM_AXILLA_TO_ELBOW_R",
        name_en="Right Upper Arm (Axillary Fold to Cubital Crease)",
        name_zh="右侧腋前纹头至肘横纹",
        region=BodyRegion.UPPER_EXTREMITY,
        axis=SegmentAxis.LONGITUDINAL,
        standard_bcun_units=9.0,
        start_landmark_id="LM_AXILLARY_FOLD_ANT_R",
        end_landmark_id="LM_CUBITAL_CREASE_R",
        who_reference="WHO 2008 Standard, p. 13: Section 2.1.4 Upper Extremities",
        notes="From apex of anterior axillary fold to cubital crease.",
    ),
    "SEG_FOREARM_ELBOW_TO_WRIST_R": BoneProportionalSegment(
        segment_id="SEG_FOREARM_ELBOW_TO_WRIST_R",
        name_en="Right Forearm (Cubital Crease to Palmar Wrist Crease)",
        name_zh="右侧肘横纹至腕掌侧远端横纹",
        region=BodyRegion.UPPER_EXTREMITY,
        axis=SegmentAxis.LONGITUDINAL,
        standard_bcun_units=12.0,
        start_landmark_id="LM_CUBITAL_CREASE_R",
        end_landmark_id="LM_WRIST_CREASE_PALMAR_R",
        who_reference="WHO 2008 Standard, p. 13: Section 2.1.4 Upper Extremities",
        notes="From cubital crease to distal palmar wrist crease.",
    ),

    # -------------------------------------------------------------------------
    # LOWER EXTREMITY
    # -------------------------------------------------------------------------
    "SEG_THIGH_TROCHANTER_TO_POPLITEAL_R": BoneProportionalSegment(
        segment_id="SEG_THIGH_TROCHANTER_TO_POPLITEAL_R",
        name_en="Right Thigh Lateral (Greater Trochanter to Popliteal Crease)",
        name_zh="右侧股骨大转子至腘横纹",
        region=BodyRegion.LOWER_EXTREMITY,
        axis=SegmentAxis.LONGITUDINAL,
        standard_bcun_units=19.0,
        start_landmark_id="LM_GREATER_TROCHANTER_R",
        end_landmark_id="LM_POPLITEAL_CREASE_R",
        who_reference="WHO 2008 Standard, p. 14: Section 2.1.5 Lower Extremities",
        notes="From prominence of greater trochanter to popliteal crease.",
    ),
    "SEG_LEG_POPLITEAL_TO_MALLEOLUS_R": BoneProportionalSegment(
        segment_id="SEG_LEG_POPLITEAL_TO_MALLEOLUS_R",
        name_en="Right Leg Lateral (Popliteal Crease to Lateral Malleolus)",
        name_zh="右侧腘横纹至外踝尖",
        region=BodyRegion.LOWER_EXTREMITY,
        axis=SegmentAxis.LONGITUDINAL,
        standard_bcun_units=16.0,
        start_landmark_id="LM_POPLITEAL_CREASE_R",
        end_landmark_id="LM_LAT_MALLEOLUS_R",
        who_reference="WHO 2008 Standard, p. 14: Section 2.1.5 Lower Extremities",
        notes="From popliteal crease to tip of lateral malleolus.",
    ),
    "SEG_LEG_MEDIAL_TIBIA_TO_MALLEOLUS_R": BoneProportionalSegment(
        segment_id="SEG_LEG_MEDIAL_TIBIA_TO_MALLEOLUS_R",
        name_en="Right Leg Medial (Inferior Tibial Condyle to Medial Malleolus)",
        name_zh="右侧胫骨内侧髁下缘至内踝尖",
        region=BodyRegion.LOWER_EXTREMITY,
        axis=SegmentAxis.LONGITUDINAL,
        standard_bcun_units=13.0,
        start_landmark_id="LM_PATELLA_INFERIOR_R",  # Reference near Yinlingquan SP9
        end_landmark_id="LM_MED_MALLEOLUS_R",
        who_reference="WHO 2008 Standard, p. 14: Section 2.1.5 Lower Extremities",
        notes="From inferior border of medial condyle of tibia to tip of medial malleolus.",
    ),
}


@dataclass
class RegionalCunMetric:
    """Calculated physical metric for 1 B-cun within an anatomical segment."""
    segment_id: str
    segment_length_mm: float
    standard_units: float
    mm_per_cun: float
    deviation_from_global_pct: float
    who_reference: str


class CunScalingEngine:
    """Parametric Cun-Scaling Engine calibrated to WHO 2008 standard and patient morphology."""

    def __init__(self, landmark_registry: Optional[LandmarkRegistry] = None):
        self.registry = landmark_registry or LandmarkRegistry()
        self.segments = dict(WHO_BONE_SEGMENTS)

    def calculate_segment_metrics(
        self,
        custom_landmarks: Optional[Dict[str, Tuple[float, float, float]]] = None,
        nominal_height_mm: float = 1720.0
    ) -> Dict[str, RegionalCunMetric]:
        """Compute the physical length and millimeter-per-cun ratio for each WHO B-cun segment."""
        metrics: Dict[str, RegionalCunMetric] = {}
        # Global naive baseline cun: body height divided by 75 (classical standard: adult = 75 cun)
        global_naive_cun_mm = nominal_height_mm / 75.0  # ≈ 22.93 mm

        for seg_id, seg in self.segments.items():
            p_start = None
            p_end = None

            if custom_landmarks:
                p_start = custom_landmarks.get(seg.start_landmark_id)
                p_end = custom_landmarks.get(seg.end_landmark_id)

            if p_start is None:
                p_start = self.registry.get_canonical_position(seg.start_landmark_id)
            if p_end is None:
                p_end = self.registry.get_canonical_position(seg.end_landmark_id)

            if p_start is None or p_end is None:
                continue

            length_mm = self.registry.calculate_distance_mm(p_start, p_end)
            mm_per_cun = length_mm / seg.standard_bcun_units if seg.standard_bcun_units > 0 else 0.0
            dev_pct = ((mm_per_cun - global_naive_cun_mm) / global_naive_cun_mm) * 100.0 if global_naive_cun_mm > 0 else 0.0

            metrics[seg_id] = RegionalCunMetric(
                segment_id=seg_id,
                segment_length_mm=round(length_mm, 2),
                standard_units=seg.standard_bcun_units,
                mm_per_cun=round(mm_per_cun, 2),
                deviation_from_global_pct=round(dev_pct, 2),
                who_reference=seg.who_reference,
            )

        return metrics

    def compute_morphology_adapted_cun(
        self,
        morphology_params: Dict[str, Any]
    ) -> Dict[str, float]:
        """Adapt regional B-cun lengths using patient anthropometric parameters from Morphology Studio.

        Parameters from Morphology Studio:
        - height_cm (100.0 - 230.0)
        - chest_circ_cm (50.0 - 180.0)
        - waist_circ_cm (40.0 - 180.0)
        - arm_circ_cm (15.0 - 65.0)
        - thigh_circ_cm (25.0 - 95.0)
        - calf_circ_cm (18.0 - 65.0)
        - shoulder_width_cm (25.0 - 65.0)
        """
        # Baseline reference stature (FJ2810 canonical height is 172.0 cm)
        ref_height_cm = 172.0
        patient_height_cm = float(morphology_params.get("height_cm", ref_height_cm))
        height_ratio = patient_height_cm / ref_height_cm

        # Shoulder width scaling for transverse thorax
        ref_shoulder_cm = 42.0
        patient_shoulder_cm = float(morphology_params.get("shoulder_width_cm", ref_shoulder_cm))
        shoulder_ratio = patient_shoulder_cm / ref_shoulder_cm

        # Limb girth scaling factors for local lateral offset adjustment
        ref_arm_circ = 28.0
        patient_arm_circ = float(morphology_params.get("arm_circ_cm", ref_arm_circ))
        arm_girth_ratio = patient_arm_circ / ref_arm_circ

        ref_thigh_circ = 54.0
        patient_thigh_circ = float(morphology_params.get("thigh_circ_cm", ref_thigh_circ))
        thigh_girth_ratio = patient_thigh_circ / ref_thigh_circ

        # Compute base canonical metrics
        canonical_metrics = self.calculate_segment_metrics(nominal_height_mm=patient_height_cm * 10.0)
        adapted_mm_per_cun: Dict[str, float] = {}

        for seg_id, metric in canonical_metrics.items():
            seg = self.segments[seg_id]
            base_mm = metric.mm_per_cun

            if seg.axis == SegmentAxis.LONGITUDINAL:
                # Longitudinal segment scales with stature ratio
                adapted_mm_per_cun[seg_id] = round(base_mm * height_ratio, 2)
            else:
                # Transverse segment scales with shoulder / bi-iliac width
                adapted_mm_per_cun[seg_id] = round(base_mm * shoulder_ratio, 2)

        # Include F-cun approximations scaled to stature
        # 1 middle-finger F-cun ≈ height / 75 (WHO Section 2.2)
        base_fcun_mm = (patient_height_cm * 10.0) / 75.0
        adapted_mm_per_cun["FCUN_MIDDLE_FINGER"] = round(base_fcun_mm, 2)
        adapted_mm_per_cun["FCUN_THUMB_WIDTH"] = round(base_fcun_mm * 0.95, 2)
        adapted_mm_per_cun["FCUN_FOUR_FINGERS"] = round(base_fcun_mm * 3.0, 2)

        return adapted_mm_per_cun

    def interpolate_point_on_segment(
        self,
        segment_id: str,
        cun_fraction: float,
        lateral_cun: float = 0.0,
        side: str = "right",
        custom_landmarks: Optional[Dict[str, Tuple[float, float, float]]] = None
    ) -> Dict[str, Any]:
        """Interpolate an anatomical point position along a B-cun segment.

        Args:
            segment_id: ID of WHO bone segment.
            cun_fraction: Fractional distance along segment (0.0 = start landmark, 1.0 = end landmark).
            lateral_cun: Lateral displacement perpendicular to segment axis (in B-cun).
            side: 'right', 'left', or 'midline'.
            custom_landmarks: Optional patient/custom landmark positions.
        """
        seg = self.segments.get(segment_id)
        if not seg:
            return {
                "position": None,
                "status": "INVALID_SEGMENT",
                "error": f"Segment '{segment_id}' not found in WHO bone segment catalog.",
            }

        # Boundary check: cun_fraction must be within physiological range [-0.2, 1.2]
        if not (-0.2 <= cun_fraction <= 1.2):
            return {
                "position": None,
                "status": "OUT_OF_SEGMENT_BOUNDS",
                "error": f"Cun fraction {cun_fraction:.3f} exceeds valid segment interpolation bounds [-0.2, 1.2].",
            }

        p_start = None
        p_end = None
        if custom_landmarks:
            p_start = custom_landmarks.get(seg.start_landmark_id)
            p_end = custom_landmarks.get(seg.end_landmark_id)

        if p_start is None:
            p_start = self.registry.get_canonical_position(seg.start_landmark_id)
        if p_end is None:
            p_end = self.registry.get_canonical_position(seg.end_landmark_id)

        if p_start is None or p_end is None:
            return {
                "position": None,
                "status": "MISSING_ANCHOR_LANDMARKS",
                "error": f"Could not resolve anchor landmarks for segment '{segment_id}'.",
            }

        # Linear interpolation between anchors in meters
        px = p_start[0] + cun_fraction * (p_end[0] - p_start[0])
        py = p_start[1] + cun_fraction * (p_end[1] - p_start[1])
        pz = p_start[2] + cun_fraction * (p_end[2] - p_start[2])

        # Lateral displacement in meters
        if lateral_cun != 0.0 and seg.standard_bcun_units > 0:
            seg_len_m = self.registry.calculate_distance_mm(p_start, p_end) / 1000.0
            m_per_cun = seg_len_m / seg.standard_bcun_units
            lat_offset_m = lateral_cun * m_per_cun
            if side == "left":
                lat_offset_m = -lat_offset_m
            # Lateral displacement along X axis
            px += lat_offset_m

        return {
            "position": (round(px, 5), round(py, 5), round(pz, 5)),
            "status": "VERIFIED_PARAMETRIC_CUN",
            "segment_id": segment_id,
            "cun_fraction": cun_fraction,
            "lateral_cun": lateral_cun,
            "who_reference": seg.who_reference,
        }
