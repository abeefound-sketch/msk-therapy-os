# MSK-THERAPY-OS V1.3 — TÀI LIỆU KỸ THUẬT SỐ 02
## FULL-BODY CANONICAL SKELETON & ANATOMICAL BINDINGS

- **Phân loại:** Kỹ thuật đồ họa / Rigging giải phẫu (ENGINEERING_RESEARCH_ONLY)
- **Hiệu lực y sinh:** CHƯA XÁC LẬP (CLINICAL_VALIDATION = NOT_ESTABLISHED)
- **Quy chuẩn:** Duy nhất một khung xương canonical 53 bones điều phối toàn bộ cơ thể người; loại bỏ hoàn toàn các rig riêng biệt cho từng chi.

---

### 1. PHÂN CẤP KHUNG XƯƠNG ĐỒNG NHẤT (CANONICAL HUMANOID RIG)

Toàn bộ hệ thống V1.3 sử dụng cây xương `HumanArmature` 53 bones chuẩn MakeHuman GameEngine:

```
[root]
  └── [pelvis] (0.000, -0.013, 0.056)
        ├── [spine_01] -> [spine_02] -> [neck] -> [head]
        │     ├── [clavicle_l] -> [upperarm_l] -> [lowerarm_l] -> [hand_l]
        │     └── [clavicle_r] -> [upperarm_r] -> [lowerarm_r] -> [hand_r]
        ├── [thigh_l] -> [calf_l] -> [foot_l] -> [toes_l]
        └── [thigh_r] -> [calf_r] -> [foot_r] -> [toes_r]
```

#### Bảng thông số hình học các phân đoạn vận động chính:

| Xương Canonical | Tọa độ đầu (Head local m) | Tọa độ đuôi (Tail local m) | Chiều dài ($L$ m) | Chức năng giải phẫu |
| :--- | :--- | :--- | :--- | :--- |
| **pelvis** | `(0.0000, -0.0132, 0.0560)` | `(0.0000, 0.0255, 0.1357)` | $0.0887$ | Khớp háng - chậu trung tâm |
| **spine_02** | `(0.0000, 0.0150, 0.2800)` | `(0.0000, 0.0050, 0.4400)` | $0.1600$ | Vận động xoay thân (Torso twist) |
| **clavicle_r** | `(-0.0227, -0.0216, 0.5248)` | `(-0.1700, -0.0193, 0.5021)` | $0.1475$ | Đai vai phải |
| **upperarm_r** | `(-0.1700, -0.0193, 0.5021)` | `(-0.3314, -0.0201, 0.3215)` | $0.2421$ | Dạng/nâng/xoay cánh tay phải |
| **lowerarm_r** | `(-0.3314, -0.0201, 0.3215)` | `(-0.4533, -0.1833, 0.1973)` | $0.2386$ | Gập/duỗi khuỷu phải ($0^\circ \to 120^\circ$) |
| **hand_r** | `(-0.4533, -0.1833, 0.1973)` | `(-0.4640, -0.2094, 0.1816)` | $0.0322$ | Cổ tay & mốc huyệt Hợp Cốc (LI4) |
| **thigh_r** | `(-0.1014, -0.0049, 0.0479)` | `(-0.1425, -0.0374, -0.3431)` | $0.3944$ | Gập/duỗi khớp háng & xương đùi |
| **calf_r** | `(-0.1425, -0.0374, -0.3431)` | `(-0.1806, -0.0227, -0.7486)` | $0.4076$ | Gập khớp gối phải ($0^\circ \to 90^\circ$) & cẳng chân |
| **foot_r** | `(-0.1806, -0.0227, -0.7486)` | `(-0.1860, -0.1395, -0.8088)` | $0.1315$ | Cổ chân, bàn chân & huyệt Thái Khê (KI3) |

---

### 2. BẢN ĐỒ LIÊN KẾT 9 XƯƠNG CỨNG BODYPARTS3D (RIGID BONES)

Toàn bộ 9 xương BodyParts3D được ràng buộc ma trận affine 4x4 không co giãn thể tích:

| Mã số BP3D | Tên xương tiếng Anh | Tên xương tiếng Việt | Xương cha | Số đỉnh | Chiến lược |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FJ3343** | Clavicle_R | Xương đòn phải | `clavicle_r` | 150 | `RIGID_BONE` |
| **FJ3368** | Humerus_R | Xương cánh tay phải | `upperarm_r` | 465 | `RIGID_BONE` |
| **FJ3349** | Radius_R | Xương quay phải | `lowerarm_r` | 370 | `RIGID_BONE` |
| **FJ3391** | Ulna_R | Xương trụ phải | `lowerarm_r` | 385 | `RIGID_BONE` |
| **FJ3352** | Metacarpal_2_R | Xương đốt bàn II phải | `hand_r` | 120 | `RIGID_BONE` |
| **FJ3365** | Femur_R | Xương đùi phải | `thigh_r` | 480 | `RIGID_BONE` |
| **FJ3387** | Tibia_R | Xương chày phải | `calf_r` | 334 | `RIGID_BONE` |
| **FJ3366** | Fibula_R | Xương mác phải | `calf_r` | 162 | `RIGID_BONE` |
| **FJ3381** | Patella_R | Xương bánh chè phải | `thigh_r` / `calf_r` | 176 | `RIGID_BONE` |

---

### 3. BẢN ĐỒ LIÊN KẾT 10 CƠ BẮP BODYPARTS3D (DUAL-BONE MUSCLES)

10 khối cơ thật được áp dụng trọng số da phân tầng kết hợp Shape Key co phồng thể tích:

| Mã số BP3D | Tên cơ tiếng Anh | Tên cơ tiếng Việt | Xương bắc qua | Trọng số Blend | Shape Key Phồng |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FJ1478** | Biceps brachii (long head) | Cơ nhị đầu - đầu dài | `upperarm_r` $\to$ `lowerarm_r` | 0.65 / 0.35 | `Biceps_Bulge` |
| **FJ1512** | Biceps brachii (short head) | Cơ nhị đầu - đầu ngắn | `upperarm_r` $\to$ `lowerarm_r` | 0.70 / 0.30 | --- |
| **FJ1477** | Triceps brachii (lateral head) | Cơ tam đầu - đầu ngoài | `upperarm_r` $\to$ `lowerarm_r` | 0.70 / 0.30 | --- |
| **FJ1479** | Triceps brachii (long head) | Cơ tam đầu - đầu dài | `upperarm_r` $\to$ `lowerarm_r` | 0.75 / 0.25 | --- |
| **FJ1480** | Triceps brachii (medial head) | Cơ tam đầu - đầu trong | `upperarm_r` $\to$ `lowerarm_r` | 0.60 / 0.40 | --- |
| **FJ1486** | Brachialis | Cơ cánh tay sâu | `upperarm_r` $\to$ `lowerarm_r` | 0.55 / 0.45 | --- |
| **FJ1433** | Rectus femoris | Cơ thẳng đùi | `thigh_r` $\to$ `calf_r` | 0.70 / 0.30 | `Quad_Flex` |
| **FJ1441** | Vastus intermedius | Cơ rộng giữa | `thigh_r` $\to$ `calf_r` | 0.75 / 0.25 | --- |
| **FJ1442** | Vastus lateralis | Cơ rộng ngoài | `thigh_r` $\to$ `calf_r` | 0.80 / 0.20 | --- |
| **FJ1443** | Vastus medialis | Cơ rộng trong | `thigh_r` $\to$ `calf_r` | 0.75 / 0.25 | --- |

---

### 4. LỚP DA MAKEHUMAN TOÀN THÂN (SKINNED MESH)

- **Mesh:** `HumanBody` (19.158 vertices, 38.312 polygons).
- **Trọng số:** Gán đầy đủ cho 52 nhóm đỉnh tương ứng 53 xương canonical từ `weights.game_engine.json`.
- **Morph Targets (7 Targets):**
  1. `Height`: Tăng giảm chiều cao nhân vật.
  2. `Proportions`: Tỷ lệ hình thể người trẻ tuổi.
  3. `ShoulderWidth`: Chiều rộng hai vai.
  4. `ArmLength`: Độ dài hai cánh tay.
  5. `LegLength`: Độ dài hai cẳng chân.
  6. `Broader`: Tăng bề ngang cơ bắp thân mình và đai vai.
  7. `Slender`: Thu gọn chu vi vòng eo và các chi theo vóc dáng mảnh mai.
