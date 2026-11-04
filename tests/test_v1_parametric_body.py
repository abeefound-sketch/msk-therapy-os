"""Unit tests for MSK-Therapy-OS V1.0 Parametric Body Engine (Package B).
Verifies sliders, presets, joint pivot recomputations, and reversibility without numerical drift.
"""
import pytest
from msk_therapy_os.body_parametric.parametric_engine import ParametricBodyEngine, BodyParameters


def test_parametric_engine_default_initialization():
    engine = ParametricBodyEngine()
    params = engine.current_params
    assert params.height_scale == 1.00
    assert params.right_arm_length_ratio == 1.00
    assert params.right_arm_circumference_visual == 1.00
    assert params.preset_name == "baseline"
    assert params.morph_version == 1


def test_apply_presets_updates_parameters_and_version():
    engine = ParametricBodyEngine()

    slender = engine.apply_preset("slender")
    assert slender.height_scale == 1.05
    assert slender.right_arm_length_ratio == 1.03
    assert slender.right_arm_circumference_visual == 0.88
    assert slender.preset_name == "slender"
    assert slender.morph_version == 2

    broader = engine.apply_preset("broader")
    assert broader.height_scale == 0.98
    assert broader.right_arm_length_ratio == 0.97
    assert broader.right_arm_circumference_visual == 1.20
    assert broader.preset_name == "broader"
    assert broader.morph_version == 3

    longer = engine.apply_preset("longer_arm")
    assert longer.height_scale == 1.02
    assert longer.right_arm_length_ratio == 1.12
    assert longer.right_arm_circumference_visual == 0.95
    assert longer.morph_version == 4


def test_unknown_preset_raises_error():
    engine = ParametricBodyEngine()
    with pytest.raises(ValueError, match="Unknown preset"):
        engine.apply_preset("non_existent_preset")


def test_parameter_clamping_enforces_physiological_bounds():
    engine = ParametricBodyEngine()
    # Out of bounds high
    clamped_high = engine.set_parameters(height_scale=2.5, right_arm_length_ratio=3.0, right_arm_circumference_visual=2.0)
    assert clamped_high.height_scale == 1.15
    assert clamped_high.right_arm_length_ratio == 1.15
    assert clamped_high.right_arm_circumference_visual == 1.30

    # Out of bounds low
    clamped_low = engine.set_parameters(height_scale=0.5, right_arm_length_ratio=0.5, right_arm_circumference_visual=0.5)
    assert clamped_low.height_scale == 0.85
    assert clamped_low.right_arm_length_ratio == 0.85
    assert clamped_low.right_arm_circumference_visual == 0.80


def test_joint_pivots_recomputed_proportionally():
    engine = ParametricBodyEngine()
    baseline_pivots = engine.compute_joint_pivots()

    assert "shoulder_R" in baseline_pivots
    assert "elbow_R" in baseline_pivots
    assert "wrist_R" in baseline_pivots

    sh_base = baseline_pivots["shoulder_R"]
    el_base = baseline_pivots["elbow_R"]
    base_humerus_len = sh_base[1] - el_base[1]

    # Apply longer arm
    engine.apply_preset("longer_arm")
    longer_pivots = engine.compute_joint_pivots()
    sh_longer = longer_pivots["shoulder_R"]
    el_longer = longer_pivots["elbow_R"]
    longer_humerus_len = sh_longer[1] - el_longer[1]

    assert longer_humerus_len > base_humerus_len


def test_reversibility_zero_drift():
    """Cycles presets 20 times and verifies maximum drift is under 1e-6 m."""
    engine = ParametricBodyEngine()
    drift = engine.check_reversibility(iterations=20)
    assert drift < 1e-6, f"Reversibility drift {drift} m exceeds tolerance 1e-6 m"
