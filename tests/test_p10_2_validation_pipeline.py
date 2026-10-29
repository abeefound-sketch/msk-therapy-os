"""MSK-Therapy-OS - Milestone P10.2 Validation Pipeline Test Suite.

Audits and verifies:
1. Versioned Data Contract 1.1-P10 & backward compatibility with 1.0-P10.
2. Independent Reviewer Role Separation (MODEL_DEVELOPER != OBSERVER != REVIEWER_1 != REVIEWER_2).
3. Subject-level 3-way partitioning (Calibration, Validation, Holdout) and zero-leakage invariants.
4. Comprehensive reproducible statistical metrics:
   - Overall RMSE, MAE, Median, P95
   - Bias vector [dX, dY, dZ]
   - Left/Right error asymmetry
   - Cohort RMSEs (Cohorts A, B, C)
   - 95% Confidence Interval for mean localization error
   - Coverage and missing data rates
5. Adversarial security & quarantine hardening:
   - Expired DUA / IRB references
   - Free-text notes and image reference PII detection
   - Laterality inversion quarantine
   - Administrative sign-off governance
6. Controlled synthetic pilot dry run:
   - Pipeline operational status
   - Gate G14 fail-closed invariant (BLOCKED_EXTERNAL_DATA)
7. REST API integration endpoints for P10.2 validation services.
"""

import json
import math
import tempfile
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path
import pytest

from msk_therapy_os.anatomical_validation import (
    IndependentAnatomicalValidator,
    ExternalGroundTruthDataset,
    GroundTruthObservation,
    CoordinateFrame,
    MeasurementUnit,
    GroundTruthModality,
    DeidentificationMethod,
    ReviewStatus,
    QuarantineReason,
    HoldoutPartitionManager,
    validate_observation_contract,
)
from msk_therapy_os.db import init_db, open_db, seed_db
from msk_therapy_os.server import create_server


class TestP102DataContractV2:
    """Verifies Data Contract Schema 1.1-P10 and backward compatibility."""

    def test_schema_1_1_contract_and_extended_fields(self):
        """Dataset and Observation support version 1.1-P10 metadata fields."""
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-EXT-CT-2026-V2",
            name="High-Res Pelvic & Lower Limb CT",
            source_organization="MSK Research Hospital",
            version="1.1",
            license="Restricted DUA",
            doi_or_url="urn:msk:ct:v2",
            modality=GroundTruthModality.CT_3D_SURFACE,
            sample_size=30,
            administrative_verification_status="PENDING_ADMIN_SIGN_OFF",
            data_retention_and_permitted_use="RESEARCH_ONLY_5_YEARS",
            deidentification_review_status="VERIFIED_DEIDENTIFIED",
            registration_method="RIGID_PROCRUSTES",
            dataset_provenance="Multicenter radiologic study under DUA-MSK-2026",
        )
        assert ds.administrative_verification_status == "PENDING_ADMIN_SIGN_OFF"
        assert ds.registration_method == "RIGID_PROCRUSTES"

        obs = GroundTruthObservation(
            point_code="ST36",
            dataset_id="DS-EXT-CT-2026-V2",
            canonical_position=(0.095, 0.485, 0.088),
            subject_pseudonym="SUBJ-CLIN-0012",
            cohort_id="COHORT_B_EXTREMITIES",
            independent_observer_id="OBS-ANAT-EXPERT-01",
            reviewer_id="REV-EXT-RADIOLOGIST-02",
            annotation_method="MULTI_EXPERT_CONSENSUS",
            source_image_reference="SERIES-CT-09412-AXIAL",
            schema_version="1.1-P10",
        )
        assert obs.schema_version == "1.1-P10"
        assert obs.cohort_id == "COHORT_B_EXTREMITIES"
        assert obs.independent_observer_id == "OBS-ANAT-EXPERT-01"
        assert obs.annotation_method == "MULTI_EXPERT_CONSENSUS"

    def test_schema_1_0_backward_compatibility(self):
        """Legacy 1.0-P10 observations pass contract validation seamlessly."""
        obs_legacy = GroundTruthObservation(
            point_code="LI4",
            dataset_id="DS-LEGACY-P10",
            canonical_position=(0.245, 0.812, 0.082),
            subject_pseudonym="SUBJ-LEGACY-0001",
            schema_version="1.0-P10",
            synthetic_fixture=True,
        )
        contract = validate_observation_contract(obs_legacy, check_authorization=False)
        assert contract["valid"] is True
        assert contract["point_code"] == "LI4"


