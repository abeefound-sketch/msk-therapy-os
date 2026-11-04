"""
MSK-Therapy-OS V1.2.1 — Full Integrated Rigged Arm Anatomy 3D Asset Builder
===========================================================================
Constructs the complete, reality-validated 3D anatomical upper limb:
1. Armature with 4 canonical bones: clavicle_r -> upperarm_r -> lowerarm_r -> hand_r.
2. Genuine MakeHuman Arm Skin (extracted from base.obj) with:
   - 4-bone Linear Blend Skinning.
   - GPU Morph Targets: ArmLength, ShoulderWidth, Broader, Slender.
3. Authentic BodyParts3D bones (CC BY 4.0 DBCLS Japan):
   - Humerus_R (FJ3368)
   - Radius_R (FJ3349)
   - Ulna_R (FJ3391)
   - Metacarpal_2_R (FJ3352)
   - Clavicle_R (FJ3362)
4. Authentic BodyParts3D muscles (CC BY 4.0 DBCLS Japan):
   - Biceps brachii - Long head (FJ1478)
   - Biceps brachii - Short head (FJ1512)
   - Triceps brachii - Lateral head (FJ1477)
   - Triceps brachii - Long head (FJ1479)
   - Triceps brachii - Medial head (FJ1480)
   - Brachialis (FJ1486)
5. True Shape Key Bulging (Biceps_Bulge).
6. 4-Posture Physiological Animation Action (0° -> 45° -> 90° -> 120° -> 0°).
7. Exports both .blend and .glb for Three.js WebGL rendering.
"""

import bpy
import gzip
import json
import math
import mathutils
from pathlib import Path

REPO_ROOT = Path(r"D:\5Projects\msk-therapy-os")
BP3D_DIR = REPO_ROOT / "tools" / "blender_anatomy_studio" / "assets" / "bp3d"
MAKEHUMAN_DIR = REPO_ROOT / "research" / "character_pipeline" / "makehuman_assets"
OUT_BLEND = REPO_ROOT / "research" / "character_pipeline" / "rigged_arm_anatomy_v12_1.blend"
OUT_GLB = REPO_ROOT / "research" / "character_pipeline" / "rigged_arm_anatomy_v12_1.glb"


def create_armature(scene):
    print("[1/7] Creating Armature with 4 Canonical Arm Bones...")
    arm_data = bpy.data.armatures.new("ArmArmature")
    arm_obj = bpy.data.objects.new("ArmArmature", arm_data)
    scene.collection.objects.link(arm_obj)

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = arm_data.edit_bones

    # 1. clavicle_r
    b_clav = ebs.new("clavicle_r")
    b_clav.head = mathutils.Vector((-0.0227, -0.0216, 0.5248))
    b_clav.tail = mathutils.Vector((-0.1700, -0.0193, 0.5021))
    b_clav.roll = -1.6565

    # 2. upperarm_r
    b_up = ebs.new("upperarm_r")
    b_up.head = mathutils.Vector((-0.1700, -0.0193, 0.5021))
    b_up.tail = mathutils.Vector((-0.3314, -0.0201, 0.3215))
    b_up.parent = b_clav
    b_up.roll = -2.3680

    # 3. lowerarm_r
    b_low = ebs.new("lowerarm_r")
    b_low.head = mathutils.Vector((-0.3314, -0.0201, 0.3215))
    b_low.tail = mathutils.Vector((-0.4533, -0.1833, 0.1973))
    b_low.parent = b_up
    b_low.roll = -2.3047

    # 4. hand_r
    b_hand = ebs.new("hand_r")
    b_hand.head = mathutils.Vector((-0.4533, -0.1833, 0.1973))
    b_hand.tail = mathutils.Vector((-0.4640, -0.2094, 0.1816))
    b_hand.parent = b_low
    b_hand.roll = 2.8013

    bpy.ops.object.mode_set(mode='OBJECT')
    print("  Armature created with 4 bones.")
    return arm_obj


def create_materials():
    print("[2/7] Configuring PBR Materials...")
    # Skin
    mat_skin = bpy.data.materials.new("M_ArmSkin")
    mat_skin.use_nodes = True
    bsdf = mat_skin.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.82, 0.68, 0.58, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.40
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 0.55
    mat_skin.blend_method = 'BLEND'

    # Bone
    mat_bone = bpy.data.materials.new("M_Bone")
    mat_bone.use_nodes = True
    bsdf = mat_bone.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.90, 0.82, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35

    # Biceps
    mat_biceps = bpy.data.materials.new("M_Biceps")
    mat_biceps.use_nodes = True
    bsdf = mat_biceps.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.22, 0.22, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.45

    # Triceps
    mat_triceps = bpy.data.materials.new("M_Triceps")
    mat_triceps.use_nodes = True
    bsdf = mat_triceps.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.75, 0.18, 0.22, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.45

    # Brachialis
    mat_brach = bpy.data.materials.new("M_Brachialis")
    mat_brach.use_nodes = True
    bsdf = mat_brach.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.80, 0.30, 0.28, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.45

    return {
        "skin": mat_skin,
        "bone": mat_bone,
        "biceps": mat_biceps,
        "triceps": mat_triceps,
        "brachialis": mat_brach
    }


