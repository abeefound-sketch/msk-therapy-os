# MSK-Therapy-OS — Milestone P21 Coordinate & Mesh Contract
## P21_04: Coordinate Frame, Surface Attachment & Annotation Contract

**Tài liệu ID:** `MSK-P21-AUD-004`  
**Ngày thực hiện:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Vai trò:** Principal 3D Anatomical Systems Architect  
**Trạng thái Thẩm định:** `CONTRACT_APPROVED`  

---

### 1. Hệ Quy Chiếu Tọa Độ Chuẩn (Canonical Coordinate Frame)

Mọi cấu trúc giải phẫu, điểm đánh dấu (acupoint marker), và đường dẫn (meridian polyline) trong P21 phải tuân thủ nghiêm ngặt hệ quy chiếu sau:

```text
       +Y (Superior / Cranial / Head)
          ^
          |
          |
          +-----> +X (Patient Left / Lateral)
         /
        /
       v
      +Z (Anterior / Ventral / Front)
```

- **Hệ tọa độ:** Descartes thuận tay phải (Right-Handed Cartesian Coordinate System).
- **Đơn vị đo lường (Units):** **Mét ($m$)** cho toàn bộ tọa độ hình học 3D; **Milimét ($mm$)** cho độ bất định bán kính (uncertainty radius).
- **Gốc tọa độ (Origin $(0,0,0)$):** Mặt phẳng sàn nâng đỡ hai gót chân tại $Y=0$, mặt phẳng đứng dọc giữa cơ thể tại $X=0$, và mặt phẳng trán đi qua trục trung tâm tại $Z=0$.
- **Định hướng trục:**
  - $+X$: Hướng sang bên trái của bệnh nhân (Patient Left).
  - $-X$: Hướng sang bên phải của bệnh nhân (Patient Right).
  - $+Y$: Hướng lên đỉnh đầu (Superior / Cranial).
  - $-Y$: Hướng xuống bàn chân (Inferior / Caudal).
  - $+Z$: Hướng ra phía trước ngực / bụng (Anterior / Ventral).
  - $-Z$: Hướng ra phía sau lưng / gáy (Posterior / Dorsal).

---

### 2. Hợp đồng Gắn kết Bề mặt Cấu trúc (Surface Attachment Contract)

Để tránh hiện tượng điểm đánh dấu hoặc đường kinh bị "trôi dạt" (drifting) khi thay đổi góc camera, zoom, hoặc khi chuyển đổi hệ thống mesh, mỗi điểm đánh dấu phải được ràng buộc hình học vào chính bề mặt của một cấu trúc giải phẫu xác định:

#### A. Cấu trúc Dữ liệu Ràng buộc Điểm (Point Annotation Schema)

```json
{
  "annotation_id": "PT-20261101-001",
  "label": "Huyệt Hợp Cốc (LI4)",
  "standard_code": "LI4",
  "category": "manual_acupoint",
  "verification_status": "USER_ANNOTATED_UNVERIFIED",
  "anatomical_target": {
    "mesh_id": "FJ3237",
    "structure_name": "Left clavicle",
    "system": "skeletal",
    "concept_id": "FMA13323",
    "asset_sha256": "c359f4bcd2cba90b7411d66d5e9fc04dc81294d46cd5c1e8b212c824f2e5bbee"
  },
  "spatial_attachment": {
    "world_position": [0.0452, 1.4120, 0.0210],
    "local_position": [0.0152, 0.0120, 0.0050],
    "surface_normal": [0.1200, 0.8500, 0.5100],
    "triangle_index": 412,
    "barycentric_coords": [0.35, 0.45, 0.20],
    "uncertainty_radius_mm": 5.0
  },
  "provenance": {
    "created_at": "2026-11-01T14:15:00Z",
    "created_by": "clinical_student_evaluator",
    "software_version": "MSK-Therapy-OS-P21-PoC",
    "notes": "Đánh dấu thử nghiệm tại mốc giải phẫu quan sát được."
  }
}
```

---

### 3. Hợp đồng Đường dẫn Đa điểm (Polyline / Meridian Contract)

Đường kinh vẽ tay (Manual Meridian / Polyline) được định nghĩa là một chuỗi tuần tự gồm tối thiểu 3 điểm mốc (waypoints):

```json
{
  "polyline_id": "PL-20261101-001",
  "label": "Đoạn Kinh Phế Thủ Thái Âm (Thực nghiệm)",
  "system_type": "meridian_trajectory",
  "status": "USER_DRAFT_UNVERIFIED",
  "waypoints": [
    {
      "index": 0,
      "mesh_id": "FJ3237",
      "world_position": [0.0452, 1.4120, 0.0210],
      "triangle_index": 412
    },
    {
      "index": 1,
      "mesh_id": "FJ3262",
      "world_position": [0.1520, 1.3500, -0.0100],
      "triangle_index": 128
    },
    {
      "index": 2,
      "mesh_id": "FJ3262",
      "world_position": [0.1850, 1.2100, -0.0250],
      "triangle_index": 305
    }
  ],
  "render_attributes": {
    "color": "#00e5ff",
    "line_width_mm": 2.5,
    "depth_offset_bias": -0.0005
  }
}
```

---

### 4. Quy tắc Bất biến: Bảo toàn Tính Toàn vẹn (Fail-Closed Governance Invariant)

1. **Cấm di chuyển ngầm (No Silent Drifting):** Khi nạp lại một annotation, nếu checksum SHA-256 của `atlas.json` hoặc mesh chunk khác với giá trị đã lưu trong `asset_sha256`, hệ thống **bắt buộc phải kích hoạt chế độ cảnh báo không khớp (Mismatch Warning)** và yêu cầu người dùng xác nhận tái căn chỉnh (remap), tuyệt đối không tự dịch chuyển tọa độ theo một thuật toán suy diễn nào.
2. **Cấm tự tuyên bố chuẩn lâm sàng:** Mọi annotation do người dùng tạo lập qua PoC bắt buộc mang nhãn `USER_ANNOTATED_UNVERIFIED`. Không một thao tác nào trên UI được phép gán trạng thái `CLINICAL_APPROVED` hay `ANATOMICAL_VERIFIED`.
3. **Độ lệch hình học < 15 mm không phải bằng chứng huyệt học:** Sự trùng hợp giữa một điểm nhấp chuột và một mặt tam giác chỉ là hiện tượng va chạm raycast đồ họa máy tính (Computer Graphics collision), không cấu thành thẩm định vị trí huyệt học theo y văn cổ truyền hoặc tiêu chuẩn WHO.
