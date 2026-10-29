"""MSK-Therapy-OS - Milestone P9.13 Anatomical Validation Test Suite.

Audits the independent anatomical validation infrastructure:
- External ground-truth dataset and clinical reviewer credential registration.
- Empirical ground-truth observation ingestion.
- Coordinate comparison, residual error distance, and error classification.
- Fail-closed governance (zero false clinical promotions when ground-truth is absent).
- 362-point provenance matrix generation (18 Class A, 344 Class B, 0 Class C/D).
- Anatomical uncertainty matrix generation and clinical depth prohibition.
- REST API validation endpoints and meridian coverage schema extensions.
"""

import json
import sqlite3
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
from msk_therapy_os.points import init_points_tables, get_meridian_atlas_coverage_dashboard


@pytest.fixture
def memory_db():
    conn = sqlite3.connect(":memory:")
    init_points_tables(conn)
    yield conn
    conn.close()


class TestIndependentAnatomicalValidation:
    """Verifies the core IndependentAnatomicalValidator engine and governance rules."""

    def test_default_reviewers_and_sources_registered(self):
        """Validator starts with vetted review authorities and BodyParts3D baseline."""
        validator = IndependentAnatomicalValidator()
        assert "REV-LEAD-ANATOMIST" in validator._reviewers
        assert "REV-CLINICAL-AUDITOR" in validator._reviewers
        assert "DS-BP3D-FJ2810" in validator._datasets

        bp3d = validator.get_dataset("DS-BP3D-FJ2810")
        assert bp3d is not None
        assert bp3d.modality == GroundTruthModality.BODYPARTS3D_DIGITAL_REFERENCE
        assert bp3d.is_synthetic_fixture is False

    def test_register_external_clinical_dataset_and_reviewer(self):
        """Clinical research centers can register empirical radiological datasets."""
        validator = IndependentAnatomicalValidator()
        rev = ClinicalReviewerCredentials(
            reviewer_id="REV-CT-SPECIALIST",
            name="Musculoskeletal Radiologist",
            role="LEAD_RADIOLOGIST",
            affiliation="Academic Medical Imaging Department",
            qualification="MD, Board Certified Radiologist",
            license_id="RAD-2026-4412",
        )
        validator.register_reviewer(rev)
        assert validator._reviewers["REV-CT-SPECIALIST"].role == "LEAD_RADIOLOGIST"

        ds = ExternalGroundTruthDataset(
            dataset_id="DS-CT-UPPER-LIMB-2026",
            name="High-Resolution 3D CT Upper Limb Surface Landmark Study",
            source_organization="MSK Clinical Imaging Consortium",
            version="1.0-CT",
            license="CC BY-NC 4.0",
            doi_or_url="doi:10.1016/j.clinimag.2026.01.004",
            modality=GroundTruthModality.CT_3D_SURFACE,
            is_synthetic_fixture=False,
            sample_size=45,
        )
        validator.register_dataset(ds)
        assert validator.get_dataset("DS-CT-UPPER-LIMB-2026") is not None

    def test_import_observations_and_retrieve(self):
        """Ground-truth observations can be imported and retrieved by point code."""
        validator = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-CT-UPPER-LIMB-2026",
            name="Upper Limb CT",
            source_organization="Consortium",
            version="1.0",
            license="CC-BY",
            doi_or_url="https://doi.org/10.1016/j.clinimag.2026.01.004",
            modality=GroundTruthModality.CT_3D_SURFACE,
            sample_size=10,
        )
        validator.register_dataset(ds)

        obs = GroundTruthObservation(
            point_code="LU7",
            dataset_id="DS-CT-UPPER-LIMB-2026",
            canonical_position=(-0.185, 0.785, 0.052),
            uncertainty_radius_mm=1.5,
            reviewer_id="REV-CT-SPECIALIST",
            notes="Identified at styloid process of radius groove via 0.5mm slice CT",
        )
        count = validator.import_observations([obs])
        assert count == 1

        retrieved = validator.get_observation("LU7", dataset_id="DS-CT-UPPER-LIMB-2026")
        assert retrieved is not None
        assert retrieved.point_code == "LU7"
        assert retrieved.canonical_position == (-0.185, 0.785, 0.052)

    def test_residual_calculation_and_error_classification(self):
        """Distance between predicted and observed coordinates maps to error classes."""
        validator = IndependentAnatomicalValidator()
        pred = validator.resolve_point_coordinate("LI4")
        p_canon = pred["position"]

        def make_ds(ds_id):
            return ExternalGroundTruthDataset(
                dataset_id=ds_id,
                name=ds_id,
                source_organization="Test Rig",
                version="1.0",
                license="MIT",
                doi_or_url="urn:test:" + ds_id,
                modality=GroundTruthModality.EXPERT_CONSENSUS_PALPATION,
                sample_size=1,
            )

        # 1. Congruent observation: 1.5 mm distance
        validator.register_dataset(make_ds("DS-TEST-CONGRUENT"))
        obs_congruent = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-TEST-CONGRUENT",
            canonical_position=(p_canon[0] + 0.001, p_canon[1] + 0.001, p_canon[2] + 0.0005),
        )
        validator.import_observations([obs_congruent])
        res1 = validator.validate_point("LI4", dataset_id="DS-TEST-CONGRUENT")
        assert res1.classification == AnatomicalErrorClassification.CONGRUENT
        assert res1.is_congruent is True

        # 2. Acceptable tolerance observation: 5.0 mm distance
        validator.register_dataset(make_ds("DS-TEST-ACCEPTABLE"))
        obs_acceptable = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-TEST-ACCEPTABLE",
            canonical_position=(p_canon[0] + 0.003, p_canon[1] + 0.004, p_canon[2]),
        )
        validator.import_observations([obs_acceptable])
        res2 = validator.validate_point("LI4", dataset_id="DS-TEST-ACCEPTABLE")
        assert res2.classification == AnatomicalErrorClassification.ACCEPTABLE_CLINICAL_TOLERANCE

        # 3. Borderline observation: 10.0 mm distance
        validator.register_dataset(make_ds("DS-TEST-BORDERLINE"))
        obs_borderline = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-TEST-BORDERLINE",
            canonical_position=(p_canon[0] + 0.008, p_canon[1] + 0.006, p_canon[2]),
        )
        validator.import_observations([obs_borderline])
        res3 = validator.validate_point("LI4", dataset_id="DS-TEST-BORDERLINE")
        assert res3.classification == AnatomicalErrorClassification.BORDERLINE

        # 4. Outlier anomaly observation: 25.0 mm distance
        validator.register_dataset(make_ds("DS-TEST-OUTLIER"))
        obs_outlier = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-TEST-OUTLIER",
            canonical_position=(p_canon[0] + 0.020, p_canon[1] + 0.015, p_canon[2]),
        )
        validator.import_observations([obs_outlier])
        res4 = validator.validate_point("LI4", dataset_id="DS-TEST-OUTLIER")
        assert res4.classification == AnatomicalErrorClassification.OUTLIER_ANOMALY
        assert res4.is_congruent is False

    def test_fail_closed_when_independent_ground_truth_unavailable(self):
        """When no external observation exists, validation explicitly returns UNAVAILABLE."""
        validator = IndependentAnatomicalValidator()
        res = validator.validate_point("BL23")
        assert res.classification == AnatomicalErrorClassification.INDEPENDENT_GROUND_TRUTH_UNAVAILABLE
        assert res.residual_error_mm is None
        assert res.is_congruent is False
        assert res.verification_tier == AnatomicalVerificationTier.TECHNICALLY_CALIBRATED
        assert "No independent external ground truth observation" in res.details.get("reason", "")

    def test_catalog_validation_summary_reflects_fail_closed_governance(self):
        """Full catalog validation without external datasets must report 362 unverified."""
        validator = IndependentAnatomicalValidator()
        rep = validator.validate_catalog()
        summary = rep.summary
        assert summary["total_points_in_scope"] == 362
        assert summary["evaluated_with_ground_truth"] == 0
        assert summary["ground_truth_unavailable_count"] == 362
        assert summary["congruent_count"] == 0
        assert summary["congruence_percentage"] == 0.0
        assert len(rep.comparisons) == 362

    def test_362_point_provenance_matrix_completeness(self):
        """362-point provenance matrix must cover exact 18 Class A and 344 Class B points."""
        validator = IndependentAnatomicalValidator()
        matrix = validator.generate_full_362_provenance_matrix()
        assert len(matrix) == 362

        class_a_rows = [r for r in matrix if r["quality_class"] == "CLASS_A"]
        class_b_rows = [r for r in matrix if r["quality_class"] == "CLASS_B"]
        class_c_rows = [r for r in matrix if r["quality_class"] == "CLASS_C"]
        class_d_rows = [r for r in matrix if r["quality_class"] == "CLASS_D"]

        assert len(class_a_rows) == 18
        assert len(class_b_rows) == 344
        assert len(class_c_rows) == 0
        assert len(class_d_rows) == 0

        # Tier 4 clinical verification claim must be strictly False across all 362 rows
        for r in matrix:
            assert ("UNVERIFIED" in str(r["clinical_verification_tier_4"]) or r["clinical_verification_tier_4"] is False)
            assert r["pos_x"] is not None and r["pos_y"] is not None and r["pos_z"] is not None
            assert r["fma_anchor"] is not None and len(r["fma_anchor"]) > 0
            assert r["who_reference"] is not None and len(r["who_reference"]) > 0

    def test_anatomical_uncertainty_matrix_prohibits_clinical_depth(self):
        """Uncertainty matrix must prohibit surgical/clinical depth guidance on all points."""
        validator = IndependentAnatomicalValidator()
        matrix = validator.generate_anatomical_uncertainty_matrix()
        assert len(matrix) == 362

        for row in matrix:
            assert row["clinical_depth_guidance_allowed"] is False
            assert row["total_spatial_uncertainty_radius_mm"] > 0.0
            assert row["confidence_interval_95_pct_mm"] > 0.0

    def test_meridian_coverage_dashboard_exposes_catalog_split(self, memory_db):
        """Dashboard exposes standard_catalog_count: 361 and extended_catalog_count: 1."""
        dash = get_meridian_atlas_coverage_dashboard(memory_db)
        assert dash["total_points"] == 362
        assert dash["standard_catalog_count"] == 361
        assert dash["extended_catalog_count"] == 1
        assert dash["extended_points"] == ["GV24+"]

        gov = dash["governance_semantic_metadata"]
        assert gov["standard_catalog_count"] == 361
        assert gov["extended_catalog_count"] == 1
        assert gov["independent_ground_truth_status"] == "INDEPENDENT_GROUND_TRUTH_UNAVAILABLE"
        assert gov["anatomical_falsification_status"] == "FALSIFICATION_FRAMEWORK_ACTIVE"

        qa = dash["quality_assurance"]
        assert qa["audit_status"] == "P9.13_PRODUCTION_HARDENED"
        assert qa["previous_audit_status"] == "P9.12_TRANCHE_3_FINAL"
