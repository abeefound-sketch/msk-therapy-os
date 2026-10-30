"""Tests for P10.5 Institutional Pilot Activation & Acquisition Readiness.

Validates:
- Gate P502: Statistical Study Design & Precision Analysis Engine
- Gate P504: Institutional Partner Onboarding System
- Gate P505: Real-World Research Data Acquisition State Machine
- Gate P506: Independent Annotation Quality Control & Adjudication Engine
"""

import datetime
import pytest

from msk_therapy_os.annotation_qc import (
    AnnotationQCStatus,
    AnnotationQualityControlEngine,
    RawLandmarkCoordinate,
)
from msk_therapy_os.institutional_simulator import SyntheticPromotionBlockedError
from msk_therapy_os.partner_onboarding import (
    InstitutionalOnboardingManager,
    OnboardingStatus,
)
from msk_therapy_os.real_world_intake_controller import (
    DatasetCustodyState,
    RealWorldIntakeController,
)
from msk_therapy_os.statistical_design_engine import (
    CohortDesignSpec,
    PlanningScenarioType,
    StatisticalStudyDesignEngine,
)


# --- Gate P502: Statistical Design Engine Tests ---

def test_statistical_design_three_planning_scenarios():
    """Validates reproducible calculations across 3 planning scenarios."""
    scenarios = [
        PlanningScenarioType.MINIMUM_FEASIBILITY_PILOT,
        PlanningScenarioType.PRIMARY_ANATOMICAL_ACCURACY_STUDY,
        PlanningScenarioType.INDEPENDENT_MULTI_SITE_VALIDATION,
    ]
    for s_type in scenarios:
        res = StatisticalStudyDesignEngine.run_scenario(s_type)
        assert res.total_subjects > 0
        assert res.total_observations > 0
        assert res.total_holdout_subjects > 0
        assert res.aggregate_holdout_effective_n > 0.0
        assert 0.0 <= res.aggregate_holdout_power <= 1.0
        assert len(res.cohort_details) == 3


def test_statistical_design_sensitivity_grid():
    """Validates multi-parameter sensitivity grid over variable ICCs and SDs."""
    grid = StatisticalStudyDesignEngine.run_sensitivity_grid(
        num_subjects=30, landmarks=12,
        icc_values=[0.20, 0.40], sd_values=[1.2, 1.6]
    )
    assert len(grid) == 4
    for pt in grid:
        assert pt["design_effect"] > 1.0
        assert pt["holdout_effective_n"] > 0
        assert pt["holdout_statistical_power"] > 0.50
        assert pt["mean_ci_half_width_mm"] > 0.0


# --- Gate P504: Institutional Partner Onboarding Tests ---

def test_partner_onboarding_lifecycle():
    mgr = InstitutionalOnboardingManager(":memory:")
    prof = mgr.register_prospective_institution(
        institution_id="INST-METRO-01",
        legal_name="Metropolitan University Hospital",
        country="US",
        primary_pi_name="Dr. Sarah Chen, MD",
        primary_pi_email="schen@metrou.edu",
        radiology_lead_name="Dr. Michael Ray, MD",
        data_custodian_id="CUST-METRO-01",
    )
    assert prof.status == OnboardingStatus.PARTNER_CONTACT_PENDING
    assert len(prof.blockers) > 0

    # Advance to PROTOCOL_UNDER_REVIEW
    updated = mgr.update_milestone_status(
        "INST-METRO-01", OnboardingStatus.PROTOCOL_UNDER_REVIEW
    )
    assert updated.status == OnboardingStatus.PROTOCOL_UNDER_REVIEW

    # Attempting to authorize intake WITHOUT executed DUA and approved IRB must raise ValueError
    with pytest.raises(ValueError) as exc_info:
        mgr.update_milestone_status(
            "INST-METRO-01", OnboardingStatus.DATASET_INTAKE_AUTHORIZED
        )
    assert "Bilateral DUA is not executed" in str(exc_info.value)

    # Valid authorization with active DUA and IRB
    auth_prof = mgr.update_milestone_status(
        "INST-METRO-01",
        OnboardingStatus.DATASET_INTAKE_AUTHORIZED,
        dua_status="EXECUTED_BILATERAL_DUA",
        irb_status="APPROVED_BY_IRB",
        irb_protocol_number="IRB-METRO-2026-99",
        authorization_expiry_iso="2027-10-30",
        resolved_blockers=["DUA/MTA agreement not executed with hospital legal counsel."]
    )
    assert auth_prof.status == OnboardingStatus.DATASET_INTAKE_AUTHORIZED
    assert auth_prof.irb_protocol_number == "IRB-METRO-2026-99"

    # Dashboard check
    dash = mgr.get_offline_onboarding_dashboard()
    assert dash["total_candidate_institutions"] == 1
    assert dash["scientific_gate_g14"] == "BLOCKED_EXTERNAL_DATA"


# --- Gate P505: Real-World Intake Controller Tests ---

