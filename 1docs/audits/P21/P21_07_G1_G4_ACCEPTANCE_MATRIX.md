# MSK-Therapy-OS — Milestone P21 Quality Gates Evaluation
## P21_07: Independent Acceptance Matrix (G1–G4)

**Tài liệu ID:** `MSK-P21-AUD-007`  
**Ngày thực hiện:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái Toàn Cục:** `ENGINEERING_PASS_SCOPE_LIMITED` (G1/G2: PASS; G3/G4: PENDING)  

---

### 1. Ma trận Nghiệm thu 4 Cổng Chất lượng (Quality Gate Matrix)

| Cổng (Gate) | Tên Cổng & Trọng tâm | Trạng thái P20 cũ | Trạng thái P21 hiện tại | Lý do & Căn cứ Kỹ thuật |
|---|---|---|---|---|
| **G1** | **Kiến trúc & Ranh giới Kỹ thuật (Architecture & Engineering Governance)** | `PASS` | **`PASS`** | Đã thiết lập sandbox hoàn toàn độc lập tại `/sandbox/p21/`, không chạm vào mã nguồn `/atlas/` cũ; chọn pipeline BodyParts3D 4.0 sạch về giấy phép (CC BY 4.0); toàn bộ 15 chunk nhị phân tồn tại offline; 34/34 bài test tự động PASS. |
| **G2** | **Độ phủ Giải phẫu & Chức năng PoC (Anatomical Coverage & PoC Functionality)** | `BLOCKED` (Do thiếu mô hình thật) | **`PASS`** | Đã chứng minh và chạy thực tế mô hình giải phẫu 3D thật với đầy đủ 4 lớp: Xương (296), Cơ (402), Nội tạng (249 tạng chính), Da (FJ2810); có raycasting đánh dấu huyệt thủ công; vẽ đường kinh đa điểm kèm hoàn tác Undo; lưu trữ và xuất Markdown chuẩn Knowledge Vault. |
| **G3** | **Kiểm chứng Giải phẫu Học thuật & Lâm sàng (Anatomical Ground-Truth Verification)** | `PENDING` | **`PENDING`** (Bảo lưu theo nguyên tắc) | Nghiêm cấm Agent tự cấp chứng nhận `ANATOMICAL_VERIFIED` hoặc `CLINICAL_APPROVED`. Vị trí các huyệt LI4, ST36, KI3 đòi hỏi hội đồng chuyên gia châm cứu và mốc giải phẫu xác định lâm sàng độc lập. |
| **G4** | **Nghiệm thu Độc lập & Phát hành (Independent Institutional Acceptance)** | `PENDING` | **`PENDING`** (Bảo lưu theo nguyên tắc) | Chưa tiến hành đánh giá bởi bên thứ ba độc lập hoặc cơ quan kiểm duyệt thiết bị y tế; mã nguồn duy trì phạm vi `ENGINEERING_RESEARCH_ONLY`. |

---

### 2. Chi tiết Đánh giá Từng Hạng mục Kỹ thuật Cổng G1 & G2

#### A. Cổng G1 — Quản trị Kiến trúc và An toàn
- [x] **Không xâm lấn runtime sản xuất:** Tuyệt đối không can thiệp vào `static/atlas/app.js` hay `meridians.js`. Tuyến `/atlas/` và `/education/` hoạt động bình thường (đã xác thực qua test `test_route_isolation_atlas_and_education_unaffected`).
- [x] **Kiểm toán giấy phép nguồn mở (IP Compliance):** Đã phân định rõ rủi ro copyleft của Z-Anatomy (CC BY-SA 4.0) và cách ly; chọn BodyParts3D 4.0 với giấy phép CC BY 4.0 cho phép tích hợp và thương mại hóa kèm điều kiện ghi công đúng chuẩn.
- [x] **Toàn vẹn tệp tin 100% Offline:** Không phụ thuộc CDN ngoại biên; toàn bộ `atlas.json` (SHA-256: `c359f4bcd2...`) và 15 chunk nhị phân đều nằm trong kho lưu trữ cục bộ.
- [x] **Bảo toàn dữ liệu P19/P20:** Không ghi đè, không xóa, không phá vỡ database hay vault của các milestone trước; test suite hồi quy 34/34 đạt tỷ lệ 100%.

#### B. Cổng G2 — Chức năng 3D Atlas PoC
- [x] **Mô hình giải phẫu thật có 4 lớp phân biệt:** Đã phân loại và trực quan hóa 296 xương, 402 cơ, 249 tạng và lớp da toàn thân bằng các chất liệu shader và nhóm Three.js riêng biệt.
- [x] **Công tắc ẩn/hiện và điều chỉnh độ mờ da:** 4 checkbox hoạt động độc lập và thanh trượt độ mờ da 0%..100% giúp quan sát các tạng sâu bên trong cơ thể.
- [x] **Thẻ thông tin giải phẫu (Inspector Card):** Hiển thị đầy đủ tên giải phẫu, mã FMA ID, hệ cơ quan, chunk tệp tin và giới hạn Bounding Box thực tế (mét).
- [x] **Chế độ đánh dấu huyệt thủ công (Manual Acupoint):** Sử dụng raycasting bắt chính xác bề mặt tam giác của cấu trúc giải phẫu; tự động gán nhãn bắt buộc `USER_ANNOTATED_UNVERIFIED`.
- [x] **Chế độ vẽ đường kinh đa điểm (Manual Polyline):** Cho phép đặt chuỗi waypoint liên tục; hỗ trợ hoàn tác Undo từng điểm; xóa bản nháp; lưu trữ vĩnh viễn với trạng thái `USER_DRAFT_UNVERIFIED`.
- [x] **Bộ chuyển đổi xuất Markdown (Knowledge Vault Adapter):** Tự động sinh tệp Markdown chứa đầy đủ chữ ký SHA-256, bảng tọa độ, cấu trúc liên kết và cảnh báo miễn trừ trách nhiệm y khoa.

---

### 3. Lý do Duy trì Trạng thái PENDING đối với Cổng G3 & G4

1. **Ranh giới Chuyên môn:** Một kỹ sư phần mềm hoặc AI Agent không có thẩm quyền lâm sàng để tuyên bố một điểm tọa độ toán học là "đúng vị trí huyệt châm cứu".
2. **Sai số Hình học Máy móc vs Mốc Huyệt học:** Độ trùng khớp raycast hình học $< 15\text{ mm}$ chỉ chứng minh tia chiếu cắt trúng mặt tam giác của mesh giải phẫu trong bộ nhớ đồ họa, **hoàn toàn không phải là bằng chứng huyệt học**. Vị trí huyệt thực tế phụ thuộc vào giải phẫu bề mặt sống, trương lực cơ, tư thế bệnh nhân và định vị ngón tay thầy thuốc (đồng thân thốn).
3. **Phán quyết:** G3 và G4 tiếp tục được giữ ở trạng thái `PENDING` một cách minh bạch và trung thực.
