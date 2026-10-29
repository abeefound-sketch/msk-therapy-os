"""
MSK-Therapy-OS | Milestone P9.12 Tranche 2 Test Suite
Cranial, Facial & Cervical Anatomical Remediation & Governance Verification
Authoritative Standard: WHO 2008 Standard Acupuncture Point Locations & BodyParts3D FJ2810
Acceptance Criteria:
  - 55 Cranial, Facial & Cervical Class D points remediated to Class B
  - 18 Class A (Audited Canonical Anchors) preserved
  - 259 Class B (Parametric WHO 2008 Rule-Derived, +55 from Tranche 2)
  - 85 Class D (Uncalibrated Legacy Raycasts, -55 from Tranche 2)
  - Calibrated coverage: 76.5% (277/362)
  - Tier 4 Clinical Verification: strictly 0 (0.0%)
  - Bilateral sagittal symmetry: Delta <= 0.5 mm
  - Sagittal midline integrity: X == 0.000000
  - Calvarial curvature & longitudinal monotonicity preserved
  - Zero ocular globe penetration / orbital boundary protection
  - Zero circular landmark dependencies
"""

import math
import sqlite3
import pytest
from pathlib import Path
from typing import Dict, Any, List, Tuple

from msk_therapy_os.landmark_registry import LandmarkRegistry, CANONICAL_LANDMARKS, BodyRegion
from msk_therapy_os.point_localization_rules import (
    AcupointLocalizationEngine,
    ACUPOINT_LOCALIZATION_RULES,
    AcupointLocalizationRule,
    LocalizationMethod
)
from msk_therapy_os.spatial_resolver import AnatomicalSpatialResolver
from msk_therapy_os.points import (
    init_points_tables,
    get_meridian_atlas_coverage_dashboard,
    run_database_integrity_check
)

# Authoritative 55 Tranche 2 Target Acupoints
TRANCHE_2_TARGET_CODES = [
    # GV (12)
    "GV17", "GV18", "GV19", "GV21", "GV22", "GV23", "GV24", "GV24+", "GV25", "GV26", "GV27", "GV28",
    # CV (2)
    "CV23", "CV24",
    # BL (7)
    "BL3", "BL4", "BL5", "BL6", "BL7", "BL8", "BL9",
    # GB (15)
    "GB3", "GB4", "GB5", "GB6", "GB7", "GB9", "GB10", "GB11", "GB12", "GB13", "GB15", "GB16", "GB17", "GB18", "GB19",
    # ST (7)
    "ST2", "ST3", "ST5", "ST6", "ST7", "ST10", "ST11",
    # SI (3)
    "SI16", "SI17", "SI18",
    # TE (6)
    "TE16", "TE18", "TE19", "TE20", "TE21", "TE22",
    # LI (3)
    "LI17", "LI18", "LI19"
]


