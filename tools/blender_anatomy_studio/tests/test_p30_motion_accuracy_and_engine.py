"""Test suite for Milestone P30: Motion Accuracy, Constraints and Validation Engine."""
import json
import pytest
from pathlib import Path

from tools.blender_anatomy_studio.motion_validation_engine import (
    MotionValidationEngine,
    ObservationState,
)
from tools.blender_anatomy_studio.contracts import validate_contract

REPO_ROOT = Path(__file__).resolve().parents[3]
P28_MOTION_PATH = REPO_ROOT / "1docs" / "audits" / "P28" / "evidence" / "p28_real_motion_sequence.json"
P30_REPORT_PATH = REPO_ROOT / "1docs" / "audits" / "P30" / "evidence" / "p30_validation_report.json"


class TestP30ObservationTaxonomyAndEngine:
    def test_observation_state_classification(self):
        engine = MotionValidationEngine()

        # Clean observed
        s1 = engine.classify_joint_observation(0.95, False, False, False, 50.0)
        assert s1 == ObservationState.OBSERVED

        # Constrained
        s2 = engine.classify_joint_observation(0.90, False, False, True, 50.0)
        assert s2 == ObservationState.CONSTRAINED

        # Unobservable
        s3 = engine.classify_joint_observation(0.90, False, True, False, 0.0)
        assert s3 == ObservationState.UNOBSERVABLE

        # Occluded / low confidence rejected
        s4 = engine.classify_joint_observation(0.30, True, False, False, 0.0)
        assert s4 == ObservationState.REJECTED

        # Excessive velocity rejected (> 720 deg/s)
        s5 = engine.classify_joint_observation(0.95, False, False, False, 900.0)
        assert s5 == ObservationState.REJECTED

    def test_validate_clean_motion_sequence(self):
        assert P28_MOTION_PATH.exists()
        with open(P28_MOTION_PATH, "r", encoding="utf-8") as f:
            motion = json.load(f)

        engine = MotionValidationEngine(fps=motion["fps"])
        res = engine.validate_motion_sequence(motion)
        assert res["valid"] is True
        assert res["total_frames"] == 100
        assert res["unreasonable_jumps_count"] == 0

    def test_detect_corrupted_motion_jump(self):
        assert P28_MOTION_PATH.exists()
        with open(P28_MOTION_PATH, "r", encoding="utf-8") as f:
            motion = json.load(f)

        # Corrupt frame 20 with 90 degree teleport
        motion["frames"][20]["joint_rotations"]["right_elbow_flexion_deg"] += 90.0
        engine = MotionValidationEngine(fps=motion["fps"])
        res = engine.validate_motion_sequence(motion)
        assert res["valid"] is False
        assert res["unreasonable_jumps_count"] >= 1

    def test_accuracy_not_established_when_no_ground_truth(self):
        res = MotionValidationEngine.evaluate_reference_accuracy([10.0, 20.0], [])
        assert res["status"] == "ACCURACY_NOT_ESTABLISHED"
        assert "No ground truth" in res["notes"]

    def test_accuracy_metrics_computed_with_reference(self):
        est = [10.0, 20.0, 30.0]
        gt = [12.0, 19.0, 31.0] # errors: 2, 1, 1 -> MAE = 1.333
        res = MotionValidationEngine.evaluate_reference_accuracy(est, gt)
        assert res["status"] == "EVALUATED_AGAINST_REFERENCE"
        assert abs(res["mae_deg"] - 1.333) < 0.01
        assert res["max_error_deg"] == 2.0


class TestP30ValidationReportContract:
    def test_validation_report_schema_and_artifacts(self):
        assert P30_REPORT_PATH.exists()
        with open(P30_REPORT_PATH, "r", encoding="utf-8") as f:
            rep = json.load(f)

        ok, err = validate_contract(rep, "validation_report")
        assert ok, f"ValidationReport failed schema: {err}"
        assert rep["milestone"] == "P30"
        assert rep["gates"]["G1_Functional"] == "PASS"
        assert rep["gates"]["G2_Data_Integrity"] == "PASS"
        assert rep["gates"]["G3_Domain_Validity"] == "BLOCKED"
        assert rep["gates"]["G4_Independent_Acceptance"] == "BLOCKED"
