# MSK-Therapy-OS — Milestone P21 Asset License & Attribution Audit
## P21_02: Asset Licensing, Copyleft Analysis & Attribution Registry

**Tài liệu ID:** `MSK-P21-AUD-002`  
**Ngày thực hiện:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Vai trò:** Principal Software & IP Compliance Auditor  
**Trạng thái Thẩm định:** `LICENSING_AUDIT_VERIFIED`  

---

### 1. Phân định Cốt lõi: Cấp phép Mã nguồn (Code) vs Cấp phép Tài nguyên (Assets/Data)

Một nguyên tắc pháp lý bất di bất dịch trong kiểm toán phần mềm y tế và đồ họa 3D là: **Giấy phép mã nguồn mở (như MIT, Apache-2.0) của một kho lưu trữ KHÔNG tự động cấp quyền tương tự cho các tệp mô hình 3D, dữ liệu giải phẫu, hoặc trọng số đi kèm.**

| Thành phần | Loại tài sản | Giấy phép áp dụng | Quyền thương mại | Ràng buộc kế thừa (Copyleft) |
|---|---|---|---|---|
| **Mã nguồn ứng dụng (Viewer / Engine)** | Scripts, UI, WebGL shaders | **MIT License** | Cho phép | Không (Permissive) |
| **Dữ liệu giải phẫu BodyParts3D 4.0** | `atlas.json`, `body-*.bin` | **CC BY 4.0 International** | Cho phép (Kèm ghi công) | Không có ràng buộc ShareAlike |
| **Mô hình Z-Anatomy** | `body.glb` (Draco) | **CC BY-SA 4.0 International** | Bị hạn chế bởi Copyleft | **Có (ShareAlike Bắt buộc)** |
| **Mô hình Sketchfab (Meridian Studio)** | `female-character.glb`, `male_character.glb` | **CC BY 4.0** | Cho phép (Kèm ghi công) | Không có ràng buộc ShareAlike |

---

### 2. Phân tích Rủi ro Copyleft: Tại sao CC BY-SA 4.0 của Z-Anatomy bị cách ly khỏi Production?

Mô hình `body.glb` trong `3refs/upstream/tcm-acupoints` có nguồn gốc từ dự án **Z-Anatomy**, được cấp phép dưới điều khoản **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**:

1. **Điều khoản ShareAlike (SA - Chia sẻ tương tự):** Theo Điều 3(b) của CC BY-SA 4.0, nếu bất kỳ tác phẩm phái sinh (Adapter, Model kết hợp, Mesh chỉnh sửa) nào được phân phối công khai, toàn bộ tác phẩm phái sinh đó **bắt buộc phải được phân phối dưới cùng một giấy phép CC BY-SA 4.0**.
2. **Rủi ro lây lan (Viral License Risk):** Nếu MSK-Therapy-OS nhúng trực tiếp `body.glb` của Z-Anatomy vào gói phân phối thương mại hoặc mã độc quyền của hệ điều hành, giấy phép ShareAlike có thể buộc toàn bộ gói dữ liệu giải phẫu đi kèm phải mở mã nguồn và chia sẻ tự do, gây xung đột với các thỏa thuận bảo mật y tế hoặc mô hình thương mại tương lai.
3. **Phán quyết:** Tệp `body.glb` của Z-Anatomy được xếp vào trạng thái **`EVALUATION_ONLY_RESTRICTED`**, KHÔNG được chọn làm nguồn dữ liệu chính thức cho Atlas core của MSK-Therapy-OS.

---

### 3. Đánh giá Tính Khả thi và Pháp lý của Nguồn Khuyến nghị: BodyParts3D 4.0

Dữ liệu giải phẫu từ **BodyParts3D Release 4.0** (Database Center for Life Science - DBCLS, Nhật Bản) là ứng viên được lựa chọn chính thức:

1. **Giấy phép CC BY 4.0 (Creative Commons Attribution 4.0 International):**
   - **Tự do sử dụng:** Cho phép sao chép, phân phối, trích xuất và biến đổi cho bất kỳ mục đích nào, kể cả thương mại.
   - **Không có ShareAlike:** Không ép buộc mã nguồn hay tác phẩm phái sinh phải mở mã nguồn.
   - **Yêu cầu duy nhất:** Bắt buộc phải duy trì ghi công (Attribution) đúng quy cách tới DBCLS Japan và cung cấp liên kết tới giấy phép CC BY 4.0.
2. **Nguồn gốc dữ liệu chuẩn hóa:** Mô hình được phân đoạn trực tiếp từ dữ liệu chụp cộng hưởng từ (MRI) và cắt lớp vi tính (CT) của một đối tượng nam giới trưởng thành chuẩn, liên kết trực tiếp với hệ thống từ vựng bản thể học giải phẫu FMA (Foundational Model of Anatomy).

---

### 4. Bảng Ghi công Chính thức (Mandatory Attribution Notices)

Khi phân phối hoặc hiển thị giao diện PoC P21, hệ thống phải hiển thị rõ các thông cáo bản quyền sau:

#### A. Dữ liệu Giải phẫu BodyParts3D 4.0
```markdown
Anatomical 3D Data:
BodyParts3D, © The Database Center for Life Science (DBCLS) Japan, licensed under 
Creative Commons Attribution 4.0 International (CC BY 4.0).
Source: https://lifesciencedb.jp/bp3d/
Original FMA Ontology mappings: University of Washington Structural Informatics Group.
```

#### B. Nền tảng Human Atlas Web Viewer
```markdown
Human Atlas Client Engine:
Copyright (c) 2026 ashemag & spacejohnlf.
Licensed under the MIT License (public/CODE-LICENSE.txt).
```

#### C. Mô hình Tham chiếu Thể biểu (Nếu sử dụng cho kiểm tra da)
```markdown
External Surface Character Models:
1. Male Character: Created by MaceLogice, licensed under CC BY 4.0.
   Source: https://sketchfab.com/3d-models/male-character-29372cc7dfcc4c88b34ecf1f40cdc35a
2. Female Character: Created by yuzutarou (@yuzuponponpon), licensed under CC BY 4.0.
   Source: https://sketchfab.com/3d-models/female-15ee49542e3d4cc3aa9dec99ea3f46be
```

---

### 5. Kết luận Kiểm toán Pháp lý P21

- **Nguồn được phép tích hợp vào PoC P21:** **BodyParts3D 4.0** (CC BY 4.0). Đáp ứng đầy đủ tiêu chí không lây nhiễm copyleft, cho phép mở rộng offline, có thể phân phối hợp pháp kèm bản quyền ghi công rõ ràng.
- **Nguồn bị cách ly (Quarantine / Restricted):**
  - **Z-Anatomy (CC BY-SA 4.0):** Cách ly do ràng buộc ShareAlike.
  - **TARA (NIH):** Tạm thời cách ly (`QUARANTINE_REMOTE`) do chưa có gói phân phối offline cục bộ và cần thỏa thuận chuyển giao học thuật nếu thương mại hóa.
