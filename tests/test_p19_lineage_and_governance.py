"""Tests for Milestone P19: Architecture Reset & Source-of-Truth Governance.

Validates:
- Real coordinate discrepancy between Baked Static JSON and Canonical Resolver.
- LI4 bounding box violation (floating outside body mesh).
- ST36 anterior depth displacement.
- KI3 laterality sign inversion (+X Left vs +X Right conflict).
- Upstream raw fail-closed response (no synthetic constants).
- Coordinate registry documentation vs baked metadata conflict detection.
- Point digest cache invalidation.
- Strict enforcement of clinical safety hard stops.
"""

import json
import math
from pathlib import Path
import pytest

from msk_therapy_os.geometry_contracts import AcupointQualityTier, MeshIdentity, compute_point_set_digest
from msk_therapy_os.spatial_resolver import AnatomicalSpatialResolver, AUDITED_CANONICAL_POINTS
from msk_therapy_os.meridian_surface_engine import MeridianSurfacePathEngine
from research.workbench.mesh_geometry import BodyPartsSkinMesh


@pytest.fixture(scope="module")
def repo_root():
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def baked_dataset(repo_root):
    json_path = repo_root / "msk_therapy_os" / "static" / "atlas" / "data" / "acupuncture_3d.json"
    assert json_path.exists(), "Baked acupuncture_3d.json must exist"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def authentic_mesh(repo_root):
    mesh_path = repo_root / "2data" / "artifacts" / "fj2810_softened.bin"
    assert mesh_path.exists(), "fj2810_softened.bin must exist"
    return BodyPartsSkinMesh(mesh_type="softened")


@pytest.fixture(scope="module")
def resolver():
    return AnatomicalSpatialResolver()


class TestP19CoordinateLineageAndMeshAudit:
    """Validate empirical mesh queries and coordinate lineage invariants."""

    def test_authentic_mesh_bounds_and_checksum(self, authentic_mesh):
        """Authentic skin mesh must match expected BodyParts3D FJ2810 checksum and bounding extents."""
        assert authentic_mesh.bin_sha256 == "05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808"
        min_v = authentic_mesh.vertices.min(axis=0)
        max_v = authentic_mesh.vertices.max(axis=0)
        # Width ~0.667m, Height ~1.719m, Depth ~0.292m
        assert -0.335 < min_v[0] < -0.330
        assert 0.330 < max_v[0] < 0.335
        assert 0.0 <= min_v[1] < 0.001
        assert 1.715 < max_v[1] < 1.725

    def test_li4_bounding_box_violation(self, authentic_mesh, baked_dataset, resolver):
        """Canonical LI4 floats in air outside the human body mesh bounding box."""
        max_x = authentic_mesh.vertices.max(axis=0)[0]
        
        # 1. Baked LI4 is inside mesh and on skin surface
        baked_li4 = baked_dataset["points"]["LI4"]["position"]
        q_b = authentic_mesh.query_point(baked_li4)
        assert baked_li4[0] < max_x
        assert q_b["distance_mm"] < 0.1, "Baked LI4 must lie exactly on authentic mesh surface"

        # 2. Canonical LI4 exceeds bounding box
        canon_li4 = resolver.resolve_point("LI4", "canonical", {}, {})["resolved_world_position"]
        assert canon_li4[0] > max_x, f"Canonical LI4 X ({canon_li4[0]}) must exceed max mesh X ({max_x})"
        excess_mm = (canon_li4[0] - max_x) * 1000.0
        assert 8.0 < excess_mm < 11.0, f"Excess should be ~9.25mm outside body, got {excess_mm:.2f}mm"

        # 3. Discrepancy between baked and canonical > 80mm
        discrepancy = math.sqrt(sum((a - b)**2 for a, b in zip(baked_li4, canon_li4))) * 1000.0
        assert discrepancy > 85.0, f"Discrepancy must be > 85mm, got {discrepancy:.2f}mm"

    def test_st36_anterior_depth_divergence(self, authentic_mesh, baked_dataset, resolver):
        """Canonical ST36 floats ~4.5 cm in front of the tibia surface on authentic mesh."""
        baked_st36 = baked_dataset["points"]["ST36"]["position"]
        q_b = authentic_mesh.query_point(baked_st36)
        assert q_b["distance_mm"] < 0.1, "Baked ST36 must lie directly on skin surface"

        canon_st36 = resolver.resolve_point("ST36", "canonical", {}, {})["resolved_world_position"]
        q_c = authentic_mesh.query_point(canon_st36)
        assert q_c["distance_mm"] > 40.0, f"Canonical ST36 must deviate > 40mm from mesh, got {q_c['distance_mm']}mm"
        assert q_c["signed_distance_mm"] > 40.0, "Canonical ST36 must be hovering anterior to the leg"

    def test_ki3_laterality_sign_inversion_conflict(self, baked_dataset, resolver):
        """KI3 exhibits massive ~175mm discrepancy due to +X Left vs +X Right laterality inversion."""
        baked_ki3 = baked_dataset["points"]["KI3"]["position"]
        canon_ki3 = resolver.resolve_point("KI3", "canonical", {}, {})["resolved_world_position"]

        # In baked JSON (+X Left): Right leg has negative X
        assert baked_ki3[0] < -0.05, f"Baked KI3 X must be negative for right leg, got {baked_ki3[0]}"
        # In canonical rule (+X Right): Right leg was computed with positive X
        assert canon_ki3[0] > 0.05, f"Canonical KI3 X was computed positive, got {canon_ki3[0]}"

        # Discrepancy exceeds 160 mm
        discrepancy = math.sqrt(sum((a - b)**2 for a, b in zip(baked_ki3, canon_ki3))) * 1000.0
        assert discrepancy > 170.0, f"KI3 discrepancy must be > 170mm, got {discrepancy:.2f}mm"


