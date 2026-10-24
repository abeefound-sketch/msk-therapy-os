"""Anatomical Landmark Registry and Ontology for MSK-Therapy-OS.

Defines standard anatomical landmarks with FMA identifiers, skeletal anchors,
canonical 3D coordinates on BodyParts3D 4.0 (FJ2810), and clinical uncertainty boundaries.
Pure-Python, zero external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple


class LandmarkType(str, Enum):
    """Ontological classification of anatomical palpation and registration landmarks."""
    BONY_LANDMARK = "BONY_LANDMARK"
    JOINT_LANDMARK = "JOINT_LANDMARK"
    TENDON_LANDMARK = "TENDON_LANDMARK"
    MUSCLE_BORDER = "MUSCLE_BORDER"
    SKIN_CREASE = "SKIN_CREASE"
    SURFACE_TOPOGRAPHIC_LANDMARK = "SURFACE_TOPOGRAPHIC_LANDMARK"


class BodyRegion(str, Enum):
    """Major anatomical regions for spatial partitioning and containment."""
    HEAD_NECK = "head_neck"
    TORSO = "torso"
    UPPER_EXTREMITY = "upper_extremity"
    LOWER_EXTREMITY = "lower_extremity"


@dataclass(frozen=True)
class AnatomicalLandmark:
    """Rigorous ontological model for an anatomical landmark."""
    landmark_id: str
    name_en: str
    name_zh: str
    name_vi: str
    landmark_type: LandmarkType
    region: BodyRegion
    canonical_position: Tuple[float, float, float]  # [X, Y, Z] in meters on FJ2810
    fma_id: str
    skeletal_anchor: str
    tolerance_radius_mm: float
    clinical_uncertainty_mm: float
    verification_status: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "landmark_id": self.landmark_id,
            "name_en": self.name_en,
            "name_zh": self.name_zh,
            "name_vi": self.name_vi,
            "landmark_type": self.landmark_type.value,
            "region": self.region.value,
            "canonical_position": list(self.canonical_position),
            "fma_id": self.fma_id,
            "skeletal_anchor": self.skeletal_anchor,
            "tolerance_radius_mm": self.tolerance_radius_mm,
            "clinical_uncertainty_mm": self.clinical_uncertainty_mm,
            "verification_status": self.verification_status,
            "description": self.description,
        }


# Canonical Reference Landmark Catalog
# Ground Truth derived from BodyParts3D 4.0 FJ2810 Mesh & WHO 2008 Standard
# Coordinate System: Right-Handed Cartesian, Y-Up (+X Right, +Y Up, +Z Front), Units: Meters
CANONICAL_LANDMARKS: Dict[str, AnatomicalLandmark] = {
    # -------------------------------------------------------------------------
    # HEAD & NECK
    # -------------------------------------------------------------------------
    "LM_VERTEX_CROWN": AnatomicalLandmark(
        landmark_id="LM_VERTEX_CROWN",
        name_en="Vertex (Crown)",
        name_zh="头顶百会点",
        name_vi="Đỉnh đầu (Huyệt Bách Hội)",
        landmark_type=LandmarkType.SURFACE_TOPOGRAPHIC_LANDMARK,
        region=BodyRegion.HEAD_NECK,
        canonical_position=(0.0000, 1.7180, -0.0150),
        fma_id="FMA:46452",
        skeletal_anchor="Sagittal suture intersection at vertex of cranium",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=8.0,
        verification_status="CANONICAL_ANCHOR",
        description="Highest point of the cranium in standard anatomical position.",
    ),
    "LM_GLABELLA": AnatomicalLandmark(
        landmark_id="LM_GLABELLA",
        name_en="Glabella",
        name_zh="印堂/眉间点",
        name_vi="Điểm giữa hai cung mày (Ấn Đường)",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.HEAD_NECK,
        canonical_position=(0.0000, 1.6250, 0.0890),
        fma_id="FMA:52851",
        skeletal_anchor="Smooth prominence of frontal bone between superciliary arches",
        tolerance_radius_mm=4.0,
        clinical_uncertainty_mm=5.0,
        verification_status="CANONICAL_ANCHOR",
        description="Midpoint between the eyebrows on the frontal bone.",
    ),
    "LM_INION": AnatomicalLandmark(
        landmark_id="LM_INION",
        name_en="Inion (External Occipital Protuberance)",
        name_zh="枕外隆凸点",
        name_vi="U chẩm ngoài",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.HEAD_NECK,
        canonical_position=(0.0000, 1.5950, -0.0980),
        fma_id="FMA:76624",
        skeletal_anchor="External occipital protuberance midline",
        tolerance_radius_mm=6.0,
        clinical_uncertainty_mm=8.0,
        verification_status="CANONICAL_ANCHOR",
        description="Most prominent projection of occipital bone at lower back of skull.",
    ),
    "LM_MASTOID_R": AnatomicalLandmark(
        landmark_id="LM_MASTOID_R",
        name_en="Right Mastoid Process (Apex)",
        name_zh="右侧乳突尖",
        name_vi="Mỏm chũm phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.HEAD_NECK,
        canonical_position=(0.0620, 1.5740, -0.0420),
        fma_id="FMA:52872",
        skeletal_anchor="Apex of right mastoid process of temporal bone",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=7.0,
        verification_status="CANONICAL_ANCHOR",
        description="Inferior conical projection of temporal bone behind ear.",
    ),
    "LM_MASTOID_L": AnatomicalLandmark(
        landmark_id="LM_MASTOID_L",
        name_en="Left Mastoid Process (Apex)",
        name_zh="左侧乳突尖",
        name_vi="Mỏm chũm trái",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.HEAD_NECK,
        canonical_position=(-0.0620, 1.5740, -0.0420),
        fma_id="FMA:52872",
        skeletal_anchor="Apex of left mastoid process of temporal bone",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=7.0,
        verification_status="CANONICAL_ANCHOR",
        description="Inferior conical projection of temporal bone behind ear.",
    ),
    "LM_C2_SPINE": AnatomicalLandmark(
        landmark_id="LM_C2_SPINE",
        name_en="C2 Spinous Process (Axis)",
        name_zh="第2颈椎棘突",
        name_vi="Mỏm gai đốt sống cổ C2 (Trục)",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.HEAD_NECK,
        canonical_position=(0.0000, 1.5580, -0.0780),
        fma_id="FMA:12520",
        skeletal_anchor="Spinous process of axis (first palpable cervical spine below inion)",
        tolerance_radius_mm=7.0,
        clinical_uncertainty_mm=10.0,
        verification_status="CANONICAL_ANCHOR",
        description="First prominent, easily palpable spinous process below the occiput.",
    ),
    "LM_C7_SPINE": AnatomicalLandmark(
        landmark_id="LM_C7_SPINE",
        name_en="C7 Spinous Process (Vertebra Prominens)",
        name_zh="第7颈椎棘突 (大椎骨)",
        name_vi="Mỏm gai đốt sống cổ C7 (Đại Chùy)",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.HEAD_NECK,
        canonical_position=(0.0000, 1.4780, -0.0920),
        fma_id="FMA:12525",
        skeletal_anchor="Depression inferior to spinous process of 7th cervical vertebra",
        tolerance_radius_mm=6.0,
        clinical_uncertainty_mm=10.0,
        verification_status="CANONICAL_ANCHOR",
        description="Vertebra prominens; principal posterior landmark dividing neck and thorax.",
    ),

    # -------------------------------------------------------------------------
    # THORAX, ABDOMEN & PELVIS
    # -------------------------------------------------------------------------
    "LM_JUGULAR_NOTCH": AnatomicalLandmark(
        landmark_id="LM_JUGULAR_NOTCH",
        name_en="Suprasternal / Jugular Notch",
        name_zh="胸骨柄颈静脉切迹 (天突)",
        name_vi="Hõm ức (Huyệt Thiên Đột)",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.TORSO,
        canonical_position=(0.0000, 1.4080, 0.0520),
        fma_id="FMA:7542",
        skeletal_anchor="Superior border of manubrium sterni between clavicular notches",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=7.0,
        verification_status="CANONICAL_ANCHOR",
        description="Deep palpable notch at top of sternum between medial clavicle heads.",
    ),
    "LM_STERNAL_ANGLE": AnatomicalLandmark(
        landmark_id="LM_STERNAL_ANGLE",
        name_en="Sternal Angle (Angle of Louis)",
        name_zh="胸骨角 (路易斯角)",
        name_vi="Góc xương ức (Góc Louis)",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.TORSO,
        canonical_position=(0.0000, 1.3560, 0.0820),
        fma_id="FMA:7547",
        skeletal_anchor="Manubriosternal synchondrosis level with 2nd costal cartilage",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=6.0,
        verification_status="CANONICAL_ANCHOR",
        description="Transverse ridge marking junction between manubrium and body of sternum.",
    ),
    "LM_XIPHOSTERNAL_JOINT": AnatomicalLandmark(
        landmark_id="LM_XIPHOSTERNAL_JOINT",
        name_en="Xiphosternal Synchondrosis",
        name_zh="胸剑联合",
        name_vi="Khớp mũi ức - thân xương ức",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.TORSO,
        canonical_position=(0.0000, 1.1980, 0.0980),
        fma_id="FMA:7503",
        skeletal_anchor="Junction between xiphoid process and body of sternum",
        tolerance_radius_mm=6.0,
        clinical_uncertainty_mm=8.0,
        verification_status="CANONICAL_ANCHOR",
        description="Inferior boundary of sternal body; superior anchor for anterior 8 B-cun.",
    ),
    "LM_UMBILICUS": AnatomicalLandmark(
        landmark_id="LM_UMBILICUS",
        name_en="Umbilicus",
        name_zh="脐中 (神阙)",
        name_vi="Rốn (Huyệt Thần Khuyết)",
        landmark_type=LandmarkType.SKIN_CREASE,
        region=BodyRegion.TORSO,
        canonical_position=(0.0000, 1.0260, 0.1120),
        fma_id="FMA:61584",
        skeletal_anchor="Level with L3-L4 intervertebral disc in erect standard position",
        tolerance_radius_mm=7.0,
        clinical_uncertainty_mm=12.0,
        verification_status="CANONICAL_ANCHOR",
        description="Center of navel; dividing landmark between upper abdomen (8 cun) and lower abdomen (5 cun).",
    ),
    "LM_PUBIC_SYMPHYSIS": AnatomicalLandmark(
        landmark_id="LM_PUBIC_SYMPHYSIS",
        name_en="Pubic Symphysis (Superior Border)",
        name_zh="耻骨联合上缘 (曲骨)",
        name_vi="Bờ trên khớp mu (Huyệt Khúc Cốt)",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.TORSO,
        canonical_position=(0.0000, 0.8640, 0.0880),
        fma_id="FMA:16950",
        skeletal_anchor="Superior margin of fibrocartilaginous pubic symphysis",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=8.0,
        verification_status="CANONICAL_ANCHOR",
        description="Anterior midline bony prominence of pelvis; lower boundary of 5 B-cun abdomen.",
    ),
    "LM_ASIS_R": AnatomicalLandmark(
        landmark_id="LM_ASIS_R",
        name_en="Right Anterior Superior Iliac Spine (ASIS)",
        name_zh="右侧髂前上棘",
        name_vi="Gai chậu trước trên phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.TORSO,
        canonical_position=(0.1320, 0.9420, 0.0750),
        fma_id="FMA:49465",
        skeletal_anchor="Anterior extremity of iliac crest on right ilium",
        tolerance_radius_mm=6.0,
        clinical_uncertainty_mm=9.0,
        verification_status="CANONICAL_ANCHOR",
        description="Prominent palpable bony anterior point of right pelvis.",
    ),
    "LM_ASIS_L": AnatomicalLandmark(
        landmark_id="LM_ASIS_L",
        name_en="Left Anterior Superior Iliac Spine (ASIS)",
        name_zh="左侧髂前上棘",
        name_vi="Gai chậu trước trên trái",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.TORSO,
        canonical_position=(-0.1320, 0.9420, 0.0750),
        fma_id="FMA:49465",
        skeletal_anchor="Anterior extremity of iliac crest on left ilium",
        tolerance_radius_mm=6.0,
        clinical_uncertainty_mm=9.0,
        verification_status="CANONICAL_ANCHOR",
        description="Prominent palpable bony anterior point of left pelvis.",
    ),
    "LM_L4_SPINE": AnatomicalLandmark(
        landmark_id="LM_L4_SPINE",
        name_en="L4 Spinous Process (Intercristal Line)",
        name_zh="第4腰椎棘突 (腰阳关)",
        name_vi="Mỏm gai đốt sống thắt lưng L4",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.TORSO,
        canonical_position=(0.0000, 1.0320, -0.0820),
        fma_id="FMA:13075",
        skeletal_anchor="Spinous process of 4th lumbar vertebra level with supracristal plane",
        tolerance_radius_mm=7.0,
        clinical_uncertainty_mm=11.0,
        verification_status="CANONICAL_ANCHOR",
        description="Level with highest points of iliac crests (Jacoby line).",
    ),

    # -------------------------------------------------------------------------
    # UPPER EXTREMITY (RIGHT)
    # -------------------------------------------------------------------------
    "LM_ACROMION_R": AnatomicalLandmark(
        landmark_id="LM_ACROMION_R",
        name_en="Right Acromion (Lateral Extremity)",
        name_zh="右侧肩峰外侧角",
        name_vi="Mỏm cùng vai phải (Góc ngoài)",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.UPPER_EXTREMITY,
        canonical_position=(0.1880, 1.4120, -0.0150),
        fma_id="FMA:23260",
        skeletal_anchor="Lateral margin and angle of acromion process of right scapula",
        tolerance_radius_mm=6.0,
        clinical_uncertainty_mm=9.0,
        verification_status="CANONICAL_ANCHOR",
        description="Lateral border of acromion forming shoulder point with clavicle.",
    ),
    "LM_ACROMION_L": AnatomicalLandmark(
        landmark_id="LM_ACROMION_L",
        name_en="Left Acromion (Lateral Extremity)",
        name_zh="左侧肩峰外侧角",
        name_vi="Mỏm cùng vai trái (Góc ngoài)",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.UPPER_EXTREMITY,
        canonical_position=(-0.1880, 1.4120, -0.0150),
        fma_id="FMA:23260",
        skeletal_anchor="Lateral margin and angle of acromion process of left scapula",
        tolerance_radius_mm=6.0,
        clinical_uncertainty_mm=9.0,
        verification_status="CANONICAL_ANCHOR",
        description="Lateral border of acromion forming shoulder point with clavicle.",
    ),
    "LM_AXILLARY_FOLD_ANT_R": AnatomicalLandmark(
        landmark_id="LM_AXILLARY_FOLD_ANT_R",
        name_en="Right Anterior Axillary Fold (Apex)",
        name_zh="右侧腋前纹头",
        name_vi="Nếp nách trước phải",
        landmark_type=LandmarkType.SKIN_CREASE,
        region=BodyRegion.UPPER_EXTREMITY,
        canonical_position=(0.1480, 1.3320, 0.0540),
        fma_id="FMA:322184",
        skeletal_anchor="Lower border of pectoralis major forming anterior axillary fold",
        tolerance_radius_mm=7.0,
        clinical_uncertainty_mm=12.0,
        verification_status="CANONICAL_ANCHOR",
        description="Apex of anterior axillary crease; upper boundary of 9 B-cun arm.",
    ),
    "LM_CUBITAL_CREASE_R": AnatomicalLandmark(
        landmark_id="LM_CUBITAL_CREASE_R",
        name_en="Right Cubital Crease (Midpoint)",
        name_zh="右侧肘横纹中点",
        name_vi="Nếp gấp khuỷu tay phải (Điểm giữa)",
        landmark_type=LandmarkType.SKIN_CREASE,
        region=BodyRegion.UPPER_EXTREMITY,
        canonical_position=(0.2460, 1.0820, 0.0210),
        fma_id="FMA:24290",
        skeletal_anchor="Transverse cubital flexion crease level with epicondyles of humerus",
        tolerance_radius_mm=6.0,
        clinical_uncertainty_mm=10.0,
        verification_status="CANONICAL_ANCHOR",
        description="Flexion crease of elbow; boundary between 9 B-cun upper arm and 12 B-cun forearm.",
    ),
    "LM_MED_EPICONDYLE_HUMERUS_R": AnatomicalLandmark(
        landmark_id="LM_MED_EPICONDYLE_HUMERUS_R",
        name_en="Right Medial Epicondyle of Humerus",
        name_zh="右侧肱骨内上髁",
        name_vi="Mỏm trên lồi cầu trong xương cánh tay phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.UPPER_EXTREMITY,
        canonical_position=(0.2180, 1.0880, 0.0050),
        fma_id="FMA:23441",
        skeletal_anchor="Medial epicondyle of distal right humerus",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=7.0,
        verification_status="CANONICAL_ANCHOR",
        description="Large subcutaneous medial projection above elbow joint.",
    ),
    "LM_LAT_EPICONDYLE_HUMERUS_R": AnatomicalLandmark(
        landmark_id="LM_LAT_EPICONDYLE_HUMERUS_R",
        name_en="Right Lateral Epicondyle of Humerus",
        name_zh="右侧肱骨外上髁",
        name_vi="Mỏm trên lồi cầu ngoài xương cánh tay phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.UPPER_EXTREMITY,
        canonical_position=(0.2720, 1.0850, 0.0080),
        fma_id="FMA:23442",
        skeletal_anchor="Lateral epicondyle of distal right humerus",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=7.0,
        verification_status="CANONICAL_ANCHOR",
        description="Subcutaneous lateral projection above elbow joint.",
    ),
    "LM_WRIST_CREASE_PALMAR_R": AnatomicalLandmark(
        landmark_id="LM_WRIST_CREASE_PALMAR_R",
        name_en="Right Palmar Wrist Crease (Distal)",
        name_zh="右侧腕前区掌侧远端横纹",
        name_vi="Nếp gấp xa cổ tay phải (Mặt lòng)",
        landmark_type=LandmarkType.SKIN_CREASE,
        region=BodyRegion.UPPER_EXTREMITY,
        canonical_position=(0.2850, 0.8420, 0.0420),
        fma_id="FMA:24292",
        skeletal_anchor="Level with proximal border of flexor retinaculum and pisiform/scaphoid",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=8.0,
        verification_status="CANONICAL_ANCHOR",
        description="Distal transverse flexion crease of anterior wrist; boundary of 12 B-cun forearm.",
    ),
    "LM_RADIAL_STYLOID_R": AnatomicalLandmark(
        landmark_id="LM_RADIAL_STYLOID_R",
        name_en="Right Radial Styloid Process",
        name_zh="右侧桡骨茎突",
        name_vi="Mỏm trâm quay phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.UPPER_EXTREMITY,
        canonical_position=(0.3020, 0.8520, 0.0380),
        fma_id="FMA:23524",
        skeletal_anchor="Distal lateral projection of right radius",
        tolerance_radius_mm=4.0,
        clinical_uncertainty_mm=6.0,
        verification_status="CANONICAL_ANCHOR",
        description="Palpable conical projection on lateral distal radius (anatomical snuffbox border).",
    ),

    # -------------------------------------------------------------------------
    # LOWER EXTREMITY (RIGHT)
    # -------------------------------------------------------------------------
    "LM_GREATER_TROCHANTER_R": AnatomicalLandmark(
        landmark_id="LM_GREATER_TROCHANTER_R",
        name_en="Right Greater Trochanter (Prominence)",
        name_zh="右侧股骨大转子隆起",
        name_vi="Mấu chuyển lớn xương đùi phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.LOWER_EXTREMITY,
        canonical_position=(0.1780, 0.8550, -0.0120),
        fma_id="FMA:32852",
        skeletal_anchor="Highest lateral point of greater trochanter of right femur",
        tolerance_radius_mm=7.0,
        clinical_uncertainty_mm=12.0,
        verification_status="CANONICAL_ANCHOR",
        description="Lateral hip bony prominence; upper landmark of 19 B-cun lateral thigh.",
    ),
    "LM_PATELLA_INFERIOR_R": AnatomicalLandmark(
        landmark_id="LM_PATELLA_INFERIOR_R",
        name_en="Right Patella (Inferior Border / Apex)",
        name_zh="右侧髌骨下缘",
        name_vi="Bờ dưới xương bánh chè phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.LOWER_EXTREMITY,
        canonical_position=(0.1150, 0.4680, 0.0820),
        fma_id="FMA:24485",
        skeletal_anchor="Apex and inferior margin of right patella",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=7.0,
        verification_status="CANONICAL_ANCHOR",
        description="Inferior apex of kneecap; level with joint line and ST35 (Dubi).",
    ),
    "LM_POPLITEAL_CREASE_R": AnatomicalLandmark(
        landmark_id="LM_POPLITEAL_CREASE_R",
        name_en="Right Popliteal Crease (Midpoint)",
        name_zh="右侧腘窝横纹中点 (委中)",
        name_vi="Nếp lằn khoeo chân phải (Huyệt Ủy Trung)",
        landmark_type=LandmarkType.SKIN_CREASE,
        region=BodyRegion.LOWER_EXTREMITY,
        canonical_position=(0.1140, 0.4620, -0.0520),
        fma_id="FMA:24294",
        skeletal_anchor="Transverse crease of popliteal fossa between biceps femoris and semitendinosus",
        tolerance_radius_mm=6.0,
        clinical_uncertainty_mm=10.0,
        verification_status="CANONICAL_ANCHOR",
        description="Transverse crease of back of knee; dividing landmark for 16 B-cun posterior leg.",
    ),
    "LM_TIBIAL_TUBEROSITY_R": AnatomicalLandmark(
        landmark_id="LM_TIBIAL_TUBEROSITY_R",
        name_en="Right Tibial Tuberosity",
        name_zh="右侧胫骨粗隆",
        name_vi="Lồi củ chày phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.LOWER_EXTREMITY,
        canonical_position=(0.1120, 0.4320, 0.0720),
        fma_id="FMA:35463",
        skeletal_anchor="Anterior subcutaneous elevation of proximal right tibia",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=7.0,
        verification_status="CANONICAL_ANCHOR",
        description="Subcutaneous prominence giving attachment to patellar ligament; reference for ST36.",
    ),
    "LM_MED_MALLEOLUS_R": AnatomicalLandmark(
        landmark_id="LM_MED_MALLEOLUS_R",
        name_en="Right Medial Malleolus (Prominence)",
        name_zh="右侧内踝尖",
        name_vi="Đỉnh mắt cá trong phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.LOWER_EXTREMITY,
        canonical_position=(0.0760, 0.0820, 0.0150),
        fma_id="FMA:35451",
        skeletal_anchor="Most prominent medial projection of distal right tibia",
        tolerance_radius_mm=4.0,
        clinical_uncertainty_mm=5.0,
        verification_status="CANONICAL_ANCHOR",
        description="Prominent medial ankle bone; terminal reference for 13 B-cun medial leg.",
    ),
    "LM_LAT_MALLEOLUS_R": AnatomicalLandmark(
        landmark_id="LM_LAT_MALLEOLUS_R",
        name_en="Right Lateral Malleolus (Prominence)",
        name_zh="右侧外踝尖",
        name_vi="Đỉnh mắt cá ngoài phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.LOWER_EXTREMITY,
        canonical_position=(0.1380, 0.0740, 0.0080),
        fma_id="FMA:35502",
        skeletal_anchor="Most prominent lateral projection of distal right fibula",
        tolerance_radius_mm=4.0,
        clinical_uncertainty_mm=5.0,
        verification_status="CANONICAL_ANCHOR",
        description="Prominent lateral ankle bone; terminal reference for 16 B-cun lateral leg.",
    ),
    "LM_CALCANEUS_POST_R": AnatomicalLandmark(
        landmark_id="LM_CALCANEUS_POST_R",
        name_en="Right Calcaneus (Posterior Tuberosity)",
        name_zh="右侧跟骨后结节",
        name_vi="Củ sau xương gót phải",
        landmark_type=LandmarkType.BONY_LANDMARK,
        region=BodyRegion.LOWER_EXTREMITY,
        canonical_position=(0.1080, 0.0240, -0.0680),
        fma_id="FMA:24496",
        skeletal_anchor="Posterior tuberosity of right calcaneus (heel)",
        tolerance_radius_mm=5.0,
        clinical_uncertainty_mm=7.0,
        verification_status="CANONICAL_ANCHOR",
        description="Posterior weight-bearing prominence of heel.",
    ),
}


class LandmarkRegistry:
    """Registry maintaining standard anatomical palpation landmarks and spatial indices."""

    def __init__(self, custom_landmarks: Optional[Dict[str, AnatomicalLandmark]] = None):
        self._landmarks: Dict[str, AnatomicalLandmark] = dict(CANONICAL_LANDMARKS)
        if custom_landmarks:
            self._landmarks.update(custom_landmarks)

    def get_landmark(self, landmark_id: str) -> Optional[AnatomicalLandmark]:
        return self._landmarks.get(landmark_id)

    def list_landmarks(self, region: Optional[BodyRegion] = None) -> List[AnatomicalLandmark]:
        if region is None:
            return list(self._landmarks.values())
        return [lm for lm in self._landmarks.values() if lm.region == region]

    def get_canonical_position(self, landmark_id: str) -> Optional[Tuple[float, float, float]]:
        lm = self.get_landmark(landmark_id)
        return lm.canonical_position if lm else None

    def calculate_distance_mm(self, p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
        """Euclidean distance in millimeters between two 3D positions in meters."""
        dx = (p1[0] - p2[0]) * 1000.0
        dy = (p1[1] - p2[1]) * 1000.0
        dz = (p1[2] - p2[2]) * 1000.0
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def find_nearest_landmark(
        self,
        position: Tuple[float, float, float],
        region: Optional[BodyRegion] = None
    ) -> Tuple[Optional[AnatomicalLandmark], float]:
        """Find the nearest canonical landmark to a given 3D position in meters."""
        candidates = self.list_landmarks(region)
        if not candidates:
            return None, float("inf")

        best_lm = None
        min_dist = float("inf")
        for lm in candidates:
            dist = self.calculate_distance_mm(position, lm.canonical_position)
            if dist < min_dist:
                min_dist = dist
                best_lm = lm

        return best_lm, min_dist
