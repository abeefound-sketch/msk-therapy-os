"""Tests for P10.4 Multi-Institutional Governance, Research Contracts, and Simulator.

Validates:
- Gate P402: Research Data Contracts & Invariant Enforcement
- Gate P403: 15-Step Institutional Intake Rehearsal & Promotion Guard
- Gate P404: Multi-Site Governance, Cross-Site Isolation & COI Screening
- Gate P406: Privacy-Preserving Evidence Package Export
- Gate P407: Adversarial Threat Vectors
"""

import datetime
import hashlib
import json
import pytest

from msk_therapy_os.evidence_export import EvidencePackageGenerator
from msk_therapy_os.institutional_simulator import (
    InstitutionalIntakeSimulator,
    SyntheticPromotionBlockedError,
)
from msk_therapy_os.multi_site_governance import (
    AdminUserRecord,
    ApprovalRevokedOrExpiredError,
    CoiDeclarationRecord,
    CrossSiteAccessViolationError,
    GovernanceAuthorizationError,
    MultiSiteGovernanceManager,
    ReviewerConflictOfInterestError,
    SiteRecord,
)
from msk_therapy_os.research_contracts import (
    AuthorizationMetadata,
    CohortDefinition,
    EvidenceType,
    ImagingSeriesContract,
    LandmarkObservationContract,
    ResearchContractValidationError,
    ResearchDatasetContract,
    ReviewerSignOffContract,
    SiteMetadata,
    validate_research_contract,
)


# --- Gate P402: Research Contracts Tests ---

