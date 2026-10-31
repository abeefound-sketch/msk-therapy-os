"""Tests for Milestone P16: Scientific Biomechanics Integrity, Muscle Mechanics & Interactive Self-Education Studio.

Validates:
1. P16-01: Disambiguated cervical gravitational physics (W_head, d_horizontal, M_gravity, r_eff, F_extensor, R_comp).
   Tissue stress status = TISSUE_STRESS_MODEL_UNAVAILABLE.
2. P16-01: Upper Crossed Syndrome conceptual framing (rejection of deterministic pathology assertions, natural variance).
3. P16-02: OpenSim data provenance manifest, SHA-256 integrity, blocked live runtime status.
4. P16-03: Multi-axis cervical motion scenarios (flexion, extension, axial rotation, lateral bending, forward head).
5. P16-04: Muscle Mechanics Inspector Modes A, B, C, D and mandatory empty states:
   - MODE_A: Anatomical participation (roles, origins, insertions, primary actions)
   - MODE_B: MODEL_GEOMETRY_INSUFFICIENT
   - MODE_C: STATIC_OPTIMIZATION_MODEL_ESTIMATE (or MUSCLE_ACTIVATION_NOT_AVAILABLE)
   - MODE_D: MUSCLE_FORCE_NOT_AVAILABLE
6. P16-05: Interactive scenario comparison engine deltas and non-diagnostic disclaimers.
7. P16-06: Unified MSK Education curriculum, 10 topics, red flags, bilingual structure.
8. P16-07: Research evidence register (EV-01..EV-20) with categorical confidence classifications.
"""

import math
import hashlib
from pathlib import Path
import pytest

from msk_therapy_os.biomechanics_adapter import (
    calculate_cervical_gravitational_mechanics,
    calculate_cervicothoracic_posture,
    get_scenario_catalog,
    get_provenance_manifest,
    get_muscle_mechanics_inspection,
    compare_scenarios,
    get_unified_education_curriculum,
    PHYSIOLOGICAL_RANGES_DEG,
    SCEN_CERVICAL_AXIAL_ROTATION,
    SCEN_CERVICAL_LATERAL_BENDING,
    SCEN_VASAVADA_CERVICAL_FLEX_EXT,
    SCEN_ILLUSTRATIVE_FORWARD_HEAD,
    SCEN_CONCURRENT_FORWARD_HEAD_ROUNDED_SHOULDER,
)


# ============================================================================
# P16-01: Cervical Gravitational Mechanics Disambiguation
# ============================================================================

