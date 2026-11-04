# MSK-THERAPY-OS V1.2.1 — BÁO CÁO KIỂM TOÁN THỰC TẾ ABS V1.2
## INDEPENDENT ENGINEERING REALITY AUDIT (GATE G1 & G2)

> [!IMPORTANT]
> **Phạm vi thẩm định:** `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`  
> **Xác thực lâm sàng:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Nguyên tắc cốt lõi:** *"Không tự dùng số liệu từ chính thuật toán làm bằng chứng kiểm định sinh học."*  
> **Mục tiêu V1.2.1:** Đối chiếu mọi tuyên bố trong V1.2 với mã nguồn, tệp GLB và runtime Three.js thực tế; khắc phục triệt để các khoảng trống về hình học đo đạc, da MakeHuman và góc gập $120^\circ$.

---

## 1. ĐỐI CHIẾU 7 HẠNG MỤC KIỂM TOÁN THỰC TẾ

| STT | Hạng mục kiểm toán | Hiện trạng thực tế tại V1.2 | Đánh giá & Phát hiện kỹ thuật | Biện pháp khắc phục V1.2.1 |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Nguồn gốc 6 cơ bắp** | Đã trích xuất từ `body-3.bin` và `body-4.bin` của BodyParts3D 4.0 (CC BY 4.0 DBCLS Japan) | **XÁC MINH: ĐẠT**. Các tệp OBJ và SHA256 khớp với `atlas.json`. | Giữ nguyên tệp nguồn, chuẩn hóa siêu dữ liệu điểm bám nguyên ủy và bám tận. |
| **2** | **Cấu trúc 4 bones & Canonical Rig** | `clavicle_r`, `upperarm_r`, `lowerarm_r`, `hand_r` lấy từ `rig.game_engine.json` | **XÁC MINH: ĐẠT**. Cây phân cấp và hướng xoay khớp đồng bộ với MakeHuman. | Giữ nguyên làm khung xương điều khiển duy nhất cho toàn bộ hệ thống. |
| **3** | **Cơ chế Dual-Bone Skinning** | Gán vertex weights phân vùng chuyển tiếp cho cơ nhị đầu và cơ tam đầu | **XÁC MINH: ĐẠT MỘT PHẦN**. Trọng số tồn tại trong GLB nhưng chưa đo độ căng/gập thực tế của từng cụm đỉnh. | Đo đạc tọa độ thế giới của đỉnh nguyên ủy và bám tận qua forward kinematics thực. |
| **4** | **Biến dạng Biceps_Bulge** | Shape Key `Biceps_Bulge` có trong GLB, nhưng số liệu co $23.17\%$ và phồng $1.141$ trong HUD được tính từ công thức giải tích | **PHÁT HIỆN: THIẾU KIỂM CHỨNG HÌNH HỌC THỰC TẾ**. Số liệu hiển thị chỉ là giá trị lý thuyết, chưa đo từ bounding box hoặc bán kính đỉnh thật của mesh. | Thay thế bằng bộ đo hình học thực tế (`GeometryEvaluator`): đo khoảng cách đỉnh thế giới và đường kính ngang bụng cơ thật. |
| **5** | **Khoảng hở khớp (Joint Gap 0 mm)** | Hàm `getJointGapMm()` trả về giá trị cố định `0.0` dựa trên suy diễn toán học của rig | **PHÁT HIỆN: CHƯA ĐO TRÊN MESH**. Khoảng cách thực giữa lồi cầu xương cánh tay và diện khớp xương quay/trụ chưa được đo bằng khoảng cách bề mặt. | Đo khoảng cách thực tế giữa các đỉnh tiếp khớp của Humerus và Radius/Ulna. |
| **6** | **Da MakeHuman trong demo** | Tệp `rigged_arm_anatomy_v12.glb` sử dụng khối hình trụ procedurally `ArmSkin`, KHÔNG PHẢI da MakeHuman thật | **PHÁT HIỆN: SAI LỆCH VỚI PIPELINE MAKEHUMAN**. V1.1 có da MakeHuman nhưng V1.2 arm asset đã dùng cylinder thay thế để xuất nhanh. | **BẮT BUỘC SỬA**: Trích xuất da chi trên thật từ MakeHuman `base.obj` kèm đầy đủ 4 nhóm trọng số da và các Shape Keys biến đổi hình thể (morph targets). |
| **7** | **Góc gập khuỷu $120^\circ$** | V1.2 chỉ kiểm thử đến $90^\circ$, slider và animation bị giới hạn ở $90^\circ$ | **PHÁT HIỆN: CHƯA ĐẠT BIÊN ĐỘ GẬP SÂU**. Cần mở rộng lên $120^\circ$ (nằm trong ROM sinh lý $145^\circ$) để kiểm tra độ xuyên thấu mô mềm. | Mở rộng animation, slider và kiểm thử Playwright lên đủ 4 mốc: $0^\circ, 45^\circ, 90^\circ, 120^\circ$. |

---

## 2. KẾ HOẠCH HÀNH ĐỘNG V1.2.1

1. **Xây dựng tài sản 3D tích hợp hoàn chỉnh (`rigged_arm_anatomy_v12_1.glb`):**
   - Khung xương: 4 bones (`clavicle_r`, `upperarm_r`, `lowerarm_r`, `hand_r`).
   - Da: Trích xuất trực tiếp từ MakeHuman `base.obj` (1.899 đỉnh chi trên, 2.009 mặt) với các morph targets: `ArmLength`, `ShoulderWidth`, `Broader`, `Slender`.
   - Xương: 5 xương BodyParts3D (`Humerus`, `Radius`, `Ulna`, `Metacarpal_2`, `Clavicle`).
   - Cơ: 6 cơ BodyParts3D (`Biceps long/short`, `Triceps lateral/long/medial`, `Brachialis`) có Dual-Bone Skinning và Shape Key `Biceps_Bulge`.
   - Chuyển động: 4 mốc $0^\circ \to 45^\circ \to 90^\circ \to 120^\circ \to 0^\circ$.
2. **Xây dựng module đo hình học thực nghiệm (`GeometryEvaluator`):**
   - Đo khoảng cách đỉnh thực giữa Origin và Insertion.
   - Đo bề dày/đường kính ngang thực của bụng cơ.
   - Đo khoảng hở và kiểm tra va chạm giữa các bề mặt xương.
   - Kiểm tra tính bất biến chiều dài thân xương (Rigid Invariance $\Delta L < 0.1\text{ mm}$).
3. **Tích hợp Đường kinh Thủ Dương Minh Đại Trường (LI Meridian):**
   - Chuỗi điểm đường kinh 3D gắn trên bề mặt da và biến dạng đồng bộ khi gập cánh tay.
4. **Cập nhật giao diện Studio Three.js tại `/character_v12_1/index.html`:**
   - Đầy đủ nút bật/tắt từng lớp: Xương, Cơ, Da, Huyệt, Đường kinh.
   - Điều khiển gập khuỷu $0^\circ \to 120^\circ$.
   - Điều khiển morph vóc dáng.
   - Chỉnh sửa mốc huyệt, lưu/mở lại trạng thái JSON.
   - Đo FPS thực tế.
5. **Kiểm thử Playwright E2E tự động:**
   - Xác minh các giá trị đo hình học thực tế tại cả 4 góc $0^\circ, 45^\circ, 90^\circ, 120^\circ$.
   - Thu thập 10 ảnh chụp bằng chứng thực nghiệm trong thư mục `evidence/`.
