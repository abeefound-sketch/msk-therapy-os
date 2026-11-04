# MA TRẬN ĐỐI SOÁT & NGHIỆM THU BỐN CỔNG G1–G4
## MSK-Therapy-OS · Product V1.0 Release Candidate

**Ngày đánh giá:** 03/11/2026  
**Phạm vi thẩm định:** Toàn bộ năm gói sản phẩm A, B, C, D, E  
**Nguyên tắc chỉ đạo:** Không tuyên bố khống, kiểm thử thực tế trên runtime và dữ liệu thật, tuân thủ nguyên tắc quản trị và an toàn lâm sàng.

---

### 1. Bảng Tổng Hợp Trạng Thái Cổng Kiểm Soát

| Cổng Kiểm Soát (Gate) | Định Nghĩa & Tiêu Chí | Kết Quả Thực Nghiệm | Quyết Định Trạng Thái | Ghi Chú & Bằng Chứng |
|---|---|---|---|---|
| **G1: Functional Acceptance** | Các chức năng của 5 gói A–E hoạt động đúng như thiết kế trên trình duyệt WebGL & Python server. | Đạt 100% qua 13 tests unit V1 và test browser Playwright E2E. | **`PASS`** | 6 ảnh chụp màn hình minh chứng tại `1docs/product_v1/evidence/`. |
| **G2: Data Integrity & Provenance** | Dữ liệu hình học, chuyển động, y văn có nguồn gốc rõ ràng, có chữ ký SHA-256, không bị trôi số học. | Tệp `atlas.json` khớp mã băm SHA-256, dữ liệu WHO 2008 & FMA chuẩn xác, độ trôi hoàn nguyên $= 0.000000\text{ m}$. | **`PASS`** | Kiểm toán giấy phép tại `V1_02_OPEN_SOURCE_LICENSE_COMPATIBILITY.csv`. |
| **G3: Domain Validity** | Độ chính xác giải phẫu và hiệu lực lâm sàng được phê duyệt bởi hội đồng chuyên gia y khoa độc lập. | Chưa tổ chức hội đồng y khoa lâm sàng độc lập thẩm định trực tiếp trên bệnh nhân. | **`PENDING`** | Tuân thủ tuyệt đối quy định: Coding Agent không tự phê duyệt `CLINICAL_APPROVED`. |
| **G4: Independent Engineering Acceptance** | Toàn bộ kiểm thử hồi quy độc lập, kiểm tra bảo mật, ranh giới an toàn và quy trình đóng gói. | 100% tests hồi quy kỹ thuật (P19–P36, P33 browser, V1 E2E) vượt qua tự động. | **`PASS`** | `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`. |

---

### 2. Chi Tiết Từng Gói Sản Phẩm (A–E)

#### Gói A: Nền Tảng Giải Phẫu (Atlas Foundation)
- **G1:** Bật/tắt 4 lớp `BONE`, `MUSCLE`, `ORGAN`, `SKIN` $\to$ `PASS`.
- **G2:** Nguồn gốc BodyParts3D Release 4.0 (CC BY 4.0), FMA IDs khớp $\to$ `PASS`.
- **G3:** Chờ chuyên gia giải phẫu lâm sàng nghiệm thu $\to$ `PENDING`.
- **G4:** Kiểm thử tải mesh và tìm kiếm thời gian thực $\to$ `PASS`.

#### Gói B: Hình Thể Tham Số & Khớp (Parametric Body & Registration)
- **G1:** 3 thanh trượt và 4 presets (`baseline`, `slender`, `broader`, `longer_arm`) co giãn 3D mesh và pivot khớp $\to$ `PASS`.
- **G2:** Hoàn nguyên tuyệt đối sau 20 chu kỳ lặp lại ($\Delta < 10^{-6}\text{ m}$) $\to$ `PASS`.
- **G3:** Mô hình nhân trắc học mở rộng cần thẩm định y học thể thao $\to$ `PENDING`.
- **G4:** Kiểm thử tự động `test_v1_parametric_body.py` vượt qua $\to$ `PASS`.

#### Gói C: Huyệt Vị Động & Đường Kinh (Dynamic Acupoints & Meridians)
- **G1:** Mốc `LI4`, `LI14`, `LI15` bám dính vào đúng xương đích khi thay đổi hình thể và chuyển động $\to$ `PASS`.
- **G2:** Undo/Redo stack ghi nhận versioning và provenance rõ ràng $\to$ `PASS`.
- **G3:** Thẩm định bởi bác sĩ Y học cổ truyền $\to$ `PENDING`.
- **G4:** Kiểm thử tự động `test_v1_dynamic_anchors.py` vượt qua $\to$ `PASS`.

#### Gói D: Chuyển Động WebGL & Kéo Chuột Tạo Dáng (Web Motion & Mouse Pose)
- **G1:** Giải quyết dứt điểm `WEB_MOTION_GEOMETRY_NOT_CONNECTED`. Chuỗi 100 frames MediaPipe và Mouse Pose làm xoay 3D mesh thật sự trên WebGL theo nhịp 2:1 $\to$ `PASS`.
- **G2:** Tích hợp dữ liệu góc quay MediaPipe từ video thực nghiệm $\to$ `PASS`.
- **G3:** Sai số camera đơn được ghi nhận trung thực là `ACCURACY_NOT_ESTABLISHED` $\to$ `PENDING`.
- **G4:** Kiểm thử Playwright WebGL canvas animation đạt $60\text{ FPS}$ $\to$ `PASS`.

#### Gói E: Tích Hợp Toàn Diện, Lưu Trữ & Báo Cáo (Persistence & Markdown)
- **G1:** Lưu và mở tệp `.mskproj`, xuất báo cáo Markdown tức thời $\to$ `PASS`.
- **G2:** Ghi tệp nguyên tử (Atomic write), chống hỏng manifest khi tắt đột ngột $\to$ `PASS`.
- **G3:** Báo cáo ghi rõ khuyến cáo an toàn, không có PII $\to$ `PASS` (về mặt đạo đức dữ liệu).
- **G4:** Khởi động 1-click qua `run_msk_therapy_os.bat` cho người dùng phổ thông $\to$ `PASS`.
