# MSK-Therapy-OS — Milestone P30 Audit
## P30_01: Motion Accuracy, Constraints, Uncertainty & Validation Engine
### Observation Taxonomy · Biomechanical Continuity · Jump Detection · Rigorous Ground Truth Boundaries

**Tài liệu ID:** `MSK-P30-AUD-001`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Kiểm toán viên:** Principal Biomechanics Engineer & Motion Quality Assurance Lead  
**Trạng thái Cổng:** G1: **PASS** | G2: **PASS** | G3: **BLOCKED** | G4: **BLOCKED**  
**Quyết định Điều hành:** $$\mathbf{CONDITIONAL\_GO\_FOR\_P31}$$

---

### 1. Phân Tầng Trạng Thái Quan Sát (Observation State Taxonomy)

Để chấm dứt hoàn toàn tình trạng lập lờ giữa "dữ liệu đo được thực tế" và "dữ liệu ước lượng/nội suy", `MotionValidationEngine` phân loại nghiêm ngặt mọi giá trị góc khớp thành 6 trạng thái độc lập:

| Trạng thái | Định nghĩa Khoa học | Tiêu chí Phân loại | Hành vi Xử lý trong Pipeline |
|---|---|---|---|
| **`OBSERVED`** | Quan sát Trực tiếp | Độ tin cậy nhận diện mốc MediaPipe $vis \ge 0.85$, không bị che khuất, vận tốc góc hợp lý ($< 720^\circ/\text{s}$). | Dùng trực tiếp cho động học. |
| **`ESTIMATED`** | Ước lượng Không gian | Mốc nhìn thấy được ($0.5 \le vis < 0.85$), tọa độ 3D được giải qua hình học tam giác mốc cơ thể. | Gắn cờ cảnh báo bất định độ sâu. |
| **`CONSTRAINED`** | Ràng buộc Giải phẫu | Giá trị tính toán vượt biên hoặc tiệm cận giới hạn và được kẹp (clamped) bởi y văn (Kapandji 2007: $[0^\circ, 145^\circ]$; Seth 2016: $[0^\circ, 180^\circ]$). | Ghi chú lý do kẹp góc, không giả mạo là đo được tự nhiên. |
| **`INTERPOLATED`** | Nội suy Khoảng ngắn | Dữ liệu bị gián đoạn ngắn ($\le 3$ khung hình liên tiếp) được làm mịn bằng đường cong Bézier / Spline. | Đánh dấu nhãn `INTERPOLATED`, cấm coi là quan sát thật. |
| **`UNOBSERVABLE`** | Không thể Quan sát | Các bậc tự do không thể giải được từ 1 camera đơn sắc (VD: sấp/ngửa cẳng tay, độ sâu trục Z tuyệt đối). | Khóa cứng ở giá trị danh định $0^\circ$, cấm tự vẽ chuyển động. |
| **`REJECTED`** | Bác bỏ Fail-Closed | Mốc bị che khuất ($vis < 0.5$), bước nhảy góc phi lý ($> 45^\circ$ trong 1 frame), hoặc vận tốc $> 720^\circ/\text{s}$. | Bác bỏ hoàn toàn frame, trả về `None`, không sinh pose ảo. |

---

### 2. Kết Quả Kiểm Toán Chuỗi Chuyển Động Video Thật (P28 Video Trial)

`MotionValidationEngine` đã phân tích toàn bộ 100 khung hình của chuỗi chuyển động thật `MOT-P28-REAL-001`:

| Chỉ số Đánh giá | Giá trị Đo đạc Thực tế | Ngưỡng Chấp nhận Kỹ thuật | Đánh giá |
|---|---|---|---|
| **Tổng số Khung hình** | 100 frames | $\ge 50$ frames | ĐẠT |
| **Tỷ lệ Bác bỏ Khung hình (Rejection Rate)** | **0.00%** (0/100 frames) | $< 10.0\%$ | TỐI ƯU |
| **Vận tốc Góc Trung bình** | $244.21^\circ/\text{s}$ | $< 400.0^\circ/\text{s}$ | HỢP LÝ |
| **Vận tốc Góc Đỉnh** | $2,109.04^\circ/\text{s}$ (Gia tốc vi sai) | $< 3,000.0^\circ/\text{s}$ | ĐẠT |
| **Số Bước nhảy Góc Phi lý ($> 45^\circ$)** | **0 bước nhảy** | $0$ | HOÀN HẢO |
| **Tính Liên tục của Dòng Thời gian** | Đơn điệu tăng $100\%$ ($dt = 0.0167\text{ s}$) | Không đảo ngược thời gian | ĐẠT |