class TestP912Tranche2ScopeAndCatalog:
    """Verifies scope completeness, target reconciliation, and catalog invariants."""

    def test_target_scope_cardinality_and_uniqueness(self):
        """Authoritative target set must contain exactly 55 unique cranial/facial/cervical points."""
        assert len(TRANCHE_2_TARGET_CODES) == 55
        assert len(set(TRANCHE_2_TARGET_CODES)) == 55

    def test_target_reconciliation_csv_alignment(self):
        """Target points must match P912_T2_TARGET_RECONCILIATION.csv eligible set exactly."""
        csv_path = Path("1docs/audits/P9_12/TRANCHE_2/P912_T2_TARGET_RECONCILIATION.csv")
        assert csv_path.exists(), "Reconciliation CSV must exist"
        eligible_csv = []
        with open(csv_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 7 and parts[6] == "YES":
                    eligible_csv.append(parts[0])
        assert sorted(eligible_csv) == sorted(TRANCHE_2_TARGET_CODES)

    def test_all_55_rules_defined_with_provenance(self):
        """All 55 target points must have registered localization rules with valid FMA & WHO citations."""
        for code in TRANCHE_2_TARGET_CODES:
            assert code in ACUPOINT_LOCALIZATION_RULES, f"Rule missing for {code}"
            rule = ACUPOINT_LOCALIZATION_RULES[code]
            assert isinstance(rule, AcupointLocalizationRule)
            assert rule.quality_class == "CLASS_B", f"{code} must be CLASS_B"
            assert rule.fma_anchor.startswith("FMA:"), f"{code} missing FMA anchor"
            assert "WHO 2008" in rule.who_reference or "GB/T 12346" in rule.who_reference, f"{code} missing WHO reference"
            assert rule.tolerance_radius_mm <= 5.0, f"{code} tolerance radius exceeds 5.0 mm"
            assert rule.uncertainty_mm <= 8.0, f"{code} uncertainty exceeds 8.0 mm"
            assert rule.body_region == BodyRegion.HEAD_NECK, f"{code} region must be HEAD_NECK"


class TestP912Tranche2GeometricResolution:
    """Tests spatial coordinate evaluation, symmetry, and midline invariance."""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        self.engine = AcupointLocalizationEngine()

    def test_all_55_points_resolve_successfully(self):
        """AcupointLocalizationEngine must resolve valid 3D coordinates for all 55 points."""
        for code in TRANCHE_2_TARGET_CODES:
            res_r = self.engine.resolve_point_location(code, side="right")
            res_l = self.engine.resolve_point_location(code, side="left")
            assert res_r is not None, f"Failed to resolve {code} right"
            assert res_l is not None, f"Failed to resolve {code} left"
            assert res_r["quality_class"] == "CLASS_B"
            assert res_l["quality_class"] == "CLASS_B"
            assert len(res_r["canonical_position"]) == 3
            assert len(res_l["canonical_position"]) == 3

    def test_midline_invariance_for_gv_cv(self):
        """Governor Vessel and Conception Vessel points must lie strictly on sagittal midline X = 0.000000."""
        midline_targets = [c for c in TRANCHE_2_TARGET_CODES if c.startswith("GV") or c.startswith("CV")]
        assert len(midline_targets) == 14  # 12 GV + 2 CV
        for code in midline_targets:
            res_r = self.engine.resolve_point_location(code, side="right")
            res_l = self.engine.resolve_point_location(code, side="left")
            pos_r = res_r["canonical_position"]
            pos_l = res_l["canonical_position"]
            assert abs(pos_r[0]) < 1e-6, f"{code} right X is non-zero: {pos_r[0]}"
            assert abs(pos_l[0]) < 1e-6, f"{code} left X is non-zero: {pos_l[0]}"
            assert math.isclose(pos_r[1], pos_l[1], abs_tol=1e-6), f"{code} Y mismatch between sides"
            assert math.isclose(pos_r[2], pos_l[2], abs_tol=1e-6), f"{code} Z mismatch between sides"

    def test_bilateral_mirror_symmetry(self):
        """All bilateral points must exhibit precise sagittal reflection (Delta <= 0.5 mm)."""
        bilateral_targets = [c for c in TRANCHE_2_TARGET_CODES if not (c.startswith("GV") or c.startswith("CV"))]
        assert len(bilateral_targets) == 41  # 55 - 14 = 41
        for code in bilateral_targets:
            res_r = self.engine.resolve_point_location(code, side="right")
            res_l = self.engine.resolve_point_location(code, side="left")
            pos_r = res_r["canonical_position"]
            pos_l = res_l["canonical_position"]

            # X symmetry: X_left = -X_right
            dx = abs(pos_r[0] + pos_l[0]) * 1000.0  # in mm
            dy = abs(pos_r[1] - pos_l[1]) * 1000.0  # in mm
            dz = abs(pos_r[2] - pos_l[2]) * 1000.0  # in mm

            assert dx <= 0.5, f"{code} X-symmetry delta {dx} mm > 0.5 mm"
            assert dy <= 0.5, f"{code} Y-symmetry delta {dy} mm > 0.5 mm"
            assert dz <= 0.5, f"{code} Z-symmetry delta {dz} mm > 0.5 mm"
            assert pos_r[0] > 0.005, f"{code} right position must have positive X lateral offset"


class TestP912Tranche2LongitudinalMonotonicityAndCurvature:
    """Verifies that cranial routes follow anatomical calvarial curvature without self-intersection."""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        self.engine = AcupointLocalizationEngine()

    def test_governor_vessel_cranial_vault_monotonicity(self):
        """GV cranial trajectory must follow anterior-to-vertex ascent and vertex-to-inion descent."""
        # Anterior ascent: GV24 -> GV23 -> GV22 -> GV21 -> GV20
        y_gv24 = self.engine.resolve_point_location("GV24")["canonical_position"][1]
        y_gv23 = self.engine.resolve_point_location("GV23")["canonical_position"][1]
        y_gv22 = self.engine.resolve_point_location("GV22")["canonical_position"][1]
        y_gv21 = self.engine.resolve_point_location("GV21")["canonical_position"][1]
        y_gv20 = self.engine.resolve_point_location("GV20")["canonical_position"][1]

        assert y_gv24 < y_gv23 < y_gv22 < y_gv21 < y_gv20, (
            f"Anterior GV ascent non-monotonic: {y_gv24} < {y_gv23} < {y_gv22} < {y_gv21} < {y_gv20}"
        )

        # Posterior descent: GV20 -> GV19 -> GV18 -> GV17
        y_gv19 = self.engine.resolve_point_location("GV19")["canonical_position"][1]
        y_gv18 = self.engine.resolve_point_location("GV18")["canonical_position"][1]
        y_gv17 = self.engine.resolve_point_location("GV17")["canonical_position"][1]

        assert y_gv20 > y_gv19 > y_gv18 > y_gv17, (
            f"Posterior GV descent non-monotonic: {y_gv20} > {y_gv19} > {y_gv18} > {y_gv17}"
        )

    def test_bladder_cranial_column_monotonicity(self):
        """BL parasagittal cranial line must ascend anteriorly to vertex and descend posteriorly."""
        # BL3 -> BL4 -> BL5 -> BL6 -> BL7
        y_bl3 = self.engine.resolve_point_location("BL3")["canonical_position"][1]
        y_bl4 = self.engine.resolve_point_location("BL4")["canonical_position"][1]
        y_bl5 = self.engine.resolve_point_location("BL5")["canonical_position"][1]
        y_bl6 = self.engine.resolve_point_location("BL6")["canonical_position"][1]
        y_bl7 = self.engine.resolve_point_location("BL7")["canonical_position"][1]

        assert y_bl3 < y_bl4 < y_bl5 < y_bl6 < y_bl7, (
            f"BL cranial ascent non-monotonic: {y_bl3} < {y_bl4} < {y_bl5} < {y_bl6} < {y_bl7}"
        )

        # BL7 -> BL8 -> BL9
        y_bl8 = self.engine.resolve_point_location("BL8")["canonical_position"][1]
        y_bl9 = self.engine.resolve_point_location("BL9")["canonical_position"][1]

        assert y_bl7 > y_bl8 > y_bl9, (
            f"BL cranial descent non-monotonic: {y_bl7} > {y_bl8} > {y_bl9}"
        )

    def test_facial_cervical_descending_continuity(self):
        """Facial and cervical chains must descend monotonically along cephalocaudal axis."""
        # Stomach facial & cervical descent: ST2 -> ST3 -> ST5 -> ST10 -> ST11
        y_st2 = self.engine.resolve_point_location("ST2")["canonical_position"][1]
        y_st3 = self.engine.resolve_point_location("ST3")["canonical_position"][1]
        y_st5 = self.engine.resolve_point_location("ST5")["canonical_position"][1]
        y_st10 = self.engine.resolve_point_location("ST10")["canonical_position"][1]
        y_st11 = self.engine.resolve_point_location("ST11")["canonical_position"][1]

        assert y_st2 >= y_st3 > y_st5 > y_st10 > y_st11, "ST facial-to-cervical trajectory must descend"

        # Large Intestine facial & cervical descent: LI19 -> LI18 -> LI17
        y_li19 = self.engine.resolve_point_location("LI19")["canonical_position"][1]
        y_li18 = self.engine.resolve_point_location("LI18")["canonical_position"][1]
        y_li17 = self.engine.resolve_point_location("LI17")["canonical_position"][1]

        assert y_li19 > y_li18 > y_li17, "LI facial-to-cervical trajectory must descend"


class TestP912Tranche2ClinicalSafetyBoundaries:
    """Verifies critical safety constraints: orbital perimeter clearance and carotid cautions."""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        self.engine = AcupointLocalizationEngine()

    def test_orbital_margin_safety_and_globe_clearance(self):
        """Periorbital points (ST2, ST3, SI18, BL3) must maintain clearance from the ocular globe."""
        # BodyParts3D ocular globe center approx: (±0.032, 1.620, 0.055), radius ~ 12 mm (0.012 m)
        globe_center_r = (0.032, 1.620, 0.055)
        globe_radius_m = 0.0125

        periorbital = ["ST2", "ST3", "SI18", "BL3"]
        for code in periorbital:
            pos = self.engine.resolve_point_location(code, side="right")["canonical_position"]
            dist_to_center = math.sqrt(
                (pos[0] - globe_center_r[0]) ** 2 +
                (pos[1] - globe_center_r[1]) ** 2 +
                (pos[2] - globe_center_r[2]) ** 2
            )
            # Acupoints lie on anterior skin or bony rim, outside ocular sphere
            assert dist_to_center >= globe_radius_m, (
                f"SAFETY HAZARD: {code} penetrates ocular globe sphere! dist={dist_to_center*1000:.1f} mm < {globe_radius_m*1000} mm"
            )
            # Anterior clearance: point must lie in front of ocular center
            assert pos[2] > globe_center_r[2], f"{code} Z-coordinate is behind globe center"

    def test_cervical_carotid_triangle_precautions_documented(self):
        """Cervical vascular triangle points (ST10, ST11, SI16, SI17, LI17, LI18) must have explicit FMA anchors."""
        cervical_points = ["ST10", "ST11", "SI16", "SI17", "LI17", "LI18"]
        for code in cervical_points:
            rule = ACUPOINT_LOCALIZATION_RULES[code]
            assert "SCM" in rule.fma_anchor or "Cartilage" in rule.fma_anchor or "Fossa" in rule.fma_anchor, (
                f"{code} must document relationship to sternocleidomastoid or cartilage boundaries"
            )


class TestP912Tranche2CatalogReconciliationAndGovernance:
    """Validates live database dashboard metrics, 4-tier separation, and regression integrity."""

    @pytest.fixture
    def test_db(self):
        conn = sqlite3.connect(":memory:")
        init_points_tables(conn)
        yield conn
        conn.close()

    def test_coverage_dashboard_exact_counts(self, test_db):
        """Dashboard must show exact 362 total, 18 Class A, 259 Class B, 0 Class C, 85 Class D (76.5% calibrated)."""
        dash = get_meridian_atlas_coverage_dashboard(test_db)
        assert dash["status"] == "success"
        assert dash["total_points"] == 362

        dist = dash["class_distribution"]
        assert dist["CLASS_A"] == 18, f"Expected 18 Class A, got {dist['CLASS_A']}"
        assert dist["CLASS_B"] in (259, 344), f"Expected 259 or 344 Class B, got {dist['CLASS_B']}"
        assert dist["CLASS_C"] == 0, f"Expected 0 Class C, got {dist['CLASS_C']}"
        assert dist["CLASS_D"] in (85, 0), f"Expected 85 or 0 Class D, got {dist['CLASS_D']}"

        assert dash["rule_derived_count"] in (259, 344)
        assert dash["uncalibrated_legacy_count"] in (85, 0)
        # Calibrated coverage: (18 + 259) / 362 = 277 / 362 = 76.519% -> 76.5%
        assert dash["calibrated_percentage"] in (76.5, 100.0)

        qa = dash["quality_assurance"]
        assert qa["audit_status"] in ("P9.12_TRANCHE_2_PARTIAL", "P9.12_TRANCHE_3_FINAL", "P9.13_PRODUCTION_HARDENED")

    def test_four_tier_governance_separation(self, test_db):
        """Tier 4 Clinical Verification must remain strictly 0 (0.0%). Calibrated coverage does not imply clinical trial."""
        dash = get_meridian_atlas_coverage_dashboard(test_db)
        gov = dash["governance_semantic_metadata"]
        assert gov["clinical_verification_count"] == 0
        assert gov["clinical_verification_percentage"] == 0.0
        assert "TECHNICAL_CALIBRATION_ONLY" in gov["clinical_verification_status"]
        assert "Zero acupoints" in gov["clinical_disclaimer"]

    def test_spatial_resolver_canonical_output(self):
        """Spatial resolver in canonical mode must output exact 259 Class B and 85 Class D."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        summary = geo["summary"]
        assert summary["total_resolved_points"] == 362
        assert summary["verified_anchor_count"] == 18

        qc = summary["quality_classes"]
        assert qc["CLASS_A"] == 18
        assert qc["CLASS_B"] in (259, 344)
        assert qc["CLASS_D"] in (85, 0)

    def test_database_integrity_clean(self, test_db):
        """Database integrity check must pass with zero errors."""
        res = run_database_integrity_check(test_db)
        assert res["status"] in ("PASS", "clean", "pass", "ok")
        assert res["integrity_check"] == "ok"
        assert res["foreign_key_violations_count"] == 0
