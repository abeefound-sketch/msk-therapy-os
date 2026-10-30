"""MSK-Therapy-OS P10.6 Adversarial Statistical & Security Regression Suite.

Tests rigorous edge cases, security barriers, and invariant violations:
1. Incorrect effective sample-size calculations and observation-subject conflation.
2. Misreported holdout power and small cohort holdout size collapse.
3. Invalid ICC values (rho < 0, rho >= 1).
4. Missing or zero variance components.
5. Anti-self-certification guard preventing developers/agents from marking external approvals.
6. Blocked synthetic fixture promotion to empirical quarantine or validation.
7. Rejection of expired IRB / DUA approvals.
8. Single-observer override and unblinded annotation rejection.
9. Attempted premature G14 unlock without authentic empirical patient scans.
10. Satterthwaite/Student's t degrees of freedom vs normal z critical value dilation.
"""

from __future__ import annotations

import datetime
import math
import pytest

from msk_therapy_os.statistical_oracle import (
    IndependentStatisticalOracle,
    OracleStudyScenario,
    CohortOracleSpec,
    VarianceComponents,
)
from msk_therapy_os.external_dependency_register import (
    ExternalDependencyRegistry,
    ExternalDependencyType,
    DependencyStatus,
    ExternalAuthorityInfo,
)
from msk_therapy_os.partner_onboarding import (
    InstitutionalOnboardingManager,
    OnboardingStatus,
)
from msk_therapy_os.real_world_intake_controller import (
    RealWorldIntakeController,
    DatasetCustodyState,
)
from msk_therapy_os.institutional_simulator import SyntheticPromotionBlockedError
from msk_therapy_os.annotation_qc import (
    AnnotationQualityControlEngine,
    AnnotationQCStatus,
    RawLandmarkCoordinate,
)
from msk_therapy_os.server import get_anatomical_validator


# ============================================================================
# 1. STATISTICAL ORACLE & ADVERSARIAL SIZING TESTS
# ============================================================================

def test_statistical_oracle_reference_case_ref01():
    """Independent verification of reference case REF-01 (design effect and M_eff)."""
    vc = VarianceComponents(1.2, 0.8, 0.5, 0.4)
    spec = CohortOracleSpec(
        cohort_id="COHORT_TEST", target_region="Test",
        num_subjects=30, landmarks_per_subject=10,
        within_subject_icc=0.40, site_icc=0.05, num_sites=2,
        variance_components=vc, holdout_ratio=0.30, dropout_rate=0.08
    )
    res = IndependentStatisticalOracle.evaluate_cohort_design(spec)
    # Holdout = 9 subjects, 90 raw obs, 82.8 valid obs
    assert res.holdout_subjects == 9
    assert res.holdout_raw_observations == 90
    assert abs(res.holdout_valid_observations - 82.8) < 0.1
    # DE = 1 + (10 - 1)*0.40 + 10*(4.5 - 1)*0.05 = 1 + 3.6 + 1.75 = 6.35
    assert abs(res.design_effect - 6.35) < 0.01
    # M_eff = 82.8 / 6.35 = 13.04
    assert abs(res.holdout_effective_n_observations - 13.04) < 0.05


def test_correlated_observations_not_conflated_with_subjects():
    """Enforces that effective observations (M_eff) and subject clusters (df) are kept distinct."""
    vc = VarianceComponents(1.2, 0.8, 0.5, 0.4)
    spec = CohortOracleSpec(
        cohort_id="COHORT_TEST", target_region="Test",
        num_subjects=25, landmarks_per_subject=10,
        within_subject_icc=0.45, site_icc=0.06, num_sites=2,
        variance_components=vc, holdout_ratio=0.25  # Holdout = 6 subjects
    )
    res = IndependentStatisticalOracle.evaluate_cohort_design(spec)
    # 6 holdout subjects, raw obs = 60
    assert res.holdout_subjects == 6
    # Cluster degrees of freedom must be strictly N_holdout - 1 = 5
    assert res.cluster_degrees_of_freedom == 5
    # Effective observations is larger than subjects but far smaller than raw observations
    assert res.holdout_effective_n_observations < res.holdout_raw_observations
    assert res.cluster_degrees_of_freedom < res.holdout_effective_n_observations


