"""P30 Motion Accuracy, Constraints and Validation Runner.
Processes real motion sequence, computes kinematics metrics, tests negative scenarios,
and generates schema-compliant validation reports and audit documentation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.blender_anatomy_studio.motion_validation_engine import (
    MotionValidationEngine,
    ObservationState,
)
from tools.blender_anatomy_studio.contracts import validate_contract
P28_MOTION_PATH = REPO_ROOT / "1docs" / "audits" / "P28" / "evidence" / "p28_real_motion_sequence.json"
P30_EVIDENCE_DIR = REPO_ROOT / "1docs" / "audits" / "P30" / "evidence"
P30_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def run_p30():
    print("=" * 60)
    print("STARTING P30 MOTION ACCURACY, CONSTRAINTS & UNCERTAINTY RUNNER")
    print("=" * 60)

    assert P28_MOTION_PATH.exists(), f"Missing motion sequence: {P28_MOTION_PATH}"
    with open(P28_MOTION_PATH, "r", encoding="utf-8") as f:
        motion_seq = json.load(f)

    engine = MotionValidationEngine(fps=motion_seq.get("fps", 60.0))

    # 1. Validate real motion sequence
    val_res = engine.validate_motion_sequence(motion_seq)
    print(f"Validation Result: Valid={val_res['valid']}")
    print(f"  Total Frames: {val_res['total_frames']}")
    print(f"  Rejection Rate: {val_res['rejection_rate'] * 100:.2f}%")
    print(f"  Mean Angular Velocity: {val_res['mean_angular_velocity_deg_s']} deg/s")
    print(f"  Max Angular Velocity: {val_res['max_angular_velocity_deg_s']} deg/s")
    print(f"  Unreasonable Jumps: {val_res['unreasonable_jumps_count']}")

    # 2. Test Observation Taxonomy Classification
    obs1 = engine.classify_joint_observation(
        confidence=0.98,
        is_occluded=False,
        is_unobservable_dof=False,
        is_clamped_by_constraint=False,
        angular_velocity_deg_per_sec=45.0
    )
    assert obs1 == ObservationState.OBSERVED, f"Expected OBSERVED, got {obs1}"

    obs_clamped = engine.classify_joint_observation(
        confidence=0.95,
        is_occluded=False,
        is_unobservable_dof=False,
        is_clamped_by_constraint=True,
        angular_velocity_deg_per_sec=30.0
    )
    assert obs_clamped == ObservationState.CONSTRAINED, f"Expected CONSTRAINED, got {obs_clamped}"

    obs_unobs = engine.classify_joint_observation(
        confidence=0.90,
        is_occluded=False,
        is_unobservable_dof=True,
        is_clamped_by_constraint=False,
        angular_velocity_deg_per_sec=0.0
    )
    assert obs_unobs == ObservationState.UNOBSERVABLE, f"Expected UNOBSERVABLE, got {obs_unobs}"

    obs_rejected = engine.classify_joint_observation(
        confidence=0.20,
        is_occluded=True,
        is_unobservable_dof=False,
        is_clamped_by_constraint=False,
        angular_velocity_deg_per_sec=0.0
    )
    assert obs_rejected == ObservationState.REJECTED, f"Expected REJECTED, got {obs_rejected}"

    print("Tested 4 observation states successfully: OBSERVED, CONSTRAINED, UNOBSERVABLE, REJECTED")

    # 3. Test Negative Case: Deliberate Jump Detection
    bad_motion = json.loads(json.dumps(motion_seq))
    # Inject a 120-degree teleport jump at frame 15
    bad_motion["frames"][15]["joint_rotations"]["right_elbow_flexion_deg"] += 120.0
    bad_val = engine.validate_motion_sequence(bad_motion)
    print(f"Negative Jump Test: Detected {bad_val['unreasonable_jumps_count']} jumps (Valid={bad_val['valid']})")
    assert bad_val["unreasonable_jumps_count"] >= 1, "Failed to detect deliberate 120 deg jump!"
    assert not bad_val["valid"], "Corrupted motion must fail validation!"

    # 4. Generate Formal Validation Report
    report = engine.generate_validation_report(
        report_id="P30-VAL-REPORT-001",
        milestone="P30",
        motion_sequence=motion_seq,
        ground_truth_series=None  # Explicitly ACCURACY_NOT_ESTABLISHED when no optical GT available
    )

    out_report_path = P30_EVIDENCE_DIR / "p30_validation_report.json"
    with open(out_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Generated Validation Report: {out_report_path}")
    print(f"Report Status: {report['status']} | Gates: {report['gates']}")
    print("=" * 60)
    print("P30 MOTION ACCURACY & VALIDATION COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    run_p30()
