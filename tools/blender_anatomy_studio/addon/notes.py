"""Vietnamese anatomical notes and clinical safety disclaimers for Blender Anatomical Studio.
Preserves strict safety invariants and links with Knowledge Vault P20.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

RELEASE_SCOPE = "ENGINEERING_RESEARCH_ONLY"
CLINICAL_VALIDATION = "NOT_ESTABLISHED"
CLINICAL_DEPTH_GUIDANCE_ALLOWED = False

DEFAULT_SAFETY_BANNER = """# BÁO CÁO GHI CHÚ GIẢI PHẪU VÀ HUYỆT HỌC — MSK-THERAPY-OS
> [!WARNING]
> **PHẠM VI NGHIÊN CỨU KỸ THUẬT (ENGINEERING_RESEARCH_ONLY)**
> Dữ liệu và hình học trong tài liệu này chỉ phục vụ mục đích nghiên cứu, mô phỏng cơ sinh học và giáo dục giải phẫu.
> **KHÔNG PHẢI CHỈ ĐỊNH ĐIỀU TRỊ HOẶC CHẨN ĐOÁN LÂM SÀNG.**
> Trạng thái kiểm định chuyên môn: `NOT_ESTABLISHED`. Mọi tọa độ huyệt mang nhãn `USER_ANNOTATED_UNVERIFIED`.
"""

def generate_markdown_note(
    title: str,
    structure_or_channel: str,
    author: str,
    vietnamese_content: str,
    annotations: List[Dict[str, Any]],
    waypoints: Optional[List[List[float]]] = None,
    citations: Optional[List[str]] = None
) -> str:
    """Generate Knowledge Vault compatible Markdown note with frontmatter and safety banners."""
    now_iso = datetime.now(timezone.utc).isoformat()
    cites = citations or ["GB/T 12346-2021", "BodyParts3D 4.0 DBCLS"]
    cites_str = "\n".join(f"- {c}" for c in cites)

    annot_rows = []
    for a in annotations:
        code = a.get("code", "N/A")
        name = a.get("name", "N/A")
        side = a.get("side", "N/A")
        status = a.get("review_status", "USER_ANNOTATED_UNVERIFIED")
        pos = a.get("global_position", [0, 0, 0])
        pos_str = f"({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})"
        annot_rows.append(f"| `{code}` | {name} | {side} | `{pos_str}` | `{status}` |")

    table_body = "\n".join(annot_rows) if annot_rows else "| Không có điểm đánh dấu | - | - | - | - |"

    waypoints_section = ""
    if waypoints:
        wp_rows = [f"1. Tọa độ: `({wp[0]:.4f}, {wp[1]:.4f}, {wp[2]:.4f})`" for wp in waypoints]
        waypoints_section = f"### Danh sách Waypoint Tuyến Kinh ({len(waypoints)} điểm):\n" + "\n".join(wp_rows) + "\n"

    md = f"""---
title: "{title}"
scope: "{RELEASE_SCOPE}"
clinical_validation: "{CLINICAL_VALIDATION}"
clinical_depth_guidance_allowed: {str(CLINICAL_DEPTH_GUIDANCE_ALLOWED).lower()}
target_structure: "{structure_or_channel}"
author: "{author}"
created_at: "{now_iso}"
review_status: "USER_ANNOTATED_UNVERIFIED"
---

{DEFAULT_SAFETY_BANNER}

## 1. Thông tin chung
- **Chủ đề / Tuyến:** {structure_or_channel}
- **Tác giả lập bản:** {author}
- **Thời gian lập:** {now_iso}
- **Trạng thái phê duyệt y học:** `CHƯA PHÊ DUYỆT (EXPERT_REVIEW_PENDING)`

## 2. Nội dung thuyết minh giải phẫu
{vietnamese_content}

## 3. Danh sách Mốc / Huyệt đã đánh dấu
| Mã huyệt | Tên huyệt | Bên | Tọa độ không gian (m) | Trạng thái thẩm định |
|---|---|---|---|---|
{table_body}

{waypoints_section}

## 4. Tài liệu dẫn chiếu (Citations)
{cites_str}
"""
    return md

try:
    import bpy

    class MSK_OT_ExportMarkdownNote(bpy.types.Operator):
        """Export scene annotations as Knowledge Vault Markdown note"""
        bl_idname = "msk.export_markdown_note"
        bl_label = "Export Markdown Note"
        bl_options = {'REGISTER'}

        filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="//MSK_Anatomy_Studio_Note.md")
        title: bpy.props.StringProperty(name="Title", default="Ghi chú Giải phẫu Cánh tay và Tuyến Kinh Thủ Dương Minh Đại Trường")
        author: bpy.props.StringProperty(name="Author", default="Kỹ sư Nghiên cứu MSK-Therapy-OS")
        notes_text: bpy.props.StringProperty(name="Notes Text", default="Đánh dấu giải phẫu bờ quay xương bàn tay II và huyệt Hợp Cốc LI4 phục vụ mô phỏng động học.")

        def execute(self, context):
            from .annotations import serialize_annotation
            from .meridian_curves import get_meridian_waypoints

            # Collect annotations
            annots = []
            for obj in context.scene.objects:
                if "msk_annotation_id" in obj:
                    annots.append(serialize_annotation(obj))

            # Collect curve waypoints
            waypoints = []
            for obj in context.scene.objects:
                if "msk_channel_code" in obj:
                    waypoints = get_meridian_waypoints(obj)
                    break

            md_content = generate_markdown_note(
                title=self.title,
                structure_or_channel="Chi Trên (Right Upper Extremity)",
                author=self.author,
                vietnamese_content=self.notes_text,
                annotations=annots,
                waypoints=waypoints
            )

            path = bpy.path.abspath(self.filepath)
            with open(path, "w", encoding="utf-8") as f:
                f.write(md_content)

            self.report({'INFO'}, f"Saved Markdown note to {path}")
            return {'FINISHED'}

    CLASSES = [MSK_OT_ExportMarkdownNote]
except ImportError:
    CLASSES = []

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
