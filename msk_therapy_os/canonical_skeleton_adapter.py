"""
MSK-Therapy-OS V1.2 — Canonical Skeleton Contract & Adapter
===========================================================
Defines the single source of truth for the canonical humanoid skeleton
derived from the MakeHuman 53-bone rig.

Governs:
- Stable Bone IDs and naming standards (Blender, Three.js, OpenSim, BodyParts3D).
- Anatomical Hierarchy and Kinematic Parent-Child chains.
- Rest/Bind Pose translations, rotations, rolls, and bone lengths in meters.
- Local Joint Frames and physiological rotation axes (flexion/extension, abduction/adduction, rotation).
- Provenance-backed registration mappings for authentic anatomical structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RIG_JSON_PATH = REPO_ROOT / "research" / "character_pipeline" / "makehuman_assets" / "rig.game_engine.json"


class Laterality(str, Enum):
    RIGHT = "RIGHT"
    LEFT = "LEFT"
    MIDLINE = "MIDLINE"


class JointAxis(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"


@dataclass(frozen=True)
class CanonicalBoneDef:
    bone_id: str                      # e.g., "upperarm_r"
    display_name_en: str              # e.g., "Right Upper Arm"
    display_name_vi: str              # e.g., "Cánh tay phải"
    parent_id: Optional[str]          # e.g., "clavicle_r"
    laterality: Laterality
    head_pos: Tuple[float, float, float]  # meters in model space
    tail_pos: Tuple[float, float, float]  # meters in model space
    length_m: float
    roll_rad: float
    flexion_axis: str                 # "X", "Y", or "Z"
    flexion_sign: float               # +1.0 or -1.0
    abduction_axis: str
    abduction_sign: float
    rotation_axis: str
    rotation_sign: float
    rom_min_deg: float                # Physiological Range of Motion (deg)
    rom_max_deg: float


@dataclass
class JointTransform:
    bone_id: str
    translation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation_euler_deg: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])


class CanonicalSkeletonAdapter:
    """Canonical Humanoid Skeleton specification and kinematic validation adapter."""

    def __init__(self, rig_json_path: Optional[Path] = None):
        self._rig_path = rig_json_path or RIG_JSON_PATH
        self._bones: Dict[str, CanonicalBoneDef] = {}
        self._load_rig_definitions()

    def _load_rig_definitions(self):
        if not self._rig_path.exists():
            raise FileNotFoundError(f"Canonical rig definition missing at: {self._rig_path}")

        with open(self._rig_path, "r", encoding="utf-8") as f:
            raw_rig = json.load(f)

        for bone_name, info in raw_rig.items():
            head = info["head"]["default_position"]
            tail = info["tail"]["default_position"]
            parent = info.get("parent")
            roll = float(info.get("roll", 0.0))

            dx = tail[0] - head[0]
            dy = tail[1] - head[1]
            dz = tail[2] - head[2]
            length = math.sqrt(dx * dx + dy * dy + dz * dz)

            # Determine laterality
            if bone_name.endswith("_r"):
                lat = Laterality.RIGHT
            elif bone_name.endswith("_l"):
                lat = Laterality.LEFT
            else:
                lat = Laterality.MIDLINE

            # Local joint axes and physiological ROM specifications
            if "lowerarm" in bone_name:
                flex_axis, flex_sign = "X", 1.0   # +X = Elbow flexion
                abd_axis, abd_sign = "Z", 0.0     # Forearm has negligible adduction
                rot_axis, rot_sign = "Y", 1.0     # Pronation / Supination
                rom_min, rom_max = 0.0, 145.0     # Elbow flexion ROM: 0° to 145°
                name_en = "Right Forearm" if lat == Laterality.RIGHT else "Left Forearm"
                name_vi = "Cẳng tay phải" if lat == Laterality.RIGHT else "Cẳng tay trái"
            elif "upperarm" in bone_name:
                flex_axis, flex_sign = "X", 1.0   # Shoulder flexion
                abd_axis, abd_sign = "Z", -1.0    # Shoulder abduction
                rot_axis, rot_sign = "Y", 1.0     # Humeral internal/external rotation
                rom_min, rom_max = -45.0, 180.0
                name_en = "Right Upper Arm" if lat == Laterality.RIGHT else "Left Upper Arm"
                name_vi = "Cánh tay phải" if lat == Laterality.RIGHT else "Cánh tay trái"
            elif "clavicle" in bone_name:
                flex_axis, flex_sign = "Y", 1.0
                abd_axis, abd_sign = "Z", 1.0
                rot_axis, rot_sign = "X", 1.0
                rom_min, rom_max = -15.0, 30.0
                name_en = "Right Clavicle" if lat == Laterality.RIGHT else "Left Clavicle"
                name_vi = "Xương đòn phải" if lat == Laterality.RIGHT else "Xương đòn trái"
            elif "hand" in bone_name:
                flex_axis, flex_sign = "X", 1.0   # Palmar flexion
                abd_axis, abd_sign = "Z", 1.0     # Radial/Ulnar deviation
                rot_axis, rot_sign = "Y", 1.0
                rom_min, rom_max = -70.0, 80.0
                name_en = "Right Hand" if lat == Laterality.RIGHT else "Left Hand"
                name_vi = "Bàn tay phải" if lat == Laterality.RIGHT else "Bàn tay trái"
            else:
                flex_axis, flex_sign = "X", 1.0
                abd_axis, abd_sign = "Z", 1.0
                rot_axis, rot_sign = "Y", 1.0
                rom_min, rom_max = -90.0, 90.0
                name_en = bone_name.replace("_", " ").title()
                name_vi = bone_name

            self._bones[bone_name] = CanonicalBoneDef(
                bone_id=bone_name,
                display_name_en=name_en,
                display_name_vi=name_vi,
                parent_id=parent,
                laterality=lat,
                head_pos=(float(head[0]), float(head[1]), float(head[2])),
                tail_pos=(float(tail[0]), float(tail[1]), float(tail[2])),
                length_m=round(length, 4),
                roll_rad=round(roll, 4),
                flexion_axis=flex_axis,
                flexion_sign=flex_sign,
                abduction_axis=abd_axis,
                abduction_sign=abd_sign,
                rotation_axis=rot_axis,
                rotation_sign=rot_sign,
                rom_min_deg=rom_min,
                rom_max_deg=rom_max,
            )

    def get_bone(self, bone_id: str) -> Optional[CanonicalBoneDef]:
        return self._bones.get(bone_id)

    def get_all_bones(self) -> Dict[str, CanonicalBoneDef]:
        return dict(self._bones)

    def get_bone_count(self) -> int:
        return len(self._bones)

    def get_arm_bones(self, laterality: Laterality = Laterality.RIGHT) -> List[CanonicalBoneDef]:
        suffix = "_r" if laterality == Laterality.RIGHT else "_l"
        chain = ["clavicle" + suffix, "upperarm" + suffix, "lowerarm" + suffix, "hand" + suffix]
        return [self._bones[b] for b in chain if b in self._bones]

    def get_parent_id(self, bone_id: str) -> Optional[str]:
        b = self._bones.get(bone_id)
        return b.parent_id if b else None

    def get_ancestor_chain(self, bone_id: str) -> List[str]:
        """Returns hierarchy from root down to parent."""
        chain = []
        curr = self.get_parent_id(bone_id)
        while curr:
            chain.append(curr)
            curr = self.get_parent_id(curr)
        return list(reversed(chain))

    def get_children(self, bone_id: str) -> List[str]:
        return [b.bone_id for b in self._bones.values() if b.parent_id == bone_id]

    def export_contract_dict(self) -> Dict[str, Any]:
        """Exports data dictionary matching Three.js and Blender canonical schema."""
        bones_dict = {}
        for b_id, b_def in self._bones.items():
            bones_dict[b_id] = {
                "bone_id": b_def.bone_id,
                "display_name_en": b_def.display_name_en,
                "display_name_vi": b_def.display_name_vi,
                "parent_id": b_def.parent_id,
                "laterality": b_def.laterality.value,
                "head_pos": list(b_def.head_pos),
                "tail_pos": list(b_def.tail_pos),
                "length_m": b_def.length_m,
                "roll_rad": b_def.roll_rad,
                "kinematics": {
                    "flexion_axis": b_def.flexion_axis,
                    "flexion_sign": b_def.flexion_sign,
                    "abduction_axis": b_def.abduction_axis,
                    "abduction_sign": b_def.abduction_sign,
                    "rotation_axis": b_def.rotation_axis,
                    "rotation_sign": b_def.rotation_sign,
                    "rom_deg": [b_def.rom_min_deg, b_def.rom_max_deg]
                }
            }
        return {
            "skeleton_name": "MakeHuman_GameEngine_53Bone_Canonical",
            "version": "1.2",
            "unit": "meter",
            "coordinate_system": "RightHanded_YUp_glTF_Compatible",
            "bone_count": len(self._bones),
            "bones": bones_dict,
        }


# Global singleton instance
canonical_skeleton = CanonicalSkeletonAdapter()
