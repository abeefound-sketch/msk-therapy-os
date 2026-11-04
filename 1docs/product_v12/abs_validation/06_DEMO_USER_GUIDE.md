# MSK-THERAPY-OS V1.2.1 — TÀI LIỆU HƯỚNG DẪN SỐ 06
## ANATOMICAL BINDING STUDIO USER & OPERATION GUIDE

- **Môi trường hoạt động:** Windows 11, Offline-first
- **Trình duyệt khuyến nghị:** Google Chrome, Microsoft Edge hoặc Chromium hỗ trợ WebGL 2.0
- **Phân loại sử dụng:** Nghiên cứu kỹ thuật đồ họa giải phẫu (ENGINEERING_RESEARCH_ONLY)
- **Tuyên bố an toàn:** KHÔNG PHẢI THIẾT BỊ Y TẾ (CLINICAL_VALIDATION = NOT_ESTABLISHED)

---

### 1. KHỞI ĐỘNG HỆ THỐNG

1. **Khởi động server cục bộ:**
   Nhấp đúp chuột vào tệp `run_msk_therapy_os.bat` tại thư mục gốc repository `D:\5Projects\msk-therapy-os`, hoặc mở PowerShell/CMD và thực thi lệnh:
   ```powershell
   cd D:\5Projects\msk-therapy-os
   C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe msk_therapy_os/server.py
   ```
2. **Mở giao diện Arm Studio V1.2.1:**
   Mở trình duyệt và truy cập theo đường dẫn URL:
   ```
   http://127.0.0.1:8000/character_v12/index.html
   ```

---

### 2. BỐ CỤC VÀ TÍNH NĂNG TRÊN GIAO DIỆN

Giao diện Studio được thiết kế trực quan gồm 4 khu vực chính:

```
┌─────────────────────────────────┬──────────────────────────────────────────┐
│  VIEWPORT 3D (Three.js WebGL)   │  BẢNG ĐIỀU KHIỂN & ĐO ĐẠC HÌNH HỌC       │
│                                 │                                          │
│  - OrbitControls:               │  [1] Vận Động Khớp (Kinematics)          │
│    * Chuột trái: Xoay góc nhìn  │      - Slider Elbow Flexion (0° - 120°)  │
│    * Chuột phải: Di chuyển pan  │      - Nút tư thế nhanh: 0°, 45°, 90°, 120│
│    * Con lăn: Phóng to / Thu nhỏ│                                          │
│                                 │  [2] Vóc Dáng Da (Morph Targets)         │
│  - Mô hình cánh tay:            │      - Sliders: Length, Width, Broader...│
│    * 5 xương BodyParts3D        │                                          │
│    * 6 cơ BodyParts3D           │  [3] Quản Lý 5 Lớp Hiển Thị              │
│    * Da thật MakeHuman          │      - [x] Xương  [x] Cơ bắp  [x] Da     │
│    * 4 mốc huyệt LI4-LI15       │      - [x] Huyệt vị   [x] Đường kinh     │
│    * Ống kinh lạc vàng 3D       │                                          │
│                                 │  [4] Bảng Đo Hình Học Thực Tế (Live HUD) │
│  [HUD FPS: ~60 native GPU]      │      - Biceps Shorten, Bulge, Joint Gap..│
│                                 │                                          │
│                                 │  [5] Quản Lý Dự Án: Lưu / Tải / Đặt lại  │
└─────────────────────────────────┴──────────────────────────────────────────┘
```

---

### 3. CÁC THAO TÁC CƠ BẢN

#### A. Thử nghiệm vận động gập khuỷu từ $0^\circ$ đến $120^\circ$
1. Kéo thanh trượt **Elbow Flexion** từ $0^\circ$ đến $120^\circ$ hoặc nhấp vào nút **120° (Deep)**.
2. Quan sát đồng thời:
   - Cẳng tay và bàn tay gấp sát về phía cánh tay.
   - Cơ nhị đầu co ngắn $-24.8\%$, bụng cơ phồng to thêm $+15.3\%$.
   - Khe khớp khuỷu giữ vững $2.40\text{ mm}$ không xuyên thấu xương.
   - Mốc huyệt LI4 trên mu bàn tay nâng cao $+0.312\text{ m}$.
   - Ống kinh lạc vàng 3D tự động uốn cong mềm mại theo góc khuỷu mới.

#### B. Thử nghiệm biến dạng vóc dáng da MakeHuman
1. Kéo thanh trượt **Broader** lên $0.8$ hoặc $1.0$.
2. Quan sát lớp da MakeHuman nở rộng cơ bắp bao trọn cấu trúc giải phẫu bên trong mà không gây rách lưới hay méo mó xương.
3. Kéo thanh trượt **Slender** để quan sát cơ chế thu hẹp vóc dáng mảnh mai.

#### C. Bật / Tắt các lớp giải phẫu theo nhu cầu
1. Bỏ chọn **Skin** để chuyển sang chế độ quan sát cơ xương giải phẫu chuyên sâu.
2. Bỏ chọn **Muscles** để khảo sát riêng khung xương cứng và vị trí các mốc huyệt.
3. Bật toàn bộ 5 lớp để có trải nghiệm tổng thể đầy đủ của nhân vật sống (Living Anatomy Character).

#### D. Lưu và Tải trạng thái dự án
1. Sau khi chỉnh sửa góc khớp và vóc dáng, nhập tên dự án vào ô văn bản (ví dụ: `Kham_Khuu_90_Do`) và nhấp nút **Lưu dự án**.
2. Khi cần khôi phục lại, chọn tên dự án từ danh sách và nhấp nút **Tải dự án**. Hệ thống sẽ khôi phục chính xác toàn bộ cấu hình 3D.
3. Nhấp nút **Đặt lại thế nghỉ (Reset Pose)** để đưa cánh tay về tư thế duỗi thẳng $0^\circ$ mặc định.

---

### 4. GIAO DIỆN LẬP TRÌNH TỰ ĐỘNG HÓA (PROGRAMMATIC JAVASCRIPT API)

Đối với các bài kiểm thử tự động (Playwright/Puppeteer) hoặc tích hợp mở rộng, console trình duyệt cung cấp đối tượng toàn cục `window.__ABS_V12_1__`:

```javascript
// Đặt góc gập khuỷu về 90 độ
window.__ABS_V12_1__.setJointAngle("lowerarm_r", "x", 90);

// Đặt trọng số morph cơ bắp
window.__ABS_V12_1__.setMorphInfluence("Broader", 0.8);

// Lấy số liệu đo đạc hình học thực tế
const biceps = window.__ABS_V12_1__.getBicepsDeformation();
console.log("Co ngắn:", biceps.shortening_pct, "%", "Đường kính:", biceps.belly_diameter_mm, "mm");

// Lấy tọa độ thế giới của huyệt Hợp Cốc
const li4 = window.__ABS_V12_1__.getAcupointWorldPos("LI4");
console.log("Tọa độ LI4:", li4);

// Kiểm tra khe khớp hoạt dịch
console.log("Khe khớp (mm):", window.__ABS_V12_1__.getArticularJointGapMm());
```
