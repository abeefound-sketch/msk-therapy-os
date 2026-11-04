# MSK-Therapy-OS — Milestone P23 Executive Gates
## P23_05: Quality Gates G1–G4 Evaluation & GO / NO-GO Decision for P24

**Tài liệu ID:** `MSK-P23-AUD-005`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Đánh giá Bốn Cổng G1–G4 Milestone P23

| Cổng | Tiêu chuẩn Nghiệm thu | Kết quả Thực tế | Đánh giá |
|---|---|---|---|
| **G1 — Functional** | - Có mẫu chuyển động thật từ CMU Mocap có nguồn và hash.<br>- Armature một cánh tay vận hành trong Blender.<br>- Phát lại animation gập/duỗi khuỷu và nâng vai.<br>- Hỗ trợ playback/scrub. | - Tải thành công `02.asf` và `02_01.amc` từ CMU Mocap database.<br>- Nạp thành công `seth_shoulder_elevation.mot` (OpenSim).<br>- Dựng Armature cánh tay đầy đủ 4 xương và 2 control bones.<br>- Chèn keyframe và phát lại mượt mà trên Blender 3.6. | **PASS** |
| **G2 — Data Integrity** | - Chuỗi chuyển động tuân thủ JSON Schema.<br>- Chiều dài xương bất biến ($\Delta L < 0.1\text{ mm}$).<br>- Khóa giới hạn xoay theo y văn (Kapandji 0°–145°).<br>- Đánh dấu rõ các bậc tự do không quan sát được. | - Xác minh khớp `motion_sequence.schema.json` 100%.<br>- Độ lệch chiều dài xương tối đa: $0.0000\text{ mm}$ (Đạt).<br>- Thử nghiệm góc $160^\circ$ bị khóa tự động về $145.0^\circ$.<br>- Cờ `right_forearm_pronation` được đánh dấu `UNOBSERVABLE`. | **PASS** |
| **G3 — Domain Validity** | - Phê chuẩn cơ sinh học lâm sàng độc lập.<br>- Xác nhận chuyển động phù hợp người bệnh thật. | - Dữ liệu CMU chỉ được phân loại là Motion Prior tham khảo.<br>- Ràng buộc khớp dẫn chiếu Kapandji nhưng chưa được xác nhận trên từng bệnh nhân.<br>- Chưa có hội đồng chuyên môn y tế nghiệm thu. | **PENDING** |
| **G4 — Independent Acceptance** | - Đơn vị kiểm toán độc lập tái lập và ký biên bản. | - Mới được kiểm thử nội bộ tự động hóa bởi hệ thống. | **PENDING** |

---

### 2. Quyết định Điều hành Milestone P23

- **Trạng thái Toàn cục:** $$\mathbf{ENGINEERING\_PASS\_SCOPE\_LIMITED}$$
- **Quyết định:** $$\mathbf{CONDITIONAL\_GO} \longrightarrow \mathbf{Milestone\ P24\ (MediaPipe\ Pose\ Import\ \&\ Reconstruction)}$$
- **Điều kiện ràng buộc:** Duy trì cờ `UNOBSERVABLE` cho chuyển động sấp/ngửa cẳng tay khi chuyển sang ước lượng pose camera đơn ở P24.