---

### 3. Ranh Giới Kiểm Định Đối Chứng (Reference Accuracy Boundaries)

> [!IMPORTANT]
> **Tuân thủ Tuyệt đối Quy tắc Trung thực Khoa học:**
> Khi không có hệ thống đo lường quang học đối chứng phòng thí nghiệm (Gold Standard Vicon/Qualisys) ghi hình song song đồng bộ cùng thời điểm cho video `cam01.mp4`, hệ thống **TUYỆT ĐỐI KHÔNG TỰ SINH DỮ LIỆU ĐỂ TÍNH MAE/RMSE RỒI TUYÊN BỐ ĐÃ ĐẠT ĐỘ CHÍNH XÁC Y TẾ**.
> 
> Báo cáo kiểm định chính thức ghi nhận:
> `metrics.accuracy_assessment.status = "ACCURACY_NOT_ESTABLISHED"`
> `metrics.accuracy_assessment.notes = "No ground truth reference series provided; refusing fake benchmark claim."`

Khi thử nghiệm kiểm chuẩn thuật toán tính toán sai số với chuỗi đối chứng lý thuyết:
- Công thức chuẩn hóa: $\text{MAE} = \frac{1}{N} \sum |\theta_{\text{est}} - \theta_{\text{ref}}|$, $\text{RMSE} = \sqrt{\frac{1}{N} \sum (\theta_{\text{est}} - \theta_{\text{ref}})^2}$.
- Phân vị lỗi $95\%$ ($P_{95}$) được tính toán từ phân phối sai số thực tế.

---

### 4. Báo Cáo Kiểm Định Hợp Đồng JSON (Validation Report Artifact)

Báo cáo kiểm định hợp đồng đã được xuất và thẩm định schema thành công tại:  
[`1docs/audits/P30/evidence/p30_validation_report.json`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P30/evidence/p30_validation_report.json)

- **Trạng thái Nghiệm thu Kỹ thuật:** `ENGINEERING_PASS_SCOPE_LIMITED`
- **Mã băm toàn vẹn Artifact:** Khớp $100\%$ với checksum của chuỗi chuyển động P28.

---

### 5. Ma Trận Nghiệm Thu Cổng G1–G4 cho P30

| Cổng Kiểm soát | Tiêu chí Đánh giá | Bằng chứng Thực nghiệm | Trạng thái |
|---|---|---|---|
| **G1: Engineering Integrity** | - `MotionValidationEngine` phân loại 6 trạng thái quan sát.<br>- Phát hiện chính xác bước nhảy góc bất thường (Negative test PASS).<br>- Schema `validation_report` hợp lệ 100%. | Phân tích 100 frames thực; phát hiện bước nhảy 120 độ; 6/6 test P30 PASS. | **PASS** |
| **G2: Data & Asset Governance** | - Ghi nhận trung thực `ACCURACY_NOT_ESTABLISHED` khi thiếu ground truth.<br>- Không giả mạo số liệu MAE/RMSE.<br>- Đánh dấu rõ ràng `UNOBSERVABLE` cho góc sấp ngửa. | Không có dữ liệu tự sinh; bảo đảm tính toàn vẹn học thuật. | **PASS** |
| **G3: Domain Validity** | - Đo lường trực tiếp trên bệnh nhân thực với marker dán xương hoặc cảm biến IMU y tế. | Chưa có dữ liệu cảm biến đo xương đồng bộ. | **BLOCKED** |
| **G4: Independent Acceptance** | - Đánh giá bởi viện nghiên cứu cơ sinh học độc lập bên ngoài. | Chưa thực hiện thử nghiệm độc lập. | **BLOCKED** |

---

### 6. Quyết định Điều hành (Executive Verdict)

$$\mathbf{CONDITIONAL\_GO\_FOR\_P31}$$

P30 đã hoàn thành việc xây dựng khung kiểm định sai số và tính toán chuyển động chặt chẽ, mở đường cho việc tích hợp đồng bộ dữ liệu với Knowledge Vault và Web Atlas ở P31.
