"""Comprehensive unit and integration tests for P9 Pose-Aware Rigging and Guarded Surface Projection."""
import math
import pytest

from msk_therapy_os.landmark_registry import LandmarkRegistry, BodyRegion
from msk_therapy_os.pose_rigging import (
    PoseKinematicsEngine,
    GuardedSurfaceProjector,
    rotate_point_around_axis,
    POSTURE_SENSITIVE_ACUPOINTS,
)


def test_rodrigues_3d_rotation():
    """Verify 3D Rodrigues rotation formula around arbitrary pivot and axis."""
    pivot = (0.0, 1.0, 0.0)
    point = (0.0, 1.0, 1.0)  # 1 meter in front along Z
    axis = (0.0, 1.0, 0.0)   # Y axis (Yaw)

    # Rotate 90 degrees around Y axis (pi/2)
    # Rotating (0, 0, 1) around Y by +90 deg should place it at (+1, 0, 0)
    res = rotate_point_around_axis(point, pivot, axis, math.pi / 2.0)
    assert res[0] == pytest.approx(1.0, abs=1e-4)
    assert res[1] == pytest.approx(1.0, abs=1e-4)
    assert res[2] == pytest.approx(0.0, abs=1e-4)


def test_forward_kinematic_landmark_transformation():
    """Verify joint angles transform dependent anatomical landmarks."""
    kin = PoseKinematicsEngine()
    reg = LandmarkRegistry()

    # Baseline glabella
    base_glabella = reg.get_canonical_position("LM_GLABELLA")

    # Apply 30 degrees cervical flexion (pitch forward)
    transformed = kin.compute_pose_transformed_landmarks({"cervical_flexion": 30.0})
    flexed_glabella = transformed["LM_GLABELLA"]

    # When head pitches forward, glabella moves anteriorly (+Z) and descends (-Y)
    assert flexed_glabella[1] < base_glabella[1]

    # Baseline right wrist
    base_wrist = reg.get_canonical_position("LM_WRIST_CREASE_PALMAR_R")

    # Apply 45 degrees shoulder abduction (lateral elevation)
    abd_transformed = kin.compute_pose_transformed_landmarks({"shoulder_abduction_r": 45.0})
    abd_wrist = abd_transformed["LM_WRIST_CREASE_PALMAR_R"]

    # Wrist should move laterally (+X) and superiorly (+Y)
    assert abd_wrist[0] > base_wrist[0]
    assert abd_wrist[1] > base_wrist[1]


def test_posture_sensitive_acupoint_evaluation():
    """Verify UNCERTAIN_POSTURE_OFFSET emission when joint flexion exceeds calibration threshold."""
    kin = PoseKinematicsEngine()

    # 1. Elbow flexion = 35 deg (> 15 deg threshold for LU5)
    lu5_eval = kin.evaluate_acupoint_posture_status("LU5", {"elbow_flexion_r": 35.0})
    assert lu5_eval["is_posture_sensitive"] is True
    assert lu5_eval["status"] == "UNCERTAIN_POSTURE_OFFSET"
    assert "exceeds posture calibration threshold" in lu5_eval["notes"]

    # 2. Elbow flexion = 8 deg (<= 15 deg threshold)
    lu5_calibrated = kin.evaluate_acupoint_posture_status("LU5", {"elbow_flexion_r": 8.0})
    assert lu5_calibrated["status"] == "CALIBRATED_POSE_VALID"

    # 3. Knee flexion = 40 deg (> 15 deg threshold for BL40 popliteal crease)
    bl40_eval = kin.evaluate_acupoint_posture_status("BL40", {"knee_flexion_r": 40.0})
    assert bl40_eval["status"] == "UNCERTAIN_POSTURE_OFFSET"

    # 4. Invariant bony point (GV14 at C7 spinous process)
    gv14_eval = kin.evaluate_acupoint_posture_status("GV14", {"elbow_flexion_r": 45.0})
    assert gv14_eval["is_posture_sensitive"] is False
    assert gv14_eval["status"] == "POSE_INVARIANT_BONY_ANCHOR"


def test_physiological_rom_bounds_validation():
    """Verify validation and warnings when joint angles exceed physiological limits."""
    kin = PoseKinematicsEngine()

    # Normal ROM
    normal_res = kin.validate_joint_angles({
        "cervical_flexion": 30.0,
        "shoulder_abduction_r": 90.0,
        "elbow_flexion_r": 60.0
    })
    assert normal_res["status"] == "NORMAL_ROM"
    assert len(normal_res["warnings"]) == 0

    # Excessive ROM (cervical flexion 80 deg > 45 deg limit)
    excess_res = kin.validate_joint_angles({
        "cervical_flexion": 80.0,
    })
    assert excess_res["status"] == "EXCEEDS_NORMAL_ROM"
    assert len(excess_res["warnings"]) > 0
    assert excess_res["validated_angles"]["cervical_flexion"] == 45.0  # Clamped to physiological max


def test_guarded_surface_projection():
    """Verify guarded raycast constraints: normal deviation <= 60 deg and regional containment."""
    projector = GuardedSurfaceProjector()

    # Case 1: Ideal anterior projection on torso
    anchor = (0.0, 1.2, 0.05)
    surface_hit = (0.0, 1.2, 0.10)
    normal = (0.0, 0.0, 1.0)
    expected_dir = (0.0, 0.0, 1.0)

    res1 = projector.project_safely(anchor, surface_hit, normal, expected_dir, BodyRegion.TORSO)
    assert res1["status"] == "SURFACE_REGISTERED_FJ2810"
    assert res1["projected_point"] == [0.0, 1.2, 0.1]

    # Case 2: Surface normal flipped backwards (> 60 deg deviation)
    flipped_normal = (0.0, 0.0, -1.0)
    res2 = projector.project_safely(anchor, surface_hit, flipped_normal, expected_dir, BodyRegion.TORSO)
    assert res2["status"] == "NORMAL_INCLINATION_REJECTED"
    assert res2["projected_point"] is None

    # Case 3: Surface normal at 45 deg inclination (<= 60 deg: PASS)
    angle_45_normal = (0.0, math.sin(math.pi / 4.0), math.cos(math.pi / 4.0))
    res3 = projector.project_safely(anchor, surface_hit, angle_45_normal, expected_dir, BodyRegion.TORSO)
    assert res3["status"] == "SURFACE_REGISTERED_FJ2810"

    # Case 4: Surface normal at 75 deg inclination (> 60 deg: REJECT)
    angle_75_normal = (0.0, math.sin(math.radians(75.0)), math.cos(math.radians(75.0)))
    res4 = projector.project_safely(anchor, surface_hit, angle_75_normal, expected_dir, BodyRegion.TORSO)
    assert res4["status"] == "NORMAL_INCLINATION_REJECTED"

    # Case 5: Ray penetrates across body boundary into opposite/incorrect region
    # Hit point X=0.0 (midline) for Upper Extremity (which requires X in [0.12, 0.38])
    cross_hit = (0.0, 1.2, 0.10)
    res5 = projector.project_safely(anchor, cross_hit, normal, expected_dir, BodyRegion.UPPER_EXTREMITY, side="right")
    assert res5["status"] == "PROJECTION_OUTSIDE_CONTAINMENT"
    assert res5["projected_point"] is None
