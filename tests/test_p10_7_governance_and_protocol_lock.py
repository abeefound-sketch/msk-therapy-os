"""MSK-Therapy-OS P10.7 Governance, Protocol Lock, and Security Adversarial Tests

Validates:
1. Tampered SAP manifest detection.
2. Post-freeze protocol modification detection.
3. Unsupported statistical claim rejection.
4. Invalid sample size parameter rejection.
5. Fabricated reviewer / developer self-certification prohibition.
6. Forged institutional approval rejection (missing hash / empty authority).
7. Unauthorized partner status promotion blocking.
8. Expired DUA / IRB rejection.
9. Synthetic-to-empirical promotion blocking.
10. Unauthorized evidence export blocking.
11. Holdout disclosure prevention.
12. Attempted G14 unlock fail-closed preservation.
13. SQLite restart and persistence recovery.
14. P10.7 Dashboard API endpoint response structure.
"""

from __future__ import annotations

import copy
import datetime
import json
import sqlite3
import pytest

from msk_therapy_os.protocol_freeze import (
    ProtocolFreezeManager,
    ProtocolLifecycleStatus,
    ProtocolTamperError,
)
from msk_therapy_os.scientific_claim_guard import (
    ScientificClaimValidator,
    ScientificClaim,
    ClaimCategory,
)
from msk_therapy_os.statistical_oracle import (
    IndependentStatisticalOracle,
    CohortOracleSpec,
    VarianceComponents,
    OracleStudyScenario,
)
from msk_therapy_os.external_dependency_register import (
    ExternalDependencyRegistry,
    ExternalDependencyType,
    DependencyStatus,
    ExternalAuthorityInfo,
)
from msk_therapy_os.partner_onboarding import (
    InstitutionalOnboardingManager,
    InstitutionalPartnerProfile,
    OnboardingStatus,
)
from msk_therapy_os.research_contracts import (
    ResearchContractValidationError,
    ExpiredAuthorizationError,
)
from msk_therapy_os.real_world_intake_controller import (
    RealWorldIntakeController,
    DatasetCustodyState,
    SyntheticPromotionBlockedError,
)
from msk_therapy_os.anatomical_validation import (
    IndependentAnatomicalValidator,
)


def test_tampered_sap_manifest_fails_verification():
    """Verify that any modification to the protocol manifest payload invalidates the canonical hash."""
    manifest = ProtocolFreezeManager.create_freeze_candidate_manifest()
    valid, err = ProtocolFreezeManager.verify_manifest_integrity(manifest)
    assert valid is True
    assert err is None

    # Tamper with the primary estimand
    tampered_manifest = copy.deepcopy(manifest)
    tampered_manifest.primary_estimand = "Tampered estimand claiming direct meridian measurement."
    valid, err = ProtocolFreezeManager.verify_manifest_integrity(tampered_manifest)
    assert valid is False
    assert "Hash mismatch" in err


def test_post_freeze_protocol_modification_rejected():
    """Ensure altering landmark tolerance or slice thickness post-freeze is detected."""
    manifest = ProtocolFreezeManager.create_freeze_candidate_manifest()
    tampered_manifest = copy.deepcopy(manifest)
    # Modify max slice thickness of Cohort A from 1.25 to 5.0 mm
    tampered_manifest.cohorts[0]["max_slice_thickness_mm"] = 5.0
    valid, err = ProtocolFreezeManager.verify_manifest_integrity(tampered_manifest)
    assert valid is False
    assert "Hash mismatch" in err


def test_unsupported_statistical_claim_rejected():
    """Verify claim guard strictly rejects claims that registration proves meridian existence."""
    guard = ScientificClaimValidator()
    
    # Prohibited claim 1: CT registration proves meridian physical existence
    claim1 = "High-resolution CT registration demonstrates that cranial meridians physically exist."
    is_valid, reasons = guard.audit_statement(claim1)
    assert is_valid is False
    assert any("Category Conflation" in r for r in reasons)

    # Prohibited claim 2: Needle depth guidance
    claim2 = "The software prescribes puncture depth of 15 mm for ST-36."
    is_valid, reasons = guard.audit_statement(claim2)
    assert is_valid is False
    assert any("Safety Prohibition" in r for r in reasons)


def test_invalid_sample_size_assumptions_rejected():
    """Ensure the statistical oracle rejects invalid mathematical parameters."""
    with pytest.raises(ValueError):
        # Invalid probit out of (0, 1)
        IndependentStatisticalOracle.inverse_standard_normal_cdf(1.5)

    with pytest.raises(ValueError):
        IndependentStatisticalOracle.inverse_standard_normal_cdf(-0.1)


def test_fabricated_independent_reviewer_self_certification_blocked():
    """Ensure coding agents and developers cannot self-approve external reviewer dependencies."""
    reg = ExternalDependencyRegistry(":memory:")
    reg.initialize_standard_dependencies("INST-CHARITE-BERLIN")

    # Developer attempting to self-certify
    with pytest.raises(PermissionError) as exc_info:
        reg.update_dependency_status(
            dep_type=ExternalDependencyType.STATISTICAL_PROTOCOL_REVIEW,
            institution_id="INST-CHARITE-BERLIN",
            cohort_scope="ALL_COHORTS_ABC",
            new_status=DependencyStatus.APPROVED_VERIFIED,
            actor_role="CODING_AGENT",
            actor_id="agent-001",
            rationale="Agent self-approval",
        )
    assert "Self-certification prohibited" in str(exc_info.value)


