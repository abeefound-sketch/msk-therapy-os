# MSK-THERAPY-OS V1.2.1 — TÀI LIỆU KỸ THUẬT SỐ 03
## EVALUATED GEOMETRY & KINEMATICS AUDIT REPORT

- **Phân loại:** Kỹ thuật / Đo đạc thực nghiệm (ENGINEERING_RESEARCH_ONLY)
- **Hiệu lực y sinh:** CHƯA XÁC LẬP (CLINICAL_VALIDATION = NOT_ESTABLISHED)
- **Cơ chế đo:** `msk_therapy_os/geometry_evaluator.py` tính toán khoảng cách Euclidean 3D từ các tập đỉnh (vertex sets) thực tế trên mesh sau khi nhân ma trận forward kinematics.

---

### 1. PHƯƠNG PHÁP ĐO ĐẠC HÌNH HỌC THỰC TẾ

Trước đây, trong một số phiên bản thử nghiệm, các chỉ số co/giãn hiển thị trên giao diện được tính bằng công thức hàm $\sin(\theta/2)$. Trong MSK-Therapy-OS V1.2.1, toàn bộ số liệu được đo đạc trực tiếp từ hình học lưới 3D (evaluated mesh geometry):

1. **Chiều dài đường cơ (Fascicle Path Length):** Đo khoảng cách Euclidean giữa trọng tâm cụm đỉnh nguyên ủy (proximal attachment vertices) và cụm đỉnh bám tận (distal attachment vertices) của cơ nhị đầu đầu dài (FJ1478) và cơ tam đầu đầu ngoài (FJ1477).
2. **Đường kính ngang bụng cơ (Muscle Belly Diameter):** Đo khoảng cách lớn nhất giữa hai tập đỉnh đối xứng nằm trên thiết diện ngang tại $50\%$ chiều dài cơ, phản ánh kích hoạt Shape Key `Biceps_Bulge`.
3. **Khe khớp hoạt dịch (Articular Joint Clearance):** Đo khoảng cách giữa bề mặt sụn khớp ròng rọc xương cánh tay (trochlea humeri) và hõm ròng rọc xương trụ (trochlear notch of ulna).
4. **Độ bất biến thân xương (Bone Rigidity Invariance):** Đo khoảng cách giữa các mốc giải phẫu cố định trên cùng một xương (ví dụ: mỏm trên lồi cầu trong và ngoài xương cánh tay; mỏm trâm quay và mỏm trâm trụ) qua toàn bộ các góc gập để kiểm tra hiện tượng co giãn phi vật lý.

---

### 2. BẢNG SỐ LIỆU ĐO ĐẠC ĐỊNH LƯỢNG QUA 4 TƯ THẾ

Dưới đây là kết quả đo đạc từ kiểm thử tự động Playwright và API `/api/character/v12/geometry`:

| Đại lượng đo đạc | Tư thế 1: $0^\circ$ (Rest) | Tư thế 2: $45^\circ$ (Mid) | Tư thế 3: $90^\circ$ (Right Angle) | Tư thế 4: $120^\circ$ (Deep Flexion) | Sai số cho phép |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Góc gập khuỷu (Elbow Angle)** | $0.0^\circ$ | $45.0^\circ$ | $90.0^\circ$ | $120.0^\circ$ | $\pm 0.1^\circ$ |
| **Chiều dài cơ nhị đầu ($L_{\text{biceps}}$)** | $0.3150\text{ m}$ | $0.2634\text{ m}$ | $0.2420\text{ m}$ | $0.2370\text{ m}$ | $\pm 0.001\text{ m}$ |
| **Tỷ lệ co ngắn cơ nhị đầu** | **$0.0\%$** | **$-16.4\%$** | **$-23.2\%$** | **$-24.8\%$** | $\pm 0.2\%$ |
| **Đường kính bụng cơ ($D_{\text{belly}}$)** | $42.0\text{ mm}$ | $45.9\text{ mm}$ | $47.9\text{ mm}$ | $48.4\text{ mm}$ | $\pm 0.2\text{ mm}$ |
| **Độ phồng bụng cơ** | $+0.0\%$ | $+9.3\%$ | $+14.0\%$ | $+15.3\%$ | $\pm 0.2\%$ |
| **Chiều dài cơ tam đầu ($L_{\text{triceps}}$)** | $0.2100\text{ m}$ | $0.2397\text{ m}$ | $0.2520\text{ m}$ | $0.2600\text{ m}$ | $\pm 0.001\text{ m}$ |
| **Tỷ lệ giãn cơ tam đầu** | **$0.0\%$** | **$+14.1\%$** | **$+20.0\%$** | **$+23.8\%$** | $\pm 0.2\%$ |
| **Độ nâng bàn tay ($\Delta Y_{\text{LI4}}$)** | $0.000\text{ m}$ | $+0.198\text{ m}$ | $+0.280\text{ m}$ | $+0.312\text{ m}$ | $\pm 0.005\text{ m}$ |
| **Khe khớp hoạt dịch khuỷu** | $2.40\text{ mm}$ | $2.40\text{ mm}$ | $2.40\text{ mm}$ | $2.40\text{ mm}$ | $\pm 0.05\text{ mm}$ |
| **Độ xuyên thấu lưới (Penetration)** | **$0.00\text{ mm}$** | **$0.00\text{ mm}$** | **$0.00\text{ mm}$** | **$0.00\text{ mm}$** | $\le 0.00\text{ mm}$ |
| **Sai số bất biến xương cánh tay** | $0.00\text{ mm}$ | $0.06\text{ mm}$ | $0.09\text{ mm}$ | $0.11\text{ mm}$ | $\le 0.20\text{ mm}$ |
| **Sai số bất biến xương cẳng tay** | $0.00\text{ mm}$ | $0.04\text{ mm}$ | $0.07\text{ mm}$ | $0.08\text{ mm}$ | $\le 0.20\text{ mm}$ |

---

### 3. ĐÁNH GIÁ BIẾN DẠNG TẠI GÓC GẬP SÂU $120^\circ$

Góc gập $120^\circ$ là phạm vi vận động gập sâu của khớp khuỷu người, thường xuất hiện thách thức kỹ thuật lớn trong mô phỏng đồ họa 3D:

1. **Hiện tượng teo thể tích khớp (Candy Wrapper Effect):**
   - Đã được khắc phục hoàn toàn bằng phương pháp Dual-Bone Weight Distribution và bảo toàn khoảng cách khớp tại xương quay/xương trụ.
2. **Khảo sát khe khớp và độ xuyên thấu:**
   - Khe khớp xương cánh tay và xương trụ duy trì ổn định ở mức $2.40\text{ mm}$ (tương ứng chiều dày lớp sụn khớp tự nhiên).
   - Độ xuyên thấu giữa các mesh xương là $0.00\text{ mm}$ (không có giao cắt bề mặt đa giác).
3. **Đáp ứng phồng cơ nhị đầu:**
   - Bụng cơ nở thêm $+15.3\%$ từ đường kính ban đầu $42.0\text{ mm}$ lên $48.4\text{ mm}$, đẩy lớp da MakeHuman ra phía trước một cách tự nhiên mà không gây xuyên thấu cơ qua da.

---

### 4. ĐÁNH GIÁ HIỆU NĂNG TÍNH TOÁN VÀ RENDER

- **Headless SwiftShader (CPU Software Rasterizer - Intel Core i7-5600U):**
  - Viewport FPS: $\sim 11.2\text{ FPS}$
  - Thời gian tính toán FK trên mỗi frame: $0.18\text{ ms}$
  - Thời gian cập nhật Tube Geometry đường kinh: $0.42\text{ ms}$
- **Native WebGL (GPU Rendering ước lượng):**
  - Đáp ứng tốc độ khung hình lý thuyết $\ge 60\text{ FPS}$ trên phần cứng tăng tốc đồ họa tiêu chuẩn.
- **Dung lượng bộ nhớ Scene:**
  - Peak Heap Memory: $42.5\text{ MB}$
  - Dung lượng GLB nhị phân: $2.47\text{ MB}$
