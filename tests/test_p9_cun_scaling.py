"""Comprehensive unit and integration tests for P9 WHO 2008 Parametric Cun-Scaling Engine."""
import math
import pytest

from msk_therapy_os.landmark_registry import LandmarkRegistry, BodyRegion
from msk_therapy_os.cun_scaling import (
    CunScalingEngine,
    WHO_BONE_SEGMENTS,
    BoneProportionalSegment,
    SegmentAxis,
)


def test_who_2008_bone_segments_catalog():
    """Verify bone proportional segments strictly follow WHO 2008 Section 2 standards."""
    engine = CunScalingEngine()
    assert len(engine.segments) >= 11

    # Check cranial segments
    cran_long = engine.segments.get("SEG_HEAD_ANTEROPOSTERIOR")
    assert cran_long is not None
    assert cran_long.standard_bcun_units == 9.0

    cran_trans = engine.segments.get("SEG_HEAD_MASTOID_TRANSVERSE")
    assert cran_trans is not None
    assert cran_trans.standard_bcun_units == 9.0

    # Check chest and abdomen segments
    sternum = engine.segments.get("SEG_CHEST_STERNUM")
    assert sternum is not None
    assert sternum.standard_bcun_units == 9.0

    abd_up = engine.segments.get("SEG_ABDOMEN_UPPER")
    assert abd_up is not None
    assert abd_up.standard_bcun_units == 8.0

    abd_low = engine.segments.get("SEG_ABDOMEN_LOWER")
    assert abd_low is not None
    assert abd_low.standard_bcun_units == 5.0

    binipple = engine.segments.get("SEG_CHEST_BINIPPLE")
    assert binipple is not None
    assert binipple.standard_bcun_units == 8.0

    # Check upper extremity segments
    arm = engine.segments.get("SEG_ARM_AXILLA_TO_ELBOW_R")
    assert arm is not None
    assert arm.standard_bcun_units == 9.0

    forearm = engine.segments.get("SEG_FOREARM_ELBOW_TO_WRIST_R")
    assert forearm is not None
    assert forearm.standard_bcun_units == 12.0

    # Check lower extremity segments
    thigh = engine.segments.get("SEG_THIGH_TROCHANTER_TO_POPLITEAL_R")
    assert thigh is not None
    assert thigh.standard_bcun_units == 19.0

    leg_lat = engine.segments.get("SEG_LEG_POPLITEAL_TO_MALLEOLUS_R")
    assert leg_lat is not None
    assert leg_lat.standard_bcun_units == 16.0

    leg_med = engine.segments.get("SEG_LEG_MEDIAL_TIBIA_TO_MALLEOLUS_R")
    assert leg_med is not None
    assert leg_med.standard_bcun_units == 13.0


def test_regional_cun_metrics_and_variance():
    """Verify mm-per-cun varies across body regions, disproving a single global constant."""
    engine = CunScalingEngine()
    metrics = engine.calculate_segment_metrics()

    assert len(metrics) >= 11
    forearm_metric = metrics["SEG_FOREARM_ELBOW_TO_WRIST_R"]
    abd_low_metric = metrics["SEG_ABDOMEN_LOWER"]
    mastoid_metric = metrics["SEG_HEAD_MASTOID_TRANSVERSE"]

    # Verify physical millimeter lengths are within realistic physiological ranges
    assert 200.0 < forearm_metric.segment_length_mm < 300.0
    assert 120.0 < abd_low_metric.segment_length_mm < 220.0
    assert 90.0 < mastoid_metric.segment_length_mm < 160.0

    # Verify mm per cun difference
    # Forearm 1 cun is ~20mm, lower abdomen 1 cun is ~33mm, mastoid 1 cun is ~14mm
    assert forearm_metric.mm_per_cun < abd_low_metric.mm_per_cun
    diff_pct = abs(abd_low_metric.mm_per_cun - forearm_metric.mm_per_cun) / forearm_metric.mm_per_cun * 100.0
    assert diff_pct > 30.0, f"Expected > 30% regional cun variance, got {diff_pct:.1f}%"


def test_segment_point_interpolation():
    """Verify interpolation of points along B-cun segments and lateral offsets."""
    engine = CunScalingEngine()

    # Forearm: midpoint (6 cun from wrist / 6 cun from elbow)
    res = engine.interpolate_point_on_segment("SEG_FOREARM_ELBOW_TO_WRIST_R", cun_fraction=0.5, lateral_cun=0.0)
    assert res["status"] == "VERIFIED_PARAMETRIC_CUN"
    assert res["position"] is not None
    mid_pos = res["position"]

    # Endpoints
    p_start = engine.registry.get_canonical_position("LM_CUBITAL_CREASE_R")
    p_end = engine.registry.get_canonical_position("LM_WRIST_CREASE_PALMAR_R")
    assert mid_pos[1] == pytest.approx((p_start[1] + p_end[1]) / 2.0, abs=1e-4)

    # Test lateral offset (e.g. 1.5 cun lateral)
    lat_res = engine.interpolate_point_on_segment("SEG_FOREARM_ELBOW_TO_WRIST_R", cun_fraction=0.5, lateral_cun=1.5, side="right")
    assert lat_res["status"] == "VERIFIED_PARAMETRIC_CUN"
    assert lat_res["position"][0] > mid_pos[0]


def test_out_of_bounds_interpolation_rejection():
    """Verify rejection when cun fraction exceeds physiological segment bounds."""
    engine = CunScalingEngine()

    # Cun fraction 1.8 (way past the joint)
    res_high = engine.interpolate_point_on_segment("SEG_FOREARM_ELBOW_TO_WRIST_R", cun_fraction=1.8)
    assert res_high["status"] == "OUT_OF_SEGMENT_BOUNDS"
    assert res_high["position"] is None

    # Cun fraction -0.5 (way proximal)
    res_low = engine.interpolate_point_on_segment("SEG_FOREARM_ELBOW_TO_WRIST_R", cun_fraction=-0.5)
    assert res_low["status"] == "OUT_OF_SEGMENT_BOUNDS"


def test_morphology_studio_adaptation():
    """Verify dynamic scaling of regional cun metrics responsive to patient stature and girths."""
    engine = CunScalingEngine()

    # Short stature patient (150 cm) vs tall stature patient (195 cm)
    short_params = {"height_cm": 150.0, "shoulder_width_cm": 38.0}
    tall_params = {"height_cm": 195.0, "shoulder_width_cm": 48.0}

    short_cun = engine.compute_morphology_adapted_cun(short_params)
    tall_cun = engine.compute_morphology_adapted_cun(tall_params)

    # Forearm cun should scale proportionally with stature
    assert short_cun["SEG_FOREARM_ELBOW_TO_WRIST_R"] < tall_cun["SEG_FOREARM_ELBOW_TO_WRIST_R"]
    expected_ratio = 195.0 / 150.0
    actual_ratio = tall_cun["SEG_FOREARM_ELBOW_TO_WRIST_R"] / short_cun["SEG_FOREARM_ELBOW_TO_WRIST_R"]
    assert actual_ratio == pytest.approx(expected_ratio, rel=0.05)

    # Transverse chest cun should scale with shoulder width
    assert short_cun["SEG_CHEST_BINIPPLE"] < tall_cun["SEG_CHEST_BINIPPLE"]

    # F-cun should scale with body height
    assert short_cun["FCUN_MIDDLE_FINGER"] < tall_cun["FCUN_MIDDLE_FINGER"]
    assert tall_cun["FCUN_FOUR_FINGERS"] == pytest.approx(tall_cun["FCUN_MIDDLE_FINGER"] * 3.0, rel=0.01)