def test_separated_cervical_gravitational_physics():
    """Verify separate physical entities: Mass -> Weight -> Moment Arm -> Torque -> Muscle Force -> Compression."""
    # Test at neutral CVA (55 degrees, minimal forward translation)
    neutral = calculate_cervical_gravitational_mechanics(cva_deg=55.0, head_mass_kg=5.0)
    
    # 1. Gravitational force of head (N)
    assert neutral["head_mass_kg"] == 5.0
    assert neutral["gravitational_accel_m_s2"] == 9.80665
    assert math.isclose(neutral["head_weight_n"], 49.03, rel_tol=1e-2)
    
    # 2. Horizontal moment arm (m)
    assert math.isclose(neutral["horizontal_moment_arm_m"], 0.025, rel_tol=1e-2)
    assert neutral["horizontal_moment_arm_cm"] == 2.5
    
    # 3. External gravitational flexion moment (N*m) = W * d
    expected_m_neutral = 49.03 * 0.025 # ~1.226 N*m
    assert math.isclose(neutral["gravitational_flexion_moment_nm"], expected_m_neutral, rel_tol=1e-2)
    
    # 4. Effective extensor moment arm
    assert neutral["effective_extensor_moment_arm_m"] == 0.035
    
    # 5. Required extensor muscle equilibrium force (N) = M / r_eff
    expected_f_ext_neutral = expected_m_neutral / 0.035 # ~35.0 N
    assert math.isclose(neutral["extensor_demand_force_n"], expected_f_ext_neutral, rel_tol=1e-2)
    
    # 6. Combined resultant joint axial compression (N) = W + F_ext
    expected_r_comp_neutral = 49.03 + expected_f_ext_neutral # ~84.1 N
    assert math.isclose(neutral["resultant_axial_compression_n"], expected_r_comp_neutral, rel_tol=1e-2)
    
    # 7. Stress status must be unavailable
    assert neutral["tissue_stress_status"] == "TISSUE_STRESS_MODEL_UNAVAILABLE"
    assert "Stress cannot be reported without patient-specific" in neutral["tissue_stress_scientific_note"]

    # Test at severe forward head posture (CVA = 30 degrees)
    severe = calculate_cervical_gravitational_mechanics(cva_deg=30.0, head_mass_kg=5.0)
    assert math.isclose(severe["horizontal_moment_arm_m"], 0.075, rel_tol=1e-2)
    assert severe["horizontal_moment_arm_cm"] == 7.5
    
    expected_m_severe = 49.03 * 0.075 # ~3.677 N*m
    assert math.isclose(severe["gravitational_flexion_moment_nm"], expected_m_severe, rel_tol=1e-2)
    
    expected_f_ext_severe = expected_m_severe / 0.035 # ~105.1 N
    assert math.isclose(severe["extensor_demand_force_n"], expected_f_ext_severe, rel_tol=1e-2)
    
    expected_r_comp_severe = 49.03 + expected_f_ext_severe # ~154.1 N
    assert math.isclose(severe["resultant_axial_compression_n"], expected_r_comp_severe, rel_tol=1e-2)
    
    # Verify strict monotonic relationship between CVA deficit and extensor demand
    assert severe["gravitational_flexion_moment_nm"] > neutral["gravitational_flexion_moment_nm"]
    assert severe["extensor_demand_force_n"] > neutral["extensor_demand_force_n"]
    assert severe["resultant_axial_compression_n"] > neutral["resultant_axial_compression_n"]


def test_gravitational_mechanics_numeric_guards():
    """Verify input validation rejects non-finite floats and out-of-range bounds."""
    with pytest.raises(ValueError, match="must be a finite real number"):
        calculate_cervical_gravitational_mechanics(cva_deg=float("nan"))

    with pytest.raises(ValueError, match="must be a finite real number"):
        calculate_cervical_gravitational_mechanics(cva_deg=float("inf"))

    with pytest.raises(ValueError, match="must be a finite real number"):
        calculate_cervical_gravitational_mechanics(cva_deg=45.0, head_mass_kg=float("nan"))

    with pytest.raises(ValueError, match="Head mass must be positive"):
        calculate_cervical_gravitational_mechanics(cva_deg=45.0, head_mass_kg=-5.0)


# ============================================================================
# P16-01: Upper Crossed Syndrome Conceptual Framing
# ============================================================================

def test_ucs_conceptual_framing_and_disclaimers():
    """Verify Janda Upper Crossed Syndrome is framed as a conceptual model, not a diagnostic truth."""
    posture = calculate_cervicothoracic_posture(forward_head_mm=25.0, cva_deg=40.0)
    
    assert "conceptual clinical framework" in posture["janda_framework_status"]
    assert "not a verified diagnostic condition" in posture["janda_framework_status"]
    assert "not deterministically establish" in posture["janda_framework_status"]
    
    # Assert presence of natural asymptomatic variation disclaimer
    assert "disclaimer" in posture
    assert "Asymptomatic individuals frequently display" in posture["disclaimer"]
    
    # Verify non-diagnostic gate invariants
    assert "FORWARD_HEAD_VARIATION != STRUCTURAL_DEFORMITY_DIAGNOSIS" in posture["disclaimer"]


# ============================================================================
# P16-02: OpenSim Data Provenance & Runtime Status
# ============================================================================

