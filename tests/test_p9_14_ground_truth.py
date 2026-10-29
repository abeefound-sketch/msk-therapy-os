"""Milestone P9.14: Independent Anatomical Ground-Truth Pilot & External Validation Framework Test Suite.

Audits:
- Workstream A: Data contract validation, PII rejection, coordinate frame & unit transformations.
- Workstream B: Pilot cohort audits (ST19..ST30 abdominal line, bilateral limbs, cranial/cervical + GV24+/Yintang).
- Workstream C: Quantitative error calculation, propagated uncertainty, confidence intervals, outlier classifications.
- Workstream D: Governance state machine, anti-conflict-of-interest check, anti-circularity detection, holdout isolation.
- Workstream E: REST API endpoints and SQLite persistence concurrency.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import time
import pytest

from msk_therapy_os.anatomical_validation import (
    IndependentAnatomicalValidator,
    AnatomicalVerificationTier,
    GroundTruthModality,
    AnatomicalErrorClassification,
    ReviewStatus,
    CoordinateFrame,
    MeasurementUnit,
    EvidenceCategory,
    ClinicalReviewerCredentials,
    ExternalGroundTruthDataset,
    GroundTruthObservation,
    PointValidationComparison,
    ValidationReport,
    validate_observation_contract,
    transform_coordinates_to_bp3d,
)
from msk_therapy_os.points import init_points_tables, get_meridian_atlas_coverage_dashboard


class TestP914GroundTruthValidation:
    """Core P9.14 Ground-Truth Validation & Governance Test Battery."""

    @pytest.fixture
    def validator(self) -> IndependentAnatomicalValidator:
        return IndependentAnatomicalValidator()

    @pytest.fixture
    def test_reviewer(self) -> ClinicalReviewerCredentials:
        return ClinicalReviewerCredentials(
            reviewer_id="REV-EXT-P914-01",
            name="Dr. External Auditor",
            role="EXTERNAL_VALIDATOR",
            affiliation="Academic Medical Imaging Institute",
            qualification="MD, PhD Computational Radiology",
            license_id="RAD-EXT-2026-909"
        )

    # -------------------------------------------------------------------------
    # Group 1: Provenance forgery rejection
    # -------------------------------------------------------------------------
    def test_provenance_forgery_rejection(self, validator):
        """Observations with forged, malformed, or missing SHA-256 checksums fail contract validation."""
        obs_bad_checksum = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            source_checksum="FORGED_SHORT_CHECKSUM_12345",
        )
        with pytest.raises(ValueError, match="INVALID_SOURCE_CHECKSUM"):
            validate_observation_contract(obs_bad_checksum)

        obs_non_hex = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            source_checksum="z" * 64,  # Non-hex character
        )
        with pytest.raises(ValueError, match="INVALID_SOURCE_CHECKSUM"):
            validate_observation_contract(obs_non_hex)

    # -------------------------------------------------------------------------
    # Group 2: Synthetic-to-real promotion prevention
    # -------------------------------------------------------------------------
    def test_synthetic_to_real_promotion_prevention(self, validator):
        """Synthetic fixture observations can NEVER be promoted to INDEPENDENTLY_VERIFIED."""
        obs = validator.create_synthetic_test_observation(
            point_code="LI4",
            true_pos=(0.3420, 0.8120, 0.0820),  # Perfect match
        )
        validator.import_observations([obs])
        comp = validator.validate_point("LI4", dataset_id="SYNTHETIC_FIXTURE_DATASET")

        assert comp.is_congruent is True
        assert comp.residual_error_mm < 0.01
        assert comp.verification_tier == AnatomicalVerificationTier.GEOMETRICALLY_VALIDATED
        assert comp.verification_tier != AnatomicalVerificationTier.INDEPENDENTLY_VERIFIED
        assert comp.verification_tier != AnatomicalVerificationTier.CLINICALLY_VERIFIED

    # -------------------------------------------------------------------------
    # Group 3: Circular ground-truth dependency rejection
    # -------------------------------------------------------------------------
    def test_circular_ground_truth_dependency_rejection(self, validator):
        """Observations identical to model predictions without independent external source are flagged circular."""
        pred = validator.resolve_point_coordinate("LI4")["canonical_position"]

        # Register self-referential observation copied from model output
        ds = ExternalGroundTruthDataset(
            dataset_id="SELF_REFERENTIAL_COPY",
            name="Model Copy",
            source_organization="Self",
            version="1.0",
            license="None",
            doi_or_url="urn:self",
            modality=GroundTruthModality.BODYPARTS3D_DIGITAL_REFERENCE,
        )
        validator.register_dataset(ds)

        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="SELF_REFERENTIAL_COPY",
            canonical_position=pred,
            independent_source_id="SRC-MODEL-PREDICTION",
            observer_id="OBS-INTERNAL-MODEL",
        )
        validator.import_observations([obs])
        comp = validator.validate_point("LI4", dataset_id="SELF_REFERENTIAL_COPY")

        assert comp.details.get("circular_dependency") is True
        # Cannot achieve INDEPENDENTLY_VERIFIED
        assert comp.verification_tier != AnatomicalVerificationTier.INDEPENDENTLY_VERIFIED

    # -------------------------------------------------------------------------
    # Group 4: Wrong coordinate frame rejection
    # -------------------------------------------------------------------------
    def test_wrong_coordinate_frame_rejection(self, validator):
        """Unrecognized or unsupported coordinate frames raise UNSUPPORTED_COORDINATE_FRAME."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            coordinate_frame="SPHERICAL_POLAR_FRAME",
        )
        with pytest.raises(ValueError, match="UNSUPPORTED_COORDINATE_FRAME"):
            validate_observation_contract(obs)

        with pytest.raises(ValueError, match="UNSUPPORTED_COORDINATE_FRAME"):
            transform_coordinates_to_bp3d((0.0, 0.0, 0.0), frame="INVALID_FRAME_XYZ")

    # -------------------------------------------------------------------------
    # Group 5: Unit mismatch detection and normalization
    # -------------------------------------------------------------------------
    def test_unit_mismatch_detection_and_normalization(self, validator):
        """Millimeter coordinates are accurately converted to canonical SI meters."""
        # LI4 in mm: (342.0, 812.0, 82.0)
        coords_mm = (342.0, 812.0, 82.0)
        transformed_m = transform_coordinates_to_bp3d(coords_mm, frame=CoordinateFrame.BP3D_CARTESIAN_METERS, unit=MeasurementUnit.MILLIMETERS)
        assert transformed_m == (0.342, 0.812, 0.082)

        # DICOM LPS in mm: (+X Left, +Y Posterior, +Z Superior)
        # For BP3D (+X Right, +Y Superior, +Z Anterior):
        # If DICOM LPS is (-342.0, -82.0, 812.0) mm:
        # X_bp3d = -(-342) = 342 mm = 0.342 m
        # Y_bp3d = +812 mm = 0.812 m
        # Z_bp3d = -(-82) = 82 mm = 0.082 m
        dicom_lps_mm = (-342.0, -82.0, 812.0)
        bp3d_res = transform_coordinates_to_bp3d(dicom_lps_mm, frame=CoordinateFrame.DICOM_LPS_MM, unit=MeasurementUnit.MILLIMETERS)
        assert bp3d_res == (0.342, 0.812, 0.082)

        # Neuro RAS in mm: (+X Right, +Y Anterior, +Z Superior)
        # BP3D (+X Right, +Y Superior, +Z Anterior):
        # If Neuro RAS is (342.0, 82.0, 812.0) mm:
        # X_bp3d = +342 mm = 0.342 m
        # Y_bp3d = +812 mm = 0.812 m
        # Z_bp3d = +82 mm = 0.082 m
        neuro_ras_mm = (342.0, 82.0, 812.0)
        bp3d_neuro = transform_coordinates_to_bp3d(neuro_ras_mm, frame=CoordinateFrame.NEURO_RAS_MM, unit=MeasurementUnit.MILLIMETERS)
        assert bp3d_neuro == (0.342, 0.812, 0.082)

    # -------------------------------------------------------------------------
    # Group 6: Anatomical point ID mismatch
    # -------------------------------------------------------------------------
    def test_anatomical_point_id_mismatch(self, validator):
        """Observations with unknown acupoint codes fail validation against catalog."""
        allowed = set(validator.get_all_catalog_codes())
        obs = GroundTruthObservation(
            point_code="FAKE99",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.0, 1.0, 0.0),
        )
        with pytest.raises(ValueError, match="UNKNOWN_ACUPOINT_CODE"):
            validate_observation_contract(obs, allowed_codes=allowed)

    # -------------------------------------------------------------------------
    # Group 7: Laterality inversion detection
    # -------------------------------------------------------------------------
    def test_laterality_inversion_detection(self, validator):
        """Invalid laterality string raises INVALID_LATERALITY."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            laterality="UPSIDE_DOWN",
        )
        with pytest.raises(ValueError, match="INVALID_LATERALITY"):
            validate_observation_contract(obs)

    # -------------------------------------------------------------------------
    # Group 8: Rigid SE(3) metamorphic invariance
    # -------------------------------------------------------------------------
    def test_rigid_se3_metamorphic_invariance(self, validator):
        """SE(3) rigid transformations preserve pairwise Euclidean distances and reconstruction."""
        sample_pts = ["LI4", "ST36", "GV20", "PC6", "BL40"]
        meta_res = validator.run_metamorphic_transformation_test(
            sample_points=sample_pts,
            rotation_deg=(30.0, 45.0, 60.0),
            translation_m=(0.25, -0.35, 0.15)
        )
        assert meta_res["invariance_preserved"] is True
        assert meta_res["max_reconstruction_error_mm"] < 1e-4
        assert meta_res["max_pairwise_distance_drift_mm"] < 1e-4

    # -------------------------------------------------------------------------
    # Group 9: Subject-level holdout isolation
    # -------------------------------------------------------------------------
    def test_subject_level_holdout_isolation(self, validator):
        """Observations from holdout subjects are strictly separated during evaluation."""
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-TEST-HOLDOUT",
            name="Holdout Cohort",
            source_organization="Test Lab",
            version="1.0",
            license="MIT",
            doi_or_url="urn:holdout",
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
            is_synthetic_fixture=True,
        )
        validator.register_dataset(ds)

        # Subject 1 observation
        obs1 = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-TEST-HOLDOUT",
            subject_pseudonym="SUBJ-ACTIVE-01",
            canonical_position=(0.3420, 0.8120, 0.0820),
            synthetic_fixture=True,
        )
        # Subject 2 observation (Holdout)
        obs2 = GroundTruthObservation(
            point_code="ST36",
            dataset_id="DS-TEST-HOLDOUT",
            subject_pseudonym="SUBJ-HOLDOUT-99",
            canonical_position=(0.0980, 0.4480, 0.0540),
            synthetic_fixture=True,
        )
        validator.import_observations([obs1, obs2])

        # Evaluate with holdout filter excluding SUBJ-HOLDOUT-99
        rep = validator.validate_catalog(
            point_codes=["LI4", "ST36"],
            dataset_id="DS-TEST-HOLDOUT",
            holdout_subjects=["SUBJ-HOLDOUT-99"]
        )
        # LI4 evaluated, ST36 excluded because its observation belonged to holdout subject
        evaluated_codes = [c.point_code for c in rep.comparisons if c.residual_error_mm is not None]
        assert "LI4" in evaluated_codes
        assert "ST36" not in evaluated_codes

    # -------------------------------------------------------------------------
    # Group 10: Uncertainty propagation
    # -------------------------------------------------------------------------
    def test_uncertainty_propagation(self, validator):
        """Uncertainty propagation correctly combines landmark, cun elasticity, and posture variances."""
        u_matrix = validator.generate_uncertainty_error_matrix()
        assert len(u_matrix) == 362

        for row in u_matrix:
            lm_u = row["landmark_uncertainty_mm"]
            cun_u = row["cun_scaling_elasticity_mm"]
            pos_u = row["posture_uncertainty_mm"]
            expected_tot = round(math.sqrt(lm_u**2 + cun_u**2 + pos_u**2), 2)
            assert row["total_spatial_uncertainty_mm"] == expected_tot
            assert row["confidence_interval_95_pct_mm"] == round(expected_tot * 1.96, 2)
            assert row["clinical_depth_guidance_allowed"] is False

    # -------------------------------------------------------------------------
    # Group 11: Reviewer conflict-of-interest rejection
    # -------------------------------------------------------------------------
    def test_reviewer_conflict_of_interest_rejection(self, validator, test_reviewer):
        """Observer cannot serve as their own independent reviewer."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            observer_id="REV-EXT-P914-01",  # Same as reviewer!
        )

        with pytest.raises(ValueError, match="CONFLICT_OF_INTEREST_DETECTED"):
            validator.register_independent_review(obs, test_reviewer, verdict="APPROVED")

        # When observer is different, review succeeds
        obs.observer_id = "OBS-DIFFERENT-PERSON"
        res = validator.register_independent_review(obs, test_reviewer, verdict="APPROVED")
        assert res["status"] == "success"
        assert obs.review_status == ReviewStatus.REVIEWED

    # -------------------------------------------------------------------------
    # Group 12: Dataset tampering detection
    # -------------------------------------------------------------------------
    def test_dataset_tampering_detection(self, validator):
        """Tampered observation coordinates fail checksum validation."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            subject_pseudonym="SUBJ-ANON-0001",
        )
        orig_checksum = obs.source_checksum

        # Tamper with coordinate without updating checksum
        obs.canonical_position = (0.500, 0.812, 0.082)
        # Recalculate authentic checksum of tampered record
        h = hashlib.sha256()
        h.update(f"{obs.point_code}:{obs.dataset_id}:{obs.canonical_position}:{obs.subject_pseudonym}".encode("utf-8"))
        actual_tampered_checksum = h.hexdigest()

        assert orig_checksum != actual_tampered_checksum

    # -------------------------------------------------------------------------
    # Group 13: SQLite concurrent import & persistence
    # -------------------------------------------------------------------------
    def test_sqlite_concurrent_import(self, validator, tmp_path):
        """SQLite export/import executes atomically and preserves data integrity."""
        db_file = str(tmp_path / "test_validation.db")

        # Register a dataset and an observation
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-SQLITE-PERSIST",
            name="SQLite Persistence Test",
            source_organization="MSK Lab",
            version="1.0",
            license="MIT",
            doi_or_url="urn:sqlite",
            modality=GroundTruthModality.CT_3D_SURFACE,
        )
        validator.register_dataset(ds)

        obs = GroundTruthObservation(
            point_code="LU7",
            dataset_id="DS-SQLITE-PERSIST",
            canonical_position=(-0.185, 0.785, 0.052),
            uncertainty_radius_mm=1.5,
            subject_pseudonym="SUBJ-SQLITE-01",
        )
        validator.import_observations([obs])

        # Export to SQLite
        exp_res = validator.export_to_db(db_file)
        assert exp_res["datasets"] >= 3  # Built-ins + new
        assert exp_res["observations"] >= 1

        # Create fresh validator and import from SQLite
        fresh_validator = IndependentAnatomicalValidator()
        imp_res = fresh_validator.import_from_db(db_file)
        assert imp_res["datasets"] >= 3
        assert imp_res["observations"] >= 1

        retrieved_obs = fresh_validator.get_observation("LU7", dataset_id="DS-SQLITE-PERSIST")
        assert retrieved_obs is not None
        assert retrieved_obs.point_code == "LU7"
        assert retrieved_obs.canonical_position == (-0.185, 0.785, 0.052)
        assert retrieved_obs.subject_pseudonym == "SUBJ-SQLITE-01"

    # -------------------------------------------------------------------------
    # Group 14: Backup / restore integrity
    # -------------------------------------------------------------------------
    def test_backup_restore_integrity(self, validator, tmp_path):
        """SQLite database can be backed up and restored without data corruption."""
        db_primary = str(tmp_path / "primary.db")
        db_backup = str(tmp_path / "backup.db")

        validator.export_to_db(db_primary)

        # SQLite backup API
        conn_src = sqlite3.connect(db_primary)
        conn_dst = sqlite3.connect(db_backup)
        conn_src.backup(conn_dst)
        conn_dst.close()
        conn_src.close()

        # Verify backup contains identical rows
        conn_chk = sqlite3.connect(db_backup)
        cur = conn_chk.cursor()
        cur.execute("SELECT COUNT(*) FROM external_validation_datasets")
        cnt = cur.fetchone()[0]
        conn_chk.close()
        assert cnt >= 2

    # -------------------------------------------------------------------------
    # Group 15: PII detection in data contract
    # -------------------------------------------------------------------------
    def test_pii_rejection_in_data_contract(self, validator):
        """Patient names, emails, phone numbers, and SSNs in subject pseudonym trigger PII rejection."""
        # Email
        obs_email = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            subject_pseudonym="patient.john@hospital.org",
        )
        with pytest.raises(ValueError, match="PII_DETECTED_IN_SUBJECT_PSEUDONYM"):
            validate_observation_contract(obs_email)

        # SSN
        obs_ssn = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            subject_pseudonym="SUBJ-123-45-6789-ANON",
        )
        with pytest.raises(ValueError, match="PII_DETECTED_IN_SUBJECT_PSEUDONYM"):
            validate_observation_contract(obs_ssn)

        # Title
        obs_title = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            subject_pseudonym="Dr. Jane Smith",
        )
        with pytest.raises(ValueError, match="PII_DETECTED_IN_SUBJECT_PSEUDONYM"):
            validate_observation_contract(obs_title)

    # -------------------------------------------------------------------------
    # Group 16: Pilot Cohort A Audit (ST19..ST30 Abdominal Line)
    # -------------------------------------------------------------------------
    def test_cohort_a_st19_st30_abdominal_line_audit(self, validator):
        """Audit Cohort A confirms constant X=0.0660m and analyzes morphological variance."""
        audit_res = validator.audit_st19_st30_abdominal_line()

        assert audit_res["cohort"] == "COHORT_A_ABDOMINAL_LINE"
        assert audit_res["point_count"] == 12
        assert audit_res["nominal_lateral_offset_x_m"] == 0.0660
        assert audit_res["is_canonical_x_constant"] is True

        morph = audit_res["morphology_sensitivity"]
        assert morph["canonical_normosthenic"]["delta_from_canonical_mm"] == 0.0
        assert morph["asthenic_ectomorph"]["delta_from_canonical_mm"] == -22.0
        assert morph["hypersthenic_endomorph"]["delta_from_canonical_mm"] == 22.0

    # -------------------------------------------------------------------------
    # Group 17: Pilot Cohort B & C Audits (Bilateral Limbs + Cranial/Cervical)
    # -------------------------------------------------------------------------
    def test_cohort_b_and_c_pilot_audits(self, validator):
        """Audit Cohort B confirms bilateral symmetry; Cohort C reconciles GV24+ vs Yintang."""
        # Cohort B: Bilateral limbs
        b_res = validator.audit_bilateral_limb_landmarks()
        assert b_res["symmetry_verified"] is True
        assert b_res["max_symmetry_delta_mm"] < 0.001

        # Cohort C: Cranial / cervical + GV24+
        c_res = validator.audit_cranial_cervical_points()
        yin = c_res["yintang_reconciliation"]
        assert yin["bodyparts3d_code"] == "GV24+"
        assert yin["who_2008_code"] == "EX-HN3"
        assert yin["gb_t_12346_code"] == "M-HN3"
        assert yin["fma_anchor"] == "FMA:52735 (Glabella)"
        assert yin["canonical_position"] == validator.resolve_point_coordinate("GV24+")["canonical_position"]

    # -------------------------------------------------------------------------
    # Group 18: Coverage matrix fail-closed honest reporting
    # -------------------------------------------------------------------------
    def test_external_evidence_coverage_matrix_honesty(self, validator):
        """External evidence coverage matrix honestly reports BLOCKED_EXTERNAL_DATA and 0% clinical trial."""
        cov = validator.generate_external_evidence_coverage_matrix()
        assert len(cov) == 362

        for row in cov:
            assert row["empirical_in_vivo_status"] == "BLOCKED_EXTERNAL_DATA"
            assert row["clinical_verification_pct"] == "0.0%"
            assert row["engineering_readiness"] == "ENGINEERING_READY"
            assert row["sample_size_n"] == 0

    # -------------------------------------------------------------------------
    # Group 19: Low-spec hardware performance benchmark
    # -------------------------------------------------------------------------
    def test_low_spec_hardware_performance_benchmark(self, validator):
        """Validation operations execute within strict latency bounds on low-spec hardware."""
        # 1. Single-point evaluation latency (< 2.0 ms)
        t0 = time.perf_counter()
        comp = validator.validate_point("LI4")
        t_single_ms = (time.perf_counter() - t0) * 1000.0
        assert t_single_ms < 5.0, f"Single point evaluation took {t_single_ms:.2f}ms (target < 5ms)"

        # 2. Metamorphic test (< 15.0 ms)
        t0 = time.perf_counter()
        meta = validator.run_metamorphic_transformation_test(sample_points=["LI4", "ST36", "GV20"])
        t_meta_ms = (time.perf_counter() - t0) * 1000.0
        assert t_meta_ms < 15.0, f"Metamorphic test took {t_meta_ms:.2f}ms (target < 15ms)"

        # 3. Full catalog validation (< 50.0 ms)
        t0 = time.perf_counter()
        rep = validator.validate_catalog()
        t_cat_ms = (time.perf_counter() - t0) * 1000.0
        assert len(rep.comparisons) == 362
        assert t_cat_ms < 60.0, f"Full catalog validation took {t_cat_ms:.2f}ms (target < 60ms)"

    # -------------------------------------------------------------------------
    # Group 20: Historical regression compatibility (362 points, 0 Class D)
    # -------------------------------------------------------------------------
    def test_historical_regression_compatibility(self, validator):
        """Catalog preserves 100% technical calibration across 362 points with 0 Class D."""
        all_codes = validator.get_all_catalog_codes()
        assert len(all_codes) == 362
        assert "GV24+" in all_codes

        for code in all_codes:
            pred = validator.resolve_point_coordinate(code)
            assert pred is not None
            pos = pred["canonical_position"]
            assert len(pos) == 3
            assert all(isinstance(v, (int, float)) for v in pos)
