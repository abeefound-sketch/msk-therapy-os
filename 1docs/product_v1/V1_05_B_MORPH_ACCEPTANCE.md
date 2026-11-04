# BÁO CÁO NGHIỆM THU GÓI B: HÌNH THỂ THAM SỐ (PARAMETRIC BODY & REGISTRATION)
## MSK-Therapy-OS · Product V1.0 Release Candidate

**Ngày thực hiện:** 03/11/2026  
**Phạm vi:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái pháp lý / y khoa:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`

---

### 1. Mục Tiêu & Cơ Chế Hoạt Động
Gói B cho phép người dùng điều chỉnh tỷ lệ cơ thể và chi trên bằng các thanh trượt tham số (Parametric Sliders) và bộ thiết lập mẫu (Presets), đồng thời tự động cập nhật tâm xoay các khớp mà không làm trôi dạt số học khi quay về cấu hình ban đầu.

- **3 Thanh trượt điều khiển:**
  1. `height_scale`: Tỷ lệ chiều cao tổng thể ($0.85\times - 1.15\times$, tương đương $1.47\text{m} - 1.99\text{m}$, tham chiếu $1.73\text{m}$).
  2. `right_arm_length_ratio`: Tỷ lệ chiều dài cánh tay phải ($0.85\times - 1.15\times$).
  3. `right_arm_circumference_visual`: Tỷ lệ chu vi/độ dày cơ bắp cánh tay ($0.80\times - 1.30\times$).
- **4 Thiết lập mẫu (Presets):**
  - `Baseline`: Chuẩn tham chiếu $1.73\text{m}$, tỷ lệ tay $1.00\times$, chu vi $1.00\times$.
  - `Slender`: Chiều cao $1.05\times$ ($1.82\text{m}$), tỷ lệ tay $1.03\times$, chu vi $0.88\times$.
  - `Broader`: Chiều cao $0.98\times$ ($1.70\text{m}$), tỷ lệ tay $0.97\times$, chu vi $1.20\times$.
  - `Longer Arm`: Chiều cao $1.02\times$ ($1.76\text{m}$), tỷ lệ tay $1.12\times$, chu vi $0.95\times$.

---

### 2. Kiểm Chứng Tính Hoàn Nguyên Số Học (Zero Reversibility Drift)
Hệ thống sử dụng kỹ thuật co giãn affine độc lập với gốc tọa độ khớp cục bộ. Khi chuyển đổi liên tục giữa các presets và quay trở lại `Baseline`:
- **Số vòng thử nghiệm:** 20 chu kỳ lặp lại liên tiếp (`baseline` $\to$ `slender` $\to$ `broader` $\to$ `longer_arm` $\to$ `baseline`).
- **Sai số vị trí đo được:** $\Delta_{\max} = 0.000000000\text{ m} < 10^{-6}\text{ m}$.
- **Kết quả:** Đạt tiêu chuẩn hoàn nguyên số học tuyệt đối (Zero numerical drift).

---

### 3. Cập Nhật Đăng Ký Giải Phẫu Khớp (Joint Pivots Registration)
Khi thanh trượt chiều dài tay thay đổi:
- Vị trí khớp khuỷu (`elbow_R`) và khớp cổ tay (`wrist_R`) tự động tính toán lại theo phân cấp:
  $$\mathbf{P}_{\text{elbow}} = \mathbf{P}_{\text{shoulder}} + \mathbf{L}_{\text{humerus}} \times \text{arm\_length\_ratio}$$
  $$\mathbf{P}_{\text{wrist}} = \mathbf{P}_{\text{elbow}} + \mathbf{L}_{\text{forearm}} \times \text{arm\_length\_ratio}$$
- Các cấu trúc xương con (Humerus, Radius, Ulna, Metacarpal II) và mốc huyệt bám trên bề mặt xương co giãn và dịch chuyển tương thích hoàn hảo.

---

### 4. Kết Luận Gói B
- **G1 Functional Acceptance:** `PASS`
- **G2 Data Integrity:** `PASS`
- **G3 Domain Validity:** `PENDING`
- **G4 Independent Engineering Acceptance:** `PASS`
