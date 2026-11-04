# MSK-THERAPY-OS V1.1 — PARAMETRIC MORPHING ACCEPTANCE
## Báo cáo Nghiệm thu Biến đổi Hình thể Tham số (GPU Morph Targets)

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Khuyến cáo:** Tuyệt đối không khẳng định mô hình hình thể tham số phản ánh chính xác phân bố mô mỡ hoặc cấu trúc giải phẫu cá thể của từng bệnh nhân cụ thể.

---

### 1. PHÂN LOẠI TRẠNG THÁI CÁC THAM SỐ HÌNH THỂ

Toàn bộ các tham số biến đổi hình thể trong V1.1 được điều khiển thông qua các Shape Keys (Morph Targets) tính toán trực tiếp trên GPU WebGL Shader, đảm bảo không làm gián đoạn ma trận phân cấp xương và không gây hiện tượng co rút lưới:

| Tham số Hình Thể | Nguồn Dữ Liệu Morph | Trạng Thái Kỹ Thuật | Phạm vi Hợp lệ | Số Đỉnh Biến Dạng |
| :--- | :--- | :--- | :--- | :--- |
| **Chiều cao (Height)** | `male-young-maxheight.target.gz` | **SUPPORTED_NATIVE** | $0.00 \to 1.00$ ($1.69\text{ m} \to 1.88\text{ m}$) | 19.150 đỉnh |
| **Tỷ lệ cơ thể (Proportions)** | `male-young-proportions.target.gz` | **SUPPORTED_NATIVE** | $0.00 \to 1.00$ | 9.378 đỉnh |
| **Độ rộng vai (Shoulder Width)** | `measure-shoulder-dist-incr.target.gz` | **SUPPORTED_NATIVE** | $0.00 \to 1.00$ ($0.44\text{ m} \to 0.52\text{ m}$) | 5.568 đỉnh |
| **Vòng eo / Vóc dáng (Waist/Build)**| `measure-waist-circ-incr.target.gz` | **SUPPORTED_NATIVE** | $0.00 \to 1.00$ | 1.518 đỉnh |
| **Chiều dài tay (Arm Length)** | `l/r-upperarm/lowerarm-vert-incr` | **SUPPORTED_NATIVE** | $0.00 \to 1.00$ | 1.394 đỉnh |
| **Chiều dài chân (Leg Length)** | `l/r-upperleg/lowerleg-vert-incr` | **SUPPORTED_NATIVE** | $0.00 \to 1.00$ | 4.518 đỉnh |
| **Độ dày mô mềm cá thể** | Không có dữ liệu quét y tế cá nhân | **NOT_SUPPORTED** | N/A | Khuyến cáo không suy diễn y khoa |

---

### 2. KẾT QUẢ KIỂM CHỨNG TÍNH HOÀN NGUYÊN (REVERSIBILITY TEST)

- **Quy trình kiểm thử:**
  1. Gán ngẫu nhiên các giá trị biến dạng trên toàn bộ 6 tham số morphing trong 20 chu kỳ liên tiếp.
  2. Thực hiện biến đổi đồng thời khi nhân vật đang ở tư thế nghỉ (Rest Pose) và tư thế gập khuỷu $90^\circ$ (Kinematic Pose).
  3. Hoàn nguyên toàn bộ các thanh trượt về giá trị cơ sở $0.000000$.
  4. Đo sai số trôi tọa độ đỉnh $\Delta d = \|\mathbf{v}_{20} - \mathbf{v}_0\|$.
- **Kết quả đo đạc thực tế:**
  $$\text{Độ trôi hoàn nguyên sau 20 chu kỳ} = \mathbf{0.000000\text{ m}}\ (0.0\text{ \mu m})$$
  *(Kết quả hoàn nguyên số học đạt độ chính xác float32 tuyệt đối).*

---

### 3. KIỂM SOÁT KHỚP XƯƠNG VÀ GIỚI HẠN SINH LÝ

- Khi thay đổi độ rộng vai hoặc chiều dài cánh tay, Skin Weights vẫn liên kết $100\%$ với các xương tương ứng (`clavicle_r`, `upperarm_r`, `lowerarm_r`).
- Khoảng cách giữa các tâm xoay khớp vai và khuỷu duy trì tính khít kín liên tục ($\text{Visual Gap} = 0.000\text{ mm}$), triệt tiêu hoàn toàn lỗi vỡ bề mặt lưới.