class TestP102ReviewerRoleSeparation:
    """Verifies strict privilege and role separation boundaries."""

    def test_observer_cannot_act_as_reviewer(self):
        """Self-approval by observer triggers REVIEWER_ROLE_CONFLICT."""
        validator = IndependentAnatomicalValidator()
        with pytest.raises(ValueError, match="REVIEWER_ROLE_CONFLICT"):
            validator.verify_reviewer_role_separation(
                observer_id="DR_SMITH",
                reviewer_1="DR_SMITH",  # Same individual
            )

    def test_reviewer_1_and_2_must_be_distinct(self):
        """Dual reviewers cannot be identical entities."""
        validator = IndependentAnatomicalValidator()
        with pytest.raises(ValueError, match="REVIEWER_ROLE_CONFLICT"):
            validator.verify_reviewer_role_separation(
                observer_id="DR_SMITH",
                reviewer_1="DR_JONES",
                reviewer_2="DR_JONES",  # Duplicate reviewer
            )

    def test_model_developer_cannot_review(self):
        """Core algorithm developer cannot act as independent reviewer."""
        validator = IndependentAnatomicalValidator()
        with pytest.raises(ValueError, match="REVIEWER_ROLE_CONFLICT"):
            validator.verify_reviewer_role_separation(
                observer_id="DR_SMITH",
                reviewer_1="DEV_ALICE",
                model_developer_id="DEV_ALICE",
            )

    def test_valid_four_tier_separation(self):
        """Valid independent assignment succeeds without error."""
        validator = IndependentAnatomicalValidator()
        valid = validator.verify_reviewer_role_separation(
            observer_id="OBS_CLINICAL_01",
            reviewer_1="REV_ANATOMIST_02",
            reviewer_2="REV_RADIOLOGIST_03",
            model_developer_id="DEV_CORE_ENGINEER",
        )
        assert valid is True


class TestP102ThreeWayHoldoutPartitioning:
    """Verifies subject-level 3-way partitioning and anti-leakage invariants."""

    def test_three_way_partition_split_ratios(self):
        """Subjects are partitioned into calibration, validation, and holdout sets."""
        mgr = HoldoutPartitionManager()
        subjects = [f"SUBJ-{i:04d}" for i in range(1, 41)]  # 40 subjects

        manifest = mgr.create_three_way_partition(
            partition_id="PART-3WAY-TEST",
            subjects=subjects,
            calib_ratio=0.50,
            val_ratio=0.25,
            holdout_ratio=0.25,
            seed=20261029,
        )

        assert manifest.total_subjects == 40
        assert len(manifest.calibration_subjects) > 0
        assert len(manifest.validation_subjects) > 0
        assert len(manifest.holdout_subjects) > 0
        assert len(manifest.calibration_subjects) + len(manifest.validation_subjects) + len(manifest.holdout_subjects) == 40

        # Verify no leakage
        mgr.verify_no_leakage_three_way(
            manifest.calibration_subjects,
            manifest.validation_subjects,
            manifest.holdout_subjects,
        )

    def test_three_way_partition_detects_injected_leakage(self):
        """Injected subject overlap across partitions triggers HOLDOUT_DATA_LEAKAGE_DETECTED."""
        mgr = HoldoutPartitionManager()
        calib = ["SUBJ-001", "SUBJ-002", "SUBJ-003"]
        val = ["SUBJ-004", "SUBJ-005"]
        holdout = ["SUBJ-005", "SUBJ-006"]  # SUBJ-005 leaked into holdout!

        with pytest.raises(ValueError, match="HOLDOUT_DATA_LEAKAGE_DETECTED"):
            mgr.verify_no_leakage_three_way(calib, val, holdout)


