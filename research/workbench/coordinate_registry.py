"""Coordinate Registry for standardizing units, axes, and anatomical landmarks across 3D datasets."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AnatomicalLandmark:
    code: str
    name_zh: str
    name_en: str
    canonical_coords: List[float]  # [x, y, z] in meters on canonical BodyParts3D model
    skeletal_anchor: str
    description: str


class CoordinateRegistry:
    """Registry managing coordinate systems, transformations, and anatomical landmark ground truths."""

    # Reference canonical coordinate system:
    # Origin: Ground plane directly below center of gravity (Y=0)
    # Sole: Y ≈ 0.00m
    # DanTian / Pelvis: Y ≈ 0.86m
    # C7 vertebra (Dazhui / GV14): Y ≈ 1.48m
    # Crown (Baihui / GV20): Y ≈ 1.72m
    # Axes: Right-handed. +X = Right, +Y = Superior (Up), +Z = Anterior (Front)
    # Units: Meters

    # Anatomical reference landmarks for Neck-Shoulder-Upper-Back scenario and key body landmarks
    LANDMARKS: Dict[str, AnatomicalLandmark] = {
        "GV14": AnatomicalLandmark(
            code="GV14",
            name_zh="大椎",
            name_en="Dazhui",
            canonical_coords=[0.000, 1.478, -0.092],
            skeletal_anchor="C7 spinous process depression (vertebra prominens)",
            description="Posterior midline, in the depression below the spinous process of the 7th cervical vertebra.",
        ),
        "GB21": AnatomicalLandmark(
            code="GB21",
            name_zh="肩井",
            name_en="Jianjing",
            canonical_coords=[0.142, 1.436, -0.012],
            skeletal_anchor="Midpoint between C7 spinous process and acromion process on upper trapezius",
            description="On the shoulder, directly above the nipple, at the midpoint of the line connecting GV14 and the acromion.",
        ),
        "GB20": AnatomicalLandmark(
            code="GB20",
            name_zh="风池",
            name_en="Fengchi",
            canonical_coords=[0.068, 1.582, -0.076],
            skeletal_anchor="Suboccipital depression between sternocleidomastoid and trapezius",
            description="In the depression between the upper portion of m. sternocleidomastoideus and m. trapezius.",
        ),
        "BL10": AnatomicalLandmark(
            code="BL10",
            name_zh="天柱",
            name_en="Tianzhu",
            canonical_coords=[0.038, 1.572, -0.084],
            skeletal_anchor="Lateral margin of trapezius at level of C2",
            description="In the depression on the lateral border of m. trapezius, 1.3 cun lateral to the posterior midline.",
        ),
        "SI15": AnatomicalLandmark(
            code="SI15",
            name_zh="肩中俞",
            name_en="Jianzhongshu",
            canonical_coords=[0.075, 1.455, -0.095],
            skeletal_anchor="2 cun lateral to lower border of C7 spinous process",
            description="On the back, 2 cun lateral to the lower border of the spinous process of the 7th cervical vertebra.",
        ),
        "TE15": AnatomicalLandmark(
            code="TE15",
            name_zh="天髎",
            name_en="Tianliao",
            canonical_coords=[0.128, 1.442, -0.045],
            skeletal_anchor="Superior angle of scapula / supraspinous fossa",
            description="In the supraspinous fossa, midway between GB21 and SI13, on the superior angle of the scapula.",
        ),
        "LI4": AnatomicalLandmark(
            code="LI4",
            name_zh="合谷",
            name_en="Hegu",
            canonical_coords=[0.268, 0.812, 0.056],
            skeletal_anchor="1st and 2nd metacarpal interosseous space",
            description="On the dorsum of the hand, between the 1st and 2nd metacarpal bones.",
        ),
        "ST36": AnatomicalLandmark(
            code="ST36",
            name_zh="足三里",
            name_en="Zusanli",
            canonical_coords=[0.092, 0.448, 0.082],
            skeletal_anchor="3 cun inferior to Dubi (ST35), 1 fingerbreadth lateral to anterior tibial crest",
            description="On the anterior aspect of the lower leg, 3 cun below ST35, one finger-breadth lateral to the anterior crest of the tibia.",
        ),
        "GV20": AnatomicalLandmark(
            code="GV20",
            name_zh="百会",
            name_en="Baihui",
            canonical_coords=[0.000, 1.718, 0.012],
            skeletal_anchor="Sagittal vertex directly above ear apices",
            description="On the head, 5 cun posterior to the anterior hairline, on the anterior midline.",
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
        """Core reference scenario acupoints: GB21, GV14, GB20, BL10, SI15, TE15."""
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
            # Already in meters BodyParts3D space
            return [x, y, z]
        elif "tcm-3d" in source_name:
            # Already in meters BodyParts3D FJ2810 space
            return [x, y, z]
        elif "acupuncture-3d-authoring" in source_name:
            return [x, y, z]

        return [x, y, z]
