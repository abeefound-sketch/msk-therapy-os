"""Milestone P10.0: External Anatomical Ground-Truth Integration & Independent Validation Test Suite.

Audits:
- Phase A: Independent evidence readiness and contract gap remediation.
- Phase B: External evidence ingestion pipeline, privacy hard-stops, authorization gate, quarantine store.
- Phase C: Subject-level holdout isolation, anti-leakage, blind dual independent review, pre-registered accuracy thresholds.
- Phase D: Three-cohort external pilot framework (A: abdominal, B: bilateral limbs, C: cranial/cervical).
- Phase E: Governance dashboard, quarantine APIs, holdout partition APIs.
- Phase F: Security, adversarial edge cases, SQLite persistence, and fail-closed clinical safety boundaries.
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
    QuarantineReason,
    DeidentificationMethod,
    EvidenceIngestionState,
    ClinicalReviewerCredentials,
    ExternalGroundTruthDataset,
    GroundTruthObservation,
    QuarantinedObservation,
    HoldoutPartitionManifest,
    HoldoutPartitionManager,
    BlindIndependentReviewRecord,
    PreRegisteredAccuracyThresholds,
    validate_observation_contract,
    transform_coordinates_to_bp3d,
)


class TestP100ExternalValidationPipeline:
    """Core test battery for Milestone P10.0."""

    @pytest.fixture
    def validator(self) -> IndependentAnatomicalValidator:
        return IndependentAnatomicalValidator()

    @pytest.fixture
    def authorized_external_dataset(self, validator) -> ExternalGroundTruthDataset:
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-AUTHORIZED-MRI-2026",
            name="Multi-Center Volunteer MRI Acupoint Study",
            source_organization="Consortium for Integrative Computational Anatomy",
            version="1.0-MRI",
            license="CC BY 4.0",
            doi_or_url="https://doi.org/10.1016/j.clinimag.2026.1001",
            modality=GroundTruthModality.MRI_T1_ANATOMICAL,
            is_synthetic_fixture=False,
            sample_size=25,
        )
        validator.register_dataset(ds)
        return ds

    # -------------------------------------------------------------------------
    # 1. Privacy Hard-Stop & Authorization Gate
    # -------------------------------------------------------------------------
    def test_unauthorized_external_dataset_rejected_at_privacy_gate(self, validator, authorized_external_dataset):
        """Real empirical observation lacking formal Data Sharing Agreement (DUA) is rejected."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-AUTHORIZED-MRI-2026",
            canonical_position=(0.342, 0.812, 0.082),
            subject_pseudonym="SUBJ-AUTH-001",
            synthetic_fixture=False,  # Real human data
            data_sharing_agreement_ref="",  # Missing DUA
            ethics_approval_or_exemption_ref="IRB-STUDY-9981",
            deidentification_method=DeidentificationMethod.SAFE_HARBOR_18_ELEMENTS,
            is_authorized_for_clinical_eval=True,
        )
        with pytest.raises(ValueError, match="UNAUTHORIZED_EXTERNAL_DATA"):
            validate_observation_contract(obs, check_authorization=True)

    def test_missing_ethics_approval_rejected(self, validator, authorized_external_dataset):
        """Real empirical observation lacking IRB / Ethics approval is rejected."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-AUTHORIZED-MRI-2026",
            canonical_position=(0.342, 0.812, 0.082),
            subject_pseudonym="SUBJ-AUTH-001",
            synthetic_fixture=False,
            data_sharing_agreement_ref="DUA-INSTITUTIONAL-2026-04",
            ethics_approval_or_exemption_ref="",  # Missing IRB
            deidentification_method=DeidentificationMethod.SAFE_HARBOR_18_ELEMENTS,
            is_authorized_for_clinical_eval=True,
        )
        with pytest.raises(ValueError, match="UNAUTHORIZED_EXTERNAL_DATA"):
            validate_observation_contract(obs, check_authorization=True)

    def test_incomplete_deidentification_rejected(self, validator, authorized_external_dataset):
        """Real empirical observation marked NOT_DEIDENTIFIED or lacking certification is rejected."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-AUTHORIZED-MRI-2026",
            canonical_position=(0.342, 0.812, 0.082),
            subject_pseudonym="SUBJ-AUTH-001",
            synthetic_fixture=False,
            data_sharing_agreement_ref="DUA-INSTITUTIONAL-2026-04",
            ethics_approval_or_exemption_ref="IRB-STUDY-9981",
            deidentification_method=DeidentificationMethod.NOT_DEIDENTIFIED,
            is_authorized_for_clinical_eval=True,
        )
        with pytest.raises(ValueError, match="INCOMPLETE_DEIDENTIFICATION"):
            validate_observation_contract(obs, check_authorization=True)

    def test_unauthorized_clinical_eval_flag_rejected(self, validator, authorized_external_dataset):
        """Dataset with is_authorized_for_clinical_eval=False is rejected for empirical evaluation."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-AUTHORIZED-MRI-2026",
            canonical_position=(0.342, 0.812, 0.082),
            subject_pseudonym="SUBJ-AUTH-001",
            synthetic_fixture=False,
            data_sharing_agreement_ref="DUA-INSTITUTIONAL-2026-04",
            ethics_approval_or_exemption_ref="IRB-STUDY-9981",
            deidentification_method=DeidentificationMethod.SAFE_HARBOR_18_ELEMENTS,
            is_authorized_for_clinical_eval=False,  # Explicitly unauthorized
        )
        with pytest.raises(ValueError, match="UNAUTHORIZED_EXTERNAL_DATA"):
            validate_observation_contract(obs, check_authorization=True)

    def test_fully_authorized_external_observation_passes_gate(self, validator, authorized_external_dataset):
        """Observation with valid DUA, IRB, Safe Harbor de-identification, and authorization PASSES."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-AUTHORIZED-MRI-2026",
            canonical_position=(0.342, 0.812, 0.082),
            subject_pseudonym="SUBJ-AUTH-001",
            synthetic_fixture=False,
            data_sharing_agreement_ref="DUA-INSTITUTIONAL-2026-04",
            ethics_approval_or_exemption_ref="IRB-STUDY-9981",
            deidentification_method=DeidentificationMethod.SAFE_HARBOR_18_ELEMENTS,
            is_authorized_for_clinical_eval=True,
        )
        res = validate_observation_contract(obs, check_authorization=True)
        assert res["valid"] is True
        assert res["point_code"] == "LI4"

    # -------------------------------------------------------------------------
    # 2. Schema Versioning & PII Enforcement
    # -------------------------------------------------------------------------
    def test_unsupported_schema_version_rejected(self, validator):
        """Observations with unsupported schema versions (e.g., 0.8) are rejected."""
        obs = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-BP3D-FJ2810",
            canonical_position=(0.342, 0.812, 0.082),
            schema_version="0.8-DEPRECATED",
        )
        with pytest.raises(ValueError, match="UNSUPPORTED_SCHEMA_VERSION"):
            validate_observation_contract(obs)

    # -------------------------------------------------------------------------
    # 3. Ingestion Pipeline & Quarantine Store
    # -------------------------------------------------------------------------
    def test_quarantine_pipeline_captures_unauthorized_records(self, validator, authorized_external_dataset):
        """Batch ingestion diverts unauthorized observations into QuarantineStore without crashing."""
        batch = {
            "dataset_id": "DS-AUTHORIZED-MRI-2026",
            "observations": [
                {
                    "point_code": "LI4",
                    "subject_pseudonym": "SUBJ-AUTH-001",
                    "canonical_position": [0.342, 0.812, 0.082],
                    "data_sharing_agreement_ref": "DUA-INSTITUTIONAL-2026-04",
                    "ethics_approval_or_exemption_ref": "IRB-STUDY-9981",
                    "deidentification_method": "SAFE_HARBOR_18_ELEMENTS",
                    "is_authorized_for_clinical_eval": True,
                    "synthetic_fixture": False,
                },
                {
                    # Unauthorized: missing DUA
                    "point_code": "ST36",
                    "subject_pseudonym": "SUBJ-UNAUTH-002",
                    "canonical_position": [0.098, 0.448, 0.054],
                    "data_sharing_agreement_ref": "",
                    "ethics_approval_or_exemption_ref": "IRB-STUDY-9981",
                    "deidentification_method": "SAFE_HARBOR_18_ELEMENTS",
                    "is_authorized_for_clinical_eval": True,
                    "synthetic_fixture": False,
                },
                {
                    # PII suspected: contains phone number
                    "point_code": "GV20",
                    "subject_pseudonym": "SUBJ-555-123-4567",
                    "canonical_position": [0.0, 1.748, -0.012],
                    "data_sharing_agreement_ref": "DUA-INSTITUTIONAL-2026-04",
                    "ethics_approval_or_exemption_ref": "IRB-STUDY-9981",
                    "deidentification_method": "SAFE_HARBOR_18_ELEMENTS",
                    "is_authorized_for_clinical_eval": True,
                    "synthetic_fixture": False,
                }
            ]
        }

        summary = validator.ingest_external_evidence_batch(batch, enforce_quarantine=True)
        assert summary["ingested_count"] == 1
        assert summary["quarantined_count"] == 2

        q_records = validator.get_quarantined_records()
        assert len(q_records) >= 2
        reasons = [q.reason for q in q_records]
        assert QuarantineReason.QUARANTINE_UNAUTHORIZED_DATA in reasons
        assert QuarantineReason.QUARANTINE_PII_SUSPECTED in reasons

    def test_circular_evidence_diverted_to_quarantine(self, validator):
        """Observations identical to model prediction without independent provenance are quarantined."""
        ds = ExternalGroundTruthDataset(
            dataset_id="SELF_ECHO_DATASET",
            name="Model Copy",
            source_organization="Internal",
            version="1.0",
            license="MIT",
            doi_or_url="urn:internal",
            modality=GroundTruthModality.BODYPARTS3D_DIGITAL_REFERENCE,
            is_synthetic_fixture=False,
        )
        validator.register_dataset(ds)

        pred_li4 = validator.resolve_point_coordinate("LI4")["canonical_position"]
        batch = {
            "dataset_id": "SELF_ECHO_DATASET",
            "observations": [
                {
                    "point_code": "LI4",
                    "subject_pseudonym": "SUBJ-CIRCULAR-01",
                    "canonical_position": list(pred_li4),
                    "data_sharing_agreement_ref": "DUA-MOCK-001",
                    "ethics_approval_or_exemption_ref": "IRB-MOCK-001",
                    "deidentification_method": "SAFE_HARBOR_18_ELEMENTS",
                    "is_authorized_for_clinical_eval": True,
                    "synthetic_fixture": False,
                }
            ]
        }
        summary = validator.ingest_external_evidence_batch(batch)
        assert summary["ingested_count"] == 0
        assert summary["quarantined_count"] == 1
        assert summary["quarantined_records"][0]["reason"] == QuarantineReason.QUARANTINE_CIRCULAR_EVIDENCE.value

    # -------------------------------------------------------------------------
    # 4. Subject-Level Holdout Partitioning & Leakage Prevention
    # -------------------------------------------------------------------------
    def test_subject_level_holdout_partition_and_lock(self, validator):
        """HoldoutPartitionManager partitions unique subjects deterministically and locks partition."""
        mgr = validator._holdout_manager
        subjects = [f"SUBJ-COHORT-{i:03d}" for i in range(1, 21)]  # 20 subjects

        manifest = mgr.create_partition("PART-PILOT-01", subjects, holdout_ratio=0.2, seed=123)
        assert manifest.is_locked is True
        assert manifest.total_subjects == 20
        assert len(manifest.calibration_subjects) + len(manifest.holdout_subjects) == 20
        assert len(manifest.holdout_subjects) >= 2
        assert len(manifest.manifest_checksum) == 64

        # Zero subject overlap
        assert set(manifest.calibration_subjects) & set(manifest.holdout_subjects) == set()

    def test_holdout_data_leakage_detection(self, validator):
        """verify_no_leakage detects any subject overlap between calibration and holdout."""
        mgr = validator._holdout_manager
        calib = ["SUBJ-001", "SUBJ-002", "SUBJ-003"]
        holdout_clean = ["SUBJ-004", "SUBJ-005"]
        holdout_leaked = ["SUBJ-003", "SUBJ-004"]  # SUBJ-003 is in both!

        assert mgr.verify_no_leakage(calib, holdout_clean) is True

        with pytest.raises(ValueError, match="HOLDOUT_DATA_LEAKAGE_DETECTED"):
            mgr.verify_no_leakage(calib, holdout_leaked)

    # -------------------------------------------------------------------------
    # 5. Blind Dual Independent Review Workflow
    # -------------------------------------------------------------------------
    def test_blind_dual_independent_review_workflow(self, validator):
        """Dual independent review records require separate qualified reviewers and enforce no self-review."""
        obs = validator.create_synthetic_test_observation("LI4", (0.342, 0.812, 0.082))
        obs.observer_id = "RAD-OBSERVER-01"
        validator.import_observations([obs])

        rev1 = ClinicalReviewerCredentials(
            reviewer_id="REV-LEAD-ANATOMIST",
            name="Lead Anatomist",
            role="ANATOMIST",
            affiliation="WG",
            qualification="PhD",
        )
        rev2 = ClinicalReviewerCredentials(
            reviewer_id="REV-CLINICAL-AUDITOR",
            name="Clinical Auditor",
            role="AUDITOR",
            affiliation="Board",
            qualification="MD",
        )

        # Observer cannot review own observation
        rev_bad = ClinicalReviewerCredentials(
            reviewer_id="RAD-OBSERVER-01",
            name="Observer",
            role="OBSERVER",
            affiliation="Lab",
            qualification="MD",
        )
        with pytest.raises(ValueError, match="CONFLICT_OF_INTEREST_DETECTED"):
            validator.register_blind_independent_review(
                "LI4", obs.dataset_id, obs.subject_pseudonym, primary_reviewer=rev_bad, primary_decision="APPROVED"
            )

        # Valid dual review
        rec = validator.register_blind_independent_review(
            "LI4", obs.dataset_id, obs.subject_pseudonym,
            primary_reviewer=rev1, primary_decision="APPROVED",
            secondary_reviewer=rev2, secondary_decision="APPROVED",
        )
        assert rec.consensus_decision == "APPROVED"
        assert rec.primary_reviewer_id == "REV-LEAD-ANATOMIST"
        assert rec.secondary_reviewer_id == "REV-CLINICAL-AUDITOR"

    def test_blind_review_pending_when_secondary_review_absent(self, validator):
        """When secondary review is missing, consensus remains INDEPENDENT_REVIEW_PENDING."""
        obs = validator.create_synthetic_test_observation("LI4", (0.342, 0.812, 0.082))
        obs.observer_id = "RAD-OBSERVER-01"
        validator.import_observations([obs])

        rev1 = ClinicalReviewerCredentials(
            reviewer_id="REV-LEAD-ANATOMIST",
            name="Lead Anatomist",
            role="ANATOMIST",
            affiliation="WG",
            qualification="PhD",
        )
        rec = validator.register_blind_independent_review(
            "LI4", obs.dataset_id, obs.subject_pseudonym,
            primary_reviewer=rev1, primary_decision="APPROVED",
            secondary_reviewer=None,
        )
        assert rec.consensus_decision == "INDEPENDENT_REVIEW_PENDING"

    # -------------------------------------------------------------------------
    # 6. Pre-Registered Accuracy Thresholds & Quantitative Analytics
    # -------------------------------------------------------------------------
    def test_pre_registered_accuracy_thresholds_evaluation(self, validator):
        """Validator evaluates comparisons against pre-registered RMSE thresholds."""
        th = PreRegisteredAccuracyThresholds(
            high_accuracy_rmse_mm=5.0,
            acceptable_accuracy_rmse_mm=10.0,
            max_outlier_tolerance_mm=15.0,
        )

        # Mock comparisons with high accuracy (RMSE ~ 2.0 mm)
        comp1 = validator.validate_point("LI4")
        # In absence of ground truth, residual is None -> INCONCLUSIVE
        res_empty = validator.evaluate_against_pre_registered_thresholds([comp1], thresholds=th)
        assert res_empty["verdict"] == "INCONCLUSIVE"

        # Create synthetic observations to test threshold evaluation (offset by 2mm)
        obs_li4 = validator.create_synthetic_test_observation("LI4", (0.344, 0.812, 0.082))  # dx = 2mm
        obs_st36 = validator.create_synthetic_test_observation("ST36", (0.112, 0.388, 0.066))  # dz = 2mm
        validator.import_observations([obs_li4, obs_st36])

        c1 = validator.validate_point("LI4", dataset_id="SYNTHETIC_FIXTURE_DATASET")
        c2 = validator.validate_point("ST36", dataset_id="SYNTHETIC_FIXTURE_DATASET")

        eval_res = validator.evaluate_against_pre_registered_thresholds([c1, c2], thresholds=th)
        assert eval_res["verdict"] == "HIGH_ACCURACY_CONFIRMED"
        assert eval_res["rmse_mm"] <= 5.0
        assert eval_res["sample_size"] == 2

    # -------------------------------------------------------------------------
    # 7. SQLite Persistence of Quarantine, Holdouts, and Governance State
    # -------------------------------------------------------------------------
    def test_sqlite_persistence_includes_quarantine_and_holdouts(self, validator, tmp_path):
        """SQLite round-trip preserves quarantined records and holdout partition manifests."""
        db_path = str(tmp_path / "test_p10_persistence.db")

        # Create a quarantine record
        q_item = QuarantinedObservation(
            point_code="LI4",
            dataset_id="DS-TEST-Q",
            subject_pseudonym="SUBJ-Q-01",
            reason=QuarantineReason.QUARANTINE_UNAUTHORIZED_DATA,
            details="Missing DUA",
            raw_payload={"point": "LI4"},
        )
        validator._quarantined_records.append(q_item)

        exp_res = validator.export_to_db(db_path)
        assert exp_res["quarantined"] >= 1

        fresh_val = IndependentAnatomicalValidator()
        imp_res = fresh_val.import_from_db(db_path)
        assert imp_res["quarantined"] >= 1

        q_retrieved = fresh_val.get_quarantined_records()
        assert len(q_retrieved) >= 1
        assert q_retrieved[0].reason == QuarantineReason.QUARANTINE_UNAUTHORIZED_DATA
        assert q_retrieved[0].point_code == "LI4"

    # -------------------------------------------------------------------------
    # 8. Governance State Machine Verification
    # -------------------------------------------------------------------------
    def test_governance_state_machine_reports_pending_without_real_data(self, validator):
        """Without authorized empirical datasets, governance state reports EXTERNAL_DATA_PENDING."""
        state = validator.get_ingestion_governance_state()
        assert state in (EvidenceIngestionState.EXTERNAL_DATA_PENDING.value, EvidenceIngestionState.ENGINEERING_READY.value)
        assert state != EvidenceIngestionState.CLINICAL_VERIFICATION_PENDING.value
        assert state != EvidenceIngestionState.INDEPENDENTLY_EVALUATED.value
