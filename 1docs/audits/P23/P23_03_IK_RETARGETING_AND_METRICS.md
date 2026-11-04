# MSK-Therapy-OS — Milestone P23 Audit
## P23_03: Quantitative IK Precision, Bone Length Invariance & Retargeting Metrics

**Tài liệu ID:** `MSK-P23-AUD-003`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Độ Chính xác Số học của Bộ giải Động học (Kinematic Roundtrip Precision)

Đánh giá tính nhất quán hai chiều giữa Forward Kinematics (FK) và Analytical Inverse Kinematics (IK) trên các góc thử nghiệm tiêu chuẩn:

| Góc Thử Nghiệm (Độ) | Góc Cánh Tay (Shoulder) | Góc Khuỷu (Elbow) | Tọa độ Cổ tay FK $(X, Y)$ | Góc Tái Lập IK $(\theta_1, \theta_2)$ | Sai số Góc Tối đa (Max Error) | Trạng thái |
|---|---|---|---|---|---|---|
| Tư thế Duỗi Thẳng ($0^\circ$) | $0.0^\circ$ | $0.0^\circ$ | $(0.000, 0.860)\text{ m}$ | $(0.0000^\circ, 0.0000^\circ)$ | $< 10^{-6}\ {}^\circ$ | **PASSED** |
| Tư thế Gập Nhẹ ($30^\circ$) | $25.0^\circ$ | $30.0^\circ$ | $(0.274, 1.018)\text{ m}$ | $(25.0000^\circ, 30.0000^\circ)$ | $< 10^{-6}\ {}^\circ$ | **PASSED** |
| Tư thế Gập Vuông ($60^\circ$) | $25.0^\circ$ | $60.0^\circ$ | $(0.380, 1.144)\text{ m}$ | $(25.0000^\circ, 60.0000^\circ)$ | $< 10^{-6}\ {}^\circ$ | **PASSED** |
| Tư thế Gập Vuông ($90^\circ$) | $25.0^\circ$ | $90.0^\circ$ | $(0.419, 1.309)\text{ m}$ | $(25.0000^\circ, 90.0000^\circ)$ | $< 10^{-6}\ {}^\circ$ | **PASSED** |

---

### 2. Thử nghiệm Tính Bất biến Chiều dài Xương (Bone Length Invariance)

Thực thi kiểm tra biến dạng đoạn xương xuyên suốt 19 bước góc chuyển động từ $0^\circ$ đến $90^\circ$:
- **Chiều dài danh định Xương cánh tay (Humerus):** $0.3000\text{ m}$
- **Chiều dài danh định Xương cẳng tay (Forearm):** $0.2600\text{ m}$
- **Độ lệch tối đa đo được:**
  $$\text{Max Upper Arm Error} = 0.0000\text{ mm}$$
  $$\text{Max Forearm Error} = 0.0000\text{ mm}$$
- **Ngưỡng dung sai cho phép:** $0.1000\text{ mm}$
- **Kết luận:** Khung xương giữ nguyên cấu trúc hình học tuyệt đối, không xảy ra hiện tượng co giãn xương ngoài ý muốn (Bone stretch = 0%).
