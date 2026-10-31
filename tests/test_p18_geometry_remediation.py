"""MSK-Therapy-OS - Milestone P18: Anatomical Geometry Remediation & Verification Suite.

Validates complete forensic remediation of the 10 audit findings from P17:
- G0: Mesh asset presence, checksums, and baseline integrity.
- G1: Two-source spatial discrepancy ledger and surface registration proof.
- G2: Removal of synthetic upstream offsets (Fail-closed UPSTREAM_TRANSFORM_UNAVAILABLE).
- G3: MeridianSurfacePathEngine cryptographic cache invalidation.
- G4: Quality Tier classification governance and taxonomy enforcement.
- G5: Clinical restriction guardrails (ENGINEERING_RESEARCH_ONLY).
- G6: Procedural fallback transparency and unverified geometry warnings.
- G7: Comprehensive documentation and audit artifact verification.

Pure Python 3.11, standard library + pytest + numpy.
"""

import hashlib
import json
import math
from pathlib import Path
import pytest

from msk_therapy_os.geometry_contracts import (
    AcupointQualityTier,
    MeshIdentity,
    MeshVerificationStatus,
    compute_point_set_digest,
)
from msk_therapy_os.meridian_surface_engine import MeridianSurfacePathEngine
from msk_therapy_os.spatial_resolver import (
    AnatomicalSpatialResolver,
    AUDITED_CANONICAL_POINTS,
    CANONICAL_MESH_HASH,
    CANONICAL_MESH_ID,
)
from research.workbench.mesh_geometry import BodyPartsSkinMesh

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestP18GateG0BaselineIntegrity:
    """Gate G0: Baseline mesh assets, canonical checksums, and physical geometry."""

    def test_authentic_fj2810_mesh_binary_integrity(self):
        """Softened authentic BodyParts3D skin mesh must exist with exact SHA256."""
        mesh_path = REPO_ROOT / "2data" / "artifacts" / "fj2810_softened.bin"
        assert mesh_path.exists(), f"Mesh binary missing at {mesh_path}"
        data = mesh_path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        assert digest == CANONICAL_MESH_HASH
        assert digest == BodyPartsSkinMesh.EXPECTED_SOFTENED_BIN_SHA256

        # Check vertex and index structure
        mesh = BodyPartsSkinMesh(mesh_type="softened")
        assert len(mesh.vertices) == 24958
        assert mesh.num_faces == 46174

    def test_baked_static_dataset_checksum_integrity(self):
        """Static reference acupuncture_3d.json must match recorded P9 release hash."""
        json_path = REPO_ROOT / "msk_therapy_os" / "static" / "atlas" / "data" / "acupuncture_3d.json"
        assert json_path.exists()
        digest = hashlib.sha256(json_path.read_bytes()).hexdigest()
        assert digest == "47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df"


