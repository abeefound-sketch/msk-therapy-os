# MSK-Therapy-OS — Milestone P23 Audit
## P23_00: Upstream Motion Capture & Biomechanics Data Register

**Tài liệu ID:** `MSK-P23-AUD-000`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Danh mục Dữ liệu Chuyển động Thật Thượng nguồn (Upstream Sources)

Hệ thống tích hợp dữ liệu chuyển động từ hai nguồn nghiên cứu cơ sinh học chuẩn mực quốc tế:

| Nguồn Thượng Nguồn | Tệp tin / Phiên bản | Kích thước | Mã băm SHA-256 | Vai trò & Đặc tính Kỹ thuật | Giấy phép & Điều kiện |
|---|---|---|---|---|---|
| **CMU Graphics Lab Motion Capture Database** | `02.asf` | 7,268 B | `c9f5ff45b4437b2781b0a70199dc6374f4b2383be992c3a5ef5268c740ee3fc2` | Cấu trúc khung xương chuẩn Acclaim Skeleton Format (VICON 120 FPS) | Miễn phí cho nghiên cứu và giáo dục; Cấm bán lại độc lập |
| **CMU Graphics Lab Motion Capture Database** | `02_01.amc` | 273,444 B | `1503c481f4726e643534b86866164f780879c53330e20ce9a35e7dfbb6a83602` | Dữ liệu chuyển động thực Acclaim Motion Capture (Subject 02 Trial 01) | Miễn phí cho nghiên cứu; Cấm thương mại hóa dữ liệu thô |
| **OpenSim Seth Scapulothoracic Model** | `seth_shoulder_elevation.mot` | 1,292 B | `78e12b7a05fe8a82cf4f1eb8ad56f8f553a1a985e509d73d6ebac7e74288ceb9` | 21 khung hình nâng vai cơ sinh học (0° đến 120°) có nhịp bả vai - cánh tay | Apache 2.0 (Stanford SimTK) |

---

### 2. Khai báo Giới hạn Sử dụng CMU (Motion Prior Notice)

- Dữ liệu CMU Motion Capture được sử dụng thuần túy làm **Motion Prior (mẫu chuyển động quan sát tham khảo)** để định hướng tư thế mượt mà.
- **TUYỆT ĐỐI KHÔNG dùng giá trị cực trị min/max quan sát được trong CMU để làm ranh giới giải phẫu học (Anatomical ROM)** hay tiêu chuẩn an toàn y tế.
- Mọi giới hạn an toàn phải dựa trên y văn giải phẫu có dẫn chiếu (Kapandji, AAOS).
