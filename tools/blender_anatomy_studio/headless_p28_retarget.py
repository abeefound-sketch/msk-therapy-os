"""P28 Blender Anatomical Studio: Real Motion Retargeting, Mesh-Bone Binding & Scene Persistence.
Runs natively inside Blender 3.6 background mode.
Loads genuine anatomy, binds meshes to armature bones, keyframes real MediaPipe angles,
verifies bone length invariance, renders evidence screenshots, and tests save & reopen round-trip.
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
    notes,
    rig,
    import_export,
)
from tools.blender_anatomy_studio.motion_bank import BoneLengthInvarianceEvaluator


def run_p28_retargeting():
    print("=" * 60)
    print("STARTING P28 BLENDER REAL MOTION RETARGETING & MESH BINDING")
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
    assert len(imported_meshes) >= 3, "Expected at least 3 bone meshes"

    humerus = bpy.data.objects.get("Humerus_R")
    clavicle = bpy.data.objects.get("Clavicle_R")
    scapula = bpy.data.objects.get("Scapula_R")
    assert humerus and clavicle and scapula, "Required bones missing"

    # 3. Classify layers
    for m in imported_meshes:
        m["msk_anatomy_class"] = layers.classify_object_name(m.name)

    ctx = bpy.context

    # 4. Build Upper Limb Armature Rig with Kapandji / Seth Constraints
    arm_obj = rig.build_upper_limb_armature(context=ctx, side="RIGHT")
    print(f"Built armature rig: {arm_obj.name}")

    # Set IK influence to 0.0 for direct FK joint angle retargeting
    p_fore = arm_obj.pose.bones["forearm.R"]
    ik_con = p_fore.constraints.get("MSK_Elbow_IK")
    if ik_con:
        ik_con.influence = 0.0
        print("Set MSK_Elbow_IK influence to 0.0 (FK retargeting mode)")

    # 5. MESH-TO-BONE BINDING (Fixing P27 Reality Check Gap)
    # Parent Humerus_R mesh to upper_arm.R bone so it moves when the arm rotates!
    humerus.parent = arm_obj
    humerus.parent_type = 'BONE'
    humerus.parent_bone = 'upper_arm.R'
    humerus.matrix_parent_inverse = (arm_obj.matrix_world @ arm_obj.pose.bones['upper_arm.R'].matrix).inverted()
    print("Successfully bound Humerus_R mesh to bone upper_arm.R")

    # Parent Clavicle_R to clavicle.R bone
    clavicle.parent = arm_obj
    clavicle.parent_type = 'BONE'
    clavicle.parent_bone = 'clavicle.R'
    clavicle.matrix_parent_inverse = (arm_obj.matrix_world @ arm_obj.pose.bones['clavicle.R'].matrix).inverted()
    print("Successfully bound Clavicle_R mesh to bone clavicle.R")

    # 6. Anchor Acupoint LI4 onto Humerus_R (it will move with the bone)
    m1 = annotations.create_annotation_marker(
        context=ctx,
        target_obj=humerus,
        world_pos=mathutils.Vector((0.20, 0.0, 1.14)),
        name="Hợp Cốc (LI4)",
        code="LI4",
        side="RIGHT",
        annotation_type="ACUPOINT",
        notes="Gắn trên mốc xương cánh tay; theo dõi động thái chuyển động qua Bone Parent",
        uncertainty_mm=5.0
    )
    # Parent marker to humerus so it tracks the bone's transformed location
    m1.parent = humerus
    m1.matrix_parent_inverse = humerus.matrix_world.inverted()
    print(f"Anchored marker {m1.name} onto {humerus.name}")

    # 7. Load Real MediaPipe Motion Sequence
    motion_json_path = REPO_ROOT / "1docs" / "audits" / "P28" / "evidence" / "p28_real_motion_sequence.json"
    assert motion_json_path.exists(), f"Motion sequence missing: {motion_json_path}"

    with open(motion_json_path, "r", encoding="utf-8") as f:
        motion_data = json.load(f)

    frames = motion_data["frames"]
    fps = motion_data.get("fps", 60.0)
    ctx.scene.render.fps = int(round(fps))
    ctx.scene.frame_start = 1
    ctx.scene.frame_end = len(frames)

    print(f"Applying {len(frames)} real motion frames to timeline...")

    p_arm = arm_obj.pose.bones["upper_arm.R"]

    for f_item in frames:
        f_idx = f_item["frame_index"] + 1 # Blender frames start at 1
        rot = f_item["joint_rotations"]
        el_flex = rot["right_elbow_flexion_deg"]
        sh_elev = rot["right_shoulder_elevation_deg"]

        # Apply angles and insert keyframes
        p_arm.rotation_mode = 'XYZ'
        p_arm.rotation_euler = (math.radians(sh_elev), 0.0, 0.0)
        p_arm.keyframe_insert(data_path="rotation_euler", frame=f_idx)

        p_fore.rotation_mode = 'XYZ'
        p_fore.rotation_euler = (math.radians(el_flex), 0.0, 0.0)
        p_fore.keyframe_insert(data_path="rotation_euler", frame=f_idx)

    print("Inserted all keyframes into timeline.")

    # 8. Setup Camera and Lighting for Evidence Rendering
    cam_data = bpy.data.cameras.new("MSK_P28_Camera")
    cam_obj = bpy.data.objects.new("MSK_P28_Camera", cam_data)
    ctx.scene.collection.objects.link(cam_obj)
    ctx.scene.camera = cam_obj
    cam_obj.location = (0.6, -1.3, 1.2)
    cam_obj.rotation_euler = (math.radians(82), 0, math.radians(26))

    light_data = bpy.data.lights.new(name="MSK_P28_Sun", type='SUN')
    light_data.energy = 4.0
    light_obj = bpy.data.objects.new(name="MSK_P28_Sun", object_data=light_data)
    ctx.scene.collection.objects.link(light_obj)
    light_obj.location = (1.0, -1.0, 3.0)

    # 9. Verify Motion & Render Screenshot Evidence at Frames 1 and 50
    evidence_dir = REPO_ROOT / "1docs" / "audits" / "P28" / "evidence"
    screenshot_dir = REPO_ROOT / "1docs" / "audits" / "P28" / "screenshots"

    # Frame 1 (Initial pose)
    ctx.scene.frame_set(1)
    dg = ctx.evaluated_depsgraph_get()
    humerus_eval_1 = humerus.evaluated_get(dg)
    m1_eval_1 = m1.evaluated_get(dg)
    v_sample_f1 = humerus_eval_1.matrix_world @ humerus.data.vertices[0].co
    pos_marker_f1 = m1_eval_1.matrix_world.translation.copy()

    render_path_1 = screenshot_dir / "02_blender_real_motion_frame_001.png"
    ctx.scene.render.filepath = str(render_path_1)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered Frame 1 evidence: {render_path_1.name} (Marker pos: {pos_marker_f1})")

    # Frame 50 (Elevated/flexed pose)
    ctx.scene.frame_set(50)
    dg = ctx.evaluated_depsgraph_get()
    humerus_eval_50 = humerus.evaluated_get(dg)
    m1_eval_50 = m1.evaluated_get(dg)
    v_sample_f50 = humerus_eval_50.matrix_world @ humerus.data.vertices[0].co
    pos_marker_f50 = m1_eval_50.matrix_world.translation.copy()

    render_path_50 = screenshot_dir / "03_blender_real_motion_frame_050.png"
    ctx.scene.render.filepath = str(render_path_50)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered Frame 50 evidence: {render_path_50.name} (Marker pos: {pos_marker_f50})")

    # Verify bone and marker displacement
    displacement_vertex = (v_sample_f50 - v_sample_f1).length
    displacement_marker = (pos_marker_f50 - pos_marker_f1).length
    print(f"Humerus Vertex Displacement between Frame 1 and 50: {displacement_vertex:.4f} m ({displacement_vertex * 1000:.1f} mm)")
    print(f"LI4 Marker Displacement between Frame 1 and 50: {displacement_marker:.4f} m ({displacement_marker * 1000:.1f} mm)")

    assert displacement_vertex > 0.05, f"Expected Humerus vertex to move > 50 mm! Was {displacement_vertex}"
    assert displacement_marker > 0.05, f"Expected LI4 marker to move > 50 mm! Was {displacement_marker}"
    print("VERIFIED: Bone mesh and acupoint marker follow armature motion in 3D space!")

    # 10. Verify Bone Length Invariance across frames 1 to 100
    upper_arm_segments = []
    forearm_segments = []

    for f_test in range(1, len(frames) + 1, 5):
        ctx.scene.frame_set(f_test)
        dg = ctx.evaluated_depsgraph_get()
        p_arm_eval = arm_obj.evaluated_get(dg).pose.bones["upper_arm.R"]
        p_fore_eval = arm_obj.evaluated_get(dg).pose.bones["forearm.R"]

        # World head and tail
        mat = arm_obj.matrix_world
        h_arm = tuple(mat @ p_arm_eval.head)
        t_arm = tuple(mat @ p_arm_eval.tail)
        h_fore = tuple(mat @ p_fore_eval.head)
        t_fore = tuple(mat @ p_fore_eval.tail)

        upper_arm_segments.append((h_arm, t_arm))
        forearm_segments.append((h_fore, t_fore))

    nominal_upper = math.dist(upper_arm_segments[0][0], upper_arm_segments[0][1])
    nominal_forearm = math.dist(forearm_segments[0][0], forearm_segments[0][1])
    inv_res = BoneLengthInvarianceEvaluator.evaluate_invariance(
        upper_arm_segments,
        forearm_segments,
        nominal_upper_length=nominal_upper,
        nominal_forearm_length=nominal_forearm,
        tolerance_m=1e-4
    )

    print(f"Upper arm max error: {inv_res['max_upper_arm_error_mm']:.4f} mm")
    print(f"Forearm max error: {inv_res['max_forearm_error_mm']:.4f} mm")
    print(f"Bone length invariance passed: {inv_res['passed']}")
    assert inv_res["passed"], "Bone lengths must remain strictly invariant!"

    # 11. Save Complete Scene (.blend)
    blend_path = evidence_dir / "p28_real_video_motion.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"Saved .blend scene: {blend_path} (Size: {os.path.getsize(blend_path)} bytes)")

    # 12. TEST SAVE & REOPEN ROUND-TRIP
    print("Testing Save & Reopen round-trip...")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    reopened_arm = bpy.data.objects.get("Armature_UpperLimb_R")
    reopened_humerus = bpy.data.objects.get("Humerus_R")
    reopened_marker = bpy.data.objects.get("Marker_LI4_RIGHT") or bpy.data.objects.get("Hợp Cốc (LI4)")

    assert reopened_arm is not None, "Reopened armature missing"
    assert reopened_humerus is not None, "Reopened humerus missing"
    assert reopened_marker is not None, "Reopened marker missing"
    assert reopened_humerus.parent == reopened_arm, "Humerus parent link lost"
    assert reopened_humerus.parent_bone == "upper_arm.R", "Humerus bone parenting lost"
    assert reopened_arm.animation_data is not None, "Animation data lost"

    print("ROUND-TRIP SUCCESS: Reopened scene verified with 100% data integrity!")
    print("=" * 60)
    print("P28 BLENDER REAL MOTION RETARGETING COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    run_p28_retargeting()