def test_real_world_intake_custody_lifecycle():
    controller = RealWorldIntakeController()
    today = datetime.date.today()
    exp_date = (today + datetime.timedelta(days=365)).isoformat()

    rec = controller.register_incoming_dataset(
        dataset_id="DS-REAL-001",
        institution_id="INST-METRO-01",
        cohort_id="COHORT_A_ABDOMEN",
        is_synthetic=False,
        dua_id="DUA-METRO-01",
        irb_number="IRB-9912",
        irb_expiration_iso=exp_date,
        deid_attestation_hash="d" * 64,
        pixel_phi_screened=True,
        raw_manifest_json='{"series": []}',
    )
    assert rec.current_state == DatasetCustodyState.EXTERNAL_UNVERIFIED

    # Transition to quarantine
    controller.transition_to_quarantine("DS-REAL-001", "OP-01")
    assert rec.current_state == DatasetCustodyState.EXTERNAL_QUARANTINED

    # Dual-admin authorization
    controller.authorize_quarantined_dataset("DS-REAL-001", "ADMIN-A", "ADMIN-B")
    assert rec.current_state == DatasetCustodyState.EXTERNAL_AUTHORIZED

    # Attach annotations
    controller.attach_independent_annotations("DS-REAL-001", "ADJ-01", "a" * 64)
    assert rec.current_state == DatasetCustodyState.INDEPENDENTLY_ANNOTATED

    # Lock holdout
    controller.lock_holdout_partition("DS-REAL-001", "OP-01", "h" * 64)
    assert rec.current_state == DatasetCustodyState.HOLDOUT_LOCKED

    # Submit for review
    controller.submit_for_empirical_review("DS-REAL-001", "OFFICER-01")
    assert rec.current_state == DatasetCustodyState.EMPIRICAL_REVIEW_PENDING
    assert len(rec.custody_chain) == 6


def test_real_world_intake_synthetic_promotion_blocked():
    """Guard: Synthetic fixtures cannot be promoted into empirical states."""
    controller = RealWorldIntakeController()
    rec = controller.register_incoming_dataset(
        dataset_id="DS-SYNTH-01",
        institution_id="SIM-INST",
        cohort_id="COHORT_A",
        is_synthetic=True,
        dua_id="DUA-0",
        irb_number="IRB-0",
        irb_expiration_iso="2027-01-01",
        deid_attestation_hash="s" * 64,
        pixel_phi_screened=False,
        raw_manifest_json='{}',
    )
    assert rec.current_state == DatasetCustodyState.SYNTHETIC_FIXTURE

    with pytest.raises(SyntheticPromotionBlockedError):
        controller.transition_to_quarantine("DS-SYNTH-01", "OP-01")


# --- Gate P506: Annotation Quality Control Tests ---

def test_annotation_qc_concordant_midpoint_calculation():
    """Concordant annotations within threshold automatically compute midpoint consensus."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    coord_a = RawLandmarkCoordinate("OBS-01", "Radiologist", (10.0, 20.0, 30.0), now, True)
    coord_b = RawLandmarkCoordinate("OBS-02", "Radiologist", (11.0, 20.0, 30.0), now, True)  # dist = 1.0 mm

    pair = AnnotationQualityControlEngine.process_annotation_pair(
        subject_id="SUBJ-001",
        cohort_id="COHORT_C_CRANIOFACIAL",
        landmark_id="NASION",
        coord_a=coord_a,
        coord_b=coord_b,
        landmark_category="CRANIAL_OSSEOUS",  # Threshold: 3.0 mm
    )
    assert pair.qc_status == AnnotationQCStatus.CONCORDANT_APPROVED
    assert pair.inter_observer_distance_mm == 1.0
    assert pair.final_consensus_lps_mm == (10.5, 20.0, 30.0)


def test_annotation_qc_discrepancy_and_adjudication():
    """Discrepant annotations trigger adjudication, which independent third reviewer resolves."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    coord_a = RawLandmarkCoordinate("OBS-01", "Radiologist", (10.0, 20.0, 30.0), now, True)
    coord_b = RawLandmarkCoordinate("OBS-02", "Radiologist", (16.0, 20.0, 30.0), now, True)  # dist = 6.0 mm > 3.0 mm

    pair = AnnotationQualityControlEngine.process_annotation_pair(
        subject_id="SUBJ-002",
        cohort_id="COHORT_C_CRANIOFACIAL",
        landmark_id="INION",
        coord_a=coord_a,
        coord_b=coord_b,
        landmark_category="CRANIAL_OSSEOUS",
    )
    assert pair.qc_status == AnnotationQCStatus.DISCREPANCY_FLAGGED
    assert pair.final_consensus_lps_mm is None

    # Third-reviewer adjudication
    resolved_coords = (12.0, 20.0, 30.0)
    adjudicated = AnnotationQualityControlEngine.adjudicate_discrepancy(
        pair=pair,
        adjudicator_id="ADJ-SENIOR-RAD",
        resolved_coords=resolved_coords,
        resolution_method="OBSERVER_A_PREFERRED",
        clinical_rationale="Observer A aligned with superior sagittal suture osseous crest.",
        coi_screened=True,
    )
    assert adjudicated.qc_status == AnnotationQCStatus.ADJUDICATED_RESOLVED
    assert adjudicated.final_consensus_lps_mm == resolved_coords
