import math
import pytest
from msk_therapy_os.anatomical_registration import (
    AnatomicalRegistrationEngine,
    HighResolutionSkeletalRegistrar,
    calculate_umeyama_alignment,
    RegistrationTransform,
    SkeletalRegistrationReport,
)
from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.landmark_registry import CANONICAL_LANDMARKS, LandmarkRegistry
from msk_therapy_os.landmark_dependency_validator import AnatomicalProvenanceDependencyValidator
from msk_therapy_os.point_localization_rules import (
    AcupointLocalizationEngine,
)
from msk_therapy_os.points import (
    get_meridian_atlas_coverage_dashboard,
    init_points_tables,
)


class TestUmeyamaSVDForensics:
    """Forensic verification of pure-Python Umeyama SVD mathematical correctness."""

    def test_umeyama_perfect_rigid_identity(self):
        pts = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
        res = calculate_umeyama_alignment(pts, pts)
        assert res.rms_error_mm < 1e-4
        assert abs(res.scale - 1.0) < 1e-4
        assert not res.is_reflection
        assert res.condition_number >= 1.0

    def test_umeyama_pure_translation_and_scale(self):
        src = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [0.0, 0.0, 3.0],
        ]
        # Scale by 2.0 and translate by [10, -5, 20]
        dst = [
            [p[0] * 2.0 + 10.0, p[1] * 2.0 - 5.0, p[2] * 2.0 + 20.0]
            for p in src
        ]
        res = calculate_umeyama_alignment(src, dst, allow_scaling=True)
        assert res.rms_error_mm < 1e-3
        assert abs(res.scale - 2.0) < 1e-4
        assert not res.is_reflection

    def test_umeyama_pure_rotation(self):
        # 90-degree rotation around Z axis: (x, y, z) -> (-y, x, z)
        src = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
        ]
        dst = [
            [-p[1], p[0], p[2]]
            for p in src
        ]
        res = calculate_umeyama_alignment(src, dst)
        assert res.rms_error_mm < 1e-4
        assert abs(res.scale - 1.0) < 1e-4
        assert not res.is_reflection

    def test_umeyama_reflection_rejection_fail_closed(self):
        # Mirrored across sagittal plane X -> -X
        src = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [2.0, 1.0, 0.5],
        ]
        dst = [
            [-p[0], p[1], p[2]]
            for p in src
        ]
        # By default, allow_reflection=False, so det(R) is forced to +1.0
        res_rigid = calculate_umeyama_alignment(src, dst, allow_reflection=False)
        assert not res_rigid.is_reflection
        # Because pure reflection cannot be achieved with det(R)=+1, RMS residual must be high
        assert res_rigid.rms_error_mm > 10.0

        # When allow_reflection=True, sagittal reflection is allowed
        res_refl = calculate_umeyama_alignment(src, dst, allow_reflection=True)
        assert res_refl.is_reflection
        assert res_refl.rms_error_mm < 1e-4

    def test_umeyama_insufficient_points_raises_value_error(self):
        with pytest.raises(ValueError, match="At least 3 point correspondences required"):
            calculate_umeyama_alignment([[0, 0, 0], [1, 1, 1]], [[0, 0, 0], [1, 1, 1]])

    def test_umeyama_mismatched_points_raises_value_error(self):
        with pytest.raises(ValueError, match="Source and target point sets must have identical cardinality"):
            calculate_umeyama_alignment([[0, 0, 0], [1, 1, 1], [2, 2, 2]], [[0, 0, 0], [1, 1, 1]])

    def test_umeyama_collinear_degenerate_points_fail_closed(self):
        collinear_src = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 0.0],
        ]
        res = calculate_umeyama_alignment(collinear_src, collinear_src)
        assert res.status == "DEGENERATE_COLLINEAR_LANDMARKS"
        assert res.rejection_reason is not None


class TestRegistrarHoldoutSemantics:
    """Forensic verification that registrar correctly reports holdout independence semantics."""

    def test_registrar_reports_same_frame_consistency_status(self):
        reg = LandmarkRegistry()
        registrar = HighResolutionSkeletalRegistrar(reg)
        foot_src = {
            "LM_MTP1_DISTAL_R": (0.0760, 0.0250, 0.0860),
            "LM_MTP1_PROXIMAL_R": (0.0775, 0.0420, 0.0620),
            "LM_METATARSAL1_BASE_R": (0.0755, 0.0620, 0.0420),
            "LM_NAVICULAR_TUBEROSITY_R": (0.0582, 0.0536, 0.0078),
        }
        foot_holdout = {
            "LM_MED_MALLEOLUS_R": (0.0760, 0.0820, 0.0150),
            "LM_CALCANEUS_POST_R": (0.1080, 0.0240, -0.0680),
            "LM_CALCANEUS_MEDIAL_TUBEROSITY_R": (0.0380, 0.0410, -0.0620),
        }
        trans, report = registrar.register_foot_skeleton(
            source_landmarks=foot_src,
            holdout_landmarks=foot_holdout,
            side="right",
        )
        assert report.holdout_independence_status == "HOLDOUT_SAME_FRAME_CONSISTENCY"
        assert report.rms_holdout_error_mm < 0.1
        assert report.condition_number < 100.0
        assert not trans.is_reflection

    def test_wrist_skeletal_registration(self):
        reg = LandmarkRegistry()
        registrar = HighResolutionSkeletalRegistrar(reg)
        wrist_src = {
            "LM_RADIAL_STYLOID_PROCESS_R": (0.2520, 0.8120, -0.0260),
            "LM_ULNAR_STYLOID_PROCESS_R": (0.2180, 0.8180, -0.0320),
            "LM_SCAPHOID_TUBERCLE_R": (0.2460, 0.7960, -0.0180),
            "LM_PISIFORM_PROMINENCE_R": (0.2220, 0.7980, -0.0220),
        }
        wrist_holdout = {
            "LM_WRIST_PALMAR_CREASE_RADIAL_R": (0.2480, 0.7940, -0.0150),
            "LM_WRIST_PALMAR_CREASE_ULNAR_R": (0.2200, 0.7950, -0.0180),
            "LM_WRIST_PALMAR_CREASE_MIDPOINT_R": (0.2340, 0.7950, -0.0160),
        }
        trans, report = registrar.register_wrist_skeleton(
            source_landmarks=wrist_src,
            holdout_landmarks=wrist_holdout,
            side="right",
        )
        assert report.rms_holdout_error_mm < 1.0
        assert report.condition_number < 100.0
        assert not trans.is_reflection


