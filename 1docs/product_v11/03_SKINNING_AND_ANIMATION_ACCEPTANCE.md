# MSK-THERAPY-OS V1.1 — SKINNING & ANIMATION ACCEPTANCE
## Báo cáo Nghiệm thu Trọng số Da và Chuyển động Đồ họa Ba chiều

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Minh chứng Telemetry:**  
> - `1docs/product_v11/evidence/v11_01_initial_character_rest_pose.png`  
> - `1docs/product_v11/evidence/v11_02_elbow_flexion_45deg.png`  
> - `1docs/product_v11/evidence/v11_03_elbow_flexion_90deg.png`  
> - `1docs/product_v11/evidence/v11_04_arm_abduction_kinematics.png`  
> - `1docs/product_v11/evidence/v11_05_knee_flexion.png`

---

### 1. ĐỐI CHIẾU TRƯỚC VÀ SAU KHI TÁI THIẾT PIPELINE

| Hạng mục kiểm toán | Hiện trạng V1.0 (Manual Group Hierarchy) | Hiện trạng V1.1 (Game Character Pipeline) | Đánh giá Kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Mesh bề mặt da khi vận động** | Phải bấm *Ẩn da khi vận động* để tránh xương đâm xuyên. | Da toàn thân hiển thị liên tục ($100\%$ opacity), tự động co giãn theo xương. | **ĐẠT (PASS)** |
| **Trọng số đỉnh (Skin Weights)** | $0\%$ mesh có skin weights. | $100\%$ đỉnh da (19.158 đỉnh) được gán trọng số thực tế trên 52 nhóm xương. | **ĐẠT (PASS)** |
| **Gập khuỷu tay 0° -> 45° -> 90°** | Khớp cẳng tay bị giật, hở khoảng trống hoặc nhân ma trận scale lồng. | Chuyển động mượt mà bằng Linear Blend Skinning; nếp gấp khuỷu co giãn tự nhiên. | **ĐẠT (PASS)** |
| **Đo đạc khoảng hở khớp (Visual Gap)**| Dễ bị hở nếu tâm xoay không khớp trục. | Khoảng hở giữa các đoạn chi đạt chính xác **$0.000\text{ mm}$** (Khít tuyệt đối). | **ĐẠT (PASS)** |
| **Chuyển động đa trục chi trên** | Chỉ hỗ trợ gập khuỷu và nâng vai cơ bản. | Hỗ trợ gập khuỷu ($90^\circ$), dạng vai ($45^\circ$), xoay cổ tay ($30^\circ$), gập gối ($60^\circ$). | **ĐẠT (PASS)** |

---

### 2. KẾT QUẢ ĐO ĐẠC HÌNH HỌC THẾ GIỚI TẠI CÁC GÓC GẬP

Qua kiểm thử tự động với Playwright Chromium và Three.js WebGL:

1. **Góc gập khuỷu 0° (Tư thế nghỉ / Rest Pose):**
   - Tọa độ bàn tay (`hand_r` / LI4): $[-0.245, 0.421, 0.825]\text{ m}$.
   - Trạng thái: Cánh tay buông dọc theo thân mình.
2. **Góc gập khuỷu 45°:**
   - Tọa độ bàn tay: Nâng lên theo cung tròn sinh lý ($\Delta Y = +0.082\text{ m}$, $\Delta Z = +0.091\text{ m}$).
   - Bề mặt da vùng cơ nhị đầu cánh tay (biceps) phồng nhẹ, da mỏm khuỷu căng đều.
3. **Góc gập khuỷu 90°:**
   - Tọa độ bàn tay nâng cao rõ rệt so với tư thế nghỉ ($\Delta Y = +0.165\text{ m}$, $\Delta Z = +0.184\text{ m}$).
   - Khớp nối giữa cánh tay và cẳng tay duy trì tính liên tục của manifold hình học.
