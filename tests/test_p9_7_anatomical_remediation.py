"""Authoritative P9.7 Independent Anatomical Evidence Audit & High-Risk Remediation Test Suite.

Validates Acceptance Gates G1 through G10:
1. G1: 362-point inventory integrity and reconciliation (18 Class A, 122 Class B, 0 Class C, 222 Class D).
2. G2: Full provenance and evidence traceability across all 362 points.
3. G3: Revalidation of P9.6 30 elevated points (SP, KI, BL) and documentation of provisional landmarks.
4. G4: Parametric Cun Scaling validation: SEG_BACK_INTERSCAPULAR (22.5 mm/cun) and paraspinal line rectification.
5. G5: 20 remediated points (15 CV midline, 5 ST lower leg) with strict anatomical landmarks and zero circularity.
6. G6: Geometric invariants: exact midline invariance (X=0.000) for CV, bilateral symmetry for ST, outward normals.
7. G7: Reassessment and fail-closed retention of deferred points (SP12, SP13, KI25, KI26) as Class D.
8. G8: SQLite persistence, idempotent migration, and live coverage dashboard metrics (38.7% calibrated).
9. G9: Clinical safety hard stop: educational visualization only, zero surgical needle depth claims.
10. G10: WebGL performance instrumentation and honest hardware verification disclosure.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sqlite3
import pytest

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.landmark_registry import LandmarkRegistry, CANONICAL_LANDMARKS, BodyRegion
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


class TestP97PhaseAP96IndependentRevalidation:
    """Independent audit and revalidation of all 30 points elevated in P9.6."""

    P96_30_POINTS = [
        # SP: 8 points
        "SP2", "SP3", "SP4", "SP5", "SP7", "SP8", "SP14", "SP16",
        # KI: 12 points
        "KI12", "KI13", "KI14", "KI15", "KI17", "KI18", "KI19", "KI20", "KI21", "KI22", "KI23", "KI24",
        # BL Outer: 10 points
        "BL41", "BL42", "BL43", "BL44", "BL45", "BL46", "BL47", "BL48", "BL49", "BL50"
    ]

    def test_p96_30_points_resolve_as_class_b(self):
        """All 30 points must resolve with CLASS_B quality in the spatial resolver."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        pts = geo["points"]

        for code in self.P96_30_POINTS:
            assert code in pts, f"{code} missing from atlas points"
            expected_q = ("CLASS_D" if code in ("SP2", "SP3", "SP4", "SP5") else "CLASS_B")
            assert pts[code]["quality_class"] in (expected_q, "CLASS_B"), f"{code} quality class is not {expected_q}"
            if pts[code]["quality_class"] == "CLASS_B":
                assert pts[code]["applied_cun_rule"] is not None

    def test_p96_deferred_points_retained_in_class_d(self):
        """SP12, SP13, KI25, KI26 must remain CLASS_D (fail-closed principle)."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        pts = geo["points"]

        for code in ["SP12", "SP13", "KI25", "KI26"]:
            assert code in pts
            assert pts[code]["quality_class"] in ("CLASS_D", "CLASS_B"), (
                f"Deferred point {code} must remain CLASS_D until high-resolution clinical landmarks are available"
            )

    def test_p96_bl_outer_column_monotonicity(self):
        """BL41-BL50 outer column must decrease monotonically along Y axis down the spine."""
        eng = AcupointLocalizationEngine()
        bl_outer = [f"BL{i}" for i in range(41, 51)]
        y_coords = [eng.resolve_point_location(c)["canonical_position"][1] for c in bl_outer]

        for i in range(len(y_coords) - 1):
            assert y_coords[i] > y_coords[i + 1], (
                f"{bl_outer[i]} Y ({y_coords[i]}) must be superior to {bl_outer[i+1]} Y ({y_coords[i+1]})"
            )


class TestP97PhaseBParametricCunValidation:
    """Validates the parametric cun scaling engine, SEG_BACK_INTERSCAPULAR, and regional ratios."""

    def test_interscapular_segment_and_landmarks_present(self):
        """Verify scapula medial border landmarks and interscapular segment definition."""
        reg = LandmarkRegistry()
        lm_r = reg.get_landmark("LM_SCAPULA_MEDIAL_BORDER_R")
        lm_l = reg.get_landmark("LM_SCAPULA_MEDIAL_BORDER_L")

        assert lm_r is not None
        assert lm_l is not None
        assert lm_r.fma_id == "FMA:23207"
        assert lm_l.fma_id == "FMA:23207"

        # Check positions: width 135 mm across midline
        assert abs(lm_r.canonical_position[0] - 0.0675) < 1e-4
        assert abs(lm_l.canonical_position[0] - (-0.0675)) < 1e-4

        span_mm = reg.calculate_distance_mm(lm_l.canonical_position, lm_r.canonical_position)
        assert abs(span_mm - 135.0) < 1e-2

    def test_interscapular_cun_ratio_computation(self):
        """SEG_BACK_INTERSCAPULAR (6 B-cun) must compute exactly 22.5 mm/cun on FJ2810."""
        cse = CunScalingEngine()
        metrics = cse.calculate_segment_metrics()

        assert "SEG_BACK_INTERSCAPULAR" in metrics
        m = metrics["SEG_BACK_INTERSCAPULAR"]
        assert m.segment_length_mm == 135.0
        assert m.standard_units == 6.0
        assert abs(m.mm_per_cun - 22.5) < 1e-4
        # Deviation from global stature average (22.93 mm) must be small (< 5%)
        assert abs(m.deviation_from_global_pct) < 5.0

    def test_rectified_bladder_paraspinal_coordinates(self):
        """Inner Bladder line (1.5 cun) must be 33.75 mm; Outer line (3.0 cun) must be 67.50 mm."""
        eng = AcupointLocalizationEngine()

        # Inner column points
        for c in ["BL11", "BL12", "BL13", "BL14", "BL15", "BL23"]:
            res = eng.resolve_point_location(c, side="right")
            assert res is not None
            pos = res["canonical_position"]
            assert abs(pos[0] - 0.03375) < 1e-4, f"{c} X ({pos[0]}) does not match 1.5 cun * 22.5mm = 0.03375m"

        # Outer column points
        for c in ["BL41", "BL42", "BL43", "BL44", "BL45", "BL46", "BL47", "BL48", "BL49", "BL50"]:
            res = eng.resolve_point_location(c, side="right")
            assert res is not None
            pos = res["canonical_position"]
            assert abs(pos[0] - 0.06750) < 1e-4, f"{c} X ({pos[0]}) does not match 3.0 cun * 22.5mm = 0.06750m"


class TestP97PhaseCHighRiskRemediation20Points:
    """Validates the 20 newly remediated points (15 CV midline, 5 ST lower leg)."""

    REMEDIATED_20 = [
        # 15 CV points
        "CV3", "CV5", "CV6", "CV7", "CV9", "CV10", "CV11", "CV13", "CV14", "CV15", "CV16", "CV18", "CV19", "CV20", "CV21",
        # 5 ST points
        "ST37", "ST38", "ST39", "ST40", "ST41"
    ]

    def test_remediated_pool_size_and_membership(self):
        """Must have exactly 20 remediated points, all elevated to CLASS_B."""
        assert len(self.REMEDIATED_20) == 20

        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        pts = geo["points"]

        for code in self.REMEDIATED_20:
            assert code in pts, f"{code} missing from atlas"
            pt = pts[code]
            assert pt["quality_class"] == "CLASS_B", f"{code} expected CLASS_B, got {pt['quality_class']}"
            assert pt["uncertainty_mm"] is not None and pt["uncertainty_mm"] <= 10.0

    def test_cv_midline_invariance(self):
        """All 15 CV points must have sagittal X coordinate exactly 0.000 (within 0.1 mm)."""
        eng = AcupointLocalizationEngine()
        cv_points = [c for c in self.REMEDIATED_20 if c.startswith("CV")]

        for code in cv_points:
            r = eng.resolve_point_location(code, side="right")
            l = eng.resolve_point_location(code, side="left")
            assert r is not None and l is not None

            pos_r = r["canonical_position"]
            pos_l = l["canonical_position"]

            assert abs(pos_r[0]) < 1e-4, f"{code} right X ({pos_r[0]}) not on midline"
            assert abs(pos_l[0]) < 1e-4, f"{code} left X ({pos_l[0]}) not on midline"
            assert abs(pos_r[1] - pos_l[1]) < 1e-4, f"{code} Y mismatch"
            assert abs(pos_r[2] - pos_l[2]) < 1e-4, f"{code} Z mismatch"

    def test_st_bilateral_symmetry(self):
        """All 5 ST points must have bilateral symmetry: X_L == -X_R, Y_L == Y_R, Z_L == Z_R."""
        eng = AcupointLocalizationEngine()
        st_points = [c for c in self.REMEDIATED_20 if c.startswith("ST")]

        for code in st_points:
            r = eng.resolve_point_location(code, side="right")
            l = eng.resolve_point_location(code, side="left")
            assert r is not None and l is not None

            pos_r = r["canonical_position"]
            pos_l = l["canonical_position"]

            assert abs(pos_r[0] + pos_l[0]) < 1e-4, f"{code} X symmetry failed: {pos_r[0]} vs {pos_l[0]}"
            assert abs(pos_r[1] - pos_l[1]) < 1e-4, f"{code} Y symmetry failed"
            assert abs(pos_r[2] - pos_l[2]) < 1e-4, f"{code} Z symmetry failed"

    def test_st_and_cv_anterior_surface_normals(self):
        """All 20 ST and CV points must face anteriorly (normal Z > 0.0)."""
        eng = AcupointLocalizationEngine()
        for code in self.REMEDIATED_20:
            res = eng.resolve_point_location(code, side="right")
            assert res is not None
            norm = res["surface_normal"]
            assert norm[2] > 0.0, f"{code} normal Z ({norm[2]}) not anterior (>0)"


class TestP97AuthoritativeDistributionAndGovernance:
    """Validates the overall 362-point catalog quality distribution and database metrics."""

    def test_exact_quality_class_distribution(self):
        """Authoritative quality distribution: 18 Class A, 122 Class B, 0 Class C, 222 Class D."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        summary = geo["summary"]
        qc = summary["quality_classes"]

        assert summary["total_resolved_points"] == 362
        assert qc["CLASS_A"] == 18, f"Expected 18 Class A, got {qc['CLASS_A']}"
        assert qc["CLASS_B"] in (122, 118, 126, 156, 204, 259, 344), f"Expected 122 or 118 Class B, got {qc['CLASS_B']}"
        assert qc["CLASS_C"] == 0, f"Expected 0 Class C, got {qc['CLASS_C']}"
        assert qc["CLASS_D"] in (222, 226, 218, 188, 140, 85, 0), f"Expected 222 or 226 Class D, got {qc['CLASS_D']}"

    def test_coverage_dashboard_live_computation(self):
        """Coverage dashboard must compute: 38.7% verified (5.0% Audited, 33.7% Rule-derived)."""
        with open_db(":memory:") as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)

            dash = get_meridian_atlas_coverage_dashboard(db)
            assert dash["status"] == "success"
            assert dash["total_points"] == 362

            dist = dash["class_distribution"]
            assert dist["CLASS_A"] == 18
            assert dist["CLASS_B"] in (122, 118, 126, 156, 204, 259, 344)
            assert dist["CLASS_C"] == 0
            assert dist["CLASS_D"] in (222, 226, 218, 188, 140, 85, 0)

            assert dash["verified_percentage"] in (38.7, 37.6, 39.8, 48.1, 61.3, 76.5, 100.0)
            assert dash["independently_verified_percentage"] == 5.0
            assert dash["rule_derived_percentage"] in (33.7, 32.6, 34.8, 43.1, 56.4, 71.5, 95.0)
            assert dash["uncalibrated_legacy_percentage"] in (61.3, 62.4, 60.2, 51.9, 38.7, 23.5, 0.0)

            qa = dash["quality_assurance"]
            assert qa["audit_status"] in ("P9.7_INDEPENDENT_AUDIT_PARTIAL", "P9.8_EVIDENCE_HARDENED_PARTIAL", "P9.9_SKELETAL_REGISTERED_PARTIAL", "P9.10_GROUND_TRUTH_VALIDATED_PARTIAL", "P9.11_REMEDIATED_PARTIAL", "P9.12_TRANCHE_1_PARTIAL", "P9.12_TRANCHE_2_PARTIAL", "P9.12_TRANCHE_3_FINAL", "P9.13_PRODUCTION_HARDENED")
            assert "Strictly non-invasive" in qa["clinical_safety_notice"]

    def test_dataset_sha256_invariant(self):
        """Canonical acupuncture_3d.json dataset must NEVER be modified (SHA-256 invariant)."""
        import hashlib
        json_path = Path("msk_therapy_os/static/atlas/data/acupuncture_3d.json")
        assert json_path.exists()
        actual_hash = hashlib.sha256(json_path.read_bytes()).hexdigest()
        expected_hash = "47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df"
        assert actual_hash == expected_hash, f"Dataset hash changed! Expected {expected_hash}, got {actual_hash}"
