"""Coordinate Registry for standardizing units, axes, and anatomical landmarks with academic provenance."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class CoordinateValidationError(Exception):
    """Base exception for coordinate and landmark validation errors."""
    pass


class ScaleDivergenceError(CoordinateValidationError):
    """Raised when coordinates show clear units or scale divergence (e.g. millimeters vs meters)."""
    pass


class LateralityInversionConflictError(CoordinateValidationError):
    """Raised when left/right laterality contradicts spatial axis sign convention."""
    pass


class MeshChecksumMismatchError(CoordinateValidationError):
    """Raised when target mesh checksum does not match registered ground truth."""
    pass


class IncompletePathwayError(CoordinateValidationError):
    """Raised when a meridian pathway has fewer than the required minimum waypoints."""
    pass


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
    review_status: str = "EXPERT_REVIEW_PENDING"
    side: str = "RIGHT"


class CoordinateRegistry:
    """Registry managing coordinate systems, transformations, and academic anatomical landmark references."""

    # Reference canonical coordinate system (BodyParts3D converted):
    # Origin: Ground plane directly below center of gravity (Y=0)
    # Sole: Y ≈ 0.00m
    # DanTian / Pelvis: Y ≈ 0.86m
    # C7 vertebra (Dazhui / GV14): Y ≈ 1.478m
    # Crown (Baihui / GV20): Y ≈ 1.718m
    # Axes: Right-handed. +X = Patient Right, +Y = Superior (Up), +Z = Anterior (Front)
    # Units: SI Meters

    # Academic & Clinical Landmark Ground Truths
    # Primary Source: WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008, ISBN 978 92 9061 248 3)
    # Anatomical Ontology: Terminologia Anatomica 2 (TA2) & Foundational Model of Anatomy (FMA)
    # National Standard: GB/T 12346-2021
    LANDMARKS: Dict[str, AnatomicalLandmark] = {
        # Core Milestones Traced Acupoints: LI4, ST36, KI3
        "LI4": AnatomicalLandmark(
            code="LI4",
            name_zh="合谷",
            name_en="Hegu",
            canonical_coords=[0.245, 0.892, 0.125],
            skeletal_anchor="Radial aspect of 2nd metacarpal bone, midpoint of shaft, 1st dorsal interosseous muscle",
            fma_id="FMA:23910 (Second metacarpal bone) & FMA:37385 (First dorsal interosseous muscle)",
            who_reference="WHO Standard 2008, p. 57: On the dorsum of the hand, radial to the midpoint of the second metacarpal bone.",
            description="Radial aspect of 2nd metacarpal bone. Caution: contraindicated in pregnancy.",
            clinical_uncertainty_mm=5.0,
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
        ),
        "ST36": AnatomicalLandmark(
            code="ST36",
            name_zh="足三里",
            name_en="Zusanli",
            canonical_coords=[0.088, 0.445, 0.062],
            skeletal_anchor="Anterior aspect of leg, 1 finger-breadth lateral to anterior crest of tibia, m. tibialis anterior",
            fma_id="FMA:24476 (Tibia) & FMA:45155 (Tibialis anterior muscle)",
            who_reference="WHO Standard 2008, p. 75: Anterior region of leg, 3 B-cun inferior to ST35, one finger-breadth lateral to anterior crest of tibia.",
            description="One finger-breadth lateral to tibial tuberosity, in belly of tibialis anterior muscle.",
            clinical_uncertainty_mm=8.0,
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
        ),
        "KI3": AnatomicalLandmark(
            code="KI3",
            name_zh="太溪",
            name_en="Taixi",
            canonical_coords=[0.038, 0.082, -0.015],
            skeletal_anchor="Posteromedial aspect of ankle, depression between prominence of medial malleolus and tendo calcaneus",
            fma_id="FMA:24476 (Tibia, medial malleolus) & FMA:51111 (Calcaneal tendon)",
            who_reference="WHO Standard 2008, p. 138: Posteromedial region of ankle, in the depression between the prominence of the medial malleolus and the calcaneal tendon.",
            description="Between medial malleolus apex and Achilles tendon, level with malleolar apex.",
            clinical_uncertainty_mm=6.0,
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
        ),
        # Neck & Shoulder Group
        "GV14": AnatomicalLandmark(
            code="GV14",
            name_zh="大椎",
            name_en="Dazhui",
            canonical_coords=[0.000, 1.478, -0.092],
            skeletal_anchor="Depression inferior to spinous process of 7th cervical vertebra (vertebra prominens)",
            fma_id="FMA:13337 (Seventh cervical vertebra)",
            who_reference="WHO Standard 2008, p. 235: Posterior midline, in the depression inferior to the spinous process of the 7th cervical vertebra (C7).",
            description="Posterior midline, below C7 spinous process. Palpable landmark that remains stationary when head rotates.",
            clinical_uncertainty_mm=12.0,
            review_status="EXPERT_REVIEW_PENDING",
            side="MIDLINE",
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
            clinical_uncertainty_mm=18.0,
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
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
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
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
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
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
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
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
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
        ),
        "LI14": AnatomicalLandmark(
            code="LI14",
            name_zh="臂臑",
            name_en="Binao",
            canonical_coords=[0.185, 1.250, 0.010],
            skeletal_anchor="Tuberositas deltoidea humeri, lateral aspect of arm, m. deltoideus insertion",
            fma_id="FMA:23412 (Deltoid tuberosity of humerus)",
            who_reference="WHO Standard 2008, p. 41: On the lateral aspect of the arm, posterior to the distal insertion of the deltoid muscle, 7 B-cun superior to the cubital crease.",
            description="Lateral aspect of arm at the insertion of m. deltoideus into humerus.",
            clinical_uncertainty_mm=5.0,
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
        ),
        "LI15": AnatomicalLandmark(
            code="LI15",
            name_zh="肩髃",
            name_en="Jianyu",
            canonical_coords=[0.170, 1.395, 0.015],
            skeletal_anchor="Acromion of scapula and greater tubercle of humerus depression",
            fma_id="FMA:23240 (Acromion of scapula)",
            who_reference="WHO Standard 2008, p. 42: On the shoulder girdle, in the depression between the acromial angle and the greater tubercle of the humerus when the arm is abducted.",
            description="Depression between acromial angle and greater tubercle of humerus in shoulder abduction.",
            clinical_uncertainty_mm=5.0,
            review_status="EXPERT_REVIEW_PENDING",
            side="RIGHT",
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
    def get_core_validation_codes(cls) -> List[str]:
        return ["LI4", "ST36", "KI3"]

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

    # --- 4x4 Homogeneous Transformation Matrices ---

    @staticmethod
    def canonical_to_blender(p: List[float]) -> List[float]:
        """Convert Canonical (X: Right, Y: Up, Z: Front, meters) to Blender (X: Right, Y: Front, Z: Up, meters).
        Matrix:
        [1,  0,  0, 0]
        [0,  0,  1, 0]
        [0,  1,  0, 0]
        [0,  0,  0, 1]
        """
        return [float(p[0]), float(p[2]), float(p[1])]

    @staticmethod
    def blender_to_canonical(p: List[float]) -> List[float]:
        """Inverse: Convert Blender to Canonical."""
        return [float(p[0]), float(p[2]), float(p[1])]

    @staticmethod
    def raw_bp3d_mm_to_canonical(p: List[float]) -> List[float]:
        """Convert raw BodyParts3D OBJ mm/Z-up to Canonical meters/Y-up.
        Matches convert-anatomy.py: x*.001, z*.001 + 0.0781112, -y*.001 - 0.1
        """
        x, y, z = p[0], p[1], p[2]
        return [float(x * 0.001), float(z * 0.001 + 0.0781112), float(-y * 0.001 - 0.1)]

    # --- Fail-Closed Validation Guardrails ---

    @staticmethod
    def validate_coordinate_scale(coords: List[float], expected_units: str = "meters"):
        """Fail-closed if point magnitude indicates a unit confusion (e.g. millimeters vs meters)."""
        mag = math.hypot(coords[0], coords[1], coords[2])
        if expected_units == "meters":
            # Human anatomy coordinates in meters must be within [0.0, 3.0]
            if mag > 5.0 or (mag < 0.005 and coords != [0.0, 0.0, 0.0]):
                raise ScaleDivergenceError(
                    f"Coordinate magnitude {mag:.3f} is inconsistent with expected units '{expected_units}'. "
                    f"Suspected millimeters or scale error."
                )
        elif expected_units == "millimeters":
            if mag < 50.0 and coords != [0.0, 0.0, 0.0]:
                raise ScaleDivergenceError(
                    f"Coordinate magnitude {mag:.3f} is too small for millimeters. Suspected meters."
                )

    @staticmethod
    def validate_laterality_sign(code: str, side: str, coords: List[float]):
        """Fail-closed if declared laterality contradicts spatial axis sign."""
        x = coords[0]
        # In canonical convention: +X = Right, -X = Left, near 0 = Midline
        if side.upper() == "RIGHT" and x < -0.02:
            raise LateralityInversionConflictError(
                f"Acupoint {code} declared side 'RIGHT' but X coordinate is negative ({x:.4f}m)."
            )
        elif side.upper() == "LEFT" and x > 0.02:
            raise LateralityInversionConflictError(
                f"Acupoint {code} declared side 'LEFT' but X coordinate is positive ({x:.4f}m)."
            )
        elif side.upper() == "MIDLINE" and abs(x) > 0.03:
            raise LateralityInversionConflictError(
                f"Acupoint {code} declared 'MIDLINE' but |X| is {abs(x):.4f}m (> 30mm)."
            )

    @staticmethod
    def validate_mesh_checksum(expected_hash: str, actual_hash: str, mesh_name: str):
        """Fail-closed when mesh SHA256 does not match recorded lineage."""
        if expected_hash != actual_hash:
            raise MeshChecksumMismatchError(
                f"Mesh '{mesh_name}' hash mismatch! Expected {expected_hash}, got {actual_hash}. "
                f"Refusing silent transform."
            )

    @staticmethod
    def validate_waypoint_completeness(waypoints: List[List[float]], min_count: int = 4):
        """Fail-closed when a meridian pathway lacks minimum waypoint density."""
        if len(waypoints) < min_count:
            raise IncompletePathwayError(
                f"Meridian pathway has only {len(waypoints)} waypoints, required at least {min_count}."
            )
