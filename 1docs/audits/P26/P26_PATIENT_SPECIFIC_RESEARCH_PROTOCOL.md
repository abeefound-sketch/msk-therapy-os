# MSK-Therapy-OS — Milestone P26 Research Protocol
## P26: Patient-Specific Anatomical Research Protocol, Anthropometric Calibration & Governance

**Tài liệu ID:** `MSK-P26-AUD-001`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Quyết định Lâm sàng Toàn Cục:** $$\mathbf{RESEARCH\_ONLY\ /\ NO\_CLINICAL\_GO}$$  

---

### 1. Phạm vi và Ranh giới Nghiên cứu (Scope & Boundaries)

Milestone P26 xác lập giao thức nghiên cứu (Research Protocol) cho việc cá nhân hóa hình học giải phẫu theo kích thước cá thể (Patient-Specific Morphometry).
> [!CAUTION]
> **RANH GIỚI BẢO VỆ PHÁP LÝ & AN TOÀN LÂM SÀNG:**
> 1. Không xem việc co giãn tỷ lệ chiều cao hoặc một bức ảnh 2D là đủ để xác định giải phẫu học 3D của một cá thể người bệnh thật.
> 2. Tuyệt đối không tự ý hiệu chỉnh tọa độ huyệt vị hoặc ranh giới ROM cho bệnh nhân thật bằng các công thức nội suy chưa qua thử nghiệm lâm sàng.
> 3. Nghiêm cấm đưa bất kỳ dữ liệu bệnh án, hình ảnh nhận diện khuôn mặt hoặc thông tin định danh y tế (PII/PHI) vào kho mã nguồn, logs hay bản demo phát triển.

---

### 2. Mô hình Hiệu chuẩn Nhân trắc học Nghiên cứu (Anthropometric Calibration Model)

Để co giãn khung xương chuẩn BodyParts3D theo kích thước chi của đối tượng nghiên cứu giả lập (synthetic subject), áp dụng hệ số tỷ lệ đoạn chi (Segment Scaling Ratio):

$$\text{Scale Ratio } s_{\text{arm}} = \frac{L_{\text{observed}}}{L_{\text{canonical}}}$$
Trong đó:
- $L_{\text{canonical}} = 0.300\text{ m}$ (Chiều dài xương cánh tay chuẩn từ mỏm cùng vai đến mỏm trên lồi cầu ngoài).
- $L_{\text{observed}}$: Khoảng cách thực đo giữa hai mốc xương có thể sờ nắn được (Palpable Bony Landmarks).

#### Các Yếu tố Gây Nhiễu & Độ Bất Định Không Thể Bỏ Qua:
1. **Nhiễu mô mềm (Soft Tissue Artifact - STA):** Da và cơ trượt tương đối trên bề mặt xương trong quá trình vận động (sai số dao động từ $10\text{ mm}$ đến $30\text{ mm}$).
2. **Biến thiên chỉ số khối cơ thể (BMI / Adiposity):** Lớp mỡ dưới da làm thay đổi khoảng cách từ bề mặt da đến mốc xương, khiến việc định vị huyệt theo chiều sâu $Z$ từ ảnh bề mặt là bất khả thi nếu không có ảnh cắt lớp MRI/CT.

---

### 3. Khung Đánh giá Thẩm định Độc lập (Validation Framework)

Giao thức kiểm định bắt buộc trước khi xem xét bất kỳ ứng dụng thực tế nào:

```text
[Volunteer / Synthetic Subject]
              │
              ├─► Standard Multi-Camera Vicon Optical Mocap (Ground Truth Gold Standard)
              │
              └─► MSK Monocular Pose Pipeline (Estimated)
                            │
                            ▼
           [Bland-Altman Limits of Agreement Analysis]
           ├── Root Mean Square Error (RMSE) per joint
           ├── Mean Absolute Error (MAE) per joint
           └── Intraclass Correlation Coefficient (ICC > 0.90)
```

---

### 4. Quyết định Điều hành Toàn Cục P26

- Do hiện tại chưa có bộ dữ liệu đối chứng lâm sàng IRB được phê chuẩn trên bệnh nhân thật:
- **Trạng thái:** $$\mathbf{RESEARCH\_ONLY}$$
- **Quyết định:** $$\mathbf{NO\_CLINICAL\_GO}$$ (Không cấp phép phát hành lâm sàng).
