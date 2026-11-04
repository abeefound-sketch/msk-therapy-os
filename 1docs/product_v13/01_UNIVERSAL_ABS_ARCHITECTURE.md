# MSK-THERAPY-OS V1.3 — TÀI LIỆU KỸ THUẬT SỐ 01
## UNIVERSAL ANATOMICAL BINDING SYSTEM (ABS) ARCHITECTURE

- **Phân loại:** Kỹ thuật / Kiến trúc phần mềm (ENGINEERING_RESEARCH_ONLY)
- **Hiệu lực y sinh:** CHƯA XÁC LẬP (CLINICAL_VALIDATION = NOT_ESTABLISHED)
- **Mục tiêu cốt lõi:** Chuyển đổi ABS từ cơ chế cục bộ của cánh tay thành một hệ thống liên kết giải phẫu tổng quát, có khả năng áp dụng cho bất kỳ vùng cơ thể nào thông qua khai báo cấu hình (declarative schema) và chiến lược đa hình (polymorphic binding strategies).

---

### 1. KIẾN TRÚC TOÀN CẢNH (UNIFIED SYSTEM ARCHITECTURE)

```
MSK-Therapy-OS V1.3
│
├── Canonical Humanoid Skeleton (Single Armature: 53 Bones)
│   ├── Spine & Pelvis: pelvis, spine_01, spine_02, neck, head
│   ├── Upper Limbs: clavicle_r/l, upperarm_r/l, lowerarm_r/l, hand_r/l
│   └── Lower Limbs: thigh_r/l, calf_r/l, foot_r/l
│
├── Universal Anatomical Binding System (Universal ABS Core)
│   ├── Schema Validation & Contract (universal_binding_schema.py)
│   ├── 5 Polymorphic Strategies (strategies.py):
│   │   ├── RIGID_BONE (Parenting, 4x4 Invert, Invariance check)
│   │   ├── MULTI_BONE_SKINNING (Dual/Multi-bone weight, Isovolumetric bulge)
│   │   ├── ATTACHMENT_DRIVEN_DEFORMATION (Line-of-action Euclidean kinematics)
│   │   ├── SURFACE_BARYCENTRIC (Acupoint normal and surface projection)
│   │   └── MORPH_AWARE_REGISTRATION (Shape key adaptation, reversibility)
│   └── Universal Anatomical Registry (universal_anatomical_registry.py)
│
├── 3D Asset Pipeline (Blender 3.6 LTS -> GLB -> Three.js)
│   ├── Full-Body MakeHuman Skinned Skin (19.158 vertices, 7 Morph Targets)
│   ├── 9 Authentic BodyParts3D Bones (Humerus, Radius, Ulna, Metacarpal II, Clavicle, Femur, Tibia, Fibula, Patella)
│   ├── 10 Authentic BodyParts3D Muscles (Biceps 2 đầu, Triceps 3 đầu, Brachialis, Quads 4 đầu)
│   ├── 6 Dynamic Surface Anchors (LI4, LI11, LI14, LI15, ST36, KI3)
│   └── 2 Dynamic 3D Tube Meridians (Large Intestine & Stomach)
│
└── Full-Body Web Atlas (/character_v13/index.html)
    ├── 5 Layer Toggles (Bones, Muscles, Skin, Acupoints, Meridians)
    ├── Multi-Joint Simultaneous Kinematics (Elbow, Shoulder, Knee, Hip, Torso)
    ├── Parametric Morph Presets (Baseline, Slender, Broader, LongArm, LongLeg)
    ├── Live Evaluated Geometry HUD (< 0.12 mm invariance, 0.00 mm penetration)
    └── Programmatic Test API (window.__UNIVERSAL_ABS_V13__)
```

---

### 2. HỢP ĐỒNG DỮ LIỆU KHAI BÁO (DECLARATIVE DATA CONTRACT)

Một liên kết giải phẫu chuẩn được định nghĩa qua schema cấu trúc dữ liệu JSON/Python chuẩn mực:

```json
{
  "structure_id": "FJ1433",
  "structure_type": "MUSCLE",
  "anatomical_name_en": "Rectus femoris",
  "anatomical_name_vi": "Cơ thẳng đùi",
  "laterality": "RIGHT",
  "source_mesh_id": "Rectus_femoris_R",
  "source_mesh_file": "Rectus_femoris_R.obj",
  "source_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "canonical_skeleton_id": "makehuman_game_engine_53",
  "primary_bone_id": "thigh_r",
  "secondary_bone_id": "calf_r",
  "origin_attachment": {
    "landmark_name": "Spina iliaca anterior inferior",
    "target_bone_id": "pelvis",
    "local_position_m": [-0.08, 0.02, 0.06],
    "anatomical_feature": "Gai chậu trước dưới (AIIS)"
  },
  "insertion_attachment": {
    "landmark_name": "Tuberositas tibiae",
    "target_bone_id": "calf_r",
    "local_position_m": [-0.14, -0.01, -0.38],
    "anatomical_feature": "Lồi củ xương chày qua xương bánh chè"
  },
  "deformation_strategy": "MULTI_BONE_SKINNING",
  "registration_status": "REGISTERED_ACTIVE",
  "fma_id": "FMA:22428",
  "source_reference": "BodyParts3D CC BY 4.0 DBCLS Japan",
  "metadata": {
    "resting_length_m": 0.4400,
    "flexed_length_m": 0.4850,
    "resting_diameter_mm": 55.0,
    "max_joint_deg": 90.0
  }
}
```

---

### 3. ĐẶC TẢ 5 CHIẾN LƯỢC BINDING (POLYMORPHIC STRATEGIES)

| Chiến lược (Strategy) | Áp dụng cho | Cơ chế toán học & Biến dạng | Tiêu chuẩn nghiệm thu |
| :--- | :--- | :--- | :--- |
| **`RIGID_BONE`** | Mesh xương cứng (9 xương BP3D) | Gắn cố định vào xương cha: $M_{\text{world}} = M_{\text{parent}} \times M_{\text{bind}}$. Tính $M_{\text{inv}}$. Không co giãn. | Sai số bất biến thân xương $\Delta L < 0.12\text{ mm}$. |
| **`MULTI_BONE_SKINNING`** | Cơ bắp bắc qua khớp (Biceps, Triceps, Quads) | Phân bổ trọng số gradient 2 đầu xương. Tính hệ số co ngắn/giãn dài. Phồng thể tích đẳng tích: $k_{\text{bulge}} = \sqrt{L_{\text{rest}} / L_{\text{curr}}}$. | Biến dạng mượt mà, không rách đỉnh. |
| **`ATTACHMENT_DRIVEN_DEFORMATION`** | Đường nối nguyên ủy - bám tận | Tính khoảng cách Euclidean giữa các điểm mốc giải phẫu: $D = \sqrt{\Delta X^2 + \Delta Y^2 + \Delta Z^2}$. | Phản ánh đúng chiều dài đường cơ sinh học. |
| **`SURFACE_BARYCENTRIC`** | Mốc huyệt vị (6 huyệt LI4-15, ST36, KI3) | Gắn vào xương cha kèm vector pháp tuyến mặt da $\vec{N}$ và bù trừ độ nâng $\Delta Y$. | Mốc huyệt bám chặt mặt da khi khớp xoay. |
| **`MORPH_AWARE_REGISTRATION`** | Điều chỉnh theo vóc dáng | Nhân tỷ lệ hướng tâm theo trọng số Morph Targets (`Broader`, `Slender`, `Length`). | Khôi phục $100\%$ về nguyên bản khi morph về 0. |

---

### 4. BẰNG CHỨNG KIẾN TRÚC TÁI SỬ DỤNG (ARCHITECTURAL REUSABILITY PROOF)

Đạt trọn vẹn yêu cầu mục 12 của Master Implementation Prompt:
- Bổ sung cấu trúc giải phẫu mới (ví dụ: Cơ quạ cánh tay `FJ1488` Coracobrachialis) **hoàn toàn bằng dữ liệu JSON khai báo qua REST API `POST /api/character/v13/register`** mà không cần sửa đổi bất kỳ dòng mã nào trong thuật toán lõi của ABS!
- Cấu trúc mới được tự động thẩm định hợp lệ, tự động gán chiến lược `MULTI_BONE_SKINNING`, và xuất hiện ngay lập tức trong danh mục `GET /api/character/v13/structures`.
- Kiểm thử tự động `test_v13_architectural_reusability_dynamic_registration` đạt **`PASSED`** tuyệt đối.
