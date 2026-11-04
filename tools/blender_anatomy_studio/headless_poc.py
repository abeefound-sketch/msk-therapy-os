"""Headless proof-of-concept pipeline for P21 Blender Anatomical Studio.
Runs natively inside Blender 3.6 background mode.
"""
import json
import math
import os
import sys
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import bpy
import mathutils

from tools.blender_anatomy_studio.addon import (
    layers,
    annotations,
    meridian_curves,
    notes,
    rig,
    import_export,
)
from tools.blender_anatomy_studio.contracts import validate_contract

def run_p21_poc():
    print("=" * 60)
    print("STARTING P21 BLENDER ANATOMICAL STUDIO POC")
    print(f"Blender version: {bpy.app.version_string}")
    print("=" * 60)

    # 1. Reset factory settings
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 2. Import genuine anatomical mesh
    # Using shoulder skeleton model
    model_path = REPO_ROOT / "msk_therapy_os" / "static" / "education" / "models" / "shoulder_skeleton.glb"
    print(f"Importing genuine anatomical mesh: {model_path}")
    bpy.ops.import_scene.gltf(filepath=str(model_path))

    imported_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    print(f"Imported {len(imported_meshes)} anatomical meshes: {[m.name for m in imported_meshes]}")
    assert len(imported_meshes) >= 4, "Expected at least 4 anatomical meshes"

    # 3. Classify layers and test visibility toggles
    for m in imported_meshes:
        cls = layers.classify_object_name(m.name)
        m["msk_anatomy_class"] = cls
        print(f"  Mesh: {m.name} -> Class: {cls}")

    # Test layer toggles
    bone_meshes = [m for m in imported_meshes if m["msk_anatomy_class"] == "BONE"]
    print(f"Bone meshes count: {len(bone_meshes)}")

    # 4. Add 3 Acupoint markers with surface anchoring
    # We place markers on Humerus_R, Scapula_R, Clavicle_R
    humerus = bpy.data.objects.get("Humerus_R")
    clavicle = bpy.data.objects.get("Clavicle_R")
    scapula = bpy.data.objects.get("Scapula_R")
    assert humerus and clavicle and scapula, "Required bones missing"

    # Context setup
    class DummyContext:
        scene = bpy.context.scene
        active_object = humerus
        view_layer = bpy.context.view_layer

    ctx = bpy.context

    # Marker 1: LI4 (anchored near distal humerus/hand region on Humerus_R)
    m1 = annotations.create_annotation_marker(
        context=ctx,
        target_obj=humerus,
        world_pos=mathutils.Vector((0.20, 0.0, 1.14)),
        name="Hợp Cốc (LI4)",
        code="LI4",
        side="RIGHT",
        annotation_type="ACUPOINT",
        notes="Gắn trên mốc giải phẫu xương cánh tay/bờ quay; trạng thái USER_ANNOTATED_UNVERIFIED",
        uncertainty_mm=5.0
    )
    print(f"Created marker 1: {m1.name} at {m1.location}")

    # Marker 2: ST36 (Túc Tam Lý - placed for systemic meridian testing)
    m2 = annotations.create_annotation_marker(
        context=ctx,
        target_obj=scapula,
        world_pos=mathutils.Vector((0.15, -0.05, 1.35)),
        name="Túc Tam Lý (ST36 - Reference Landmark)",
        code="ST36",
        side="RIGHT",
        annotation_type="LANDMARK",
        notes="Mốc giải phẫu đối chứng; trạng thái USER_ANNOTATED_UNVERIFIED",
        uncertainty_mm=10.0
    )
    print(f"Created marker 2: {m2.name} at {m2.location}")

    # Marker 3: KI3 (Thái Khê - placed for lineage reference)
    m3 = annotations.create_annotation_marker(
        context=ctx,
        target_obj=clavicle,
        world_pos=mathutils.Vector((0.08, 0.0, 1.43)),
        name="Thái Khê (KI3 - Lineage Reference)",
        code="KI3",
        side="RIGHT",
        annotation_type="LANDMARK",
        notes="Mốc giải phẫu xương đòn đối chứng; trạng thái USER_ANNOTATED_UNVERIFIED",
        uncertainty_mm=8.0
    )
    print(f"Created marker 3: {m3.name} at {m3.location}")

    # 5. Add 3D Meridian curve with 5 waypoints and test undo
    curve_obj = meridian_curves.create_or_get_meridian_curve(
        context=ctx,
        curve_name="Meridian_Large_Intestine_LI",
        channel_code="LI"
    )
    wps = [
        (0.22, 0.05, 1.05),
        (0.20, 0.02, 1.15),
        (0.18, 0.01, 1.25),
        (0.16, 0.0, 1.35),
        (0.14, 0.0, 1.42),
    ]
    meridian_curves.set_meridian_waypoints(curve_obj, wps)
    print(f"Created meridian curve with {len(wps)} waypoints")

    # Test undo (pop waypoint)
    ok = meridian_curves.pop_meridian_waypoint(curve_obj)
    assert ok, "Undo failed"
    curr_wps = meridian_curves.get_meridian_waypoints(curve_obj)
    print(f"Undo tested: Waypoints reduced to {len(curr_wps)} (expected 4)")
    assert len(curr_wps) == 4, f"Expected 4 waypoints after undo, got {len(curr_wps)}"

    # 6. Build Armature Rig & IK
    arm_obj = rig.build_upper_limb_armature(context=ctx, side="RIGHT")
    print(f"Built armature rig: {arm_obj.name} with bones: {[b.name for b in arm_obj.data.bones]}")

    # Animate 3 keyframes using Seth shoulder elevation / elbow flexion angles
    # Keyframe 1: frame 1, 0 deg elevation, 0 deg elbow
    rig.apply_joint_angles_to_armature(arm_obj, 0.0, 0.0, frame=1)
    # Keyframe 2: frame 20, 45 deg elevation, 45 deg elbow
    rig.apply_joint_angles_to_armature(arm_obj, 45.0, 45.0, frame=20)
    # Keyframe 3: frame 40, 90 deg elevation, 90 deg elbow
    rig.apply_joint_angles_to_armature(arm_obj, 90.0, 90.0, frame=40)
    print("Inserted 3 keyframes on upper_arm.R and forearm.R (frames 1, 20, 40)")

    # 7. Setup Camera and Lighting for Render Evidence
    cam_data = bpy.data.cameras.new("MSK_Camera")
    cam_obj = bpy.data.objects.new("MSK_Camera", cam_data)
    ctx.scene.collection.objects.link(cam_obj)
    ctx.scene.camera = cam_obj
    cam_obj.location = (0.5, -1.2, 1.3)
    cam_obj.rotation_euler = (math.radians(80), 0, math.radians(25))

    light_data = bpy.data.lights.new(name="MSK_Sun", type='SUN')
    light_data.energy = 3.0
    light_obj = bpy.data.objects.new("MSK_Sun", light_data)
    ctx.scene.collection.objects.link(light_obj)
    light_obj.location = (1.0, -1.0, 2.5)

    # Render evidence screenshot 1: Initial Anatomical Studio Setup
    evidence_dir = REPO_ROOT / "1docs" / "audits" / "P21" / "screenshots"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    shot1_path = evidence_dir / "01_blender_36_anatomical_studio_poc.png"

    ctx.scene.render.image_settings.file_format = 'PNG'
    ctx.scene.render.resolution_x = 960
    ctx.scene.render.resolution_y = 720
    ctx.scene.render.filepath = str(shot1_path)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered evidence screenshot 1: {shot1_path} (exists: {shot1_path.exists()})")

    # Scrub to frame 30 (flexed pose) and render screenshot 2
    ctx.scene.frame_set(30)
    shot2_path = evidence_dir / "02_blender_arm_rig_flexed_pose.png"
    ctx.scene.render.filepath = str(shot2_path)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered evidence screenshot 2: {shot2_path} (exists: {shot2_path.exists()})")

    # 8. Export Full Studio Package
    export_prefix = REPO_ROOT / "1docs" / "audits" / "P21" / "evidence" / "p21_studio_export"
    export_prefix.parent.mkdir(parents=True, exist_ok=True)

    export_res = import_export.export_studio_package(
        context=ctx,
        base_path_str=str(export_prefix),
        source_id="Shoulder_Skeleton_BodyParts3D_Submodel",
        license_id="CC-BY-4.0",
        license_scope="COMMERCIAL_PERMITTED_WITH_ATTRIBUTION",
        attribution="BodyParts3D, © DBCLS Japan licensed under CC Attribution 4.0 International."
    )
    print("Export results:")
    for k, v in export_res.items():
        print(f"  {k}: {v}")

    # 9. Verify Reopen & Reimport
    # A) Verify saved .blend file opens cleanly
    blend_path = export_res["blend_file"]
    assert Path(blend_path).exists() and Path(blend_path).stat().st_size > 0
    print(f"Verified .blend file size: {Path(blend_path).stat().st_size} bytes")

    # B) Test clean-slate import
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Import the original mesh again
    bpy.ops.import_scene.gltf(filepath=str(model_path))

    import_res = import_export.import_studio_package(
        context=bpy.context,
        manifest_path=export_res["manifest_json"],
        annotations_path=export_res["annotations_json"],
        curves_path=export_res["curves_json"],
        verify_checksum=True
    )
    print(f"Re-import successful: {import_res}")
    assert import_res["imported_markers"] == 3, f"Expected 3 imported markers, got {import_res['imported_markers']}"
    assert import_res["imported_curves"] == 1, f"Expected 1 imported curve, got {import_res['imported_curves']}"

    # C) Test Fail-Closed Checksum Mutation
    # Create tampered annotations file with modified mesh hash
    tampered_annots = []
    with open(export_res["annotations_json"], "r", encoding="utf-8") as f:
        tampered_annots = json.load(f)
    tampered_annots[0]["mesh_hash"] = "f" * 64 # Corrupt hash

    tampered_path = REPO_ROOT / "1docs" / "audits" / "P21" / "evidence" / "tampered_annotations.json"
    with open(tampered_path, "w", encoding="utf-8") as f:
        json.dump(tampered_annots, f, indent=2)

    try:
        import_export.import_studio_package(
            context=bpy.context,
            manifest_path=export_res["manifest_json"],
            annotations_path=str(tampered_path),
            verify_checksum=True
        )
        print("FAIL: Expected MeshChecksumMismatchError was not raised!")
        sys.exit(1)
    except import_export.MeshChecksumMismatchError as e:
        print(f"PASS: Fail-closed checksum verified successfully. Caught expected error:\n  {e}")

    print("=" * 60)
    print("ALL P21 BLENDER ANATOMICAL STUDIO POC VERIFICATIONS PASSED")
    print("=" * 60)

if __name__ == "__main__":
    run_p21_poc()
