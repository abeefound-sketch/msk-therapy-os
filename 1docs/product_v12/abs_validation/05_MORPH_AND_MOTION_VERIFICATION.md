# MSK-THERAPY-OS V1.2.1 — TÀI LIỆU KỸ THUẬT SỐ 05
## SIMULTANEOUS MORPH & MOTION DUAL-VERIFICATION REPORT

- **Phân loại:** Kỹ thuật / Kiểm thử tích hợp đồ họa (ENGINEERING_RESEARCH_ONLY)
- **Mục tiêu:** Xác minh tính toàn vẹn hình học khi kết hợp đồng thời biến dạng thể trạng (Morphing) và động học chuyển động (Skeletal Forward Kinematics).
- **Phạm vi:** Chi trên phải (Arm Canonical Rig).

---

### 1. NGUYÊN LÝ KẾT HỢP DUAL-SYSTEM (MORPH + MOTION)

Trong các pipeline đồ họa nhân vật game tiêu chuẩn, việc kết hợp giữa biến dạng hình thể (Shape Keys / Morph Targets) và biến dạng chuyển động (Skeletal Skinning) thường dễ gặp các lỗi nghiêm trọng như:
- Xé rách mesh (vertex shearing).
- Xuyên thấu phi vật lý giữa các lớp giải phẫu (mesh clipping / Z-fighting).
- Mốc giải phẫu bị trôi lệch khỏi bề mặt cơ thể (anchor detachment).

MSK-Therapy-OS V1.2.1 xử lý vấn đề này bằng kiến trúc **Phân tầng độc lập nhưng tham chiếu chung**:
1. **Khung xương (Armature):** Điều khiển toàn bộ không gian tọa độ thế giới thông qua các ma trận biến đổi affine.
2. **Lớp xương cứng (BodyParts3D):** Giữ nguyên tỷ lệ 1:1, bám cứng vào các đốt xương cha.
3. **Lớp cơ bắp:** Biến dạng theo động học xương (Dual-Bone Skinning) đồng thời phồng thể tích qua Shape Key `Biceps_Bulge`.
4. **Lớp da nhân vật (MakeHuman):** Tiếp nhận cả 4 GPU Morph Targets (`ArmLength`, `ShoulderWidth`, `Broader`, `Slender`) kết hợp Linear Blend Skinning từ 4 khớp xương.
5. **Mốc huyệt và đường kinh:** Bám theo bề mặt da và ma trận xương cha thế giới.

---

### 2. KẾT QUẢ THỬ NGHIỆM ĐỒNG THỜI (TEST CASE 8: BROADER MORPH + 90° FLEXION)

Trong kịch bản kiểm thử tự động Playwright:
- Đặt góc gập khuỷu: $\theta = 90^\circ$ (`lowerarm_r.rotation.x = 1.5708 rad`).
- Kích hoạt hình thể vận động viên: `Broader = 0.8` (gia tăng bề ngang cơ bắp và chu vi cánh tay lên $+16\%$).
- Bật đồng thời 5 lớp hiển thị: Xương, Cơ bắp, Da, Huyệt vị, Đường kinh.

#### Kết quả quan sát và đo đạc:
- **Độ tương thích lớp da:** Da MakeHuman nở rộng đồng tâm bao bọc toàn bộ khối cơ nhị đầu và cơ tam đầu đang gập $90^\circ$. Không có bất kỳ tam giác cơ nào bị đâm xuyên qua bề mặt da (0 vertex penetration).
- **Hành vi đường kinh:** Ống kinh lạc màu vàng 3D tự động dạt ra theo bề mặt mới của cánh tay cơ bắp, giữ vững đường nối từ huyệt LI4 trên mu bàn tay qua LI11 ở nếp khuỷu đến LI14 và LI15 trên vai.
- **Minh chứng ảnh chụp Telemetry:** Đã ghi lại tại [`1docs/product_v12/abs_validation/evidence/v12_1_08_morphed_broader_flexion90.png`](file:///D:/5Projects/msk-therapy-os/1docs/product_v12/abs_validation/evidence/v12_1_08_morphed_broader_flexion90.png).

---

### 3. THỬ NGHIỆM LƯU TRỮ VÀ KHÔI PHỤC DỰ ÁN (PROJECT PERSISTENCE)

Hệ thống được kiểm tra khả năng serialization và khôi phục trạng thái hoàn chỉnh thông qua API REST và UI Studio:

1. **Gửi lệnh lưu dự án:**
   - POST `/api/character/v12/project/save` với payload JSON chứa:
     ```json
     {
       "project_name": "Arm_Flexion_90_Morph_Broader",
       "joint_angles": { "lowerarm_r": 90.0, "upperarm_r": 0.0 },
       "morph_influences": { "ArmLength": 0.0, "ShoulderWidth": 0.0, "Broader": 0.8, "Slender": 0.0 },
       "layer_visibility": { "bones": true, "muscles": true, "skin": true, "acupoints": true, "meridian": true }
     }
     ```
   - Server ghi nhận tệp lưu thành công tại `2data/character_v12_projects/project_Arm_Flexion_90_Morph_Broader.json`.
2. **Khôi phục dự án:**
   - Đặt lại toàn bộ giao diện về trạng thái mặc định (0° rest).
   - Gọi GET `/api/character/v12/project/load?name=Arm_Flexion_90_Morph_Broader`.
   - Kết quả: Toàn bộ góc quay, thanh trượt morph, trạng thái hiển thị 5 lớp và vị trí huyệt được khôi phục chính xác $100\%$.
   - **Minh chứng ảnh chụp:** [`1docs/product_v12/abs_validation/evidence/v12_1_09_project_state_restored.png`](file:///D:/5Projects/msk-therapy-os/1docs/product_v12/abs_validation/evidence/v12_1_09_project_state_restored.png).

---

### 4. THỬ NGHIỆM KHÔI PHỤC VỀ THẾ NGHỈ (RESET POSE)

Sau chuỗi kiểm thử vận động gập sâu $120^\circ$ và biến dạng vóc dáng, hàm `resetPose()` được gọi để đưa cánh tay về tư thế giải phẫu cơ bản:
- Góc gập khuỷu: Trở về $0.0^\circ$ ($\pm 0.0^\circ$).
- Toàn bộ trọng số morph: Trở về $0.0$.
- Chiều dài cơ nhị đầu: Phục hồi chính xác về $0.3150\text{ m}$.
- Đường kính bụng cơ: Trở về $42.0\text{ mm}$.
- Không phát hiện biến dạng dư thừa (residual distortion) hay rò rỉ bộ nhớ.
- **Minh chứng ảnh chụp:** [`1docs/product_v12/abs_validation/evidence/v12_1_10_final_verified_rest_pose.png`](file:///D:/5Projects/msk-therapy-os/1docs/product_v12/abs_validation/evidence/v12_1_10_final_verified_rest_pose.png).