def load_target_deltas_blender(gz_path):
    """Reads MakeHuman target deltas and maps from MH (X, Y up, Z depth) to Blender (X, Y depth, Z up)."""
    deltas = {}
    with gzip.open(gz_path, "rt") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                idx = int(parts[0])
                dx = float(parts[1]) * 0.1
                dy_mh = float(parts[2]) * 0.1
                dz_mh = float(parts[3]) * 0.1
                # When base.obj rotation of +90 around X is applied: y_new = -z_old, z_new = y_old
                deltas[idx] = mathutils.Vector((dx, -dz_mh, dy_mh))
    return deltas


def build_makehuman_arm_skin(arm_obj, mat_skin):
    print("[3/7] Extracting Genuine MakeHuman Arm Skin with Morph Targets...")
    base_obj_path = MAKEHUMAN_DIR / "base.obj"
    weights_path = MAKEHUMAN_DIR / "weights.game_engine.json"

    # 1. Import base.obj
    bpy.ops.wm.obj_import(filepath=str(base_obj_path))
    mesh_obj = bpy.context.selected_objects[0]
    mesh_obj.name = "ArmSkin_MakeHuman"
    mesh_obj.data.materials.append(mat_skin)

    # Scale to meters and apply transform
    mesh_obj.scale = (0.1, 0.1, 0.1)
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # 2. Add Shape Keys (Basis + Morph Targets) BEFORE deleting vertices
    sk_basis = mesh_obj.shape_key_add(name="Basis", from_mix=False)

    targets = {
        "ArmLength": [
            MAKEHUMAN_DIR / "r-upperarm-vert-incr.target.gz",
            MAKEHUMAN_DIR / "r-lowerarm-vert-incr.target.gz"
        ],
        "ShoulderWidth": [
            MAKEHUMAN_DIR / "shoulder-width-incr.target.gz"
        ],
        "Broader": [
            MAKEHUMAN_DIR / "male-young-proportions.target.gz"
        ],
        "Slender": [
            MAKEHUMAN_DIR / "male-young-minheight.target.gz"
        ]
    }

    verts = mesh_obj.data.vertices
    for morph_name, gz_files in targets.items():
        combined_deltas = {}
        for gzf in gz_files:
            if gzf.exists():
                d = load_target_deltas_blender(gzf)
                for idx, v in d.items():
                    combined_deltas[idx] = combined_deltas.get(idx, mathutils.Vector((0, 0, 0))) + v

        sk = mesh_obj.shape_key_add(name=morph_name, from_mix=False)
        for idx, delta in combined_deltas.items():
            if idx < len(verts):
                if morph_name == "Slender":
                    sk.data[idx].co = verts[idx].co - delta * 0.40
                else:
                    sk.data[idx].co = verts[idx].co + delta

    # 3. Assign Vertex Weights for all 4 arm bones
    with open(weights_path, "r") as f:
        wdata = json.load(f)
    w_dict = wdata.get("weights", {})

    arm_bones = ["clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"]
    arm_vset = set()

    for bname in arm_bones:
        vg = mesh_obj.vertex_groups.new(name=bname)
        for v_idx, w in w_dict.get(bname, []):
            if v_idx < len(verts):
                vg.add([v_idx], float(w), 'REPLACE')
                if float(w) > 0.05:
                    arm_vset.add(v_idx)

    # Also include nearby vertices forming right shoulder/clavicle connection
    for idx, v in enumerate(verts):
        if -0.48 < v.co.x < -0.01 and 0.15 < v.co.z < 0.60 and -0.25 < v.co.y < 0.08:
            arm_vset.add(idx)

    # 4. Bind to Armature
    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True

    # 5. Isolate right arm: delete vertices not in arm_vset
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    for idx, v in enumerate(verts):
        if idx not in arm_vset:
            v.select = True

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"  Extracted ArmSkin_MakeHuman with {len(mesh_obj.data.vertices)} vertices, {len(mesh_obj.data.shape_keys.key_blocks)-1} morph targets.")
    return mesh_obj


