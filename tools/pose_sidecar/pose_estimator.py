"""Pose Estimation Sidecar and Reconstruction Pipeline for P24.
Maps MediaPipe 33 landmarks to anatomical arm rig, generates observability matrices,
detects occlusions, and validates reconstructed kinematics fail-closed.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.blender_anatomy_studio.contracts import validate_contract
from tools.blender_anatomy_studio.motion_bank import JointConstraintRegistry

# MediaPipe Pose Landmarker 33 indices
MEDIAPIPE_LANDMARKS = {
    0: "NOSE",
    11: "LEFT_SHOULDER",
    12: "RIGHT_SHOULDER",
    13: "LEFT_ELBOW",
    14: "RIGHT_ELBOW",
    15: "LEFT_WRIST",
    16: "RIGHT_WRIST",
    17: "LEFT_PINKY",
    18: "RIGHT_PINKY",
    19: "LEFT_INDEX",
    20: "RIGHT_INDEX",
    21: "LEFT_THUMB",
    22: "RIGHT_THUMB",
    23: "LEFT_HIP",
    24: "RIGHT_HIP",
    25: "LEFT_KNEE",
    26: "RIGHT_KNEE",
    27: "LEFT_ANKLE",
    28: "RIGHT_ANKLE"
}

OBSERVABILITY_MATRIX = {
    "shoulder_elevation": {
        "status": "OBSERVABLE",
        "dofs": ["elevation_in_scapular_plane"],
        "confidence_factors": ["visibility", "chest_torso_angle"],
        "notes": "Glenohumeral joint center approximated from acromion-deltoid surface landmark."
    },
    "elbow_flexion": {
        "status": "OBSERVABLE",
        "dofs": ["flexion_extension"],
        "confidence_factors": ["visibility_shoulder", "visibility_elbow", "visibility_wrist"],
        "notes": "Humeroulnar hinge flexion computed from shoulder-elbow-wrist vector angle."
    },
    "forearm_pronation_supination": {
        "status": "UNOBSERVABLE",
        "dofs": ["axial_rotation"],
        "confidence_factors": [],
        "notes": "Elbow-wrist line vector cannot resolve forearm axial twist in single monocular view."
    },
    "monocular_depth": {
        "status": "ESTIMATED_UNCERTAIN",
        "dofs": ["camera_z_distance"],
        "confidence_factors": ["apparent_torso_scale"],
        "notes": "MediaPipe world_landmarks Z is an uncalibrated relative metric estimate."
    }
}


class PoseObservationPipeline:
    """Processes pose observations, validates against schema, and performs kinematics reconstruction."""

    def __init__(self, model_version: str = "MediaPipe_Pose_v0.10.14_Heavy"):
        self.model_version = model_version
        self.model_hash = "9a7f34c2b8109d43e201bcf54d3910c228876fe019a89c31492ba61b490f845a"

    def compute_elbow_flexion_from_landmarks(
        self,
        shoulder: Tuple[float, float, float],
        elbow: Tuple[float, float, float],
        wrist: Tuple[float, float, float]
    ) -> float:
        """Compute elbow flexion angle (degrees) from 3D joint centers.
        0 deg = straight arm; 90 deg = right angle; 145 deg = maximum anatomical flexion.
        """
        # Vector upper arm: from shoulder to elbow
        v1 = (shoulder[0] - elbow[0], shoulder[1] - elbow[1], shoulder[2] - elbow[2])
        # Vector forearm: from elbow to wrist
        v2 = (wrist[0] - elbow[0], wrist[1] - elbow[1], wrist[2] - elbow[2])

        mag1 = math.hypot(v1[0], v1[1], v1[2])
        mag2 = math.hypot(v2[0], v2[1], v2[2])

        if mag1 < 1e-5 or mag2 < 1e-5:
            return 0.0

        dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
        cos_ang = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        interior_angle_deg = math.degrees(math.acos(cos_ang))

        # Flexion is deviation from straight extension (180 deg interior angle)
        flexion_deg = 180.0 - interior_angle_deg
        return round(flexion_deg, 2)

    def create_observation_frame(
        self,
        frame_id: int,
        timestamp: float,
        source_video_hash: str,
        landmarks_33: List[Dict[str, Any]],
        image_width: int = 1280,
        image_height: int = 720
    ) -> Dict[str, Any]:
        """Construct schema-compliant PoseObservation object with quality flags."""
        norm_landmarks = []
        world_landmarks = []
        quality_flags = []

        # Check visibility for right arm landmarks (12: shoulder, 14: elbow, 16: wrist)
        right_arm_ids = [12, 14, 16]
        occluded = False

        for lm in landmarks_33:
            idx = lm["id"]
            name = MEDIAPIPE_LANDMARKS.get(idx, f"LANDMARK_{idx}")
            vis = float(lm.get("visibility", 1.0))
            pres = float(lm.get("presence", 1.0))

            if idx in right_arm_ids and vis < 0.5:
                occluded = True

            norm_landmarks.append({
                "id": idx,
                "name": name,
                "x": float(lm["x"]),
                "y": float(lm["y"]),
                "z": float(lm.get("z", 0.0)),
                "visibility": vis,
                "presence": pres
            })

            world_landmarks.append({
                "id": idx,
                "name": name,
                "x": float(lm.get("world_x", lm["x"])),
                "y": float(lm.get("world_y", lm["y"])),
                "z": float(lm.get("world_z", lm.get("z", 0.0))),
                "visibility": vis
            })

        if occluded:
            quality_flags.append("RIGHT_ARM_OCCLUSION_DETECTED")
            quality_flags.append("RECONSTRUCTION_CONFIDENCE_LOW")
        else:
            quality_flags.append("TRACKING_OPTIMAL")

        obs = {
            "schema_version": "1.0.0",
            "model_id": "google_mediapipe_pose",
            "model_version": self.model_version,
            "model_hash": self.model_hash,
            "source_video_hash": source_video_hash,
            "frame_id": frame_id,
            "timestamp": timestamp,
            "camera_id": "webcam_c920_monocular",
            "image_width": image_width,
            "image_height": image_height,
            "landmarks_normalized": norm_landmarks,
            "landmarks_world_estimated": world_landmarks,
            "camera_calibration": {
                "focal_length_px": 1050.0,
                "principal_point": [image_width / 2.0, image_height / 2.0]
            },
            "observability_flags": {
                "forearm_pronation": "UNOBSERVABLE",
                "monocular_depth": "ESTIMATED_UNCERTAIN"
            },
            "quality_flags": quality_flags
        }

        ok, err = validate_contract(obs, "pose_observation")
        if not ok:
            raise ValueError(f"PoseObservation failed schema validation: {err}")

        return obs

    def reconstruct_arm_kinematics(
        self,
        observation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reconstruct right arm joint angles from observation with fail-closed rejection of occluded frames."""
        flags = observation.get("quality_flags", [])
        if "RIGHT_ARM_OCCLUSION_DETECTED" in flags:
            return {
                "status": "REJECTED_DUE_TO_OCCLUSION",
                "frame_id": observation["frame_id"],
                "timestamp": observation["timestamp"],
                "elbow_flexion_deg": None,
                "confidence": 0.0,
                "reason": "Elbow or wrist landmark visibility < 0.5; refusing fake pose invention."
            }

        # Find landmarks 12, 14, 16
        world_lms = {lm["id"]: lm for lm in observation["landmarks_world_estimated"]}
        if 12 not in world_lms or 14 not in world_lms or 16 not in world_lms:
            return {
                "status": "MISSING_LANDMARKS",
                "frame_id": observation["frame_id"],
                "timestamp": observation["timestamp"],
                "elbow_flexion_deg": None,
                "confidence": 0.0,
                "reason": "Missing shoulder, elbow, or wrist landmarks."
            }

        s = world_lms[12]
        e = world_lms[14]
        w = world_lms[16]

        sh_pos = (s["x"], s["y"], s["z"])
        el_pos = (e["x"], e["y"], e["z"])
        wr_pos = (w["x"], w["y"], w["z"])

        flexion = self.compute_elbow_flexion_from_landmarks(sh_pos, el_pos, wr_pos)

        # Validate against Kapandji Joint Constraints
        ok, clamped, reason = JointConstraintRegistry.validate_angle("right_elbow", flexion)

        return {
            "status": "RECONSTRUCTED",
            "frame_id": observation["frame_id"],
            "timestamp": observation["timestamp"],
            "raw_elbow_flexion_deg": flexion,
            "constrained_elbow_flexion_deg": clamped,
            "is_within_anatomical_bounds": ok,
            "constraint_note": reason,
            "confidence": min(s["visibility"], e["visibility"], w["visibility"])
        }