class TestP19GovernanceAndContracts:
    """Validate data integrity, safety invariant enforcement, and fail-closed contracts."""

    def test_coordinate_metadata_conflict_documented(self, repo_root, baked_dataset):
        """System documents the discrepancy between COORDINATE_REGISTRY.md and acupuncture_3d.json."""
        metadata = baked_dataset.get("metadata", {})
        coord_sys = metadata.get("coordinate_system", "")
        assert "+X Left" in coord_sys, f"Baked JSON must declare +X Left convention, got: {coord_sys}"

        registry_path = repo_root / "1docs" / "COORDINATE_REGISTRY.md"
        assert registry_path.exists()
        reg_text = registry_path.read_text(encoding="utf-8")
        assert "$+X$: Right" in reg_text, "Registry must document historical +X: Right expectation"

    def test_upstream_raw_fail_closed(self, resolver):
        """Upstream raw layer mode must fail-closed with UPSTREAM_TRANSFORM_UNAVAILABLE."""
        res = resolver.resolve_point("LI4", "upstream_raw", {}, {})
        assert res["registration_status"] == "UPSTREAM_TRANSFORM_UNAVAILABLE"
        assert "Synthetic offset removed" in res["rejection_reason"]
        # Legacy coordinates returned without artificial offset
        legacy = res["legacy_position"]
        resolved = res["resolved_world_position"]
        assert legacy == resolved, "No synthetic offsets may be added"

    def test_point_digest_invalidation_governance(self):
        """Mutating point coordinates changes the SHA-256 point digest."""
        pts_v1 = {
            "LI1": {"position": [0.35, 0.70, 0.05], "normal": [0.0, 1.0, 0.0]},
            "LI4": {"position": [0.286, 0.831, 0.014], "normal": [0.35, -0.32, -0.87]},
        }
        pts_v2 = {
            "LI1": {"position": [0.35, 0.70, 0.05], "normal": [0.0, 1.0, 0.0]},
            "LI4": {"position": [0.286, 0.831, 0.084], "normal": [0.35, -0.32, -0.87]},  # Mutated Z +70mm
        }
        digest1 = compute_point_set_digest(pts_v1)
        digest2 = compute_point_set_digest(pts_v2)
        assert digest1 != digest2, "Point digest must change when any coordinate mutates"
        assert len(digest1) == 16
        assert len(digest2) == 16

    def test_safety_invariants_fail_closed(self, repo_root):
        """Safety invariants remain locked to non-clinical research boundaries."""
        from msk_therapy_os import biomechanics_adapter as ba
        from msk_therapy_os import scientific_claim_guard as scg

        assert ba.RELEASE_SCOPE == "ENGINEERING_RESEARCH_ONLY"
        assert ba.CLINICAL_VALIDATION == "NOT_ESTABLISHED"
        assert ba.CLINICAL_DEPTH_GUIDANCE_ALLOWED is False

        # In server.py
        server_path = repo_root / "msk_therapy_os" / "server.py"
        server_text = server_path.read_text(encoding="utf-8")
        assert '"clinical_depth_guidance_allowed": False' in server_text