def import_and_transform_bp3d(filename, target_segment="upperarm"):
    """Imports BP3D OBJ, swaps Y and Z, scales and aligns to target bone segment."""
    filepath = BP3D_DIR / filename
    bpy.ops.wm.obj_import(filepath=str(filepath))
    obj = bpy.context.selected_objects[0]

    # Swap Y and Z: (x, y, z) -> (x, z, y)
    for v in obj.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        v.co = mathutils.Vector((x, z, y))

    if target_segment == "upperarm":
        bp_head = mathutils.Vector((-0.190, -0.024, 1.415))
        bp_elbow = mathutils.Vector((-0.215, -0.015, 1.108))
        bp_dir = (bp_elbow - bp_head).normalized()

        mh_head = mathutils.Vector((-0.1700, -0.0193, 0.5021))
        mh_elbow = mathutils.Vector((-0.3314, -0.0201, 0.3215))
        mh_dir = (mh_elbow - mh_head).normalized()

        scale_f = (mh_elbow - mh_head).length / (bp_elbow - bp_head).length
        rot = bp_dir.rotation_difference(mh_dir)

        for v in obj.data.vertices:
            rel = v.co - bp_head
            scaled = rel * scale_f
            rotated = rot @ scaled
            v.co = rotated + mh_head

    elif target_segment == "lowerarm":
        bp_elbow = mathutils.Vector((-0.235, -0.015, 1.115))
        bp_wrist = mathutils.Vector((-0.260, 0.010, 0.884))
        bp_dir = (bp_wrist - bp_elbow).normalized()

        mh_elbow = mathutils.Vector((-0.3314, -0.0201, 0.3215))
        mh_wrist = mathutils.Vector((-0.4533, -0.1833, 0.1973))
        mh_dir = (mh_wrist - mh_elbow).normalized()

        scale_f = (mh_wrist - mh_elbow).length / (bp_wrist - bp_elbow).length
        rot = bp_dir.rotation_difference(mh_dir)

        for v in obj.data.vertices:
            rel = v.co - bp_elbow
            scaled = rel * scale_f
            rotated = rot @ scaled
            v.co = rotated + mh_elbow

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

    obj.data.update()
    return obj


def bind_mesh_to_armature(obj, arm_obj, default_bone=None, dual_blend=False):
    """Binds mesh with vertex groups and armature modifier."""
    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True

    if default_bone:
        vg = obj.vertex_groups.new(name=default_bone)
        all_indices = list(range(len(obj.data.vertices)))
        vg.add(all_indices, 1.0, 'REPLACE')

    elif dual_blend:
        vg_up = obj.vertex_groups.new(name="upperarm_r")
        vg_low = obj.vertex_groups.new(name="lowerarm_r")

        for idx, v in enumerate(obj.data.vertices):
            z = v.co.z
            if z > 0.38:
                w_up = 1.0
                w_low = 0.0
            elif z < 0.28:
                w_up = 0.0
                w_low = 1.0
            else:
                t = (z - 0.28) / 0.10
                w_up = t
                w_low = 1.0 - t

            if w_up > 0.0:
                vg_up.add([idx], float(w_up), 'REPLACE')
            if w_low > 0.0:
                vg_low.add([idx], float(w_low), 'REPLACE')


def add_biceps_bulge_shape_key(obj):
    """Adds a Shape Key for Biceps Belly Bulge (isovolumetric expansion factor ~14%)."""
    sk_basis = obj.shape_key_add(name="Basis", from_mix=False)
    sk_bulge = obj.shape_key_add(name="Biceps_Bulge", from_mix=False)

    bb = [v.co for v in obj.data.vertices]
    mid_z = (max(v.z for v in bb) + min(v.z for v in bb)) * 0.5
    half_h = (max(v.z for v in bb) - min(v.z for v in bb)) * 0.5

    for idx, v in enumerate(obj.data.vertices):
        dist_z = abs(v.co.z - mid_z) / max(half_h, 0.01)
        belly_weight = max(0.0, 1.0 - dist_z * dist_z)

        norm = v.normal
        # Expand radially by up to 14%
        bulge_disp = norm * (0.014 * belly_weight)
        sk_bulge.data[idx].co = v.co + bulge_disp


