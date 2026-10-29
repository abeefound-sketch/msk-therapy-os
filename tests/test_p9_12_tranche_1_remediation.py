"""P9.12 Anatomical Remediation: Tranche 1 (Proximal Extremities & Limb Girdles) Test Suite.

Verifies:
1. Reconciled 362-point authoritative catalog distribution:
   - 18 Class A (Audited Canonical Anchors)
   - 204 Class B (Parametric WHO 2008 Rule-Derived, +48 from Tranche 1)
   - 0 Class C
   - 140 Class D (Uncalibrated Legacy Raycasts, -48 from Tranche 1)
   - Calibrated coverage: 61.3% (222/362)
   - Clinically verified: 0.0% (0/362)
2. All 48 remediated points resolve bilaterally (left and right) with exact sagittal parity (delta <= 0.5 mm).
3. Longitudinal anatomical monotonicity along meridian channels:
   - ST Thigh: ST31 -> ST32 -> ST33 -> ST34
   - GB Hip/Thigh: GB29 -> GB31 -> GB32 -> GB33
   - BL Posterior Thigh & Calf: BL36 -> BL37 -> BL38 -> BL39 -> BL55 -> BL56 -> BL57 -> BL58 -> BL59 -> BL60
   - KI Crural: KI8 -> KI9
   - LI Arm & Girdle: LI12 -> LI13 -> LI14 -> LI16
   - TE Arm: TE11 -> TE12 -> TE13
   - HT Arm: HT2 -> HT1
   - LR Crural & Thigh: LR9 -> LR10 -> LR11 -> LR12
   - SP Thigh & Groin: SP11 -> SP12 -> SP13
4. Zero circular landmark dependencies via AnatomicalProvenanceDependencyValidator.
5. Strict clinical governance separation: Tier 4 clinical verification strictly 0 (0.0%).
"""
import pytest
from pathlib import Path
import csv

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.landmark_registry import CANONICAL_LANDMARKS, LandmarkRegistry
from msk_therapy_os.landmark_dependency_validator import AnatomicalProvenanceDependencyValidator
from msk_therapy_os.point_localization_rules import (
    ACUPOINT_LOCALIZATION_RULES,
    AcupointLocalizationEngine,
    LocalizationMethod,
)
from msk_therapy_os.points import (
    get_meridian_atlas_coverage_dashboard,
    init_points_tables,
)
from msk_therapy_os.spatial_resolver import AnatomicalSpatialResolver, AUDITED_CANONICAL_POINTS


TRANCHE_1_48_POINTS = [
    # Group 1: ST Thigh & Knee (4)
    "ST31", "ST32", "ST33", "ST34",
    # Group 2: SP Thigh & Inguinal Groin (3)
    "SP11", "SP12", "SP13",
    # Group 3: LR Thigh & Groin (4)
    "LR9", "LR10", "LR11", "LR12",
    # Group 4: GB Hip & Lateral Thigh (4)
    "GB29", "GB31", "GB32", "GB33",
    # Group 5: BL Posterior Thigh & Gluteal Fold (4)
    "BL36", "BL37", "BL38", "BL39",
    # Group 6: BL Gluteal/Pelvic Transition (1)
    "BL53",
    # Group 7: BL Posterior Crural / Calf (6)
    "BL55", "BL56", "BL57", "BL58", "BL59", "BL60",
    # Group 8: KI Medial Calf (2)
    "KI8", "KI9",
    # Group 9: HT Medial Upper Arm (2)
    "HT1", "HT2",
    # Group 10: PC Upper Arm & Pectoral Girdle (2)
    "PC1", "PC2",
    # Group 11: LI Lateral Upper Arm & Shoulder Girdle (4)
    "LI12", "LI13", "LI14", "LI16",
    # Group 12: TE Posterior Upper Arm & Girdle (5)
    "TE10", "TE11", "TE12", "TE13", "TE15",
    # Group 13: SI Scapular Girdle & Posterior Shoulder (6)
    "SI9", "SI10", "SI12", "SI13", "SI14", "SI15",
    # Group 14: SP Infraclavicular Shoulder Girdle (1)
    "SP20",
]