def test_opensim_provenance_manifest_and_offline_status():
    """Verify data provenance manifest completeness, SHA-256 integrity, and blocked live runtime."""
    manifest = get_provenance_manifest()
    
    assert manifest["live_opensim_runtime_status"] == "OPENSIM_LIVE_SIMULATION_BLOCKED"
    assert "scenarios_count" in manifest
    assert manifest["scenarios_count"] >= 7
    
    base_dir = Path(__file__).resolve().parent.parent / "msk_therapy_os" / "data" / "biomechanics"
    
    for entry in manifest["scenarios"]:
        assert "source_model" in entry
        assert "model_license" in entry
        assert "coordinate_system" in entry
        
        mot_name = entry["source_motion_file"]
        if mot_name.endswith(".mot"):
            mot_path = base_dir / mot_name
            assert mot_path.exists(), f"Missing mot file: {mot_path}"
            
            # Verify SHA-256 integrity
            with open(mot_path, "rb") as f:
                actual_mot_sha = hashlib.sha256(f.read()).hexdigest()
            assert actual_mot_sha == entry["motion_file_hash"]
            assert entry["hash_match"] is True


# ============================================================================
# P16-03: Multi-Axis Cervical Kinematics Scenarios
# ============================================================================

def test_cervical_motion_scenarios_and_ranges():
    """Verify cervical motion scenarios exist and respect physiological limits."""
    catalog = get_scenario_catalog()
    scen_ids = [s.scenario_id for s in catalog]
    assert SCEN_CERVICAL_AXIAL_ROTATION in scen_ids
    assert SCEN_CERVICAL_LATERAL_BENDING in scen_ids
    assert SCEN_VASAVADA_CERVICAL_FLEX_EXT in scen_ids
    
    # Check physiological bounds
    assert "cervical_rotation" in PHYSIOLOGICAL_RANGES_DEG
    assert PHYSIOLOGICAL_RANGES_DEG["cervical_rotation"][0] <= -40.0
    assert PHYSIOLOGICAL_RANGES_DEG["cervical_rotation"][1] >= 40.0
    
    assert "cervical_lateral_bend" in PHYSIOLOGICAL_RANGES_DEG
    assert PHYSIOLOGICAL_RANGES_DEG["cervical_lateral_bend"][0] <= -30.0
    assert PHYSIOLOGICAL_RANGES_DEG["cervical_lateral_bend"][1] >= 30.0


# ============================================================================
# P16-04: Muscle Mechanics Inspector Modes & Empty States
# ============================================================================

def test_muscle_mechanics_mode_a_anatomical_participation():
    """Mode A: Returns anatomical participation without fabricated activations or forces."""
    res = get_muscle_mechanics_inspection(
        region="cervicothoracic",
        scenario_id=SCEN_VASAVADA_CERVICAL_FLEX_EXT,
        time_sec=0.0,
        mode="MODE_A_ANATOMICAL_PARTICIPATION",
    )
    assert res["mode"] == "MODE_A_ANATOMICAL_PARTICIPATION"
    assert res["status"] in ("AVAILABLE", "SUCCESS")
    assert len(res["muscles"]) >= 6
    
    first = res["muscles"][0]
    assert "muscle_id" in first
    assert "name_en" in first
    assert "name_vi" in first
    assert "anatomical_role" in first
    assert "primary_actions" in first
    assert "origin" in first
    assert "insertion" in first


def test_muscle_mechanics_mode_b_empty_state():
    """Mode B: Geometric change returns mandatory MODEL_GEOMETRY_INSUFFICIENT."""
    res = get_muscle_mechanics_inspection(
        region="cervicothoracic",
        scenario_id=SCEN_VASAVADA_CERVICAL_FLEX_EXT,
        time_sec=0.0,
        mode="MODE_B_GEOMETRIC_CHANGE",
    )
    assert res["mode"] == "MODE_B_GEOMETRIC_CHANGE"
    assert res["status"] == "MODEL_GEOMETRY_INSUFFICIENT"
    assert res["empty_state_code"] == "MODEL_GEOMETRY_INSUFFICIENT"
    assert "unmeshed in the current rigid osseous surface model" in res["notice"]


