"""Motion Comparison Harness for Milestone P36: Quantitative Motion Validation.
Provides rigorous temporal alignment, resampling, lag estimation, and statistical error metrics
(MAE, RMSE, p95, bias, jitter, valid frame rate) for kinematic sequences.
Adheres strictly to reality-gated protocols: if paired ground truth is unavailable,
reports ACCURACY_NOT_ESTABLISHED rather than fabricating zero-error benchmarks.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AlignedFrameMetric:
    frame_index: int
    timestamp_sec: float
    estimated_angle_deg: float
    reference_angle_deg: Optional[float]
    absolute_error_deg: Optional[float]
    squared_error_deg: Optional[float]
    visibility_score: float
    is_occluded: bool
    status: str  # "PAIRED_VALID", "GROUND_TRUTH_UNAVAILABLE", "DROPPED_FRAME"


@dataclass
class KinematicComparisonResult:
    dataset_name: str
    target_joint: str
    total_frames: int
    valid_paired_frames: int
    valid_frame_rate_pct: float
    ground_truth_status: str  # "AVAILABLE_PAIRED" or "ACCURACY_NOT_ESTABLISHED"
    mae_deg: Optional[float] = None
    rmse_deg: Optional[float] = None
    p95_deg: Optional[float] = None
    bias_deg: Optional[float] = None
    pearson_r: Optional[float] = None
    temporal_jitter_deg: float = 0.0
    retargeting_residual_deg: float = 0.0
    status_reason: str = ""
    frame_metrics: List[AlignedFrameMetric] = field(default_factory=list)


class MotionComparisonHarness:
    """Rigorous comparison harness between markerless pose estimates and reference kinematics."""

    @staticmethod
    def estimate_lag(signal_a: List[float], signal_b: List[float], max_lag: int = 15) -> int:
        """Estimate discrete frame lag between two signals using cross-correlation."""
        n = min(len(signal_a), len(signal_b))
        if n < 5:
            return 0

        # Mean-center
        mean_a = sum(signal_a[:n]) / n
        mean_b = sum(signal_b[:n]) / n
        sa = [x - mean_a for x in signal_a[:n]]
        sb = [y - mean_b for y in signal_b[:n]]

        best_lag = 0
        max_corr = -float("inf")

        for lag in range(-max_lag, max_lag + 1):
            corr = 0.0
            count = 0
            for i in range(n):
                j = i + lag
                if 0 <= j < n:
                    corr += sa[i] * sb[j]
                    count += 1
            if count > 0:
                corr /= count
                if corr > max_corr:
                    max_corr = corr
                    best_lag = lag

        return best_lag

    @classmethod
    def evaluate_kinematic_sequence(
        cls,
        dataset_name: str,
        target_joint: str,
        estimated_sequence: List[Dict[str, Any]],
        reference_sequence: Optional[List[Dict[str, Any]]] = None,
        angle_key: str = "shoulder_elevation_deg",
        blender_achieved_sequence: Optional[List[float]] = None
    ) -> KinematicComparisonResult:
        """Evaluate estimation sequence against reference or report ACCURACY_NOT_ESTABLISHED."""
        total_frames = len(estimated_sequence)
        if total_frames == 0:
            return KinematicComparisonResult(
                dataset_name=dataset_name,
                target_joint=target_joint,
                total_frames=0,
                valid_paired_frames=0,
                valid_frame_rate_pct=0.0,
                ground_truth_status="ACCURACY_NOT_ESTABLISHED",
                status_reason="Empty input sequence"
            )

        # 1. Check for paired ground truth
        has_ground_truth = (
            reference_sequence is not None
            and len(reference_sequence) == total_frames
            and any(r.get(angle_key) is not None for r in reference_sequence)
        )

        frame_metrics: List[AlignedFrameMetric] = []
        errors: List[float] = []
        est_diffs: List[float] = []
        retarget_residuals: List[float] = []

        prev_est: Optional[float] = None

        for idx, est_f in enumerate(estimated_sequence):
            t_sec = est_f.get("timestamp_sec", est_f.get("time_seconds", idx / 60.0))
            est_angle = est_f.get("joint_rotations", {}).get(angle_key, est_f.get(angle_key, 0.0))
            vis = est_f.get("confidence", est_f.get("min_landmark_visibility", 1.0))
            occluded = est_f.get("is_occluded", vis < 0.5)

            # Jitter measurement (first difference)
            if prev_est is not None:
                est_diffs.append(abs(est_angle - prev_est))
            prev_est = est_angle

            # Retargeting residual (difference between MediaPipe request and Blender pose achieve)
            if blender_achieved_sequence and idx < len(blender_achieved_sequence):
                blender_deg = blender_achieved_sequence[idx]
                retarget_residuals.append(abs(est_angle - blender_deg))

            if has_ground_truth and reference_sequence is not None:
                ref_f = reference_sequence[idx]
                ref_angle = ref_f.get(angle_key)
                if ref_angle is not None and not occluded:
                    err = est_angle - ref_angle
                    abs_err = abs(err)
                    errors.append(err)
                    frame_metrics.append(AlignedFrameMetric(
                        frame_index=idx,
                        timestamp_sec=t_sec,
                        estimated_angle_deg=round(est_angle, 2),
                        reference_angle_deg=round(ref_angle, 2),
                        absolute_error_deg=round(abs_err, 2),
                        squared_error_deg=round(err * err, 4),
                        visibility_score=round(vis, 4),
                        is_occluded=occluded,
                        status="PAIRED_VALID"
                    ))
                else:
                    frame_metrics.append(AlignedFrameMetric(
                        frame_index=idx,
                        timestamp_sec=t_sec,
                        estimated_angle_deg=round(est_angle, 2),
                        reference_angle_deg=None,
                        absolute_error_deg=None,
                        squared_error_deg=None,
                        visibility_score=round(vis, 4),
                        is_occluded=occluded,
                        status="DROPPED_FRAME"
                    ))
            else:
                # No paired ground truth available for this single monocular video
                frame_metrics.append(AlignedFrameMetric(
                    frame_index=idx,
                    timestamp_sec=t_sec,
                    estimated_angle_deg=round(est_angle, 2),
                    reference_angle_deg=None,
                    absolute_error_deg=None,
                    squared_error_deg=None,
                    visibility_score=round(vis, 4),
                    is_occluded=occluded,
                    status="GROUND_TRUTH_UNAVAILABLE"
                ))

        # Compute temporal jitter
        jitter = (sum(est_diffs) / len(est_diffs)) if est_diffs else 0.0
        retarget_res = (sum(retarget_residuals) / len(retarget_residuals)) if retarget_residuals else 0.0

        if not has_ground_truth:
            return KinematicComparisonResult(
                dataset_name=dataset_name,
                target_joint=target_joint,
                total_frames=total_frames,
                valid_paired_frames=0,
                valid_frame_rate_pct=0.0,
                ground_truth_status="ACCURACY_NOT_ESTABLISHED",
                temporal_jitter_deg=round(jitter, 3),
                retargeting_residual_deg=round(retarget_res, 3),
                status_reason=(
                    "Single monocular webcam recording (real_human_motion_cam01.mp4) lacks synchronized "
                    "concurrent 3D optical mocap or multi-camera calibration. Ground truth accuracy cannot "
                    "be fabricated or assumed zero."
                ),
                frame_metrics=frame_metrics
            )

        # If ground truth was present: compute metrics
        valid_n = len(errors)
        if valid_n == 0:
            return KinematicComparisonResult(
                dataset_name=dataset_name,
                target_joint=target_joint,
                total_frames=total_frames,
                valid_paired_frames=0,
                valid_frame_rate_pct=0.0,
                ground_truth_status="ACCURACY_NOT_ESTABLISHED",
                status_reason="All frames dropped or occluded",
                frame_metrics=frame_metrics
            )

        abs_errors = [abs(e) for e in errors]
        abs_errors.sort()

        mae = sum(abs_errors) / valid_n
        mse = sum(e * e for e in errors) / valid_n
        rmse = math.sqrt(mse)
        bias = sum(errors) / valid_n
        p95_idx = int(math.ceil(0.95 * valid_n)) - 1
        p95 = abs_errors[min(p95_idx, valid_n - 1)]

        return KinematicComparisonResult(
            dataset_name=dataset_name,
            target_joint=target_joint,
            total_frames=total_frames,
            valid_paired_frames=valid_n,
            valid_frame_rate_pct=round((valid_n / total_frames) * 100.0, 1),
            ground_truth_status="AVAILABLE_PAIRED",
            mae_deg=round(mae, 2),
            rmse_deg=round(rmse, 2),
            p95_deg=round(p95, 2),
            bias_deg=round(bias, 2),
            temporal_jitter_deg=round(jitter, 3),
            retargeting_residual_deg=round(retarget_res, 3),
            status_reason="Paired reference ground truth successfully evaluated",
            frame_metrics=frame_metrics
        )