class TestP18GateG1SpatialReconciliation:
    """Gate G1: Reconciliation and forensic proof between static baked JSON and canonical resolver."""

    def test_reconciliation_audit_artifacts_exist(self):
        """Authoritative P18 reconciliation CSV and JSON must exist with 362 points."""
        csv_path = REPO_ROOT / "1docs" / "audits" / "P18" / "P18_ACUPOINT_RECONCILIATION.csv"
        json_path = REPO_ROOT / "1docs" / "audits" / "P18" / "P18_ACUPOINT_RECONCILIATION.json"
        assert csv_path.exists()
        assert json_path.exists()

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["total_points_evaluated"] == 362
        assert data["divergence_metrics"]["delta_ge_100mm"] == 28
        assert data["divergence_metrics"]["delta_ge_50mm"] == 130
        assert data["divergence_metrics"]["delta_ge_20mm"] == 219
        assert data["divergence_metrics"]["worst_divergent_point"] == "KI3"
        assert abs(data["divergence_metrics"]["max_delta_mm"] - 175.45) < 0.1

    def test_baked_points_correspond_to_authentic_fj2810_surface(self):
        """Forensic proof: Baked points (e.g. LI4, ST36) lie directly on fj2810_softened mesh (<0.2 mm)."""
        mesh = BodyPartsSkinMesh(mesh_type="softened")

        # Baked LI4 [0.286, 0.831, 0.01414]
        res_li4 = mesh.query_point([0.286, 0.831, 0.01414])
        assert res_li4["distance_mm"] < 0.20, f"Expected LI4 baked on mesh, got {res_li4['distance_mm']} mm"

        # Baked ST36 [0.111, 0.368, 0.01463]
        res_st36 = mesh.query_point([0.111, 0.368, 0.01463])
        assert res_st36["distance_mm"] < 0.05, f"Expected ST36 baked on mesh, got {res_st36['distance_mm']} mm"

    def test_canonical_li4_bounds_outside_mesh(self):
        """Forensic confirmation: Canonical LI4 (X=0.342) floats outside the mesh bounding box (X_max=0.3328)."""
        mesh = BodyPartsSkinMesh(mesh_type="softened")
        max_x = float(mesh.vertices[:, 0].max())
        assert max_x < 0.3340
        canonical_li4_x = AUDITED_CANONICAL_POINTS["LI4"]["canonical_position"][0]
        assert canonical_li4_x == 0.342
        assert canonical_li4_x > max_x, "Canonical LI4 must exceed body mesh bounding box (+9.2 mm offset)"


class TestP18GateG2UpstreamGovernance:
    """Gate G2: Upstream raw coordinate conversion governance and synthetic offset removal."""

    def test_upstream_raw_synthetic_offsets_removed(self):
        """upstream_raw layer must NOT inject fake dx/dy/dz; returns legacy pos with explicit rejection status."""
        resolver = AnatomicalSpatialResolver()
        res_legacy = resolver.resolve_point("LI4", "legacy_raycast", {}, {})
        res_upstream = resolver.resolve_point("LI4", "upstream_raw", {}, {})

        assert res_upstream["registration_status"] == "UPSTREAM_TRANSFORM_UNAVAILABLE"
        assert res_upstream["rejection_reason"] is not None
        assert "Synthetic offset removed" in res_upstream["rejection_reason"]
        assert res_upstream["resolved_world_position"] == res_legacy["resolved_world_position"]


class TestP18GateG3CacheIntegrity:
    """Gate G3: MeridianSurfacePathEngine cryptographic invalidation on point mutation."""

    def test_meridian_engine_cache_invalidates_on_point_mutation(self):
        """Modifying point coordinates invalidates the cache key and returns a freshly recalculated path."""
        resolver = AnatomicalSpatialResolver()
        engine = MeridianSurfacePathEngine()

        resolved = {}
        for i in range(1, 21):
            code = f"LI{i}"
            resolved[code] = resolver.resolve_point(code, "canonical", {}, {})

        li_meta = {"points": [f"LI{i}" for i in range(1, 21)]}
        path1 = engine.reconstruct_channel("LI", li_meta, resolved, "right", "canonical")
        assert path1 is not None
        v0_initial = list(path1["surface_vertices"][0])

        # Mutate LI1 coordinates (+70 mm on each axis)
        resolved_mutated = dict(resolved)
        li1_mutated = dict(resolved["LI1"])
        mutated_pos = [v0_initial[0] + 0.070, v0_initial[1] + 0.070, v0_initial[2] + 0.070]
        li1_mutated["resolved_world_position"] = mutated_pos
        li1_mutated["canonical_position"] = mutated_pos
        li1_mutated["instances"] = [{"side": "right", "position": mutated_pos, "normal": [0, 0, 1]}]
        resolved_mutated["LI1"] = li1_mutated

        path2 = engine.reconstruct_channel("LI", li_meta, resolved_mutated, "right", "canonical")

        assert path2 is not path1, "Engine returned stale cached object after point mutation!"
        assert path2["surface_vertices"][0] != v0_initial, "Vertex 0 did not reflect mutated coordinates!"
        assert abs(path2["surface_vertices"][0][0] - mutated_pos[0]) < 0.001


