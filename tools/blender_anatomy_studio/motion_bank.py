"""Motion Bank, Joint Constraint Registry, and Retargeting Engine for P23.
Parses genuine motion files (.mot, mocap), enforces joint constraints, and computes kinematic quality metrics.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .contracts import validate_contract

class JointConstraintRegistry:
    """Authoritative registry for kinematic DOFs, literature citations, and hard/soft limits."""

    CONSTRAINTS: Dict[str, Dict[str, Any]] = {
        "right_elbow": {
            "schema_version": "1.0.0",
            "joint_id": "right_elbow",
            "kinematic_dofs": ["flexion_extension"],
            "axis_frame": "local_humerus",
            "convention": "Kapandji_2007",
            "units": "deg",
            "rom_reference": "Kapandji IA. The Physiology of the Joints, Vol 1 (2007), p. 82",
            "rom_context": "Active elbow flexion in sagittal plane, standard anatomic reference",
            "bounds_status": "LITERATURE_REFERENCED",
            "hard_limits": {
                "min": 0.0,
                "max": 145.0
            },
            "soft_prior_id": "CMU_Subject_02_Trial_01",
            "model_assumptions": [
                "Uniaxial hinge joint (trochlea humeri and trochlear notch)",
                "Soft tissue opposition limits flexion in muscular subjects"
            ],
            "review_status": "EXPERT_REVIEW_PENDING"
        },
        "right_shoulder_elevation": {
            "schema_version": "1.0.0",
            "joint_id": "right_shoulder_elevation",
            "kinematic_dofs": ["scapulohumeral_elevation"],
            "axis_frame": "scapular_plane",
            "convention": "OpenSim_Seth2016",
            "units": "deg",
            "rom_reference": "Seth A, et al. A biomechanical model of the scapulothoracic joint to address the full shoulder range of motion. J Biomech. 2016.",
            "rom_context": "Thoracohumeral elevation from resting adduction to full overhead elevation",
            "bounds_status": "LITERATURE_REFERENCED",
            "hard_limits": {
                "min": 0.0,
                "max": 180.0
            },
            "soft_prior_id": "OpenSim_Seth_Elevation_Trial",
            "model_assumptions": [
                "Coupled scapulothoracic rhythm (2:1 glenohumeral to scapular rotation ratio)",
                "Full elevation requires upward rotation of scapula and clavicular elevation"
            ],
            "review_status": "EXPERT_REVIEW_PENDING"
        },
        "right_forearm_pronation": {
            "schema_version": "1.0.0",
            "joint_id": "right_forearm_pronation",
            "kinematic_dofs": ["pronation_supination"],
            "axis_frame": "longitudinal_forearm",
            "convention": "AAOS_1965",
            "units": "deg",
            "rom_reference": "American Academy of Orthopaedic Surgeons (AAOS). Joint Motion: Method of Measuring and Recording (1965).",
            "rom_context": "Elbow flexed at 90 deg, thumb pointing upward at neutral",
            "bounds_status": "LITERATURE_REFERENCED",
            "hard_limits": {
                "min": -85.0,  # 85 deg supination
                "max": 90.0    # 90 deg pronation
            },
            "soft_prior_id": None,
            "model_assumptions": [
                "Radius pivots around stationary ulna at proximal and distal radioulnar joints",
                "Flagged as UNOBSERVABLE when tracked via single-camera 2D wrist landmarks"
            ],
            "review_status": "EXPERT_REVIEW_PENDING"
        }
    }

    @classmethod
    def get_constraint(cls, joint_id: str) -> Optional[Dict[str, Any]]:
        return cls.CONSTRAINTS.get(joint_id)

    @classmethod
    def validate_angle(cls, joint_id: str, angle_deg: float) -> Tuple[bool, float, str]:
        """Validate an angle against constraints. Returns (is_within_bounds, clamped_angle, reason)."""
        c = cls.get_constraint(joint_id)
        if not c or not c.get("hard_limits"):
            return True, angle_deg, "No hard limits defined"

        limits = c["hard_limits"]
        min_lim = limits["min"]
        max_lim = limits["max"]

        if angle_deg < min_lim:
            return False, min_lim, f"Angle {angle_deg:.2f}° is below minimum {min_lim}° ({c['rom_reference']})"
        elif angle_deg > max_lim:
            return False, max_lim, f"Angle {angle_deg:.2f}° exceeds maximum {max_lim}° ({c['rom_reference']})"

        return True, angle_deg, "Within bounds"


class MotionBank:
    """Manages motion sequence loading, OpenSim .mot conversion, CMU AMC parsing, and validation."""

    @staticmethod
    def parse_opensim_mot(mot_filepath: str | Path) -> Dict[str, Any]:
        """Parse OpenSim .mot file into structured MotionSequence dictionary."""
        p = Path(mot_filepath).resolve()
        if not p.exists():
            raise FileNotFoundError(f"OpenSim motion file not found: {p}")

        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        header_end = 0
        in_degrees = True
        n_rows = 0
        n_cols = 0

        for i, line in enumerate(lines):
            line_str = line.strip()
            if line_str.startswith("nRows="):
                n_rows = int(line_str.split("=")[1])
            elif line_str.startswith("nColumns="):
                n_cols = int(line_str.split("=")[1])
            elif line_str.startswith("inDegrees="):
                in_degrees = line_str.split("=")[1].lower() in ["yes", "true", "1"]
            elif line_str.lower() == "endheader":
                header_end = i + 1
                break

        if header_end == 0 or header_end >= len(lines):
            raise ValueError(f"Invalid .mot file format: 'endheader' not found in {p}")

        # Column names are on the line immediately following endheader
        col_names = lines[header_end].strip().split()
        data_rows = []
        for line in lines[header_end + 1:]:
            parts = line.strip().split()
            if parts and len(parts) == len(col_names):
                data_rows.append([float(x) for x in parts])

        sha256 = hashlib.sha256(p.read_bytes()).hexdigest()

        frames = []
        fps = 10.0
        if len(data_rows) >= 2:
            dt = data_rows[1][0] - data_rows[0][0]
            if dt > 1e-4:
                fps = round(1.0 / dt, 2)

        for idx, row in enumerate(data_rows):
            t = row[0]
            row_dict = dict(zip(col_names, row))
            rotations = {}
            for k, v in row_dict.items():
                if k != "time":
                    rotations[k] = v if in_degrees else math.degrees(v)

            frames.append({
                "frame_index": idx,
                "time_seconds": t,
                "joint_rotations": rotations,
                "confidence": 1.0,
                "observable_flags": {
                    "shoulder_elevation": True,
                    "elbow_flexion": True,
                    "pronation_supination": False
                }
            })

        motion_seq = {
            "schema_version": "1.0.0",
            "motion_id": f"mot_{p.stem}",
            "source_trial": p.name,
            "source_type": "OPENSIM_MOT",
            "fps": fps,
            "root_transform": [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0
            ],
            "rig_version": "1.0.0",
            "source_skeleton": "OpenSim_Seth_Shoulder_Model",
            "target_skeleton": "MSK_UpperLimb_Armature_R",
            "frames": frames,
            "quality_metadata": {
                "total_frames": len(frames),
                "dropped_frames": 0,
                "unobservable_dofs": ["right_forearm_pronation"],
                "checksum": sha256
            }
        }

        ok, err = validate_contract(motion_seq, "motion_sequence")
        if not ok:
            raise ValueError(f"Generated motion sequence failed schema validation: {err}")

        return motion_seq

    @staticmethod
    def parse_cmu_amc(
        amc_filepath: str | Path,
        max_frames: Optional[int] = 100,
        fps: float = 120.0
    ) -> Dict[str, Any]:
        """Parse CMU Mocap AMC file into structured MotionSequence dictionary."""
        p = Path(amc_filepath).resolve()
        if not p.exists():
            raise FileNotFoundError(f"CMU AMC file not found: {p}")

        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        sha256 = hashlib.sha256(p.read_bytes()).hexdigest()

        frames = []
        current_frame_idx = None
        current_rotations = {}

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or line_str.startswith(":"):
                continue

            parts = line_str.split()
            if len(parts) == 1 and parts[0].isdigit():
                # New frame header
                if current_frame_idx is not None:
                    t = current_frame_idx / fps
                    frames.append({
                        "frame_index": current_frame_idx,
                        "time_seconds": round(t, 4),
                        "joint_rotations": current_rotations,
                        "confidence": 1.0,
                        "observable_flags": {
                            "shoulder_elevation": "rhumerus" in current_rotations,
                            "elbow_flexion": "rradius" in current_rotations,
                            "pronation_supination": False
                        }
                    })
                    if max_frames and len(frames) >= max_frames:
                        break
                current_frame_idx = int(parts[0])
                current_rotations = {}
            elif len(parts) >= 2 and current_frame_idx is not None:
                bone_name = parts[0]
                vals = [float(v) for v in parts[1:]]
                if len(vals) == 1:
                    current_rotations[bone_name] = vals[0]
                elif len(vals) == 3:
                    current_rotations[f"{bone_name}_rx"] = vals[0]
                    current_rotations[f"{bone_name}_ry"] = vals[1]
                    current_rotations[f"{bone_name}_rz"] = vals[2]

        # Flush final frame if needed
        if current_frame_idx is not None and (not max_frames or len(frames) < max_frames):
            frames.append({
                "frame_index": current_frame_idx,
                "time_seconds": round(current_frame_idx / fps, 4),
                "joint_rotations": current_rotations,
                "confidence": 1.0,
                "observable_flags": {
                    "shoulder_elevation": "rhumerus" in current_rotations,
                    "elbow_flexion": "rradius" in current_rotations,
                    "pronation_supination": False
                }
            })

        motion_seq = {
            "schema_version": "1.0.0",
            "motion_id": f"cmu_{p.stem}",
            "source_trial": p.name,
            "source_type": "CMU_MOCAP",
            "fps": fps,
            "root_transform": [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0
            ],
            "rig_version": "1.0.0",
            "source_skeleton": "CMU_Vicon_FoxedUp_ASF",
            "target_skeleton": "MSK_UpperLimb_Armature_R",
            "frames": frames,
            "quality_metadata": {
                "total_frames": len(frames),
                "dropped_frames": 0,
                "unobservable_dofs": ["right_forearm_pronation", "wrist_deviation"],
                "checksum": sha256
            }
        }

        ok, err = validate_contract(motion_seq, "motion_sequence")
        if not ok:
            raise ValueError(f"Generated CMU motion sequence failed schema validation: {err}")

        return motion_seq


class BoneLengthInvarianceEvaluator:
    """Evaluates that arm bone lengths remain invariant across all animated poses."""

    @staticmethod
    def evaluate_invariance(
        upper_arm_segments: List[Tuple[Any, Any]],
        forearm_segments: List[Tuple[Any, Any]],
        nominal_upper_length: float = 0.30,
        nominal_forearm_length: float = 0.26,
        tolerance_m: float = 1e-4
    ) -> Dict[str, Any]:
        """Check that segment lengths stay within tolerance_m of nominal."""
        upper_errors = []
        forearm_errors = []

        for p1, p2 in upper_arm_segments:
            l_upper = math.dist(p1, p2)
            upper_errors.append(abs(l_upper - nominal_upper_length))

        for p1, p2 in forearm_segments:
            l_fore = math.dist(p1, p2)
            forearm_errors.append(abs(l_fore - nominal_forearm_length))

        max_upper_err = max(upper_errors) if upper_errors else 0.0
        max_fore_err = max(forearm_errors) if forearm_errors else 0.0

        passed = (max_upper_err <= tolerance_m) and (max_fore_err <= tolerance_m)
        return {
            "passed": passed,
            "max_upper_arm_error_mm": max_upper_err * 1000.0,
            "max_forearm_error_mm": max_fore_err * 1000.0,
            "tolerance_mm": tolerance_m * 1000.0
        }
