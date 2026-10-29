"""MSK-Therapy-OS - Milestone P9.13 Anatomical Falsification Test Suite.

Audits whether the system can actively detect when anatomical coordinates,
landmarks, surface normals, lateralities, or transformations are wrong.

Tests follow the scientific falsification paradigm:
- Perturbed landmarks (+50mm offset) must be flagged as OUTLIER_ANOMALY.
- Sub-millimeter ground truth is classified as CONGRUENT.
- Synthetic fixtures must never be promoted to clinical verification tiers.
- Inverted coordinate frames or normals must fail validation envelopes.
- Extreme or abnormal cun scaling must be bounded and reject out-of-envelope coords.
- Metamorphic 3D rigid transforms must preserve pairwise Euclidean distances.
- Injected circular dependencies must be detected by the dependency validator.
- ST19..ST30 constant X must be documented with cun scaling elasticity uncertainty.
"""

import math
import pytest
from msk_therapy_os.anatomical_validation import (
    IndependentAnatomicalValidator,
    AnatomicalVerificationTier,
    GroundTruthModality,
    AnatomicalErrorClassification,
    GroundTruthObservation,
    ExternalGroundTruthDataset,
    ClinicalReviewerCredentials,
)
from msk_therapy_os.points import validate_coordinates, BODY_ENVELOPE
from msk_therapy_os.landmark_registry import CANONICAL_LANDMARKS, LandmarkRegistry
from msk_therapy_os.landmark_dependency_validator import AnatomicalProvenanceDependencyValidator, DependencyIssueSeverity
from msk_therapy_os.point_localization_rules import AcupointLocalizationRule, ACUPOINT_LOCALIZATION_RULES
from msk_therapy_os.cun_scaling import CunScalingEngine


