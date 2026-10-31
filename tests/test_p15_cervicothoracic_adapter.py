"""Tests for Milestone P15: Cervicothoracic Biomechanics & Forward Head Posture Adapter.

Verifies:
1. G14 and security invariants remain locked.
2. OpenSim parsing for cervical motion (.mot) and static optimization activations (.sto).
3. Craniovertebral Angle (CVA), gravitational moment arm, and extensor force calculations.
4. Janda's Upper Crossed Syndrome reciprocal inhibition modeling.
5. 8-stage bilingual curriculum, 4-question interactive quiz, and EV-09..16 evidence register.
6. Authentic BodyParts3D cervicothoracic skeleton GLB asset integrity.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
import pytest

from msk_therapy_os.biomechanics_adapter import (
    G14,
    CLINICAL_DEPTH_GUIDANCE_ALLOWED,
    RELEASE_SCOPE,
    CLINICAL_VALIDATION,
    OpenSimFormatParser,
    get_scenario_catalog,
    calculate_cervicothoracic_posture,
    get_cervicothoracic_curriculum,
    get_shoulder_education_curriculum,
    PHYSIOLOGICAL_RANGES_DEG,
)


def test_p15_invariants_and_constants():
    """Verify non-negotiable governance invariants are unchanged."""
    assert G14 == "BLOCKED_EXTERNAL_DATA"
    assert CLINICAL_DEPTH_GUIDANCE_ALLOWED is False
    assert RELEASE_SCOPE == "ENGINEERING_RESEARCH_ONLY"
    assert CLINICAL_VALIDATION == "NOT_ESTABLISHED"


def test_p15_physiological_cervical_ranges():
    """Verify cervical degrees of freedom are registered in physiological ranges."""
    assert "cervical_flexion" in PHYSIOLOGICAL_RANGES_DEG
    assert "lower_cervical_flex" in PHYSIOLOGICAL_RANGES_DEG
    assert "upper_cervical_flex" in PHYSIOLOGICAL_RANGES_DEG
    assert "cva_angle" in PHYSIOLOGICAL_RANGES_DEG
    assert PHYSIOLOGICAL_RANGES_DEG["cva_angle"] == (15.0, 80.0)


def test_p15_scenario_manifests_registered():
    """Verify Cervicothoracic scenarios exist in scenario catalog with valid files and hashes."""
    catalog = get_scenario_catalog()
    scen_ids = [s.scenario_id for s in catalog]
    assert "SCEN_VASAVADA_CERVICAL_FLEX_EXT" in scen_ids
    assert "SCEN_ILLUSTRATIVE_FORWARD_HEAD" in scen_ids

    vasavada_scen = next(s for s in catalog if s.scenario_id == "SCEN_VASAVADA_CERVICAL_FLEX_EXT")
    assert vasavada_scen.validation_level == "OPENSIM_MODEL_GENERATED"
    assert vasavada_scen.muscle_output_type == "ESTIMATED_ACTIVATION"
    assert "cervical_flexion" in vasavada_scen.joint_coordinate_names
    assert "lower_cervical_flex" in vasavada_scen.joint_coordinate_names

    fhp_scen = next(s for s in catalog if s.scenario_id == "SCEN_ILLUSTRATIVE_FORWARD_HEAD")
    assert fhp_scen.validation_level == "ILLUSTRATIVE"
    assert "cva_angle" in fhp_scen.joint_coordinate_names

    # Check file existence and sha256 checksums
    base_dir = Path("msk_therapy_os/data/biomechanics")
    for scen in [vasavada_scen, fhp_scen]:
        fpath = base_dir / scen.source_motion_file
        assert fpath.exists(), f"Motion file missing: {fpath}"
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
        assert actual_hash == scen.motion_file_hash, f"Hash mismatch for {scen.source_motion_file}"


def test_p15_vasavada_motion_and_sto_parsing():
    """Verify parsing of vasavada cervical motion (.mot) and static optimization (.sto)."""
    mot_path = "msk_therapy_os/data/biomechanics/vasavada_cervical_flexion_extension.mot"
    parsed_mot = OpenSimFormatParser.parse_file(mot_path)
    assert parsed_mot.n_rows == 21
    assert parsed_mot.n_columns == 8
    assert parsed_mot.in_degrees is True
    assert "cervical_flexion" in parsed_mot.headers
    assert "lower_cervical_flex" in parsed_mot.headers
    assert "upper_cervical_flex" in parsed_mot.headers
    assert "cva_angle" in parsed_mot.headers

    # Check timestamps strictly monotonic
    for i in range(1, len(parsed_mot.time)):
        assert parsed_mot.time[i] > parsed_mot.time[i - 1]

    # Verify sto activations
    sto_path = "msk_therapy_os/data/biomechanics/vasavada_cervical_flexion_extension.sto"
    parsed_sto = OpenSimFormatParser.parse_file(sto_path)
    assert parsed_sto.n_rows == 21
    assert parsed_sto.n_columns == 10
    assert parsed_sto.in_degrees is False
    assert "scm" in parsed_sto.headers
    assert "suboccipital" in parsed_sto.headers
    assert "levator" in parsed_sto.headers
    assert "longus_colli" in parsed_sto.headers

    # Check activations bounded in [0.0, 1.0]
    for ch in parsed_sto.headers[1:]:
        for val in parsed_sto.data[ch]:
            assert 0.0 <= val <= 1.0, f"Muscle activation out of bounds in channel {ch}: {val}"


def test_p15_illustrative_fhp_coupled_kinematics():
    """Verify coupled lower cervical flexion with upper cervical hyperextension in FHP."""
    mot_path = "msk_therapy_os/data/biomechanics/illustrative_forward_head_posture.mot"
    parsed = OpenSimFormatParser.parse_file(mot_path)

    # At t=0.0 (neutral posture)
    assert parsed.data["lower_cervical_flex"][0] == 0.0
    assert parsed.data["upper_cervical_flex"][0] == 0.0
    assert parsed.data["cva_angle"][0] == 54.0

    # At t=2.0 (forward head posture)
    assert parsed.data["lower_cervical_flex"][-1] == 26.0   # Lower cervical flexes forward
    assert parsed.data["upper_cervical_flex"][-1] == -18.0  # Upper cervical hyperextends backward
    assert parsed.data["cva_angle"][-1] == 32.0             # CVA drops significantly
    assert parsed.data["head_anterior_trans"][-1] == 50.0   # 50 mm anterior translation


def test_p15_illustrative_fhp_reciprocal_inhibition_sto():
    """Verify Janda's Upper Crossed Syndrome: hyperactive vs inhibited muscle pairs."""
    sto_path = "msk_therapy_os/data/biomechanics/illustrative_forward_head_posture.sto"
    parsed = OpenSimFormatParser.parse_file(sto_path)

    # Hypertonic / Facilitated muscles increase activation:
    suboccipital_initial = parsed.data["suboccipital"][0]
    suboccipital_final = parsed.data["suboccipital"][-1]
    assert suboccipital_final > suboccipital_initial * 3.0  # Massive hypertonicity

    levator_initial = parsed.data["levator"][0]
    levator_final = parsed.data["levator"][-1]
    assert levator_final > levator_initial * 3.0            # Levator scapulae eccentric overload

    trap_u_initial = parsed.data["trap_u"][0]
    trap_u_final = parsed.data["trap_u"][-1]
    assert trap_u_final > trap_u_initial * 3.0              # Upper trapezius spasm/holding

    # Inhibited muscles drop activation:
    longus_colli_initial = parsed.data["longus_colli"][0]
    longus_colli_final = parsed.data["longus_colli"][-1]
    assert longus_colli_final < longus_colli_initial * 0.25 # Deep neck flexors severely inhibited

    trap_l_initial = parsed.data["trap_l"][0]
    trap_l_final = parsed.data["trap_l"][-1]
    assert trap_l_final < trap_l_initial * 0.3              # Lower trapezius inhibited