class TestP18GateG4QualityClassification:
    """Gate G4: Quality Tier Taxonomy and Classification Contracts."""

    def test_quality_tier_taxonomy_contract(self):
        """Enums match the authoritative 5-tier classification."""
        assert AcupointQualityTier.EXPERT_REVIEWED.value == "CLASS_A"
        assert AcupointQualityTier.LANDMARK_DERIVED.value == "CLASS_B"
        assert AcupointQualityTier.SURFACE_ONLY_APPROXIMATE.value == "CLASS_D"
        assert AcupointQualityTier.UNVERIFIED.value == "CLASS_E"
        assert AcupointQualityTier.UNAVAILABLE.value == "UNAVAILABLE"

    def test_point_digest_computation(self):
        """compute_point_set_digest produces a 16-hex deterministic hash."""
        pts = {
            "LI1": {"resolved_world_position": [0.28, 0.83, 0.01], "surface_normal": [0, 0, 1]},
            "LI4": {"resolved_world_position": [0.29, 0.84, 0.02], "surface_normal": [0, 1, 0]},
        }
        d1 = compute_point_set_digest(pts)
        d2 = compute_point_set_digest(pts)
        assert d1 == d2
        assert len(d1) == 16


class TestP18GateG5ClinicalRestrictionGuardrails:
    """Gate G5: Clinical safety flags and research-only scopes."""

    def test_clinical_safety_boundaries_preserved(self):
        """System strictly maintains non-clinical research classification."""
        from msk_therapy_os.spatial_resolver import AnatomicalSpatialResolver
        resolver = AnatomicalSpatialResolver()
        res = resolver.resolve_point("LI4", "canonical", {}, {})
        # Gate G5: Depth/surgical guidance is strictly disallowed under fail-closed governance
        assert "surgical_depth_mm" not in res
        assert "clinical_penetration_vector" not in res


class TestP18GateG6ProceduralFallbackTransparency:
    """Gate G6: Transparency regarding procedural mannequin geometry."""

    def test_procedural_fallback_status_contract(self):
        """MeshIdentity dataclass properly flags procedural fallback."""
        identity = MeshIdentity(
            mesh_id="DEMO-BODY",
            mesh_sha256="PROCEDURAL_HASH",
            verification_status=MeshVerificationStatus.PROCEDURAL_DEMO_MANNEQUIN,
            is_procedural_fallback=True,
            disclaimer="[UNVERIFIED PROCEDURAL GEOMETRY] Demo Mannequin",
        )
        d = identity.to_dict()
        assert d["is_procedural_fallback"] is True
        assert d["verification_status"] == "PROCEDURAL_DEMO_MANNEQUIN"


class TestP18GateG7DocumentationArtifacts:
    """Gate G7: Authoritative audit documentation in 1docs/audits/P18/."""

    @pytest.mark.parametrize("filename", [
        "P18_ANATOMICAL_ROOT_CAUSE.md",
        "P18_MESH_ASSET_PROVENANCE.md",
        "P18_ROUTE_TOPOLOGY_AND_SURFACE_QA.md",
        "P18_EXTERNAL_REFERENCE_LICENSES.md",
        "P18_TEST_AND_RELEASE_MATRIX.md",
        "P18_HANDOFF_APPEND.md",
        "P18_ACUPOINT_RECONCILIATION.csv",
        "P18_ACUPOINT_RECONCILIATION.json",
    ])
    def test_mandatory_audit_file_presence(self, filename):
        file_path = REPO_ROOT / "1docs" / "audits" / "P18" / filename
        assert file_path.exists(), f"Mandatory P18 audit file {filename} missing at {file_path}"