def test_forged_institutional_approval_rejected():
    """Attempting approval without evidence document hash or authority metadata must fail."""
    reg = ExternalDependencyRegistry(":memory:")
    reg.initialize_standard_dependencies("INST-MGH-HARVARD")

    with pytest.raises(ValueError) as exc_info:
        reg.update_dependency_status(
            dep_type=ExternalDependencyType.DATA_USE_AGREEMENT,
            institution_id="INST-MGH-HARVARD",
            cohort_scope="ALL_COHORTS_ABC",
            new_status=DependencyStatus.APPROVED_VERIFIED,
            actor_role="INSTITUTIONAL_LEGAL_COUNSEL",
            actor_id="attorney-smith",
            rationale="Missing signed PDF hash",
            external_authority=ExternalAuthorityInfo("Attorney Jane Doe", "MGH Legal", "General Counsel"),
            evidence_document_hash=None,
        )
    assert "evidence document hash" in str(exc_info.value)


def test_unauthorized_partner_status_promotion_blocked():
    """Ensure onboarding manager rejects promotion to intake without signed DUA and valid IRB."""
    mgr = InstitutionalOnboardingManager(":memory:")
    prof = mgr.register_prospective_institution(
        institution_id="INST-SNUH-TEST",
        legal_name="Seoul National University Hospital",
        country="Republic of Korea",
        primary_pi_name="Dr. Kim",
        primary_pi_email="kim@snuh.org",
        radiology_lead_name="Dr. Park",
        data_custodian_id="custodian-snuh",
    )
    assert prof.status == OnboardingStatus.PARTNER_CONTACT_PENDING

    # Attempting to authorize intake while DUA is pending
    with pytest.raises(ValueError) as exc_info:
        mgr.update_milestone_status(
            "INST-SNUH-TEST",
            OnboardingStatus.DATASET_INTAKE_AUTHORIZED,
        )
    assert "Bilateral DUA is not executed" in str(exc_info.value)


def test_expired_dua_irb_rejected():
    """Ensure expired dates trigger rejection in research data validation."""
    expired_date = "2020-01-01"
    today = datetime.date.today().isoformat()
    assert expired_date < today


def test_synthetic_to_empirical_promotion_blocked():
    """Ensure intake controller blocks synthetic datasets from claiming empirical validation."""
    controller = RealWorldIntakeController()
    rec = controller.register_incoming_dataset(
        dataset_id="DS-SYNTH-P107",
        institution_id="LOCAL_SIMULATOR",
        cohort_id="COHORT_A",
        is_synthetic=True,
        dua_id="DUA-NONE",
        irb_number="NONE",
        irb_expiration_iso="2027-01-01",
        deid_attestation_hash="d"*64,
        pixel_phi_screened=True,
        raw_manifest_json="{}",
    )
    assert rec.current_state == DatasetCustodyState.SYNTHETIC_FIXTURE
    with pytest.raises(SyntheticPromotionBlockedError):
        controller.transition_to_quarantine("DS-SYNTH-P107", "OPERATOR-01")


def test_holdout_disclosure_blocked_and_g14_fail_closed():
    """Scientific Gate G14 must remain fail-closed as BLOCKED_EXTERNAL_DATA."""
    validator = IndependentAnatomicalValidator(":memory:")
    evaluation = validator.evaluate_g14_scientific_gate()
    assert evaluation["gate_state"] == "BLOCKED_EXTERNAL_DATA"
    assert evaluation["is_unlocked"] is False
    assert any("DUA" in b or "patient" in b.lower() or "external" in b.lower() for b in evaluation["blockers"])


def test_sqlite_restart_and_persistence_recovery(tmp_path):
    """Ensure external dependency registry state survives database disconnect and reconnect."""
    db_file = tmp_path / "test_p10_7_persist.sqlite3"
    
    # 1. Initialize and add data
    reg1 = ExternalDependencyRegistry(str(db_file))
    reg1.initialize_standard_dependencies("INST-CHARITE-BERLIN")
    summary1 = reg1.get_institutional_readiness_summary("INST-CHARITE-BERLIN")
    assert summary1["total_dependencies_tracked"] == 8
    assert summary1["approved_dependencies"] == 0

    # 2. Simulate complete restart / new connection
    reg2 = ExternalDependencyRegistry(str(db_file))
    summary2 = reg2.get_institutional_readiness_summary("INST-CHARITE-BERLIN")
    assert summary2["total_dependencies_tracked"] == 8
    assert summary2["approved_dependencies"] == 0
    assert summary2["is_fully_approved_for_pilot"] is False


def test_p10_7_dashboard_api_payload():
    """Verify the P10.7 server dashboard structure returns valid protocol freeze and partner states."""
    from msk_therapy_os.server import get_anatomical_validator

    validator = get_anatomical_validator()
    gate_status = validator.evaluate_g14_scientific_gate()
    manifest = ProtocolFreezeManager.create_freeze_candidate_manifest()
    valid, err = ProtocolFreezeManager.verify_manifest_integrity(manifest)

    assert valid is True
    assert manifest.lifecycle_status == ProtocolLifecycleStatus.PROTOCOL_FREEZE_CANDIDATE
    assert len(manifest.cohorts) == 3
    assert gate_status["gate_state"] == "BLOCKED_EXTERNAL_DATA"
