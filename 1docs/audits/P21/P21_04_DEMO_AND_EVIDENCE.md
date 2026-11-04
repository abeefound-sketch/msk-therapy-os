# MSK-Therapy-OS — Milestone P21 Audit
## P21_04: Demo Evidence, Artifacts Registry & User Operating Guide

**Tài liệu ID:** `MSK-P21-AUD-004`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Bằng chứng Trực quan Đã Kết Xuất (Visual Evidence)

Các hình ảnh kết xuất thực tế từ Blender 3.6.5 LTS (độ phân giải 960×720, 64 samples) được lưu trữ tại:

1. **Tổng quan Không gian Anatomical Studio PoC:**  
   [01_blender_36_anatomical_studio_poc.png](file:///D:/5Projects/msk-therapy-os/1docs/audits/P21/screenshots/01_blender_36_anatomical_studio_poc.png)  
   *Mô tả:* Hiển thị mô hình khung xương chi trên (`shoulder_skeleton.glb`), 3 điểm đánh dấu huyệt vị bề mặt (`Marker_LI4_RIGHT`, `Marker_ST36_RIGHT`, `Marker_KI3_RIGHT`), đường cong kinh lạc 3D màu vàng óng chứa 4 waypoint, và hệ thống khung Armature cánh tay.

2. **Khung Xương và Tư Thế Cánh Tay Gập Khớp Khuỷu (Flexed Pose at Frame 30):**  
   [02_blender_arm_rig_flexed_pose.png](file:///D:/5Projects/msk-therapy-os/1docs/audits/P21/screenshots/02_blender_arm_rig_flexed_pose.png)  
   *Mô tả:* Minh chứng trạng thái kích hoạt ràng buộc IK và góc gập khuỷu được điều khiển theo keyframe động học, các mốc huyệt bám vững chắc theo cấu trúc xương.

---

### 2. Danh mục Tệp tin Artifacts Đã Xuất Bản (Exported Artifacts)

Tất cả các tệp tin dưới đây đã được kiểm tra tính hợp lệ bằng các bộ JSON Schema chuẩn:

| Tệp tin | Định dạng | Dung lượng | Mã băm SHA-256 | Vai trò & Tiêu chuẩn |
|---|---|---|---|---|
| `p21_studio_export_manifest.json` | JSON | 845 B | `365e109f0868f08f886f4a5690dfa1f8bb2e5f524738a0f9b6c86a11e114cf78` | Khớp `anatomy_asset_manifest.schema.json` |
| `p21_studio_export_annotations.json` | JSON | 1.8 KB | `82f254b0c03dc875952dfa2ee4711822851ea89cf29656821d3f9e29a39ca5d0` | Khớp `annotation.schema.json` (3 markers) |
| `p21_studio_export_meridian_curves.json` | JSON | 382 B | `704ca98108c4cb71c4c1143896dfa42bf4ae85c96b797828c4ff8046bcf319a2` | Tuyến kinh 4 waypoint (mã LI) |
| `p21_studio_export_note.md` | Markdown | 1.9 KB | `9f5bca9c560e9f1a0ea4c16a24eb5bc8784d720b6045d4fec033dfd59702ba69` | Thuyết minh tiếng Việt chuẩn Knowledge Vault P20 |
| `p21_studio_export.blend` | Nhị phân Blender | 2,202,700 B (~2.2 MB) | `265a882a1727787f1c1f4e3c66f778d9102434586d1a9ee08316773a4b64f9cb` | File cảnh hoàn chỉnh mở lại được 100% |

---

### 3. Hướng dẫn Vận hành Demo Trực tiếp (Operator Guide)

Để mở trực tiếp bản demo trong giao diện đồ họa Blender 3.6:

```powershell
# Chạy Blender và mở trực tiếp file cảnh đã lưu
& "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe" "D:\5Projects\msk-therapy-os\1docs\audits\P21\evidence\p21_studio_export.blend"
```

Khi giao diện Blender hiện ra:
1. Nhấn phím `Spacebar` để xem chuyển động cánh tay gập/duỗi từ Frame 1 đến Frame 40.
2. Bấm phím `N` trên bàn phím để mở thanh Sidebar, chọn tab `MSK Studio` để thử nghiệm các nút:
   - `Bones` / `Muscles` / `Organs` / `Skin` (Ẩn/Hiện lớp giải phẫu).
   - `Place Acupoint Marker` (Đặt huyệt tại con trỏ 3D).
   - `Add Waypoint` / `Undo Point` (Chỉnh sửa đường kinh).
   - `Build Arm Rig (FK/IK)` (Dựng lại rig).
   - `Export Studio Package` (Xuất gói dữ liệu mới).