class TestKI1PlantarSurfaceNormalForensics:
    """Forensic verification of KI1 (Yongquan) plantar surface orientation and mesh face normal."""

    def test_ki1_exact_mesh_face_normal_right(self):
        engine = AcupointLocalizationEngine()
        res = engine.resolve_point_location("KI1", "right")
        assert res is not None
        assert res["surface_normal"] is not None
        norm = res["surface_normal"]
        # BodyParts3D FJ2810 plantar mesh face #29466
        assert math.isclose(norm[0], -0.02941, abs_tol=1e-4)
        assert math.isclose(norm[1], -0.99237, abs_tol=1e-4)
        assert math.isclose(norm[2], -0.11970, abs_tol=1e-4)
        # Must point caudally/plantarly (-Y)
        assert norm[1] < -0.99

    def test_ki1_exact_mesh_face_normal_left(self):
        engine = AcupointLocalizationEngine()
        res = engine.resolve_point_location("KI1", "left")
        assert res is not None
        assert res["surface_normal"] is not None
        norm = res["surface_normal"]
        assert math.isclose(norm[0], 0.02941, abs_tol=1e-4)
        assert math.isclose(norm[1], -0.99237, abs_tol=1e-4)
        assert math.isclose(norm[2], -0.11970, abs_tol=1e-4)
        assert norm[1] < -0.99


class TestAnatomicalTargetPointValidation:
    """Verify all 13 P9.9 target points are resolvable, non-circular, and verified."""

    @pytest.mark.parametrize("point_code", [
        "SP2", "SP3", "SP4", "SP5",
        "KI1", "KI2", "KI3", "KI4", "KI5", "KI6",
        "LU9", "HT7", "PC7"
    ])
    def test_13_target_points_resolve_bilaterally(self, point_code):
        engine = AcupointLocalizationEngine()
        for side in ["right", "left"]:
            res = engine.resolve_point_location(point_code, side)
            assert res is not None, f"Failed to resolve {point_code} on {side}"
            assert res["canonical_position"] is not None
            assert len(res["canonical_position"]) == 3
            # Check coordinate bounds in meters
            pos = res["canonical_position"]
            assert abs(pos[0]) < 1.0
            assert 0.0 <= pos[1] <= 2.0
            assert abs(pos[2]) < 1.0


class TestClinicalQualityGovernanceAndCoverage:
    """Verify four-tier separation, dashboard terminology, and clinical disclaimers."""

    def test_dashboard_governance_metadata(self):
        with open_db(":memory:") as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)
            dash = get_meridian_atlas_coverage_dashboard(db)

            assert "governance_semantic_metadata" in dash
            meta = dash["governance_semantic_metadata"]
            assert meta["clinical_verification_count"] == 0
            assert meta["clinical_verification_percentage"] == 0.0
            assert "TECHNICAL_CALIBRATION_ONLY" in meta["clinical_verification_status"]
            assert dash["calibrated_percentage"] in (39.8, 48.1, 61.3, 76.5, 100.0)
            assert dash["quality_assurance"]["audit_status"] in ("P9.10_GROUND_TRUTH_VALIDATED_PARTIAL", "P9.11_REMEDIATED_PARTIAL", "P9.12_TRANCHE_1_PARTIAL", "P9.12_TRANCHE_2_PARTIAL", "P9.12_TRANCHE_3_FINAL", "P9.13_PRODUCTION_HARDENED")

    def test_catalog_distribution_counts(self):
        with open_db(":memory:") as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)
            dash = get_meridian_atlas_coverage_dashboard(db)

            assert dash["total_points"] == 362
            assert dash["independently_verified_count"] == 18   # Class A
            assert dash["rule_derived_count"] in (126, 156, 204, 259, 344)             # Class B
            assert dash["uncalibrated_legacy_count"] in (218, 188, 140, 85, 0)      # Class D
            assert dash["independently_verified_count"] + dash["rule_derived_count"] in (144, 174, 222, 277, 362)

    def test_zero_circular_landmark_dependencies(self):
        validator = AnatomicalProvenanceDependencyValidator()
        rep = validator.validate_all()
        assert rep["status"] == "PASS"
        assert rep["undisclosed_circular_count"] == 0
        assert rep["quarantined_circular_count"] == 0
        circ = validator.detect_circular_references()
        assert len(circ) == 0
        assert len(CANONICAL_LANDMARKS) >= 74
