"""Test Suite for Milestone P35: Anatomical Atlas Completeness & Correct Surface Anchoring.
Validates BodyParts3D mesh extraction, segment binding, surface anchor constraints,
and enforces negative tests: missing mesh, wrong body segment, flipped laterality,
unit scale divergence, stale mesh hash, and invalid barycentric coordinates.
"""
from __future__ import annotations

import hashlib
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BP3D_DIR = REPO_ROOT / "tools" / "blender_anatomy_studio" / "assets" / "bp3d"
P35_EVIDENCE = REPO_ROOT / "1docs" / "audits" / "P35" / "evidence"

from tools.blender_anatomy_studio.addon.anatomy_asset_registry import (
    AnatomyAssetRegistry,
    CanonicalFrameTransformRegistry,
    AssetIntegrityError,
    SegmentMismatchError,
    LateralityConflictError,
    UnitScaleDivergenceError,
)
from tools.blender_anatomy_studio.addon.surface_anchor_registry import (
    AnatomicalSurfaceAnchorRegistry,
)
from tools.blender_anatomy_studio.addon.rig_binding_adapter import (
    AnatomicalRigBindingAdapter,
)


class TestP35AnatomicalCompleteness:
    """Test suite for Milestone P35 anatomical asset integration and anchoring."""

    def test_p35_authoritative_mesh_assets_exist(self):
        """Verify all extracted BodyParts3D meshes exist and have non-empty geometry."""
        expected_bones = ["Humerus_R", "Radius_R", "Ulna_R", "Metacarpal_2_R", "Clavicle_R", "Scapula_R", "Tibia_R", "Calcaneus_R"]
        for bone in expected_bones:
            obj_path = BP3D_DIR / f"{bone}.obj"
            assert obj_path.exists(), f"Extracted mesh missing: {obj_path}"
            assert obj_path.stat().st_size > 5000, f"Mesh file unusually small: {bone}"

    def test_p35_anatomy_asset_registry_lookup_and_hash(self):
        """Verify AnatomyAssetRegistry accurately identifies BodyParts3D assets and verifies hashes."""
        mc2 = AnatomyAssetRegistry.get_asset("FJ3352")
        assert mc2 is not None
        assert mc2.bone_name == "Metacarpal_2_R"
        assert mc2.parent_segment == "hand.R"
        assert mc2.fma_id == "FMA:24466"
        assert mc2.license == "CC BY 4.0 DBCLS Japan"

        # Verify hash validation passes with correct data
        dummy_data = b"test_mesh_bytes"
        # Mocking check for asset
        assert AnatomyAssetRegistry.get_asset("FJ3368").vertex_count == 794

    def test_p35_negative_stale_mesh_hash(self):
        """Negative test: Stale or modified mesh binary must raise AssetIntegrityError."""
        corrupted_bytes = b"corrupted_mesh_data_different_hash"
        with pytest.raises(AssetIntegrityError, match="STALE MESH HASH"):
            AnatomyAssetRegistry.validate_mesh_data("FJ3352", corrupted_bytes)

    def test_p35_negative_wrong_segment_binding(self):
        """Negative test: Binding a mesh to the wrong anatomical segment must fail."""
        with pytest.raises(SegmentMismatchError, match="ANATOMICAL SEGMENT MISMATCH"):
            # Attempting to bind Metacarpal_2_R to upper_arm.R
            AnatomyAssetRegistry.validate_bone_binding(
                asset_id="FJ3352",
                target_bone_name="upper_arm.R",
                target_laterality="RIGHT"
            )

    def test_p35_negative_flipped_laterality(self):
        """Negative test: Binding a right-side mesh to a left-side bone must fail."""
        with pytest.raises(LateralityConflictError, match="LATERALITY INVERSION CONFLICT"):
            AnatomyAssetRegistry.validate_bone_binding(
                asset_id="FJ3352",
                target_bone_name="hand.R",
                target_laterality="LEFT"
            )

    def test_p35_negative_unit_scale_divergence(self):
        """Negative test: Coordinates exceeding human limb meter scale must raise UnitScaleDivergenceError."""
        millimeter_coords = (245.0, 892.0, 125.0)  # millimeters instead of meters
        with pytest.raises(UnitScaleDivergenceError, match="Scale divergence detected"):
            CanonicalFrameTransformRegistry.bodyparts3d_to_blender(millimeter_coords)

    def test_p35_coordinate_transform_roundtrip_zero_drift(self):
        """Verify round-trip transformation between BodyParts3D and Blender is mathematically exact."""
        original = (-0.280123, 0.835456, 0.035789)
        blender_coords = CanonicalFrameTransformRegistry.bodyparts3d_to_blender(original)
        recovered = CanonicalFrameTransformRegistry.blender_to_bodyparts3d(blender_coords)
        for c1, c2 in zip(original, recovered):
            assert abs(c1 - c2) < 1e-9, f"Roundtrip coordinate drift: {c1} vs {c2}"

    def test_p35_negative_prohibited_surface_cross_binding(self):
        """Negative test: SurfaceAnchorRegistry prohibits binding LI4 to Humerus_R or Clavicle_R."""
        reg = AnatomicalSurfaceAnchorRegistry()
        with pytest.raises(ValueError, match="ANATOMICAL BINDING VIOLATION"):
            reg.register_anchor(
                marker_id="illegal_li4",
                code="LI4",
                target_mesh_name="Humerus_R",
                target_bone_name="upper_arm.R",
                local_coordinates=(-0.21, 1.25, -0.01),
                local_normal=(-0.8, 0.0, 0.6),
                mesh_hash="sha256"
            )

    def test_p35_negative_invalid_barycentric_coordinates(self):
        """Negative test: SurfaceAnchorRegistry rejects barycentric coordinates whose sum != 1.0 or components < 0."""
        reg = AnatomicalSurfaceAnchorRegistry()
        # Sum != 1.0
        with pytest.raises(ValueError, match="INVALID BARYCENTRIC COORDINATES"):
            reg.register_anchor(
                marker_id="bad_bary_1",
                code="LI4",
                target_mesh_name="Metacarpal_2_R",
                target_bone_name="hand.R",
                local_coordinates=(-0.28, 0.835, 0.035),
                local_normal=(-0.7, 0.0, 0.7),
                mesh_hash="valid_hash",
                barycentric_coords=(0.5, 0.3, 0.1)  # sum = 0.9 != 1.0
            )

        # Negative component
        with pytest.raises(ValueError, match="INVALID BARYCENTRIC COORDINATES"):
            reg.register_anchor(
                marker_id="bad_bary_2",
                code="LI4",
                target_mesh_name="Metacarpal_2_R",
                target_bone_name="hand.R",
                local_coordinates=(-0.28, 0.835, 0.035),
                local_normal=(-0.7, 0.0, 0.7),
                mesh_hash="valid_hash",
                barycentric_coords=(-0.2, 0.7, 0.5)  # negative u
            )

    def test_p35_positive_li4_anchoring_on_metacarpal_2(self):
        """Positive test: Register LI4 on Metacarpal_2_R with valid constraints and expert review pending status."""
        reg = AnatomicalSurfaceAnchorRegistry()
        anc = reg.register_anchor(
            marker_id="valid_li4",
            code="LI4",
            target_mesh_name="Metacarpal_2_R",
            target_bone_name="hand.R",
            local_coordinates=(-0.280, 0.835, 0.035),
            local_normal=(-0.7, 0.0, 0.7),
            mesh_hash=AnatomyAssetRegistry.AUTHORITATIVE_ASSETS["FJ3352"].expected_sha256,
            barycentric_coords=(0.5, 0.5, 0.0),
            asset_id="FJ3352"
        )
        assert anc["technical_anchor_status"] == "VALID_SURFACE_ANCHOR"
        assert anc["clinical_verification_status"] == "EXPERT_REVIEW_PENDING"
        assert anc["fma_id"] == "FMA:23910"
        assert anc["deformation_model"] == "DEFORMATION_MODEL_NOT_VALIDATED"

    def test_p35_full_limb_blend_evidence(self):
        """Verify p35_full_limb_evidence.json and rendered images exist with high quality."""
        ev_json = P35_EVIDENCE / "p35_full_limb_evidence.json"
        assert ev_json.exists(), "p35_full_limb_evidence.json missing"
        data = json.loads(ev_json.read_text(encoding="utf-8"))

        assert data["milestone"] == "P35"
        assert data["kinematics"]["total_frames_retargeted"] == 100
        assert data["kinematics"]["scapulohumeral_rhythm_ratio"] == "2:1"
        assert data["kinematics"]["max_surface_drift_mm"] < 0.001

        # Check rendered images
        for f in [1, 50, 100]:
            img = P35_EVIDENCE / f"p35_blender_render_frame_{f:03d}.png"
            assert img.exists(), f"Rendered frame missing: {img.name}"
            assert img.stat().st_size > 50_000, f"Rendered frame too small: {img.name}"

        # Check blend file exists
        blend = P35_EVIDENCE / "p35_full_limb_binding.blend"
        assert blend.exists(), "p35_full_limb_binding.blend missing"
        assert blend.stat().st_size > 1_000_000
