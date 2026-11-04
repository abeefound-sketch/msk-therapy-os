# MSK-THERAPY-OS V1.1 — CHARACTER PIPELINE SPECIFICATION
## Quy trình Tạo và Xuất Nhân vật 3D Hoàn chỉnh (Rigged & Skinned Humanoid)

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Tài sản tạo lập:**  
> - `research/character_pipeline/rigged_human_v11.blend`  
> - `research/character_pipeline/rigged_human_v11.glb` (16.49 MB)

---

### 1. KIẾN TRÚC NHÂN VẬT NGƯỜI (HUMANOID ARCHITECTURE)

Nhân vật người V1.1 được xây dựng từ quy trình nguồn mở MakeHuman kết hợp công cụ biên tập Blender 3.6 LTS, giải quyết triệt để vấn đề "da tĩnh, xương rời" của V1.0.

```
HumanArmature (THREE.Skeleton / 53 Bones)
  └── Root (0.00, 0.00, 0.00)
        └── pelvis (0.00, -0.01, 0.06)
              ├── spine_01 -> spine_02 -> spine_03 -> neck_01 -> head
              │     ├── clavicle_l -> upperarm_l -> lowerarm_l -> hand_l -> (fingers)
              │     └── clavicle_r -> upperarm_r -> lowerarm_r -> hand_r -> (fingers)
              ├── thigh_l -> calf_l -> foot_l -> ball_l
              └── thigh_r -> calf_r -> foot_r -> ball_r
```

- **Lớp Da Liền Mạch (Full Body Manifold):**
  - Tên đối tượng: `HumanBody`
  - Đỉnh hình học: 19.158 đỉnh (quand-dominant topology, không có đường nối rách hay cạnh hở).
  - Đa giác: 18.486 mặt.
  - Tỷ lệ cơ thể: Chiều cao chuẩn nhân trắc học người trưởng thành $1.695\text{ m}$ (Z từ $-0.845\text{ m}$ đến $+0.850\text{ m}$), sải tay $1.650\text{ m}$, bề rộng vai $0.440\text{ m}$.
  - Vật liệu: `M_HumanSkin` (Principled BSDF, Base Color RGB `[0.80, 0.65, 0.55]`, Roughness `0.45`).

---

### 2. PHÂN BỔ TRỌNG SỐ DA (SKIN WEIGHTS & VERTEX GROUPS)

Khác với V1.0 không có bất kỳ trọng số nào, nhân vật V1.1 sở hữu 52 nhóm đỉnh (Vertex Groups) được gán trọng số thực tế từ `weights.game_engine.json`:
- **Khớp khuỷu tay phải (`lowerarm_r` & `upperarm_r`):** Vùng da khuỷu tay được nội suy trọng số mượt mà giữa đầu dưới xương cánh tay và đầu trên cẳng tay. Khi gập góc từ $0^\circ$ đến $90^\circ$, bề mặt da co lại tự nhiên ở nếp gấp phía trước và căng đều ở mỏm khuỷu phía sau.
- **Khớp vai phải (`upperarm_r` & `clavicle_r`):** Vùng cơ delta và nách duy trì thể tích khi cánh tay dạng ra xa thân mình, không bị thắt cổ chai (candy-wrapper artifact) hay tách rời khỏi lồng ngực.
- **Khớp gối phải (`calf_r` & `thigh_r`):** Da bánh chè và khoeo chân biến dạng đồng bộ, giữ liên kết với đùi và cẳng chân.

---

### 3. HÌNH THỂ THAM SỐ (PARAMETRIC MORPH TARGETS / SHAPE KEYS)

Được tích hợp trực tiếp vào tệp GLB dưới dạng 6 Shape Keys (Morph Targets) tương thích GPU Three.js:
1. `Height`: Thay đổi chiều cao tổng thể theo phân bố nhân trắc học MakeHuman (19.150 đỉnh biến dạng).
2. `Proportions`: Điều chỉnh tỷ lệ cơ thể lý tưởng / thường gặp (9.378 đỉnh biến dạng).
3. `ShoulderWidth`: Thay đổi độ rộng khung vai từ mỏm cùng vai trái sang phải (5.568 đỉnh biến dạng).
4. `WaistCircumference`: Điều chỉnh vòng eo và độ dày vùng bụng (1.518 đỉnh biến dạng).
5. `ArmLength`: Tăng giảm chiều dài đoạn chi cánh tay và cẳng tay (1.394 đỉnh biến dạng).
6. `LegLength`: Tăng giảm chiều dài đùi và cẳng chân (4.518 đỉnh biến dạng).

---

### 4. BỘ CHUYỂN ĐỘNG THỰC NGHIỆM (ANIMATION TRACKS)

Tệp GLB nhúng sẵn chuỗi chuyển động chuẩn `A_HumanoidMotion` gồm 180 khung hình ($6.0\text{ s}$ tại $30\text{ FPS}$):
- **Frame 1:** Tư thế nghỉ (Rest Pose / Anatomical A-Pose, $0^\circ$).
- **Frame 30:** Gập khuỷu tay $45^\circ$ (`lowerarm_r` quay quanh trục X cục bộ $+45^\circ$).
- **Frame 60:** Gập khuỷu tay $90^\circ$ (`lowerarm_r` quay quanh trục X cục bộ $+90^\circ$).
- **Frame 90:** Dạng khớp vai $45^\circ$ kết hợp gập khuỷu $45^\circ$ (`upperarm_r` quay Z $-45^\circ$).
- **Frame 120:** Gập khớp gối phải $60^\circ$ (`calf_r` quay X $+60^\circ$).
- **Frame 150:** Vặn thân mình $20^\circ$ (`spine_02`) và xoay cổ tay $30^\circ$ (`hand_r`).
- **Frame 180:** Hoàn nguyên toàn bộ chuỗi khớp về tư thế giải phẫu chuẩn ($0^\circ$).

---

### 5. KIỂM CHỨNG VÒNG LẶP (ROUND-TRIP VERIFICATION)

Đã kiểm chứng nạp ngược tệp `rigged_human_v11.glb` vào phiên làm việc mới của Blender:
- Cấu trúc Armature: 53 xương được nhận diện chính xác.
- Khối hình học: 73.944 đỉnh render (sau khi tam giác hóa và nhân bản đỉnh tại UV seam của GLTF exporter), giữ nguyên vẹn 53 Vertex Groups.
- Toàn bộ 6 Shape Keys và Action `A_HumanoidMotion_HumanArmature` được giữ nguyên vẹn 100%.
