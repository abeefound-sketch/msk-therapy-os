# MSK-Therapy-OS — Milestone P21 Executive Gates
## P21_05: Quality Gates G1–G4 Evaluation & Milestone Decision

**Tài liệu ID:** `MSK-P21-AUD-005`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Đánh giá Bốn Cổng Độc lập G1–G4

| Cổng (Gate) | Tiêu chí Nghiệm thu | Kết quả Quan sát Thực tế | Quyết định |
|---|---|---|---|
| **G1 — Functional (Chức năng)** | - Chạy thực tế trên Blender 3.6 LTS không giả lập.<br>- Nạp mô hình giải phẫu thật có nguồn.<br>- Ẩn/hiện lớp giải phẫu hoạt động.<br>- 3 markers + 1 tuyến kinh $\ge 4$ waypoints.<br>- Hỗ trợ hoàn tác Undo.<br>- Ghi chú tiếng Việt.<br>- Lưu `.blend` và mở lại nguyên vẹn. | - Blender 3.6.5 chạy thành công trên máy trạm Windows i7-5600U.<br>- Nạp `shoulder_skeleton.glb` và `anatomy.glb`.<br>- Tách 4 lớp giải phẫu và cô lập lớp xương.<br>- Đặt 3 huyệt `LI4`, `ST36`, `KI3` gắn kết bề mặt.<br>- Dựng tuyến kinh 5 điểm, Undo thành công còn 4 điểm.<br>- Xuất file Markdown tiếng Việt kèm banner an toàn.<br>- File `.blend` (2.2 MB) lưu và mở lại hoàn hảo.<br>- Kết xuất 2 ảnh PNG minh chứng thực tế. | **PASS** |
| **G2 — Data Integrity (Toàn vẹn Dữ liệu)** | - Xuất/nhập đúng JSON Schema.<br>- Lưu trữ mã băm SHA-256 cấu trúc gốc.<br>- Khóa chặt tọa độ cục bộ bám bề mặt.<br>- Fail-closed khi mã băm mesh bị sửa đổi.<br>- Không âm thầm dịch chuyển hay lật trục. | - Xuất manifest và annotations khớp 100% schema chuẩn.<br>- Lưu trữ SHA-256 của lưới mesh `Humerus_R`.<br>- Thử nghiệm sửa đổi mã băm mesh giả mạo kích hoạt lỗi ngoại lệ `MeshChecksumMismatchError` thành công, ngăn chặn âm thầm ánh xạ sai.<br>- Giữ nguyên đơn vị mét (SI) và hệ trục tọa độ chuẩn. | **PASS** |
| **G3 — Domain Validity (Thẩm định Chuyên môn)** | - Huyệt vị được kiểm định bởi chuyên gia y học cổ truyền trên giải phẫu thực.<br>- Giới hạn cơ sinh học được đối chiếu y văn. | - Toàn bộ huyệt vị mang nhãn bắt buộc `USER_ANNOTATED_UNVERIFIED`.<br>- Ràng buộc khớp khuỷu dẫn chiếu Kapandji (2007) nhưng chưa qua hội đồng lâm sàng phê duyệt.<br>- Chưa có biên bản thẩm định của bác sĩ chuyên khoa độc lập. | **PENDING** *(Không được tự ý báo PASS)* |
| **G4 — Independent Acceptance (Nghiệm thu Độc lập)** | - Bên thứ ba độc lập tái lập toàn bộ quy trình trên mã nguồn và dữ liệu gốc. | - Báo cáo được lập bởi Coding Agent thực thi, chưa có chữ ký nghiệm thu của kiểm toán viên độc lập bên ngoài. | **PENDING** *(Giữ nguyên theo quy định)* |

---

### 2. Quyết định Điều hành Kỹ thuật (Executive Milestone Decision)

- **Trạng thái Kỹ thuật Toàn Cục:** $$\mathbf{ENGINEERING\_PASS\_SCOPE\_LIMITED}$$
- **Quyết định Chuyển Giai Đoạn:** $$\mathbf{CONDITIONAL\_GO} \longrightarrow \mathbf{Milestone\ P22}$$
- **Điều kiện ràng buộc:** Duy trì nhãn `USER_ANNOTATED_UNVERIFIED`, không tự phong chứng nhận y tế, và tiếp tục chuẩn hóa hệ tọa độ mốc chuẩn trong P22.
