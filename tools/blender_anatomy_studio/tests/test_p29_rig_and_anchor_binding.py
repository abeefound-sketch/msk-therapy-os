"""Test suite for Milestone P29: Anatomical Rig Binding, Surface Anchor Registry & Prohibitions."""
import pytest
from pathlib import Path

from tools.blender_anatomy_studio.addon.surface_anchor_registry import AnatomicalSurfaceAnchorRegistry
from tools.blender_anatomy_studio.addon.rig_binding_adapter import AnatomicalRigBindingAdapter

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / "1docs" / "audits" / "P29" / "evidence"
SCREENSHOT_DIR = REPO_ROOT / "1docs" / "audits" / "P29" / "screenshots"


class TestP29SurfaceAnchorRegistryAndProhibitions:
    def test_prohibit_li4_on_humerus_or_arm(self):
        reg = AnatomicalSurfaceAnchorRegistry()
        with pytest.raises(ValueError, match="ANATOMICAL BINDING VIOLATION"):
            reg.register_anchor(
                marker_id="illegal_li4",
                code="LI4",
                target_mesh_name="Humerus_R",
                target_bone_name="upper_arm.R",
                local_coordinates=(0.0, 0.0, 0.0),
                local_normal=(0.0, 1.0, 0.0),
                mesh_hash="hash123"
            )

    def test_prohibit_st36_and_ki3_on_shoulder_or_arm(self):
        reg = AnatomicalSurfaceAnchorRegistry()
        with pytest.raises(ValueError, match="ANATOMICAL BINDING VIOLATION"):
            reg.register_anchor(
                marker_id="illegal_st36",
                code="ST36",
                target_mesh_name="Scapula_R",
                target_bone_name="clavicle.R",
                local_coordinates=(0.0, 0.0, 0.0),
                local_normal=(0.0, 1.0, 0.0),
                mesh_hash="hash123"
            )

        with pytest.raises(ValueError, match="ANATOMICAL BINDING VIOLATION"):
            reg.register_anchor(
                marker_id="illegal_ki3",
                code="KI3",
                target_mesh_name="Clavicle_R",
                target_bone_name="clavicle.R",
                local_coordinates=(0.0, 0.0, 0.0),
                local_normal=(0.0, 1.0, 0.0),
                mesh_hash="hash123"
            )

    def test_register_legitimate_arm_anchors_succeeds(self):
        reg = AnatomicalSurfaceAnchorRegistry()
        a_li14 = reg.register_anchor(
            marker_id="valid_li14",
            code="LI14",
            target_mesh_name="Humerus_R",
            target_bone_name="upper_arm.R",
            local_coordinates=(0.03, -0.01, -0.15),
            local_normal=(0.8, 0.0, 0.6),
            mesh_hash="hash_humerus"
        )
        assert a_li14["verification_status"] == "VALID_SURFACE_ANCHOR"
        assert a_li14["fma_id"] == "FMA:23412"

        a_li15 = reg.register_anchor(
            marker_id="valid_li15",
            code="LI15",
            target_mesh_name="Scapula_R",
            target_bone_name="clavicle.R",
            local_coordinates=(0.02, 0.02, 0.04),
            local_normal=(0.0, 0.7, 0.7),
            mesh_hash="hash_scapula"
        )
        assert a_li15["verification_status"] == "VALID_SURFACE_ANCHOR"
        assert a_li15["fma_id"] == "FMA:23240"


class TestP29RigBindingAdapterAndRhythm:
    def test_audit_scene_structures_marks_missing(self):
        present_meshes = ["Humerus_R", "Clavicle_R", "Scapula_R", "Thorax"]
        audit = AnatomicalRigBindingAdapter.audit_scene_structures(present_meshes)
        assert audit["present_structures"]["Humerus_R"]["status"] == "AVAILABLE"
        assert audit["missing_structures"]["Metacarpals_R"]["status"] == "ASSET_NOT_AVAILABLE"
        assert audit["missing_structures"]["Tibia_R"]["status"] == "ASSET_NOT_AVAILABLE"

    def test_scapulohumeral_rhythm_ratio(self):
        res = AnatomicalRigBindingAdapter.apply_scapulohumeral_rhythm(None, thoracohumeral_elevation_deg=90.0)
        assert abs(res["scapular_elevation_deg"] - 30.0) < 0.1
        assert abs(res["glenohumeral_elevation_deg"] - 60.0) < 0.1
        assert "2:1" in res["rhythm_ratio"]


class TestP29BlenderEvidenceArtifacts:
    def test_saved_blend_file_and_screenshots_exist(self):
        blend = EVIDENCE_DIR / "p29_anatomical_rig_binding.blend"
        s1 = SCREENSHOT_DIR / "01_p29_pose_a_rest_0deg.png"
        s2 = SCREENSHOT_DIR / "02_p29_pose_b_mid_45deg.png"
        s3 = SCREENSHOT_DIR / "03_p29_pose_c_elevated_90deg.png"

        assert blend.exists(), "p29_anatomical_rig_binding.blend must exist"
        assert blend.stat().st_size > 2_000_000
        assert s1.exists(), "01_p29_pose_a_rest_0deg.png must exist"
        assert s2.exists(), "02_p29_pose_b_mid_45deg.png must exist"
        assert s3.exists(), "03_p29_pose_c_elevated_90deg.png must exist"
