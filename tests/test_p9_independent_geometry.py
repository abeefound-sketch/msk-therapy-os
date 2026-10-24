"""Independent Geometric and Mathematical Validation Tests for P9 (QA Specialist Suite).

Uses NumPy in the test environment to cross-validate pure-Python SVD, Umeyama alignment,
Rodrigues rotation kinematics, and dual-denominator Cun scaling mathematics.
Ensures zero external dependency in runtime codebase while maintaining independent QA rigor.
"""
import math
import numpy as np
import pytest

from msk_therapy_os.landmark_registry import LandmarkRegistry, BodyRegion
from msk_therapy_os.anatomical_registration import (
    AnatomicalRegistrationEngine,
    svd_3x3,
    mat3_mult,
    mat3_transpose,
    mat3_det,
)
from msk_therapy_os.cun_scaling import CunScalingEngine
from msk_therapy_os.pose_rigging import (
    PoseKinematicsEngine,
    rotate_point_around_axis,
)


def test_independent_svd_against_numpy():
    """Cross-validate pure-Python svd_3x3 against numpy.linalg.svd."""
    # Test across multiple pseudo-random 3x3 matrices
    np.random.seed(42)
    for i in range(10):
        h_np = np.random.randn(3, 3)
        h_list = h_np.tolist()

        # Pure-Python SVD
        u_py, s_py, vt_py = svd_3x3(h_list)

        # NumPy SVD
        u_np, s_np, vt_np = np.linalg.svd(h_np)

        # 1. Compare Singular Values (invariant to sign)
        for k in range(3):
            assert s_py[k] == pytest.approx(s_np[k], abs=1e-4)

        # 2. Check Pure-Python Matrix Reconstruction: H = U * S * V^T
        u_mat = np.array(u_py)
        s_mat = np.diag(s_py)
        vt_mat = np.array(vt_py)
        reconstructed = u_mat @ s_mat @ vt_mat

        np.testing.assert_allclose(reconstructed, h_np, atol=1e-4)

        # 3. Check Orthogonality of U and V
        np.testing.assert_allclose(u_mat.T @ u_mat, np.eye(3), atol=1e-5)
        np.testing.assert_allclose(vt_mat @ vt_mat.T, np.eye(3), atol=1e-5)


def test_independent_umeyama_against_numpy_ground_truth():
    """Cross-validate Umeyama 3D alignment against an independent NumPy solver."""
    reg = LandmarkRegistry()
    engine = AnatomicalRegistrationEngine(reg)

    # 4 Canonical Anchors forming a true 3D non-planar tetrahedron
    anchor_keys = ["LM_C7_SPINE", "LM_XIPHOSTERNAL_JOINT", "LM_ASIS_R", "LM_ASIS_L"]
    canonical_coords = [reg.get_canonical_position(k) for k in anchor_keys]
    dst_np = np.array(canonical_coords)

    # Apply known 3D rotation (yaw 15 deg, pitch 10 deg) and translation
    theta_y = np.radians(15.0)
    theta_x = np.radians(10.0)
    ry = np.array([
        [np.cos(theta_y), 0, np.sin(theta_y)],
        [0, 1, 0],
        [-np.sin(theta_y), 0, np.cos(theta_y)]
    ])
    rx = np.array([
        [1, 0, 0],
        [0, np.cos(theta_x), -np.sin(theta_x)],
        [0, np.sin(theta_x), np.cos(theta_x)]
    ])
    r_known = ry @ rx
    t_known = np.array([0.05, -0.12, 0.08])

    # Generate source coordinates: src = R^T * (dst - t)
    src_np = (r_known.T @ (dst_np - t_known).T).T

    source_landmarks = {anchor_keys[i]: tuple(src_np[i]) for i in range(len(anchor_keys))}

    # Run Pure-Python Registration
    transform = engine.calculate_umeyama_alignment(source_landmarks, region=BodyRegion.TORSO)

    assert transform.status == "VERIFIED_ANATOMICAL_ANCHOR"
    assert transform.rms_error_mm == pytest.approx(0.0, abs=1e-3)

    # Verify recovered rotation against known matrix
    r_recovered = np.array(transform.rotation_matrix)
    np.testing.assert_allclose(r_recovered, r_known, atol=1e-3)

    # Verify recovered translation against known vector
    t_recovered = np.array(transform.translation_vector)
    np.testing.assert_allclose(t_recovered, t_known, atol=1e-3)


