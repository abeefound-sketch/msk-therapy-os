import sys
import bpy

def inspect(path):
    print("=" * 60)
    print("INSPECTING:", path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=path)
    except Exception as e:
        print("Failed to import:", e)
        return
    
    print("OBJECTS:")
    for obj in bpy.data.objects:
        parent_name = obj.parent.name if obj.parent else "None"
        print(f"  {obj.name} (type={obj.type}, parent={parent_name})")
        if obj.type == 'ARMATURE':
            print(f"    Bones count: {len(obj.data.bones)}")
            for b in obj.data.bones[:15]:
                print(f"      bone: {b.name}")
        if obj.type == 'MESH':
            print(f"    Verts: {len(obj.data.vertices)}, Polys: {len(obj.data.polygons)}")
            print(f"    Vertex groups ({len(obj.vertex_groups)}): {[vg.name for vg in obj.vertex_groups[:10]]}")
            print(f"    Modifiers: {[(m.name, m.type) for m in obj.modifiers]}")
            if obj.data.shape_keys:
                print(f"    Shape keys ({len(obj.data.shape_keys.key_blocks)}): {[k.name for k in obj.data.shape_keys.key_blocks[:10]]}")

if __name__ == "__main__":
    if "--" in sys.argv:
        files = sys.argv[sys.argv.index("--") + 1:]
    else:
        files = sys.argv[1:]
    for p in files:
        if p and not p.startswith("-"):
            inspect(p)