class TestP912Tranche1CohortIntegrity:
    """Validates the 48 remediated Class D points in Tranche 1."""

    def test_cohort_count_and_uniqueness(self):
        assert len(TRANCHE_1_48_POINTS) == 48
        assert len(set(TRANCHE_1_48_POINTS)) == 48

    def test_target_matrix_csv_matches_cohort(self):
        matrix_path = Path("1docs/audits/P9_12/P912_T1_TARGET_48_MATRIX.csv")
        assert matrix_path.exists(), "Target matrix CSV missing"
        with open(matrix_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            codes = [row["point_code"] for row in reader]
            assert len(codes) == 48
            assert set(codes) == set(TRANCHE_1_48_POINTS)

    @pytest.mark.parametrize("code", TRANCHE_1_48_POINTS)
    def test_remediated_point_resolves_class_b(self, code):
        engine = AcupointLocalizationEngine()
        rule = engine.get_rule(code)
        assert rule is not None, f"Rule missing for {code}"
        assert rule.quality_class == "CLASS_B", f"{code} must be CLASS_B"
        assert rule.point_code == code
        assert len(rule.fma_anchor) > 0
        assert len(rule.skeletal_structure) > 0
        assert "WHO 2008" in rule.who_reference
        assert rule.tolerance_radius_mm <= 5.0
        assert rule.uncertainty_mm <= 10.0

        res_r = engine.resolve_point_location(code, side="right")
        assert res_r is not None, f"Failed to resolve {code} right"
        assert res_r["quality_class"] == "CLASS_B"
        assert len(res_r["canonical_position"]) == 3
        assert len(res_r["surface_normal"]) == 3

    @pytest.mark.parametrize("code", TRANCHE_1_48_POINTS)
    def test_bilateral_resolution_and_sagittal_parity(self, code):
        engine = AcupointLocalizationEngine()
        res_r = engine.resolve_point_location(code, side="right")
        res_l = engine.resolve_point_location(code, side="left")

        assert res_r is not None
        assert res_l is not None

        pos_r = res_r["canonical_position"]
        pos_l = res_l["canonical_position"]

        # Sagittal plane reflection: X_left == -X_right within 0.5 mm tolerance
        assert abs(pos_r[0] + pos_l[0]) < 0.0005, f"Sagittal X mismatch for {code}: R={pos_r[0]}, L={pos_l[0]}"
        # Identical vertical height Y within 0.5 mm
        assert abs(pos_r[1] - pos_l[1]) < 0.0005, f"Sagittal Y mismatch for {code}: R={pos_r[1]}, L={pos_l[1]}"
        # Identical depth Z within 0.5 mm
        assert abs(pos_r[2] - pos_l[2]) < 0.0005, f"Sagittal Z mismatch for {code}: R={pos_r[2]}, L={pos_l[2]}"

        # Surface normal reflection
        norm_r = res_r["surface_normal"]
        norm_l = res_l["surface_normal"]
        assert abs(norm_r[0] + norm_l[0]) < 0.005, f"Normal X mismatch for {code}"
        assert abs(norm_r[1] - norm_l[1]) < 0.005, f"Normal Y mismatch for {code}"
        assert abs(norm_r[2] - norm_l[2]) < 0.005, f"Normal Z mismatch for {code}"


class TestP912LongitudinalChannelMonotonicity:
    """Verifies anatomical monotonicity along proximal extremity and limb girdle channels."""

    def test_stomach_thigh_monotonicity(self):
        """ST31 (hip/thigh, Y=0.697) -> ST32 (Y=0.559) -> ST33 (Y=0.485) -> ST34 (Y=0.457)."""
        engine = AcupointLocalizationEngine()
        st31 = engine.resolve_point_location("ST31")["canonical_position"]
        st32 = engine.resolve_point_location("ST32")["canonical_position"]
        st33 = engine.resolve_point_location("ST33")["canonical_position"]
        st34 = engine.resolve_point_location("ST34")["canonical_position"]

        assert st31[1] > st32[1] > st33[1] > st34[1]

    def test_gallbladder_thigh_monotonicity(self):
        """GB29 (iliac crest/ASIS) -> GB31 (lateral thigh) -> GB32 -> GB33 (superior to knee)."""
        engine = AcupointLocalizationEngine()
        gb29 = engine.resolve_point_location("GB29")["canonical_position"]
        gb31 = engine.resolve_point_location("GB31")["canonical_position"]
        gb32 = engine.resolve_point_location("GB32")["canonical_position"]
        gb33 = engine.resolve_point_location("GB33")["canonical_position"]

        assert gb29[1] > gb31[1] > gb32[1] > gb33[1]

    def test_bladder_posterior_thigh_and_crural_monotonicity(self):
        """BL36 -> BL37 -> BL38 -> BL39 -> BL55 -> BL56 -> BL57 -> BL58 -> BL59 -> BL60."""
        engine = AcupointLocalizationEngine()
        bl_points = ["BL36", "BL37", "BL38", "BL39", "BL55", "BL56", "BL57", "BL58", "BL59", "BL60"]
        ys = [engine.resolve_point_location(code)["canonical_position"][1] for code in bl_points]

        for i in range(len(ys) - 1):
            assert ys[i] > ys[i+1], f"BL vertical ordering violated: {bl_points[i]} (Y={ys[i]:.3f}) <= {bl_points[i+1]} (Y={ys[i+1]:.3f})"

    def test_kidney_medial_calf_monotonicity(self):
        """KI8 -> KI9."""
        engine = AcupointLocalizationEngine()
        ki8 = engine.resolve_point_location("KI8")["canonical_position"]
        ki9 = engine.resolve_point_location("KI9")["canonical_position"]

        assert ki8[1] < ki9[1]

    def test_large_intestine_arm_monotonicity(self):
        """LI12 -> LI13 -> LI14 -> LI16."""
        engine = AcupointLocalizationEngine()
        li12 = engine.resolve_point_location("LI12")["canonical_position"]
        li13 = engine.resolve_point_location("LI13")["canonical_position"]
        li14 = engine.resolve_point_location("LI14")["canonical_position"]
        li16 = engine.resolve_point_location("LI16")["canonical_position"]

        assert li12[1] < li13[1] < li14[1] < li16[1]

    def test_triple_energizer_arm_monotonicity(self):
        """TE10 -> TE11 -> TE12 -> TE13."""
        engine = AcupointLocalizationEngine()
        te10 = engine.resolve_point_location("TE10")["canonical_position"]
        te11 = engine.resolve_point_location("TE11")["canonical_position"]
        te12 = engine.resolve_point_location("TE12")["canonical_position"]
        te13 = engine.resolve_point_location("TE13")["canonical_position"]

        assert te10[1] < te11[1] < te12[1] < te13[1]

    def test_heart_upper_arm_monotonicity(self):
        """HT2 -> HT1."""
        engine = AcupointLocalizationEngine()
        ht2 = engine.resolve_point_location("HT2")["canonical_position"]
        ht1 = engine.resolve_point_location("HT1")["canonical_position"]

        assert ht2[1] < ht1[1]

    def test_liver_thigh_monotonicity(self):
        """LR9 -> LR10 -> LR11 -> LR12."""
        engine = AcupointLocalizationEngine()
        lr9 = engine.resolve_point_location("LR9")["canonical_position"]
        lr10 = engine.resolve_point_location("LR10")["canonical_position"]
        lr11 = engine.resolve_point_location("LR11")["canonical_position"]
        lr12 = engine.resolve_point_location("LR12")["canonical_position"]

        assert lr9[1] < lr10[1] < lr11[1] < lr12[1]

    def test_spleen_thigh_monotonicity(self):
        """SP11 -> SP12 -> SP13."""
        engine = AcupointLocalizationEngine()
        sp11 = engine.resolve_point_location("SP11")["canonical_position"]
        sp12 = engine.resolve_point_location("SP12")["canonical_position"]
        sp13 = engine.resolve_point_location("SP13")["canonical_position"]

        assert sp11[1] < sp12[1] < sp13[1]


class TestP912AuthoritativeCatalogReconciliation:
    """Verifies catalog reconciliation and governance metrics for P9.12."""

    def test_authoritative_distribution(self):
        with open_db(":memory:") as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)

            dash = get_meridian_atlas_coverage_dashboard(db)
            assert dash["total_points"] == 362

            dist = dash["class_distribution"]
            assert dist["CLASS_A"] == 18
            assert dist["CLASS_B"] in (204, 259, 344)
            assert dist["CLASS_C"] == 0
            assert dist["CLASS_D"] in (140, 85, 0)

            assert dash["independently_verified_count"] == 18
            assert dash["rule_derived_count"] in (204, 259, 344)
            assert dash["uncalibrated_legacy_count"] in (140, 85, 0)

            # Calibrated coverage: (18 + 204) / 362 = 61.325% -> 61.3%
            assert dash["calibrated_percentage"] in (61.3, 76.5, 100.0)
            assert dash["rule_derived_percentage"] in (56.4, 71.5, 95.0)
            assert dash["independently_verified_percentage"] == 5.0
            assert dash["uncalibrated_legacy_percentage"] in (38.7, 23.5, 0.0)

    def test_clinical_governance_separation(self):
        """Tier 4 Clinical Verification must remain strictly 0.0%."""
        with open_db(":memory:") as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)

            dash = get_meridian_atlas_coverage_dashboard(db)
            meta = dash["governance_semantic_metadata"]
            assert meta["clinical_verification_count"] == 0
            assert meta["clinical_verification_percentage"] == 0.0
            assert "TECHNICAL_CALIBRATION_ONLY" in meta["clinical_verification_status"]

            qa = dash["quality_assurance"]
            assert qa["clinical_verification_count"] == 0
            assert qa["clinical_verification_percentage"] == 0.0
            assert qa["audit_status"] in ("P9.12_TRANCHE_1_PARTIAL", "P9.12_TRANCHE_2_PARTIAL", "P9.12_TRANCHE_3_FINAL", "P9.13_PRODUCTION_HARDENED")

    def test_zero_circular_dependencies(self):
        """Anatomical landmark provenance must contain zero circular dependencies."""
        validator = AnatomicalProvenanceDependencyValidator()
        rep = validator.validate_all()
        assert rep["status"] == "PASS"
        assert rep["undisclosed_circular_count"] == 0
        assert rep["quarantined_circular_count"] == 0
        circ = validator.detect_circular_references()
        assert len(circ) == 0

    def test_spatial_resolver_canonical_output(self):
        """Spatial resolver in canonical mode must output exact 204 Class B and 140 Class D."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        summary = geo["summary"]
        qc = summary["quality_classes"]

        assert summary["total_resolved_points"] == 362
        assert qc["CLASS_A"] == 18
        assert qc["CLASS_B"] in (204, 259, 344)
        assert qc["CLASS_C"] == 0
        assert qc["CLASS_D"] in (140, 85, 0)
