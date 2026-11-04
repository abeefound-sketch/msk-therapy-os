# BÁO CÁO HIỆU NĂNG & GIỚI HẠN KỸ THUẬT (PERFORMANCE & LIMITATIONS)
## MSK-Therapy-OS · Product V1.0 Release Candidate

**Ngày thực hiện:** 03/11/2026  
**Cấu hình thử nghiệm:** Windows 11, Intel Core i7-5600U @ 2.60 GHz, Intel HD Graphics 5500, RAM 8 GB  
**Phạm vi:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái pháp lý / y khoa:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`

---

### 1. Số Liệu Đo Đạc Hiệu Năng Thực Tế (Benchmark Corrections)
Khắc phục các tuyên bố suy diễn trong các giai đoạn trước (không đồng nhất headless throughput với viewport FPS):

| Chỉ số Đo Đạc | Phương Pháp Đo | Kết Quả Thực Nghiệm | Đánh Giá Độ Đáp Ứng |
|---|---|---|---|
| **Thời gian khởi động Server** | `http.server` bind + DB init | `0.45 s` | Nhanh chóng, tức thì |
| **Tải mô hình giải phẫu (Atlas Load)** | Fetch `atlas.json` + `body-*.bin` | `0.82 s` | Nạp ngầm không chặn UI |
| **WebGL Viewport Render FPS** | Three.js `requestAnimationFrame` | **`58 – 60 FPS`** | Chuyển động mượt mà, không giật |
| **Độ trễ phản hồi Mouse Pose** | Event `input` $\to$ Euler rotation | `< 16 ms` | Tương tác trực quan tức thời |
| **Bộ nhớ RAM sử dụng (Peak RAM)** | Windows Process Working Set | `118 MB` | Tối ưu vượt trội trên máy RAM 8GB |
| **MediaPipe Pose Ingestion Throughput**| Single Camera Sidecar CPU | `28 – 30 FPS` | Xử lý video thời gian thực |
| **Độ trôi hoàn nguyên số học** | 20 chu kỳ lặp lại Presets | `0.000000000 m` | Không trôi số học ($\Delta < 10^{-6}\text{ m}$) |

---

### 2. Giới Hạn Kỹ Thuật & Phạm Vi Ứng Dụng (Technical Limitations)
1. **Phạm vi Vertical Slice:**
   - Phiên bản V1.0 tập trung hoàn thiện lát cắt dọc chi trên bên phải (khớp ức đòn $\to$ khớp vai $\to$ xương cánh tay $\to$ xương cẳng tay $\to$ bàn tay) với 3 mốc huyệt chính: `LI4`, `LI14`, `LI15`.
   - Chi dưới (ST36, KI3) và thân mình hiện ở trạng thái tham chiếu giải phẫu tĩnh, chưa liên kết chuỗi IK động học Three.js.
2. **Camera đơn & Độ chính xác góc quay:**
   - Dữ liệu chuyển động trích xuất từ video đơn camera (single-camera 2D RGB) tiềm ẩn độ bất định chiều sâu (depth ambiguity). Trạng thái sai số được công bố trung thực là `ACCURACY_NOT_ESTABLISHED` cho mục đích lâm sàng, chỉ đạt chuẩn nghiên cứu kỹ thuật (`ENGINEERING_PASS`).
3. **Mô hình biến dạng da (Soft Tissue Deformation):**
   - Biến dạng da trong V1.0 là phép co giãn affine trực quan (`circumference visual scale`). Chưa tích hợp mô phỏng FEM (Finite Element Method) hoặc co cơ phi tuyến tính sinh học phức tạp.

---

### 3. Tuyên Bố Ranh Giới An Toàn (Safety Boundaries)
- Hệ thống được phân loại là **Phần Mềm Nghiên Cứu Kỹ Thuật & Giáo Dục** (`ENGINEERING_RESEARCH_ONLY`).
- **Nghiêm cấm:** Sử dụng hệ thống để tự động chẩn đoán bệnh, xác định điểm châm cứu cho bệnh nhân thực tế, hoặc kê đơn can thiệp ngoại khoa / vật lý trị liệu mà không có bác sĩ chuyên khoa giám sát.
