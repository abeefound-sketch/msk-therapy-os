import bpy
import json
import math
import mathutils
from pathlib import Path

BASE_OBJ = Path(r"D:\5Projects\msk-therapy-os\research\character_pipeline\makehuman_assets\base.obj")
RIG_JSON = Path(r"D:\5Projects\msk-therapy-os\research\character_pipeline\makehuman_assets\rig.game_engine.json")
WEIGHTS_JSON = Path(r"D:\5Projects\msk-therapy-os\research\character_pipeline\makehuman_assets\weights.game_engine.json")
OUT_GLB = Path(r"D:\5Projects\msk-therapy-os\research\character_pipeline\rigged_human_v11.glb")
OUT_BLEND = Path(r"D:\5Projects\msk-therapy-os\research\character_pipeline\rigged_human_v11.blend")

def build_rigged_character():
    print("=== BUILDING RIGGED HUMAN CHARACTER FROM MAKEHUMAN ASSETS ===")
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Import base.obj
    print("Importing base.obj...")
    bpy.ops.wm.obj_import(filepath=str(BASE_OBJ))
    
    # Get the imported mesh
    mesh_obj = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            mesh_obj = obj
            break
            
    assert mesh_obj is not None, "Failed to import base.obj mesh"
    mesh_obj.name = "HumanBody"
    print(f"Imported mesh: {mesh_obj.name} with {len(mesh_obj.data.vertices)} vertices, {len(mesh_obj.data.polygons)} polygons")
    
    # Check bounds
    bb = [mesh_obj.matrix_world @ mathutils.Vector(corner) for corner in mesh_obj.bound_box]
    min_z = min(v.z for v in bb)
    max_z = max(v.z for v in bb)
    print(f"Mesh Z range: {min_z:.3f} to {max_z:.3f} (height={max_z-min_z:.3f}m)")

    # 2. Load rig definition
    with open(RIG_JSON, "r") as f:
        rig_def = json.load(f)
        
    with open(WEIGHTS_JSON, "r") as f:
        weights_data = json.load(f)
    weights_def = weights_data.get("weights", {})

    # 3. Create Armature
    print("Creating Armature...")
    arm_data = bpy.data.armatures.new("HumanArmature")
    arm_obj = bpy.data.objects.new("HumanArmature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    
    # Switch to edit mode to add bones
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    edit_bones = arm_data.edit_bones
    
    # First pass: create all bones with head and tail
    for bone_name, binfo in rig_def.items():
        eb = edit_bones.new(bone_name)
        head_pos = binfo["head"]["default_position"]
        tail_pos = binfo["tail"]["default_position"]
        
        eb.head = mathutils.Vector((head_pos[0], head_pos[1], head_pos[2]))
        eb.tail = mathutils.Vector((tail_pos[0], tail_pos[1], tail_pos[2]))
        
        # If head and tail are identical or too close, offset tail slightly
        if (eb.tail - eb.head).length < 0.001:
            eb.tail = eb.head + mathutils.Vector((0, 0, 0.05))
            
        eb.roll = float(binfo.get("roll", 0.0))

    # Second pass: set parents
    for bone_name, binfo in rig_def.items():
        parent_name = binfo.get("parent")
        if parent_name and parent_name in edit_bones:
            edit_bones[bone_name].parent = edit_bones[parent_name]

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Created Armature with {len(arm_data.bones)} bones")

    # 4. Bind Mesh to Armature and assign Vertex Groups (Skin Weights)
    print("Assigning vertex groups and skin weights...")
    for bone_name, wlist in weights_def.items():
        if not wlist:
            continue
        vg = mesh_obj.vertex_groups.new(name=bone_name)
        for v_idx, w in wlist:
            vg.add([v_idx], float(w), 'REPLACE')

    print(f"Assigned {len(mesh_obj.vertex_groups)} vertex groups to mesh")

    # 5. Add Armature Modifier to mesh
    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True

    # 6. Create Basic Material for character
    mat = bpy.data.materials.new(name="M_HumanSkin")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        # Subtle warm skin tone
        bsdf.inputs["Base Color"].default_value = (0.82, 0.68, 0.58, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.45
    mesh_obj.data.materials.append(mat)

    # 7. Add Test Animation (Flex elbow 0 to 90 degrees, raise arm, flex knee)
    print("Creating test animations...")
    arm_obj.animation_data_create()
    action = bpy.data.actions.new(name="A_TestMotion")
    arm_obj.animation_data.action = action

    # Switch to pose mode
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    # Keyframe 1 (Frame 1): Rest Pose (0 deg)
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.keyframe_insert(data_path="rotation_euler", frame=1)

    # Keyframe 30 (Frame 30): Elbow flex 45 deg, arm raise 20 deg
    if "lowerarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["lowerarm_r"].rotation_euler = (0, math.radians(-45), 0)
        arm_obj.pose.bones["lowerarm_r"].keyframe_insert(data_path="rotation_euler", frame=30)
    if "upperarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["upperarm_r"].rotation_euler = (0, 0, math.radians(-20))
        arm_obj.pose.bones["upperarm_r"].keyframe_insert(data_path="rotation_euler", frame=30)
    if "calf_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["calf_r"].rotation_euler = (math.radians(30), 0, 0)
        arm_obj.pose.bones["calf_r"].keyframe_insert(data_path="rotation_euler", frame=30)

    # Keyframe 60 (Frame 60): Elbow flex 90 deg, arm raise 45 deg, knee flex 60 deg
    if "lowerarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["lowerarm_r"].rotation_euler = (0, math.radians(-90), 0)
        arm_obj.pose.bones["lowerarm_r"].keyframe_insert(data_path="rotation_euler", frame=60)
    if "upperarm_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["upperarm_r"].rotation_euler = (0, 0, math.radians(-45))
        arm_obj.pose.bones["upperarm_r"].keyframe_insert(data_path="rotation_euler", frame=60)
    if "calf_r" in arm_obj.pose.bones:
        arm_obj.pose.bones["calf_r"].rotation_euler = (math.radians(60), 0, 0)
        arm_obj.pose.bones["calf_r"].keyframe_insert(data_path="rotation_euler", frame=60)

    # Keyframe 90 (Frame 90): Return to Rest Pose (0 deg)
    for pb in arm_obj.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.keyframe_insert(data_path="rotation_euler", frame=90)

    bpy.ops.object.mode_set(mode='OBJECT')

    # 8. Save .blend file
    print(f"Saving .blend file to {OUT_BLEND}...")
    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))

    # 9. Export GLB
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

    print(f"GLB export complete! File size: {OUT_GLB.stat().st_size} bytes")

if __name__ == "__main__":
    build_rigged_character()
