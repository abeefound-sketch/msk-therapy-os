# MSK-THERAPY-OS V1.3 — TÀI LIỆU KỸ THUẬT SỐ 04
## SIMULTANEOUS MULTI-SEGMENT MOTION & MORPH-AWARE VERIFICATION

- **Phân loại:** Kỹ thuật / Kiểm thử tích hợp toàn thân (ENGINEERING_RESEARCH_ONLY)
- **Hiệu lực y sinh:** CHƯA XÁC LẬP (CLINICAL_VALIDATION = NOT_ESTABLISHED)
- **Mục tiêu:** Kiểm chứng tính toàn vẹn hình học khi điều khiển đồng thời vận động chi trên (tay), chi dưới (chân), thân mình (cột sống) kết hợp biến dạng thể trạng (Morphing).

---

### 1. THỬ NGHIỆM VẬN ĐỘNG ĐỒNG THỜI (SIMULTANEOUS ARM & LEG MOTION)

Trong các hệ thống đồ họa cũ hoặc phiên bản V1.2.1, cánh tay và chân chỉ được thử nghiệm riêng biệt. Trong V1.3, chúng tôi kích hoạt đồng thời toàn bộ chuỗi động học trên cùng một armature 53 bones:
- **Gập khuỷu tay phải:** $\theta_{\text{elbow}} = 90.0^\circ$ (`lowerarm_r.rotation.x = +1.5708 rad`).
- **Gập khớp gối phải:** $\theta_{\text{knee}} = 60.0^\circ$ (`calf_r.rotation.x = +1.0472 rad`).
- **Xoay thân mình:** $\theta_{\text{torso}} = 15.0^\circ$ (`spine_02.rotation.z = +0.2618 rad`).

#### Kết quả đo đạc thời gian thực từ evaluated geometry:
- **Chi trên:**
  * Cơ nhị đầu co ngắn: **$-23.2\%$** (từ $0.3150\text{ m}$ xuống $0.2420\text{ m}$).
  * Bụng cơ nhị đầu phồng to: **$+14.1\%$** (đường kính đạt $47.9\text{ mm}$).
  * Mốc huyệt Hợp Cốc (LI4) nâng cao: **$+0.280\text{ m}$**.
  * Khe khớp khuỷu: **$2.40\text{ mm}$**, độ xuyên thấu: **$0.00\text{ mm}$**.
- **Chi dưới:**
  * Cơ tứ đầu đùi giãn dài: **$+8.9\%$** (từ $0.4400\text{ m}$ lên $0.4790\text{ m}$).
  * Gót chân dịch chuyển lùi: **$-0.353\text{ m}$**, nâng cao: **$+0.204\text{ m}$**.
  * Mốc huyệt Túc Tam Lý (ST36) chuyển động theo mâm chày, nâng cao: **$+0.041\text{ m}$**.
  * Khe khớp gối: **$3.00\text{ mm}$**, độ xuyên thấu: **$0.00\text{ mm}$**.
- **Tính ổn định của lớp da:** Lớp da MakeHuman toàn thân co giãn mượt mà theo cả ba phân đoạn mà không xảy ra rách lưới, xé đỉnh hay biến dạng cục bộ.
- **Minh chứng ảnh chụp:** [`1docs/product_v13/evidence/v13_04_simultaneous_arm_leg_motion.png`](file:///D:/5Projects/msk-therapy-os/1docs/product_v13/evidence/v13_04_simultaneous_arm_leg_motion.png).

---

### 2. THỬ NGHIỆM BIẾN DẠNG VÓC DÁNG (MORPH-AWARE REGISTRATION)

Hệ thống được kích hoạt đồng thời 2 Shape Keys trong khi nhân vật đang ở tư thế vận động gập tay 90° và gập gối 60°:
- `Broader = 0.8`: Tăng thể tích cơ bắp thân mình, đai vai và chu vi các chi thêm $+16\%$.
- `LegLength = 0.5`: Kéo dài phân đoạn cẳng chân thêm $+5\%$.

#### Kết quả quan sát:
1. **Lớp da MakeHuman:** Nở rộng đồng tâm, bao bọc toàn bộ khối cơ nhị đầu đang co và khối cơ tứ đầu đang gập gối. Không có bất kỳ tam giác cơ nào đâm xuyên qua da ($0\text{ vertex penetration}$).
2. **Đường kinh 3D:** Cả 2 ống kinh lạc (Kinh Đại Trường màu vàng ở tay và Kinh Vị màu xanh ở chân) tự động dạt ra theo bề mặt mới của vóc dáng vận động viên mà không bị cắt chìm vào trong mô mỡ/da.
3. **Minh chứng ảnh chụp:** [`1docs/product_v13/evidence/v13_07_morph_broader_fullbody_motion.png`](file:///D:/5Projects/msk-therapy-os/1docs/product_v13/evidence/v13_07_morph_broader_fullbody_motion.png).

---

### 3. THỬ NGHIỆM LƯU VÀ KHÔI PHỤC DỰ ÁN (PROJECT PERSISTENCE)

Hệ thống tiến hành chu trình tuần hoàn:
1. Gửi lệnh lưu dự án qua `POST /api/character/v13/project/save` với payload trạng thái đồng thời.
2. Gọi hàm `resetPose()` đưa toàn bộ các khớp về $0.0^\circ$ và toàn bộ morph về $0.0$.
3. Gửi lệnh nạp lại qua `GET /api/character/v13/project/load`.
4. Toàn bộ các góc quay (`lowerarm_r = 90.0`, `calf_r = 60.0`, `Broader = 0.8`), 5 lớp hiển thị và tọa độ mốc huyệt được khôi phục chính xác $100\%$ không suy hao.
5. **Minh chứng ảnh chụp:** [`1docs/product_v13/evidence/v13_08_project_state_restored.png`](file:///D:/5Projects/msk-therapy-os/1docs/product_v13/evidence/v13_08_project_state_restored.png).

---

### 4. THỬ NGHIỆM ĐẶT LẠI THẾ NGHỈ (RESET REST POSE)

- Nhấp nút "Đặt lại (Reset Pose)": Toàn bộ xương, cơ và da trở về tư thế giải phẫu chuẩn đứng thẳng $0.0^\circ$.
- Chiều dài Biceps phục hồi: $0.3150\text{ m}$ ($\pm 0.000\text{ m}$).
- Chiều dài Quadriceps phục hồi: $0.4400\text{ m}$ ($\pm 0.000\text{ m}$).
- Không rò rỉ bộ nhớ Three.js (Peak Heap duy trì an toàn $< 65\text{ MB}$).
- **Minh chứng ảnh chụp:** [`1docs/product_v13/evidence/v13_10_final_verified_rest_pose.png`](file:///D:/5Projects/msk-therapy-os/1docs/product_v13/evidence/v13_10_final_verified_rest_pose.png).
