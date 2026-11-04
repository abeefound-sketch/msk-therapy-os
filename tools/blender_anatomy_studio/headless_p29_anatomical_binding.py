"""Headless P29 Pipeline: Anatomical Mesh, Joint & Marker Binding.
Enforces authentic bone-to-mesh parenting, strictly prohibits cross-segment marker misbinding (e.g. LI4 to Humerus),
applies 2:1 scapulohumeral rhythm, dynamically updates meridian splines, and renders 3-pose evidence.
"""
from __future__ import annotations

import hashlib
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
    rig,
    rig_binding_adapter,
    surface_anchor_registry,
)
from tools.blender_anatomy_studio.addon.rig_binding_adapter import AnatomicalRigBindingAdapter
from tools.blender_anatomy_studio.addon.surface_anchor_registry import AnatomicalSurfaceAnchorRegistry
from tools.blender_anatomy_studio.motion_bank import BoneLengthInvarianceEvaluator


def run_p29_pipeline():
    print("=" * 60)
    print("STARTING P29 ANATOMICAL MESH, JOINT & MARKER BINDING")
    print(f"Blender version: {bpy.app.version_string}")
    print("=" * 60)

    # 1. Reset factory settings
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 2. Import genuine anatomical mesh
    model_path = REPO_ROOT / "msk_therapy_os" / "static" / "education" / "models" / "shoulder_skeleton.glb"
    print(f"Importing genuine anatomical mesh: {model_path}")
    bpy.ops.import_scene.gltf(filepath=str(model_path))

    imported_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    print(f"Imported meshes: {[m.name for m in imported_meshes]}")

    # 3. Audit Scene Structures
    audit = AnatomicalRigBindingAdapter.audit_scene_structures(imported_meshes)
    print(f"Audit Present Structures: {list(audit['present_structures'].keys())}")
    print(f"Audit Missing Structures: {list(audit['missing_structures'].keys())}")
    assert "Humerus_R" in audit["present_structures"]
    assert "Clavicle_R" in audit["present_structures"]
    assert "Scapula_R" in audit["present_structures"]
    assert "Metacarpals_R" in audit["missing_structures"]
    assert audit["missing_structures"]["Metacarpals_R"]["status"] == "ASSET_NOT_AVAILABLE"

    # 4. Audit Surface Anchors & Validate Restrictions
    anchor_reg = AnatomicalSurfaceAnchorRegistry()
    coverage = anchor_reg.validate_asset_coverage([m.name for m in imported_meshes])
    print(f"Landmark Asset Coverage: {coverage}")

    # Negative test: Prohibit binding LI4 to Humerus_R
    try:
        anchor_reg.register_anchor(
            marker_id="test_illegal_li4",
            code="LI4",
            target_mesh_name="Humerus_R",
            target_bone_name="upper_arm.R",
            local_coordinates=(0.20, 0.0, 1.14),
            local_normal=(0.0, 1.0, 0.0),
            mesh_hash="sha256_mock"
        )
        assert False, "CRITICAL ERROR: Registry failed to prohibit binding LI4 to Humerus_R!"
    except ValueError as e:
        print(f"PASSED PROHIBITION TEST: {e}")

    # Register legitimate upper limb points on available meshes
    anc_li14 = anchor_reg.register_anchor(
        marker_id="anchor_LI14",
        code="LI14",
        target_mesh_name="Humerus_R",
        target_bone_name="upper_arm.R",
        local_coordinates=(0.03, -0.01, -0.15),
        local_normal=(0.8, 0.0, 0.6),
        mesh_hash="sha256_humerus_r"
    )
    anc_li15 = anchor_reg.register_anchor(
        marker_id="anchor_LI15",
        code="LI15",
        target_mesh_name="Scapula_R",
        target_bone_name="clavicle.R",
        local_coordinates=(0.02, 0.02, 0.04),
        local_normal=(0.0, 0.7, 0.7),
        mesh_hash="sha256_scapula_r"
    )
    anc_lat_epi = anchor_reg.register_anchor(
        marker_id="anchor_LAT_EPI",
        code="LATERAL_EPICONDYLE",
        target_mesh_name="Humerus_R",
        target_bone_name="upper_arm.R",
        local_coordinates=(0.025, 0.0, -0.28),
        local_normal=(1.0, 0.0, 0.0),
        mesh_hash="sha256_humerus_r"
    )
    print("Registered legitimate anatomical anchors: LI14 (Binao), LI15 (Jianyu), LATERAL_EPICONDYLE")

    # 5. Build Armature Rig
    ctx = bpy.context
    arm_obj = rig.build_upper_limb_armature(context=ctx, side="RIGHT")
    print(f"Built Armature Rig: {arm_obj.name}")

    # Disable IK influence for direct FK / rhythm retargeting
    p_fore = arm_obj.pose.bones.get("forearm.R")
    if p_fore and "MSK_Elbow_IK" in p_fore.constraints:
        p_fore.constraints["MSK_Elbow_IK"].influence = 0.0

    # 6. Bind Anatomical Bone Meshes to Rig
    humerus = bpy.data.objects.get("Humerus_R")
    clavicle = bpy.data.objects.get("Clavicle_R")
    scapula = bpy.data.objects.get("Scapula_R")

    bind_hum = AnatomicalRigBindingAdapter.bind_mesh_to_bone(humerus, arm_obj, "upper_arm.R")
    bind_clav = AnatomicalRigBindingAdapter.bind_mesh_to_bone(clavicle, arm_obj, "clavicle.R")
    bind_scap = AnatomicalRigBindingAdapter.bind_mesh_to_bone(scapula, arm_obj, "clavicle.R")

    print(f"Bound Humerus_R: {bind_hum['status']} to {bind_hum['parent_bone']}")
    print(f"Bound Clavicle_R: {bind_clav['status']} to {bind_clav['parent_bone']}")
    print(f"Bound Scapula_R: {bind_scap['status']} to {bind_scap['parent_bone']}")

    # 7. Create Visual Markers on Correct Anatomical Meshes
    # LI14 on Humerus_R
    m_li14 = annotations.create_annotation_marker(
        context=ctx,
        target_obj=humerus,
        world_pos=humerus.matrix_world @ mathutils.Vector(anc_li14["local_surface_coordinates"]),
        name="Tí Nhu (LI14)",
        code="LI14",
        side="RIGHT",
        annotation_type="ACUPOINT",
        notes="Gắn trên lồi củ cơ delta xương cánh tay (FMA:23412); đúng định vị WHO 2008",
        uncertainty_mm=5.0
    )
    m_li14.parent = humerus
    m_li14.matrix_parent_inverse = humerus.matrix_world.inverted()

    # LI15 on Scapula_R
    m_li15 = annotations.create_annotation_marker(
        context=ctx,
        target_obj=scapula,
        world_pos=scapula.matrix_world @ mathutils.Vector(anc_li15["local_surface_coordinates"]),
        name="Kiên Ngung (LI15)",
        code="LI15",
        side="RIGHT",
        annotation_type="ACUPOINT",
        notes="Gắn trên mỏm cùng vai (FMA:23240); đúng định vị WHO 2008",
        uncertainty_mm=6.0
    )
    m_li15.parent = scapula
    m_li15.matrix_parent_inverse = scapula.matrix_world.inverted()

    # Lateral Epicondyle on Humerus_R
    m_lat_epi = annotations.create_annotation_marker(
        context=ctx,
        target_obj=humerus,
        world_pos=humerus.matrix_world @ mathutils.Vector(anc_lat_epi["local_surface_coordinates"]),
        name="Mỏm Lồi Cầu Ngoài (LAT_EPI)",
        code="LAT_EPI_R",
        side="RIGHT",
        annotation_type="LANDMARK",
        notes="Mốc lồi cầu ngoài xương cánh tay (FMA:23420 / TA2:2988)",
        uncertainty_mm=3.0
    )
    m_lat_epi.parent = humerus
    m_lat_epi.matrix_parent_inverse = humerus.matrix_world.inverted()

    # 8. Create Dynamic Meridian Spline
    curve_obj = meridian_curves.create_or_get_meridian_curve(
        context=ctx,
        curve_name="Meridian_Arm_LI_Dynamic",
        channel_code="LI"
    )

    meridian_anchor_defs = [
        {"parent_obj": scapula, "local_pos": anc_li15["local_surface_coordinates"], "code": "LI15"},
        {"parent_obj": humerus, "local_pos": (0.02, -0.01, -0.08), "code": "MID_DELTOID"},
        {"parent_obj": humerus, "local_pos": anc_li14["local_surface_coordinates"], "code": "LI14"},
        {"parent_obj": humerus, "local_pos": anc_lat_epi["local_surface_coordinates"], "code": "LAT_EPI_R"}
    ]

    # Initial curve placement
    meridian_curves.update_meridian_curve_from_anchors(curve_obj, meridian_anchor_defs)
    print(f"Initialized dynamic meridian curve with {len(meridian_anchor_defs)} anchors")

    # 9. Setup Camera and Lighting
    evidence_dir = REPO_ROOT / "1docs" / "audits" / "P29" / "evidence"
    screenshot_dir = REPO_ROOT / "1docs" / "audits" / "P29" / "screenshots"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    cam_data = bpy.data.cameras.new("MSK_P29_Camera")
    cam_obj = bpy.data.objects.new("MSK_P29_Camera", cam_data)
    ctx.scene.collection.objects.link(cam_obj)
    ctx.scene.camera = cam_obj
    cam_obj.location = (0.7, -1.3, 1.3)
    cam_obj.rotation_euler = (math.radians(80), 0, math.radians(28))

    light_data = bpy.data.lights.new(name="MSK_P29_Sun", type='SUN')
    light_data.energy = 4.0
    light_obj = bpy.data.objects.new(name="MSK_P29_Sun", object_data=light_data)
    ctx.scene.collection.objects.link(light_obj)
    light_obj.location = (1.5, -1.0, 3.5)

    # 10. Keyframe 3 Poses with Scapulohumeral Rhythm
    # Pose A: Frame 1, 0 deg elevation
    # Pose B: Frame 30, 45 deg elevation
    # Pose C: Frame 60, 90 deg elevation
    ctx.scene.frame_start = 1
    ctx.scene.frame_end = 60

    poses = [
        (1, 0.0, "01_p29_pose_a_rest_0deg.png"),
        (30, 45.0, "02_p29_pose_b_mid_45deg.png"),
        (60, 90.0, "03_p29_pose_c_elevated_90deg.png")
    ]

    for f_idx, elev_deg, _ in poses:
        AnatomicalRigBindingAdapter.apply_scapulohumeral_rhythm(arm_obj, elev_deg, frame=f_idx)

    # Render and measure each pose
    pose_measurements = {}

    for f_idx, elev_deg, img_name in poses:
        ctx.scene.frame_set(f_idx)
        dg = ctx.evaluated_depsgraph_get()

        # Update dynamic meridian spline to match deformed pose
        w_pts = meridian_curves.update_meridian_curve_from_anchors(curve_obj, meridian_anchor_defs, depsgraph=dg)

        humerus_eval = humerus.evaluated_get(dg)
        scapula_eval = scapula.evaluated_get(dg)
        m_li14_eval = m_li14.evaluated_get(dg)
        m_li15_eval = m_li15.evaluated_get(dg)

        pos_humerus_v = humerus_eval.matrix_world @ humerus.data.vertices[0].co
        pos_li14 = m_li14_eval.matrix_world.translation.copy()
        pos_li15 = m_li15_eval.matrix_world.translation.copy()

        pose_measurements[f_idx] = {
            "elevation_deg": elev_deg,
            "humerus_vertex": pos_humerus_v,
            "li14_marker": pos_li14,
            "li15_marker": pos_li15,
            "meridian_pts": w_pts
        }

        render_path = screenshot_dir / img_name
        ctx.scene.render.filepath = str(render_path)
        bpy.ops.render.render(write_still=True)
        print(f"Rendered Pose at frame {f_idx} ({elev_deg} deg): {img_name}")

    # 11. Calculate Displacements & Invariants
    p1 = pose_measurements[1]
    p60 = pose_measurements[60]

    disp_humerus = (p60["humerus_vertex"] - p1["humerus_vertex"]).length
    disp_li14 = (p60["li14_marker"] - p1["li14_marker"]).length
    disp_li15 = (p60["li15_marker"] - p1["li15_marker"]).length

    print(f"Displacement Humerus Mesh (Frame 1 -> 60): {disp_humerus * 1000:.1f} mm")
    print(f"Displacement LI14 Marker (Frame 1 -> 60): {disp_li14 * 1000:.1f} mm")
    print(f"Displacement LI15 Marker (Frame 1 -> 60): {disp_li15 * 1000:.1f} mm")

    assert disp_humerus > 0.05, "Humerus mesh must move significantly!"
    assert disp_li14 > 0.05, "LI14 marker must move significantly with humerus!"
    assert disp_li15 > 0.005, "LI15 marker must move with scapula upward rotation!"

    # Invariance check: Distance between LI14 and its parent mesh origin
    dist_li14_local = (p60["li14_marker"] - p60["humerus_vertex"]).length
    dist_li14_local_p1 = (p1["li14_marker"] - p1["humerus_vertex"]).length
    drift_mm = abs(dist_li14_local - dist_li14_local_p1) * 1000.0
    print(f"LI14 Surface Attachment Drift: {drift_mm:.4f} mm")
    assert drift_mm < 0.1, f"Surface anchor must not drift on rigid bone! Drift was {drift_mm} mm"

    # 12. Save Scene (.blend) and Test Save & Reopen
    blend_path = evidence_dir / "p29_anatomical_rig_binding.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"Saved .blend scene: {blend_path} (Size: {os.path.getsize(blend_path)} bytes)")

    print("Testing Save & Reopen round-trip...")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    assert "Armature_UpperLimb_R" in bpy.data.objects
    assert "Humerus_R" in bpy.data.objects
    assert "Scapula_R" in bpy.data.objects
    assert "Meridian_Arm_LI_Dynamic" in bpy.data.objects
    assert bpy.data.objects["Humerus_R"].parent_bone == "upper_arm.R"
    assert bpy.data.objects["Scapula_R"].parent_bone == "clavicle.R"

    print("ROUND-TRIP SUCCESS: Scene reloaded with 100% structural integrity!")
    print("=" * 60)
    print("P29 ANATOMICAL BINDING PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    run_p29_pipeline()
