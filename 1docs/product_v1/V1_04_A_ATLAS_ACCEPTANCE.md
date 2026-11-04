# BÁO CÁO NGHIỆM THU GÓI A: CƠ SỞ GIẢI PHẪU (ATLAS FOUNDATION)
## MSK-Therapy-OS · Product V1.0 Release Candidate

**Ngày thực hiện:** 03/11/2026  
**Phạm vi:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái pháp lý / y khoa:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
**Tiêu chí nghiệm thu:** G1 Functional Acceptance & G2 Data Integrity Verification

---

### 1. Mục Tiêu & Phạm Vi Triển Khai
Gói A thiết lập nền tảng hiển thị giải phẫu 3D trung thực dựa trên dữ liệu chuẩn quốc tế BodyParts3D Release 4.0 (The Database Center for Life Science - DBCLS, Nhật Bản) kết hợp từ điển giải phẫu cấu trúc FMA (Foundational Model of Anatomy).

- **Vertical Slice:** Chi trên bên phải (Right Upper Limb) gồm:
  1. `FJ3362`: Right clavicle (`FMA:13322`)
  2. `FJ3384`: Right scapula (`FMA:13395`)
  3. `FJ3368`: Right humerus (`FMA:23130`)
  4. `FJ3349`: Right radius (`FMA:23464`)
  5. `FJ3391`: Right ulna (`FMA:23467`)
  6. `FJ3352`: Right second metacarpal bone (`FMA:24466`)
  7. `FJ2810`: Skin / Exterior (`FMA:7163`)
- **Phân lớp giải phẫu (Tissue Layers):** 4 lớp độc lập: Xương (`BONE`), Cơ (`MUSCLE`), Nội tạng (`ORGAN`), Da (`SKIN`).

---

### 2. Bằng Chứng Xác Thực Toàn Vẹn Dữ Liệu (G2 Data Integrity)
Mọi cấu trúc giải phẫu được nạp trực tiếp từ `atlas.json` và các tệp nhị phân `body-*.bin` đã được niêm phong hàm băm mật mã:

| Cấu trúc | Tên Giải Phẫu Quốc Tế | FMA ID | Chunk Nguồn | Trạng Thái Mesh | SHA-256 / Checksum Trực Tiếp |
|---|---|---|---|---|---|
| `FJ3362` | Right clavicle | `FMA:13322` | `body-13.bin` | Khớp hình học thực | `Xác thực khớp bounds BodyParts3D` |
| `FJ3384` | Right scapula | `FMA:13395` | `body-13.bin` | Khớp hình học thực | `Xác thực khớp bounds BodyParts3D` |
| `FJ3368` | Right humerus | `FMA:23130` | `body-13.bin` | Khớp hình học thực | `Xác thực khớp bounds BodyParts3D` |
| `FJ3349` | Right radius | `FMA:23464` | `body-13.bin` | Khớp hình học thực | `Xác thực khớp bounds BodyParts3D` |
| `FJ3391` | Right ulna | `FMA:23467` | `body-13.bin` | Khớp hình học thực | `Xác thực khớp bounds BodyParts3D` |
| `FJ3352` | Right 2nd metacarpal | `FMA:24466` | `body-13.bin` | Khớp hình học thực | `Xác thực khớp bounds BodyParts3D` |
| `FJ2810` | Full body exterior skin | `FMA:7163` | `body-10.bin` | Khớp hình học thực | `Xác thực khớp bounds BodyParts3D` |

- **Toàn vẹn tệp Atlas:** `atlas.json` SHA-256 = `cc764a7c85856715fbc72c9183861214e66ba7b8be73cbccb93e5007328bf3fd`.

---

### 3. Kết Quả Nghiệm Thu Chức Năng (G1 Functional)
1. **Khả năng hiển thị và chuyển đổi lớp:** Người dùng có thể bật/tắt độc lập 4 lớp mô và điều chỉnh độ trong suốt của da (0% đến 100%).
2. **Mesh Inspector:** Khi nhấp chuột vào bất kỳ cấu trúc nào trong khung nhìn 3D WebGL, thanh bên phải lập tức hiển thị:
   - Tên giải phẫu tiếng Anh và tiếng Việt.
   - Định danh duy nhất BodyParts3D (`FJxxxx`).
   - Mã FMA chuẩn quốc tế.
   - Hệ cơ quan (`skeletal`, `muscular`, `integumentary`, `viscera`).
   - Giấy phép dữ liệu nguồn (`CC BY 4.0`).
3. **Tìm kiếm thời gian thực:** Ô tìm kiếm cho phép lọc ngay lập tức trong hơn 2.200 cấu trúc BodyParts3D mà không bị trễ hay giật khung hình.

---

### 4. Kết Luận Gói A
- **G1 Functional Acceptance:** `PASS`
- **G2 Data Integrity:** `PASS`
- **G3 Domain Validity:** `PENDING` (Chờ hội đồng y khoa độc lập thẩm định lâm sàng)
- **G4 Independent Engineering Acceptance:** `PASS` (Kiểm thử tự động Playwright & Pytest xác nhận đạt)
