"""Parametric Body Engine for MSK-Therapy-OS V1.0.
Manages body parametric sliders (height, limb length, circumference), presets,
joint pivot recomputations, and reversibility without numerical drift.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BodyParameters:
    height_scale: float = 1.00
    right_arm_length_ratio: float = 1.00
    right_arm_circumference_visual: float = 1.00
    preset_name: str = "baseline"
    morph_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ParametricBodyEngine:
    """Engine managing body parameters, joint pivot recomputation, and presets."""

    PRESETS: Dict[str, Dict[str, float]] = {
        "baseline": {
            "height_scale": 1.00,
            "right_arm_length_ratio": 1.00,
            "right_arm_circumference_visual": 1.00
        },
        "slender": {
            "height_scale": 1.05,
            "right_arm_length_ratio": 1.03,
            "right_arm_circumference_visual": 0.88
        },
        "broader": {
            "height_scale": 0.98,
            "right_arm_length_ratio": 0.97,
            "right_arm_circumference_visual": 1.20
        },
        "longer_arm": {
            "height_scale": 1.02,
            "right_arm_length_ratio": 1.12,
            "right_arm_circumference_visual": 0.95
        }
    }

    # Anatomical base segment lengths in meters (BodyParts3D male reference)
    BASE_CLAVICLE_LENGTH_M = 0.16
    BASE_HUMERUS_LENGTH_M = 0.30
    BASE_FOREARM_LENGTH_M = 0.26
    BASE_HAND_LENGTH_M = 0.16
    BASE_SHOULDER_HEIGHT_M = 1.42

    def __init__(self, initial_params: Optional[BodyParameters] = None):
        self.current_params = initial_params or BodyParameters()
        self.history: List[BodyParameters] = [copy.deepcopy(self.current_params)]

    def set_parameters(
        self,
        height_scale: Optional[float] = None,
        right_arm_length_ratio: Optional[float] = None,
        right_arm_circumference_visual: Optional[float] = None,
        preset_name: str = "custom"
    ) -> BodyParameters:
        """Set parameters with fail-closed bounds checking."""
        h = self.current_params.height_scale if height_scale is None else float(height_scale)
        l = self.current_params.right_arm_length_ratio if right_arm_length_ratio is None else float(right_arm_length_ratio)
        c = self.current_params.right_arm_circumference_visual if right_arm_circumference_visual is None else float(right_arm_circumference_visual)

        # Clamping within physically and geometrically safe bounds
        h_clamped = max(0.85, min(1.15, h))
        l_clamped = max(0.85, min(1.15, l))
        c_clamped = max(0.80, min(1.30, c))

        self.current_params = BodyParameters(
            height_scale=round(h_clamped, 4),
            right_arm_length_ratio=round(l_clamped, 4),
            right_arm_circumference_visual=round(c_clamped, 4),
            preset_name=preset_name,
            morph_version=self.current_params.morph_version + 1
        )
        self.history.append(copy.deepcopy(self.current_params))
        return self.current_params

    def apply_preset(self, preset_name: str) -> BodyParameters:
        if preset_name not in self.PRESETS:
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {list(self.PRESETS.keys())}")
        p = self.PRESETS[preset_name]
        return self.set_parameters(
            height_scale=p["height_scale"],
            right_arm_length_ratio=p["right_arm_length_ratio"],
            right_arm_circumference_visual=p["right_arm_circumference_visual"],
            preset_name=preset_name
        )

    def compute_joint_pivots(self, params: Optional[BodyParameters] = None) -> Dict[str, Tuple[float, float, float]]:
        """Compute 3D joint centers in meters based on current parametric scales.
        Frame: +X Right, +Y Superior (Up), +Z Anterior (Front).
        """
        p = params or self.current_params
        h_scale = p.height_scale
        arm_scale = p.right_arm_length_ratio

        sh_y = self.BASE_SHOULDER_HEIGHT_M * h_scale
        humerus_len = self.BASE_HUMERUS_LENGTH_M * arm_scale
        forearm_len = self.BASE_FOREARM_LENGTH_M * arm_scale
        hand_len = self.BASE_HAND_LENGTH_M * arm_scale

        pivots = {
            "sternoclavicular_R": (0.02, round(sh_y, 4), 0.0),
            "shoulder_R": (0.18, round(sh_y, 4), 0.0),
            "elbow_R": (0.20, round(sh_y - humerus_len, 4), 0.0),
            "wrist_R": (0.22, round(sh_y - humerus_len - forearm_len, 4), 0.0),
            "hand_tip_R": (0.23, round(sh_y - humerus_len - forearm_len - hand_len, 4), 0.0)
        }
        return pivots

    def check_reversibility(self, iterations: int = 20) -> float:
        """Verify that cycling parameters back to baseline produces zero drift (< 1e-6 m)."""
        baseline_pivots = self.compute_joint_pivots(BodyParameters())
        for _ in range(iterations):
            self.apply_preset("slender")
            self.apply_preset("broader")
            self.apply_preset("longer_arm")
            self.apply_preset("baseline")

        end_pivots = self.compute_joint_pivots(self.current_params)
        max_diff = 0.0
        for k in baseline_pivots:
            p1 = baseline_pivots[k]
            p2 = end_pivots[k]
            diff = max(abs(a - b) for a, b in zip(p1, p2))
            if diff > max_diff:
                max_diff = diff
        return max_diff
