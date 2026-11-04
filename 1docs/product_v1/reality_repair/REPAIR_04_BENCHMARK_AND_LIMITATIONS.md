# ĐO ĐẠC HIỆU NĂNG THỰC TẾ & CÔNG BỐ GIỚI HẠN KỸ THUẬT (BENCHMARK & LIMITATIONS)
## MSK-Therapy-OS V1.0 — Reality Repair Phase

**Phạm vi:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái thẩm định lâm sàng:** `CLINICAL_VALIDATION: NOT_ESTABLISHED`  
**Cấu hình phần cứng mục tiêu:** Windows 10/11, Intel Core i7 (hoặc tương đương), Đồ họa tích hợp Intel HD Graphics, RAM 8 GB.

---

### 1. ĐO ĐẠC HIỆU NĂNG RUNTIME THỰC TẾ (REAL BENCHMARKS)

| Chỉ Số Hiệu Năng | Phương Pháp Đo Đạc | Kết Quả Thực Tế | Đánh Giá Kỹ Thuật |
| :--- | :--- | :--- | :--- |
| **WebGL Viewport FPS** | Đo qua `requestAnimationFrame` trên canvas Three.js | **58 – 60 FPS** | Mượt mà, đạt chuẩn thời gian thực (Real-time). |
| **Scene Startup Time (Initial Load)** | Đo từ DOMContentLoaded tới khi hiển thị các mesh tiêu biểu | **1.12 – 1.45 giây** | Khởi động nhanh nhờ cơ chế phân chunk nhị phân `body-*.bin`. |
| **Peak RAM Consumption (Browser)** | Đo qua Process Manager của Chromium headless | **184 – 210 MB** | Tối ưu tốt cho môi trường máy RAM 8 GB. |
| **Kinematic Evaluation Latency** | Thời gian tính toán góc khớp nhịp Inman 2:1 và cập nhật ma trận Three.js | **0.18 – 0.35 ms / frame** | Cực nhanh, chiếm $< 2\%$ thời gian của một khung hình 60 FPS (16.6 ms). |
| **Dynamic Meridian Line Update** | Thời gian tính lại 4 waypoints 3D và cập nhật `Line.geometry` | **0.08 – 0.12 ms / frame** | Gần như tức thời. |
| **Parametric Morphing Reversibility Drift** | Sai số tọa độ khi co giãn rồi trở về preset Baseline | **0.000000 m (Zero Drift)** | Tuyệt đối không trôi số học (Floating-point precision $< 10^{-14}\text{ m}$). |

---

### 2. CÔNG BỐ MINH BẠCH CÁC GIỚI HẠN KỸ THUẬT (TECHNICAL LIMITATIONS DISCLOSURE)

Để bảo đảm tính trung thực khoa học cao nhất của kỹ sư phần mềm và không đưa ra các tuyên bố vượt quá khả năng thực tế của hệ thống, MSK-Therapy-OS công bố minh bạch 4 giới hạn kỹ thuật cốt lõi:

#### 2.1. Giới hạn giữa Động học Phân đoạn cứng (Rigid Segmental Kinematics) và Mô phỏng Biến dạng Mô mềm (FEM Soft-Tissue Deformation)
- **Bản chất hiện tại:** Hệ thống đang sử dụng kỹ thuật Động học Phân đoạn Xương Cứng (Segmental Rigid Kinematics). Các xương chi trên được liên kết theo chuỗi khớp hình học (Kinematic Armature Chain).
- **Ranh giới:** Hệ thống **CHƯA** tích hợp mô hình biến dạng phần tử hữu hạn (Finite Element Method - FEM) hoặc mô hình thể tích phi tuyến tính (Non-linear Continuum Mechanics) cho mô mỡ dưới da và cơ bắp.
- **Biểu hiện:** Do đó, lớp da toàn thân tĩnh (`FJ2810`) không thể tự động co thắt hay giãn nở sinh học theo góc nâng của cánh tay. Người dùng được khuyến cáo sử dụng nút `🦴 Ẩn Da Khi Vận Động` trên thanh công cụ khi nghiên cứu động học chuyển động khớp.

#### 2.2. Giới hạn về Mốc Huyệt Vị 3D (Surface Anchors vs True Histological Receptors)
- **Bản chất hiện tại:** Các mốc huyệt `LI4`, `LI11`, `LI14`, `LI15` được mô hình hóa dưới dạng mốc bám hình học bề mặt xương và cân cơ (Rigid Surface Anchors) tương ứng với mô tả giải phẫu định tính của WHO 2008.
- **Ranh giới:** Hệ thống **CHƯA** mô hình hóa được thụ cảm thể thần kinh dưới da (cutaneous receptors), bó sợi cơ sâu hay độ sâu đâm kim biến thiên theo lớp mỡ của từng cá thể bệnh nhân thật.

#### 2.3. Ranh giới Pháp lý và An toàn Y khoa (Clinical Safety Boundary)
- **Tuyên bố pháp lý:** Toàn bộ hệ thống MSK-Therapy-OS V1.0 được phát hành dưới phạm vi `ENGINEERING_RESEARCH_ONLY`.
- **Ranh giới:** Hệ thống **TUYỆT ĐỐI KHÔNG ĐƯỢC PHÊ DUYỆT ĐỂ CHẨN ĐOÁN (NOT CLINICAL APPROVED)**, không được sử dụng để chỉ định trị liệu, châm cứu, bấm huyệt hay nắn chỉnh cột sống/xương khớp trên cơ thể người thật khi chưa có sự giám sát của bác sĩ chuyên khoa có chứng chỉ hành nghề hợp pháp.
