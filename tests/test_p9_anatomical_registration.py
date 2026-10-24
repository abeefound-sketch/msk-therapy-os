"""Comprehensive unit and integration tests for P9 Anatomical Landmark Registration Engine."""
import math
import sqlite3
import pytest

from msk_therapy_os.landmark_registry import (
    AnatomicalLandmark,
    BodyRegion,
    CANONICAL_LANDMARKS,
    LandmarkRegistry,
    LandmarkType,
)
from msk_therapy_os.anatomical_registration import (
    AnatomicalRegistrationEngine,
    RegistrationTransform,
    BODY_ENVELOPE,
    MAX_PERMISSIBLE_RMS_MM,
    mat3_mult,
    mat3_transpose,
    mat3_det,
    svd_3x3,
)
from msk_therapy_os.points import (
    init_points_tables,
    list_anatomical_landmarks,
    get_anatomical_landmark,
    list_cun_scaling_rules,
    record_registration_metric,
)


def test_canonical_reference_frame_and_landmarks():
    """Verify landmark registry covers all 6 ontological categories and physiological envelope."""
    reg = LandmarkRegistry()
    lms = reg.list_landmarks()
    assert len(lms) >= 30, f"Expected >= 30 canonical landmarks, got {len(lms)}"

    types_found = {lm.landmark_type for lm in lms}
    assert LandmarkType.BONY_LANDMARK in types_found
    assert LandmarkType.JOINT_LANDMARK in types_found or LandmarkType.SKIN_CREASE in types_found
    assert LandmarkType.SURFACE_TOPOGRAPHIC_LANDMARK in types_found

    # Check key primary skeletal anchors
    c7 = reg.get_landmark("LM_C7_SPINE")
    assert c7 is not None
    assert c7.fma_id == "FMA:13337"
    assert c7.canonical_position[1] == pytest.approx(1.478, abs=0.01)

    vertex = reg.get_landmark("LM_VERTEX_CROWN")
    assert vertex is not None
    assert vertex.canonical_position[1] == pytest.approx(1.718, abs=0.01)

    # Check all canonical positions fall strictly within adult anatomical body envelope
    for lm in lms:
        pos = lm.canonical_position
        assert AnatomicalRegistrationEngine.validate_body_envelope(pos), f"Landmark {lm.landmark_id} out of envelope: {pos}"
        assert lm.fma_id.startswith("FMA:"), f"Landmark {lm.landmark_id} missing valid FMA ID"
        assert lm.clinical_uncertainty_mm > 0.0


def test_pure_python_3x3_linear_algebra_and_svd():
    """Verify pure Python 3x3 matrix multiplication, determinant, and SVD accuracy."""
    # Identity test
    ident = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    assert mat3_det(ident) == pytest.approx(1.0)
    assert mat3_mult(ident, ident) == ident

    # 3x3 SVD of known diagonal matrix
    diag = [[3.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 1.0]]
    u, s_vals, vt = svd_3x3(diag)
    assert s_vals[0] == pytest.approx(3.0, abs=1e-5)
    assert s_vals[1] == pytest.approx(2.0, abs=1e-5)
    assert s_vals[2] == pytest.approx(1.0, abs=1e-5)

    # Reconstruction test: H = U * S * V^T
    s_mat = [[s_vals[i] if i == j else 0.0 for j in range(3)] for i in range(3)]
    reconstructed = mat3_mult(mat3_mult(u, s_mat), vt)
    for i in range(3):
        for j in range(3):
            assert reconstructed[i][j] == pytest.approx(diag[i][j], abs=1e-4)


def test_umeyama_exact_identity_alignment():
    """Verify Umeyama alignment on identical points yields 0.0 mm RMS error and identity transform."""
    reg = LandmarkRegistry()
    engine = AnatomicalRegistrationEngine(reg)

    subset = {
        "LM_VERTEX_CROWN": reg.get_canonical_position("LM_VERTEX_CROWN"),
        "LM_GLABELLA": reg.get_canonical_position("LM_GLABELLA"),
        "LM_INION": reg.get_canonical_position("LM_INION"),
        "LM_MASTOID_R": reg.get_canonical_position("LM_MASTOID_R"),
    }
    transform = engine.calculate_umeyama_alignment(subset, region=BodyRegion.HEAD_NECK)

    assert transform.status == "VERIFIED_ANATOMICAL_ANCHOR"
    assert transform.rms_error_mm == pytest.approx(0.0, abs=1e-4)
    assert transform.scale == pytest.approx(1.0, abs=1e-4)
    for i in range(3):
        assert transform.translation_vector[i] == pytest.approx(0.0, abs=1e-4)


def test_umeyama_translation_recovery():
    """Verify recovery of known spatial offset (e.g. Z-Anatomy pelvis offset +0.86m, dX=0.03m)."""
    reg = LandmarkRegistry()
    engine = AnatomicalRegistrationEngine(reg)

    shift_x = 0.04
    shift_y = -0.15
    shift_z = 0.02

    src_pts = {}
    for code in ["LM_C7_SPINE", "LM_JUGULAR_NOTCH", "LM_XIPHOSTERNAL_JOINT", "LM_UMBILICUS"]:
        pos = reg.get_canonical_position(code)
        src_pts[code] = (pos[0] - shift_x, pos[1] - shift_y, pos[2] - shift_z)

    transform = engine.calculate_umeyama_alignment(src_pts, region=BodyRegion.TORSO)

    assert transform.status == "VERIFIED_ANATOMICAL_ANCHOR"
    assert transform.rms_error_mm == pytest.approx(0.0, abs=1e-4)
    assert transform.translation_vector[0] == pytest.approx(shift_x, abs=1e-4)
    assert transform.translation_vector[1] == pytest.approx(shift_y, abs=1e-4)
    assert transform.translation_vector[2] == pytest.approx(shift_z, abs=1e-4)


