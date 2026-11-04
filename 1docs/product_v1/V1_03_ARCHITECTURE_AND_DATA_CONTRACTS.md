# V1_03: ARCHITECTURE AND DATA CONTRACTS SPECIFICATION
**MSK-Therapy-OS V1.0 | Product Completion Roadmap**

---

## 1. THỨ TỰ BIẾN ĐỔI CHUẨN VÀ TRÁNH DOUBLE TRANSFORM (TRANSFORM ORDER CONTRACT)

Để đảm bảo tính nhất quán hình học và tránh hiện tượng nhân đôi ma trận biến đổi (double transformation), toàn bộ hệ thống tuân thủ nghiêm ngặt chuỗi thực thi 5 giai đoạn:

```
[1. Base Anatomy] 
      │ (Tọa độ gốc BodyParts3D theo mét)
      ▼
[2. Body Morph & Parametric Scaling] 
      │ (Thanh trượt: Chiều cao, Tỷ lệ dài chi, Chu vi chi)
      ▼
[3. Joint Pivot & Landmark Recomputation] 
      │ (Cập nhật tâm xoay khớp khuỷu, cổ tay và mốc bám xương)
      ▼
[4. Surface Anchor & Meridian Re-evaluation] 
      │ (Tọa độ cục bộ / Barycentric giữ nguyên trên mesh biến dạng)
      ▼
[5. Pose Kinematics & Armature Hierarchy] 
      │ (Quay xương theo nhịp 2:1 và gập duỗi khuỷu)
      ▼
[6. WebGL Canvas & Blender Viewport Rendering]
```

---

## 2. HỢP ĐỒNG DỮ LIỆU THAM SỐ HÌNH THỂ (BODY PARAMETERS SCHEMA)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BodyParameters",
  "type": "object",
  "required": ["height_scale", "right_arm_length_ratio", "right_arm_circumference_visual", "preset_name"],
  "properties": {
    "height_scale": {
      "type": "number",
      "minimum": 0.85,
      "maximum": 1.15,
      "default": 1.00,
      "description": "Tỷ lệ co giãn chiều cao toàn thân theo trục Y"
    },
    "right_arm_length_ratio": {
      "type": "number",
      "minimum": 0.85,
      "maximum": 1.15,
      "default": 1.00,
      "description": "Tỷ lệ chiều dài cánh tay và cẳng tay phải"
    },
    "right_arm_circumference_visual": {
      "type": "number",
      "minimum": 0.80,
      "maximum": 1.30,
      "default": 1.00,
      "description": "Tỷ lệ độ dày chu vi cơ bắp và mô mềm vùng cánh tay (mô hình trực quan)"
    },
    "preset_name": {
      "type": "string",
      "enum": ["baseline", "slender", "broader", "longer_arm", "custom"],
      "default": "baseline"
    },
    "morph_version": {
      "type": "integer",
      "default": 1
    }
  }
}
```

---

## 3. HỢP ĐỒNG DỮ LIỆU MỐC HUYỆT VÀ ĐƯỜNG KINH (DYNAMIC ANCHORS SCHEMA)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SurfaceAnchor",
  "type": "object",
  "required": ["marker_id", "code", "target_mesh_name", "target_bone_name", "local_coordinates", "clinical_verification_status"],
  "properties": {
    "marker_id": {"type": "string"},
    "code": {"type": "string"},
    "name_vi": {"type": "string"},
    "name_en": {"type": "string"},
    "fma_id": {"type": "string"},
    "target_mesh_name": {"type": "string"},
    "target_bone_name": {"type": "string"},
    "local_coordinates": {
      "type": "array",
      "items": {"type": "number"},
      "minItems": 3,
      "maxItems": 3
    },
    "local_normal": {
      "type": "array",
      "items": {"type": "number"},
      "minItems": 3,
      "maxItems": 3
    },
    "barycentric_coordinates": {
      "type": ["array", "null"],
      "items": {"type": "number"},
      "minItems": 3,
      "maxItems": 3
    },
    "technical_anchor_status": {
      "type": "string",
      "enum": ["VALID_SURFACE_ANCHOR", "UNATTACHED"]
    },
    "clinical_verification_status": {
      "type": "string",
      "enum": ["EXPERT_REVIEW_PENDING", "VALID_ANATOMICAL_LANDMARK", "REVISE_REQUIRED"]
    },
    "source_reference": {"type": "string"}
  }
}
```

---

## 4. HỢP ĐỒNG DỰ ÁN DI ĐỘNG (PORTABLE PROJECT MANIFEST SCHEMA)

Tệp dự án có phần mở rộng `.mskproj` được đóng gói dưới định dạng JSON nguyên tử (atomic JSON), chứa đầy đủ thông tin để khôi phục chính xác trạng thái làm việc:

```json
{
  "project_id": "proj_msk_v1_001",
  "schema_version": "1.0.0",
  "created_at": "2026-11-03T19:00:00Z",
  "updated_at": "2026-11-03T19:20:00Z",
  "body_parameters": {
    "height_scale": 1.05,
    "right_arm_length_ratio": 1.10,
    "right_arm_circumference_visual": 1.00,
    "preset_name": "longer_arm"
  },
  "current_pose": {
    "frame_index": 50,
    "shoulder_elevation_deg": 98.02,
    "elbow_flexion_deg": 80.44
  },
  "surface_anchors": {},
  "manual_adjustments": [],
  "knowledge_references": ["LI4", "LI14", "LI15"],
  "notes": "Hồ sơ nghiên cứu hình thể người mẫu dài tay"
}
```