def test_p15_cervicothoracic_posture_calculation():
    """Verify biomechanical calculation of CVA, moment arm, and extensor force."""
    # Neutral alignment
    res_neutral = calculate_cervicothoracic_posture(forward_head_mm=0.0, cva_deg=53.0)
    assert res_neutral["postural_level"] == "NORMAL_ALIGNMENT"
    assert res_neutral["head_moment_arm_cm"] == 2.9
    assert res_neutral["extensor_muscle_force_n"] > 35.0
    assert "FORWARD_HEAD_VARIATION != STRUCTURAL_DEFORMITY_DIAGNOSIS" in res_neutral["disclaimer"]

    # Marked forward head posture
    res_fhp = calculate_cervicothoracic_posture(forward_head_mm=45.0, cva_deg=33.0, rounded_shoulder_pct=75.0)
    assert res_fhp["postural_level"] == "MARKED_FORWARD_HEAD"
    assert res_fhp["head_moment_arm_cm"] > 6.0
    assert res_fhp["extensor_muscle_force_n"] > 90.0
    assert res_fhp["levator_scapulae_tension_index"] > 2.0
    assert res_fhp["facet_shear_stress_ratio"] > 2.0


def test_p15_cervicothoracic_curriculum_structure():
    """Verify 8 stages, 4 quiz questions, and EV-09..16 evidence items."""
    curriculum = get_cervicothoracic_curriculum(version="P15")
    assert curriculum["curriculum_id"] == "P15_CERVICOTHORACIC_BIOMECHANICS_STUDIO"
    assert curriculum["region"] == "cervicothoracic"
    assert len(curriculum["stages"]) == 8

    # Verify quiz
    assert "quiz" in curriculum
    assert len(curriculum["quiz"]) == 4
    for q in curriculum["quiz"]:
        assert q["correct_option"] in ("A", "B", "C")
        assert len(q["options_en"]) == 3
        assert len(q["options_vi"]) == 3
        assert len(q["explanation_en"]) > 20
        assert len(q["explanation_vi"]) > 20

    # Verify Evidence Register EV-09 to EV-16
    assert "evidence_register" in curriculum
    assert len(curriculum["evidence_register"]) == 8
    ev_ids = [e["evidence_id"] for e in curriculum["evidence_register"]]
    assert ev_ids == [f"EV-{i:02d}" for i in range(9, 17)]


