import bpy
import gzip
import json
import math
import mathutils
from pathlib import Path

ASSETS_DIR = Path(r"D:\5Projects\msk-therapy-os\research\character_pipeline\makehuman_assets")
BASE_OBJ = ASSETS_DIR / "base.obj"
RIG_JSON = ASSETS_DIR / "rig.game_engine.json"
WEIGHTS_JSON = ASSETS_DIR / "weights.game_engine.json"
OUT_GLB = Path(r"D:\5Projects\msk-therapy-os\research\character_pipeline\rigged_human_v11.glb")
OUT_BLEND = Path(r"D:\5Projects\msk-therapy-os\research\character_pipeline\rigged_human_v11.blend")

def load_target_deltas(gz_path):
    """Reads MakeHuman .target.gz file and returns dict: {v_idx: Vector((dx, dy, dz))} in METERS."""
    deltas = {}
    with gzip.open(gz_path, "rt") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                idx = int(parts[0])
                dx = float(parts[1]) * 0.1
                dy = float(parts[2]) * 0.1
                dz = float(parts[3]) * 0.1
                deltas[idx] = mathutils.Vector((dx, dy, dz))
    return deltas

def build_rigged_character():
    print("==========================================================")
    print("MSK-THERAPY-OS V1.1: BUILDING RIGGED CHARACTER WITH MORPHS")
    print("==========================================================")
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Import base.obj
    print("[1/8] Importing base.obj...")
    bpy.ops.wm.obj_import(filepath=str(BASE_OBJ))
    
    mesh_obj = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            mesh_obj = obj
            break
            
    assert mesh_obj is not None, "Failed to import base.obj mesh"
    mesh_obj.name = "HumanBody"
    
    # Scale base mesh by 0.1 (decimeters -> meters)
    mesh_obj.scale = (0.1, 0.1, 0.1)
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    verts = mesh_obj.data.vertices
    print(f"Mesh has {len(verts)} vertices, {len(mesh_obj.data.polygons)} polygons")
    
    bb = [mesh_obj.matrix_world @ mathutils.Vector(corner) for corner in mesh_obj.bound_box]
    min_z = min(v.z for v in bb)
    max_z = max(v.z for v in bb)
    print(f"Scaled Mesh Z bounds: {min_z:.3f} to {max_z:.3f} (Height = {max_z-min_z:.3f} m)")

    # 2. Add Shape Keys (Morph Targets)
    print("[2/8] Creating Shape Keys (Morph Targets)...")
    sk_basis = mesh_obj.shape_key_add(name="Basis", from_mix=False)
    
    targets_map = {
        "Height": [ASSETS_DIR / "male-young-maxheight.target.gz"],
        "Proportions": [ASSETS_DIR / "male-young-proportions.target.gz"],
        "ShoulderWidth": [ASSETS_DIR / "shoulder-width-incr.target.gz"],
        "WaistCircumference": [ASSETS_DIR / "waist-circ-incr.target.gz"],
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
        ]
    }
    
    for sk_name, gz_files in targets_map.items():
        combined_deltas = {}
        for gz_file in gz_files:
            if gz_file.exists():
                d = load_target_deltas(gz_file)
                for idx, vec in d.items():
                    combined_deltas[idx] = combined_deltas.get(idx, mathutils.Vector((0, 0, 0))) + vec
        
        sk = mesh_obj.shape_key_add(name=sk_name, from_mix=False)
        for idx, delta in combined_deltas.items():
            if idx < len(verts):
                sk.data[idx].co = verts[idx].co + delta
        print(f"  Added shape key '{sk_name}' with {len(combined_deltas)} displaced vertices")

    # 3. Create Armature from rig.game_engine.json
    print("[3/8] Creating Armature from game_engine rig...")
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
    print(f"  Created Armature with {len(arm_data.bones)} bones")

    # 4. Assign Skin Weights
    print("[4/8] Assigning skin weights from weights.game_engine.json...")
    with open(WEIGHTS_JSON, "r") as f:
        weights_data = json.load(f)
    weights_def = weights_data.get("weights", {})
    
    for bone_name, wlist in weights_def.items():
        if not wlist:
            continue
        vg = mesh_obj.vertex_groups.new(name=bone_name)
        for v_idx, w in wlist:
            if v_idx < len(verts):
                vg.add([v_idx], float(w), 'REPLACE')

    print(f"  Assigned {len(mesh_obj.vertex_groups)} vertex groups")

    # 5. Bind Mesh to Armature
    print("[5/8] Binding Mesh to Armature with Armature Modifier...")
    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True

    # 6. Setup Material
    print("[6/8] Configuring Principled BSDF Skin Material...")
    mat = bpy.data.materials.new(name="M_HumanSkin")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.80, 0.65, 0.55, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.45
    mesh_obj.data.materials.append(mat)

    # 7. Create Animations (Complete Range of Motion Actions)
    print("[7/8] Generating Animation Tracks...")
    arm_obj.animation_data_create()
    action = bpy.data.actions.new(name="A_HumanoidMotion")
    arm_obj.animation_data.action = action

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    # Ensure all bones have rotation_mode XYZ
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

    # Frame 60: Elbow flex 90 deg (full physiological elbow flexion)
    if "lowerarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["lowerarm_r"].rotation_euler = (math.radians(90), 0, 0)
        arm_obj.pose.bones["lowerarm_r"].keyframe_insert(data_path="rotation_euler", frame=60)

    # Frame 90: Shoulder Abduction 45 deg + Elbow flex 45 deg
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

    # Frame 150: Torso Twist 20 deg + Wrist Rotation 30 deg
    if "spine_02" in arm_obj.pose.bones:
        arm_obj.pose.bones["spine_02"].rotation_euler = (0, 0, math.radians(20))
        arm_obj.pose.bones["spine_02"].keyframe_insert(data_path="rotation_euler", frame=150)
    if "hand_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["hand_r"].rotation_euler = (0, math.radians(30), 0)
        arm_obj.pose.bones["hand_r"].keyframe_insert(data_path="rotation_euler", frame=150)

    # Frame 180: Complete Return to Rest Pose (0 deg)
    for pb in arm_obj.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.keyframe_insert(data_path="rotation_euler", frame=180)

    bpy.ops.object.mode_set(mode='OBJECT')

    # 8. Export .blend and .glb
    print(f"[8/8] Saving {OUT_BLEND} and exporting {OUT_GLB}...")
    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))

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
    build_rigged_character()