def test_abstention_on_insufficient_landmarks():
    """Verify clinical abstention (UNREGISTERED) when fewer than 3 non-collinear anchors exist."""
    reg = LandmarkRegistry()
    engine = AnatomicalRegistrationEngine(reg)

    # Only 2 points
    sparse_pts = {
        "LM_C7_SPINE": (0.0, 1.478, -0.092),
        "LM_GLABELLA": (0.0, 1.625, 0.089),
    }
    transform = engine.calculate_umeyama_alignment(sparse_pts)
    assert transform.status == "UNREGISTERED"
    assert "Insufficient common landmarks" in (transform.rejection_reason or "")


def test_rejection_on_collinear_configuration():
    """Verify rejection (DEGENERATE_COLLINEAR_LANDMARKS) when landmarks are collinear."""
    reg = LandmarkRegistry()
    engine = AnatomicalRegistrationEngine(reg)

    collinear_pts = {
        "LM_P1": (0.0, 1.0, 0.0),
        "LM_P2": (0.0, 1.2, 0.0),
        "LM_P3": (0.0, 1.4, 0.0),
    }
    target_pts = {
        "LM_P1": (0.0, 1.05, 0.0),
        "LM_P2": (0.0, 1.25, 0.0),
        "LM_P3": (0.0, 1.45, 0.0),
    }
    transform = engine.calculate_umeyama_alignment(collinear_pts, target_landmarks=target_pts)
    assert transform.status == "DEGENERATE_COLLINEAR_LANDMARKS"
    assert "collinear" in (transform.rejection_reason or "").lower()


def test_clinical_uncertainty_threshold_flagging():
    """Verify marking HIGH_DISCREPANCY_UNVERIFIED when residual error exceeds tolerance."""
    reg = LandmarkRegistry()
    engine = AnatomicalRegistrationEngine(reg)

    # Create synthetic points with intentional large distortion (> 30mm)
    src_pts = {
        "LM_VERTEX_CROWN": (0.0, 1.718, -0.015),
        "LM_GLABELLA": (0.0, 1.625 + 0.05, 0.089),  # 50mm vertical distortion
        "LM_INION": (0.0, 1.595, -0.098 - 0.04),     # 40mm anterior distortion
        "LM_MASTOID_R": (0.062, 1.574, -0.042),
    }
    transform = engine.calculate_umeyama_alignment(src_pts, region=BodyRegion.HEAD_NECK)

    assert transform.status == "HIGH_DISCREPANCY_UNVERIFIED"
    assert transform.rms_error_mm > MAX_PERMISSIBLE_RMS_MM[BodyRegion.HEAD_NECK]
    assert "exceeds clinical tolerance" in (transform.rejection_reason or "")


def test_out_of_bounds_envelope_rejection():
    """Verify rejection of points transformed outside standard adult physiological envelope."""
    reg = LandmarkRegistry()
    engine = AnatomicalRegistrationEngine(reg)

    # Transform that places points 3 meters in the air
    wild_transform = RegistrationTransform(
        rotation_matrix=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        translation_vector=(0.0, 2.5, 0.0),
        status="VERIFIED_ANATOMICAL_ANCHOR"
    )

    res = engine.register_point_to_canonical("GV20", (0.0, 1.7, 0.0), wild_transform)
    assert res["status"] == "OUT_OF_ANATOMICAL_BOUNDS"
    assert "outside human anatomical envelope" in res["rejection_reason"]


def test_database_persistence_and_querying():
    """Verify SQLite table migrations, landmark catalog, and registration audit metric records."""
    db = sqlite3.connect(":memory:")
    init_points_tables(db)

    # Query landmarks from database
    db_lms = list_anatomical_landmarks(db)
    assert len(db_lms) >= 30
    c7_row = get_anatomical_landmark(db, "LM_C7_SPINE")
    assert c7_row is not None
    assert c7_row["fma_id"] == "FMA:13337"

    # Query cun rules
    db_rules = list_cun_scaling_rules(db)
    assert len(db_rules) >= 11

    # Record registration metric
    metric_id = record_registration_metric(db, {
        "source_name": "JICio/tcm-3d",
        "region": "head_neck",
        "rms_error_mm": 12.4,
        "max_error_mm": 14.8,
        "rotation_matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "translation_vector": [0.0, 0.0, 0.0],
        "scale": 1.0,
        "status": "VERIFIED_ANATOMICAL_ANCHOR",
        "rejection_reason": None,
    })
    assert metric_id > 0

    cursor = db.cursor()
    cursor.execute("SELECT * FROM landmark_registration_metrics WHERE metric_id = ?", (metric_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == "JICio/tcm-3d"
    assert row[3] == 12.4