def test_p15_cervicothoracic_skeleton_glb_asset():
    """Verify authentic BodyParts3D cervicothoracic skeleton GLB file integrity."""
    glb_path = Path("msk_therapy_os/static/education/models/cervicothoracic_skeleton.glb")
    assert glb_path.exists(), "cervicothoracic_skeleton.glb does not exist"
    assert glb_path.stat().st_size > 1_000_000, "GLB size is suspiciously small"
    assert glb_path.stat().st_size < 3_000_000, "GLB size exceeds 3MB limit"

    # Inspect glTF header and nodes
    data = glb_path.read_bytes()
    magic, ver, length = struct.unpack("<4sII", data[:12])
    assert magic == b"glTF"
    assert ver == 2
    assert length == len(data)

    c_len, c_type = struct.unpack("<II", data[12:20])
    gltf_json = json.loads(data[20:20 + c_len])

    node_names = [n["name"] for n in gltf_json["nodes"]]
    expected_nodes = [
        "Thorax", "Cervical_Lower", "Cervical_Upper", "Skull_Cranium",
        "Clavicle_R", "Scapula_R", "Humerus_R", "Levator_Scapulae", "Suboccipital_Muscles"
    ]
    for en in expected_nodes:
        assert en in node_names, f"Node {en} missing from cervicothoracic_skeleton.glb"

    mat_names = [m["name"] for m in gltf_json["materials"]]
    assert "BoneMaterial" in mat_names
    assert "LevatorMaterial" in mat_names
    assert "SuboccipitalMaterial" in mat_names


def test_p15_backward_compatibility_p13_and_p14():
    """Verify that get_shoulder_education_curriculum still produces both P13 and P14 curricula."""
    p13_curr = get_shoulder_education_curriculum(version="P13")
    assert len(p13_curr["stages"]) == 6
    assert p13_curr["curriculum_id"] == "P13_SHOULDER_POSTURE_MECHANICS"

    p14_curr = get_shoulder_education_curriculum(version="P14")
    assert len(p14_curr["stages"]) == 8
    assert p14_curr["curriculum_id"] == "P14_SHOULDER_BIOMECHANICS_STUDIO"
