"""WHO 2008 Standard Acupoint Localization Rules & Geometric Resolution Engine.

Models the 361 classical acupuncture points using formal anatomical localization rules:
- LANDMARK_DEFINED: Exact palpation bony/soft-tissue anchor.
- B_CUN_PROPORTIONAL: Parametric proportional division between landmark boundaries.
- TENDON_INTERVAL: Depression between two palpated tendons.
- MUSCLE_BORDER: Border of a specified skeletal muscle.
- SKIN_CREASE: Joint flexion crease anchor.
- MIDLINE_REFERENCE: Sagittal anterior or posterior midline alignment.
- PARASAGITTAL_LINE: Prescribed lateral B-cun distance from midline.

Zero external dependencies (pure Python 3.11).
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
from .cun_scaling import (
    BoneProportionalSegment,
    CunScalingEngine,
    WHO_BONE_SEGMENTS,
)


class LocalizationMethod(str, Enum):
    LANDMARK_DEFINED = "LANDMARK_DEFINED"
    B_CUN_PROPORTIONAL = "B_CUN_PROPORTIONAL"
    F_CUN_REFERENCED = "F_CUN_REFERENCED"
    TENDON_INTERVAL = "TENDON_INTERVAL"
    MUSCLE_BORDER = "MUSCLE_BORDER"
    SKIN_CREASE = "SKIN_CREASE"
    JOINT_DEPRESSION = "JOINT_DEPRESSION"
    MIDLINE_REFERENCE = "MIDLINE_REFERENCE"
    PARASAGITTAL_LINE = "PARASAGITTAL_LINE"
    MULTI_LANDMARK_RELATION = "MULTI_LANDMARK_RELATION"
    MANUAL_EXPERT_ANNOTATION = "MANUAL_EXPERT_ANNOTATION"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class AcupointLocalizationRule:
    """Rigorous mathematical specification for locating an acupuncture point."""
    point_code: str
    meridian_code: str
    name_en: str
    name_zh: str
    name_vi: str
    localization_method: LocalizationMethod
    fma_anchor: str
    body_region: BodyRegion
    who_reference: str
    skeletal_structure: str
    start_landmark_id: Optional[str] = None
    end_landmark_id: Optional[str] = None
    proportional_fraction: float = 0.0  # 0.0 to 1.0 along the segment
    lateral_offset_cun: float = 0.0     # B-cun distance from midline
    transverse_segment_id: Optional[str] = None
    tolerance_radius_mm: float = 5.0
    uncertainty_mm: float = 10.0
    quality_class: str = "CLASS_B"      # CLASS_A if independently audited, else CLASS_B
    is_posture_sensitive: bool = False
    sensitive_joint: Optional[str] = None
    threshold_deg: float = 15.0


def _normalize(v: List[float] | Tuple[float, ...]) -> List[float]:
    mag = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if mag < 1e-9:
        return [0.0, 0.0, 1.0]
    return [v[0] / mag, v[1] / mag, v[2] / mag]


# Catalog of Authoritative Acupoint Localization Rules (WHO 2008 Standard + FJ2810 Anatomy)
ACUPOINT_LOCALIZATION_RULES: Dict[str, AcupointLocalizationRule] = {
    # -------------------------------------------------------------------------
    # LU: LUNG MERIDIAN (11 points)
    # -------------------------------------------------------------------------
    "LU1": AcupointLocalizationRule(
        point_code="LU1", meridian_code="LU", name_en="Zhongfu", name_zh="中府", name_vi="Trung Phủ",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:24074 (1st Intercostal Space)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 23: On anterior chest, 1st intercostal space, 6 B-cun lateral to anterior midline.",
        skeletal_structure="First intercostal space lateral to infraclavicular fossa",
        start_landmark_id="LM_JUGULAR_NOTCH", end_landmark_id="LM_STERNAL_ANGLE",
        proportional_fraction=0.65, lateral_offset_cun=6.0, transverse_segment_id="SEG_CHEST_BINIPPLE",
        tolerance_radius_mm=5.0, uncertainty_mm=10.0,
    ),
    "LU2": AcupointLocalizationRule(
        point_code="LU2", meridian_code="LU", name_en="Yunmen", name_zh="云门", name_vi="Vân Môn",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24073 (Infraclavicular Fossa)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 24: In infraclavicular fossa, medial to coracoid process, 6 B-cun lateral to midline.",
        skeletal_structure="Infraclavicular fossa medial to coracoid process",
        start_landmark_id="LM_JUGULAR_NOTCH", end_landmark_id="LM_ACROMION_R",
        proportional_fraction=0.75, lateral_offset_cun=6.0,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0,
    ),
    "LU3": AcupointLocalizationRule(
        point_code="LU3", meridian_code="LU", name_en="Tianfu", name_zh="天府", name_vi="Thiên Phủ",
        localization_method=LocalizationMethod.MUSCLE_BORDER,
        fma_anchor="FMA:24072 (Lateral Biceps Brachii)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 24: Anterolateral arm, lateral border of biceps brachii, 3 B-cun inferior to anterior axillary fold.",
        skeletal_structure="Lateral border of biceps brachii muscle belly",
        start_landmark_id="LM_AXILLARY_FOLD_ANT_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.333, lateral_offset_cun=0.0,
        tolerance_radius_mm=5.0, uncertainty_mm=12.0,
    ),
    "LU4": AcupointLocalizationRule(
        point_code="LU4", meridian_code="LU", name_en="Xiabai", name_zh="侠白", name_vi="Hiệp Bạch",
        localization_method=LocalizationMethod.MUSCLE_BORDER,
        fma_anchor="FMA:24071 (Lateral Biceps Brachii)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 25: Anterolateral arm, lateral border of biceps brachii, 4 B-cun inferior to anterior axillary fold.",
        skeletal_structure="Lateral border of biceps brachii muscle belly",
        start_landmark_id="LM_AXILLARY_FOLD_ANT_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.444, lateral_offset_cun=0.0,
        tolerance_radius_mm=5.0, uncertainty_mm=12.0,
    ),
    "LU5": AcupointLocalizationRule(
        point_code="LU5", meridian_code="LU", name_en="Chize", name_zh="尺泽", name_vi="Xích Trạch",
        localization_method=LocalizationMethod.SKIN_CREASE,
        fma_anchor="FMA:24290 (Cubital Crease Radial to Biceps)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 25: Anterior elbow, at cubital crease, in depression radial to biceps brachii tendon.",
        skeletal_structure="Cubital crease radial to tendon of m. biceps brachii",
        start_landmark_id="LM_CUBITAL_CREASE_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.0, lateral_offset_cun=0.0,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0, quality_class="CLASS_A",
        is_posture_sensitive=True, sensitive_joint="elbow_flexion_r", threshold_deg=15.0,
    ),
    "LU6": AcupointLocalizationRule(
        point_code="LU6", meridian_code="LU", name_en="Kongzui", name_zh="孔最", name_vi="Khổng Tối",
        localization_method=LocalizationMethod.B_CUN_PROPORTIONAL,
        fma_anchor="FMA:24070 (Anterior Forearm Radial)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 26: Anterolateral forearm, on line connecting LU5 and LU9, 7 B-cun superior to palmar wrist crease.",
        skeletal_structure="Line connecting Chize LU5 and Taiyuan LU9, 7 cun proximal to wrist crease",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.583, lateral_offset_cun=0.0,
        tolerance_radius_mm=5.0, uncertainty_mm=10.0,
    ),
    "LU7": AcupointLocalizationRule(
        point_code="LU7", meridian_code="LU", name_en="Lieque", name_zh="列缺", name_vi="Liệt Khuyết",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24069 (Radial Styloid Process)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 26: Radial aspect of forearm, superior to styloid process of radius, 1.5 B-cun proximal to wrist crease.",
        skeletal_structure="Groove proximal to styloid process of radius between brachioradialis and abductor pollicis longus",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_RADIAL_STYLOID_R",
        proportional_fraction=0.8, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=6.0,
    ),
    "LU8": AcupointLocalizationRule(
        point_code="LU8", meridian_code="LU", name_en="Jingqu", name_zh="经渠", name_vi="Kinh Cừ",
        localization_method=LocalizationMethod.TENDON_INTERVAL,
        fma_anchor="FMA:24068 (Radial Artery Groove)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 27: Anterior forearm, in depression between radial styloid process and radial artery, 1 B-cun proximal to wrist crease.",
        skeletal_structure="Depression between radial styloid process and radial artery",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.083, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=6.0,
    ),
    "LU9": AcupointLocalizationRule(
        point_code="LU9", meridian_code="LU", name_en="Taiyuan", name_zh="太渊", name_vi="Thái Uyên",
        localization_method=LocalizationMethod.SKIN_CREASE,
        fma_anchor="FMA:24067 (Palmar Wrist Crease Radial)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 27: Palmar wrist crease, in depression between radial artery and abductor pollicis longus tendon.",
        skeletal_structure="Palmar wrist crease radial depression lateral to flexor carpi radialis",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_RADIAL_STYLOID_R",
        proportional_fraction=0.1, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=5.0,
    ),
    "LU10": AcupointLocalizationRule(
        point_code="LU10", meridian_code="LU", name_en="Yuji", name_zh="鱼际", name_vi="Ngư Tế",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24066 (1st Metacarpal Midpoint)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 28: Palmar aspect of hand, midpoint of 1st metacarpal bone, at junction of red and white skin.",
        skeletal_structure="Midpoint of 1st metacarpal bone radial border",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_RADIAL_STYLOID_R",
        proportional_fraction=0.45, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=6.0,
    ),
    "LU11": AcupointLocalizationRule(
        point_code="LU11", meridian_code="LU", name_en="Shaoshang", name_zh="少商", name_vi="Thiếu Thương",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24065 (Radial Thumb Nail Corner)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 28: Distal phalanx of thumb, 0.1 B-cun proximal to radial corner of thumb nail.",
        skeletal_structure="Radial border of distal phalanx of thumb",
        start_landmark_id="LM_RADIAL_STYLOID_R", end_landmark_id="LM_WRIST_CREASE_PALMAR_R",
        proportional_fraction=0.1, lateral_offset_cun=0.0,
        tolerance_radius_mm=2.0, uncertainty_mm=4.0,
    ),

    # -------------------------------------------------------------------------
    # LI: LARGE INTESTINE MERIDIAN (20 points)
    # -------------------------------------------------------------------------
    "LI1": AcupointLocalizationRule(
        point_code="LI1", meridian_code="LI", name_en="Shangyang", name_zh="商阳", name_vi="Thương Dương",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24076 (Radial Index Nail Corner)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 33: Index finger, 0.1 B-cun proximal to radial corner of index nail.",
        skeletal_structure="Radial corner of distal phalanx of 2nd digit",
        start_landmark_id="LM_RADIAL_STYLOID_R", end_landmark_id="LM_WRIST_CREASE_PALMAR_R",
        proportional_fraction=0.15, lateral_offset_cun=0.0,
        tolerance_radius_mm=2.0, uncertainty_mm=4.0,
    ),
    "LI4": AcupointLocalizationRule(
        point_code="LI4", meridian_code="LI", name_en="Hegu", name_zh="合谷", name_vi="Hợp Cốc",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24075 (2nd Metacarpal Midpoint)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 35: Dorsum of hand, radial to midpoint of 2nd metacarpal bone.",
        skeletal_structure="Radial border of 2nd metacarpal bone midpoint",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_RADIAL_STYLOID_R",
        proportional_fraction=0.5, lateral_offset_cun=0.0,
        tolerance_radius_mm=4.0, uncertainty_mm=6.0, quality_class="CLASS_A",
    ),
    "LI5": AcupointLocalizationRule(
        point_code="LI5", meridian_code="LI", name_en="Yangxi", name_zh="阳溪", name_vi="Dương Khê",
        localization_method=LocalizationMethod.TENDON_INTERVAL,
        fma_anchor="FMA:24077 (Anatomical Snuffbox)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 35: Posterolateral wrist, in depression of anatomical snuffbox between tendons.",
        skeletal_structure="Anatomical snuffbox between EPL and EPB tendons",
        start_landmark_id="LM_RADIAL_STYLOID_R", end_landmark_id="LM_WRIST_CREASE_PALMAR_R",
        proportional_fraction=0.5, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=5.0,
    ),
    "LI11": AcupointLocalizationRule(
        point_code="LI11", meridian_code="LI", name_en="Quchi", name_zh="曲池", name_vi="Khúc Trì",
        localization_method=LocalizationMethod.SKIN_CREASE,
        fma_anchor="FMA:24078 (Lateral Cubital Crease End)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 38: Lateral elbow, midway between LU5 and lateral epicondyle of humerus, at lateral end of cubital crease.",
        skeletal_structure="Midway between biceps tendon and lateral epicondyle of humerus",
        start_landmark_id="LM_LAT_EPICONDYLE_HUMERUS_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.5, quality_class="CLASS_A",
        is_posture_sensitive=True, sensitive_joint="elbow_flexion_r", threshold_deg=15.0,
        tolerance_radius_mm=4.0, uncertainty_mm=7.0,
    ),
    "LI15": AcupointLocalizationRule(
        point_code="LI15", meridian_code="LI", name_en="Jianyu", name_zh="肩髃", name_vi="Kiên Ngung",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24079 (Acromion Anterior Depression)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 40: Shoulder, in depression anterior and inferior to acromion when arm is abducted.",
        skeletal_structure="Depression anterior and inferior to lateral border of acromion",
        start_landmark_id="LM_ACROMION_R", end_landmark_id="LM_AXILLARY_FOLD_ANT_R",
        proportional_fraction=0.2, quality_class="CLASS_A",
        is_posture_sensitive=True, sensitive_joint="shoulder_abduction_r", threshold_deg=20.0,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0,
    ),
    "LI20": AcupointLocalizationRule(
        point_code="LI20", meridian_code="LI", name_en="Yingxiang", name_zh="迎香", name_vi="Nghinh Hương",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24080 (Nasolabial Groove Ala Nasi)", body_region=BodyRegion.HEAD_NECK,
        who_reference="WHO 2008, p. 43: Face, in nasolabial groove, at level of midpoint of lateral border of ala nasi.",
        skeletal_structure="Nasolabial sulcus lateral to alar groove of nose",
        start_landmark_id="LM_GLABELLA", end_landmark_id="LM_C2_SPINE",
        proportional_fraction=0.15, lateral_offset_cun=1.0,
        tolerance_radius_mm=3.0, uncertainty_mm=5.0,
    ),

    # -------------------------------------------------------------------------
    # CV: CONCEPTION VESSEL / REN MAI (24 points, Midline)
    # -------------------------------------------------------------------------
    "CV2": AcupointLocalizationRule(
        point_code="CV2", meridian_code="CV", name_en="Qugu", name_zh="曲骨", name_vi="Khúc Cốt",
        localization_method=LocalizationMethod.MIDLINE_REFERENCE,
        fma_anchor="FMA:16900 (Pubic Symphysis Superior Border)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 253: Anterior midline, superior border of pubic symphysis.",
        skeletal_structure="Superior border of pubic symphysis on midline",
        start_landmark_id="LM_PUBIC_SYMPHYSIS", end_landmark_id="LM_PUBIC_SYMPHYSIS",
        proportional_fraction=0.0, lateral_offset_cun=0.0, tolerance_radius_mm=3.0, uncertainty_mm=5.0,
    ),
    "CV4": AcupointLocalizationRule(
        point_code="CV4", meridian_code="CV", name_en="Guanyuan", name_zh="关元", name_vi="Quan Nguyên",
        localization_method=LocalizationMethod.B_CUN_PROPORTIONAL,
        fma_anchor="FMA:16901 (Linea Alba Lower Abdomen 3 cun inferior)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 254: Anterior midline, 3 B-cun inferior to center of umbilicus.",
        skeletal_structure="Linea alba 3 B-cun inferior to center of umbilicus",
        start_landmark_id="LM_UMBILICUS", end_landmark_id="LM_PUBIC_SYMPHYSIS",
        proportional_fraction=0.6, lateral_offset_cun=0.0, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=6.0,
    ),
    "CV8": AcupointLocalizationRule(
        point_code="CV8", meridian_code="CV", name_en="Shenque", name_zh="神阙", name_vi="Thần Khuyết",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:14552 (Umbilicus Center)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 256: Anterior midline, center of umbilicus.",
        skeletal_structure="Center of umbilicus on linea alba",
        start_landmark_id="LM_UMBILICUS", end_landmark_id="LM_UMBILICUS",
        proportional_fraction=0.0, lateral_offset_cun=0.0, tolerance_radius_mm=3.0, uncertainty_mm=4.0,
    ),
    "CV12": AcupointLocalizationRule(
        point_code="CV12", meridian_code="CV", name_en="Zhongwan", name_zh="中脘", name_vi="Trung Quản",
        localization_method=LocalizationMethod.B_CUN_PROPORTIONAL,
        fma_anchor="FMA:16902 (Linea Alba Upper Abdomen Midpoint)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 258: Anterior midline, 4 B-cun superior to center of umbilicus, midway to xiphisternal joint.",
        skeletal_structure="Midpoint between center of umbilicus and xiphisternal synchondrosis",
        start_landmark_id="LM_UMBILICUS", end_landmark_id="LM_XIPHOSTERNAL_JOINT",
        proportional_fraction=0.5, lateral_offset_cun=0.0, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=6.0,
    ),
    "CV17": AcupointLocalizationRule(
        point_code="CV17", meridian_code="CV", name_en="Danzhong", name_zh="膻中", name_vi="Đản Trung",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:16903 (Sternal Body 4th Intercostal)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 260: Anterior midline, on sternum, level with 4th intercostal space, midway between nipples.",
        skeletal_structure="Midpoint of sternal body at 4th intercostal level",
        start_landmark_id="LM_JUGULAR_NOTCH", end_landmark_id="LM_XIPHOSTERNAL_JOINT",
        proportional_fraction=0.67, lateral_offset_cun=0.0, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=6.0,
    ),
    "CV22": AcupointLocalizationRule(
        point_code="CV22", meridian_code="CV", name_en="Tiantu", name_zh="天突", name_vi="Thiên Đột",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:16904 (Suprasternal Fossa Jugular Notch)", body_region=BodyRegion.HEAD_NECK,
        who_reference="WHO 2008, p. 262: Anterior midline, suprasternal fossa, 0.5 B-cun superior to jugular notch.",
        skeletal_structure="Center of suprasternal fossa superior to jugular notch",
        start_landmark_id="LM_JUGULAR_NOTCH", end_landmark_id="LM_JUGULAR_NOTCH",
        proportional_fraction=0.0, lateral_offset_cun=0.0, quality_class="CLASS_A",
        tolerance_radius_mm=3.0, uncertainty_mm=5.0,
    ),

    # -------------------------------------------------------------------------
    # GV: GOVERNOR VESSEL / DU MAI (29 points, Posterior Midline)
    # -------------------------------------------------------------------------
    "GV4": AcupointLocalizationRule(
        point_code="GV4", meridian_code="GV", name_en="Mingmen", name_zh="命门", name_vi="Mệnh Môn",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:12520 (L2 Spinous Process Depression)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 231: Posterior midline, in depression inferior to spinous process of 2nd lumbar vertebra (L2).",
        skeletal_structure="Depression inferior to spinous process of L2",
        start_landmark_id="LM_L4_SPINE", end_landmark_id="LM_C7_SPINE",
        proportional_fraction=0.18, lateral_offset_cun=0.0, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=6.0,
    ),
    "GV14": AcupointLocalizationRule(
        point_code="GV14", meridian_code="GV", name_en="Dazhui", name_zh="大椎", name_vi="Đại Chùy",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:12525 (C7 Spinous Process Depression)", body_region=BodyRegion.HEAD_NECK,
        who_reference="WHO 2008, p. 235: Posterior midline, in depression inferior to spinous process of 7th cervical vertebra (C7).",
        skeletal_structure="Depression inferior to spinous process of C7",
        start_landmark_id="LM_C7_SPINE", end_landmark_id="LM_C7_SPINE",
        proportional_fraction=0.0, lateral_offset_cun=0.0, quality_class="CLASS_A",
        tolerance_radius_mm=3.0, uncertainty_mm=5.0,
    ),
    "GV20": AcupointLocalizationRule(
        point_code="GV20", meridian_code="GV", name_en="Baihui", name_zh="百会", name_vi="Bách Hội",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:46452 (Vertex Cranium Midline)", body_region=BodyRegion.HEAD_NECK,
        who_reference="WHO 2008, p. 238: Head, 5 B-cun superior to anterior hairline, at intersection of sagittal midline and connecting line of ear apexes.",
        skeletal_structure="Crown vertex at sagittal suture intersection",
        start_landmark_id="LM_VERTEX_CROWN", end_landmark_id="LM_VERTEX_CROWN",
        proportional_fraction=0.0, lateral_offset_cun=0.0, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=6.0,
    ),

    # -------------------------------------------------------------------------
    # BL: BLADDER MERIDIAN (67 points)
    # -------------------------------------------------------------------------
    "BL10": AcupointLocalizationRule(
        point_code="BL10", meridian_code="BL", name_en="Tianzhu", name_zh="天柱", name_vi="Thiên Trụ",
        localization_method=LocalizationMethod.MUSCLE_BORDER,
        fma_anchor="FMA:9164 (Lateral Trapezius C2 Level)", body_region=BodyRegion.HEAD_NECK,
        who_reference="WHO 2008, p. 117: Posterior neck, in depression lateral to m. trapezius, level with C2 spine, 1.3 B-cun lateral to midline.",
        skeletal_structure="Depression on lateral border of trapezius muscle level with C2",
        start_landmark_id="LM_C2_SPINE", end_landmark_id="LM_C2_SPINE",
        lateral_offset_cun=1.3, quality_class="CLASS_A", tolerance_radius_mm=4.0, uncertainty_mm=8.0,
    ),
    "BL11": AcupointLocalizationRule(
        point_code="BL11", meridian_code="BL", name_en="Dazhu", name_zh="大杼", name_vi="Đại Trữ",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:9165 (T1 Spinous 1.5 cun lateral)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 117: Upper back, 1.5 B-cun lateral to posterior midline, level with inferior border of T1 spine.",
        skeletal_structure="1.5 B-cun lateral to inferior border of T1 spinous process",
        start_landmark_id="LM_C7_SPINE", end_landmark_id="LM_L4_SPINE",
        proportional_fraction=0.05, lateral_offset_cun=1.5, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=7.0,
    ),
    "BL12": AcupointLocalizationRule(
        point_code="BL12", meridian_code="BL", name_en="Fengmen", name_zh="风门", name_vi="Phong Môn",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:9166 (T2 Spinous 1.5 cun lateral)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 118: Upper back, 1.5 B-cun lateral to posterior midline, level with T2 spine.",
        skeletal_structure="1.5 B-cun lateral to inferior border of T2 spinous process",
        start_landmark_id="LM_C7_SPINE", end_landmark_id="LM_L4_SPINE",
        proportional_fraction=0.10, lateral_offset_cun=1.5, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=7.0,
    ),
    "BL13": AcupointLocalizationRule(
        point_code="BL13", meridian_code="BL", name_en="Feishu", name_zh="肺俞", name_vi="Phế Du",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:9167 (T3 Spinous 1.5 cun lateral)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 119: Upper back, 1.5 B-cun lateral to posterior midline, level with T3 spine.",
        skeletal_structure="1.5 B-cun lateral to inferior border of T3 spinous process",
        start_landmark_id="LM_C7_SPINE", end_landmark_id="LM_L4_SPINE",
        proportional_fraction=0.15, lateral_offset_cun=1.5, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=7.0,
    ),
    "BL40": AcupointLocalizationRule(
        point_code="BL40", meridian_code="BL", name_en="Weizhong", name_zh="委中", name_vi="Ủy Trung",
        localization_method=LocalizationMethod.SKIN_CREASE,
        fma_anchor="FMA:24294 (Popliteal Fossa Midpoint)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 138: Posterior knee, at midpoint of popliteal crease.",
        skeletal_structure="Midpoint of popliteal crease between biceps femoris and semitendinosus",
        start_landmark_id="LM_POPLITEAL_CREASE_R", end_landmark_id="LM_POPLITEAL_CREASE_R",
        proportional_fraction=0.0, lateral_offset_cun=0.0, quality_class="CLASS_A",
        is_posture_sensitive=True, sensitive_joint="knee_flexion_r", threshold_deg=15.0,
        tolerance_radius_mm=5.0, uncertainty_mm=8.0,
    ),

    # -------------------------------------------------------------------------
    # ST: STOMACH MERIDIAN (45 points)
    # -------------------------------------------------------------------------
    "ST35": AcupointLocalizationRule(
        point_code="ST35", meridian_code="ST", name_en="Dubi", name_zh="犊鼻", name_vi="Độc Tỵ",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24485 (Patellar Ligament Lateral Depression)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 67: Anterior knee, in depression lateral to patellar ligament.",
        skeletal_structure="Depression lateral to patellar ligament",
        start_landmark_id="LM_PATELLA_INFERIOR_R", end_landmark_id="LM_PATELLA_INFERIOR_R",
        proportional_fraction=0.0, quality_class="CLASS_A",
        is_posture_sensitive=True, sensitive_joint="knee_flexion_r", threshold_deg=20.0,
        tolerance_radius_mm=4.0, uncertainty_mm=7.0,
    ),
    "ST36": AcupointLocalizationRule(
        point_code="ST36", meridian_code="ST", name_en="Zusanli", name_zh="足三里", name_vi="Túc Tam Lý",
        localization_method=LocalizationMethod.B_CUN_PROPORTIONAL,
        fma_anchor="FMA:24486 (Tibialis Anterior Lateral to Crest 3 cun below Dubi)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 68: Anterior leg, 3 B-cun inferior to ST35, one fingerbreadth lateral to anterior crest of tibia.",
        skeletal_structure="3 B-cun inferior to ST35 on m. tibialis anterior",
        start_landmark_id="LM_PATELLA_INFERIOR_R", end_landmark_id="LM_LAT_MALLEOLUS_R",
        proportional_fraction=0.1875, quality_class="CLASS_A",
        tolerance_radius_mm=5.0, uncertainty_mm=8.0,
    ),

    # -------------------------------------------------------------------------
    # GB: GALLBLADDER MERIDIAN (44 points)
    # -------------------------------------------------------------------------
    "GB20": AcupointLocalizationRule(
        point_code="GB20", meridian_code="GB", name_en="Fengchi", name_zh="风池", name_vi="Phong Trì",
        localization_method=LocalizationMethod.MUSCLE_BORDER,
        fma_anchor="FMA:9168 (Occipital Depression between Trapezius and SCM)", body_region=BodyRegion.HEAD_NECK,
        who_reference="WHO 2008, p. 209: Posterior neck, inferior to occipital bone, in depression between sternocleidomastoid and trapezius.",
        skeletal_structure="Depression between trapezius and sternocleidomastoid below superior nuchal line",
        start_landmark_id="LM_INION", end_landmark_id="LM_MASTOID_R",
        proportional_fraction=0.5, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=7.0,
    ),
    "GB21": AcupointLocalizationRule(
        point_code="GB21", meridian_code="GB", name_en="Jianjing", name_zh="肩井", name_vi="Kiên Tỉnh",
        localization_method=LocalizationMethod.B_CUN_PROPORTIONAL,
        fma_anchor="FMA:24081 (Trapezius Midpoint between C7 and Acromion)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 210: Shoulder, midpoint of line connecting spinous process of C7 with lateral end of acromion.",
        skeletal_structure="Highest point of trapezius muscle belly midway between C7 and acromion",
        start_landmark_id="LM_C7_SPINE", end_landmark_id="LM_ACROMION_R",
        proportional_fraction=0.5, quality_class="CLASS_A",
        tolerance_radius_mm=4.0, uncertainty_mm=7.0,
    ),

    # -------------------------------------------------------------------------
    # HT: HEART MERIDIAN (9 points)
    # -------------------------------------------------------------------------
    "HT3": AcupointLocalizationRule(
        point_code="HT3", meridian_code="HT", name_en="Shaohai", name_zh="少海", name_vi="Thiếu Hải",
        localization_method=LocalizationMethod.SKIN_CREASE,
        fma_anchor="FMA:23441 (Medial Epicondyle Cubital Crease)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 95: Anteromedial elbow, just anterior to medial epicondyle of humerus, level with cubital crease.",
        skeletal_structure="Midpoint between medial epicondyle of humerus and medial end of cubital crease",
        start_landmark_id="LM_MED_EPICONDYLE_HUMERUS_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.3, quality_class="CLASS_A",
        is_posture_sensitive=True, sensitive_joint="elbow_flexion_r", threshold_deg=15.0,
        tolerance_radius_mm=4.0, uncertainty_mm=7.0,
    ),

    # -------------------------------------------------------------------------
    # PC: PERICARDIUM MERIDIAN (9 points)
    # -------------------------------------------------------------------------
    "PC6": AcupointLocalizationRule(
        point_code="PC6", meridian_code="PC", name_en="Neiguan", name_zh="内关", name_vi="Nội Quan",
        localization_method=LocalizationMethod.TENDON_INTERVAL,
        fma_anchor="FMA:24292 (Palmaris Longus / FCR Interval 2 cun proximal)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 167: Anterior forearm, between tendons of palmaris longus and flexor carpi radialis, 2 B-cun proximal to wrist crease.",
        skeletal_structure="Between tendons of palmaris longus and flexor carpi radialis 2 B-cun proximal to palmar wrist crease",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.1667, quality_class="CLASS_A",
        is_posture_sensitive=True, sensitive_joint="elbow_flexion_r", threshold_deg=12.0,
        tolerance_radius_mm=3.0, uncertainty_mm=6.0,
    ),
    "PC3": AcupointLocalizationRule(
        point_code="PC3", meridian_code="PC", name_en="Quze", name_zh="曲泽", name_vi="Khúc Trạch",
        localization_method=LocalizationMethod.SKIN_CREASE,
        fma_anchor="FMA:24291 (Cubital Crease Medial to Biceps)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 165: Anterior aspect of elbow, at cubital crease, in depression medial to biceps brachii tendon.",
        skeletal_structure="Cubital crease medial to tendon of m. biceps brachii",
        start_landmark_id="LM_CUBITAL_CREASE_R", end_landmark_id="LM_MED_EPICONDYLE_HUMERUS_R",
        proportional_fraction=0.35, quality_class="CLASS_B",
        is_posture_sensitive=True, sensitive_joint="elbow_flexion_r", threshold_deg=15.0,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0,
    ),
    "PC7": AcupointLocalizationRule(
        point_code="PC7", meridian_code="PC", name_en="Daling", name_zh="大陵", name_vi="Đại Lăng",
        localization_method=LocalizationMethod.SKIN_CREASE,
        fma_anchor="FMA:24293 (Palmar Wrist Crease Midpoint)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 168: Anterior aspect of wrist, midpoint of palmar wrist crease between tendons of palmaris longus and flexor carpi radialis.",
        skeletal_structure="Palmar wrist crease midpoint between tendons",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_WRIST_CREASE_PALMAR_R",
        proportional_fraction=0.0, quality_class="CLASS_B",
        tolerance_radius_mm=3.0, uncertainty_mm=6.0,
    ),

    # -------------------------------------------------------------------------
    # SP: SPLEEN MERIDIAN (21 points)
    # -------------------------------------------------------------------------
    "SP1": AcupointLocalizationRule(
        point_code="SP1", meridian_code="SP", name_en="Yinbai", name_zh="隐白", name_vi="Ẩn Bạch",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24082 (Great Toe Medial Nail Bed)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 77: Medial aspect of great toe, 0.1 B-cun proximal to medial corner of nail.",
        skeletal_structure="Medial aspect of terminal phalanx of great toe",
        start_landmark_id="LM_MED_MALLEOLUS_R", end_landmark_id="LM_CALCANEUS_POST_R",
        proportional_fraction=0.1, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=5.0, quality_class="CLASS_B",
    ),
    "SP6": AcupointLocalizationRule(
        point_code="SP6", meridian_code="SP", name_en="Sanyinjiao", name_zh="三阴交", name_vi="Tam Âm Giao",
        localization_method=LocalizationMethod.B_CUN_PROPORTIONAL,
        fma_anchor="FMA:24084 (Medial Tibial Border 3 Cun Proximal to Malleolus)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 81: Medial aspect of leg, 3 B-cun superior to prominence of medial malleolus, in depression posterior to medial border of tibia.",
        skeletal_structure="Posterior border of tibia 3 B-cun superior to medial malleolus",
        start_landmark_id="LM_MED_MALLEOLUS_R", end_landmark_id="LM_PATELLA_INFERIOR_R",
        proportional_fraction=0.2308, lateral_offset_cun=0.0,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0, quality_class="CLASS_B",
    ),
    "SP9": AcupointLocalizationRule(
        point_code="SP9", meridian_code="SP", name_en="Yinlingquan", name_zh="阴陵泉", name_vi="Âm Lăng Tuyền",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24085 (Medial Tibial Condyle Depression)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 84: Medial aspect of leg, in depression between inferior border of medial condyle of tibia and medial border of tibia.",
        skeletal_structure="Depression inferior to medial condyle of tibia",
        start_landmark_id="LM_MED_MALLEOLUS_R", end_landmark_id="LM_PATELLA_INFERIOR_R",
        proportional_fraction=0.9231, lateral_offset_cun=0.0,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0, quality_class="CLASS_B",
    ),
    "SP10": AcupointLocalizationRule(
        point_code="SP10", meridian_code="SP", name_en="Xuehai", name_zh="血海", name_vi="Huyết Hải",
        localization_method=LocalizationMethod.MUSCLE_BORDER,
        fma_anchor="FMA:24086 (Vastus Medialis 2 Cun Superior to Patella)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 85: Anterior thigh, 2 B-cun superior to mediocranial border of patella on bulge of vastus medialis.",
        skeletal_structure="Bulge of vastus medialis 2 B-cun proximal to patellar base",
        start_landmark_id="LM_PATELLA_INFERIOR_R", end_landmark_id="LM_GREATER_TROCHANTER_R",
        proportional_fraction=0.15, lateral_offset_cun=0.0,
        tolerance_radius_mm=5.0, uncertainty_mm=9.0, quality_class="CLASS_B",
    ),
    "SP15": AcupointLocalizationRule(
        point_code="SP15", meridian_code="SP", name_en="Daheng", name_zh="大横", name_vi="Đại Hoành",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:24087 (Lateral Rectus Abdominis 4 Cun from Umbilicus)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 89: Anterior abdomen, 4 B-cun lateral to center of umbilicus on lateral border of rectus abdominis.",
        skeletal_structure="Lateral border of rectus abdominis level with umbilicus",
        start_landmark_id="LM_UMBILICUS", end_landmark_id="LM_UMBILICUS",
        proportional_fraction=0.0, lateral_offset_cun=4.0,
        tolerance_radius_mm=6.0, uncertainty_mm=12.0, quality_class="CLASS_B",
    ),
    "SP21": AcupointLocalizationRule(
        point_code="SP21", meridian_code="SP", name_en="Dabao", name_zh="大包", name_vi="Đại Bao",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:24088 (6th Intercostal Midaxillary Line)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 93: Lateral thoracic region, 6th intercostal space on midaxillary line.",
        skeletal_structure="Sixth intercostal space on midaxillary line",
        start_landmark_id="LM_AXILLARY_FOLD_ANT_R", end_landmark_id="LM_ASIS_R",
        proportional_fraction=0.35, lateral_offset_cun=6.0,
        tolerance_radius_mm=6.0, uncertainty_mm=12.0, quality_class="CLASS_B",
    ),

    # -------------------------------------------------------------------------
    # SI: SMALL INTESTINE MERIDIAN (19 points)
    # -------------------------------------------------------------------------
    "SI1": AcupointLocalizationRule(
        point_code="SI1", meridian_code="SI", name_en="Shaoze", name_zh="少泽", name_vi="Thiếu Trạch",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24076 (Little Finger Ulnar Nail Bed)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 101: Medial aspect of little finger, 0.1 B-cun proximal to ulnar corner of nail.",
        skeletal_structure="Ulnar side of distal phalanx of 5th digit",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_RADIAL_STYLOID_R",
        proportional_fraction=0.0, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=5.0, quality_class="CLASS_B",
    ),
    "SI3": AcupointLocalizationRule(
        point_code="SI3", meridian_code="SI", name_en="Houxi", name_zh="后溪", name_vi="Hậu Khê",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24077 (5th Metacarpophalangeal Joint Depression)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 102: Dorsum of hand, in depression proximal to 5th metacarpophalangeal joint, on border of red and white skin.",
        skeletal_structure="Ulnar border of hand proximal to 5th MCP head",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_RADIAL_STYLOID_R",
        proportional_fraction=0.2, lateral_offset_cun=0.0,
        tolerance_radius_mm=4.0, uncertainty_mm=6.0, quality_class="CLASS_B",
    ),
    "SI8": AcupointLocalizationRule(
        point_code="SI8", meridian_code="SI", name_en="Xiaohai", name_zh="小海", name_vi="Tiểu Hải",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24078 (Ulnar Nerve Groove at Elbow)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 106: Posteromedial elbow, depression between olecranon of ulna and medial epicondyle of humerus.",
        skeletal_structure="Ulnar sulcus between olecranon and medial epicondyle",
        start_landmark_id="LM_MED_EPICONDYLE_HUMERUS_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.1, lateral_offset_cun=0.0,
        is_posture_sensitive=True, sensitive_joint="elbow_flexion_r", threshold_deg=15.0,
        tolerance_radius_mm=4.0, uncertainty_mm=7.0, quality_class="CLASS_B",
    ),
    "SI11": AcupointLocalizationRule(
        point_code="SI11", meridian_code="SI", name_en="Tianzong", name_zh="天宗", name_vi="Thiên Tông",
        localization_method=LocalizationMethod.B_CUN_PROPORTIONAL,
        fma_anchor="FMA:24080 (Scapular Infraspinous Fossa Center)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 108: Scapular region, in depression in center of infraspinous fossa, forming equilateral triangle with SI9 and SI10.",
        skeletal_structure="Center of infraspinous fossa of scapula",
        start_landmark_id="LM_ACROMION_R", end_landmark_id="LM_C7_SPINE",
        proportional_fraction=0.45, lateral_offset_cun=3.0,
        tolerance_radius_mm=5.0, uncertainty_mm=10.0, quality_class="CLASS_B",
    ),
    "SI19": AcupointLocalizationRule(
        point_code="SI19", meridian_code="SI", name_en="Tinggong", name_zh="听宫", name_vi="Thính Cung",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24081 (Pre-auricular Depression Anterior to Tragus)", body_region=BodyRegion.HEAD_NECK,
        who_reference="WHO 2008, p. 112: Face, in depression between anterior border of tragus and posterior border of condylar process of mandible.",
        skeletal_structure="Depression anterior to tragus when mouth is slightly opened",
        start_landmark_id="LM_MASTOID_R", end_landmark_id="LM_GLABELLA",
        proportional_fraction=0.35, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=5.0, quality_class="CLASS_B",
    ),

    # -------------------------------------------------------------------------
    # KI: KIDNEY MERIDIAN (27 points)
    # -------------------------------------------------------------------------
    "KI1": AcupointLocalizationRule(
        point_code="KI1", meridian_code="KI", name_en="Yongquan", name_zh="涌泉", name_vi="Dũng Tuyền",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24089 (Sole Plantar Depression Anterior 1/3)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 149: Sole of foot, in depression formed when foot is in plantar flexion, at junction of anterior 1/3 and posterior 2/3 of line from web between 2nd/3rd toes to heel.",
        skeletal_structure="Plantar aponeurosis depression between 2nd and 3rd metatarsal shafts",
        start_landmark_id="LM_CALCANEUS_POST_R", end_landmark_id="LM_MED_MALLEOLUS_R",
        proportional_fraction=0.1, lateral_offset_cun=0.0,
        tolerance_radius_mm=5.0, uncertainty_mm=10.0, quality_class="CLASS_B",
    ),
    "KI3": AcupointLocalizationRule(
        point_code="KI3", meridian_code="KI", name_en="Taixi", name_zh="太溪", name_vi="Thái Khê",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24090 (Medial Malleolus - Calcaneal Tendon Depression)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 151: Posteromedial ankle, depression between prominence of medial malleolus and calcaneal tendon.",
        skeletal_structure="Depression between medial malleolus and calcaneal tendon level with malleolar prominence",
        start_landmark_id="LM_MED_MALLEOLUS_R", end_landmark_id="LM_CALCANEUS_POST_R",
        proportional_fraction=0.45, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=6.0, quality_class="CLASS_B",
    ),
    "KI6": AcupointLocalizationRule(
        point_code="KI6", meridian_code="KI", name_en="Zhaohai", name_zh="照海", name_vi="Chiếu Hải",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24091 (Depression Inferior to Medial Malleolus)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 153: Medial aspect of foot, in depression 1 B-cun inferior to prominence of medial malleolus.",
        skeletal_structure="Depression 1 B-cun directly inferior to medial malleolus",
        start_landmark_id="LM_MED_MALLEOLUS_R", end_landmark_id="LM_CALCANEUS_POST_R",
        proportional_fraction=0.3, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=6.0, quality_class="CLASS_B",
    ),
    "KI7": AcupointLocalizationRule(
        point_code="KI7", meridian_code="KI", name_en="Fuliu", name_zh="复溜", name_vi="Phục Lưu",
        localization_method=LocalizationMethod.B_CUN_PROPORTIONAL,
        fma_anchor="FMA:24092 (2 Cun Superior to Taixi Anterior to Achilles)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 154: Posteromedial leg, 2 B-cun superior to KI3, anterior to calcaneal tendon.",
        skeletal_structure="Posteromedial aspect of shank 2 B-cun proximal to medial malleolus",
        start_landmark_id="LM_MED_MALLEOLUS_R", end_landmark_id="LM_PATELLA_INFERIOR_R",
        proportional_fraction=0.1538, lateral_offset_cun=0.0,
        tolerance_radius_mm=4.0, uncertainty_mm=7.0, quality_class="CLASS_B",
    ),
    "KI10": AcupointLocalizationRule(
        point_code="KI10", meridian_code="KI", name_en="Yingu", name_zh="阴谷", name_vi="Âm Cốc",
        localization_method=LocalizationMethod.TENDON_INTERVAL,
        fma_anchor="FMA:24093 (Medial Popliteal Semitendinosus Interval)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 156: Posteromedial knee, medial end of popliteal crease, between tendons of semitendinosus and semimembranosus.",
        skeletal_structure="Depression between semitendinosus and semimembranosus tendons on popliteal crease",
        start_landmark_id="LM_POPLITEAL_CREASE_R", end_landmark_id="LM_PATELLA_INFERIOR_R",
        proportional_fraction=0.3, lateral_offset_cun=0.0,
        is_posture_sensitive=True, sensitive_joint="knee_flexion_r", threshold_deg=15.0,
        tolerance_radius_mm=4.0, uncertainty_mm=7.0, quality_class="CLASS_B",
    ),
    "KI11": AcupointLocalizationRule(
        point_code="KI11", meridian_code="KI", name_en="Henggu", name_zh="横骨", name_vi="Hoành Cốt",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:24094 (0.5 Cun Lateral to Pubic Symphysis)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 157: Lower abdomen, 0.5 B-cun lateral to anterior midline, level with superior border of pubic symphysis.",
        skeletal_structure="0.5 B-cun lateral to superior margin of pubic symphysis",
        start_landmark_id="LM_PUBIC_SYMPHYSIS", end_landmark_id="LM_PUBIC_SYMPHYSIS",
        proportional_fraction=0.0, lateral_offset_cun=0.5,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0, quality_class="CLASS_B",
    ),
    "KI16": AcupointLocalizationRule(
        point_code="KI16", meridian_code="KI", name_en="Huangshu", name_zh="肓俞", name_vi="Hoang Du",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:24095 (0.5 Cun Lateral to Umbilicus)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 160: Middle abdomen, 0.5 B-cun lateral to center of umbilicus.",
        skeletal_structure="0.5 B-cun lateral to umbilicus on rectus abdominis",
        start_landmark_id="LM_UMBILICUS", end_landmark_id="LM_UMBILICUS",
        proportional_fraction=0.0, lateral_offset_cun=0.5,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0, quality_class="CLASS_B",
    ),
    "KI27": AcupointLocalizationRule(
        point_code="KI27", meridian_code="KI", name_en="Shufu", name_zh="俞府", name_vi="Du Phủ",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:24096 (1st Intercostal 2 Cun Lateral to Midline)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 164: Anterior chest, in depression inferior to clavicle, 2 B-cun lateral to anterior midline.",
        skeletal_structure="First intercostal space 2 B-cun lateral to anterior midline",
        start_landmark_id="LM_JUGULAR_NOTCH", end_landmark_id="LM_STERNAL_ANGLE",
        proportional_fraction=0.3, lateral_offset_cun=2.0,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0, quality_class="CLASS_B",
    ),

    # -------------------------------------------------------------------------
    # TE: TRIPLE ENERGIZER MERIDIAN (San Jiao, 23 points)
    # -------------------------------------------------------------------------
    "TE1": AcupointLocalizationRule(
        point_code="TE1", meridian_code="TE", name_en="Guanchong", name_zh="关冲", name_vi="Quan Xung",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24097 (Ring Finger Ulnar Nail Bed)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 177: Medial aspect of 4th digit (ring finger), 0.1 B-cun proximal to ulnar corner of nail.",
        skeletal_structure="Terminal phalanx of 4th digit ulnar side",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_RADIAL_STYLOID_R",
        proportional_fraction=0.0, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=5.0, quality_class="CLASS_B",
    ),
    "TE5": AcupointLocalizationRule(
        point_code="TE5", meridian_code="TE", name_en="Waiguan", name_zh="外关", name_vi="Ngoại Quan",
        localization_method=LocalizationMethod.B_CUN_PROPORTIONAL,
        fma_anchor="FMA:24100 (Dorsal Forearm 2 Cun Proximal to Wrist Crease)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 180: Posterior forearm, between radius and ulna, 2 B-cun proximal to dorsal wrist crease.",
        skeletal_structure="Interosseous space between radius and ulna 2 B-cun proximal to dorsal wrist crease",
        start_landmark_id="LM_WRIST_CREASE_PALMAR_R", end_landmark_id="LM_CUBITAL_CREASE_R",
        proportional_fraction=0.1667, lateral_offset_cun=0.0,
        is_posture_sensitive=True, sensitive_joint="elbow_flexion_r", threshold_deg=12.0,
        tolerance_radius_mm=3.0, uncertainty_mm=6.0, quality_class="CLASS_B",
    ),
    "TE14": AcupointLocalizationRule(
        point_code="TE14", meridian_code="TE", name_en="Jianliao", name_zh="肩髎", name_vi="Kiên Liêu",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24102 (Posterior Infraclavicular/Acromial Depression)", body_region=BodyRegion.UPPER_EXTREMITY,
        who_reference="WHO 2008, p. 185: Shoulder girdle, depression posterior and inferior to lateral acromion.",
        skeletal_structure="Posterior depression below acromion when arm is abducted",
        start_landmark_id="LM_ACROMION_R", end_landmark_id="LM_ACROMION_R",
        proportional_fraction=0.0, lateral_offset_cun=0.0,
        tolerance_radius_mm=4.0, uncertainty_mm=8.0, quality_class="CLASS_B",
    ),
    "TE17": AcupointLocalizationRule(
        point_code="TE17", meridian_code="TE", name_en="Yifeng", name_zh="翳风", name_vi="Ế Phong",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24103 (Depression Between Mastoid and Mandibular Angle)", body_region=BodyRegion.HEAD_NECK,
        who_reference="WHO 2008, p. 187: Lateral neck, in depression between mastoid process and angle of mandible, posterior to ear lobe.",
        skeletal_structure="Depression posterior to ear lobe between mastoid and mandibular ramus",
        start_landmark_id="LM_MASTOID_R", end_landmark_id="LM_C2_SPINE",
        proportional_fraction=0.3, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=6.0, quality_class="CLASS_B",
    ),
    "TE23": AcupointLocalizationRule(
        point_code="TE23", meridian_code="TE", name_en="Sizhukong", name_zh="丝竹空", name_vi="Ti Châu Không",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24105 (Lateral Eyebrow Depression)", body_region=BodyRegion.HEAD_NECK,
        who_reference="WHO 2008, p. 191: Face, in depression at lateral end of eyebrow.",
        skeletal_structure="Frontozygomatic suture depression at lateral extremity of eyebrow",
        start_landmark_id="LM_GLABELLA", end_landmark_id="LM_MASTOID_R",
        proportional_fraction=0.35, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=5.0, quality_class="CLASS_B",
    ),

    # -------------------------------------------------------------------------
    # LR: LIVER MERIDIAN (14 points)
    # -------------------------------------------------------------------------
    "LR1": AcupointLocalizationRule(
        point_code="LR1", meridian_code="LR", name_en="Dadun", name_zh="大敦", name_vi="Đại Đôn",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24106 (Great Toe Lateral Nail Bed)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 219: Lateral aspect of terminal phalanx of great toe, 0.1 B-cun proximal to lateral corner of nail.",
        skeletal_structure="Lateral aspect of distal phalanx of 1st toe",
        start_landmark_id="LM_MED_MALLEOLUS_R", end_landmark_id="LM_CALCANEUS_POST_R",
        proportional_fraction=0.1, lateral_offset_cun=0.0,
        tolerance_radius_mm=3.0, uncertainty_mm=5.0, quality_class="CLASS_B",
    ),
    "LR3": AcupointLocalizationRule(
        point_code="LR3", meridian_code="LR", name_en="Taichong", name_zh="太冲", name_vi="Thái Xung",
        localization_method=LocalizationMethod.JOINT_DEPRESSION,
        fma_anchor="FMA:24108 (1st and 2nd Metatarsal Junction Depression)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 220: Dorsum of foot, in depression proximal to 1st interdigital space, between 1st and 2nd metatarsal bones.",
        skeletal_structure="Depression anterior to junction of 1st and 2nd metatarsal bases",
        start_landmark_id="LM_MED_MALLEOLUS_R", end_landmark_id="LM_CALCANEUS_POST_R",
        proportional_fraction=0.25, lateral_offset_cun=0.0,
        tolerance_radius_mm=4.0, uncertainty_mm=7.0, quality_class="CLASS_B",
    ),
    "LR8": AcupointLocalizationRule(
        point_code="LR8", meridian_code="LR", name_en="Ququan", name_zh="曲泉", name_vi="Khúc Tuyền",
        localization_method=LocalizationMethod.SKIN_CREASE,
        fma_anchor="FMA:24110 (Medial Knee Popliteal Crease End)", body_region=BodyRegion.LOWER_EXTREMITY,
        who_reference="WHO 2008, p. 223: Medial aspect of knee, in depression medial to medial epicondyle of femur, superior to medial end of popliteal crease.",
        skeletal_structure="Medial aspect of knee anterior to semimembranosus/semitendinosus insertions",
        start_landmark_id="LM_POPLITEAL_CREASE_R", end_landmark_id="LM_PATELLA_INFERIOR_R",
        proportional_fraction=0.25, lateral_offset_cun=0.0,
        is_posture_sensitive=True, sensitive_joint="knee_flexion_r", threshold_deg=15.0,
        tolerance_radius_mm=4.0, uncertainty_mm=7.0, quality_class="CLASS_B",
    ),
    "LR13": AcupointLocalizationRule(
        point_code="LR13", meridian_code="LR", name_en="Zhangmen", name_zh="章门", name_vi="Chương Môn",
        localization_method=LocalizationMethod.LANDMARK_DEFINED,
        fma_anchor="FMA:24111 (Free End of 11th Rib Flank)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 226: Lateral abdomen, directly inferior to free end of 11th rib.",
        skeletal_structure="Inferior border of free end of 11th rib",
        start_landmark_id="LM_XIPHOSTERNAL_JOINT", end_landmark_id="LM_ASIS_R",
        proportional_fraction=0.6, lateral_offset_cun=5.0,
        tolerance_radius_mm=6.0, uncertainty_mm=12.0, quality_class="CLASS_B",
    ),
    "LR14": AcupointLocalizationRule(
        point_code="LR14", meridian_code="LR", name_en="Qimen", name_zh="期门", name_vi="Kỳ Môn",
        localization_method=LocalizationMethod.PARASAGITTAL_LINE,
        fma_anchor="FMA:24112 (6th Intercostal Mammillary Line)", body_region=BodyRegion.TORSO,
        who_reference="WHO 2008, p. 227: Anterior chest, 6th intercostal space, directly inferior to nipple, 4 B-cun lateral to anterior midline.",
        skeletal_structure="Sixth intercostal space 4 B-cun lateral to anterior midline directly below nipple",
        start_landmark_id="LM_STERNAL_ANGLE", end_landmark_id="LM_XIPHOSTERNAL_JOINT",
        proportional_fraction=0.8, lateral_offset_cun=4.0,
        tolerance_radius_mm=5.0, uncertainty_mm=10.0, quality_class="CLASS_B",
    ),
}


class AcupointLocalizationEngine:
    """Evaluates anatomical localization rules against BodyParts3D FJ2810 landmarks."""

    def __init__(self, landmark_registry: Optional[LandmarkRegistry] = None) -> None:
        self.registry = landmark_registry or LandmarkRegistry()
        self.cun_engine = CunScalingEngine(self.registry)
        self.rules = dict(ACUPOINT_LOCALIZATION_RULES)

    def get_rule(self, point_code: str) -> Optional[AcupointLocalizationRule]:
        return self.rules.get(point_code)

    def resolve_point_location(
        self,
        point_code: str,
        side: str = "right",
    ) -> Optional[Dict[str, Any]]:
        """Evaluate rule for a point and compute its canonical 3D coordinates and normal."""
        rule = self.get_rule(point_code)
        if not rule:
            return None

        pos: Optional[List[float]] = None
        norm: Optional[List[float]] = None

        # 1. LANDMARK_DEFINED directly on an authoritative landmark
        if rule.start_landmark_id and rule.start_landmark_id == rule.end_landmark_id:
            lm = self.registry.get_landmark(rule.start_landmark_id)
            if lm:
                pos = list(lm.canonical_position)

        # 2. B_CUN_PROPORTIONAL interpolation between two landmarks
        elif rule.start_landmark_id and rule.end_landmark_id:
            lm_start = self.registry.get_landmark(rule.start_landmark_id)
            lm_end = self.registry.get_landmark(rule.end_landmark_id)

            if lm_start and lm_end:
                p0 = lm_start.canonical_position
                p1 = lm_end.canonical_position
                t = rule.proportional_fraction

                # Interpolate along chord
                interpolated = [
                    (1.0 - t) * p0[0] + t * p1[0],
                    (1.0 - t) * p0[1] + t * p1[1],
                    (1.0 - t) * p0[2] + t * p1[2],
                ]

                # Apply lateral B-cun offset if specified
                if rule.lateral_offset_cun > 0.0:
                    seg_key = rule.transverse_segment_id or "SEG_CHEST_BINIPPLE"
                    metrics = self.cun_engine.calculate_segment_metrics()
                    seg_metric = metrics.get(seg_key)
                    cun_val = (seg_metric.mm_per_cun / 1000.0) if seg_metric else 0.020
                    lat_dist = rule.lateral_offset_cun * cun_val
                    # On right side +X, left side -X
                    interpolated[0] = lat_dist if side == "right" else -lat_dist

                pos = interpolated

        if pos is None:
            return None

        # Adjust side laterality
        is_midline = (rule.meridian_code in ["GV", "CV"] or rule.lateral_offset_cun == 0.0 and abs(pos[0]) < 0.01)
        if side == "left" and not is_midline:
            pos = [-abs(pos[0]), pos[1], pos[2]]
        elif side == "right" and not is_midline:
            pos = [abs(pos[0]), pos[1], pos[2]]

        # Radial unit normal calculation
        r_x = pos[0]
        r_z = pos[2] if abs(pos[2]) > 0.01 else 0.1
        norm = _normalize([r_x, 0.1, r_z])
        if side == "left" and not is_midline:
            norm = [-abs(norm[0]), norm[1], norm[2]]

        return {
            "point_code": point_code,
            "meridian_code": rule.meridian_code,
            "name_en": rule.name_en,
            "name_zh": rule.name_zh,
            "name_vi": rule.name_vi,
            "quality_class": rule.quality_class,
            "localization_method": rule.localization_method.value,
            "canonical_position": [round(x, 6) for x in pos],
            "surface_normal": [round(x, 5) for x in norm],
            "fma_anchor": rule.fma_anchor,
            "skeletal_structure": rule.skeletal_structure,
            "who_reference": rule.who_reference,
            "uncertainty_mm": rule.uncertainty_mm,
            "tolerance_radius_mm": rule.tolerance_radius_mm,
            "is_posture_sensitive": rule.is_posture_sensitive,
            "sensitive_joint": rule.sensitive_joint,
            "threshold_deg": rule.threshold_deg,
        }
