"""Automated test suite for P21 Blender Anatomical Studio contracts and headless pipeline."""
import json
import subprocess
from pathlib import Path
import pytest

from tools.blender_anatomy_studio.contracts import load_schema, validate_contract
from tools.blender_anatomy_studio.addon.layers import classify_object_name
from tools.blender_anatomy_studio.addon.notes import (
    generate_markdown_note,
    RELEASE_SCOPE,
    CLINICAL_VALIDATION,
    CLINICAL_DEPTH_GUIDANCE_ALLOWED
)
from tools.blender_anatomy_studio.addon.rig import ArmKinematicsSolver

REPO_ROOT = Path(__file__).resolve().parents[3]

class TestP21ContractsAndSafetyInvariants:
    def test_safety_invariants(self):
        assert RELEASE_SCOPE == "ENGINEERING_RESEARCH_ONLY"
        assert CLINICAL_VALIDATION == "NOT_ESTABLISHED"
        assert CLINICAL_DEPTH_GUIDANCE_ALLOWED is False

    def test_schema_loading(self):
        manifest_schema = load_schema("anatomy_asset_manifest")
        assert manifest_schema["title"] == "AnatomyAssetManifest"
        annot_schema = load_schema("annotation")
        assert annot_schema["title"] == "AnatomicalAnnotation"
        joint_schema = load_schema("joint_constraint")
        assert joint_schema["title"] == "JointConstraint"
        motion_schema = load_schema("motion_sequence")
        assert motion_schema["title"] == "MotionSequence"

    def test_manifest_contract_validation(self):
        valid_manifest = {
            "schema_version": "1.0.0",
            "source_id": "BodyParts3D_4.0_DBCLS",
            "asset_sha256": "a" * 64,
            "license_id": "CC-BY-4.0",
            "license_scope": "COMMERCIAL_PERMITTED_WITH_ATTRIBUTION",
            "attribution": "BodyParts3D © DBCLS",
            "structure_ids": ["Humerus_R", "Clavicle_R"],
            "frame_id": "canonical_bodyparts3d_meters_y_up",
            "units": "meters",
            "mesh_transform": [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            "anatomy_classes": ["BONE"],
            "review_status": "USER_ANNOTATED_UNVERIFIED"
        }
        ok, err = validate_contract(valid_manifest, "anatomy_asset_manifest")
        assert ok, f"Expected manifest to pass: {err}"

    def test_annotation_contract_validation(self):
        valid_annot = {
            "schema_version": "1.0.0",
            "annotation_id": "annot_test_123",
            "type": "ACUPOINT",
            "name": "Hợp Cốc (LI4)",
            "code": "LI4",
            "structure_id": "Humerus_R",
            "mesh_hash": "b" * 64,
            "surface_anchor": {
                "method": "local_coordinates",
                "triangle_id": 42,
                "local_position": [0.1, 0.2, 0.3],
                "normal": [0.0, 1.0, 0.0]
            },
            "global_position": [0.15, 0.25, 0.35],
            "transform_version": "1.0.0",
            "side": "RIGHT",
            "author": "Tester",
            "source_claim_ids": ["CLAIM_001"],
            "review_status": "USER_ANNOTATED_UNVERIFIED",
            "uncertainty_mm": 5.0,
            "created_at": "2026-11-02T12:00:00Z"
        }
        ok, err = validate_contract(valid_annot, "annotation")
        assert ok, f"Expected annotation to pass: {err}"

    def test_annotation_forbids_fake_clinical_approved(self):
        fake_annot = {
            "schema_version": "1.0.0",
            "annotation_id": "annot_fake_123",
            "type": "ACUPOINT",
            "structure_id": "Humerus_R",
            "mesh_hash": "b" * 64,
            "surface_anchor": {"method": "local_coordinates", "local_position": [0.0, 0.0, 0.0]},
            "global_position": [0.0, 0.0, 0.0],
            "transform_version": "1.0.0",
            "side": "RIGHT",
            "author": "Tester",
            "source_claim_ids": [],
            "review_status": "CLINICAL_APPROVED", # Prohibited
            "uncertainty_mm": 5.0,
            "created_at": "2026-11-02T12:00:00Z"
        }
        ok, err = validate_contract(fake_annot, "annotation")
        assert not ok, "Expected validation to fail for unauthorized CLINICAL_APPROVED status"

    def test_layer_classification_rules(self):
        assert classify_object_name("Humerus_R") == "BONE"
        assert classify_object_name("Clavicle_R") == "BONE"
        assert classify_object_name("Scapula_R") == "BONE"
        assert classify_object_name("Biceps_Brachii") == "MUSCLE"
        assert classify_object_name("Heart_Left_Ventricle") == "ORGAN"
        assert classify_object_name("Outer_Skin_Surface") == "SKIN"
        assert classify_object_name("Camera_Rig") == "OTHER"

    def test_vietnamese_markdown_note_generation(self):
        md = generate_markdown_note(
            title="Thử nghiệm Ghi chú Giải phẫu",
            structure_or_channel="Chi Trên",
            author="Test Runner",
            vietnamese_content="Nội dung kiểm thử tự động.",
            annotations=[{
                "code": "LI4",
                "name": "Hợp Cốc",
                "side": "RIGHT",
                "review_status": "USER_ANNOTATED_UNVERIFIED",
                "global_position": [0.1, 0.2, 0.3]
            }],
            waypoints=[[0.1, 0.2, 0.3], [0.15, 0.25, 0.35], [0.2, 0.3, 0.4], [0.25, 0.35, 0.45]]
        )
        assert "ENGINEERING_RESEARCH_ONLY" in md
        assert "NOT_ESTABLISHED" in md
        assert "USER_ANNOTATED_UNVERIFIED" in md
        assert "Hợp Cốc" in md
        assert "4 điểm" in md

    def test_pure_python_arm_kinematics_roundtrip(self):
        solver = ArmKinematicsSolver(upper_arm_length=0.30, forearm_length=0.26)
        # Test 3 test cases: 30 deg, 60 deg, 90 deg elbow flexion
        for test_elbow in [30.0, 60.0, 90.0]:
            test_shoulder = 25.0
            (elbow_pt, wrist_pt) = solver.forward_kinematics_2d(test_shoulder, test_elbow)
            res = solver.inverse_kinematics_2d(wrist_pt)
            assert res is not None
            rec_shoulder, rec_elbow = res
            assert abs(rec_shoulder - test_shoulder) < 1e-3, f"Shoulder mismatch: {rec_shoulder} vs {test_shoulder}"
            assert abs(rec_elbow - test_elbow) < 1e-3, f"Elbow mismatch: {rec_elbow} vs {test_elbow}"

    def test_exported_evidence_artifacts_exist(self):
        evidence_dir = REPO_ROOT / "1docs" / "audits" / "P21" / "evidence"
        screenshots_dir = REPO_ROOT / "1docs" / "audits" / "P21" / "screenshots"

        assert (evidence_dir / "p21_studio_export_manifest.json").exists()
        assert (evidence_dir / "p21_studio_export_annotations.json").exists()
        assert (evidence_dir / "p21_studio_export_meridian_curves.json").exists()
        assert (evidence_dir / "p21_studio_export_note.md").exists()
        assert (evidence_dir / "p21_studio_export.blend").exists()

        assert (screenshots_dir / "01_blender_36_anatomical_studio_poc.png").exists()
        assert (screenshots_dir / "02_blender_arm_rig_flexed_pose.png").exists()
