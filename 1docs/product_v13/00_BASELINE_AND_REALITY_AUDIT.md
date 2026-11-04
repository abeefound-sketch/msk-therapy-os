# MSK-THERAPY-OS V1.3 — TÀI LIỆU KIỂM TOÁN HIỆN TRẠNG SỐ 00
## BASELINE & REALITY AUDIT: UNIVERSAL ANATOMICAL BINDING SYSTEM

- **Môi trường thực tế:** Windows 11, Blender 3.6 LTS, Three.js WebGL 2.0, Python 3.11 sidecar, CPU Intel Core i7-5600U, GPU Intel HD Graphics 5500, RAM 8 GB.
- **Ranh giới pháp lý & chuyên môn:** `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`, `CLINICAL_VALIDATION = NOT_ESTABLISHED`.
- **Mục tiêu kiểm toán:** Rà soát toàn bộ mã nguồn ABS V1.2.1, xác định các điểm còn hardcoded cho chi trên, khảo sát tài nguyên giải phẫu chi dưới sẵn có trong BodyParts3D và thiết lập cơ sở dữ liệu chuyển đổi sang hệ thống Universal ABS.

---

### 1. KẾT QUẢ ĐỐI CHIẾU THỰC TRẠNG THEO 7 CÂU HỎI CỐT LÕI

