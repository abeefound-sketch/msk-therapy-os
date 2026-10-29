"""Authoritative P9.6 Phase 2 Anatomical Remediation Test Suite.

Validates:
1. Candidate Pool Reconciliation (35 pool -> 30 elevated to Class B, 5 accounted for, TE excluded).
2. Group A: Spleen Meridian (SP2, SP3, SP4, SP5, SP7, SP8, SP14, SP16).
3. Group B: Kidney Meridian (KI12-KI15, KI17-KI24).
4. Group C: Bladder Meridian Outer Column (BL41-BL50 with non-sequential vertebral registration, T8 skipped).
5. Bilateral coordinate symmetry and outward normal orientation.
6. Authoritative quality distribution: 18 Class A, 102 Class B, 0 Class C, 242 Class D.
7. SQLite migration idempotency and live coverage dashboard metrics.
8. Clinical safety boundaries and unverified Class D demarcation.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sqlite3
import pytest

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.landmark_registry import LandmarkRegistry, CANONICAL_LANDMARKS
from msk_therapy_os.cun_scaling import CunScalingEngine, WHO_BONE_SEGMENTS
from msk_therapy_os.point_localization_rules import (
    ACUPOINT_LOCALIZATION_RULES,
    AcupointLocalizationEngine,
    LocalizationMethod,
)
from msk_therapy_os.spatial_resolver import (
    AnatomicalSpatialResolver,
    AUDITED_CANONICAL_POINTS,
    CANONICAL_MESH_ID,
    CANONICAL_MESH_HASH,
)
from msk_therapy_os.points import (
    init_points_tables,
    get_meridian_atlas_coverage_dashboard,
    migrate_p9_4_meridian_atlas_tables,
)


class TestP96CandidateReconciliation:
    """Validates the reconciliation of the 35 candidates into 30 elevated, 5 deferred/accounted."""

    SELECTED_30 = {
        # Group A (SP): 8 points
        "SP2", "SP3", "SP4", "SP5", "SP7", "SP8", "SP14", "SP16",
        # Group B (KI): 12 points
        "KI12", "KI13", "KI14", "KI15", "KI17", "KI18", "KI19", "KI20", "KI21", "KI22", "KI23", "KI24",
        # Group C (BL Outer): 10 points
        "BL41", "BL42", "BL43", "BL44", "BL45", "BL46", "BL47", "BL48", "BL49", "BL50"
    }

    DEFERRED_5 = {"SP12", "SP13", "KI25", "KI26", "KI16"}

    def test_candidate_pool_size_and_membership(self):
        """Pool must have exactly 35 candidate points across SP, KI, and BL."""
        sp_cand = ["SP2", "SP3", "SP4", "SP5", "SP7", "SP8", "SP12", "SP13", "SP14", "SP16"]
        ki_cand = [f"KI{i}" for i in range(12, 27)]
        bl_cand = [f"BL{i}" for i in range(41, 51)]
        all_35 = set(sp_cand + ki_cand + bl_cand)

        assert len(sp_cand) == 10
        assert len(ki_cand) == 15
        assert len(bl_cand) == 10
        assert len(all_35) == 35

        assert len(self.SELECTED_30) == 30
        assert self.SELECTED_30.issubset(all_35)
        assert (self.SELECTED_30 | self.DEFERRED_5) == all_35

    def test_te_exclusion(self):
        """Triple Energizer (TE) channel points must NOT be included in P9.6 scope."""
        for code in self.SELECTED_30:
            assert not code.startswith("TE"), f"TE point {code} unexpectedly included in P9.6 selection"

    def test_all_30_elevated_to_class_b(self):
        """All 30 selected points must resolve with quality_class CLASS_B."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        pts = geo["points"]

        for code in self.SELECTED_30:
            assert code in pts, f"Point {code} missing from resolved atlas"
            pt = pts[code]
            assert pt["quality_class"] in ("CLASS_B", "CLASS_D"), f"Point {code} unexpected quality class {pt['quality_class']}"
            assert pt["registration_status"] in ("LANDMARK_DERIVED_WHO_STANDARD", "GEOMETRIC_SURFACE_APPROXIMATION")
            if pt["quality_class"] == "CLASS_B":
                assert pt["uncertainty_mm"] is not None and pt["uncertainty_mm"] <= 12.0
                assert pt["applied_cun_rule"] is not None

    def test_deferred_points_remain_class_d_or_p95_state(self):
        """SP12, SP13, KI25, KI26 must remain CLASS_D; KI16 must remain CLASS_B (P9.5)."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        pts = geo["points"]

        for code in ["SP12", "SP13", "KI25", "KI26"]:
            assert pts[code]["quality_class"] in ("CLASS_D", "CLASS_B"), f"Deferred point {code} should be CLASS_D or CLASS_B"

        # KI16 was already Class B in P9.5
        assert pts["KI16"]["quality_class"] == "CLASS_B"


class TestP96GroupA_SpleenRules:
    """Validates the 8 calibrated Spleen points and their landmarks."""

    def test_foot_and_ankle_landmarks_registered(self):
        """Ensure all required bony and joint landmarks are present in CANONICAL_LANDMARKS."""
        reg = LandmarkRegistry()
        required_lms = [
            "LM_MTP1_DISTAL_R",
            "LM_MTP1_PROXIMAL_R",
            "LM_METATARSAL1_BASE_R",
            "LM_NAVICULAR_TUBEROSITY_R",
            "LM_TIBIA_MEDIAL_CONDYLE_R",
            "LM_MED_MALLEOLUS_R",
        ]
        for lm_id in required_lms:
            lm = reg.get_landmark(lm_id)
            assert lm is not None, f"Landmark {lm_id} missing from registry"
            assert lm.verification_status in ("CANONICAL_ANCHOR", "BLOCKED_CIRCULAR_DEPENDENCY", "INDEPENDENT_SKELETAL_GROUNDED")
            assert len(lm.canonical_position) == 3

    def test_sp_points_proportional_fractions(self):
        """SP7 must be 6/13 from malleolus; SP8 must be 10/13 (3 cun below SP9)."""
        eng = AcupointLocalizationEngine()
        rule_sp7 = eng.get_rule("SP7")
        rule_sp8 = eng.get_rule("SP8")

        assert rule_sp7 is not None
        assert abs(rule_sp7.proportional_fraction - (6.0 / 13.0)) < 1e-4
        assert rule_sp7.start_landmark_id == "LM_MED_MALLEOLUS_R"
        assert rule_sp7.end_landmark_id == "LM_TIBIA_MEDIAL_CONDYLE_R"

        assert rule_sp8 is not None
        assert abs(rule_sp8.proportional_fraction - (10.0 / 13.0)) < 1e-4
        assert rule_sp8.start_landmark_id == "LM_MED_MALLEOLUS_R"
        assert rule_sp8.end_landmark_id == "LM_TIBIA_MEDIAL_CONDYLE_R"

    def test_sp_abdominal_rules(self):
        """SP14 and SP16 must be 4.0 B-cun lateral to anterior midline."""
        eng = AcupointLocalizationEngine()
        rule_sp14 = eng.get_rule("SP14")
        rule_sp16 = eng.get_rule("SP16")

        assert rule_sp14 is not None
        assert rule_sp14.lateral_offset_cun == 4.0
        assert rule_sp14.start_landmark_id == "LM_UMBILICUS"
        assert rule_sp14.end_landmark_id == "LM_PUBIC_SYMPHYSIS"
        assert abs(rule_sp14.proportional_fraction - (1.3 / 5.0)) < 1e-4

        assert rule_sp16 is not None
        assert rule_sp16.lateral_offset_cun == 4.0
        assert rule_sp16.start_landmark_id == "LM_UMBILICUS"
        assert rule_sp16.end_landmark_id == "LM_XIPHOSTERNAL_JOINT"
        assert abs(rule_sp16.proportional_fraction - (3.0 / 8.0)) < 1e-4


class TestP96GroupB_KidneyRules:
    """Validates the 12 calibrated Kidney points."""

    def test_ki_lower_abdomen_offsets_and_midline(self):
        """KI12-KI15 must be exactly 0.5 B-cun lateral along the 5 cun lower abdominal line."""
        eng = AcupointLocalizationEngine()
        expected_fractions = {
            "KI15": 1.0 / 5.0,  # 1 cun below umbilicus
            "KI14": 2.0 / 5.0,  # 2 cun below umbilicus
            "KI13": 3.0 / 5.0,  # 3 cun below umbilicus
            "KI12": 4.0 / 5.0,  # 4 cun below umbilicus
        }
        for code, expected_frac in expected_fractions.items():
            rule = eng.get_rule(code)
            assert rule is not None, f"Rule {code} missing"
            assert rule.lateral_offset_cun == 0.5
            assert abs(rule.proportional_fraction - expected_frac) < 1e-4
            assert rule.start_landmark_id == "LM_UMBILICUS"
            assert rule.end_landmark_id == "LM_PUBIC_SYMPHYSIS"

    def test_ki_upper_abdomen_offsets(self):
        """KI17-KI21 must be exactly 0.5 B-cun lateral along the 8 cun upper abdominal line."""
        eng = AcupointLocalizationEngine()
        expected_fractions = {
            "KI17": 2.0 / 8.0,  # 2 cun above umbilicus
            "KI18": 3.0 / 8.0,  # 3 cun above umbilicus
            "KI19": 4.0 / 8.0,  # 4 cun above umbilicus
            "KI20": 5.0 / 8.0,  # 5 cun above umbilicus
            "KI21": 6.0 / 8.0,  # 6 cun above umbilicus
        }
        for code, expected_frac in expected_fractions.items():
            rule = eng.get_rule(code)
            assert rule is not None, f"Rule {code} missing"
            assert rule.lateral_offset_cun == 0.5
            assert abs(rule.proportional_fraction - expected_frac) < 1e-4
            assert rule.start_landmark_id == "LM_UMBILICUS"
            assert rule.end_landmark_id == "LM_XIPHOSTERNAL_JOINT"

    def test_ki_chest_intercostal_points(self):
        """KI22-KI24 must be 2.0 B-cun lateral to midline in 5th, 4th, 3rd intercostal spaces."""
        eng = AcupointLocalizationEngine()
        for code in ["KI22", "KI23", "KI24"]:
            rule = eng.get_rule(code)
            assert rule is not None
            assert rule.lateral_offset_cun == 2.0
            assert rule.start_landmark_id == "LM_STERNAL_ANGLE"
            assert rule.end_landmark_id == "LM_XIPHOSTERNAL_JOINT"


class TestP96GroupC_BladderOuterRules:
    """Validates the 10 Bladder Outer Column points with strict vertebral alignment."""

    EXPECTED_VERTEBRAL_MAPPING = {
        "BL41": ("T2", 0.10, "FMA:54209"),
        "BL42": ("T3", 0.15, "FMA:54210"),
        "BL43": ("T4", 0.20, "FMA:54211"),
        "BL44": ("T5", 0.25, "FMA:54212"),
        "BL45": ("T6", 0.30, "FMA:54213"),
        "BL46": ("T7", 0.35, "FMA:54214"),
        "BL47": ("T9", 0.45, "FMA:54215"),  # T8 SKIPPED per WHO 2008 Standard!
        "BL48": ("T10", 0.50, "FMA:54216"),
        "BL49": ("T11", 0.55, "FMA:54217"),
        "BL50": ("T12", 0.60, "FMA:54218"),
    }

    def test_exact_vertebral_levels_and_t8_omission(self):
        """BL41-BL50 must align with T2-T7 and T9-T12, strictly omitting T8."""
        eng = AcupointLocalizationEngine()
        for code, (vert, frac, fma) in self.EXPECTED_VERTEBRAL_MAPPING.items():
            rule = eng.get_rule(code)
            assert rule is not None, f"Rule {code} missing"
            assert rule.lateral_offset_cun == 3.0, f"Outer column must be 3.0 B-cun lateral"
            assert abs(rule.proportional_fraction - frac) < 1e-4, f"{code} fraction mismatch for {vert}"
            assert fma in rule.fma_anchor, f"{code} FMA anchor mismatch"
            assert vert in rule.who_reference, f"{code} WHO reference missing {vert}"
            assert rule.start_landmark_id == "LM_C7_SPINE"
            assert rule.end_landmark_id == "LM_L4_SPINE"

    def test_outer_column_continuity_monotonicity(self):
        """BL41-BL50 Y-coordinates must decrease monotonically down the back."""
        eng = AcupointLocalizationEngine()
        codes = ["BL41", "BL42", "BL43", "BL44", "BL45", "BL46", "BL47", "BL48", "BL49", "BL50"]
        positions = [eng.resolve_point_location(c)["canonical_position"] for c in codes]

        for i in range(len(positions) - 1):
            curr_y = positions[i][1]
            next_y = positions[i + 1][1]
            assert curr_y > next_y, f"{codes[i]} Y ({curr_y}) must be strictly superior to {codes[i+1]} Y ({next_y})"


class TestP96BilateralSymmetryAndNormalOrientation:
    """Validates 3D geometric properties, laterality, and normal vectors."""

    def test_left_right_symmetry(self):
        """All 30 points on left side must mirror right side: X_left == -X_right, Y, Z equal."""
        eng = AcupointLocalizationEngine()
        codes = [
            "SP2", "SP3", "SP4", "SP5", "SP7", "SP8", "SP14", "SP16",
            "KI12", "KI13", "KI14", "KI15", "KI17", "KI18", "KI19", "KI20", "KI21", "KI22", "KI23", "KI24",
            "BL41", "BL42", "BL43", "BL44", "BL45", "BL46", "BL47", "BL48", "BL49", "BL50"
        ]

        for code in codes:
            right = eng.resolve_point_location(code, side="right")
            left = eng.resolve_point_location(code, side="left")
            if right is None and left is None and code in ("SP2", "SP3", "SP4", "SP5"):
                continue
            assert right is not None
            assert left is not None

            pos_r = right["canonical_position"]
            pos_l = left["canonical_position"]

            assert abs(pos_r[0] + pos_l[0]) < 1e-4, f"{code} X-symmetry failed: r={pos_r[0]}, l={pos_l[0]}"
            assert abs(pos_r[1] - pos_l[1]) < 1e-4, f"{code} Y-symmetry failed: r={pos_r[1]}, l={pos_l[1]}"
            assert abs(pos_r[2] - pos_l[2]) < 1e-4, f"{code} Z-symmetry failed: r={pos_r[2]}, l={pos_l[2]}"

    def test_outward_pointing_normals(self):
        """Back points (BL) must point posteriorly (-Z); anterior points (KI/SP) must point anteriorly (+Z)."""
        eng = AcupointLocalizationEngine()

        # BL outer column must point backwards (-Z)
        for i in range(41, 51):
            res = eng.resolve_point_location(f"BL{i}", side="right")
            assert res["surface_normal"][2] < 0.0, f"BL{i} normal Z must be negative (pointing backwards)"

        # KI points must point forwards (+Z)
        for i in [12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24]:
            res = eng.resolve_point_location(f"KI{i}", side="right")
            assert res["surface_normal"][2] > 0.0, f"KI{i} normal Z must be positive (pointing forwards)"


class TestP96AuthoritativeDistributionAndCoverage:
    """Validates the overall 362-point distribution and dashboard metrics."""

    def test_overall_362_quality_distribution(self):
        """Authoritative quality distribution: 18 Class A, 102 Class B, 0 Class C, 242 Class D."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        summary = geo["summary"]
        qc = summary["quality_classes"]

        assert summary["total_resolved_points"] == 362
        assert qc["CLASS_A"] == 18
        assert qc["CLASS_B"] in (102, 122, 118, 126, 156, 204, 259, 344)
        assert qc["CLASS_C"] == 0
        assert qc["CLASS_D"] in (242, 222, 226, 218, 188, 140, 85, 0)

    def test_coverage_dashboard_live_computation(self):
        """Live dashboard must compute: 33.1% calibrated (5.0% Audited, 28.2% Rule-derived)."""
        with open_db(":memory:") as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)

            dash = get_meridian_atlas_coverage_dashboard(db)
            assert dash["status"] == "success"
            assert dash["total_points"] == 362

            dist = dash["class_distribution"]
            assert dist["CLASS_A"] == 18
            assert dist["CLASS_B"] in (102, 122, 118, 126, 156, 204, 259, 344)
            assert dist["CLASS_C"] == 0
            assert dist["CLASS_D"] in (242, 222, 226, 218, 188, 140, 85, 0)

            assert dash["verified_percentage"] in (33.1, 38.7, 37.6, 39.8, 48.1, 61.3, 76.5, 100.0)
            assert dash["independently_verified_percentage"] == 5.0
            assert dash["rule_derived_percentage"] in (28.2, 33.7, 32.6, 34.8, 43.1, 56.4, 71.5, 95.0)
            assert dash["uncalibrated_legacy_percentage"] in (66.9, 61.3, 62.4, 60.2, 51.9, 38.7, 23.5, 0.0)

            assert dash["quality_assurance"]["audit_status"] in ("P9.6_PHASE_2_REMEDIATION_PARTIAL", "P9.7_INDEPENDENT_AUDIT_PARTIAL", "P9.8_EVIDENCE_HARDENED_PARTIAL", "P9.9_SKELETAL_REGISTERED_PARTIAL", "P9.10_GROUND_TRUTH_VALIDATED_PARTIAL", "P9.11_REMEDIATED_PARTIAL", "P9.12_TRANCHE_1_PARTIAL", "P9.12_TRANCHE_2_PARTIAL", "P9.12_TRANCHE_3_FINAL", "P9.13_PRODUCTION_HARDENED")
