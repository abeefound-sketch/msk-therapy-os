# MSK-Therapy-OS — Milestone P24 Audit
## P24_02: Camera Observability Matrix & Degrees-of-Freedom Boundaries

**Tài liệu ID:** `MSK-P24-AUD-002`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Ma trận Khả năng Quan sát (Observability Matrix)

Camera đơn (Monocular 2D/3D) không đủ khả năng toán học để quan sát toàn bộ các bậc tự do (DOFs) cơ sinh học của chi trên. Hệ thống thiết lập bảng ma trận khả năng quan sát bắt buộc:

| Bậc Tự Do Khớp (Joint DOF) | Trạng thái Quan sát | Chỉ số Mốc MediaPipe | Yếu tố Tin cậy & Hạn chế Vật lý | Quyết định Xử lý |
|---|---|---|---|---|
| **Gập / Duỗi Khớp Khuỷu (Elbow Flexion/Extension)** | $$\mathbf{OBSERVABLE}$$ | 12 (Vai), 14 (Khuỷu), 16 (Cổ tay) | Góc giữa 2 vector $\vec{V}_{\text{arm}}$ và $\vec{V}_{\text{forearm}}$ tính được ổn định khi cả 3 điểm nhìn thấy rõ (`visibility > 0.5`). | Giải góc và đưa qua bộ kẹp Kapandji $[0^\circ, 145^\circ]$. |
| **Nâng / Khép Vai (Shoulder Elevation/Adduction)** | $$\mathbf{OBSERVABLE}$$ | 12 (Vai), 24 (Hông), 14 (Khuỷu) | Góc nâng cánh tay so với trục thân người. Bị ảnh hưởng bởi góc quay của ngực. | Giải góc thô và đối chiếu OpenSim Seth model. |
| **Xoay Sấp / Ngửa Cẳng Tay (Forearm Pronation/Supination)** | $$\mathbf{UNOBSERVABLE}$$ | 14 (Khuỷu), 16 (Cổ tay) | Đường thẳng nối 2 điểm khuỷu-cổ tay **không có thông tin quay quanh trục dọc** trong ảnh phẳng. Mốc ngón tay bị nhiễu lớn khi quay. | **Ghi nhận `UNOBSERVABLE`. TUYỆT ĐỐI KHÔNG tự suy đoán góc xoay.** |
| **Chiều Sâu Không Gian (Monocular Depth Z)** | $$\mathbf{ESTIMATED\_UNCERTAIN}$$ | Toàn bộ 33 điểm | Ước tính chiều sâu từ camera đơn bị mơ hồ tỷ lệ (Scale ambiguity). Phụ thuộc vào kích thước người mặc định. | Đánh nhãn `ESTIMATED_UNCERTAIN`. Không dùng để đo khoảng cách lâm sàng. |
| **Gập / Duỗi Cổ Tay (Wrist Flexion/Extension)** | $$\mathbf{PARTIAL\_RECONSTRUCTION}$$ | 16 (Cổ tay), 18/20 (Ngón) | Bị che khuất thường xuyên khi bàn tay nắm hoặc quay ngang. | Chỉ ước lượng khi độ tin cậy ngón tay $> 0.8$. |

---

### 2. Xử lý Che khuất (Occlusion Handling - Fail-Closed)

Khi một mốc giải phẫu bị che khuất (ví dụ: cẳng tay bị khuất sau lưng hoặc đồ vật trong 15 frames liên tiếp, `visibility < 0.5`):
- Hệ thống phát tín hiệu `RIGHT_ARM_OCCLUSION_DETECTED`.
- Bác bỏ tính toán góc và trả về:
  $$\text{status} = \mathbf{REJECTED\_DUE\_TO\_OCCLUSION},\quad \theta_{\text{elbow}} = \mathbf{None}$$
- **Nghiêm cấm tự sinh tư thế giả (No fake pose interpolation) khi mất dấu vết quan sát thực tế.**