#### Câu hỏi 1: Mã nguồn ABS hiện tại có thực sự generic hay còn hardcoded cho cánh tay?
- **Thực tế:**
  - Lớp `CanonicalSkeletonAdapter` ([`canonical_skeleton_adapter.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/canonical_skeleton_adapter.py)) đã có hợp đồng chuẩn cho toàn bộ 53 xương của nhân vật MakeHuman (`pelvis`, `spine_01`, `spine_02`, `neck`, `head`, `thigh_l/r`, `calf_l/r`, `foot_l/r`, `upperarm_l/r`, `lowerarm_l/r`, `hand_l/r`).
  - Tuy nhiên, các adapter liên kết trong `msk_therapy_os/anatomical_binding/`:
    * [`rigid_bone_binding.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_binding/rigid_bone_binding.py): Phương thức `_init_canonical_bindings()` đang hardcoded 5 xương chi trên (`FJ3368` Humerus, `FJ3349` Radius, `FJ3391` Ulna, `FJ3352` Metacarpal 2, `FJ3343` Clavicle).
    * [`muscle_deformation_binding.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_binding/muscle_deformation_binding.py): Đang hardcoded 6 cơ chi trên (`FJ1478`, `FJ1512`, `FJ1477`, `FJ1479`, `FJ1480`, `FJ1486`), hàm `evaluate_state(elbow_flexion_deg)` cố định tham số góc khuỷu.
    * [`surface_anchor_binding.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_binding/surface_anchor_binding.py): Đang hardcoded 4 huyệt thuộc kinh Đại Trường trên cánh tay (`LI4`, `LI11`, `LI14`, `LI15`).
    * [`kinematic_chain_coordinator.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_binding/kinematic_chain_coordinator.py): Đang chuyên biệt hóa thành `ArmKinematicState` với các trường dành riêng cho cánh tay (`elbow_flexion_deg`, `biceps_shortening_pct`, `hand_elevation_delta_m`).
- **Kết luận:** Lõi ABS cần được tổng quát hóa (generalized) thành **Universal ABS Core**: chuyển các định nghĩa cấu trúc giải phẫu thành **Declarative Configuration** (schema JSON/Python chuẩn) và tái sử dụng thuật toán tính biến dạng chung cho bất kỳ khớp nào (khuỷu tay, gối, hông, vai).

#### Câu hỏi 2: Hệ thống có sử dụng một skeleton duy nhất không?
- **Thực tế:**
  - Trong V1.1, toàn bộ cơ thể người được gắn vào khung xương 53 xương `HumanArmature` (`rigged_human_v11.glb`).
  - Trong V1.2 và V1.2.1, để kiểm chứng kỹ thuật giải phẫu co phồng cơ, chúng tôi đã trích xuất phân đoạn cánh tay 4 xương (`clavicle_r`, `upperarm_r`, `lowerarm_r`, `hand_r`) trong `rigged_arm_anatomy_v12_1.glb`.
- **Kết luận:** Trong V1.3, bắt buộc **quy tụ về một khung xương duy nhất (Single Canonical Humanoid Skeleton 53 xương)**. Không tạo 2 rig riêng biệt cho tay và chân.

#### Câu hỏi 3: Binding của cơ, xương và skin có thể tái sử dụng không?
- **Thực tế:**
  - Thuật toán Rigid Bone Binding (nhân ma trận cha con 4x4, tính ma trận nghịch đảo $M_{\text{inv}}$) là toán học tổng quát, áp dụng được cho bất kỳ xương nào.
  - Thuật toán Dual-Bone Muscle Skinning kết hợp bảo toàn thể tích đẳng tích ($k_{\text{bulge}} = \sqrt{L_{\text{rest}} / L_{\text{curr}}}$) hoàn toàn có thể áp dụng tương đương cho cơ tứ đầu đùi (Quadriceps femoris) vắt qua khớp gối từ xương đùi/hông xuống xương chày/bánh chè.
  - Trọng số Linear Blend Skinning của da MakeHuman đã được MakeHuman gán sẵn cho toàn bộ 53 xương trong `weights.game_engine.json`.
- **Kết luận:** Các thuật toán lõi có tính tái sử dụng cao, chỉ cần tách biệt logic tính toán khỏi dữ liệu cụ thể.

#### Câu hỏi 4: Những thành phần nào thực sự chạy trong Three.js?
- **Thực tế:**
  - `THREE.SkinnedMesh` với `THREE.Skeleton` và ma trận xương (`bone.matrixWorld`).
  - `THREE.Mesh` dạng Rigid Object làm con của `THREE.Bone`.
  - `morphTargetInfluences` cho biến dạng cơ bắp và vóc dáng da.
  - `THREE.CatmullRomCurve3D` kết hợp `THREE.TubeGeometry` tái tạo đường kinh động học thời gian thực.
  - `THREE.OrbitControls` cho phép thao tác chuột xoay, zoom, pan mượt mà.
  - Đã kiểm chứng chạy ổn định trên WebGL/Chromium.

#### Câu hỏi 5: Có bao nhiêu cấu trúc giải phẫu đã được registration?
- **Thực tế V1.2.1:**
  - Xương: 5 (Clavicle, Humerus, Radius, Ulna, Metacarpal II).
  - Cơ: 6 (Biceps long/short, Triceps lateral/long/medial, Brachialis).
  - Huyệt vị: 4 (LI4, LI11, LI14, LI15).
  - Lớp da: 1 (ArmSkin_MakeHuman).
- **Kế hoạch mở rộng V1.3:**
  - Thêm Xương chi dưới: 4 (Femur, Tibia, Fibula, Patella).
  - Thêm Cơ chi dưới: 4 (Rectus femoris, Vastus lateralis, Vastus medialis, Vastus intermedius).
  - Thêm Huyệt vị chi dưới: 2 (ST36 Túc tam lý, KI3 Thái khê).
  - Lớp da toàn thân: 1 (HumanBody full MakeHuman với 53 xương).

#### Câu hỏi 6: Morphing có làm thay đổi anatomical mapping không?
- **Thực tế:**
  - Các Shape Keys của MakeHuman (`Height`, `Proportions`, `ShoulderWidth`, `WaistCircumference`, `ArmLength`, `LegLength`) làm dịch chuyển các đỉnh lưới da theo các vector delta.
  - Khi xương bên trong là Rigid Bodies bám theo các mấu xương của Armature, nếu Armature không thay đổi chiều dài xương thì thể tích da có thể co thắt hoặc phình rộng quanh xương.
  - Do đó, Universal ABS cần hỗ trợ chiến lược `MORPH_AWARE_REGISTRATION`: khi vóc dáng thay đổi, hệ thống tính toán lại vị trí bề mặt (surface anchors) theo tọa độ tam giác (barycentric coordinates) để huyệt vị bám chính xác trên mặt da mới.

#### Câu hỏi 7: Đã có những asset chi dưới nào trong BodyParts3D hiện hành?
- **Kiểm tra trực tiếp tại `3refs/upstream/tcm-3d/public/models/atlas.json` và các tệp nhị phân `body-*.bin`:**
  - **Xương chi dưới (Bones - Chunk 13):**
    * `FJ3365`: Right femur (Xương đùi phải) — 480 vertices.
    * `FJ3387`: Right tibia (Xương chày phải) — 496 vertices.
    * `FJ3366`: Right fibula (Xương mác phải) — 384 vertices.
    * `FJ3381`: Right patella (Xương bánh chè phải) — 176 vertices.
  - **Cơ chi dưới (Muscles - Chunk 1):**
    * `FJ1433`: Right rectus femoris (Cơ thẳng đùi phải) — 910 vertices.
    * `FJ1441`: Right vastus intermedius (Cơ rộng giữa phải) — 840 vertices.
    * `FJ1442`: Right vastus lateralis (Cơ rộng ngoài phải) — 1.091 vertices.
    * `FJ1443`: Right vastus medialis (Cơ rộng trong phải) — 784 vertices.
  - **Dây chằng bánh chè / Gân bánh chè (Patellar ligament / tendon):**
    * *Hiện trạng trong BodyParts3D:* Trong bộ dữ liệu DBCLS, gân cơ tứ đầu đùi bám liên tục vào cực trên xương bánh chè và tiếp nối thành dây chằng bánh chè bám vào lồi củ xương chày mà không có mesh riêng biệt mang mã FMA rời.
    * *Xử lý kỹ thuật trung thực:* Ghi nhận rõ ràng trạng thái `CONTINUOUS_WITH_QUADRICEPS_AND_PATELLA`, không tạo mesh giả mạo để tự nhận có asset độc lập.

---

### 2. KẾ HOẠCH HÀNH ĐỘNG TRIỂN KHAI V1.3

1. **Phase A:** Tái cấu trúc thư mục `msk_therapy_os/anatomical_binding/`:
   - Xây dựng schema khai báo cấu trúc chuẩn (`AnatomicalStructureDefinition`).
   - Cung cấp 5 chiến lược liên kết (`RIGID_BONE`, `MULTI_BONE_SKINNING`, `ATTACHMENT_DRIVEN_DEFORMATION`, `SURFACE_BARYCENTRIC`, `MORPH_AWARE_REGISTRATION`).
2. **Phase B & C:**
   - Trích xuất 4 xương (`FJ3365`, `FJ3387`, `FJ3366`, `FJ3381`) và 4 cơ chi dưới (`FJ1433`, `FJ1441`, `FJ1442`, `FJ1443`) thành OBJ có checksum SHA-256.
   - Đăng ký cấu trúc vào Universal ABS.
3. **Phase D:** Xây dựng tệp công cụ Blender `tools/build_rigged_human_v13.py` xuất bản `rigged_human_anatomy_v13.glb` toàn thân chứa:
   - 1 khung xương 53 bones.
   - Da MakeHuman toàn thân có 6 morph targets.
   - 9 xương BodyParts3D (5 chi trên + 4 chi dưới).
   - 10 cơ BodyParts3D (6 chi trên + 4 chi dưới).
   - 6 mốc huyệt (LI4, LI11, LI14, LI15, ST36, KI3) và 2 đường kinh uốn động 3D.
4. **Phase E – I:** Phát triển Web Atlas `/character_v13/index.html`, bộ kiểm thử Playwright tự động hóa, đo đạc hình học thực tế, ghi hình ảnh bằng chứng và ban hành bộ hồ sơ nghiệm thu.
