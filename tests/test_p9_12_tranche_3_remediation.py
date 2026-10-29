"""
MSK-Therapy-OS | Milestone P9.12 Tranche 3 Test Suite
Final Anatomical Remediation & Full Catalog Calibration Verification
Authoritative Standard: WHO 2008 Standard Acupuncture Point Locations & BodyParts3D FJ2810
Acceptance Criteria:
  - 85 Final Class D points remediated to Class B (61 Axial/Torso + 24 Distal Extremity)
  - 18 Class A (Audited Canonical Anchors) preserved
  - 344 Class B (Parametric WHO 2008 Rule-Derived, +85 from Tranche 3)
  - 0 Class C (Quarantined Inconsistencies)
  - 0 Class D (Zero Uncalibrated Legacy Raycasts remaining)
  - Calibrated coverage: 100.0% (362/362)
  - Tier 4 Clinical Verification: strictly 0 (0.0%)
  - Bilateral sagittal symmetry: Delta <= 0.5 mm (actual <= 0.001 mm)
  - Sagittal midline integrity: X == 0.000000, Nx == 0.000000
  - Collinear abdominal alignment (ST19..ST30 lateral offset X == 0.066m matching ST25)
  - Anatomical monotonicity along spinal, thoracic, abdominal, and pedal trajectories
  - Zero circular landmark dependencies
  - Clean SQLite database integrity and foreign key constraints
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
from msk_therapy_os.landmark_dependency_validator import AnatomicalProvenanceDependencyValidator


# Authoritative 85 Tranche 3 Target Acupoints
TRANCHE_3_GROUP_A_AXIAL = [
    # BL paraspinal & sacral (19)
    "BL16", "BL17", "BL18", "BL19", "BL20", "BL21", "BL22", "BL24",
    "BL26", "BL27", "BL28", "BL29", "BL30", "BL31", "BL32", "BL33", "BL34", "BL35", "BL51",
    # GV spine & sacrum (12)
    "GV1", "GV2", "GV3", "GV5", "GV6", "GV7", "GV8", "GV9", "GV10", "GV11", "GV12", "GV13",
    # CV perineum (1)
    "CV1",
    # GB flank (7)
    "GB22", "GB23", "GB24", "GB25", "GB26", "GB27", "GB28",
    # KI upper thorax (2)
    "KI25", "KI26",
    # SP lateral thorax (3)
    "SP17", "SP18", "SP19",
    # ST thorax (6)
    "ST13", "ST14", "ST15", "ST16", "ST17", "ST18",
    # ST abdomen (11)
    "ST19", "ST20", "ST21", "ST22", "ST23", "ST24", "ST26", "ST27", "ST28", "ST29", "ST30"
]

TRANCHE_3_GROUP_B_DISTAL = [
    # HT distal hand (2)
    "HT8", "HT9",
    # LI distal hand (2)
    "LI2", "LI3",
    # PC distal hand (2)
    "PC8", "PC9",
    # SI distal hand (1)
    "SI2",
    # TE distal hand (2)
    "TE2", "TE3",
    # BL distal foot (7)
    "BL61", "BL62", "BL63", "BL64", "BL65", "BL66", "BL67",
    # GB distal foot (4)
    "GB41", "GB42", "GB43", "GB44",
    # ST distal foot (4)
    "ST42", "ST43", "ST44", "ST45"
]

TRANCHE_3_TARGET_CODES = TRANCHE_3_GROUP_A_AXIAL + TRANCHE_3_GROUP_B_DISTAL


@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    init_points_tables(conn)
    yield conn
    conn.close()


class TestP912Tranche3ScopeAndCatalog:
    """Verifies scope completeness, target reconciliation, and catalog invariants."""

    def test_target_scope_cardinality_and_uniqueness(self):
        """Authoritative target set must contain exactly 85 unique points (61 axial + 24 distal)."""
        assert len(TRANCHE_3_GROUP_A_AXIAL) == 61
        assert len(TRANCHE_3_GROUP_B_DISTAL) == 24
        assert len(TRANCHE_3_TARGET_CODES) == 85
        assert len(set(TRANCHE_3_TARGET_CODES)) == 85

    def test_scope_reconciliation_csv_alignment(self):
        """Target points must match P912_T3_SCOPE_RECONCILIATION.csv eligible set exactly."""
        csv_path = Path("1docs/audits/P9_12/TRANCHE_3/P912_T3_SCOPE_RECONCILIATION.csv")
        if not csv_path.exists():
            pytest.skip("Scope reconciliation CSV not yet written to disk")
        eligible_csv = []
        with open(csv_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.strip().split(",")]
                if len(parts) >= 8 and parts[7] == "ELIGIBLE":
                    eligible_csv.append(parts[0])
        assert sorted(eligible_csv) == sorted(TRANCHE_3_TARGET_CODES)

    def test_all_85_rules_defined_with_provenance(self):
        """All 85 target points must have registered localization rules with valid FMA & WHO citations."""
        for code in TRANCHE_3_TARGET_CODES:
            assert code in ACUPOINT_LOCALIZATION_RULES, f"Rule missing for {code}"
            rule = ACUPOINT_LOCALIZATION_RULES[code]
            assert isinstance(rule, AcupointLocalizationRule)
            assert rule.quality_class == "CLASS_B", f"{code} must be CLASS_B"
            assert rule.fma_anchor.startswith("FMA:"), f"{code} missing FMA anchor"
            assert "WHO 2008" in rule.who_reference or "GB/T 12346" in rule.who_reference, f"{code} missing WHO reference"
            assert rule.tolerance_radius_mm <= 5.0, f"{code} tolerance radius exceeds 5.0 mm"
            assert rule.uncertainty_mm <= 8.0, f"{code} uncertainty exceeds 8.0 mm"
            assert rule.surface_normal is not None, f"{code} must have explicit surface normal vector"
            assert len(rule.surface_normal) == 3


class TestP912Tranche3GeometricResolution:
    """Tests spatial coordinate evaluation, symmetry, and midline invariance."""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        self.engine = AcupointLocalizationEngine()

    def test_all_85_points_resolve_successfully(self):
        """AcupointLocalizationEngine must resolve valid 3D coordinates and normals for all 85 points."""
        for code in TRANCHE_3_TARGET_CODES:
            res_r = self.engine.resolve_point_location(code, side="right")
            res_l = self.engine.resolve_point_location(code, side="left")
            assert res_r is not None, f"Failed to resolve {code} right"
            assert res_l is not None, f"Failed to resolve {code} left"
            assert res_r["quality_class"] == "CLASS_B"
            assert res_l["quality_class"] == "CLASS_B"
            assert len(res_r["canonical_position"]) == 3
            assert len(res_l["canonical_position"]) == 3
            assert len(res_r["surface_normal"]) == 3
            assert len(res_l["surface_normal"]) == 3

    def test_midline_invariance_for_gv_and_cv1(self):
        """Governor Vessel spine points and CV1 must lie strictly on sagittal midline X = 0.000000 with Nx = 0."""
        midline_targets = [c for c in TRANCHE_3_TARGET_CODES if c.startswith("GV") or c == "CV1"]
        assert len(midline_targets) == 13  # 12 GV + 1 CV1
        for code in midline_targets:
            res_r = self.engine.resolve_point_location(code, side="right")
            res_l = self.engine.resolve_point_location(code, side="left")
            pos_r = res_r["canonical_position"]
            pos_l = res_l["canonical_position"]
            norm_r = res_r["surface_normal"]
            norm_l = res_l["surface_normal"]

            assert abs(pos_r[0]) < 1e-6, f"{code} right X ({pos_r[0]}) violates sagittal midline invariance"
            assert abs(pos_l[0]) < 1e-6, f"{code} left X ({pos_l[0]}) violates sagittal midline invariance"
            assert abs(norm_r[0]) < 1e-6, f"{code} right Nx ({norm_r[0]}) must be 0 on sagittal midline"
            assert abs(norm_l[0]) < 1e-6, f"{code} left Nx ({norm_l[0]}) must be 0 on sagittal midline"

    def test_bilateral_mirror_symmetry_delta(self):
        """All 72 bilateral points (85 - 13 midline) must have mirror symmetry Delta <= 0.5 mm."""
        bilateral_targets = [c for c in TRANCHE_3_TARGET_CODES if not (c.startswith("GV") or c == "CV1")]
        assert len(bilateral_targets) == 72
        for code in bilateral_targets:
            res_r = self.engine.resolve_point_location(code, side="right")
            res_l = self.engine.resolve_point_location(code, side="left")
            pos_r = res_r["canonical_position"]
            pos_l = res_l["canonical_position"]
            norm_r = res_r["surface_normal"]
            norm_l = res_l["surface_normal"]

            # X coordinates must be mirrored: X_right == -X_left
            delta_x = abs(pos_r[0] - (-pos_l[0]))
            delta_y = abs(pos_r[1] - pos_l[1])
            delta_z = abs(pos_r[2] - pos_l[2])
            dist_diff_mm = math.sqrt(delta_x**2 + delta_y**2 + delta_z**2) * 1000.0

            assert dist_diff_mm <= 0.5, f"{code} bilateral symmetry delta {dist_diff_mm:.4f}mm exceeds 0.5mm"
            # Normal vector X mirrored, Y and Z preserved
            assert abs(norm_r[0] - (-norm_l[0])) < 1e-6, f"{code} normal vector Nx reflection failed"
            assert abs(norm_r[1] - norm_l[1]) < 1e-6, f"{code} normal vector Ny mismatch"
            assert abs(norm_r[2] - norm_l[2]) < 1e-6, f"{code} normal vector Nz mismatch"

    def test_surface_normal_outward_orientation(self):
        """Normal vectors must be unit length and point outwards from anatomical body surfaces."""
        for code in TRANCHE_3_TARGET_CODES:
            res_r = self.engine.resolve_point_location(code, side="right")
            norm = res_r["surface_normal"]
            length = math.sqrt(norm[0]**2 + norm[1]**2 + norm[2]**2)
            assert abs(length - 1.0) < 1e-3, f"{code} normal length {length} is not unit vector"

            # In BodyParts3D: Z is anteroposterior (Z < 0 is posterior, Z > 0 is anterior)
            # Posterior back points must face posteriorly: Nz < 0
            if code.startswith("BL") and code not in ("BL61", "BL62", "BL63", "BL64", "BL65", "BL66", "BL67"):
                assert norm[2] < 0, f"{code} posterior back normal Nz ({norm[2]}) should be negative"
            if code.startswith("GV") and code not in ("GV1", "GV2"):
                assert norm[2] < 0, f"{code} posterior spine normal Nz ({norm[2]}) should be negative"
            # Anterior torso points must face anteriorly: Nz > 0
            if code.startswith("ST") and code not in ("ST42", "ST43", "ST44", "ST45"):
                assert norm[2] > 0, f"{code} anterior torso normal Nz ({norm[2]}) should be positive"


class TestP912Tranche3MonotonicityAndTopology:
    """Verifies anatomical ordering and spatial topology along meridian trajectories."""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        self.engine = AcupointLocalizationEngine()

    def test_bl_paraspinal_monotonicity(self):
        """BL paraspinal medial line points must decrease monotonically along craniocaudal Y axis."""
        bl_medial = ["BL16", "BL17", "BL18", "BL19", "BL20", "BL21", "BL22", "BL24", "BL26"]
        y_coords = [self.engine.resolve_point_location(c, side="right")["canonical_position"][1] for c in bl_medial]
        for i in range(len(y_coords) - 1):
            assert y_coords[i] > y_coords[i+1], f"BL paraspinal monotonicity violation at {bl_medial[i]} -> {bl_medial[i+1]}"

    def test_bl_sacral_descent_monotonicity(self):
        """BL sacral points (BL27..BL30, BL35) and foramina (BL31..BL34) must decrease monotonically in Y."""
        bl_sacral = ["BL27", "BL28", "BL29", "BL30", "BL35"]
        y_coords = [self.engine.resolve_point_location(c, side="right")["canonical_position"][1] for c in bl_sacral]
        for i in range(len(y_coords) - 1):
            assert y_coords[i] > y_coords[i+1], f"BL sacral monotonicity violation at {bl_sacral[i]} -> {bl_sacral[i+1]}"

        bl_foramina = ["BL31", "BL32", "BL33", "BL34"]
        y_foram = [self.engine.resolve_point_location(c, side="right")["canonical_position"][1] for c in bl_foramina]
        for i in range(len(y_foram) - 1):
            assert y_foram[i] > y_foram[i+1], f"BL foramina monotonicity violation at {bl_foramina[i]} -> {bl_foramina[i+1]}"

    def test_gv_spine_monotonicity(self):
        """Governor Vessel spinal points (GV13 down to GV1) must decrease monotonically in Y."""
        gv_spine = ["GV13", "GV12", "GV11", "GV10", "GV9", "GV8", "GV7", "GV6", "GV5", "GV3", "GV2", "GV1"]
        y_coords = [self.engine.resolve_point_location(c, side="right")["canonical_position"][1] for c in gv_spine]
        for i in range(len(y_coords) - 1):
            assert y_coords[i] > y_coords[i+1], f"GV spine monotonicity violation at {gv_spine[i]} -> {gv_spine[i+1]}"

    def test_st_thorax_monotonicity(self):
        """ST thoracic line (ST13..ST18) along midclavicular line must decrease monotonically in Y."""
        st_thorax = ["ST13", "ST14", "ST15", "ST16", "ST17", "ST18"]
        y_coords = [self.engine.resolve_point_location(c, side="right")["canonical_position"][1] for c in st_thorax]
        for i in range(len(y_coords) - 1):
            assert y_coords[i] > y_coords[i+1], f"ST thorax monotonicity violation at {st_thorax[i]} -> {st_thorax[i+1]}"

    def test_st_abdomen_collinear_and_monotonic(self):
        """ST abdominal line (ST19..ST30) must be collinear at lateral offset X == 0.066m (matching ST25) and monotonic in Y."""
        st_abdomen = ["ST19", "ST20", "ST21", "ST22", "ST23", "ST24", "ST26", "ST27", "ST28", "ST29", "ST30"]
        pos_list = [self.engine.resolve_point_location(c, side="right")["canonical_position"] for c in st_abdomen]

        # Monotonicity in Y
        y_coords = [p[1] for p in pos_list]
        for i in range(len(y_coords) - 1):
            assert y_coords[i] > y_coords[i+1], f"ST abdomen monotonicity violation at {st_abdomen[i]} -> {st_abdomen[i+1]}"

        # Collinearity in X (lateral offset 2 cun = 0.066m)
        for i, code in enumerate(st_abdomen):
            x_coord = pos_list[i][0]
            assert abs(x_coord - 0.066) < 1e-4, f"ST abdomen point {code} X coordinate {x_coord} does not match 2 cun line 0.066m"

    def test_distal_extremity_monotonicity(self):
        """Foot points must progress anteriorly (increasing in Z) towards distal digits."""
        # ST foot: ST42 -> ST43 -> ST44 -> ST45
        st_foot = ["ST42", "ST43", "ST44", "ST45"]
        z_st = [self.engine.resolve_point_location(c, side="right")["canonical_position"][2] for c in st_foot]
        for i in range(len(z_st) - 1):
            assert z_st[i] < z_st[i+1], f"ST foot anterior monotonicity violation at {st_foot[i]} -> {st_foot[i+1]}"

        # GB foot: GB41 -> GB42 -> GB43 -> GB44
        gb_foot = ["GB41", "GB42", "GB43", "GB44"]
        z_gb = [self.engine.resolve_point_location(c, side="right")["canonical_position"][2] for c in gb_foot]
        for i in range(len(z_gb) - 1):
            assert z_gb[i] < z_gb[i+1], f"GB foot anterior monotonicity violation at {gb_foot[i]} -> {gb_foot[i+1]}"

        # BL foot: BL61 -> BL62 -> BL63 -> BL64 -> BL65 -> BL66 -> BL67
        bl_foot = ["BL61", "BL62", "BL63", "BL64", "BL65", "BL66", "BL67"]
        z_bl = [self.engine.resolve_point_location(c, side="right")["canonical_position"][2] for c in bl_foot]
        for i in range(len(z_bl) - 1):
            assert z_bl[i] < z_bl[i+1], f"BL foot anterior monotonicity violation at {bl_foot[i]} -> {bl_foot[i+1]}"


class TestP912Tranche3ZeroCircularityAndGovernance:
    """Verifies complete graph acyclicity, 100% calibrated coverage, and strict Tier 4 governance separation."""

    def test_zero_circular_landmark_dependencies(self):
        """Dependency validator must report PASS, zero circularities, and zero missing landmarks."""
        validator = AnatomicalProvenanceDependencyValidator()
        result = validator.validate_all()
        assert result["status"] == "PASS"
        assert result["undisclosed_circular_count"] == 0
        assert result["missing_landmark_count"] == 0
        assert result["blocked_landmark_count"] == 0

    def test_coverage_dashboard_100_percent_calibrated(self, test_db):
        """Dashboard must show exact 362 total, 18 Class A, 344 Class B, 0 Class C, 0 Class D (100.0% calibrated)."""
        dash = get_meridian_atlas_coverage_dashboard(test_db)
        assert dash["status"] == "success"
        assert dash["total_points"] == 362

        dist = dash["class_distribution"]
        assert dist["CLASS_A"] == 18, f"Expected 18 Class A, got {dist['CLASS_A']}"
        assert dist["CLASS_B"] == 344, f"Expected 344 Class B, got {dist['CLASS_B']}"
        assert dist["CLASS_C"] == 0, f"Expected 0 Class C, got {dist['CLASS_C']}"
        assert dist["CLASS_D"] == 0, f"Expected 0 Class D, got {dist['CLASS_D']}"

        assert dash["independently_verified_count"] == 18
        assert dash["rule_derived_count"] == 344
        assert dash["uncalibrated_legacy_count"] == 0
        assert dash["calibrated_percentage"] == 100.0
        assert "0 Class D points" in dash["class_d_warning"]

        qa = dash["quality_assurance"]
        assert qa["audit_status"] in ("P9.12_TRANCHE_3_FINAL", "P9.13_PRODUCTION_HARDENED")

    def test_four_tier_governance_separation(self, test_db):
        """Tier 4 Clinical Verification must remain strictly 0 (0.0%). Calibrated coverage does not imply clinical trial."""
        dash = get_meridian_atlas_coverage_dashboard(test_db)
        gov = dash["governance_semantic_metadata"]
        assert gov["clinical_verification_count"] == 0
        assert gov["clinical_verification_percentage"] == 0.0
        assert "TECHNICAL_CALIBRATION_ONLY" in gov["clinical_verification_status"]
        assert "Zero acupoints" in gov["clinical_disclaimer"]

    def test_spatial_resolver_canonical_output(self):
        """Spatial resolver in canonical mode must output exact 344 Class B and 0 Class D."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        summary = geo["summary"]
        assert summary["total_resolved_points"] == 362
        assert summary["verified_anchor_count"] == 18

        qc = summary["quality_classes"]
        assert qc["CLASS_A"] == 18
        assert qc["CLASS_B"] == 344
        assert qc["CLASS_D"] == 0

    def test_database_integrity_clean(self, test_db):
        """Database integrity check must pass with zero errors."""
        res = run_database_integrity_check(test_db)
        assert res["status"] in ("PASS", "clean", "pass", "ok")
        assert res["integrity_check"] == "ok"
        assert res["foreign_key_violations_count"] == 0
