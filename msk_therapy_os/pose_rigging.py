"""Pose-Aware Rigging, Kinematics and Guarded Surface Projection for MSK-Therapy-OS.

Translates joint angles into anatomical landmark kinematics, monitors posture validity limits,
emits UNCERTAIN_POSTURE_OFFSET for posture-sensitive crease/tendon loci,
and enforces guarded surface raycasting with normal orientation and region containment constraints.
Zero external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple

from .landmark_registry import (
    AnatomicalLandmark,
    BodyRegion,
    CANONICAL_LANDMARKS,
    LandmarkRegistry,
)

# Reference neutral physiological ranges of motion (degrees)
PHYSIOLOGICAL_ROM_BOUNDS = {
    "cervical_flexion": (0.0, 45.0),
    "cervical_extension": (0.0, 45.0),
    "cervical_lateral_flexion": (-45.0, 45.0),
    "shoulder_abduction_r": (0.0, 180.0),
    "shoulder_abduction_l": (0.0, 180.0),
    "shoulder_flexion_r": (0.0, 180.0),
    "shoulder_flexion_l": (0.0, 180.0),
    "elbow_flexion_r": (0.0, 150.0),
    "elbow_flexion_l": (0.0, 150.0),
    "knee_flexion_r": (0.0, 140.0),
    "knee_flexion_l": (0.0, 140.0),
}

# Posture-sensitive acupuncture points located at skin creases or mobile tendons
# (Require standard calibration posture; invalidate static surface coordinates when flexed)
POSTURE_SENSITIVE_ACUPOINTS = {
    "LU5": {"joint": "elbow_flexion", "threshold_deg": 15.0, "crease": "cubital", "who_ref": "WHO 2008, p. 25: cubital crease, radial side of tendon of m. biceps brachii"},
    "PC3": {"joint": "elbow_flexion", "threshold_deg": 15.0, "crease": "cubital", "who_ref": "WHO 2008, p. 165: cubital crease, ulnar side of tendon of m. biceps brachii"},
    "HT3": {"joint": "elbow_flexion", "threshold_deg": 15.0, "crease": "cubital", "who_ref": "WHO 2008, p. 95: midway between medial epicondyle and cubital crease"},
    "PC6": {"joint": "wrist_flexion", "threshold_deg": 12.0, "crease": "wrist", "who_ref": "WHO 2008, p. 167: 2 cun proximal to palmar wrist crease, between tendons"},
    "LU9": {"joint": "wrist_flexion", "threshold_deg": 10.0, "crease": "wrist", "who_ref": "WHO 2008, p. 29: radial palmar wrist crease, depression radial to radial artery"},
    "HT7": {"joint": "wrist_flexion", "threshold_deg": 10.0, "crease": "wrist", "who_ref": "WHO 2008, p. 99: palmar wrist crease, radial side of flexor carpi ulnaris tendon"},
    "BL40": {"joint": "knee_flexion", "threshold_deg": 15.0, "crease": "popliteal", "who_ref": "WHO 2008, p. 138: midpoint of popliteal crease"},
    "LR8": {"joint": "knee_flexion", "threshold_deg": 15.0, "crease": "popliteal", "who_ref": "WHO 2008, p. 219: anterior to semimembranosus tendon, level with popliteal crease"},
    "KI10": {"joint": "knee_flexion", "threshold_deg": 15.0, "crease": "popliteal", "who_ref": "WHO 2008, p. 157: medial end of popliteal crease between semitendinosus and semimembranosus"},
    "ST35": {"joint": "knee_flexion", "threshold_deg": 20.0, "crease": "patellar", "who_ref": "WHO 2008, p. 67: in depression lateral to patellar ligament with knee flexed"},
    "GB34": {"joint": "knee_flexion", "threshold_deg": 20.0, "crease": "knee", "who_ref": "WHO 2008, p. 204: antero-inferior to head of fibula"},
}

# Regional 3D Bounding Boxes for Guarded Raycasting (meters)
REGIONAL_CONTAINMENT_BOXES = {
    BodyRegion.HEAD_NECK: {
        "x": (-0.15, 0.15),
        "y": (1.45, 1.76),
        "z": (-0.16, 0.16),
    },
    BodyRegion.TORSO: {
        "x": (-0.26, 0.26),
        "y": (0.80, 1.48),
        "z": (-0.22, 0.22),
    },
    BodyRegion.UPPER_EXTREMITY: {
        "x": (0.12, 0.38),  # Right arm
        "y": (0.75, 1.45),
        "z": (-0.15, 0.15),
    },
    BodyRegion.LOWER_EXTREMITY: {
        "x": (0.03, 0.25),  # Right leg
        "y": (-0.02, 0.90),
        "z": (-0.18, 0.18),
    },
}


def rotate_point_around_axis(
    point: Tuple[float, float, float],
    pivot: Tuple[float, float, float],
    axis: Tuple[float, float, float],
    angle_rad: float
) -> Tuple[float, float, float]:
    """Rodrigues rotation formula to rotate 3D point around an arbitrary pivot and unit axis."""
    px, py, pz = point[0] - pivot[0], point[1] - pivot[1], point[2] - pivot[2]
    ax, ay, az = axis

    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Dot product (p . a)
    dot = px * ax + py * ay + pz * az

    # Cross product (a x p)
    cx = ay * pz - az * py
    cy = az * px - ax * pz
    cz = ax * py - ay * px

    rx = px * cos_a + cx * sin_a + ax * dot * (1.0 - cos_a)
    ry = py * cos_a + cy * sin_a + ay * dot * (1.0 - cos_a)
    rz = pz * cos_a + cz * sin_a + az * dot * (1.0 - cos_a)

    return (rx + pivot[0], ry + pivot[1], rz + pivot[2])


class PoseKinematicsEngine:
    """Computes pose-aware anatomical landmark transformations and posture offset uncertainty."""

    def __init__(self, landmark_registry: Optional[LandmarkRegistry] = None):
        self.registry = landmark_registry or LandmarkRegistry()

    def validate_joint_angles(self, angles: Dict[str, float]) -> Dict[str, Any]:
        """Validate joint angles against physiological human ROM limits."""
        status = "NORMAL_ROM"
        warnings = []
        clamped: Dict[str, float] = {}

        for key, val in angles.items():
            if key in PHYSIOLOGICAL_ROM_BOUNDS:
                min_a, max_a = PHYSIOLOGICAL_ROM_BOUNDS[key]
                val_f = float(val)
                if not (min_a <= val_f <= max_a):
                    warnings.append(f"Angle '{key}' ({val_f:.1f}deg) outside normal ROM [{min_a}, {max_a}].")
                    status = "EXCEEDS_NORMAL_ROM"
                clamped[key] = max(min_a, min(max_a, val_f))
            else:
                clamped[key] = float(val)

        return {
            "status": status,
            "validated_angles": clamped,
            "warnings": warnings,
        }

    def compute_pose_transformed_landmarks(
        self,
        joint_angles: Dict[str, float]
    ) -> Dict[str, Tuple[float, float, float]]:
        """Apply forward kinematic joint transformations to canonical anatomical landmarks."""
        transformed: Dict[str, Tuple[float, float, float]] = {}

        # Initialize with baseline canonical positions
        for lm in self.registry.list_landmarks():
            transformed[lm.landmark_id] = lm.canonical_position

        # 1. Cervical Flexion / Extension (Pivot at C7 Spinous Process)
        cervical_flex = float(joint_angles.get("cervical_flexion", 0.0))
        cervical_ext = float(joint_angles.get("cervical_extension", 0.0))
        net_cervical_pitch = cervical_flex - cervical_ext  # Positive = forward flexion

        c7_pos = self.registry.get_canonical_position("LM_C7_SPINE") or (0.0, 1.478, -0.092)
        if abs(net_cervical_pitch) > 0.01:
            rad = math.radians(net_cervical_pitch)
            # Pitch axis is lateral X axis: (1, 0, 0)
            pitch_axis = (1.0, 0.0, 0.0)
            cervical_landmarks = [
                "LM_VERTEX_CROWN", "LM_GLABELLA", "LM_INION",
                "LM_MASTOID_R", "LM_MASTOID_L", "LM_C2_SPINE"
            ]
            for lm_id in cervical_landmarks:
                if lm_id in transformed:
                    transformed[lm_id] = rotate_point_around_axis(
                        transformed[lm_id], c7_pos, pitch_axis, rad  # Pitch forward drops Y and advances Z
                    )

        # 2. Shoulder Abduction (Right Arm, Pivot at Right Acromion)
        shoulder_abd_r = float(joint_angles.get("shoulder_abduction_r", 0.0))
        acromion_r = self.registry.get_canonical_position("LM_ACROMION_R") or (0.188, 1.412, -0.015)
        if abs(shoulder_abd_r) > 0.01:
            rad = math.radians(shoulder_abd_r)
            # Abduction axis in sagittal Z axis: (0, 0, 1)
            abd_axis = (0.0, 0.0, 1.0)
            arm_r_landmarks = [
                "LM_AXILLARY_FOLD_ANT_R", "LM_CUBITAL_CREASE_R",
                "LM_MED_EPICONDYLE_HUMERUS_R", "LM_LAT_EPICONDYLE_HUMERUS_R",
                "LM_WRIST_CREASE_PALMAR_R", "LM_RADIAL_STYLOID_R"
            ]
            for lm_id in arm_r_landmarks:
                if lm_id in transformed:
                    transformed[lm_id] = rotate_point_around_axis(
                        transformed[lm_id], acromion_r, abd_axis, rad
                    )

        # 3. Elbow Flexion (Right Arm, Pivot at Transformed Cubital Crease)
        elbow_flex_r = float(joint_angles.get("elbow_flexion_r", 0.0))
        cubital_r = transformed.get("LM_CUBITAL_CREASE_R") or (0.246, 1.082, 0.021)
        if abs(elbow_flex_r) > 0.01:
            rad = math.radians(elbow_flex_r)
            # Flexion axis across epicondyles: (1, 0, 0)
            elbow_axis = (1.0, 0.0, 0.0)
            forearm_r_landmarks = [
                "LM_WRIST_CREASE_PALMAR_R", "LM_RADIAL_STYLOID_R"
            ]
            for lm_id in forearm_r_landmarks:
                if lm_id in transformed:
                    transformed[lm_id] = rotate_point_around_axis(
                        transformed[lm_id], cubital_r, elbow_axis, rad
                    )

        # 4. Knee Flexion (Right Leg, Pivot at Right Popliteal Crease)
        knee_flex_r = float(joint_angles.get("knee_flexion_r", 0.0))
        popliteal_r = transformed.get("LM_POPLITEAL_CREASE_R") or (0.114, 0.462, -0.052)
        if abs(knee_flex_r) > 0.01:
            rad = math.radians(knee_flex_r)
            knee_axis = (1.0, 0.0, 0.0)
            leg_r_landmarks = [
                "LM_MED_MALLEOLUS_R", "LM_LAT_MALLEOLUS_R", "LM_CALCANEUS_POST_R"
            ]
            for lm_id in leg_r_landmarks:
                if lm_id in transformed:
                    transformed[lm_id] = rotate_point_around_axis(
                        transformed[lm_id], popliteal_r, knee_axis, -rad
                    )

        return transformed

    def evaluate_acupoint_posture_status(
        self,
        point_code: str,
        joint_angles: Dict[str, float]
    ) -> Dict[str, Any]:
        """Check whether a specific point is affected by posture shift and emit UNCERTAIN_POSTURE_OFFSET."""
        base_code = point_code.replace("_R", "").replace("_L", "")
        spec = POSTURE_SENSITIVE_ACUPOINTS.get(base_code)

        if not spec:
            return {
                "point_code": point_code,
                "is_posture_sensitive": False,
                "status": "POSE_INVARIANT_BONY_ANCHOR",
                "notes": "Point anchored to rigid bony landmark unaffected by moderate joint flexion.",
            }

        joint_key = spec["joint"]
        threshold = spec["threshold_deg"]
        current_deg = 0.0

        # Match relevant joint angle
        for k, v in joint_angles.items():
            if joint_key in k:
                current_deg = max(current_deg, abs(float(v)))

        if current_deg > threshold:
            return {
                "point_code": point_code,
                "is_posture_sensitive": True,
                "status": "UNCERTAIN_POSTURE_OFFSET",
                "joint": joint_key,
                "current_angle_deg": round(current_deg, 1),
                "threshold_deg": threshold,
                "who_reference": spec["who_ref"],
                "notes": (
                    f"Joint deviation ({current_deg:.1f}deg) exceeds posture calibration threshold ({threshold:.1f}deg). "
                    f"Skin crease distortion and tendon tension invalidate static 3D coordinate localization."
                ),
            }

        return {
            "point_code": point_code,
            "is_posture_sensitive": True,
            "status": "CALIBRATED_POSE_VALID",
            "joint": joint_key,
            "current_angle_deg": round(current_deg, 1),
            "threshold_deg": threshold,
            "who_reference": spec["who_ref"],
            "notes": "Joint posture within valid calibration tolerance.",
        }


# =============================================================================
# Guarded Surface Projection (Raycasting with Containment & Normal Constraints)
# =============================================================================

class GuardedSurfaceProjector:
    """Raycasting projector enforcing surface normal angular tolerance and anatomical region bounding."""

    @staticmethod
    def check_region_containment(
        point: Tuple[float, float, float],
        region: BodyRegion,
        side: str = "right"
    ) -> bool:
        """Verify whether a 3D point in meters is inside designated regional bounding box."""
        box = REGIONAL_CONTAINMENT_BOXES.get(region)
        if not box:
            return True

        x, y, z = point
        x_min, x_max = box["x"]
        if side == "left":
            x_min, x_max = -x_max, -x_min

        return (
            x_min <= x <= x_max and
            box["y"][0] <= y <= box["y"][1] and
            box["z"][0] <= z <= box["z"][1]
        )

    @staticmethod
    def validate_surface_normal(
        surface_normal: Tuple[float, float, float],
        expected_direction: Tuple[float, float, float],
        max_angle_deg: float = 60.0
    ) -> bool:
        """Ensure mesh surface normal does not diverge more than max_angle_deg from anatomical direction.

        cos(60 deg) = 0.50.
        """
        nx, ny, nz = surface_normal
        dx, dy, dz = expected_direction

        norm_n = math.sqrt(nx * nx + ny * ny + nz * nz)
        norm_d = math.sqrt(dx * dx + dy * dy + dz * dz)

        if norm_n < 1e-6 or norm_d < 1e-6:
            return False

        dot = (nx * dx + ny * dy + nz * dz) / (norm_n * norm_d)
        min_cos = math.cos(math.radians(max_angle_deg))
        return dot >= min_cos

    def project_safely(
        self,
        point_anchor: Tuple[float, float, float],
        surface_hit: Tuple[float, float, float],
        surface_normal: Tuple[float, float, float],
        expected_direction: Tuple[float, float, float],
        region: BodyRegion,
        side: str = "right"
    ) -> Dict[str, Any]:
        """Perform guarded projection validation against containment and normal deviation."""
        # Check 1: Regional containment of hit point
        if not self.check_region_containment(surface_hit, region, side):
            return {
                "projected_point": None,
                "status": "PROJECTION_OUTSIDE_CONTAINMENT",
                "rejection_reason": (
                    f"Surface raycast intersection {surface_hit} breached regional containment envelope for {region.value} ({side})."
                ),
            }

        # Check 2: Surface normal inclination
        if not self.validate_surface_normal(surface_normal, expected_direction, max_angle_deg=60.0):
            return {
                "projected_point": None,
                "status": "NORMAL_INCLINATION_REJECTED",
                "rejection_reason": (
                    f"Surface normal {surface_normal} deviates > 60 degrees from expected anatomical outward direction {expected_direction}."
                ),
            }

        # Successful guarded projection
        return {
            "projected_point": [round(c, 5) for c in surface_hit],
            "surface_normal": [round(n, 5) for n in surface_normal],
            "status": "SURFACE_REGISTERED_FJ2810",
            "region": region.value,
        }