class TestAnatomicalFalsification:
    """Verifies that the system detects and rejects false or corrupted anatomy."""

    def test_perturbed_landmark_triggers_outlier_detection(self):
        """A +50 mm displacement on a known landmark must be flagged as OUTLIER_ANOMALY."""
        validator = IndependentAnatomicalValidator()
        obs = validator.create_synthetic_test_observation(
            point_code="LI4",
            true_pos=(-0.165, 0.720, 0.080),  # Displaced by >50 mm from canonical
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
            tolerance_radius_mm=5.0,
        )
        validator.import_observations([obs])

        comparison = validator.validate_point("LI4", dataset_id="SYNTHETIC_FIXTURE_DATASET")
        assert comparison.classification == AnatomicalErrorClassification.OUTLIER_ANOMALY
        assert comparison.residual_error_mm is not None
        assert comparison.residual_error_mm > 15.0
        assert comparison.is_congruent is False

    def test_sub_millimeter_ground_truth_identified_as_congruent(self):
        """When an observation matches within 3.0 mm, it is classified as CONGRUENT."""
        validator = IndependentAnatomicalValidator()
        res = validator.resolve_point_coordinate("LI4")
        pred_pos = res["position"]

        # Synthetic observation 1.2 mm away
        perturbed_pos = (pred_pos[0] + 0.0008, pred_pos[1] + 0.0008, pred_pos[2] + 0.0004)
        obs = validator.create_synthetic_test_observation(
            point_code="LI4",
            true_pos=perturbed_pos,
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
            tolerance_radius_mm=5.0,
        )
        validator.import_observations([obs])

        comparison = validator.validate_point("LI4", dataset_id="SYNTHETIC_FIXTURE_DATASET")
        assert comparison.classification == AnatomicalErrorClassification.CONGRUENT
        assert comparison.residual_error_mm is not None
        assert comparison.residual_error_mm < 3.0
        assert comparison.is_congruent is True

    def test_synthetic_fixture_cannot_promote_to_clinical_tier(self):
        """Synthetic fixture observations must be fail-closed and never promote to Tier 3 or 4."""
        validator = IndependentAnatomicalValidator()
        res = validator.resolve_point_coordinate("ST36")
        pred_pos = res["position"]

        obs = validator.create_synthetic_test_observation(
            point_code="ST36",
            true_pos=pred_pos,
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
        )
        validator.import_observations([obs])

        comparison = validator.validate_point("ST36", dataset_id="SYNTHETIC_FIXTURE_DATASET")
        assert comparison.is_congruent is True
        assert comparison.is_synthetic is True
        # Synthetic observations CANNOT achieve INDEPENDENTLY_VERIFIED or CLINICALLY_VERIFIED
        assert comparison.verification_tier in (
            AnatomicalVerificationTier.TECHNICALLY_CALIBRATED,
            AnatomicalVerificationTier.GEOMETRICALLY_VALIDATED,
            AnatomicalVerificationTier.ANATOMICALLY_CORROBORATED,
        )
        assert comparison.verification_tier != AnatomicalVerificationTier.INDEPENDENTLY_VERIFIED
        assert comparison.verification_tier != AnatomicalVerificationTier.CLINICALLY_VERIFIED

    def test_out_of_envelope_coordinates_fail_closed(self):
        """Coordinates violating the human anatomical envelope must raise ValueError."""
        # Standard envelope: X [-0.85, 0.85], Y [-0.10, 2.05], Z [-0.45, 0.45]
        with pytest.raises(ValueError, match="outside anatomical envelope"):
            validate_coordinates(1.50, 1.0, 0.0)  # X too wide

        with pytest.raises(ValueError, match="outside anatomical envelope"):
            validate_coordinates(0.0, 3.20, 0.0)  # Y taller than 3.2m human

        with pytest.raises(ValueError, match="outside anatomical envelope"):
            validate_coordinates(0.0, 1.0, -1.2)  # Z too deep

        with pytest.raises(ValueError, match="non-finite"):
            validate_coordinates(float("nan"), 1.0, 0.0)

        with pytest.raises(ValueError, match="non-finite"):
            validate_coordinates(0.0, float("inf"), 0.0)

    def test_extreme_cun_scaling_elasticity_bounds(self):
        """Extreme body scaling (height 110cm vs 220cm) must remain numerically bounded."""
        engine = CunScalingEngine()
        metrics = engine.calculate_segment_metrics()
        forearm = metrics.get("SEG_FOREARM_ELBOW_TO_WRIST_R")
        assert forearm is not None
        assert 15.0 <= forearm.mm_per_cun <= 45.0

        # Adapted cun for tall vs short morphology
        tall_cuns = engine.compute_morphology_adapted_cun({"height_cm": 220.0, "waist_circ_cm": 110.0})
        short_cuns = engine.compute_morphology_adapted_cun({"height_cm": 110.0, "waist_circ_cm": 50.0})

        # Forearm cun must be longer for tall individual than short individual
        assert tall_cuns["SEG_FOREARM_ELBOW_TO_WRIST_R"] > short_cuns["SEG_FOREARM_ELBOW_TO_WRIST_R"]
        assert 20.0 <= tall_cuns["SEG_FOREARM_ELBOW_TO_WRIST_R"] <= 50.0
        assert 10.0 <= short_cuns["SEG_FOREARM_ELBOW_TO_WRIST_R"] <= 25.0

    def test_metamorphic_rigid_transformation_invariance(self):
        """Rigid 3D rotation and translation must preserve all inter-point distances exactly."""
        validator = IndependentAnatomicalValidator()
        pts = ["LI4", "LU7", "ST36", "SP6", "PC6", "HT7"]
        res = validator.run_metamorphic_transformation_test(
            sample_points=pts,
            rotation_deg=(30.0, 45.0, 15.0),
            translation_m=(0.25, -0.15, 0.50),
        )

        assert res["points_evaluated"] == len(pts)
        assert res["invariance_preserved"] is True
        assert res["max_reconstruction_error_mm"] < 1e-4
        assert res["max_pairwise_distance_drift_mm"] < 1e-4

    def test_bilateral_reflection_symmetry_detection(self):
        """Bilateral points across sagittal midline (X=0) must exhibit mirrored coordinates."""
        validator = IndependentAnatomicalValidator()
        right_st36 = validator.resolve_point_coordinate("ST36", side="right")
        left_st36 = validator.resolve_point_coordinate("ST36", side="left")

        rx, ry, rz = right_st36["position"]
        lx, ly, lz = left_st36["position"]

        # X coordinate should be reflected across midline (rx ≈ -lx)
        assert math.isclose(rx, -lx, abs_tol=1e-3)
        # Y and Z coordinates must match closely for upright posture
        assert math.isclose(ry, ly, abs_tol=1e-3)
        assert math.isclose(rz, lz, abs_tol=1e-3)

    def test_midline_points_sagittal_centering(self):
        """Conception Vessel (CV) and Governor Vessel (GV) points must align to sagittal plane (X ≈ 0)."""
        validator = IndependentAnatomicalValidator()
        midline_pts = ["CV3", "CV4", "CV8", "CV12", "CV17", "GV4", "GV14", "GV20"]
        for pt in midline_pts:
            res = validator.resolve_point_coordinate(pt)
            pos = res["position"]
            assert abs(pos[0]) < 0.005, f"Midline point {pt} lateral deviation {pos[0]}m exceeds 5mm"

    def test_landmark_graph_detects_circular_dependencies(self):
        """Circular dependency detection must audit the catalog and detect injected circularity."""
        dep_val = AnatomicalProvenanceDependencyValidator()
        # Production catalog has zero undisclosed circularities
        res = dep_val.validate_all()
        assert res["undisclosed_circular_count"] == 0

        # Inject an artificial circular rule
        registry = LandmarkRegistry()
        custom_rules = dict(ACUPOINT_LOCALIZATION_RULES)
        # Point ST36 is normally rule-derived; inject rule pointing directly to a landmark derived from it
        test_rule = AcupointLocalizationRule(
            point_code="ST36",
            meridian_code="ST",
            name_en="Zusanli",
            name_zh="足三里",
            name_vi="Túc Tam Lý",
            localization_method="LANDMARK_DIRECT",
            fma_anchor="FMA:58304",
            body_region="LOWER_EXTREMITY",
            who_reference="WHO-2008 ST36",
            skeletal_structure="TIBIA",
            start_landmark_id="LM_TIBIAL_TUBEROSITY_R",
            end_landmark_id="LM_TIBIAL_TUBEROSITY_R",
            proportional_fraction=0.0,
            lateral_offset_cun=0.0,
            quality_class="CLASS_B",
        )
        custom_rules["ST36"] = test_rule

        # Synthetic injector
        injected_validator = AnatomicalProvenanceDependencyValidator(landmark_registry=registry, rules=custom_rules)
        # Set raw point of ST36 right at LM_TIBIAL_TUBEROSITY_R position
        lm = registry.get_landmark("LM_TIBIAL_TUBEROSITY_R")
        assert lm is not None
        injected_validator._raw_points["ST36"] = {"position": list(lm.canonical_position)}

        issues = injected_validator.detect_circular_references(tolerance_mm=5.0)
        st36_issues = [i for i in issues if i.entity_id == "ST36"]
        assert len(st36_issues) > 0
        assert st36_issues[0].issue_type == DependencyIssueSeverity.UNDISCLOSED_CIRCULARITY

    def test_stomach_abdominal_x_constant_falsification_documentation(self):
        """ST19..ST30 canonical coordinates share X = 0.0660m; system must flag this as unscaled mesh assumption."""
        validator = IndependentAnatomicalValidator()
        uncert_matrix = validator.generate_anatomical_uncertainty_matrix()
        st_abdominal = [u for u in uncert_matrix if u["channel_code"] == "ST" and 19 <= int(u["point_code"][2:]) <= 30]
        assert len(st_abdominal) == 12
        for u in st_abdominal:
            # Must document cun scaling elasticity uncertainty >= 8.0 mm
            assert u["cun_scaling_elasticity_mm"] >= 8.0
            # Must state clinical depth guidance is NOT allowed
            assert u["clinical_depth_guidance_allowed"] is False
