"""Test suite for Milestone P28: Real Video MediaPipe Inference, Constrained IK & Mesh-Bone Binding."""
import hashlib
import json
import math
from pathlib import Path
import pytest

from tools.blender_anatomy_studio.contracts import validate_contract
from tools.blender_anatomy_studio.motion_bank import (
    BoneLengthInvarianceEvaluator,
    JointConstraintRegistry,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / "1docs" / "audits" / "P28" / "evidence"
SCREENSHOT_DIR = REPO_ROOT / "1docs" / "audits" / "P28" / "screenshots"
SAMPLES_DIR = REPO_ROOT / "tools" / "pose_sidecar" / "samples"
MODELS_DIR = REPO_ROOT / "tools" / "pose_sidecar" / "models"


class TestP28RealVideoAndModelIntegrity:
    def test_real_video_sample_exists_and_checksum(self):
        vid_path = SAMPLES_DIR / "real_human_motion_cam01.mp4"
        assert vid_path.exists(), "Sample video file must exist"
        assert vid_path.stat().st_size > 300_000, "Sample video size must exceed 300 KB"
        h = hashlib.sha256(vid_path.read_bytes()).hexdigest()
        assert h == "cf4f2816c86bea4bfbea255333d8626ff32a3ecabdab8b0fb147cea9167fde3a"

    def test_mediapipe_task_model_exists_and_checksum(self):
        model_path = MODELS_DIR / "pose_landmarker_full.task"
        assert model_path.exists(), "MediaPipe task model must exist"
        assert model_path.stat().st_size > 9_000_000, "Model file size must exceed 9 MB"
        h = hashlib.sha256(model_path.read_bytes()).hexdigest()
        assert h == "4eaa5eb7a98365221087693fcc286334cf0858e2eb6e15b506aa4a7ecdcec4ad"


class TestP28MotionSequenceContractAndConstraints:
    @pytest.fixture
    def motion_data(self):
        json_path = EVIDENCE_DIR / "p28_real_motion_sequence.json"
        assert json_path.exists(), "p28_real_motion_sequence.json must exist"
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_motion_sequence_schema_validation(self, motion_data):
        ok, err = validate_contract(motion_data, "motion_sequence")
        assert ok, f"MotionSequence failed schema validation: {err}"
        assert motion_data["source_type"] == "MEDIAPIPE_ESTIMATED"
        assert len(motion_data["frames"]) == 100

    def test_joint_angles_within_kapandji_and_seth_bounds(self, motion_data):
        for f in motion_data["frames"]:
            rot = f["joint_rotations"]
            el = rot["right_elbow_flexion_deg"]
            sh = rot["right_shoulder_elevation_deg"]

            # Kapandji 2007 limits for active elbow flexion
            assert 0.0 <= el <= 145.0, f"Elbow angle {el} exceeds Kapandji limits [0, 145]"
            # Seth 2016 limits for shoulder elevation
            assert 0.0 <= sh <= 180.0, f"Shoulder angle {sh} exceeds Seth limits [0, 180]"

    def test_unobservable_dofs_flagged(self, motion_data):
        unobs = motion_data["quality_metadata"]["unobservable_dofs"]
        assert "forearm_pronation_supination" in unobs


class TestP28BlenderEvidenceAndPersistence:
    def test_saved_blend_file_exists(self):
        blend_path = EVIDENCE_DIR / "p28_real_video_motion.blend"
        assert blend_path.exists(), "p28_real_video_motion.blend must exist"
        assert blend_path.stat().st_size > 2_000_000, "Blend file size must exceed 2 MB"

    def test_rendered_screenshots_exist(self):
        s1 = SCREENSHOT_DIR / "01_real_mediapipe_frame_000.png"
        s2 = SCREENSHOT_DIR / "02_blender_real_motion_frame_001.png"
        s3 = SCREENSHOT_DIR / "03_blender_real_motion_frame_050.png"
        assert s1.exists(), "01_real_mediapipe_frame_000.png missing"
        assert s2.exists(), "02_blender_real_motion_frame_001.png missing"
        assert s3.exists(), "03_blender_real_motion_frame_050.png missing"