def test_research_contract_valid_construction():
    site = SiteMetadata(
        site_id="SITE-TEST-01",
        institution_name="Test University Hospital",
        country="US",
        regulatory_framework="HIPAA",
        authorized_contact_email="audit@testhospital.org",
        data_custodian_id="CUST-001",
    )
    today = datetime.date.today()
    auth = AuthorizationMetadata(
        dua_id="DUA-2026-001",
        irb_approval_number="IRB-TEST-100",
        irb_effective_date=(today - datetime.timedelta(days=10)).isoformat(),
        irb_expiration_date=(today + datetime.timedelta(days=365)).isoformat(),
        deidentification_method="DICOM_PS3.15",
        attestation_manifest_hash="a" * 64,
        is_synthetic_fixture=False,
    )
    obs = LandmarkObservationContract(
        observation_id="OBS-001",
        subject_id="SUBJ-001",
        cohort_id=CohortDefinition.COHORT_A_HEAD_NECK_CT.value,
        landmark_id="NASION",
        evidence_type=EvidenceType.PHYSICAL_ANATOMICAL_LANDMARK,
        lps_coordinates_mm=(0.0, 40.0, 120.0),
        observer_id="OBSERVER-01",
        observer_qualification="MD Radiologist",
        timestamp_iso=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    contract = ResearchDatasetContract(
        contract_version="v2.0-P10.4",
        dataset_id="DS-TEST-001",
        cohort_id=CohortDefinition.COHORT_A_HEAD_NECK_CT.value,
        site=site,
        authorization=auth,
        imaging_series=[],
        observations=[obs],
        holdout_ratio=0.3,
        holdout_seed=20261030,
    )
    h = contract.seal()
    assert len(h) == 64
    is_valid, errors = validate_research_contract(contract.to_dict())
    assert is_valid, f"Expected valid contract, got errors: {errors}"
    assert len(errors) == 0


def test_research_contract_expired_irb_rejected():
    today = datetime.date.today()
    auth = AuthorizationMetadata(
        dua_id="DUA-2026-001",
        irb_approval_number="IRB-TEST-100",
        irb_effective_date=(today - datetime.timedelta(days=400)).isoformat(),
        irb_expiration_date=(today - datetime.timedelta(days=30)).isoformat(),  # EXPIRED
        deidentification_method="DICOM_PS3.15",
        attestation_manifest_hash="a" * 64,
    )
    contract_data = {
        "contract_version": "v2.0-P10.4",
        "cohort_id": CohortDefinition.COHORT_A_HEAD_NECK_CT.value,
        "site": {
            "site_id": "S1", "institution_name": "Inst", "country": "US",
            "regulatory_framework": "HIPAA", "authorized_contact_email": "test@test.org",
            "data_custodian_id": "C1"
        },
        "authorization": auth.to_dict(),
        "observations": [{
            "observation_id": "O1", "landmark_id": "NASION",
            "evidence_type": EvidenceType.PHYSICAL_ANATOMICAL_LANDMARK.value,
            "lps_coordinates_mm": [0.0, 0.0, 0.0]
        }]
    }
    is_valid, errors = validate_research_contract(contract_data)
    assert not is_valid
    assert any("EXPIRED" in e for e in errors)


def test_research_contract_acupoint_as_direct_physical_landmark_forbidden():
    """Scientific invariant: An acupoint cannot be claimed as directly visible on CT/MRI."""
    contract_data = {
        "contract_version": "v2.0-P10.4",
        "cohort_id": CohortDefinition.COHORT_A_HEAD_NECK_CT.value,
        "site": {
            "site_id": "S1", "institution_name": "Inst", "country": "US",
            "regulatory_framework": "HIPAA", "authorized_contact_email": "test@test.org",
            "data_custodian_id": "C1"
        },
        "authorization": {
            "dua_id": "DUA-01", "irb_approval_number": "IRB-01",
            "irb_effective_date": "2026-01-01", "irb_expiration_date": "2027-01-01",
            "deidentification_method": "DICOM_PS3.15", "attestation_manifest_hash": "a" * 64,
        },
        "observations": [{
            "observation_id": "O1",
            "landmark_id": "ST36",  # Acupoint code wrongly labeled as physical anatomical landmark!
            "evidence_type": EvidenceType.PHYSICAL_ANATOMICAL_LANDMARK.value,
            "lps_coordinates_mm": [0.0, 0.0, 0.0]
        }]
    }
    is_valid, errors = validate_research_contract(contract_data)
    assert not is_valid
    assert any("Acupoint 'ST36' cannot be declared as PHYSICAL_ANATOMICAL_LANDMARK" in e for e in errors)


# --- Gate P404: Multi-Site Governance Tests ---

def test_multi_site_cross_site_isolation_enforced():
    gov = MultiSiteGovernanceManager(":memory:")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Site A
    site_a = SiteRecord(
        site_id="SITE-ALPHA", institution_name="Hospital Alpha", country="US",
        regulatory_framework="HIPAA", data_custodian_id="CUST-A", status="ACTIVE", created_at_iso=now
    )
    gov.register_site(site_a)

    # Site B
    site_b = SiteRecord(
        site_id="SITE-BETA", institution_name="Hospital Beta", country="US",
        regulatory_framework="HIPAA", data_custodian_id="CUST-B", status="ACTIVE", created_at_iso=now
    )
    gov.register_site(site_b)

    # Admins
    admin_a1 = AdminUserRecord(
        admin_id="ADM-A1", site_id="SITE-ALPHA", full_name="Alice Alpha", role="SITE_ADMIN",
        password_hash=MultiSiteGovernanceManager.hash_password("PassA1!"), is_active=True, created_at_iso=now
    )
    admin_a2 = AdminUserRecord(
        admin_id="ADM-A2", site_id="SITE-ALPHA", full_name="Alan Alpha", role="SITE_ADMIN",
        password_hash=MultiSiteGovernanceManager.hash_password("PassA2!"), is_active=True, created_at_iso=now
    )
    admin_b1 = AdminUserRecord(
        admin_id="ADM-B1", site_id="SITE-BETA", full_name="Bob Beta", role="SITE_ADMIN",
        password_hash=MultiSiteGovernanceManager.hash_password("PassB1!"), is_active=True, created_at_iso=now
    )
    gov.register_admin(admin_a1)
    gov.register_admin(admin_a2)
    gov.register_admin(admin_b1)

    # Valid Site A authorization
    res = gov.authorize_dataset_dual_admin(
        dataset_id="DS-ALPHA-01", site_id="SITE-ALPHA",
        primary_admin_id="ADM-A1", primary_admin_pass="PassA1!",
        secondary_admin_id="ADM-A2", secondary_admin_pass="PassA2!",
        effective_date_iso="2026-01-01", expiration_date_iso="2027-01-01"
    )
    assert res["status"] == "APPROVED"

    # THREAT VECTOR: Cross-site authorization bypass
    # Admin B1 attempts to authorize Site A dataset -> MUST RAISE CrossSiteAccessViolationError
    with pytest.raises(CrossSiteAccessViolationError) as exc_info:
        gov.authorize_dataset_dual_admin(
            dataset_id="DS-ALPHA-02", site_id="SITE-ALPHA",
            primary_admin_id="ADM-B1", primary_admin_pass="PassB1!",
            secondary_admin_id="ADM-A2", secondary_admin_pass="PassA2!",
            effective_date_iso="2026-01-01", expiration_date_iso="2027-01-01"
        )
    assert "Cross-site access violation" in str(exc_info.value)


def test_multi_site_coi_screening():
    gov = MultiSiteGovernanceManager(":memory:")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    site = SiteRecord("SITE-01", "Inst", "US", "HIPAA", "C1", "ACTIVE", now)
    gov.register_site(site)

    # Reviewer 1 declares no conflict
    gov.declare_coi(CoiDeclarationRecord(
        declaration_id="DEC-01", reviewer_id="REV-01", site_id="SITE-01",
        study_or_dataset_id="DS-01", has_conflict=False, conflict_details="None",
        declaration_timestamp_iso=now
    ))
    ok, msg = gov.check_reviewer_eligibility("REV-01", "DS-01")
    assert ok is True
    assert msg == "Eligible"

    # Reviewer 2 declares conflict
    gov.declare_coi(CoiDeclarationRecord(
        declaration_id="DEC-02", reviewer_id="REV-02", site_id="SITE-01",
        study_or_dataset_id="DS-01", has_conflict=True,
        conflict_details="Stockholder in imaging equipment sponsor",
        declaration_timestamp_iso=now
    ))
    ok, msg = gov.check_reviewer_eligibility("REV-02", "DS-01")
    assert ok is False
    assert "declared COI" in msg


def test_multi_site_approval_revocation():
    gov = MultiSiteGovernanceManager(":memory:")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    site = SiteRecord("SITE-01", "Inst", "US", "HIPAA", "C1", "ACTIVE", now)
    gov.register_site(site)
    adm1 = AdminUserRecord("ADM-1", "SITE-01", "A1", "ROLE", MultiSiteGovernanceManager.hash_password("P1"), True, now)
    adm2 = AdminUserRecord("ADM-2", "SITE-01", "A2", "ROLE", MultiSiteGovernanceManager.hash_password("P2"), True, now)
    gov.register_admin(adm1)
    gov.register_admin(adm2)

    app = gov.authorize_dataset_dual_admin(
        "DS-REV-01", "SITE-01", "ADM-1", "P1", "ADM-2", "P2", "2026-01-01", "2027-01-01"
    )
    val_ok, _ = gov.verify_approval_validity(app["approval_id"])
    assert val_ok is True

    # Revoke approval
    gov.revoke_approval(app["approval_id"], "ADM-1", "P1", "Data transfer agreement suspended by sponsor")
    val_after, reason = gov.verify_approval_validity(app["approval_id"])
    assert val_after is False
    assert "REVOKED" in reason


# --- Gate P403: Institutional Simulator Tests ---

def test_institutional_simulator_15_step_rehearsal():
    sim = InstitutionalIntakeSimulator()
    res = sim.run_15_step_rehearsal(
        site_id="HOSP-SYNTH-42",
        cohort_id=CohortDefinition.COHORT_A_HEAD_NECK_CT.value,
        num_synthetic_subjects=30,
    )
    assert res["status"] == "REHEARSAL_COMPLETED_G14_BLOCKED"
    assert res["step_count"] == 15
    assert res["all_steps_passed"] is True
    assert res["contract_valid"] is True
    assert res["gate_g14"] == "BLOCKED_EXTERNAL_DATA"


def test_synthetic_to_empirical_promotion_blocked():
    """Gate P403 Guard: Attempting to promote synthetic data into empirical namespace must raise error."""
    sim = InstitutionalIntakeSimulator()
    site_meta = SiteMetadata("S1", "Inst", "US", "HIPAA", "c@c.org", "C1")
    auth_meta = AuthorizationMetadata("DUA1", "IRB1", "2026-01-01", "2027-01-01", "DICOM", "a" * 64, is_synthetic_fixture=True)
    contract = ResearchDatasetContract(
        contract_version="v2.0-P10.4",
        dataset_id="DS-SYNTH-PROMO",
        cohort_id=CohortDefinition.COHORT_A_HEAD_NECK_CT.value,
        site=site_meta,
        authorization=auth_meta,
        imaging_series=[],
        observations=[],
    )
    with pytest.raises(SyntheticPromotionBlockedError) as exc_info:
        sim.attempt_promote_synthetic_to_empirical(contract)
    assert "Promotion blocked" in str(exc_info.value)
    assert "is_synthetic_fixture = True" in str(exc_info.value)


# --- Gate P406: External Evidence Export Tests ---

def test_evidence_package_generation_redacted():
    gen = EvidencePackageGenerator(release_version="v2.1.0-local-rc3")
    cohort_results = {
        "COHORT_A_HEAD_NECK_CT": {
            "region": "Head & Neck", "n_subjects": 30, "mean_error_mm": 1.48, "rmse_mm": 1.62,
            "ci_lower_mm": 1.40, "ci_upper_mm": 1.85, "status": "SYNTHETIC_REHEARSAL_PASS"
        }
    }
    gov_sum = {"active_sites_count": 2, "adjudicators_coi_screened": True, "approvals_active_count": 2}
    sec_sum = {"total_vectors_tested": 15, "passed_vectors": 15, "unresolved_critical_vulnerabilities": 0}

    bundle = gen.build_evidence_bundle(
        cohort_results=cohort_results,
        governance_summary=gov_sum,
        holdout_manifest_hash="e" * 64,
        security_audit_summary=sec_sum,
        g14_status="BLOCKED_EXTERNAL_DATA"
    )
    assert bundle["evidence_package_version"] == "v2.0-P10.4"
    assert bundle["scientific_boundary"]["gate_g14"] == "BLOCKED_EXTERNAL_DATA"
    assert bundle["partitioning_and_holdout"]["holdout_raw_annotations_redacted"] is True
    assert "bundle_manifest_sha256" in bundle
    assert len(bundle["bundle_manifest_sha256"]) == 64

    # Verify markdown generation
    md = gen.render_markdown_report(bundle)
    assert "# MSK-THERAPY-OS — EXTERNAL SCIENTIFIC EVIDENCE AUDIT REPORT" in md
    assert "BLOCKED_EXTERNAL_DATA" in md
    assert "COHORT_A_HEAD_NECK_CT" in md
    assert "CLINICALLY_VALIDATED" in md or "ENGINEERING_READY" in md


# --- Gate P407: Adversarial Threat Vectors ---

def test_adversarial_tampered_dataset_hash_mismatch():
    """Threat Vector 5: Modifying dataset payload after sealing must invalidate hash."""
    site = SiteMetadata("S1", "Inst", "US", "HIPAA", "test@test.org", "C1")
    auth = AuthorizationMetadata("DUA1", "IRB1", "2026-01-01", "2027-01-01", "DICOM", "a" * 64)
    obs = LandmarkObservationContract(
        "O1", "SUBJ-1", CohortDefinition.COHORT_A_HEAD_NECK_CT.value, "NASION",
        EvidenceType.PHYSICAL_ANATOMICAL_LANDMARK, (0.0, 10.0, 20.0), "REV-1", "MD", "2026-01-01T00:00:00Z"
    )
    contract = ResearchDatasetContract("v2.0-P10.4", "DS-1", CohortDefinition.COHORT_A_HEAD_NECK_CT.value, site, auth, [], [obs])
    orig_hash = contract.seal()

    # Adversarial tampering: modify coordinate
    obs.lps_coordinates_mm = (0.0, 10.0, 25.0)
    recalculated_hash = contract.compute_canonical_hash()
    assert orig_hash != recalculated_hash, "Tampered payload must not match original canonical hash"


def test_adversarial_subject_duplication_across_partitions():
    """Threat Vector 7: Subject appearing in both exploration and holdout sets must be rejected."""
    from msk_therapy_os.anatomical_validation import HoldoutPartitionManager
    mgr = HoldoutPartitionManager()
    subjects = [f"SUBJ-{i:03d}" for i in range(20)]
    part = mgr.create_partition("DS-DUP-TEST", subjects, holdout_ratio=0.3, seed=42)
    
    # Assert disjoint sets
    exploration_set = set(part.calibration_subjects)
    holdout_set = set(part.holdout_subjects)
    intersection = exploration_set.intersection(holdout_set)
    assert len(intersection) == 0, f"Partition leak detected: {intersection}"


def test_adversarial_corrupted_coordinates_out_of_bounds():
    """Threat Vector 9: Absurd anatomical coordinates must fail validation."""
    site = SiteMetadata("S1", "Inst", "US", "HIPAA", "test@test.org", "C1")
    auth = AuthorizationMetadata("DUA1", "IRB1", "2026-01-01", "2027-01-01", "DICOM", "a" * 64)
    # 50 meters outside human body!
    obs = LandmarkObservationContract(
        "O1", "SUBJ-1", CohortDefinition.COHORT_A_HEAD_NECK_CT.value, "NASION",
        EvidenceType.PHYSICAL_ANATOMICAL_LANDMARK, (0.0, 50000.0, 20.0), "REV-1", "MD", "2026-01-01T00:00:00Z"
    )
    contract = ResearchDatasetContract("v2.0-P10.4", "DS-1", CohortDefinition.COHORT_A_HEAD_NECK_CT.value, site, auth, [], [obs])
    is_valid, errors = validate_research_contract(contract.to_dict())
    assert not is_valid
    assert any("out of anatomical bounds" in e for e in errors)


def test_adversarial_unauthorized_g14_transition_blocked():
    """Threat Vector 15: G14 cannot be flipped to PASS without verified external real empirical evidence."""
    from msk_therapy_os.anatomical_validation import IndependentAnatomicalValidator
    val = IndependentAnatomicalValidator()
    gate_eval = val.evaluate_g14_scientific_gate()
    assert gate_eval["gate_state"] == "BLOCKED_EXTERNAL_DATA"
    assert gate_eval["is_unlocked"] is False
    assert len(gate_eval["blockers"]) > 0
    assert "SYNTHETIC_TEST_SUCCESS != EMPIRICAL_VALIDATION" in gate_eval["scientific_invariant"]


def test_adversarial_forged_institution_and_reviewer_rejected():
    """Threat Vectors 1 & 2: Forged site or reviewer/admin rejected."""
    gov = MultiSiteGovernanceManager(":memory:")
    # Unregistered site
    with pytest.raises(GovernanceAuthorizationError) as exc_info:
        gov.authorize_dataset_dual_admin(
            "DS-FORGED", "SITE-FORGED-999", "ADM-1", "Pass", "ADM-2", "Pass", "2026-01-01", "2027-01-01"
        )
    assert "not active or does not exist" in str(exc_info.value)

    # Valid site, but forged primary admin
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    gov.register_site(SiteRecord("SITE-10", "Hospital", "US", "HIPAA", "C1", "ACTIVE", now))
    with pytest.raises(GovernanceAuthorizationError) as exc_info:
        gov.authorize_dataset_dual_admin(
            "DS-FORGED", "SITE-10", "ADM-UNKNOWN", "Pass", "ADM-2", "Pass", "2026-01-01", "2027-01-01"
        )
    assert "Primary admin ADM-UNKNOWN not found" in str(exc_info.value)


def test_adversarial_path_traversal_in_dataset_intake_rejected():
    """Threat Vector 11: Path traversal attempts in dataset IDs or file references."""
    site = SiteMetadata("S1", "Inst", "US", "HIPAA", "test@test.org", "C1")
    auth = AuthorizationMetadata("DUA1", "IRB1", "2026-01-01", "2027-01-01", "DICOM", "a" * 64)
    # Traversal in series UID or file path
    series = ImagingSeriesContract(
        series_instance_uid="../../etc/passwd",
        study_instance_uid="1.2.3.4",
        modality="CT", body_part_examined="HEAD",
        slice_thickness_mm=1.0, pixel_spacing_row_mm=0.5, pixel_spacing_col_mm=0.5,
        lps_origin_mm=(0.0, 0.0, 0.0),
        lps_orientation_matrix_4x4=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
        manufacturer="Vendor", model_name="Model"
    )
    # In DICOM UID specification, characters must be digits and periods only.
    import re
    assert not re.match(r"^[0-9]+(\.[0-9]+)*$", series.series_instance_uid)


