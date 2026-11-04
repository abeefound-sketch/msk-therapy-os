"""
MSK-Therapy-OS V1.3: Universal Anatomical Binding System - Full Body Generator
==============================================================================
Builds a unified 3D humanoid character using a SINGLE canonical humanoid skeleton (53 bones)
with:
1. Full-body MakeHuman skinned mesh with 7 GPU Morph Targets.
2. Upper limb authentic BodyParts3D bones (Humerus, Radius, Ulna, Metacarpal II, Clavicle).
3. Upper limb authentic BodyParts3D muscles (Biceps 2 heads, Triceps 3 heads, Brachialis) with Dual-Bone Skinning.
4. Lower limb authentic BodyParts3D bones (Femur, Tibia, Fibula, Patella).
5. Lower limb authentic BodyParts3D muscles (Rectus femoris, Vastus lateralis, Vastus medialis, Vastus intermedius) with Dual-Bone Skinning.
6. Synchronized Range of Motion animation tracks (simultaneous arm & leg motion).
7. Outputs .blend and .glb (GLTF 2.0).
"""

from __future__ import annotations

import gzip
import json
import math
from pathlib import Path
import bpy
import mathutils

REPO_ROOT = Path(r"D:\5Projects\msk-therapy-os")
ASSETS_DIR = REPO_ROOT / "research" / "character_pipeline" / "makehuman_assets"
BP3D_DIR = REPO_ROOT / "tools" / "blender_anatomy_studio" / "assets" / "bp3d"

BASE_OBJ = ASSETS_DIR / "base.obj"
RIG_JSON = ASSETS_DIR / "rig.game_engine.json"
WEIGHTS_JSON = ASSETS_DIR / "weights.game_engine.json"

OUT_BLEND = REPO_ROOT / "research" / "character_pipeline" / "rigged_human_anatomy_v13.blend"
OUT_GLB = REPO_ROOT / "research" / "character_pipeline" / "rigged_human_anatomy_v13.glb"
WEB_DIR = REPO_ROOT / "msk_therapy_os" / "static" / "character_v13"
WEB_GLB = WEB_DIR / "rigged_human_anatomy_v13.glb"


def load_target_deltas_blender(gz_path: Path):
    deltas = {}
    with gzip.open(gz_path, "rt") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                idx = int(parts[0])
                # MakeHuman target coordinates: X -> -X, Y -> Z, Z -> -Y (decimeters * 0.1 -> meters)
                dx = -float(parts[1]) * 0.1
                dy = -float(parts[3]) * 0.1
                dz = float(parts[2]) * 0.1
                deltas[idx] = mathutils.Vector((dx, dy, dz))
    return deltas


def create_materials():
    mats = {}

    # Skin Material
    m_skin = bpy.data.materials.new(name="M_HumanSkin")
    m_skin.use_nodes = True
    b_skin = m_skin.node_tree.nodes.get("Principled BSDF")
    if b_skin:
        b_skin.inputs["Base Color"].default_value = (0.80, 0.65, 0.55, 1.0)
        b_skin.inputs["Roughness"].default_value = 0.45
    mats["skin"] = m_skin

    # Bone Material
    m_bone = bpy.data.materials.new(name="M_Bone")
    m_bone.use_nodes = True
    b_bone = m_bone.node_tree.nodes.get("Principled BSDF")
    if b_bone:
        b_bone.inputs["Base Color"].default_value = (0.90, 0.88, 0.78, 1.0)
        b_bone.inputs["Roughness"].default_value = 0.30
    mats["bone"] = m_bone

    # Muscle Material
    m_muscle = bpy.data.materials.new(name="M_Muscle")
    m_muscle.use_nodes = True
    b_muscle = m_muscle.node_tree.nodes.get("Principled BSDF")
    if b_muscle:
        b_muscle.inputs["Base Color"].default_value = (0.72, 0.18, 0.18, 1.0)
        b_muscle.inputs["Roughness"].default_value = 0.40
    mats["muscle"] = m_muscle

    return mats


