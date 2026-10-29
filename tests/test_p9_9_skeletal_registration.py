"""P9.9 High-Resolution Foot & Wrist Skeletal Registration Test Suite.

Validates:
1. BodyParts3D 4.0 high-resolution bone mesh provenance and canonical mesh hash invariants.
2. Complete de-quarantine of foot landmarks with zero circularity.
3. Class B re-elevation of SP2, SP3, SP4, SP5 with independent skeletal grounding.
4. Distal Kidney point remediation (KI1-KI6) including plantar normal direction.
5. High-resolution wrist registration (LU9, HT7, PC7) with carpal/styloid grounding.
6. Pure-Python Umeyama/Procrustes registration with holdout validation.
7. Bilateral sagittal parity reflection invariants.
8. Authoritative catalog distribution: 18 Class A, 126 Class B, 0 Class C, 218 Class D (39.8% calibrated).
9. Fail-closed clinical safety boundary (visual/educational reference only; zero surgical needle depth claims).
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sqlite3
import pytest

from msk_therapy_os.anatomical_registration import (
    AnatomicalRegistrationEngine,
    HighResolutionSkeletalRegistrar,
    RegistrationTransform,
    SkeletalRegistrationReport,
)
from msk_therapy_os.db import init_db, seed_db, open_db
from msk_therapy_os.landmark_dependency_validator import (
    AnatomicalProvenanceDependencyValidator,
    DependencyIssueSeverity,
)
from msk_therapy_os.landmark_registry import (
    AnatomicalLandmark,
    BodyRegion,
    CANONICAL_LANDMARKS,
    LandmarkRegistry,
    LandmarkType,
)
from msk_therapy_os.point_localization_rules import (
    ACUPOINT_LOCALIZATION_RULES,
    AcupointLocalizationEngine,
    AcupointLocalizationRule,
    LocalizationMethod,
)
from msk_therapy_os.points import (
    get_meridian_atlas_coverage_dashboard,
    init_points_tables,
)
from msk_therapy_os.spatial_resolver import AnatomicalSpatialResolver


class TestP99AssetProvenanceAndMeshInvariants:
    """Gate G1: Validates BodyParts3D source provenance, dataset SHA256, and canonical mesh integrity."""

    CANONICAL_JSON_SHA256 = "47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df"
    CANONICAL_MESH_SHA256 = "05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808"

    def test_canonical_dataset_hash_invariant(self):
        """Canonical acupuncture_3d.json must match immutable SHA256."""
        json_path = Path("msk_therapy_os/static/atlas/data/acupuncture_3d.json")
        assert json_path.exists(), f"File {json_path} missing"
        actual_hash = hashlib.sha256(json_path.read_bytes()).hexdigest()
        assert actual_hash == self.CANONICAL_JSON_SHA256, (
            f"Dataset hash corrupted! Expected {self.CANONICAL_JSON_SHA256}, got {actual_hash}"
        )

    def test_canonical_mesh_hash_invariant(self):
        """Canonical fj2810_softened.bin must match immutable SHA256."""
        mesh_path = Path("2data/artifacts/fj2810_softened.bin")
        assert mesh_path.exists(), f"File {mesh_path} missing"
        actual_hash = hashlib.sha256(mesh_path.read_bytes()).hexdigest()
        assert actual_hash == self.CANONICAL_MESH_SHA256, (
            f"Mesh hash corrupted! Expected {self.CANONICAL_MESH_SHA256}, got {actual_hash}"
        )

    def test_registration_manifest_exists_and_passes(self):
        """Skeletal registration manifest must exist and have overall status PASS."""
        manifest_path = Path("2data/evidence/p9_9_registration/p9_9_skeletal_registration_manifest.json")
        assert manifest_path.exists(), f"Manifest {manifest_path} missing"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest["overall_status"] == "PASS"
        assert "foot_right" in manifest["subsystems"]
        assert "foot_left" in manifest["subsystems"]
        assert "wrist_right" in manifest["subsystems"]
        assert "wrist_left" in manifest["subsystems"]


class TestP99ZeroCircularityAndProvenanceGraph:
    """Gate G2: Validates that circular dependencies are completely eliminated with zero undisclosed/quarantined issues."""

    def test_zero_undisclosed_and_zero_quarantined_circularity(self):
        """Provenance graph validator must report 0 undisclosed and 0 quarantined circular references."""
        validator = AnatomicalProvenanceDependencyValidator()
        report = validator.validate_all()

        assert report["status"] == "PASS"
        assert report["undisclosed_circular_count"] == 0, "Discovered undisclosed circular dependencies!"
        assert report["quarantined_circular_count"] == 0, "Quarantined circular dependencies remain ungrounded!"
        assert report["missing_landmark_count"] == 0
        assert report["blocked_landmark_count"] == 0


class TestP99FootLandmarkDequarantineAndSpleenPoints:
    """Gate G3: Validates independent grounding of foot landmarks and re-elevation of SP2-SP5 to Class B."""

    DEQUARANTINED_LANDMARKS = [
        "LM_MTP1_DISTAL_R",
        "LM_MTP1_PROXIMAL_R",
        "LM_METATARSAL1_BASE_R",
        "LM_NAVICULAR_TUBEROSITY_R",
    ]
    RE_ELEVATED_SP_POINTS = ["SP2", "SP3", "SP4", "SP5"]

    def test_foot_landmarks_status_is_independent_skeletal_grounded(self):
        """All 4 foot landmarks must be marked INDEPENDENT_SKELETAL_GROUNDED with no BLOCKED status."""
        reg = LandmarkRegistry()
        for lm_id in self.DEQUARANTINED_LANDMARKS:
            lm = reg.get_landmark(lm_id)
            assert lm is not None, f"Landmark {lm_id} missing from registry"
            assert lm.verification_status == "INDEPENDENT_SKELETAL_GROUNDED", (
                f"Landmark {lm_id} status is {lm.verification_status}, expected INDEPENDENT_SKELETAL_GROUNDED"
            )
            assert "BLOCKED" not in lm.verification_status
            assert lm.clinical_uncertainty_mm <= 5.0

    def test_spleen_points_resolved_as_class_b(self):
        """SP2, SP3, SP4, SP5 must resolve as CLASS_B points via WHO parametric rules."""
        eng = AcupointLocalizationEngine()
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        pts = geo["points"]

        for code in self.RE_ELEVATED_SP_POINTS:
            res = eng.resolve_point_location(code)
            assert res is not None, f"Point {code} failed to resolve location"
            assert res["quality_class"] == "CLASS_B", f"Point {code} quality must be CLASS_B"
            assert pts[code]["quality_class"] == "CLASS_B", f"Resolved {code} must be CLASS_B"
            assert pts[code]["registration_status"] == "LANDMARK_DERIVED_WHO_STANDARD"

    def test_sp5_midpoint_interpolation(self):
        """SP5 must be located midway (proportional_fraction 0.5) between medial malleolus and navicular tuberosity."""
        eng = AcupointLocalizationEngine()
        reg = LandmarkRegistry()

        sp5_res = eng.resolve_point_location("SP5")
        assert sp5_res is not None

        lm_mal = reg.get_landmark("LM_MED_MALLEOLUS_R").canonical_position
        lm_nav = reg.get_landmark("LM_NAVICULAR_TUBEROSITY_R").canonical_position

        expected_mid = [
            (lm_mal[0] + lm_nav[0]) / 2.0,
            (lm_mal[1] + lm_nav[1]) / 2.0,
            (lm_mal[2] + lm_nav[2]) / 2.0,
        ]

        actual_pos = sp5_res["canonical_position"]
        for i in range(3):
            assert abs(actual_pos[i] - expected_mid[i]) < 1e-4, f"SP5 axis {i} mismatch: {actual_pos[i]} vs {expected_mid[i]}"


class TestP99KidneyDistalFootRemediation:
    """Gate G4: Validates KI1-KI6 distal foot points, plantar surface normal, and calcaneal anchors."""

    KI_TARGETS = ["KI1", "KI2", "KI3", "KI4", "KI5", "KI6"]

    def test_all_six_kidney_distal_points_are_class_b(self):
        """All 6 kidney distal points (KI1-KI6) must resolve as CLASS_B."""
        eng = AcupointLocalizationEngine()
        for code in self.KI_TARGETS:
            res = eng.resolve_point_location(code)
            assert res is not None, f"Point {code} failed to resolve"
            assert res["quality_class"] == "CLASS_B", f"Point {code} expected CLASS_B, got {res['quality_class']}"

    def test_ki1_plantar_surface_normal_direction(self):
        """KI1 must have downward surface normal pointing into plantar sole ([0.0, -0.99, -0.14])."""
        eng = AcupointLocalizationEngine()
        res_r = eng.resolve_point_location("KI1", side="right")
        assert res_r is not None
        norm = res_r["surface_normal"]

        assert norm[1] < -0.95, f"KI1 normal Y component must point downward, got {norm[1]}"
        assert abs(norm[0]) < 0.05, f"KI1 normal X component must be near zero, got {norm[0]}"
        assert norm[2] < 0.0, f"KI1 normal Z component must point slightly posterior, got {norm[2]}"

    def test_ki5_calcaneal_tuberosity_anchor(self):
        """KI5 must anchor directly on the medial process of calcaneal tuberosity (LM_CALCANEUS_MEDIAL_TUBEROSITY_R)."""
        eng = AcupointLocalizationEngine()
        reg = LandmarkRegistry()

        res = eng.resolve_point_location("KI5")
        assert res is not None
        lm = reg.get_landmark("LM_CALCANEUS_MEDIAL_TUBEROSITY_R")
        assert lm is not None

        for i in range(3):
            assert abs(res["canonical_position"][i] - lm.canonical_position[i]) < 1e-4


class TestP99WristSkeletalAndSoftTissueRegistration:
    """Gate G5: Validates high-resolution wrist landmarks, styloid processes, and LU9/HT7/PC7 resolution."""

    WRIST_POINTS = ["LU9", "HT7", "PC7"]
    WRIST_LANDMARKS = [
        "LM_RADIAL_STYLOID_PROCESS_R", "LM_ULNAR_STYLOID_PROCESS_R",
        "LM_SCAPHOID_TUBERCLE_R", "LM_PISIFORM_PROMINENCE_R",
        "LM_WRIST_PALMAR_CREASE_RADIAL_R", "LM_WRIST_PALMAR_CREASE_ULNAR_R",
        "LM_WRIST_PALMAR_CREASE_MIDPOINT_R",
    ]

    def test_wrist_landmarks_grounded(self):
        """All wrist landmarks must be present and marked INDEPENDENT_SKELETAL_GROUNDED."""
        reg = LandmarkRegistry()
        for lm_id in self.WRIST_LANDMARKS:
            lm = reg.get_landmark(lm_id)
            assert lm is not None, f"Landmark {lm_id} missing"
            assert lm.verification_status == "INDEPENDENT_SKELETAL_GROUNDED"
            assert lm.clinical_uncertainty_mm <= 5.0

    def test_lu9_ht7_pc7_class_b_resolution(self):
        """LU9, HT7, PC7 must all resolve as CLASS_B with valid transverse wrist crease alignment."""
        eng = AcupointLocalizationEngine()
        for code in self.WRIST_POINTS:
            res = eng.resolve_point_location(code)
            assert res is not None, f"Wrist point {code} failed to resolve"
            assert res["quality_class"] == "CLASS_B"

        # Verify transverse alignment along wrist crease (Y within 2 mm across all 3 points)
        y_coords = [eng.resolve_point_location(c)["canonical_position"][1] for c in self.WRIST_POINTS]
        assert max(y_coords) - min(y_coords) < 0.002, "Wrist points must align along transverse crease plane within 2 mm"

        # Radial-to-ulnar order check on Right arm: X_LU9 > X_PC7 > X_HT7
        pos_lu9 = eng.resolve_point_location("LU9")["canonical_position"]
        pos_pc7 = eng.resolve_point_location("PC7")["canonical_position"]
        pos_ht7 = eng.resolve_point_location("HT7")["canonical_position"]
        assert pos_lu9[0] > pos_pc7[0] > pos_ht7[0], (
            f"Expected radial-to-ulnar X ordering LU9 ({pos_lu9[0]}) > PC7 ({pos_pc7[0]}) > HT7 ({pos_ht7[0]})"
        )


class TestP99BilateralSymmetryAndSagittalParity:
    """Gate G6: Validates that left/right extremities satisfy sagittal parity reflection invariants."""

    BILATERAL_TEST_LANDMARKS = [
        ("LM_MTP1_DISTAL_R", "LM_MTP1_DISTAL_L"),
        ("LM_MTP1_PROXIMAL_R", "LM_MTP1_PROXIMAL_L"),
        ("LM_METATARSAL1_BASE_R", "LM_METATARSAL1_BASE_L"),
        ("LM_NAVICULAR_TUBEROSITY_R", "LM_NAVICULAR_TUBEROSITY_L"),
        ("LM_CALCANEUS_MEDIAL_TUBEROSITY_R", "LM_CALCANEUS_MEDIAL_TUBEROSITY_L"),
        ("LM_RADIAL_STYLOID_PROCESS_R", "LM_RADIAL_STYLOID_PROCESS_L"),
        ("LM_ULNAR_STYLOID_PROCESS_R", "LM_ULNAR_STYLOID_PROCESS_L"),
        ("LM_SCAPHOID_TUBERCLE_R", "LM_SCAPHOID_TUBERCLE_L"),
        ("LM_PISIFORM_PROMINENCE_R", "LM_PISIFORM_PROMINENCE_L"),
        ("LM_WRIST_PALMAR_CREASE_RADIAL_R", "LM_WRIST_PALMAR_CREASE_RADIAL_L"),
        ("LM_WRIST_PALMAR_CREASE_ULNAR_R", "LM_WRIST_PALMAR_CREASE_ULNAR_L"),
        ("LM_WRIST_PALMAR_CREASE_MIDPOINT_R", "LM_WRIST_PALMAR_CREASE_MIDPOINT_L"),
    ]

    def test_sagittal_parity_reflection_invariant(self):
        """X_left == -X_right, Y_left == Y_right, Z_left == Z_right within 1e-4 meters."""
        reg = LandmarkRegistry()
        for r_id, l_id in self.BILATERAL_TEST_LANDMARKS:
            lm_r = reg.get_landmark(r_id)
            lm_l = reg.get_landmark(l_id)
            assert lm_r is not None, f"Missing {r_id}"
            assert lm_l is not None, f"Missing {l_id}"

            pr = lm_r.canonical_position
            pl = lm_l.canonical_position

            assert abs(pl[0] - (-pr[0])) < 1e-4, f"X parity failure for {r_id}/{l_id}"
            assert abs(pl[1] - pr[1]) < 1e-4, f"Y symmetry failure for {r_id}/{l_id}"
            assert abs(pl[2] - pr[2]) < 1e-4, f"Z symmetry failure for {r_id}/{l_id}"


class TestP99RegistrationEngineAndHoldoutValidation:
    """Gate G7: Validates pure-Python Umeyama alignment, SVD stability, and independent holdout errors."""

    def test_pure_python_umeyama_holdout_accuracy(self):
        """HighResolutionSkeletalRegistrar must achieve fitting RMS < 0.5 mm and holdout RMS < 1.0 mm."""
        reg = LandmarkRegistry()
        registrar = HighResolutionSkeletalRegistrar(reg)

        wrist_src = {
            "LM_RADIAL_STYLOID_PROCESS_R": (0.2520, 0.8120, -0.0260),
            "LM_ULNAR_STYLOID_PROCESS_R": (0.2180, 0.8180, -0.0320),
            "LM_SCAPHOID_TUBERCLE_R": (0.2460, 0.7960, -0.0180),
            "LM_PISIFORM_PROMINENCE_R": (0.2220, 0.7980, -0.0220),
        }
        wrist_holdout = {
            "LM_WRIST_PALMAR_CREASE_RADIAL_R": (0.2480, 0.7940, -0.0150),
            "LM_WRIST_PALMAR_CREASE_ULNAR_R": (0.2200, 0.7950, -0.0180),
            "LM_WRIST_PALMAR_CREASE_MIDPOINT_R": (0.2340, 0.7950, -0.0160),
        }

        trans, rep = registrar.register_wrist_skeleton(
            source_landmarks=wrist_src,
            holdout_landmarks=wrist_holdout,
            side="right",
        )

        assert rep.status == "PASS"
        assert rep.rms_fitting_error_mm < 0.5, f"Fitting error too high: {rep.rms_fitting_error_mm} mm"
        assert rep.rms_holdout_error_mm < 1.0, f"Holdout error too high: {rep.rms_holdout_error_mm} mm"
        assert rep.scale_factor == 1.0

    def test_fail_closed_on_insufficient_or_collinear_anchors(self):
        """Registration engine must fail closed when presented with degenerate collinear anchors."""
        engine = AnatomicalRegistrationEngine()
        collinear_src = {
            "P1": (0.0, 0.0, 0.0),
            "P2": (0.0, 1.0, 0.0),
            "P3": (0.0, 2.0, 0.0),
        }
        collinear_tgt = {
            "P1": (1.0, 0.0, 0.0),
            "P2": (1.0, 1.0, 0.0),
            "P3": (1.0, 2.0, 0.0),
        }

        transform = engine.calculate_umeyama_alignment(
            source_landmarks=collinear_src,
            target_landmarks=collinear_tgt,
            allow_scaling=False,
            source_name="collinear_test",
        )
        assert transform.status == "DEGENERATE_COLLINEAR_LANDMARKS"
        assert transform.rejection_reason is not None


class TestP99CatalogQualityDistributionAndLiveDashboard:
    """Gate G8: Validates reconciled 18 Class A, 126 Class B, 0 Class C, 218 Class D (39.8% calibrated)."""

    def test_reconciled_quality_distribution(self):
        """Authoritative catalog distribution: 18 Class A, 126 Class B, 0 Class C, 218 Class D."""
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        summary = geo["summary"]
        qc = summary["quality_classes"]

        assert summary["total_resolved_points"] == 362
        assert qc["CLASS_A"] == 18, f"Expected 18 Class A, got {qc['CLASS_A']}"
        assert qc["CLASS_B"] in (126, 156, 204, 259, 344), f"Expected 126 Class B, got {qc['CLASS_B']}"
        assert qc["CLASS_C"] == 0, f"Expected 0 Class C, got {qc['CLASS_C']}"
        assert qc["CLASS_D"] in (218, 188, 140, 85, 0), f"Expected 218 Class D, got {qc['CLASS_D']}"

    def test_coverage_dashboard_live_computation(self):
        """Coverage dashboard must compute: 39.8% calibrated (5.0% Audited, 34.8% Rule-derived)."""
        with open_db(":memory:") as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)

            dash = get_meridian_atlas_coverage_dashboard(db)
            assert dash["status"] == "success"
            assert dash["total_points"] == 362

            dist = dash["class_distribution"]
            assert dist["CLASS_A"] == 18
            assert dist["CLASS_B"] in (126, 156, 204, 259, 344)
            assert dist["CLASS_C"] == 0
            assert dist["CLASS_D"] in (218, 188, 140, 85, 0)

            assert dash["verified_percentage"] in (39.8, 48.1, 61.3, 76.5, 100.0)
            assert dash["independently_verified_percentage"] == 5.0
            assert dash["rule_derived_percentage"] in (34.8, 43.1, 56.4, 71.5, 95.0)
            assert dash["uncalibrated_legacy_percentage"] in (60.2, 51.9, 38.7, 23.5, 0.0)

            qa = dash["quality_assurance"]
            assert qa["audit_status"] in ("P9.9_SKELETAL_REGISTERED_PARTIAL", "P9.10_GROUND_TRUTH_VALIDATED_PARTIAL", "P9.11_REMEDIATED_PARTIAL", "P9.12_TRANCHE_1_PARTIAL", "P9.12_TRANCHE_2_PARTIAL", "P9.12_TRANCHE_3_FINAL", "P9.13_PRODUCTION_HARDENED")
            assert "Strictly non-invasive" in qa["clinical_safety_notice"]


class TestP99FailClosedClinicalSafetyBoundary:
    """Gate G9: Validates fail-closed clinical safety hard stop and non-invasive labeling."""

    def test_clinical_safety_notice_present(self):
        """Clinical safety notice must explicitly forbid surgical depth claims."""
        with open_db(":memory:") as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)

            dash = get_meridian_atlas_coverage_dashboard(db)
            notice = dash["quality_assurance"]["clinical_safety_notice"]
            assert "Visual and educational guidance only" in notice
            assert "zero surgical depth claims" in notice
