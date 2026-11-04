"""
MSK-Therapy-OS V1.1 — Character Motion Retarget Adapter
======================================================
Retargets authentic MediaPipe landmark sequences (100 frames from real video)
to the MakeHuman 53-bone humanoid character rig.

Kinematic Rules:
1. MediaPipe Landmarks -> Joint Angle Sequence -> Humanoid Armature Bones.
2. Physiological Range of Motion (ROM) Clamping:
   - Right Elbow Flexion: [0.0, 145.0] degrees
   - Right Shoulder Elevation: [0.0, 180.0] degrees
3. Scapulohumeral Rhythm: 2:1 ratio (2 parts glenohumeral / upperarm_r, 1 part scapular / clavicle_r).
4. Strict DOF Observability:
   - Observable: Shoulder elevation, Elbow flexion.
   - Non-observable from monocular frontal camera: Forearm pronation/supination (explicitly flagged).
"""

from dataclasses import dataclass, asdict
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
P28_MOTION_PATH = REPO_ROOT / "1docs" / "audits" / "P28" / "evidence" / "p28_real_motion_sequence.json"


@dataclass
class RetargetedFrame:
    frame_index: int
    time_seconds: float
    confidence: float
    raw_shoulder_elevation_deg: float
    raw_elbow_flexion_deg: float
    clamped_shoulder_elevation_deg: float
    clamped_elbow_flexion_deg: float
    scapulohumeral_clavicle_deg: float
    scapulohumeral_humerus_deg: float
    bone_rotations_rad: Dict[str, Dict[str, float]]
    observable_flags: Dict[str, bool]
    retargeting_residual_deg: float


class CharacterMotionRetargetAdapter:
    """Retargets MediaPipe 100-frame video sequence onto the MakeHuman game_engine rig."""

    def __init__(self, motion_path: Optional[Path] = None):
        self.motion_path = motion_path or P28_MOTION_PATH
        self._raw_data: Dict[str, Any] = {}
        self._frames: List[RetargetedFrame] = []
        self._load_and_retarget()

    def _load_and_retarget(self):
        if not self.motion_path.exists():
            print(f"[CharacterMotionRetargetAdapter] Warning: {self.motion_path} not found")
            return

        with open(self.motion_path, "r", encoding="utf-8") as f:
            self._raw_data = json.load(f)

        raw_frames = self._raw_data.get("frames", [])
        for f in raw_frames:
            idx = f.get("frame_index", 0)
            t_sec = f.get("time_seconds", 0.0)
            conf = f.get("confidence", 1.0)
            rot = f.get("joint_rotations", {})

            raw_shoulder = rot.get("right_shoulder_elevation_deg", 0.0)
            raw_elbow = rot.get("right_elbow_flexion_deg", 0.0)

            # Physiological clamping
            clamped_shoulder = max(0.0, min(180.0, raw_shoulder))
            clamped_elbow = max(0.0, min(145.0, raw_elbow))

            # Scapulohumeral rhythm (2:1 ratio)
            # Above 30 degrees of total elevation, scapula contributes 1/3, humerus 2/3
            if clamped_shoulder <= 30.0:
                clavicle_elev = 0.0
                humerus_elev = clamped_shoulder
            else:
                clavicle_elev = (clamped_shoulder - 30.0) * (1.0 / 3.0)
                humerus_elev = 30.0 + (clamped_shoulder - 30.0) * (2.0 / 3.0)

            # Mapping to MakeHuman bone rotation axes
            # lowerarm_r: rot X = +clamped_elbow
            # upperarm_r: rot Z = -humerus_elev
            # clavicle_r: rot Z = -clavicle_elev
            bone_rotations = {
                "clavicle_r": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": -math.radians(clavicle_elev)
                },
                "upperarm_r": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": -math.radians(humerus_elev)
                },
                "lowerarm_r": {
                    "x": math.radians(clamped_elbow),
                    "y": 0.0,
                    "z": 0.0
                }
            }

            # Observability flags
            obs = f.get("observable_flags", {})
            obs["shoulder_elevation_observable"] = True
            obs["elbow_flexion_observable"] = True
            obs["forearm_pronation_observable"] = False  # Not observable in 2D monocular

            residual = abs(raw_shoulder - clamped_shoulder) + abs(raw_elbow - clamped_elbow)

            self._frames.append(RetargetedFrame(
                frame_index=idx,
                time_seconds=t_sec,
                confidence=conf,
                raw_shoulder_elevation_deg=raw_shoulder,
                raw_elbow_flexion_deg=raw_elbow,
                clamped_shoulder_elevation_deg=clamped_shoulder,
                clamped_elbow_flexion_deg=clamped_elbow,
                scapulohumeral_clavicle_deg=clavicle_elev,
                scapulohumeral_humerus_deg=humerus_elev,
                bone_rotations_rad=bone_rotations,
                observable_flags=obs,
                retargeting_residual_deg=round(residual, 3)
            ))

    def get_frame(self, index: int) -> Optional[RetargetedFrame]:
        if 0 <= index < len(self._frames):
            return self._frames[index]
        return None

    def get_total_frames(self) -> int:
        return len(self._frames)

    def export_retargeted_sequence(self) -> List[Dict[str, Any]]:
        return [asdict(f) for f in self._frames]

    def get_motion_summary(self) -> Dict[str, Any]:
        if not self._frames:
            return {"error": "No frames loaded"}
        
        elbow_angles = [f.clamped_elbow_flexion_deg for f in self._frames]
        shoulder_angles = [f.clamped_shoulder_elevation_deg for f in self._frames]
        confidences = [f.confidence for f in self._frames]

        return {
            "total_frames": len(self._frames),
            "duration_seconds": self._frames[-1].time_seconds if self._frames else 0.0,
            "mean_confidence": round(sum(confidences) / len(confidences), 4),
            "min_elbow_flex_deg": round(min(elbow_angles), 2),
            "max_elbow_flex_deg": round(max(elbow_angles), 2),
            "min_shoulder_elev_deg": round(min(shoulder_angles), 2),
            "max_shoulder_elev_deg": round(max(shoulder_angles), 2),
            "scapulohumeral_rhythm_applied": "2:1",
            "kinematic_model": "MakeHuman 53-Bone Humanoid Armature"
        }


# Module-level singleton
motion_retarget_adapter = CharacterMotionRetargetAdapter()
