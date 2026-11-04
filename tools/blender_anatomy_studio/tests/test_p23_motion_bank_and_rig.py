"""Test suite for Milestone P23: Motion Bank, Joint Constraint Registry, Arm Rig & Retargeting."""
import math
from pathlib import Path
import pytest

from tools.blender_anatomy_studio.motion_bank import (
    JointConstraintRegistry,
    MotionBank,
    BoneLengthInvarianceEvaluator
)
from tools.blender_anatomy_studio.addon.rig import ArmKinematicsSolver

REPO_ROOT = Path(__file__).resolve().parents[3]

class TestP23JointConstraintRegistry:
    def test_elbow_constraint_metadata_and_limits(self):
        c = JointConstraintRegistry.get_constraint("right_elbow")
        assert c is not None
        assert c["joint_id"] == "right_elbow"
        assert "flexion_extension" in c["kinematic_dofs"]
        assert c["hard_limits"]["min"] == 0.0
        assert c["hard_limits"]["max"] == 145.0
        assert "Kapandji" in c["rom_reference"]
        assert c["review_status"] == "EXPERT_REVIEW_PENDING"

    def test_elbow_angle_validation(self):
        # Within bounds: 45 deg
        ok, clamped, reason = JointConstraintRegistry.validate_angle("right_elbow", 45.0)
        assert ok is True
        assert clamped == 45.0

        # Out of bounds upper: 160 deg -> clamped to 145
        ok, clamped, reason = JointConstraintRegistry.validate_angle("right_elbow", 160.0)
        assert ok is False
        assert clamped == 145.0
        assert "exceeds maximum 145.0°" in reason

        # Out of bounds lower: -10 deg -> clamped to 0
        ok, clamped, reason = JointConstraintRegistry.validate_angle("right_elbow", -10.0)
        assert ok is False
        assert clamped == 0.0
        assert "below minimum 0.0°" in reason

    def test_shoulder_elevation_constraint(self):
        c = JointConstraintRegistry.get_constraint("right_shoulder_elevation")
        assert c is not None
        assert c["hard_limits"]["max"] == 180.0
        assert "Seth" in c["rom_reference"] or "OpenSim" in c["convention"]


class TestP23MotionBankParsers:
    def test_opensim_mot_parser(self):
        mot_path = REPO_ROOT / "msk_therapy_os" / "data" / "biomechanics" / "seth_shoulder_elevation.mot"
        assert mot_path.exists(), f"Missing OpenSim file: {mot_path}"

        seq = MotionBank.parse_opensim_mot(mot_path)
        assert seq["source_type"] == "OPENSIM_MOT"
        assert seq["quality_metadata"]["total_frames"] == 21
        assert len(seq["frames"]) == 21

        # Check first frame (0 deg elevation)
        f0 = seq["frames"][0]
        assert f0["time_seconds"] == 0.0
        assert "arm_elevation" in f0["joint_rotations"]
        assert f0["joint_rotations"]["arm_elevation"] == 0.0

        # Check final frame (120 deg elevation)
        f_last = seq["frames"][-1]
        assert f_last["time_seconds"] == 2.0
        assert f_last["joint_rotations"]["arm_elevation"] == 120.0

    def test_cmu_mocap_amc_parser(self):
        amc_path = REPO_ROOT / "research" / "motion_samples" / "02_01.amc"
        assert amc_path.exists(), f"Missing CMU sample: {amc_path}"

        seq = MotionBank.parse_cmu_amc(amc_path, max_frames=50)
        assert seq["source_type"] == "CMU_MOCAP"
        assert seq["fps"] == 120.0
        assert len(seq["frames"]) == 50

        # Verify genuine Vicon degrees
        f0 = seq["frames"][0]
        assert "rradius" in f0["joint_rotations"] # elbow flexion
        elbow_angle = f0["joint_rotations"]["rradius"]
        assert abs(elbow_angle - 46.2257) < 1e-3, f"Expected 46.2257, got {elbow_angle}"


class TestP23KinematicsAndInvariance:
    def test_bone_length_invariance(self):
        # Synthetic movement: shoulder 0 -> 90, elbow 0 -> 90
        solver = ArmKinematicsSolver(upper_arm_length=0.30, forearm_length=0.26)
        upper_segs = []
        fore_segs = []

        for angle in range(0, 91, 5):
            (el_pt, wr_pt) = solver.forward_kinematics_2d(shoulder_elevation_deg=angle, elbow_flexion_deg=angle)
            shoulder_pt = (0.0, 1.42, 0.0)
            elbow_3d = (el_pt[0], el_pt[1], 0.0)
            wrist_3d = (wr_pt[0], wr_pt[1], 0.0)

            upper_segs.append((shoulder_pt, elbow_3d))
            fore_segs.append((elbow_3d, wrist_3d))

        res = BoneLengthInvarianceEvaluator.evaluate_invariance(
            upper_arm_segments=upper_segs,
            forearm_segments=fore_segs,
            nominal_upper_length=0.30,
            nominal_forearm_length=0.26,
            tolerance_m=1e-4
        )
        assert res["passed"] is True
        assert res["max_upper_arm_error_mm"] < 0.1
        assert res["max_forearm_error_mm"] < 0.1