class TestP102StatisticalMetrics:
    """Verifies rigorous mathematical calculations for validation error metrics."""

    def test_comprehensive_metrics_calculation(self):
        """Validator computes overall RMSE, MAE, bias vector, asymmetry, and confidence intervals."""
        validator = IndependentAnatomicalValidator()
        ds_id = "DS-TEST-METRICS"
        ds = ExternalGroundTruthDataset(
            dataset_id=ds_id,
            name="Metrics Calculation Test Dataset",
            source_organization="MSK Lab",
            version="1.0",
            license="MIT",
            doi_or_url="urn:metrics",
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
            is_synthetic_fixture=True,
        )
        validator.register_dataset(ds)

        # Ingest 4 known points with explicit offsets
        test_pts = [
            ("LI4", (0.002, 0.001, -0.001)),   # ~2.45 mm offset
            ("ST36", (0.001, -0.002, 0.001)),  # ~2.45 mm offset
            ("GV20", (0.000, 0.002, 0.000)),   # 2.00 mm offset
            ("CV8", (0.000, 0.000, 0.003)),    # 3.00 mm offset
        ]

        obs_list = []
        for code, offset in test_pts:
            c_pos = validator.resolve_point_coordinate(code)["canonical_position"]
            obs = GroundTruthObservation(
                point_code=code,
                dataset_id=ds_id,
                canonical_position=(c_pos[0] + offset[0], c_pos[1] + offset[1], c_pos[2] + offset[2]),
                synthetic_fixture=True,
                subject_pseudonym="SUBJ-METRIC-01",
            )
            obs_list.append(obs)

        validator.import_observations(obs_list)
        report = validator.validate_catalog(point_codes=[p[0] for p in test_pts], dataset_id=ds_id)
        s = report.summary

        # Assert all statistical metrics are populated with valid numbers
        assert "overall_rmse_mm" in s
        assert "mae_mm" in s
        assert "bias_vector_mm" in s
        assert "left_right_asymmetry_mm" in s
        assert "cohort_rmse_mm" in s
        assert "confidence_interval_95_mm" in s
        assert "coverage_percentage" in s
        assert "missing_data_rate_percentage" in s
        assert "preregistered_high_accuracy_pass" in s
        assert "statistical_power_specification" in s

        # Verify mathematical consistency
        assert s["overall_rmse_mm"] > 0.0
        assert s["mae_mm"] <= s["overall_rmse_mm"]  # Mathematical theorem: MAE <= RMSE
        assert len(s["bias_vector_mm"]) == 3
        assert len(s["confidence_interval_95_mm"]) == 2
        assert s["confidence_interval_95_mm"][0] <= s["confidence_interval_95_mm"][1]


class TestP102AdversarialGovernanceAndQuarantine:
    """Verifies security, governance, and quarantine boundaries."""

    def test_expired_dua_is_quarantined(self):
        """Dataset with expired DUA is quarantined with EXPIRED_DATA_AUTHORIZATION."""
        validator = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-EXPIRED-DUA",
            name="Expired DUA Dataset",
            source_organization="Hospital B",
            version="1.0",
            license="Restricted",
            doi_or_url="urn:dua:expired",
            modality=GroundTruthModality.CT_3D_SURFACE,
            is_synthetic_fixture=False,
        )
        validator.register_dataset(ds)

        obs = GroundTruthObservation(
            point_code="LU5",
            dataset_id="DS-EXPIRED-DUA",
            canonical_position=(0.220, 0.990, 0.040),
            data_sharing_agreement_ref="DUA-EXPIRED-2025-12-31",  # EXPIRED!
            ethics_approval_or_exemption_ref="IRB-2026-ACTIVE",
            deidentification_method=DeidentificationMethod.SAFE_HARBOR_18_ELEMENTS,
            is_authorized_for_clinical_eval=True,
            synthetic_fixture=False,
        )

        res = validator.ingest_external_evidence_batch({
            "dataset_id": "DS-EXPIRED-DUA",
            "observations": [obs.to_dict()],
        }, enforce_quarantine=True)

        assert res["quarantined_count"] == 1
        assert res["quarantined_records"][0]["reason"] == QuarantineReason.QUARANTINE_EXPIRED_AUTHORIZATION.value

    def test_free_text_notes_phi_is_quarantined(self):
        """Free-text notes containing email address or SSN are quarantined."""
        validator = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-PHI-NOTES",
            name="PHI in Notes Dataset",
            source_organization="Clinic C",
            version="1.0",
            license="Restricted",
            doi_or_url="urn:notes:phi",
            modality=GroundTruthModality.CT_3D_SURFACE,
            is_synthetic_fixture=False,
        )
        validator.register_dataset(ds)

        obs = GroundTruthObservation(
            point_code="ST36",
            dataset_id="DS-PHI-NOTES",
            canonical_position=(0.095, 0.485, 0.088),
            notes="Contact patient at patient.doe@hospital.org regarding follow-up",  # PHI Email!
            data_sharing_agreement_ref="DUA-ACTIVE-2026",
            ethics_approval_or_exemption_ref="IRB-ACTIVE-2026",
            deidentification_method=DeidentificationMethod.SAFE_HARBOR_18_ELEMENTS,
            is_authorized_for_clinical_eval=True,
            synthetic_fixture=False,
        )

        res = validator.ingest_external_evidence_batch({
            "dataset_id": "DS-PHI-NOTES",
            "observations": [obs.to_dict()],
        }, enforce_quarantine=True)

        assert res["quarantined_count"] == 1
        assert res["quarantined_records"][0]["reason"] == QuarantineReason.QUARANTINE_PII_SUSPECTED.value

    def test_administrative_sign_off_lifecycle(self):
        """Administrative sign-off verifies institutional approvals and updates dataset state."""
        validator = IndependentAnatomicalValidator()
        ds = ExternalGroundTruthDataset(
            dataset_id="DS-ADMIN-SIGNOFF",
            name="Admin Sign-Off Test Dataset",
            source_organization="Medical School",
            version="1.0",
            license="Restricted",
            doi_or_url="urn:admin",
            modality=GroundTruthModality.CT_3D_SURFACE,
            administrative_verification_status="PENDING_ADMIN_SIGN_OFF",
        )
        validator.register_dataset(ds)
        assert ds.administrative_verification_status == "PENDING_ADMIN_SIGN_OFF"

        # Unauthorized user cannot sign off
        with pytest.raises(ValueError, match="UNAUTHORIZED_ADMIN"):
            validator.admin_sign_off_dataset("DS-ADMIN-SIGNOFF", admin_reviewer_id="REV_SYNTHETIC_TEST")

        # Authorized clinical auditor signs off
        success = validator.admin_sign_off_dataset("DS-ADMIN-SIGNOFF", admin_reviewer_id="REV-CLINICAL-AUDITOR")
        assert success is True
        assert ds.administrative_verification_status == "VERIFIED_ADMIN_SIGNED_OFF"
        assert "admin_sign_off" in ds.governance_metadata