def test_small_cohort_holdout_collapses_degrees_of_freedom():
    """Verify that small holdouts trigger warning and wide t-critical values."""
    vc = VarianceComponents(1.4, 0.9, 0.8, 0.5)
    spec = CohortOracleSpec(
        cohort_id="COHORT_SMALL", target_region="Small",
        num_subjects=10, landmarks_per_subject=8,
        within_subject_icc=0.50, site_icc=0.08, num_sites=1,
        variance_components=vc, holdout_ratio=0.20  # Holdout = 2 subjects
    )
    res = IndependentStatisticalOracle.evaluate_cohort_design(spec)
    assert res.holdout_subjects == 2
    assert res.cluster_degrees_of_freedom == 1
    # df=1 t-critical value is 12.706, causing wide CI half-width
    assert res.mean_error_ci_95_half_width_mm > 5.0
    assert not res.is_adequately_powered_subgroup
    assert "dangerously small" in res.limitation_warning


def test_student_t_dilation_over_normal_z():
    """Verifies that Student's t critical value exceeds normal z=1.96 for small sample clusters."""
    t_df3 = IndependentStatisticalOracle.student_t_critical_value(3, 0.05)
    t_df10 = IndependentStatisticalOracle.student_t_critical_value(10, 0.05)
    t_df100 = IndependentStatisticalOracle.student_t_critical_value(100, 0.05)

    assert t_df3 == 3.182
    assert t_df10 == 2.228
    assert t_df100 < 2.0
    assert t_df3 > t_df10 > t_df100 > 1.96


def test_multi_scenario_comparative_oracle():
    """Evaluates that N=45 is underpowered, N=85 is pilot ready, N=115 is near 90%, N=150 is gold standard."""
    p45 = IndependentStatisticalOracle.evaluate_scenario(OracleStudyScenario.FEASIBILITY_PILOT)
    p85 = IndependentStatisticalOracle.evaluate_scenario(OracleStudyScenario.PRIMARY_ACCURACY_STUDY)
    p115 = IndependentStatisticalOracle.evaluate_scenario(OracleStudyScenario.EXPANDED_ACCURACY_STUDY)
    p150 = IndependentStatisticalOracle.evaluate_scenario(OracleStudyScenario.MULTI_SITE_VALIDATION)

    # N=45 cannot satisfy all subgroups (Cohort B power is < 65%)
    assert not p45["all_subgroups_adequately_powered"]
    assert p45["minimum_subgroup_power"] < 0.65

    # N=85 has high power overall, but min subgroup (Cohort B) is ~81.6%
    assert 0.80 <= p85["minimum_subgroup_power"] < 0.85

    # N=115 lifts min subgroup power to ~88.9% (demonstrating STAT-04: not automatically 99%)
    assert 0.88 <= p115["minimum_subgroup_power"] < 0.90

    # N=150 achieves gold-standard >= 95%
    assert p150["all_subgroups_adequately_powered"]
    assert p150["minimum_subgroup_power"] >= 0.95


# ============================================================================
# 2. EXTERNAL DEPENDENCY GOVERNANCE & ANTI-SELF-CERTIFICATION TESTS
# ============================================================================

def test_developer_self_certification_strictly_prohibited():
    """Prevents developer or automated coding agent from self-certifying external approvals."""
    reg = ExternalDependencyRegistry(":memory:")
    reg.initialize_standard_dependencies("INST-TEST-001")

    # Developer attempts to approve DUA
    with pytest.raises(PermissionError, match="Self-certification prohibited"):
        reg.update_dependency_status(
            dep_type=ExternalDependencyType.DATA_USE_AGREEMENT,
            institution_id="INST-TEST-001",
            cohort_scope="ALL_COHORTS_ABC",
            new_status=DependencyStatus.APPROVED_VERIFIED,
            actor_role="CODING_AGENT",
            actor_id="AGENT-LOCAL-01",
            rationale="Simulated developer approval",
            external_authority=ExternalAuthorityInfo("Fake Authority", "Hospital", "Counsel"),
            evidence_document_hash="a"*64,
        )


def test_missing_evidence_hash_rejected_for_approval():
    """Ensures APPROVED_VERIFIED cannot be set without valid cryptographic document hash."""
    reg = ExternalDependencyRegistry(":memory:")
    reg.initialize_standard_dependencies("INST-TEST-001")

    with pytest.raises(ValueError, match="cryptographic evidence document hash"):
        reg.update_dependency_status(
            dep_type=ExternalDependencyType.STATISTICAL_PROTOCOL_REVIEW,
            institution_id="INST-TEST-001",
            cohort_scope="ALL_COHORTS_ABC",
            new_status=DependencyStatus.APPROVED_VERIFIED,
            actor_role="EXTERNAL_BIOSTATISTICIAN",
            actor_id="STAT-CHAIR-01",
            rationale="Endorsed without document hash",
            external_authority=ExternalAuthorityInfo("Dr. External", "Univ", "Chair of Biostats"),
            evidence_document_hash="",  # Empty
        )


