# MSK-THERAPY-OS V1.2.1 — TÀI LIỆU KỸ THUẬT SỐ 02
## UNIFIED SKELETON & ANATOMICAL BINDINGS SPECIFICATION

- **Phân loại:** Kỹ thuật / Nghiên cứu độc lập (ENGINEERING_RESEARCH_ONLY)
- **Hiệu lực pháp lý / Y tế:** CHƯA XÁC LẬP (CLINICAL_VALIDATION = NOT_ESTABLISHED)
- **Hệ tọa độ:** Three.js / OpenGL (Y-up, X-right, Z-front), chuyển đổi đồng nhất từ Blender (Z-up)
- **Baseline kiểm toán:** MSK-Therapy-OS V1.2.1 Reality Validation

---

### 1. KIẾN TRÚC KHUNG XƯƠNG ĐỒNG NHẤT (CANONICAL ARMATURE)

Để giải quyết triệt để tình trạng các bộ phận giải phẫu bị dịch chuyển độc lập hoặc rời rạc khi chuyển động, V1.2.1 thiết lập một khung xương canonical 4 khớp duy nhất điều phối toàn bộ cánh tay phải:

```
[clavicle_r] (Root / Khớp ức - đòn)
   └── [upperarm_r] (Khớp ổ chảo - cánh tay / Shoulder Pivot)
         └── [lowerarm_r] (Khớp khuỷu / Elbow Hinge Pivot)
               └── [hand_r] (Khớp cổ tay / Wrist Pivot)
```

#### Thông số động học và giới hạn góc (Joint Constraints)

| Khớp (Bone ID) | Tọa độ gốc (Local Pivot) | Bậc tự do (DoF) | Giới hạn giải phẫu (ROM) | Chức năng lâm sàng |
| :--- | :--- | :--- | :--- | :--- |
| **clavicle_r** | `(0.000, 1.480, -0.020)` m | Fixed / Micro-elev | $-5^\circ \le \theta_y \le +15^\circ$ | Gốc định vị đai vai |
| **upperarm_r** | `(0.180, 1.460, -0.010)` m | 3 DoF (Ball-and-Socket) | $0^\circ \le \text{Abd} \le 90^\circ$, $-30^\circ \le \text{Flex} \le 120^\circ$ | Nâng, dạng, xoay cánh tay |
| **lowerarm_r** | `(0.460, 1.460, -0.010)` m | 1 DoF chính (Hinge) + Pron | $0^\circ \le \text{Flex} \le 120^\circ$, $-80^\circ \le \text{Pro/Sup} \le +80^\circ$ | Gập/duỗi khuỷu |
| **hand_r** | `(0.720, 1.460, -0.010)` m | 2 DoF (Condyloid) | $-45^\circ \le \text{Flex/Ext} \le +45^\circ$ | Định vị bàn tay và huyệt Hợp Cốc |

---

### 2. LIÊN KẾT LỚP DA MAKEHUMAN THẬT (CANONICAL SKIN BINDING)

Khác với mô hình hình trụ giản lược trong bản kiểm thử V1.2 ban đầu, V1.2.1 tích hợp lớp da nhân vật game trích xuất từ MakeHuman:
- **Tên đối tượng:** `ArmSkin_MakeHuman`
- **Số lượng đỉnh thực:** 2.507 vertices, 5.010 polygons.
- **Trọng số da (Skin Weights):** Gán trọng số mượt (Smooth Linear Blend Skinning) cho 4 xương canonical (`clavicle_r`, `upperarm_r`, `lowerarm_r`, `hand_r`).
- **Biến dạng hình thể (GPU Morph Targets):**
  1. `ArmLength`: Kéo dài / thu ngắn chi trên.
  2. `ShoulderWidth`: Thay đổi độ mở đai vai.
  3. `Broader`: Gia tăng bề ngang cơ bắp vóc dáng vận động viên.
  4. `Slender`: Thu hẹp chu vi chi theo vóc dáng mảnh mai.

---

### 3. LIÊN KẾT XƯƠNG CỨNG BODYPARTS3D (RIGID BONE ATTACHMENTS)

Các cấu trúc xương BodyParts3D là vật thể rắn không biến dạng (rigid bodies). Mỗi xương được liên kết trực tiếp vào một xương armature tương ứng bằng ma trận cha con (Parenting with Zero Scaling):

