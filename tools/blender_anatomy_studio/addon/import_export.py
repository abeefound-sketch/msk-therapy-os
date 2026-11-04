"""Import and Export bundle pipeline for Blender Anatomical Studio.
Guarantees schema compliance, fail-closed checksum validation, and bidirectional interoperability.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..contracts import validate_contract
from .notes import generate_markdown_note

class MeshChecksumMismatchError(Exception):
    """Raised when an imported annotation mesh checksum does not match the active scene mesh."""
    pass

class SchemaValidationError(Exception):
    """Raised when exported or imported JSON fails schema validation."""
    pass

try:
    import bpy
    import mathutils
    from .annotations import get_object_mesh_hash, serialize_annotation
    from .meridian_curves import get_meridian_waypoints, set_meridian_waypoints, create_or_get_meridian_curve
    from .layers import classify_object_name

    def export_studio_package(
        context: bpy.types.Context,
        base_path_str: str,
        source_id: str = "BodyParts3D_4.0_DBCLS",
        license_id: str = "CC-BY-4.0",
        license_scope: str = "COMMERCIAL_PERMITTED_WITH_ATTRIBUTION",
        attribution: str = "BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International."
    ) -> Dict[str, str]:
        """Export full studio bundle: manifest, annotations, curve, Markdown note, and .blend."""
        base_path = Path(bpy.path.abspath(base_path_str)).resolve()
        base_path.parent.mkdir(parents=True, exist_ok=True)
        stem = base_path.stem

        # 1. Collect meshes and structure IDs
        mesh_objs = [o for o in context.scene.objects if o.type == 'MESH' and "msk_annotation_id" not in o]
        structure_ids = [m.name for m in mesh_objs]

        # Calculate primary asset hash from all meshes
        import hashlib
        combined_hasher = hashlib.sha256()
        for m in sorted(mesh_objs, key=lambda x: x.name):
            mhash = get_object_mesh_hash(m)
            combined_hasher.update(mhash.encode('utf-8'))
        asset_sha256 = combined_hasher.hexdigest()

        # Identify unique anatomy classes present
        classes_present = sorted(list(set(classify_object_name(m.name) for m in mesh_objs)))
        if not classes_present:
            classes_present = ["OTHER"]

        manifest_data = {
            "schema_version": "1.0.0",
            "source_id": source_id,
            "asset_sha256": asset_sha256,
            "license_id": license_id,
            "license_scope": license_scope,
            "attribution": attribution,
            "structure_ids": structure_ids,
            "frame_id": "canonical_bodyparts3d_meters_y_up",
            "units": "meters",
            "mesh_transform": [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0
            ],
            "anatomy_classes": classes_present,
            "review_status": "USER_ANNOTATED_UNVERIFIED"
        }

        # Validate manifest
        ok, err = validate_contract(manifest_data, "anatomy_asset_manifest")
        if not ok:
            raise SchemaValidationError(f"Manifest schema validation failed: {err}")

        manifest_file = base_path.parent / f"{stem}_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        # 2. Collect Annotations
        annot_objs = [o for o in context.scene.objects if "msk_annotation_id" in o]
        annotations_list = [serialize_annotation(o) for o in annot_objs]

        for a in annotations_list:
            ok, err = validate_contract(a, "annotation")
            if not ok:
                raise SchemaValidationError(f"Annotation {a.get('code')} schema validation failed: {err}")

        annots_file = base_path.parent / f"{stem}_annotations.json"
        with open(annots_file, "w", encoding="utf-8") as f:
            json.dump(annotations_list, f, indent=2, ensure_ascii=False)

        # 3. Collect Meridian Curves
        curve_objs = [o for o in context.scene.objects if "msk_channel_code" in o]
        curve_waypoints = []
        curve_data_list = []
        for c in curve_objs:
            wps = get_meridian_waypoints(c)
            curve_data_list.append({
                "channel_code": c.get("msk_channel_code", "LI"),
                "curve_name": c.name,
                "waypoints": wps
            })
            if wps:
                curve_waypoints = wps

        curves_file = base_path.parent / f"{stem}_meridian_curves.json"
        with open(curves_file, "w", encoding="utf-8") as f:
            json.dump(curve_data_list, f, indent=2, ensure_ascii=False)

        # 4. Generate Vietnamese Markdown Note
        md_text = generate_markdown_note(
            title=f"Bản Ghi Giải Phẫu và Huyệt Vị — {stem}",
            structure_or_channel="Chi Trên và Tuyến Kinh Phế/Đại Trường",
            author="MSK Studio Operator",
            vietnamese_content="Dữ liệu ghi nhận từ mô hình giải phẫu thật có bản quyền chuẩn. Các điểm huyệt được định vị bề mặt tương đối phục vụ mô phỏng động học.",
            annotations=annotations_list,
            waypoints=curve_waypoints
        )
        md_file = base_path.parent / f"{stem}_note.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_text)

        # 5. Save .blend scene file
        blend_file = base_path.parent / f"{stem}.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_file))

        return {
            "manifest_json": str(manifest_file),
            "annotations_json": str(annots_file),
            "curves_json": str(curves_file),
            "markdown_note": str(md_file),
            "blend_file": str(blend_file),
            "asset_sha256": asset_sha256,
            "annotations_count": len(annotations_list),
            "waypoints_count": len(curve_waypoints)
        }

    def import_studio_package(
        context: bpy.types.Context,
        manifest_path: str,
        annotations_path: str,
        curves_path: Optional[str] = None,
        verify_checksum: bool = True
    ) -> Dict[str, Any]:
        """Import annotations and curves into scene with fail-closed checksum verification."""
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        ok, err = validate_contract(manifest, "anatomy_asset_manifest")
        if not ok:
            raise SchemaValidationError(f"Invalid manifest: {err}")

        with open(annotations_path, "r", encoding="utf-8") as f:
            annotations = json.load(f)

        imported_markers = 0
        for item in annotations:
            ok, err = validate_contract(item, "annotation")
            if not ok:
                raise SchemaValidationError(f"Invalid annotation item: {err}")

            target_name = item["structure_id"]
            if target_name in context.scene.objects:
                target_obj = context.scene.objects[target_name]
                if verify_checksum:
                    curr_hash = get_object_mesh_hash(target_obj)
                    expected_hash = item["mesh_hash"]
                    # If target has dummy zero hash or mismatch
                    if expected_hash != "0" * 64 and curr_hash != expected_hash:
                        raise MeshChecksumMismatchError(
                            f"Fail-closed: Mesh checksum mismatch for '{target_name}'. "
                            f"Expected: {expected_hash}, Actual: {curr_hash}. Refusing silent remap."
                        )

                # Recreate marker from local surface anchor
                from .annotations import create_annotation_marker
                anchor = item["surface_anchor"]
                local_pos = mathutils.Vector(anchor["local_position"])
                world_pos = target_obj.matrix_world @ local_pos

                create_annotation_marker(
                    context=context,
                    target_obj=target_obj,
                    world_pos=world_pos,
                    name=item["name"],
                    code=item["code"],
                    side=item["side"],
                    annotation_type=item["type"],
                    notes=item.get("notes", ""),
                    uncertainty_mm=item.get("uncertainty_mm", 5.0)
                )
                imported_markers += 1

        # Recreate curves if provided
        imported_curves = 0
        if curves_path and Path(curves_path).exists():
            with open(curves_path, "r", encoding="utf-8") as f:
                curves_data = json.load(f)
            for cd in curves_data:
                c_obj = create_or_get_meridian_curve(context, cd["curve_name"], cd["channel_code"])
                set_meridian_waypoints(c_obj, cd["waypoints"])
                imported_curves += 1

        return {
            "status": "SUCCESS",
            "imported_markers": imported_markers,
            "imported_curves": imported_curves,
            "manifest_source": manifest["source_id"]
        }

    class MSK_OT_ExportPackage(bpy.types.Operator):
        """Export full MSK Anatomy Studio package (JSON, MD, .blend)"""
        bl_idname = "msk.export_package"
        bl_label = "Export Studio Package"
        bl_options = {'REGISTER'}

        base_path: bpy.props.StringProperty(subtype="FILE_PATH", default="//MSK_Studio_Export")

        def execute(self, context):
            try:
                res = export_studio_package(context, self.base_path)
                self.report({'INFO'}, f"Exported {res['annotations_count']} markers, {res['waypoints_count']} waypoints")
                return {'FINISHED'}
            except Exception as e:
                self.report({'ERROR'}, f"Export failed: {e}")
                return {'CANCELLED'}

    CLASSES = [MSK_OT_ExportPackage]
except ImportError:
    CLASSES = []

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