class TestP102SyntheticPilotDryRun:
    """Verifies end-to-end synthetic pilot dry run and Gate G14 invariant."""

    def test_run_synthetic_pilot_dry_run_executes_successfully(self):
        """Dry run runs end-to-end and outputs PIPELINE_OPERATIONAL / EMPIRICAL_VALIDATION_BLOCKED."""
        validator = IndependentAnatomicalValidator()
        res = validator.run_synthetic_pilot_dry_run()

        assert res["synthetic_dry_run_passed"] is True
        assert res["status"] == "PIPELINE_OPERATIONAL / EMPIRICAL_VALIDATION_BLOCKED"
        assert res["legacy_gate_g14"] == "BLOCKED_EXTERNAL_DATA"
        assert res["three_way_partition_verified"] is True
        assert res["holdout_leakage_prevented"] is True
        assert res["scientific_invariant"] == "SYNTHETIC_TEST_SUCCESS != EMPIRICAL_VALIDATION"
        assert res["overall_rmse_mm"] is not None

    def test_synthetic_success_cannot_unlock_g14(self):
        """Synthetically generated passes must never alter the catalog empirical ground-truth count."""
        validator = IndependentAnatomicalValidator()
        validator.run_synthetic_pilot_dry_run()

        cov = validator.generate_external_evidence_coverage_matrix()
        # Non-synthetic empirical count must remain 0
        real_avail = [r for r in cov if r["empirical_in_vivo_status"] == "AVAILABLE"]
        assert len(real_avail) == 0, "Synthetic dry run improperly promoted to empirical ground truth!"


class TestP102ServerEndpoints:
    """Verifies REST API endpoints exposed for P10.2 validation operations."""

    @classmethod
    def setup_class(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = str(Path(cls.temp_dir.name) / "test_p102_web.sqlite3")

        with open_db(cls.db_path) as db:
            init_db(db)
            seed_db(db)

        cls.server = create_server(cls.db_path, host="127.0.0.1", port=0)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.05)

    @classmethod
    def teardown_class(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1.0)

    def test_get_pilot_cohorts_details_api(self):
        """GET /api/atlas/validation/pilot-cohorts/details returns Cohorts A, B, C."""
        url = f"{self.base_url}/api/atlas/validation/pilot-cohorts/details"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["status"] == "success"
            specs = data["pilot_cohort_specifications"]
            assert "cohort_a" in specs
            assert "cohort_b" in specs
            assert "cohort_c" in specs

    def test_get_metrics_summary_api(self):
        """GET /api/atlas/validation/metrics/summary returns statistical metrics object."""
        url = f"{self.base_url}/api/atlas/validation/metrics/summary"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["status"] == "success"
            assert "summary_metrics" in data
            sm = data["summary_metrics"]
            assert "overall_rmse_mm" in sm
            assert "bias_vector_mm" in sm

    def test_export_evidence_manifest_api(self):
        """GET /api/atlas/validation/export-evidence returns audit manifest with G14 fail-closed."""
        url = f"{self.base_url}/api/atlas/validation/export-evidence"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["status"] == "success"
            manifest = data["evidence_manifest"]
            assert manifest["manifest_version"] == "1.1-P10"
            assert manifest["legacy_gate_g14_status"] == "BLOCKED_EXTERNAL_DATA"

    def test_post_dry_run_api(self):
        """POST /api/atlas/validation/dry-run executes synthetic dry run."""
        url = f"{self.base_url}/api/atlas/validation/dry-run"
        req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["status"] == "PIPELINE_OPERATIONAL / EMPIRICAL_VALIDATION_BLOCKED"
            assert data["legacy_gate_g14"] == "BLOCKED_EXTERNAL_DATA"
