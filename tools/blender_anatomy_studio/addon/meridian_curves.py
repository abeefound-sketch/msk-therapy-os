"""Acupuncture meridian curve system for Blender Anatomical Studio.
Allows interactive polyline curve generation, waypoint adding/undo, and trajectory serialization.
"""
from typing import Any, Dict, List, Optional, Tuple

try:
    import bpy
    import mathutils

    def create_or_get_meridian_curve(
        context: bpy.types.Context,
        curve_name: str = "Meridian_Large_Intestine_LI",
        channel_code: str = "LI"
    ) -> bpy.types.Object:
        """Create or retrieve a 3D curve object for meridian pathway."""
        col_name = "MSK_Meridians"
        if col_name not in bpy.data.collections:
            col = bpy.data.collections.new(col_name)
            context.scene.collection.children.link(col)
        else:
            col = bpy.data.collections[col_name]

        if curve_name in bpy.data.objects:
            return bpy.data.objects[curve_name]

        curve_data = bpy.data.curves.new(name=curve_name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.003  # 3mm pipe radius
        curve_data.bevel_resolution = 4

        curve_obj = bpy.data.objects.new(name=curve_name, object_data=curve_data)
        col.objects.link(curve_obj)

        # Set material
        mat_name = f"MSK_Mat_Meridian_{channel_code}"
        if mat_name not in bpy.data.materials:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            principled = mat.node_tree.nodes.get("Principled BSDF")
            if principled:
                principled.inputs[0].default_value = (1.0, 0.8, 0.1, 1.0)  # Gold/Yellow
            curve_obj.data.materials.append(mat)
        else:
            curve_obj.data.materials.append(bpy.data.materials[mat_name])

        curve_obj["msk_channel_code"] = channel_code
        curve_obj["msk_meridian_name"] = curve_name
        curve_obj["msk_waypoint_count"] = 0
        return curve_obj

    def set_meridian_waypoints(
        curve_obj: bpy.types.Object,
        waypoints: List[Tuple[float, float, float]]
    ):
        """Set points of the spline to given waypoints."""
        curve_data = curve_obj.data
        curve_data.splines.clear()
        if not waypoints:
            return

        spline = curve_data.splines.new(type='POLY')
        spline.points.add(len(waypoints) - 1)
        for i, pt in enumerate(waypoints):
            spline.points[i].co = (pt[0], pt[1], pt[2], 1.0)

        curve_obj["msk_waypoint_count"] = len(waypoints)

    def append_meridian_waypoint(
        curve_obj: bpy.types.Object,
        waypoint: Tuple[float, float, float]
    ):
        """Append a single waypoint to the meridian curve."""
        curve_data = curve_obj.data
        if not curve_data.splines:
            set_meridian_waypoints(curve_obj, [waypoint])
            return

        spline = curve_data.splines[0]
        pts = [(p.co.x, p.co.y, p.co.z) for p in spline.points]
        pts.append(waypoint)
        set_meridian_waypoints(curve_obj, pts)

    def pop_meridian_waypoint(curve_obj: bpy.types.Object) -> bool:
        """Remove last waypoint (Undo) from the curve."""
        curve_data = curve_obj.data
        if not curve_data.splines:
            return False
        spline = curve_data.splines[0]
        pts = [(p.co.x, p.co.y, p.co.z) for p in spline.points]
        if not pts:
            return False
        pts.pop()
        set_meridian_waypoints(curve_obj, pts)
        return True

    def get_meridian_waypoints(curve_obj: bpy.types.Object) -> List[List[float]]:
        """Retrieve waypoints from curve."""
        curve_data = curve_obj.data
        if not curve_data.splines:
            return []
        spline = curve_data.splines[0]
        return [[float(p.co.x), float(p.co.y), float(p.co.z)] for p in spline.points]

    def update_meridian_curve_from_anchors(
        curve_obj: bpy.types.Object,
        anchors: List[Dict[str, Any]],
        depsgraph: Optional[bpy.types.Depsgraph] = None
    ) -> List[Tuple[float, float, float]]:
        """Dynamically update curve spline points from parented anatomical anchors.
        Each anchor is a dict: {'parent_obj': Object, 'local_pos': (x,y,z), 'code': str}.
        Evaluates world coordinates through dependency graph to prevent frame drift.
        """
        world_pts = []
        for anc in anchors:
            parent_obj = anc["parent_obj"]
            loc_pos = mathutils.Vector(anc["local_pos"])
            if depsgraph:
                eval_parent = parent_obj.evaluated_get(depsgraph)
                w_pos = eval_parent.matrix_world @ loc_pos
            else:
                w_pos = parent_obj.matrix_world @ loc_pos
            world_pts.append((float(w_pos.x), float(w_pos.y), float(w_pos.z)))

        set_meridian_waypoints(curve_obj, world_pts)
        return world_pts

    class MSK_OT_AddMeridianWaypoint(bpy.types.Operator):
        """Add waypoint to active meridian curve at 3D Cursor"""
        bl_idname = "msk.add_meridian_waypoint"
        bl_label = "Add Meridian Waypoint"
        bl_options = {'REGISTER', 'UNDO'}

        channel_code: bpy.props.StringProperty(name="Channel Code", default="LI")
        curve_name: bpy.props.StringProperty(name="Curve Name", default="Meridian_Large_Intestine_LI")

        def execute(self, context):
            curve_obj = create_or_get_meridian_curve(context, self.curve_name, self.channel_code)
            cursor_loc = context.scene.cursor.location
            append_meridian_waypoint(curve_obj, (cursor_loc.x, cursor_loc.y, cursor_loc.z))
            count = curve_obj.get("msk_waypoint_count", 0)
            self.report({'INFO'}, f"Added waypoint #{count} to {curve_obj.name}")
            return {'FINISHED'}

    class MSK_OT_UndoMeridianWaypoint(bpy.types.Operator):
        """Undo last waypoint from active meridian curve"""
        bl_idname = "msk.undo_meridian_waypoint"
        bl_label = "Undo Last Waypoint"
        bl_options = {'REGISTER', 'UNDO'}

        curve_name: bpy.props.StringProperty(name="Curve Name", default="Meridian_Large_Intestine_LI")

        def execute(self, context):
            if self.curve_name in bpy.data.objects:
                curve_obj = bpy.data.objects[self.curve_name]
                ok = pop_meridian_waypoint(curve_obj)
                if ok:
                    count = curve_obj.get("msk_waypoint_count", 0)
                    self.report({'INFO'}, f"Removed last waypoint. Remaining: {count}")
                    return {'FINISHED'}
            self.report({'WARNING'}, "No waypoints to undo")
            return {'CANCELLED'}

    CLASSES = [MSK_OT_AddMeridianWaypoint, MSK_OT_UndoMeridianWaypoint]
except ImportError:
    CLASSES = []

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
