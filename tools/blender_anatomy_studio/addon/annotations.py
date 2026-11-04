"""Acupoint and anatomical landmark annotation system for Blender.
Enforces surface binding, local coordinates, and explicit review provenance.
"""
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

def compute_mesh_hash_from_data(vertices: List[Tuple[float, float, float]], faces: List[Tuple[int, ...]]) -> str:
    """Compute deterministic SHA256 from raw vertex positions and face topology."""
    hasher = hashlib.sha256()
    for v in vertices:
        hasher.update(f"{v[0]:.6f},{v[1]:.6f},{v[2]:.6f};".encode("utf-8"))
    for f in faces:
        hasher.update(f"{','.join(map(str, f))};".encode("utf-8"))
    return hasher.hexdigest()

try:
    import bpy
    import mathutils

    def get_object_mesh_hash(obj: bpy.types.Object) -> str:
        """Get or compute cached SHA256 of an object mesh."""
        if "msk_mesh_hash" in obj:
            return obj["msk_mesh_hash"]
        if obj.type != 'MESH' or not obj.data:
            return "0" * 64
        mesh = obj.data
        verts = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]
        faces = [tuple(p.vertices) for p in mesh.polygons]
        mhash = compute_mesh_hash_from_data(verts, faces)
        obj["msk_mesh_hash"] = mhash
        return mhash

    def create_annotation_marker(
        context: bpy.types.Context,
        target_obj: bpy.types.Object,
        world_pos: mathutils.Vector,
        name: str,
        code: str,
        side: str = "RIGHT",
        annotation_type: str = "ACUPOINT",
        notes: str = "",
        uncertainty_mm: float = 5.0
    ) -> bpy.types.Object:
        """Create a visual marker anchored to target mesh surface."""
        # Ensure collection exists
        col_name = "MSK_Annotations"
        if col_name not in bpy.data.collections:
            annot_col = bpy.data.collections.new(col_name)
            context.scene.collection.children.link(annot_col)
        else:
            annot_col = bpy.data.collections[col_name]

        # Calculate local position and normal relative to target object
        mat_inv = target_obj.matrix_world.inverted()
        local_pos = mat_inv @ world_pos

        # Find closest point on mesh surface
        res, closest_point, normal, face_idx = target_obj.closest_point_on_mesh(local_pos)
        if not res:
            closest_point = local_pos
            normal = mathutils.Vector((0.0, 0.0, 1.0))
            face_idx = 0
        corrected_world_pos = target_obj.matrix_world @ closest_point

        # Create small visual sphere marker
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.008, # 8mm radius in meters
            location=corrected_world_pos
        )
        marker = context.active_object
        marker.name = f"Marker_{code}_{side}"

        # Assign distinctive material
        mat_name = f"MSK_Mat_Marker_{annotation_type}"
        if mat_name not in bpy.data.materials:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            principled = mat.node_tree.nodes.get("Principled BSDF")
            if principled:
                if annotation_type == "ACUPOINT":
                    principled.inputs[0].default_value = (0.95, 0.2, 0.1, 1.0) # Bright red/orange
                else:
                    principled.inputs[0].default_value = (0.1, 0.8, 0.3, 1.0) # Green for landmarks
            marker.data.materials.append(mat)
        else:
            marker.data.materials.append(bpy.data.materials[mat_name])

        # Link to collection and unlink from active
        if marker.name in context.scene.collection.objects:
            context.scene.collection.objects.unlink(marker)
        if marker.name not in annot_col.objects:
            annot_col.objects.link(marker)

        # Store metadata attributes adhering to schema
        annot_id = f"annot_{uuid.uuid4().hex[:12]}"
        mesh_hash = get_object_mesh_hash(target_obj)
        now_iso = datetime.now(timezone.utc).isoformat()

        marker["msk_annotation_id"] = annot_id
        marker["msk_type"] = annotation_type
        marker["msk_name"] = name
        marker["msk_code"] = code
        marker["msk_structure_id"] = target_obj.name
        marker["msk_mesh_hash"] = mesh_hash
        marker["msk_anchor_method"] = "local_coordinates"
        marker["msk_triangle_id"] = face_idx
        marker["msk_local_x"] = float(closest_point.x)
        marker["msk_local_y"] = float(closest_point.y)
        marker["msk_local_z"] = float(closest_point.z)
        marker["msk_normal_x"] = float(normal.x)
        marker["msk_normal_y"] = float(normal.y)
        marker["msk_normal_z"] = float(normal.z)
        marker["msk_side"] = side
        marker["msk_author"] = "User (Manual Annotation)"
        marker["msk_review_status"] = "USER_ANNOTATED_UNVERIFIED"
        marker["msk_uncertainty_mm"] = float(uncertainty_mm)
        marker["msk_notes"] = notes
        marker["msk_created_at"] = now_iso

        return marker

    def serialize_annotation(marker_obj: bpy.types.Object) -> Dict[str, Any]:
        """Convert a Blender marker object to schema-compliant dictionary."""
        loc = marker_obj.location
        return {
            "schema_version": "1.0.0",
            "annotation_id": marker_obj.get("msk_annotation_id", f"annot_{uuid.uuid4().hex[:12]}"),
            "type": marker_obj.get("msk_type", "ACUPOINT"),
            "name": marker_obj.get("msk_name", marker_obj.name),
            "code": marker_obj.get("msk_code", marker_obj.name),
            "structure_id": marker_obj.get("msk_structure_id", "UNKNOWN"),
            "mesh_hash": marker_obj.get("msk_mesh_hash", "0" * 64),
            "surface_anchor": {
                "method": marker_obj.get("msk_anchor_method", "local_coordinates"),
                "triangle_id": marker_obj.get("msk_triangle_id", None),
                "vertex_index": None,
                "barycentric_coords": None,
                "local_position": [
                    float(marker_obj.get("msk_local_x", 0.0)),
                    float(marker_obj.get("msk_local_y", 0.0)),
                    float(marker_obj.get("msk_local_z", 0.0))
                ],
                "normal": [
                    float(marker_obj.get("msk_normal_x", 0.0)),
                    float(marker_obj.get("msk_normal_y", 0.0)),
                    float(marker_obj.get("msk_normal_z", 1.0))
                ]
            },
            "global_position": [float(loc.x), float(loc.y), float(loc.z)],
            "transform_version": "1.0.0",
            "side": marker_obj.get("msk_side", "RIGHT"),
            "author": marker_obj.get("msk_author", "User (Manual Annotation)"),
            "source_claim_ids": ["CLAIM_MANUAL_ANCHOR"],
            "review_status": marker_obj.get("msk_review_status", "USER_ANNOTATED_UNVERIFIED"),
            "uncertainty_mm": float(marker_obj.get("msk_uncertainty_mm", 5.0)),
            "notes": marker_obj.get("msk_notes", ""),
            "created_at": marker_obj.get("msk_created_at", datetime.now(timezone.utc).isoformat())
        }

    class MSK_OT_AddAcupointMarker(bpy.types.Operator):
        """Add manual acupoint marker anchored to active mesh"""
        bl_idname = "msk.add_acupoint_marker"
        bl_label = "Add Acupoint Marker"
        bl_options = {'REGISTER', 'UNDO'}

        name: bpy.props.StringProperty(name="Name", default="Hợp Cốc (LI4)")
        code: bpy.props.StringProperty(name="Code", default="LI4")
        side: bpy.props.EnumProperty(
            name="Side",
            items=[
                ('RIGHT', "Right", "Phía Phải"),
                ('LEFT', "Left", "Phía Trái"),
                ('MIDLINE', "Midline", "Đường Giữa")
            ],
            default='RIGHT'
        )
        notes: bpy.props.StringProperty(name="Notes", default="Gắn trên bờ quay xương bàn tay II / cơ gian cốt mu tay I")
        uncertainty_mm: bpy.props.FloatProperty(name="Uncertainty (mm)", default=5.0, min=0.1)

        def execute(self, context):
            target = context.active_object
            if not target or target.type != 'MESH':
                self.report({'ERROR'}, "Please select a target anatomical MESH first.")
                return {'CANCELLED'}

            cursor_loc = context.scene.cursor.location
            marker = create_annotation_marker(
                context=context,
                target_obj=target,
                world_pos=cursor_loc,
                name=self.name,
                code=self.code,
                side=self.side,
                annotation_type="ACUPOINT",
                notes=self.notes,
                uncertainty_mm=self.uncertainty_mm
            )
            self.report({'INFO'}, f"Created marker: {marker.name} bound to {target.name}")
            return {'FINISHED'}

    CLASSES = [MSK_OT_AddAcupointMarker]
except ImportError:
    CLASSES = []

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
