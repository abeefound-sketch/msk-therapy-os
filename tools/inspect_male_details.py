import bpy
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r'D:\5Projects\msk-therapy-os\3refs\upstream\acupuncture-3d-authoring\models\male_character.glb')

print("SUMMARY OF OBJECTS IN male_character.glb:")
for obj in bpy.data.objects:
    print(f"- {obj.name} (type={obj.type})")
    if obj.type == 'MESH':
        bb = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        min_z = min(v.z for v in bb)
        max_z = max(v.z for v in bb)
        min_x = min(v.x for v in bb)
        max_x = max(v.x for v in bb)
        min_y = min(v.y for v in bb)
        max_y = max(v.y for v in bb)
        print(f"    Verts: {len(obj.data.vertices)}, Polys: {len(obj.data.polygons)}")
        print(f"    Bounds: X=[{min_x:.3f}, {max_x:.3f}] Y=[{min_y:.3f}, {max_y:.3f}] Z=[{min_z:.3f}, {max_z:.3f}]")