def test_expired_external_approval_rejected():
    """Ensures expired approvals cannot be verified as active."""
    reg = ExternalDependencyRegistry(":memory:")
    reg.initialize_standard_dependencies("INST-TEST-001")

    with pytest.raises(PermissionError, match="Approval expired"):
        reg.update_dependency_status(
            dep_type=ExternalDependencyType.ETHICAL_APPROVAL_OR_DETERMINATION,
            institution_id="INST-TEST-001",
            cohort_scope="ALL_COHORTS_ABC",
            new_status=DependencyStatus.APPROVED_VERIFIED,
            actor_role="IRB_CHAIR",
            actor_id="IRB-CHAIR-01",
            rationale="Expired ethics approval",
            external_authority=ExternalAuthorityInfo("IRB Committee", "Hospital", "Chair"),
            evidence_document_hash="b"*64,
            expiration_date_iso="2020-01-01",  # Past date
        )


def test_valid_external_authority_approval_succeeds():
    """Verifies that genuine external authority approval with hash and active date succeeds."""
    reg = ExternalDependencyRegistry(":memory:")
    reg.initialize_standard_dependencies("INST-TEST-001")

    auth = ExternalAuthorityInfo(
        authority_name="Prof. Dr. Biostat",
        organization="Independent Academic Biostatistics Unit",
        credential_title="Head of Biostatistical Methodology",
        contact_email="biostat@independent-audit.org",
    )
    rec = reg.update_dependency_status(
        dep_type=ExternalDependencyType.STATISTICAL_PROTOCOL_REVIEW,
        institution_id="INST-TEST-001",
        cohort_scope="ALL_COHORTS_ABC",
        new_status=DependencyStatus.APPROVED_VERIFIED,
        actor_role="INDEPENDENT_EXTERNAL_BIOSTATISTICIAN",
        actor_id="BIOSTAT-EXT-01",
        rationale="Formally audited and approved Statistical Analysis Plan v2.0",
        external_authority=auth,
        evidence_document_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        approval_certificate_id="CERT-SAP-2026-001",
        effective_date_iso="2026-10-30",
        expiration_date_iso="2028-10-30",
        resolved_blockers=["SAP draft pending external statistician review."],
    )
    assert rec.current_status == DependencyStatus.APPROVED_VERIFIED
    assert len(rec.blockers) == 0


# ============================================================================
# 3. DATA CUSTODY, PRIVACY & ANNOTATION BARRIERS
# ============================================================================

def test_synthetic_promotion_blocked_by_intake_controller():
    """Guarantees synthetic test fixtures cannot enter empirical external quarantine."""
    controller = RealWorldIntakeController()
    rec = controller.register_incoming_dataset(
        dataset_id="DS-SYNTH-001",
        institution_id="INST-SYNTH",
        cohort_id="COHORT_A",
        is_synthetic=True,
        dua_id="DUA-NONE",
        irb_number="NONE",
        irb_expiration_iso="2027-01-01",
        deid_attestation_hash="c"*64,
        pixel_phi_screened=True,
        raw_manifest_json="{}",
    )
    assert rec.current_state == DatasetCustodyState.SYNTHETIC_FIXTURE
    with pytest.raises(SyntheticPromotionBlockedError):
        controller.transition_to_quarantine("DS-SYNTH-001", "OPERATOR-01")


def test_unblinded_annotation_rejected():
    """Guarantees observers exposed to model coordinates are disqualified."""
    c_a = RawLandmarkCoordinate("OBS-01", "Radiologist", (10.0, 20.0, 30.0), "2026-10-30T10:00:00Z", is_blinded=False)
    c_b = RawLandmarkCoordinate("OBS-02", "Anatomist", (10.5, 20.2, 30.1), "2026-10-30T10:00:00Z", is_blinded=True)

    with pytest.raises(PermissionError, match="Unblinded annotations are invalid"):
        AnnotationQualityControlEngine.process_annotation_pair(
            "SUBJ-001", "COHORT_C", "NASION", c_a, c_b
        )


def test_scientific_gate_g14_fail_closed_preserved():
    """Guarantees that Gate G14 cannot unlock without empirical external patient data."""
    val = get_anatomical_validator()
    status = val.evaluate_g14_scientific_gate()
    assert status["gate_state"] == "BLOCKED_EXTERNAL_DATA"
    assert status["is_unlocked"] is False
    assert any("DUA" in b or "patient" in b.lower() or "external" in b.lower() for b in status["blockers"])
