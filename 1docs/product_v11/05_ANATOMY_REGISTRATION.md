# MSK-THERAPY-OS V1.1 — ANATOMICAL ATLAS ADAPTER SPECIFICATION
## Bộ Chuyển Đổi Đăng Ký Giải Phẫu (Character-Anatomy Registration)

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Bộ điều hợp:** `msk_therapy_os/character_anatomy_adapter.py`

---

### 1. NGUYÊN TẮC THIẾT KẾ ĐĂNG KÝ GIẢI PHẪU

1. **Phân định Nền tảng vs Nguồn Giải phẫu:**
   - MakeHuman đóng vai trò là khung tham chiếu chuyển động học (Kinematic Skeleton) và bề mặt nhân trắc học (Surface Manifold).
   - BodyParts3D 4.0 và Z-Anatomy đóng vai trò là nguồn tài sản giải phẫu có hồ sơ xuất xứ (Provenance).
2. **Không đồng nhất topology:** Tuyệt đối không giả định hai mô hình có chung topology, số lượng đỉnh hay cùng trục tọa độ. Mọi liên kết phải qua ma trận transform rõ ràng.
3. **Bảo toàn hình học xương:** Xương thật không bị co giãn thể tích như mô mềm (`RIGID_PARENT_TO_BONE`), chỉ nhận phép quay và tịnh tiến theo tâm xoay khớp sinh lý.
4. **Quy tắc Thất bại Đóng (Fail-Closed):** Mọi cấu trúc chưa có điểm mốc đối ứng được đo đạc tin cậy bắt buộc gán nhãn **`ANATOMICAL_REGISTRATION_PENDING`**, không dùng AI suy đoán geometry.

---

### 2. BẢNG DANH MỤC ĐĂNG KÝ VÙNG CHI TRÊN PHẢI

| Structure ID | Cấu trúc Giải phẫu | Mesh Nguồn BodyParts3D | Khớp Rig Tham Chiếu | Phương pháp Biến dạng | Trạng thái Nghiệm thu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`FJ3238`** | Xương đòn phải (Right clavicle) | `Clavicle_R.obj` | `clavicle_r` | `RIGID_PARENT_TO_BONE` | <span class="pill-pass">REGISTERED_ACTIVE</span> |
| **`FJ3368`** | Xương cánh tay phải (Right humerus) | `Humerus_R.obj` | `upperarm_r` | `RIGID_PARENT_TO_BONE` | <span class="pill-pass">REGISTERED_ACTIVE</span> |
| **`FJ3381`** | Xương quay phải (Right radius) | `Radius_R.obj` | `lowerarm_r` | `RIGID_PARENT_TO_BONE` | <span class="pill-pass">REGISTERED_ACTIVE</span> |
| **`FJ3383`** | Xương trụ phải (Right ulna) | `Ulna_R.obj` | `lowerarm_r` | `RIGID_PARENT_TO_BONE` | <span class="pill-pass">REGISTERED_ACTIVE</span> |
| **`FJ3352`** | Xương bàn tay 2 phải (Metacarpal 2 R) | `Metacarpal_2_R.obj` | `hand_r` | `RIGID_PARENT_TO_BONE` | <span class="pill-pass">REGISTERED_ACTIVE</span> |
| **`FJ3280`** | Đốt sống ngực T1 (Thoracic vertebra 1) | `Thoracic_Vertebra_1.obj` | `spine_03` | `PENDING_MODEL` | <span class="pill-pending">ANATOMICAL_REGISTRATION_PENDING</span> |

---

### 3. CƠ CHẾ HIỂN THỊ BA CHẾ ĐỘ (THREE DISPLAY MODES)

- **`CHARACTER_MODE` (Chế độ Nhân vật):**
  - Mesh da hiển thị độ mờ $100\%$ (`opacity: 1.0`).
  - Toàn bộ xương giải phẫu ẩn (`visible: false`).
  - Thích hợp cho quan sát chuyển động tổng thể và tương tác cử động chi thể mượt mà.
- **`ANATOMY_MODE` (Chế độ Giải phẫu):**
  - Mesh da ẩn hoàn toàn (`visible: false`).
  - Toàn bộ các xương BodyParts3D đã đăng ký hiển thị rõ nét với vật liệu xương chuẩn (`opacity: 1.0`).
  - Thích hợp cho đào tạo và khảo sát cấu trúc cơ xương khớp.
- **`OVERLAY_MODE` (Chế độ Lớp lồng):**
  - Mesh da hiển thị bán trong suốt (`opacity: 0.65`, có thể điều chỉnh qua thanh trượt).
  - Toàn bộ xương giải phẫu hiển thị bên trong lòng lớp da, cho phép người dùng quan sát trực quan vị trí xương dưới da khi gập khuỷu tay hoặc dạng vai.
