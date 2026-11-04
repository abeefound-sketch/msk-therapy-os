"""Web Motion Controller for MSK-Therapy-OS V1.0.
Maps MediaPipe 100-frame video kinematics to 3D hierarchical bone groups
with Inman 2:1 scapulohumeral rhythm and interactive mouse posing.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
P28_MOTION_JSON = REPO_ROOT / "1docs" / "audits" / "P28" / "evidence" / "p28_real_motion_sequence.json"


@dataclass
class MotionPose:
    frame_index: int
    timestamp_sec: float
    total_shoulder_elevation_deg: float
    scapular_elevation_deg: float
    glenohumeral_elevation_deg: float
    elbow_flexion_deg: float
    confidence: float = 1.0
    observable_flags: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WebMotionController:
    """Coordinates video kinematics, 2:1 rhythm retargeting, and mouse posing."""

    def __init__(self):
        self.frames: List[MotionPose] = []
        self._load_sequence()

    def _load_sequence(self):
        if not P28_MOTION_JSON.exists():
            return
        data = json.loads(P28_MOTION_JSON.read_text(encoding="utf-8"))
        for f in data.get("frames", []):
            idx = f["frame_index"]
            t_sec = f["time_seconds"]
            rot = f["joint_rotations"]
            sh_elev = rot["right_shoulder_elevation_deg"]
            el_flex = rot["right_elbow_flexion_deg"]

            # 2:1 Inman Rhythm calculation
            scap_deg = sh_elev / 3.0
            gleno_deg = (sh_elev * 2.0) / 3.0

            self.frames.append(MotionPose(
                frame_index=idx,
                timestamp_sec=t_sec,
                total_shoulder_elevation_deg=round(sh_elev, 2),
                scapular_elevation_deg=round(scap_deg, 2),
                glenohumeral_elevation_deg=round(gleno_deg, 2),
                elbow_flexion_deg=round(el_flex, 2),
                confidence=f.get("confidence", 1.0),
                observable_flags=f.get("observable_flags", {})
            ))

    def get_pose(self, frame_index: int) -> Optional[MotionPose]:
        if 0 <= frame_index < len(self.frames):
            return self.frames[frame_index]
        return None

    def compute_mouse_pose(self, shoulder_elevation_deg: float, elbow_flexion_deg: float) -> MotionPose:
        """Compute hierarchical angles from direct user mouse dragging input."""
        # Anatomical ROM clamping
        sh_clamped = max(0.0, min(180.0, float(shoulder_elevation_deg)))
        el_clamped = max(0.0, min(145.0, float(elbow_flexion_deg)))

        scap_deg = sh_clamped / 3.0
        gleno_deg = (sh_clamped * 2.0) / 3.0

        return MotionPose(
            frame_index=-1,
            timestamp_sec=-1.0,
            total_shoulder_elevation_deg=round(sh_clamped, 2),
            scapular_elevation_deg=round(scap_deg, 2),
            glenohumeral_elevation_deg=round(gleno_deg, 2),
            elbow_flexion_deg=round(el_clamped, 2),
            confidence=1.0,
            observable_flags={"source": "INTERACTIVE_MOUSE_POSE"}
        )

    def get_all_frames_dict(self) -> List[Dict[str, Any]]:
        return [f.to_dict() for f in self.frames]