def build_rigged_arm_v12_1():
    print("==================================================================")
    print("MSK-THERAPY-OS V1.2.1: INTEGRATED RIGGED ARM ANATOMICAL STUDIO")
    print("==================================================================")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # 1. Armature
    arm_obj = create_armature(scene)

    # 2. Materials
    mats = create_materials()

    # 3. MakeHuman Right Arm Skin Mesh with Morph Targets
    skin_obj = build_makehuman_arm_skin(arm_obj, mats["skin"])

    # 4. Authentic BP3D Bones
    print("[4/7] Importing and Rigging Authentic BodyParts3D Bones...")
    bones_specs = [
        ("Humerus_R.obj", "Bone_Humerus", "upperarm", "upperarm_r"),
        ("Radius_R.obj", "Bone_Radius", "lowerarm", "lowerarm_r"),
        ("Ulna_R.obj", "Bone_Ulna", "lowerarm", "lowerarm_r"),
        ("Metacarpal_2_R.obj", "Bone_Metacarpal_2", "hand", "hand_r"),
        ("Clavicle_R.obj", "Bone_Clavicle", "clavicle", "clavicle_r"),
    ]

    for fname, bname, seg, parent_b in bones_specs:
        b_obj = import_and_transform_bp3d(fname, seg)
        b_obj.name = bname
        b_obj.data.materials.append(mats["bone"])
        bind_mesh_to_armature(b_obj, arm_obj, default_bone=parent_b)
        print(f"  Bound {bname} ({len(b_obj.data.vertices)} verts) -> {parent_b}")

    # 5. Authentic BP3D Muscles
    print("[5/7] Importing and Rigging Authentic BodyParts3D Muscles with Dual-Skinning & Bulge...")
    muscles_specs = [
        ("Biceps_brachii_long_R.obj", "Muscle_Biceps_Long", mats["biceps"], True),
        ("Biceps_brachii_short_R.obj", "Muscle_Biceps_Short", mats["biceps"], True),
        ("Triceps_brachii_lateral_R.obj", "Muscle_Triceps_Lateral", mats["triceps"], False),
        ("Triceps_brachii_long_R.obj", "Muscle_Triceps_Long", mats["triceps"], False),
        ("Triceps_brachii_medial_R.obj", "Muscle_Triceps_Medial", mats["triceps"], False),
        ("Brachialis_R.obj", "Muscle_Brachialis", mats["brachialis"], False),
    ]

    for fname, mname, mat, has_bulge in muscles_specs:
        m_obj = import_and_transform_bp3d(fname, "upperarm")
        m_obj.name = mname
        m_obj.data.materials.append(mat)
        bind_mesh_to_armature(m_obj, arm_obj, dual_blend=True)
        if has_bulge:
            add_biceps_bulge_shape_key(m_obj)
            print(f"  Bound {mname} with Dual-Bone Skinning + Biceps_Bulge Shape Key")
        else:
            print(f"  Bound {mname} with Dual-Bone Skinning")

    # 6. Keyframed Animation (0° -> 45° -> 90° -> 120° -> 0°)
    print("[6/7] Generating Animation Tracks: Elbow Flexion 0° -> 45° -> 90° -> 120°...")
    arm_obj.animation_data_create()
    action = bpy.data.actions.new(name="A_ElbowFlexion_0_120")
    arm_obj.animation_data.action = action

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'

    pb_low = arm_obj.pose.bones.get("lowerarm_r")

    # Frame 1: 0 deg
    pb_low.rotation_euler = (0, 0, 0)
    pb_low.keyframe_insert(data_path="rotation_euler", frame=1)

    # Frame 30: 45 deg
    pb_low.rotation_euler = (math.radians(45), 0, 0)
    pb_low.keyframe_insert(data_path="rotation_euler", frame=30)

    # Frame 60: 90 deg
    pb_low.rotation_euler = (math.radians(90), 0, 0)
    pb_low.keyframe_insert(data_path="rotation_euler", frame=60)

    # Frame 90: 120 deg (Deep physiological flexion)
    pb_low.rotation_euler = (math.radians(120), 0, 0)
    pb_low.keyframe_insert(data_path="rotation_euler", frame=90)

    # Frame 120: Return to 0 deg
    pb_low.rotation_euler = (0, 0, 0)
    pb_low.keyframe_insert(data_path="rotation_euler", frame=120)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Keyframe Biceps_Bulge on biceps meshes
    for mname in ["Muscle_Biceps_Long", "Muscle_Biceps_Short"]:
        m_obj = bpy.data.objects.get(mname)
        if m_obj and m_obj.data.shape_keys:
            sk_bulge = m_obj.data.shape_keys.key_blocks.get("Biceps_Bulge")
            if sk_bulge:
                sk_bulge.value = 0.0
                sk_bulge.keyframe_insert(data_path="value", frame=1)
                sk_bulge.value = 0.38
                sk_bulge.keyframe_insert(data_path="value", frame=30)
                sk_bulge.value = 0.78
                sk_bulge.keyframe_insert(data_path="value", frame=60)
                sk_bulge.value = 1.00
                sk_bulge.keyframe_insert(data_path="value", frame=90)
                sk_bulge.value = 0.0
                sk_bulge.keyframe_insert(data_path="value", frame=120)

    # 7. Export .blend and .glb
    print(f"[7/7] Saving .blend to {OUT_BLEND}...")
    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
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

    print(f"SUCCESS: Exported {OUT_GLB} ({OUT_GLB.stat().st_size} bytes)")


if __name__ == "__main__":
    build_rigged_arm_v12_1()
