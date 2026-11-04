"""Test suite for Milestone P24: MediaPipe Pose Import, Observability Matrix & Kinematics Reconstruction."""
import math
import pytest

from tools.pose_sidecar.pose_estimator import (
    PoseObservationPipeline,
    OBSERVABILITY_MATRIX,
    MEDIAPIPE_LANDMARKS
)
from tools.blender_anatomy_studio.contracts import validate_contract

class TestP24ObservabilityAndProvenance:
    def test_observability_matrix_invariants(self):
        assert OBSERVABILITY_MATRIX["forearm_pronation_supination"]["status"] == "UNOBSERVABLE"
        assert OBSERVABILITY_MATRIX["monocular_depth"]["status"] == "ESTIMATED_UNCERTAIN"
        assert OBSERVABILITY_MATRIX["elbow_flexion"]["status"] == "OBSERVABLE"

    def test_mediapipe_landmark_mapping(self):
        assert MEDIAPIPE_LANDMARKS[12] == "RIGHT_SHOULDER"
        assert MEDIAPIPE_LANDMARKS[14] == "RIGHT_ELBOW"
        assert MEDIAPIPE_LANDMARKS[16] == "RIGHT_WRIST"


class TestP24SyntheticDeterminism:
    def test_synthetic_elbow_flexion_angles(self):
        pipe = PoseObservationPipeline()

        # Pose 1: Fully extended straight arm (Shoulder: 0, 1.42, 0; Elbow: 0, 1.12, 0; Wrist: 0, 0.86, 0)
        sh = (0.0, 1.42, 0.0)
        el = (0.0, 1.12, 0.0)
        wr_straight = (0.0, 0.86, 0.0)
        deg_0 = pipe.compute_elbow_flexion_from_landmarks(sh, el, wr_straight)
        assert abs(deg_0 - 0.0) < 0.1, f"Expected 0.0 deg, got {deg_0}"

        # Pose 2: 90 deg flexion (Wrist bent anteriorly along Z: 0.0, 1.12, 0.26)
        wr_90 = (0.0, 1.12, 0.26)
        deg_90 = pipe.compute_elbow_flexion_from_landmarks(sh, el, wr_90)
        assert abs(deg_90 - 90.0) < 0.1, f"Expected 90.0 deg, got {deg_90}"

        # Pose 3: 45 deg flexion
        # Forearm direction: down by cos(45), forward by sin(45)
        l2 = 0.26
        wr_45 = (0.0, 1.12 - l2 * math.cos(math.radians(45)), l2 * math.sin(math.radians(45)))
        deg_45 = pipe.compute_elbow_flexion_from_landmarks(sh, el, wr_45)
        assert abs(deg_45 - 45.0) < 0.1, f"Expected 45.0 deg, got {deg_45}"


class TestP24OcclusionAndFailClosed:
    def test_occluded_frames_fail_closed(self):
        pipe = PoseObservationPipeline()
        dummy_lms = []
        for i in range(33):
            # Normal visibility = 0.95
            dummy_lms.append({"id": i, "x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.95, "presence": 0.95})

        # Set right elbow (14) to occluded (visibility = 0.15) for 15 frames test case
        dummy_lms[14]["visibility"] = 0.15

        obs = pipe.create_observation_frame(
            frame_id=42,
            timestamp=1.40,
            source_video_hash="test_video_hash_abc123",
            landmarks_33=dummy_lms
        )

        assert "RIGHT_ARM_OCCLUSION_DETECTED" in obs["quality_flags"]

        # Reconstruction MUST reject occluded frame and NOT invent fake angles
        res = pipe.reconstruct_arm_kinematics(obs)
        assert res["status"] == "REJECTED_DUE_TO_OCCLUSION"
        assert res["elbow_flexion_deg"] is None
        assert res["confidence"] == 0.0
        assert "refusing fake pose" in res["reason"].lower()

    def test_clean_frame_reconstruction_passes_and_clamps(self):
        pipe = PoseObservationPipeline()
        clean_lms = []
        for i in range(33):
            clean_lms.append({"id": i, "x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.98, "presence": 0.98})

        # Provide valid 60 deg flexion geometry in world coordinates
        clean_lms[12].update({"world_x": 0.0, "world_y": 1.42, "world_z": 0.0}) # Shoulder
        clean_lms[14].update({"world_x": 0.0, "world_y": 1.12, "world_z": 0.0}) # Elbow
        l2 = 0.26
        clean_lms[16].update({
            "world_x": 0.0,
            "world_y": 1.12 - l2 * math.cos(math.radians(60)),
            "world_z": l2 * math.sin(math.radians(60))
        }) # Wrist

        obs = pipe.create_observation_frame(
            frame_id=1,
            timestamp=0.033,
            source_video_hash="clean_trial_vid",
            landmarks_33=clean_lms
        )

        res = pipe.reconstruct_arm_kinematics(obs)
        assert res["status"] == "RECONSTRUCTED"
        assert abs(res["raw_elbow_flexion_deg"] - 60.0) < 0.2
        assert res["is_within_anatomical_bounds"] is True
        assert res["confidence"] >= 0.95