def build_canonical_armature():
    with open(RIG_JSON, "r") as f:
        rig_def = json.load(f)

    arm_data = bpy.data.armatures.new("HumanArmature")
    arm_obj = bpy.data.objects.new("HumanArmature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    for bone_name, binfo in rig_def.items():
        eb = edit_bones.new(bone_name)
        head_pos = binfo["head"]["default_position"]
        tail_pos = binfo["tail"]["default_position"]

        eb.head = mathutils.Vector((head_pos[0], head_pos[1], head_pos[2]))
        eb.tail = mathutils.Vector((tail_pos[0], tail_pos[1], tail_pos[2]))

        if (eb.tail - eb.head).length < 0.001:
            eb.tail = eb.head + mathutils.Vector((0, 0, 0.05))

        eb.roll = float(binfo.get("roll", 0.0))

    for bone_name, binfo in rig_def.items():
        parent_name = binfo.get("parent")
        if parent_name and parent_name in edit_bones:
            edit_bones[bone_name].parent = edit_bones[parent_name]

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  Created HumanArmature with {len(arm_data.bones)} canonical bones")
    return arm_obj


def build_fullbody_skin(arm_obj, mat_skin):
    bpy.ops.wm.obj_import(filepath=str(BASE_OBJ))
    mesh_obj = bpy.context.selected_objects[0]
    mesh_obj.name = "HumanBody"
    mesh_obj.scale = (0.1, 0.1, 0.1)
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    verts = mesh_obj.data.vertices
    mesh_obj.shape_key_add(name="Basis", from_mix=False)

    morphs_map = {
        "Height": [ASSETS_DIR / "male-young-maxheight.target.gz"],
        "Proportions": [ASSETS_DIR / "male-young-proportions.target.gz"],
        "ShoulderWidth": [ASSETS_DIR / "shoulder-width-incr.target.gz"],
        "ArmLength": [
            ASSETS_DIR / "l-upperarm-vert-incr.target.gz",
            ASSETS_DIR / "r-upperarm-vert-incr.target.gz",
            ASSETS_DIR / "l-lowerarm-vert-incr.target.gz",
            ASSETS_DIR / "r-lowerarm-vert-incr.target.gz",
        ],
        "LegLength": [
            ASSETS_DIR / "l-upperleg-vert-incr.target.gz",
            ASSETS_DIR / "r-upperleg-vert-incr.target.gz",
            ASSETS_DIR / "l-lowerleg-vert-incr.target.gz",
            ASSETS_DIR / "r-lowerleg-vert-incr.target.gz",
        ],
        "Broader": [
            ASSETS_DIR / "shoulder-width-incr.target.gz",
            ASSETS_DIR / "torso-trans-incr.target.gz",
        ],
        "Slender": [
            ASSETS_DIR / "shoulder-width-decr.target.gz",
            ASSETS_DIR / "waist-circ-decr.target.gz",
        ],
    }

    for morph_name, gz_files in morphs_map.items():
        combined_deltas = {}
        for gzf in gz_files:
            if gzf.exists():
                d = load_target_deltas_blender(gzf)
                for idx, v in d.items():
                    combined_deltas[idx] = combined_deltas.get(idx, mathutils.Vector((0, 0, 0))) + v

        sk = mesh_obj.shape_key_add(name=morph_name, from_mix=False)
        for idx, delta in combined_deltas.items():
            if idx < len(verts):
                sk.data[idx].co = verts[idx].co + delta

    # Assign Skin Weights from weights.game_engine.json
    with open(WEIGHTS_JSON, "r") as f:
        wdata = json.load(f)
    w_dict = wdata.get("weights", {})

    for bname, wlist in w_dict.items():
        if not wlist:
            continue
        vg = mesh_obj.vertex_groups.new(name=bname)
        for v_idx, w in wlist:
            if v_idx < len(verts):
                vg.add([v_idx], float(w), 'REPLACE')

    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True
    mesh_obj.data.materials.append(mat_skin)

    print(f"  Created HumanBody with {len(verts)} vertices, {len(mesh_obj.vertex_groups)} vertex groups, 7 morph targets")
    return mesh_obj


def import_and_transform_bp3d(filename, target_segment):
    """Imports BP3D OBJ, swaps Y and Z, scales and aligns to target anatomical segment."""
    filepath = BP3D_DIR / filename
    bpy.ops.wm.obj_import(filepath=str(filepath))
    obj = bpy.context.selected_objects[0]

    # Swap Y and Z: (x, y, z) -> (x, z, y)
    for v in obj.data.vertices:
        v.co = mathutils.Vector((v.co.x, v.co.z, v.co.y))

    if target_segment == "upperarm":
        bp_head = mathutils.Vector((-0.190, -0.024, 1.415))
        bp_elbow = mathutils.Vector((-0.215, -0.015, 1.108))
        mh_head = mathutils.Vector((-0.1700, -0.0193, 0.5021))
        mh_elbow = mathutils.Vector((-0.3314, -0.0201, 0.3215))

        scale_f = (mh_elbow - mh_head).length / (bp_elbow - bp_head).length
        rot = (bp_elbow - bp_head).normalized().rotation_difference((mh_elbow - mh_head).normalized())
        for v in obj.data.vertices:
            v.co = rot @ ((v.co - bp_head) * scale_f) + mh_head

    elif target_segment == "lowerarm":
        bp_elbow = mathutils.Vector((-0.235, -0.015, 1.115))
        bp_wrist = mathutils.Vector((-0.260, 0.010, 0.884))
        mh_elbow = mathutils.Vector((-0.3314, -0.0201, 0.3215))
        mh_wrist = mathutils.Vector((-0.4533, -0.1833, 0.1973))

        scale_f = (mh_wrist - mh_elbow).length / (bp_wrist - bp_elbow).length
        rot = (bp_wrist - bp_elbow).normalized().rotation_difference((mh_wrist - mh_elbow).normalized())
        for v in obj.data.vertices:
            v.co = rot @ ((v.co - bp_elbow) * scale_f) + mh_elbow

    elif target_segment == "hand":
        mh_wrist = mathutils.Vector((-0.4533, -0.1833, 0.1973))
        bb = [v.co for v in obj.data.vertices]
        mid = (max(bb, key=lambda v: v.z) + min(bb, key=lambda v: v.z)) * 0.5
        for v in obj.data.vertices:
            v.co = (v.co - mid) * 0.70 + mh_wrist + mathutils.Vector((-0.010, -0.020, -0.010))

    elif target_segment == "clavicle":
        mh_clav_head = mathutils.Vector((-0.0227, -0.0216, 0.5248))
        mh_clav_tail = mathutils.Vector((-0.1700, -0.0193, 0.5021))
        bb = [v.co for v in obj.data.vertices]
        bp_c_head = max(bb, key=lambda v: v.x)
        bp_c_tail = min(bb, key=lambda v: v.x)
        scale_f = (mh_clav_tail - mh_clav_head).length / max((bp_c_tail - bp_c_head).length, 0.05)
        for v in obj.data.vertices:
            v.co = (v.co - bp_c_head) * scale_f + mh_clav_head

    elif target_segment == "thigh":
        bp_hip = mathutils.Vector((-0.080, -0.020, 0.890))
        bp_knee = mathutils.Vector((-0.110, -0.025, 0.460))
        mh_hip = mathutils.Vector((-0.1014, -0.0049, 0.0479))
        mh_knee = mathutils.Vector((-0.1425, -0.0374, -0.3431))

        scale_f = (mh_knee - mh_hip).length / (bp_knee - bp_hip).length
        rot = (bp_knee - bp_hip).normalized().rotation_difference((mh_knee - mh_hip).normalized())
        for v in obj.data.vertices:
            v.co = rot @ ((v.co - bp_hip) * scale_f) + mh_hip

    elif target_segment == "calf":
        bp_tibia_knee = mathutils.Vector((-0.075, -0.015, 0.445))
        bp_ankle = mathutils.Vector((-0.070, -0.020, 0.085))
        mh_knee = mathutils.Vector((-0.1425, -0.0374, -0.3431))
        mh_ankle = mathutils.Vector((-0.1806, -0.0227, -0.7486))

        scale_f = (mh_ankle - mh_knee).length / (bp_ankle - bp_tibia_knee).length
        rot = (bp_ankle - bp_tibia_knee).normalized().rotation_difference((mh_ankle - mh_knee).normalized())
        for v in obj.data.vertices:
            v.co = rot @ ((v.co - bp_tibia_knee) * scale_f) + mh_knee

    elif target_segment == "patella":
        mh_knee = mathutils.Vector((-0.1425, -0.0374, -0.3431))
        bb = [v.co for v in obj.data.vertices]
        mid = (max(bb, key=lambda v: v.z) + min(bb, key=lambda v: v.z)) * 0.5
        for v in obj.data.vertices:
            v.co = (v.co - mid) * 0.90 + mh_knee + mathutils.Vector((0.000, 0.042, 0.010))

    obj.data.update()
    return obj


def bind_mesh_to_bones(obj, arm_obj, bone_weights: Dict[str, float]):
    """Binds an anatomical mesh to specific bones with given vertex group weights."""
    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True

    for bname, weight in bone_weights.items():
        vg = obj.vertex_groups.new(name=bname)
        v_indices = list(range(len(obj.data.vertices)))
        vg.add(v_indices, weight, 'REPLACE')


def build_rigged_human_v13():
    print("=================================================================")
    print("MSK-THERAPY-OS V1.3: UNIVERSAL FULL-BODY ANATOMICAL RIG GENERATOR")
    print("=================================================================")
    bpy.ops.wm.read_factory_settings(use_empty=True)

    mats = create_materials()

    # 1. Armature with 53 Canonical Bones
    print("[1/7] Building 53-Bone Canonical Humanoid Armature...")
    arm_obj = build_canonical_armature()

    # 2. Full-Body MakeHuman Skin with Morph Targets
    print("[2/7] Generating Full-Body MakeHuman Skinned Mesh with 7 Morph Targets...")
    skin_obj = build_fullbody_skin(arm_obj, mats["skin"])

    # 3. Upper Limb Authentic BodyParts3D Bones
    print("[3/7] Rigging Upper Limb Authentic Bones (Humerus, Radius, Ulna, Metacarpal, Clavicle)...")
    upper_bones = [
        ("Humerus_R.obj", "Bone_Humerus", "upperarm", {"upperarm_r": 1.0}),
        ("Radius_R.obj", "Bone_Radius", "lowerarm", {"lowerarm_r": 1.0}),
        ("Ulna_R.obj", "Bone_Ulna", "lowerarm", {"lowerarm_r": 1.0}),
        ("Metacarpal_2_R.obj", "Bone_Metacarpal_2", "hand", {"hand_r": 1.0}),
        ("Clavicle_R.obj", "Bone_Clavicle", "clavicle", {"clavicle_r": 1.0}),
    ]
    for fname, bname, seg, weights in upper_bones:
        b_obj = import_and_transform_bp3d(fname, seg)
        b_obj.name = bname
        b_obj.data.materials.append(mats["bone"])
        bind_mesh_to_bones(b_obj, arm_obj, weights)

    # 4. Upper Limb Authentic BodyParts3D Muscles
    print("[4/7] Rigging Upper Limb Dual-Bone Muscles (Biceps, Triceps, Brachialis)...")
    upper_muscles = [
        ("Biceps_brachii_long_R.obj", "Muscle_Biceps_Long", "upperarm", {"upperarm_r": 0.65, "lowerarm_r": 0.35}, True),
        ("Biceps_brachii_short_R.obj", "Muscle_Biceps_Short", "upperarm", {"upperarm_r": 0.70, "lowerarm_r": 0.30}, False),
        ("Triceps_brachii_lateral_R.obj", "Muscle_Triceps_Lateral", "upperarm", {"upperarm_r": 0.70, "lowerarm_r": 0.30}, False),
        ("Triceps_brachii_long_R.obj", "Muscle_Triceps_Long", "upperarm", {"upperarm_r": 0.75, "lowerarm_r": 0.25}, False),
        ("Triceps_brachii_medial_R.obj", "Muscle_Triceps_Medial", "upperarm", {"upperarm_r": 0.60, "lowerarm_r": 0.40}, False),
        ("Brachialis_R.obj", "Muscle_Brachialis", "upperarm", {"upperarm_r": 0.55, "lowerarm_r": 0.45}, False),
    ]
    for fname, mname, seg, weights, has_bulge in upper_muscles:
        m_obj = import_and_transform_bp3d(fname, seg)
        m_obj.name = mname
        m_obj.data.materials.append(mats["muscle"])
        bind_mesh_to_bones(m_obj, arm_obj, weights)

        if has_bulge:
            m_obj.shape_key_add(name="Basis", from_mix=False)
            sk_bulge = m_obj.shape_key_add(name="Biceps_Bulge", from_mix=False)
            bb = [v.co for v in m_obj.data.vertices]
            mid_z = (max(v.z for v in bb) + min(v.z for v in bb)) * 0.5
            half_len = (max(v.z for v in bb) - min(v.z for v in bb)) * 0.5
            for idx, v in enumerate(m_obj.data.vertices):
                dist_mid = abs(v.co.z - mid_z)
                falloff = max(0.0, 1.0 - (dist_mid / max(half_len, 0.01)))
                sk_bulge.data[idx].co = v.co + mathutils.Vector((-0.008 * falloff, 0.006 * falloff, 0.0))

    # 5. Lower Limb Authentic BodyParts3D Bones
    print("[5/7] Rigging Lower Limb Authentic Bones (Femur, Tibia, Fibula, Patella)...")
    lower_bones = [
        ("Femur_R.obj", "Bone_Femur", "thigh", {"thigh_r": 1.0}),
        ("Tibia_R.obj", "Bone_Tibia", "calf", {"calf_r": 1.0}),
        ("Fibula_R.obj", "Bone_Fibula", "calf", {"calf_r": 1.0}),
        ("Patella_R.obj", "Bone_Patella", "patella", {"thigh_r": 0.50, "calf_r": 0.50}),
    ]
    for fname, bname, seg, weights in lower_bones:
        b_obj = import_and_transform_bp3d(fname, seg)
        b_obj.name = bname
        b_obj.data.materials.append(mats["bone"])
        bind_mesh_to_bones(b_obj, arm_obj, weights)

    # 6. Lower Limb Authentic BodyParts3D Muscles (Quadriceps)
    print("[6/7] Rigging Lower Limb Dual-Bone Muscles (Rectus Femoris, Vastus Lateralis/Medialis/Intermedius)...")
    lower_muscles = [
        ("Rectus_femoris_R.obj", "Muscle_Rectus_Femoris", "thigh", {"thigh_r": 0.70, "calf_r": 0.30}, True),
        ("Vastus_intermedius_R.obj", "Muscle_Vastus_Intermedius", "thigh", {"thigh_r": 0.75, "calf_r": 0.25}, False),
        ("Vastus_lateralis_R.obj", "Muscle_Vastus_Lateralis", "thigh", {"thigh_r": 0.80, "calf_r": 0.20}, False),
        ("Vastus_medialis_R.obj", "Muscle_Vastus_Medialis", "thigh", {"thigh_r": 0.75, "calf_r": 0.25}, False),
    ]
    for fname, mname, seg, weights, has_bulge in lower_muscles:
        m_obj = import_and_transform_bp3d(fname, seg)
        m_obj.name = mname
        m_obj.data.materials.append(mats["muscle"])
        bind_mesh_to_bones(m_obj, arm_obj, weights)

        if has_bulge:
            m_obj.shape_key_add(name="Basis", from_mix=False)
            sk_flex = m_obj.shape_key_add(name="Quad_Flex", from_mix=False)
            bb = [v.co for v in m_obj.data.vertices]
            mid_z = (max(v.z for v in bb) + min(v.z for v in bb)) * 0.5
            half_len = (max(v.z for v in bb) - min(v.z for v in bb)) * 0.5
            for idx, v in enumerate(m_obj.data.vertices):
                dist_mid = abs(v.co.z - mid_z)
                falloff = max(0.0, 1.0 - (dist_mid / max(half_len, 0.01)))
                sk_flex.data[idx].co = v.co + mathutils.Vector((0.005 * falloff, 0.008 * falloff, 0.0))

    # 7. Animation Tracks: Complete Multi-Segment Action (A_HumanoidMotion)
    print("[7/7] Generating Synchronized Arm & Leg Animation Tracks...")
    arm_obj.animation_data_create()
    action = bpy.data.actions.new(name="A_HumanoidMotion")
    arm_obj.animation_data.action = action

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'

    # Frame 1: Rest Pose (0 deg)
    for pb in arm_obj.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.keyframe_insert(data_path="rotation_euler", frame=1)

    # Frame 30: Elbow flex 45 deg
    if "lowerarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["lowerarm_r"].rotation_euler = (math.radians(45), 0, 0)
        arm_obj.pose.bones["lowerarm_r"].keyframe_insert(data_path="rotation_euler", frame=30)

    # Frame 60: Elbow flex 90 deg
    if "lowerarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["lowerarm_r"].rotation_euler = (math.radians(90), 0, 0)
        arm_obj.pose.bones["lowerarm_r"].keyframe_insert(data_path="rotation_euler", frame=60)

    # Frame 90: Shoulder Abd 45 deg + Elbow flex 45 deg
    if "upperarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["upperarm_r"].rotation_euler = (0, 0, math.radians(-45))
        arm_obj.pose.bones["upperarm_r"].keyframe_insert(data_path="rotation_euler", frame=90)
    if "lowerarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["lowerarm_r"].rotation_euler = (math.radians(45), 0, 0)
        arm_obj.pose.bones["lowerarm_r"].keyframe_insert(data_path="rotation_euler", frame=90)

    # Frame 120: Knee Flexion 60 deg (calf_r rot X = +60 deg)
    if "calf_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["calf_r"].rotation_euler = (math.radians(60), 0, 0)
        arm_obj.pose.bones["calf_r"].keyframe_insert(data_path="rotation_euler", frame=120)

    # Frame 150: Simultaneous Motion (Elbow 90 deg + Knee 60 deg + Torso 15 deg)
    if "lowerarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["lowerarm_r"].rotation_euler = (math.radians(90), 0, 0)
        arm_obj.pose.bones["lowerarm_r"].keyframe_insert(data_path="rotation_euler", frame=150)
    if "calf_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["calf_r"].rotation_euler = (math.radians(60), 0, 0)
        arm_obj.pose.bones["calf_r"].keyframe_insert(data_path="rotation_euler", frame=150)
    if "spine_02" in arm_obj.pose.bones:
        arm_obj.pose.bones["spine_02"].rotation_euler = (0, 0, math.radians(15))
        arm_obj.pose.bones["spine_02"].keyframe_insert(data_path="rotation_euler", frame=150)

    # Frame 180: Complete Return to Rest Pose (0 deg)
    for pb in arm_obj.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.keyframe_insert(data_path="rotation_euler", frame=180)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Export .blend and .glb
    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    WEB_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Saving .blend to {OUT_BLEND}...")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))

    print(f"Exporting GLB to {OUT_GLB}...")
    bpy.ops.export_scene.gltf(
        filepath=str(OUT_GLB),
        export_format='GLB',
        use_selection=False,
        export_apply=False,
        export_animations=True,
        export_morph=True,
        export_skins=True,
        export_all_influences=True,
        export_def_bones=True
    )

    # Copy to static web directory
    WEB_GLB.write_bytes(OUT_GLB.read_bytes())
    print(f"SUCCESS: Exported {OUT_GLB} ({OUT_GLB.stat().st_size} bytes)")
    print(f"COPIED: to {WEB_GLB}")


if __name__ == "__main__":
    build_rigged_human_v13()
