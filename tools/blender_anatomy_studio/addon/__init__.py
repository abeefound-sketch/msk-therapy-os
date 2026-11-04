bl_info = {
    "name": "MSK Anatomical Studio",
    "author": "MSK-Therapy-OS",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > MSK Studio",
    "description": "Anatomical authoring, layers, landmarks, acupuncture curves, and motion rig",
    "warning": "ENGINEERING_RESEARCH_ONLY - Not clinical advice",
    "doc_url": "https://github.com/msk-therapy-os",
    "category": "3D View",
}

try:
    import bpy
    HAS_BPY = True
except ImportError:
    bpy = None
    HAS_BPY = False

from . import layers
from . import annotations
from . import meridian_curves
from . import notes
from . import rig
from . import import_export
from . import rig_binding_adapter
from . import surface_anchor_registry

if HAS_BPY:
    class MSK_PT_StudioMainPanel(bpy.types.Panel):
        """MSK Anatomical Studio Main Sidebar Panel"""
        bl_label = "MSK Anatomical Studio"
        bl_idname = "MSK_PT_studio_main"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = 'MSK Studio'

        def draw(self, context):
            layout = self.layout

            # Safety Banner
            box = layout.box()
            box.label(text="ENGINEERING_RESEARCH_ONLY", icon='ERROR')
            box.label(text="Status: USER_ANNOTATED_UNVERIFIED")

            # 1. Anatomical Layers
            box_layer = layout.box()
            box_layer.label(text="1. Anatomical Layers", icon='OUTLINER_OB_MESH')
            row = box_layer.row(align=True)
            op_bone = row.operator("msk.toggle_layer", text="Bones")
            op_bone.layer_name = "BONE"
            op_musc = row.operator("msk.toggle_layer", text="Muscles")
            op_musc.layer_name = "MUSCLE"

            row2 = box_layer.row(align=True)
            op_org = row2.operator("msk.toggle_layer", text="Organs")
            op_org.layer_name = "ORGAN"
            op_skin = row2.operator("msk.toggle_layer", text="Skin")
            op_skin.layer_name = "SKIN"

            row3 = box_layer.row()
            op_iso = row3.operator("msk.isolate_layer", text="Isolate Bones")
            op_iso.layer_name = "BONE"
            row3.operator("msk.classify_meshes", text="Auto-Classify")

            # 2. Acupoints & Markers
            box_annot = layout.box()
            box_annot.label(text="2. Acupoint & Landmark Markers", icon='EMPTY_SINGLE_ARROW')
            box_annot.operator("msk.add_acupoint_marker", text="Place Acupoint Marker", icon='ADD')

            # 3. Meridian Curves
            box_curve = layout.box()
            box_curve.label(text="3. Meridian Curve (>=4 waypoints)", icon='CURVE_PATH')
            row_c = box_curve.row(align=True)
            row_c.operator("msk.add_meridian_waypoint", text="Add Waypoint", icon='PLUS')
            row_c.operator("msk.undo_meridian_waypoint", text="Undo Point", icon='LOOP_BACK')

            # 4. Upper Limb Rig & IK
            box_rig = layout.box()
            box_rig.label(text="4. Armature & IK Constraints", icon='ARMATURE_DATA')
            box_rig.operator("msk.build_arm_rig", text="Build Arm Rig (FK/IK)", icon='BONE_DATA')

            # 5. Export & Knowledge Vault
            box_io = layout.box()
            box_io.label(text="5. Studio Package & Notes", icon='EXPORT')
            box_io.operator("msk.export_package", text="Export Studio Package", icon='PACKAGE')
            box_io.operator("msk.export_markdown_note", text="Export Markdown Note", icon='FILE_TEXT')

    classes = [
        MSK_PT_StudioMainPanel
    ]
else:
    classes = []

modules = [
    layers,
    annotations,
    meridian_curves,
    notes,
    rig,
    import_export
]

def register():
    if not HAS_BPY:
        return
    for m in modules:
        m.register()
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    if not HAS_BPY:
        return
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    for m in reversed(modules):
        m.unregister()

if __name__ == "__main__":
    register()
