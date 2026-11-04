"""Test Suite for Milestone P36: Quantitative Motion Validation.
Validates the MotionComparisonHarness, lag estimation, metric computation,
and enforces reality-gated protocols (ACCURACY_NOT_ESTABLISHED when lacking ground truth).
"""
from __future__ import annotations

import csv
import json
import math
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
P36_CSV = REPO_ROOT / "1docs" / "audits" / "P36" / "P36_FRAME_ALIGNED_METRICS.csv"
P36_JSON = REPO_ROOT / "1docs" / "audits" / "P36" / "evidence" / "p36_validation_results.json"

from tools.blender_anatomy_studio.motion_comparison_harness import (
    MotionComparisonHarness,
    KinematicComparisonResult,
    AlignedFrameMetric,
)


class TestP36MotionValidation:
    """Test suite for Milestone P36 quantitative motion validation."""

    def test_p36_lag_estimation(self):
        """Verify cross-correlation lag estimation on known synthetic time-shifted signals."""
        signal_base = [math.sin(i * 0.2) for i in range(100)]
        lag_ground_truth = 3
        # Signal B is delayed by 3 frames: B[i] = A[i - 3]
        signal_delayed = [0.0] * lag_ground_truth + signal_base[:-lag_ground_truth]

        detected_lag = MotionComparisonHarness.estimate_lag(signal_base, signal_delayed, max_lag=10)
        assert detected_lag == lag_ground_truth, f"Expected lag {lag_ground_truth}, got {detected_lag}"

    def test_p36_metric_calculation_with_known_ground_truth(self):
        """Verify mathematical calculation of MAE, RMSE, p95, and Bias with synthetic paired reference."""
        ref_seq = []
        est_seq = []
        # Constant bias +2.0 deg, no noise
        for i in range(50):
            t = i * 0.02
            true_angle = 30.0 + 10.0 * math.sin(t)
            ref_seq.append({"angle": true_angle, "timestamp_sec": t})
            est_seq.append({"angle": true_angle + 2.0, "timestamp_sec": t, "confidence": 1.0, "is_occluded": False})

        res = MotionComparisonHarness.evaluate_kinematic_sequence(
            dataset_name="Test_Synthetic_Paired",
            target_joint="shoulder",
            estimated_sequence=est_seq,
            reference_sequence=ref_seq,
            angle_key="angle"
        )

        assert res.ground_truth_status == "AVAILABLE_PAIRED"
        assert res.valid_paired_frames == 50
        assert res.valid_frame_rate_pct == 100.0
        assert res.mae_deg == 2.0
        assert res.rmse_deg == 2.0
        assert res.bias_deg == 2.0
        assert res.p95_deg == 2.0

    def test_p36_accuracy_not_established_when_ground_truth_absent(self):
        """Verify that when paired ground truth is omitted, harness reports ACCURACY_NOT_ESTABLISHED."""
        dummy_est = [{"angle": 45.0, "timestamp_sec": 0.0, "confidence": 0.99}]
        res = MotionComparisonHarness.evaluate_kinematic_sequence(
            dataset_name="Unpaired_Test",
            target_joint="shoulder",
            estimated_sequence=dummy_est,
            reference_sequence=None,  # No ground truth
            angle_key="angle"
        )

        assert res.ground_truth_status == "ACCURACY_NOT_ESTABLISHED"
        assert res.mae_deg is None
        assert res.rmse_deg is None
        assert "Ground truth accuracy cannot be fabricated" in res.status_reason

    def test_p36_frame_aligned_metrics_csv_integrity(self):
        """Verify P36_FRAME_ALIGNED_METRICS.csv exists, has 100 frames, and contains valid statuses."""
        assert P36_CSV.exists(), "P36_FRAME_ALIGNED_METRICS.csv missing"
        with open(P36_CSV, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        assert len(reader) == 100, f"Expected 100 frames, got {len(reader)}"
        # Check first and middle rows
        f0 = reader[0]
        f50 = reader[50]

        assert f0["validation_status"] == "GROUND_TRUTH_UNAVAILABLE"
        assert f0["reference_ground_truth_deg"] == "GROUND_TRUTH_NOT_AVAILABLE"
        assert f0["absolute_error_deg"] == "ACCURACY_NOT_ESTABLISHED"

        assert float(f50["estimated_shoulder_elevation_deg"]) > 90.0  # Frame 50 elevation
        assert float(f50["visibility_score"]) > 0.8

    def test_p36_validation_results_json(self):
        """Verify p36_validation_results.json exists and accurately reflects reality-gated evaluation."""
        assert P36_JSON.exists(), "p36_validation_results.json missing"
        data = json.loads(P36_JSON.read_text(encoding="utf-8"))

        assert data["milestone"] == "P36"
        real_eval = data["real_video_evaluation"]
        assert real_eval["total_frames"] == 100
        assert real_eval["ground_truth_status"] == "ACCURACY_NOT_ESTABLISHED"
        assert real_eval["temporal_jitter_deg"] > 0.0

        bench = data["harness_capability_benchmark"]
        assert bench["mae_deg"] == 2.0
        assert bench["rmse_deg"] == 2.26
        assert bench["valid_frame_rate_pct"] == 100.0