def test_independent_rodrigues_rotation_against_matrix_formula():
    """Verify rotate_point_around_axis matches matrix exponential / Rodrigues matrix."""
    pivot = (0.1, 1.2, -0.05)
    point = (0.25, 1.05, 0.12)
    axis = (0.0, 0.0, 1.0)  # Sagittal rotation around Z
    angle_rad = np.radians(35.0)

    # Pure-Python Rodrigues result
    p_py = rotate_point_around_axis(point, pivot, axis, angle_rad)

    # NumPy standard rotation matrix
    v = np.array(point) - np.array(pivot)
    k_mat = np.array([
        [0, -axis[2], axis[1]],
        [axis[2], 0, -axis[0]],
        [-axis[1], axis[0], 0]
    ])
    r_matrix = np.eye(3) + np.sin(angle_rad) * k_mat + (1.0 - np.cos(angle_rad)) * (k_mat @ k_mat)
    p_np = np.array(pivot) + r_matrix @ v

    np.testing.assert_allclose(p_py, p_np, atol=1e-5)


def test_cun_scaling_dual_denominator_formulas():
    """Verify mathematical definitions of deviation_from_global_pct and ratio_vs_forearm_pct."""
    engine = CunScalingEngine()
    metrics = engine.calculate_segment_metrics()

    forearm_m = metrics["SEG_FOREARM_ELBOW_TO_WRIST_R"]
    chest_m = metrics["SEG_CHEST_BINIPPLE"]
    mastoid_m = metrics["SEG_HEAD_MASTOID_TRANSVERSE"]

    # 1. Global Mean Baseline = 1720 / 75 = 22.933 mm
    global_mean = 1720.0 / 75.0

    # Chest deviation from global mean
    expected_chest_global = ((chest_m.mm_per_cun - global_mean) / global_mean) * 100.0
    assert chest_m.deviation_from_global_pct == pytest.approx(expected_chest_global, abs=0.05)
    assert chest_m.deviation_from_global_pct == pytest.approx(43.90, abs=0.1)

    # Chest ratio relative to forearm base (~20.34 mm)
    expected_chest_forearm = ((chest_m.mm_per_cun - forearm_m.mm_per_cun) / forearm_m.mm_per_cun) * 100.0
    assert chest_m.ratio_vs_forearm_pct == pytest.approx(expected_chest_forearm, abs=0.05)
    assert chest_m.ratio_vs_forearm_pct == pytest.approx(62.24, abs=0.2)

    # Mastoid deviation from global mean
    expected_mastoid_global = ((mastoid_m.mm_per_cun - global_mean) / global_mean) * 100.0
    assert mastoid_m.deviation_from_global_pct == pytest.approx(expected_mastoid_global, abs=0.05)
    assert mastoid_m.deviation_from_global_pct == pytest.approx(-39.92, abs=0.1)

    # Mastoid ratio relative to forearm base
    expected_mastoid_forearm = ((mastoid_m.mm_per_cun - forearm_m.mm_per_cun) / forearm_m.mm_per_cun) * 100.0
    assert mastoid_m.ratio_vs_forearm_pct == pytest.approx(expected_mastoid_forearm, abs=0.05)
    assert mastoid_m.ratio_vs_forearm_pct == pytest.approx(-32.25, abs=0.2)


def test_level_a_b_c_abstention_semantics():
    """Verify that Level A geometry correctness does not bypass Level C clinical abstention."""
    reg = LandmarkRegistry()
    engine = AnatomicalRegistrationEngine(reg)
    kin = PoseKinematicsEngine(reg)

    # Level A: Mathematical correctness on synthetic points
    # Even though math passes with 0.0 error:
    pts = {
        "LM_C7_SPINE": reg.get_canonical_position("LM_C7_SPINE"),
        "LM_GLABELLA": reg.get_canonical_position("LM_GLABELLA"),
        "LM_INION": reg.get_canonical_position("LM_INION"),
    }
    t = engine.calculate_umeyama_alignment(pts, region=BodyRegion.HEAD_NECK)
    assert t.status == "VERIFIED_ANATOMICAL_ANCHOR"  # Level B: within engineering threshold

    # Level C: Posture shift on mobile crease points MUST abstain and emit UNCERTAIN_POSTURE_OFFSET
    pose_res = kin.evaluate_acupoint_posture_status("LU5", {"elbow_flexion_r": 30.0})
    assert pose_res["status"] == "UNCERTAIN_POSTURE_OFFSET"
    assert "exceeds posture calibration threshold" in pose_res["notes"]
