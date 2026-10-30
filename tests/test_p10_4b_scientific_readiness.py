"""Tests for P10.4B Institutional Pilot Activation and Scientific Readiness.

Validates:
- Gate B402: Statistical Power, Cluster Design Effect, and Sample Allocation
- Gate B405: Scientific Claim Boundary Guard (Prohibition of Category Conflation)
- Gate B406: External Independent Reviewer Workflow and Developer Exclusion
"""

import pytest

from msk_therapy_os.reviewer_workflow import (
    IndependentReviewEngine,
    ReviewDossierItem,
    ReviewVerdict,
    ReviewerCOIUnresolvedError,
    ReviewerIdentity,
    ReviewerImpersonationError,
    ReviewerRole,
)
from msk_therapy_os.scientific_claim_guard import (
    ClaimCategory,
    InvalidScientificClaimError,
    ScientificClaim,
    ScientificClaimValidator,
)
from msk_therapy_os.statistical_power import (
    CohortSampleSpec,
    StatisticalProtocolEvaluator,
    evaluate_statistical_power,
)


# --- Gate B405: Scientific Claim Guard Tests ---

def test_claim_guard_prohibits_registration_proving_meridian_existence():
    """Invariant: CT/MRI registration accuracy cannot be asserted as proof of meridian physical existence."""
    statement = "The CT registration achieved 1.2mm RMSE, which proves the physical meridian exists."
    ok, violations = ScientificClaimValidator.audit_statement(statement)
    assert not ok
    assert any("Category Conflation" in v for v in violations)

    with pytest.raises(InvalidScientificClaimError):
        ScientificClaimValidator.enforce_guard(statement)


def test_claim_guard_prohibits_coordinate_accuracy_proving_efficacy():
    """Invariant: Coordinate estimation cannot be asserted as proof of therapeutic efficacy."""
    statement = "The B-cun algorithm accuracy validates clinical treatment efficacy for chronic knee osteoarthritis."
    ok, violations = ScientificClaimValidator.audit_statement(statement)
    assert not ok
    assert any("efficacy" in v for v in violations)


def test_claim_guard_prohibits_needle_depth_guidance():
    """Safety Invariant: Needle insertion depth recommendations are strictly forbidden."""
    statement = "We recommend needle insertion depth of 25mm into the peroneal tissue."
    ok, violations = ScientificClaimValidator.audit_statement(statement)
    assert not ok
    assert any("clinical_depth_guidance_allowed: False" in v for v in violations)


def test_claim_guard_allows_legitimate_engineering_statements():
    """Legitimate technical and anatomical boundary statements must pass without error."""
    statement = (
        "The CT landmark evaluation demonstrates anatomical surface correspondence "
        "relative to standard osseous landmarks, without establishing clinical therapeutic efficacy."
    )
    ok, violations = ScientificClaimValidator.audit_statement(statement)
    assert ok
    assert len(violations) == 0


# --- Gate B406: External Reviewer Workflow Tests ---

def test_reviewer_workflow_developer_exclusion():
    """Independence Invariant: Developers or internal AI agents cannot act as independent reviewers."""
    engine = IndependentReviewEngine()
    fake_reviewer = ReviewerIdentity(
        reviewer_id="AGENT-DEV-001",
        external_institution="Internal Dev Team",
        full_name="Claude Agent",
        role=ReviewerRole.EXTERNAL_BIOSTATISTICIAN,
        credential_number="DEV-1234",
        is_developer_or_internal_agent=True,  # Disqualified
    )
    with pytest.raises(ReviewerImpersonationError) as exc_info:
        engine.initiate_review(
            fake_reviewer, "a" * 64, "No conflict", False
        )
    assert "Independence violation" in str(exc_info.value)
    assert "strictly barred" in str(exc_info.value)


def test_reviewer_workflow_coi_blocking():
    """Independence Invariant: A reviewer with declared conflict cannot execute independent review."""
    engine = IndependentReviewEngine()
    reviewer = ReviewerIdentity(
        reviewer_id="BIO-001",
        external_institution="Independent University",
        full_name="Dr. External Stat",
        role=ReviewerRole.EXTERNAL_BIOSTATISTICIAN,
        credential_number="STAT-9921",
        is_developer_or_internal_agent=False,
    )
    with pytest.raises(ReviewerCOIUnresolvedError) as exc_info:
        engine.initiate_review(
            reviewer, "a" * 64, "Consultant for imaging vendor", has_conflict=True
        )
    assert "conflict of interest" in str(exc_info.value)


def test_reviewer_workflow_valid_review_submission():
    """Legitimate external reviewer can submit sealed review dossier."""
    engine = IndependentReviewEngine()
    reviewer = ReviewerIdentity(
        reviewer_id="RAD-001",
        external_institution="Metropolitan Academic Hospital",
        full_name="Dr. Jane Radiologist",
        role=ReviewerRole.INDEPENDENT_RADIOLOGIST,
        credential_number="MD-RAD-4412",
        is_developer_or_internal_agent=False,
    )
    items = [
        ReviewDossierItem("CH-01", "DICOM De-identification", True, "All 18 Safe Harbor tags suppressed.", "h" * 64),
        ReviewDossierItem("CH-02", "Osseous Landmark Accuracy", True, "Nasion and inion coordinates conform to standard.", "h" * 64),
    ]
    rec = engine.submit_review(
        review_id="REV-RAD-001-TEST",
        reviewer=reviewer,
        dataset_or_package_hash="b" * 64,
        coi_statement="I certify zero financial, commercial, or academic conflict of interest.",
        has_conflict=False,
        checklist_items=items,
        verdict=ReviewVerdict.APPROVED,
        justification="Engineering sandbox satisfies radiological coordinate verification requirements.",
    )
    assert rec.record_sha256 != ""
    assert len(rec.record_sha256) == 64
    assert engine.get_review("REV-RAD-001-TEST") is not None


# --- Gate B402: Statistical Power and Sample Allocation Tests ---

def test_statistical_power_cluster_design_effect():
    """Validates cluster design effect inflation formula DE = 1 + (m - 1) * rho."""
    spec = CohortSampleSpec(
        cohort_id="COHORT_A",
        target_region="Head & Neck",
        num_subjects=30,
        landmarks_per_subject=12,
        intra_subject_icc=0.35,
        calibration_ratio=0.50,
        tuning_ratio=0.25,
        holdout_ratio=0.25,
    )
    metrics = spec.calculate_metrics()
    expected_de = 1.0 + (12 - 1) * 0.35  # 1 + 3.85 = 4.85
    assert abs(metrics["design_effect"] - expected_de) < 0.001
    assert metrics["total_observations"] == 360
    # Holdout: 25% of 30 = 8 subjects (after int rounding and residual adjustment: 30 - 15 - 8 = 7)
    holdout_subjs = metrics["partitions"]["holdout"]["subjects"]
    assert holdout_subjs in (7, 8)
    assert metrics["partitions"]["holdout"]["observations"] == holdout_subjs * 12


def test_statistical_power_evaluation_evaluator():
    """Validates full protocol evaluation across Cohorts A, B, C."""
    evaluator = StatisticalProtocolEvaluator()
    res = evaluator.evaluate_protocol(evaluator.BASELINE_COHORTS)
    
    assert len(res["cohort_analyses"]) == 3
    agg = res["aggregate"]
    assert agg["total_patients"] == 85
    assert agg["total_observations"] == 30 * 12 + 25 * 10 + 30 * 13  # 360 + 250 + 390 = 1000
    assert agg["total_holdout_patients"] >= 20
    assert agg["aggregate_holdout_power"] > 0.95
