"""Project Persistence Manager for MSK-Therapy-OS V1.0.
Handles atomic saving and loading of portable .mskproj project manifests,
schema validation, and Markdown report generation.
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProjectManager:
    """Manages saving, loading, and exporting .mskproj project manifests."""

    SCHEMA_VERSION = "1.0.0"

    @classmethod
    def create_default_project(cls, project_id: str = "project_default") -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        return {
            "project_id": project_id,
            "schema_version": cls.SCHEMA_VERSION,
            "created_at": now_iso,
            "updated_at": now_iso,
            "body_parameters": {
                "height_scale": 1.00,
                "right_arm_length_ratio": 1.00,
                "right_arm_circumference_visual": 1.00,
                "preset_name": "baseline",
                "morph_version": 1
            },
            "current_pose": {
                "frame_index": 0,
                "shoulder_elevation_deg": 39.49,
                "elbow_flexion_deg": 24.59
            },
            "surface_anchors": {
                "LI4": {
                    "code": "LI4",
                    "target_mesh_name": "Metacarpal_2_R",
                    "local_coordinates": [-0.280, 0.835, 0.035],
                    "status": "VALID_SURFACE_ANCHOR"
                },
                "LI14": {
                    "code": "LI14",
                    "target_mesh_name": "Humerus_R",
                    "local_coordinates": [-0.210, 1.250, -0.015],
                    "status": "VALID_SURFACE_ANCHOR"
                },
                "LI15": {
                    "code": "LI15",
                    "target_mesh_name": "Scapula_R",
                    "local_coordinates": [-0.160, 1.410, -0.020],
                    "status": "VALID_SURFACE_ANCHOR"
                }
            },
            "manual_adjustments": [],
            "knowledge_references": ["LI4", "LI14", "LI15"],
            "notes": "MSK-Therapy-OS V1.0 Research Project Session",
            "scope": "ENGINEERING_RESEARCH_ONLY"
        }

    @classmethod
    def save_project(cls, filepath: Path, project_data: Dict[str, Any]) -> str:
        """Atomically save project to file."""
        if not str(filepath).endswith(".mskproj") and not str(filepath).endswith(".json"):
            filepath = filepath.with_suffix(".mskproj")

        filepath.parent.mkdir(parents=True, exist_ok=True)
        project_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Atomic write via temp file
        temp_file = tempfile.NamedTemporaryFile("w", dir=filepath.parent, delete=False, encoding="utf-8")
        try:
            json.dump(project_data, temp_file, indent=2, ensure_ascii=False)
            temp_file.flush()
            temp_file.close()
            Path(temp_file.name).replace(filepath)
        except Exception as e:
            if Path(temp_file.name).exists():
                Path(temp_file.name).unlink()
            raise e

        return str(filepath)

    @classmethod
    def load_project(cls, filepath: Path) -> Dict[str, Any]:
        """Load and validate project file."""
        if not filepath.exists():
            raise FileNotFoundError(f"Project file not found: {filepath}")

        data = json.loads(filepath.read_text(encoding="utf-8"))
        if "schema_version" not in data or "body_parameters" not in data:
            raise ValueError(f"Corrupted or invalid .mskproj manifest: {filepath}")
        return data

    @classmethod
    def export_markdown_report(cls, project_data: Dict[str, Any]) -> str:
        """Export comprehensive Markdown research report from project data."""
        bp = project_data.get("body_parameters", {})
        pose = project_data.get("current_pose", {})
        anchors = project_data.get("surface_anchors", {})

        md = []
        md.append(f"# MSK-Therapy-OS V1.0 — Báo Cáo Phiên Nghiên Cứu Hình Thể & Động Học: {project_data.get('project_id', 'V1_PROJECT')}")
        md.append(f"**Thời gian cập nhật:** {project_data.get('updated_at', '')}")
        md.append(f"**Phạm vi:** `ENGINEERING_RESEARCH_ONLY` | `CLINICAL_VALIDATION = NOT_ESTABLISHED`\n")

        md.append("## 1. NGUỒN DỮ LIỆU & BẢN QUYỀN (DATA PROVENANCE)")
        md.append("- **Mô hình giải phẫu 3D:** BodyParts3D Release 4.0 (DBCLS Japan)")
        md.append("- **Giấy phép hình học:** Creative Commons Attribution 4.0 International (CC BY 4.0)")
        md.append("- **Chuỗi chuyển động:** MediaPipe Pose Landmark Video Ingestion (100 frames)")
        md.append("- **Cơ chế nhịp vận động:** Inman 2:1 Scapulohumeral Rhythm Constraint\n")

        md.append("## 2. THAM SỐ HÌNH THỂ (PARAMETRIC BODY)")
        md.append(f"- **Hình thể thiết lập:** `{bp.get('preset_name', 'baseline')}`")
        md.append(f"- **Tỷ lệ chiều cao (Height Scale):** {bp.get('height_scale', 1.0):.2f}")
        md.append(f"- **Tỷ lệ chiều dài cánh tay (Arm Length Ratio):** {bp.get('right_arm_length_ratio', 1.0):.2f}")
        md.append(f"- **Tỷ lệ chu vi cơ bắp (Circumference Visual):** {bp.get('right_arm_circumference_visual', 1.0):.2f}\n")

        md.append("## 3. TRẠNG THÁI TƯ THẾ ĐỘNG HỌC (CURRENT POSE)")
        md.append(f"- **Chỉ số Frame:** {pose.get('frame_index', 0)} / 99")
        md.append(f"- **Góc nâng vai (Thoracohumeral Elevation):** {pose.get('shoulder_elevation_deg', 0.0):.1f}°")
        md.append(f"- **Góc gập khuỷu (Elbow Flexion):** {pose.get('elbow_flexion_deg', 0.0):.1f}°\n")

        md.append("## 4. MỐC HUYỆT BỀ MẶT (DYNAMIC ANCHORS)")
        for code, a in anchors.items():
            coords = a.get("local_coordinates", [0, 0, 0])
            md.append(f"- **{code}:** Gắn trên `{a.get('target_mesh_name', '-')}` | Tọa độ: `({coords[0]:.4f}, {coords[1]:.4f}, {coords[2]:.4f})` m | Trạng thái: `EXPERT_REVIEW_PENDING`")

        md.append("\n## 5. GHI CHÚ VÀ KHUYẾN CÁO AN TOÀN")
        md.append(f"{project_data.get('notes', 'Không có ghi chú thêm.')}")
        md.append("> [!WARNING] Toàn bộ dữ liệu chỉ phục vụ nghiên cứu giải phẫu tính toán số, không thay thế chẩn đoán y tế.")

        return "\n".join(md)
