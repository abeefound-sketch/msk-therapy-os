"""Anatomical layer management for Blender Anatomical Studio.
Handles classification, visibility toggling, and isolation for Bone, Muscle, Organ, and Skin.
"""
from typing import Dict, List, Set

ANATOMY_KEYWORDS = {
    "BONE": [
        "bone", "skeleton", "clavicle", "scapula", "humerus", "radius", "ulna",
        "femur", "tibia", "fibula", "vertebra", "cervical", "thoracic", "cranium",
        "skull", "patella", "pelvis", "ilium", "rib", "sternum", "sacrum", "carpal",
        "metacarpal", "tarsal", "metatarsal", "phalanx", "hand", "foot", "joint", "crest"
    ],
    "MUSCLE": [
        "muscle", "biceps", "triceps", "deltoid", "delt", "brachialis", "brachiorad",
        "pectoralis", "trapezius", "latissimus", "quadriceps", "gastrocnemius", "soleus",
        "tibialis", "adductors", "adductor", "gluteus", "rectus", "oblique", "interosseous",
        "levator", "subscap", "infraspinatus", "supraspinatus", "teres", "pronator", "supinator"
    ],
    "ORGAN": [
        "organ", "viscera", "heart", "lung", "liver", "stomach", "kidney", "spleen",
        "pancreas", "intestine", "bladder", "brain", "artery", "vein", "esophagus", "trachea"
    ],
    "SKIN": [
        "skin", "integument", "body", "character", "surface", "epidermis", "cutaneous"
    ]
}

def classify_object_name(name: str) -> str:
    """Deterministic classification of an object name into an anatomy class."""
    n = name.lower()
    # Check Organ first (vital organs often have specific names)
    for kw in ANATOMY_KEYWORDS["ORGAN"]:
        if kw in n:
            return "ORGAN"
    # Check Muscle next (muscles often contain muscle name)
    for kw in ANATOMY_KEYWORDS["MUSCLE"]:
        if kw in n:
            return "MUSCLE"
    # Check Skin next
    for kw in ANATOMY_KEYWORDS["SKIN"]:
        if kw in n:
            return "SKIN"
    # Check Bone
    for kw in ANATOMY_KEYWORDS["BONE"]:
        if kw in n:
            return "BONE"
    return "OTHER"

try:
    import bpy

    class MSK_OT_ToggleLayer(bpy.types.Operator):
        """Toggle visibility of an anatomical layer"""
        bl_idname = "msk.toggle_layer"
        bl_label = "Toggle Anatomical Layer"
        bl_options = {'REGISTER', 'UNDO'}

        layer_name: bpy.props.StringProperty(name="Layer", default="BONE")

        def execute(self, context):
            target = self.layer_name.upper()
            count = 0
            # Check current visibility of the first matching object
            sample_visible = True
            for obj in context.scene.objects:
                if obj.type == 'MESH':
                    cls = obj.get("msk_anatomy_class", classify_object_name(obj.name))
                    if cls == target:
                        sample_visible = not obj.hide_viewport
                        break

            new_hide = sample_visible
            for obj in context.scene.objects:
                if obj.type == 'MESH':
                    cls = obj.get("msk_anatomy_class", classify_object_name(obj.name))
                    if cls == target:
                        obj.hide_viewport = new_hide
                        obj.hide_render = new_hide
                        count += 1
            self.report({'INFO'}, f"Toggled {count} objects in layer {target} to {'hidden' if new_hide else 'visible'}")
            return {'FINISHED'}

    class MSK_OT_IsolateLayer(bpy.types.Operator):
        """Isolate a specific anatomical layer and hide others"""
        bl_idname = "msk.isolate_layer"
        bl_label = "Isolate Anatomical Layer"
        bl_options = {'REGISTER', 'UNDO'}

        layer_name: bpy.props.StringProperty(name="Layer", default="BONE")

        def execute(self, context):
            target = self.layer_name.upper()
            for obj in context.scene.objects:
                if obj.type == 'MESH':
                    cls = obj.get("msk_anatomy_class", classify_object_name(obj.name))
                    if cls == target:
                        obj.hide_viewport = False
                        obj.hide_render = False
                    else:
                        obj.hide_viewport = True
                        obj.hide_render = True
            self.report({'INFO'}, f"Isolated layer: {target}")
            return {'FINISHED'}

    class MSK_OT_ClassifyAllMeshes(bpy.types.Operator):
        """Classify and tag all mesh objects in the scene"""
        bl_idname = "msk.classify_meshes"
        bl_label = "Classify Scene Meshes"
        bl_options = {'REGISTER', 'UNDO'}

        def execute(self, context):
            counts = {"BONE": 0, "MUSCLE": 0, "ORGAN": 0, "SKIN": 0, "OTHER": 0}
            for obj in context.scene.objects:
                if obj.type == 'MESH':
                    cls = classify_object_name(obj.name)
                    obj["msk_anatomy_class"] = cls
                    counts[cls] += 1
            self.report({'INFO'}, f"Classified meshes: {counts}")
            return {'FINISHED'}

    CLASSES = [MSK_OT_ToggleLayer, MSK_OT_IsolateLayer, MSK_OT_ClassifyAllMeshes]
except ImportError:
    CLASSES = []

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
