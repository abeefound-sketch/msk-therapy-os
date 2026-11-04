# BÁO CÁO NGHIỆM THU GÓI C: HUYỆT VỊ ĐỘNG & ĐƯỜNG KINH (DYNAMIC ACUPOINTS & MERIDIANS)
## MSK-Therapy-OS · Product V1.0 Release Candidate

**Ngày thực hiện:** 03/11/2026  
**Phạm vi:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái pháp lý / y khoa:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`

---

### 1. Mục Tiêu & Cơ Chế Bám Dính Giải Phẫu
Gói C đảm bảo các mốc huyệt giải phẫu bám dính động lực học vào bề mặt xương đích khi cơ thể thay đổi hình thể (morph) hoặc thực hiện chuyển động (pose).

- **Danh mục mốc huyệt Vertical Slice (Chi trên phải):**
  1. **LI4 (Hợp Cốc):** Bám trên xương đốt bàn tay II phải (`Metacarpal_2_R`, `FJ3352`, `FMA:24466`), mặt mu bàn tay phía quay.
  2. **LI14 (Tí Nhu):** Bám trên xương cánh tay phải (`Humerus_R`, `FJ3368`, `FMA:23130`), bờ ngoài lồi củ cơ delta.
  3. **LI15 (Kiên Ngung):** Bám trên xương bả vai phải (`Scapula_R`, `FJ3384`, `FMA:13395`), mỏm cùng vai.
- **Ranh giới an toàn giải phẫu:**
  - Tuyệt đối không gắn các huyệt chi dưới như ST36 (Túc Tam Lý - Xương chày) hay KI3 (Thái Khê - Xương gót) lên cánh tay. Hệ thống phân định rõ ràng và cảnh báo `ASSET_NOT_AVAILABLE` trên giao diện khi người dùng tra cứu huyệt chi dưới.

---

### 2. Đường Kinh Đại Trường 3D (Dynamic Meridian Pathway)
- Một đường cong 3D liên tục nối các điểm mốc `LI4` $\to$ `LI11` (vùng khuỷu) $\to$ `LI14` $\to$ `LI15`.
- Khi cánh tay nâng lên hoặc khuỷu tay gập lại, đường kinh tự động tính toán lại vị trí đỉnh trong không gian 3D, duy trì sự gắn kết thị giác mượt mà không bị đứt đoạn.

---

### 3. Khả Năng Tinh Chỉnh Thủ Công & Ngăn Xếp Undo/Redo
- **Chỉnh sửa:** Người dùng có thể điều chỉnh tọa độ mốc huyệt.
- **Quản lý phiên bản:** Mỗi thao tác chỉnh sửa tăng số hiệu `version` và ghi nhận `edit_author`.
- **Ngăn xếp Undo/Redo:**
  - Hỗ trợ hoàn tác (`Undo`) và làm lại (`Redo`) không giới hạn.
  - Phục hồi chính xác từng tọa độ mốc đã tinh chỉnh.
- **Trạng thái an toàn quản trị:**
  - Mọi mốc chỉnh sửa thủ công tự động mang trạng thái `MANUALLY_ADJUSTED` và `EXPERT_REVIEW_PENDING`.
  - Nghiêm cấm hệ thống tự phong `CLINICAL_APPROVED` hoặc `ANATOMICAL_VERIFIED`.

---

### 4. Kết Luận Gói C
- **G1 Functional Acceptance:** `PASS`
- **G2 Data Integrity:** `PASS`
- **G3 Domain Validity:** `PENDING`
- **G4 Independent Engineering Acceptance:** `PASS`