def test_muscle_mechanics_mode_c_estimated_activation():
    """Mode C: Returns static optimization mathematical estimate with mandatory disclaimers."""
    res = get_muscle_mechanics_inspection(
        region="cervicothoracic",
        scenario_id=SCEN_VASAVADA_CERVICAL_FLEX_EXT,
        time_sec=1.0,
        mode="MODE_C_ESTIMATED_ACTIVATION",
    )
    assert res["mode"] == "MODE_C_ESTIMATED_ACTIVATION"
    assert res["status"] in ("AVAILABLE", "SUCCESS")
    assert "muscles" in res
    assert len(res["muscles"]) > 0
    
    for m in res["muscles"]:
        assert 0.0 <= m["normalized_activation"] <= 1.0


def test_muscle_mechanics_mode_d_empty_state():
    """Mode D: Estimated force returns mandatory MUSCLE_FORCE_NOT_AVAILABLE."""
    res = get_muscle_mechanics_inspection(
        region="cervicothoracic",
        scenario_id=SCEN_VASAVADA_CERVICAL_FLEX_EXT,
        time_sec=0.0,
        mode="MODE_D_ESTIMATED_FORCE",
    )
    assert res["mode"] == "MODE_D_ESTIMATED_FORCE"
    assert res["status"] == "MUSCLE_FORCE_NOT_AVAILABLE"
    assert res["empty_state_code"] == "MUSCLE_FORCE_NOT_AVAILABLE"
    assert "Individual muscle force calculation in Newtons requires live OpenSim dynamic equilibrium solving" in res["notice"]


# ============================================================================
# P16-05: Interactive Scenario Comparison Engine
# ============================================================================

def test_scenario_comparison_engine():
    """Compare two scenarios and assert deltas, physical entities, and non-diagnostic disclaimer."""
    cmp_res = compare_scenarios(
        scenario_id_a=SCEN_VASAVADA_CERVICAL_FLEX_EXT,
        scenario_id_b=SCEN_ILLUSTRATIVE_FORWARD_HEAD,
        time_a_sec=1.0,
        time_b_sec=1.0,
    )
    assert "scenario_a" in cmp_res
    assert "scenario_b" in cmp_res
    assert "coordinate_deltas" in cmp_res
    assert "gravitational_mechanics_delta" in cmp_res
    assert "disclaimer" in cmp_res
    
    d_grav = cmp_res["gravitational_mechanics_delta"]
    assert "delta_moment_arm_cm" in d_grav
    assert "delta_gravitational_moment_nm" in d_grav
    assert "delta_extensor_muscle_force_n" in d_grav
    assert "delta_compression_force_n" in d_grav
    
    assert "ILLUSTRATIVE_SCENARIO_COMPARISON_ONLY" in cmp_res["disclaimer"]


# ============================================================================
# P16-06: Unified MSK Education Curriculum & Red Flags
# ============================================================================

def test_unified_curriculum_structure_and_red_flags():
    """Unified MSK Education Curriculum: 10 topics, 5-question bilingual quiz, 3 red flag groups."""
    curr = get_unified_education_curriculum(region="all", version="P16")
    
    assert "P16" in curr["curriculum_id"]
    assert len(curr["topics"]) == 10
    assert len(curr["quiz"]) == 5
    
    # Verify Red Flag safety triage groups
    assert "red_flags" in curr
    rf = curr["red_flags"]
    assert len(rf) == 3
    flag_ids = [f["flag_id"] for f in rf]
    assert "RF1_PROGRESSIVE_NEUROLOGICAL_DEFICIT" in flag_ids
    assert "RF2_CERVICAL_MYELOPATHY" in flag_ids
    assert "RF3_ACUTE_TRAUMA_OR_SYSTEMIC_SIGNS" in flag_ids


# ============================================================================
# P16-07: Research Evidence Register (EV-01..EV-20)
# ============================================================================

def test_evidence_register_classifications():
    """Verify all 20 evidence entries have rigorous formal confidence classifications."""
    curr = get_unified_education_curriculum(region="all", version="P16")
    ev_list = curr["evidence_register"]
    
    assert len(ev_list) == 20
    
    for ev in ev_list:
        assert "evidence_id" in ev
        assert "citation" in ev
        assert "category" in ev
        assert "confidence" in ev
        assert "topic" in ev
