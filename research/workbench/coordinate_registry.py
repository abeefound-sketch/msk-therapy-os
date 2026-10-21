"""Coordinate Registry for standardizing units, axes, and anatomical landmarks with academic provenance."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AnatomicalLandmark:
    code: str
    name_zh: str
    name_en: str
    canonical_coords: List[float]  # [x, y, z] in meters on canonical BodyParts3D model
    skeletal_anchor: str
    fma_id: str
    who_reference: str
    description: str
    clinical_uncertainty_mm: float  # Expected physiological variance across body types


class CoordinateRegistry:
    """Registry managing coordinate systems, transformations, and academic anatomical landmark references."""

    # Reference canonical coordinate system:
    # Origin: Ground plane directly below center of gravity (Y=0)
    # Sole: Y ≈ 0.00m
    # DanTian / Pelvis: Y ≈ 0.86m
    # C7 vertebra (Dazhui / GV14): Y ≈ 1.478m
    # Crown (Baihui / GV20): Y ≈ 1.718m
    # Axes: Right-handed. +X = Right, +Y = Superior (Up), +Z = Anterior (Front)
    # Units: SI Meters

    # Academic & Clinical Landmark Ground Truths
    # Primary Source: WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008, ISBN 978 92 9061 248 3)
    # Anatomical Ontology: Terminologia Anatomica 2 (TA2) & Foundational Model of Anatomy (FMA)
    LANDMARKS: Dict[str, AnatomicalLandmark] = {
        "GV14": AnatomicalLandmark(
            code="GV14",
            name_zh="大椎",
            name_en="Dazhui",
            canonical_coords=[0.000, 1.478, -0.092],
            skeletal_anchor="Depression inferior to spinous process of 7th cervical vertebra (vertebra prominens)",
            fma_id="FMA:13337 (Seventh cervical vertebra)",
            who_reference="WHO Standard 2008, p. 235: Posterior midline, in the depression inferior to the spinous process of the 7th cervical vertebra (C7).",
            description="Posterior midline, below C7 spinous process. Palpable landmark that remains stationary when head rotates.",
            clinical_uncertainty_mm=12.0,  # Cervical flexion/extension alters skin-to-bone offset
        ),
        "GB21": AnatomicalLandmark(
            code="GB21",
            name_zh="肩井",
            name_en="Jianjing",
            canonical_coords=[0.142, 1.436, -0.012],
            skeletal_anchor="Midpoint between C7 spinous process and lateral extremity of acromion process, on m. trapezius",
            fma_id="FMA:9626 (Trapezius muscle) & FMA:23214 (Acromion)",
            who_reference="WHO Standard 2008, p. 195: On the shoulder, at the midpoint of the line connecting the spinous process of C7 and the lateral extremity of the acromion.",
            description="Highest point of the trapezius shoulder ridge. Caution: deep insertion risks pneumothorax.",
            clinical_uncertainty_mm=18.0,  # Shoulder elevation and trapezius hypertrophy shift midpoint
        ),
        "GB20": AnatomicalLandmark(
            code="GB20",
            name_zh="风池",
            name_en="Fengchi",
            canonical_coords=[0.068, 1.582, -0.076],
            skeletal_anchor="Suboccipital depression between upper portion of m. sternocleidomastoideus and m. trapezius",
            fma_id="FMA:13407 (Sternocleidomastoid muscle) & FMA:9626 (Trapezius muscle)",
            who_reference="WHO Standard 2008, p. 194: In the anterior region of the neck, inferior to the occipital bone, in the depression between m. sternocleidomastoideus and m. trapezius.",
            description="Inferior to occiput, level with inferior border of mastoid process.",
            clinical_uncertainty_mm=10.0,
        ),
        "BL10": AnatomicalLandmark(
            code="BL10",
            name_zh="天柱",
            name_en="Tianzhu",
            canonical_coords=[0.038, 1.572, -0.084],
            skeletal_anchor="Lateral margin of m. trapezius at level of C2 vertebra",
            fma_id="FMA:13332 (Axis vertebra) & FMA:9626 (Trapezius muscle)",
            who_reference="WHO Standard 2008, p. 116: In the posterior region of the neck, level with the superior border of the spinous process of C2, in the depression on the lateral border of m. trapezius.",
            description="Lateral border of trapezius in suboccipital depression.",
            clinical_uncertainty_mm=10.0,
        ),
        "SI15": AnatomicalLandmark(
            code="SI15",
            name_zh="肩中俞",
            name_en="Jianzhongshu",
            canonical_coords=[0.075, 1.455, -0.095],
            skeletal_anchor="2 cun lateral to lower border of C7 spinous process, medial border of scapula",
            fma_id="FMA:13337 (Seventh cervical vertebra) & FMA:23215 (Spine of scapula)",
            who_reference="WHO Standard 2008, p. 109: Upper back, 2 B-cun lateral to the posterior midline, level with the lower border of C7 spinous process.",
            description="On upper back near medial border of scapula.",
            clinical_uncertainty_mm=15.0,
        ),
        "TE15": AnatomicalLandmark(
            code="TE15",
            name_zh="天髎",
            name_en="Tianliao",
            canonical_coords=[0.128, 1.442, -0.045],
            skeletal_anchor="Superior angle of scapula / supraspinous fossa",
            fma_id="FMA:23215 (Supraspinous fossa) & FMA:24285 (Superior angle of scapula)",
            who_reference="WHO Standard 2008, p. 182: Scapular region, in the supraspinous fossa, midway between GB21 and SI13, on the superior angle of the scapula.",
            description="In the depression superior to the scapular spine.",
            clinical_uncertainty_mm=15.0,
        ),
    }

    @staticmethod
    def euclidean_distance(p1: List[float], p2: List[float]) -> float:
        """Calculate Euclidean distance in millimeters between two 3D points in meters."""
        dx = (p1[0] - p2[0]) * 1000.0
        dy = (p1[1] - p2[1]) * 1000.0
        dz = (p1[2] - p2[2]) * 1000.0
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    @classmethod
    def get_landmark(cls, code: str) -> Optional[AnatomicalLandmark]:
        return cls.LANDMARKS.get(code)

    @classmethod
    def list_landmarks(cls) -> List[str]:
        return list(cls.LANDMARKS.keys())

    @classmethod
    def get_neck_shoulder_scenario_codes(cls) -> List[str]:
        return ["GB21", "GV14", "GB20", "BL10", "SI15", "TE15"]

    @classmethod
    def transform_to_canonical(cls, source_name: str, coords: List[float]) -> List[float]:
        """Transform coordinates from an upstream source into canonical BodyParts3D coordinates."""
        if not coords or len(coords) < 3:
            return [0.0, 0.0, 0.0]

        x, y, z = coords[0], coords[1], coords[2]

        if "tcm-acupoints" in source_name:
            # Shift Y from pelvis origin (-0.86 to +0.86) to floor origin (0.0 to 1.72)
            return [x, y + 0.86, z]
        elif "anatomy-3d" in source_name:
            return [x, y, z]
        elif "tcm-3d" in source_name:
            return [x, y, z]
        elif "acupuncture-3d-authoring" in source_name:
            return [x, y, z]

        return [x, y, z]
