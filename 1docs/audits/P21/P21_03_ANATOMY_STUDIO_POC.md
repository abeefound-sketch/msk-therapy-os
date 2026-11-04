# MSK-Therapy-OS — Milestone P21 Audit
## P21_03: Blender Anatomical Studio PoC Architecture & Add-on Implementation

**Tài liệu ID:** `MSK-P21-AUD-003`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Cấu trúc Mô-đun của Công cụ Studio Offline

Hệ thống được tổ chức hoàn toàn tách biệt trong thư mục `tools/blender_anatomy_studio/`:

```text
tools/blender_anatomy_studio/
├── addon/
│   ├── __init__.py           # Đăng ký Panel "MSK Studio" trên Sidebar 3D Viewport
│   ├── layers.py             # Quản lý lớp giải phẫu (Bone, Muscle, Organ, Skin), ẩn/hiện, cô lập
│   ├── annotations.py        # Đánh dấu huyệt 3D, tính toán gắn kết bề mặt và mã băm SHA256
│   ├── meridian_curves.py    # Dựng đường cong kinh lạc 3D đa điểm, hỗ trợ Undo
│   ├── notes.py              # Quản lý ghi chú tiếng Việt và banner an toàn lâm sàng
│   ├── rig.py                # Xây dựng Armature cánh tay, IK solver và ràng buộc góc quay Kapandji
│   └── import_export.py      # Xuất/nhập trọn gói JSON schema, Markdown Knowledge Vault và .blend
├── contracts/
│   ├── __init__.py           # Bộ kiểm tra schema (hỗ trợ jsonschema và fallback standard library)
│   ├── anatomy_asset_manifest.schema.json
│   ├── annotation.schema.json
│   ├── joint_constraint.schema.json
│   ├── motion_sequence.schema.json
│   ├── pose_observation.schema.json
│   └── validation_report.schema.json
├── tests/
│   └── test_p21_blender_studio.py
├── headless_poc.py           # Pipeline tự động hóa chạy trực tiếp trong Blender headless
├── motion_bank.py            # Ngân hàng chuyển động và phân tích ràng buộc khớp
└── README.md
```

---

### 2. Chi tiết Triển khai Kỹ thuật

#### A. Gắn kết Bề mặt và Tính toàn vẹn Hình học (Surface Anchoring)
- Không lưu tọa độ global XYZ trôi dạt.
- Mỗi huyệt vị được gắn trực tiếp vào một cấu trúc giải phẫu đích (`target_obj`).
- Hệ thống tính toán tọa độ cục bộ `local_position` thông qua ma trận nghịch đảo `matrix_world.inverted()`, tìm điểm gần nhất trên bề mặt lưới `closest_point_on_mesh`, ghi nhận chỉ số mặt phẳng tam giác `triangle_id` và vector pháp tuyến bề mặt `normal`.
- Ghi nhận mã băm SHA-256 của lưới mesh để ngăn chặn việc âm thầm dịch chuyển khi mô hình thay đổi.

#### B. Trạng thái Thẩm định Mặc định (Default Review Status)
Mọi điểm đánh dấu mới được gán mặc định là:
$$\text{review\_status} = \mathbf{USER\_ANNOTATED\_UNVERIFIED}$$
Tuyệt đối cấm tự ý gán nhãn `ANATOMICAL_VERIFIED` hoặc `CLINICAL_APPROVED`.

#### C. Đường kinh Đa điểm và Hoàn tác (Meridian Curves & Undo)
- Sử dụng đối tượng `CURVE` 3D trong Blender với vật liệu ánh sáng chuyên dụng.
- Lưu trữ danh sách waypoint chính xác (tối thiểu 4 waypoint theo yêu cầu P21).
- Hàm `pop_meridian_waypoint()` cho phép hoàn tác xóa điểm vừa thêm ngay lập tức.

#### D. Ràng buộc Khớp Khớp cánh tay (Kinematic Armature & IK)
- Dựng khung xương 4 khớp: `clavicle.R` $\to$ `upper_arm.R` $\to$ `forearm.R` $\to$ `hand.R`.
- Tích hợp điều khiển IK 2-link qua `wrist_IK.R` và `elbow_pole.R`.
- Áp dụng ràng buộc xoay `LIMIT_ROTATION` trên khớp khuỷu theo y văn giải phẫu học cơ sinh học Kapandji (2007):
  * Góc gập khuỷu (Flexion): $[0^\circ, 145^\circ]$.
  * Góc xoay ngang/trục: cố định $0^\circ$ theo mô hình bản lề một trục (hinge model).