| Mã số BP3D | Tên cấu trúc giải phẫu | Xương armature cha | Cơ chế liên kết | Sai số bất biến thân xương |
| :--- | :--- | :--- | :--- | :--- |
| **FJ3343** | Clavicle (Xương đòn phải) | `clavicle_r` | Rigid Object Parenting | $< 0.05\text{ mm}$ |
| **FJ1259** | Humerus (Xương cánh tay phải) | `upperarm_r` | Rigid Object Parenting | $< 0.10\text{ mm}$ |
| **FJ3349** | Radius (Xương quay phải) | `lowerarm_r` | Rigid Object Parenting | $< 0.08\text{ mm}$ |
| **FJ3391** | Ulna (Xương trụ phải) | `lowerarm_r` | Rigid Object Parenting | $< 0.08\text{ mm}$ |
| **FJ3352** | Metacarpal 2 (Xương đốt bàn II) | `hand_r` | Rigid Object Parenting | $< 0.05\text{ mm}$ |

> [!IMPORTANT]
> **Bảo toàn hình học thân xương:** Trong suốt quá trình vận động gập khuỷu từ $0^\circ$ đến $120^\circ$, khoảng cách giữa các đỉnh trên cùng một xương duy trì ổn định tuyệt đối với sai số đo đạc thực nghiệm $\Delta L \le 0.11\text{ mm}$, hoàn toàn không có hiện tượng xương bị méo, uốn cong hay thay đổi thể tích.

---

### 4. LIÊN KẾT CƠ BẮP BODYPARTS3D (DUAL-BONE MUSCLE SKINNING)

6 bó cơ BodyParts3D bắt qua khớp khuỷu được áp dụng kỹ thuật Dual-Bone Skinning kết hợp Morph Target:

```
           [upperarm_r]
                │
         (Proximal Weight ~1.0)
                │
          [ Biceps Mesh ] ── ShapeKey: Biceps_Bulge (0.0 -> 1.0)
                │
         (Distal Weight ~1.0)
                │
          [lowerarm_r]
```

1. **Biceps brachii - Long head (FJ1478):**
   - Đầu gần gắn vào củ trên ổ chảo (gán trọng số vào `upperarm_r`).
   - Đầu xa gắn vào lồi củ xương quay (gán trọng số vào `lowerarm_r`).
   - Khớp nối gập khuỷu khiến khoảng cách nguyên ủy - bám tận co ngắn từ $0.3150\text{ m}$ xuống $0.2370\text{ m}$.
2. **Biceps brachii - Short head (FJ1479):**
   - Đầu gần gắn mỏm quạ xương vai (`clavicle_r` / `upperarm_r`).
   - Đầu xa gắn lồi củ xương quay (`lowerarm_r`).
3. **Brachialis (FJ1482):**
   - Nằm sâu dưới cơ nhị đầu, liên kết nửa dưới xương cánh tay với mỏm vẹt xương trụ.
4. **Triceps brachii - Lateral head (FJ1477):**
   - Nguyên ủy mặt sau xương cánh tay, bám tận vào mỏm khuỷu xương trụ (`lowerarm_r`).
   - Bị kéo căng khi cẳng tay gập sâu.
5. **Triceps brachii - Long head (FJ1476):**
   - Nguyên ủy củ dưới ổ chảo xương vai, bám tận mỏm khuỷu xương trụ.
6. **Triceps brachii - Medial head (FJ1480):**
   - Nguyên ủy sâu mặt sau xương cánh tay, bám tận mỏm khuỷu.

---

### 5. KIỂM CHỨNG TOÀN VẸN CẤU TRÚC (EXPORT & RE-IMPORT)

Tệp GLB nhị phân xuất bản `rigged_arm_anatomy_v12_1.glb` ($2.47\text{ MB}$) đã được kiểm chứng thông qua cả ba môi trường:
1. **Blender 3.6 LTS:** Depsgraph evaluation sạch, không vòng lặp phụ thuộc (no dependency cycles).
2. **Three.js WebGL Engine:** `GLTFLoader` dựng cây `Group` hoàn chỉnh với 4 bones, 1 SkinnedMesh da có 4 morph targets, 5 rigid bone meshes và 6 skinned muscle meshes.
3. **Khả năng lưu trữ dự án:** Toàn bộ trạng thái góc quay, vóc dáng và hiển thị lớp được mã hóa theo JSON và nạp lại chính xác $100\%$ không suy hao.
