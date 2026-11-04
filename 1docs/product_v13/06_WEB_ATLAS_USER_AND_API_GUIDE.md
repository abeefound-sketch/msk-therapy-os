# MSK-THERAPY-OS V1.3 — TÀI LIỆU HƯỚNG DẪN SỐ 06
## UNIVERSAL WEB ATLAS USER & API OPERATION GUIDE

- **Môi trường:** Offline-first, Windows 11, WebGL 2.0
- **URL giao diện chính:** `http://127.0.0.1:8000/character_v13/index.html`
- **Phân loại sử dụng:** Nghiên cứu kỹ thuật mô phỏng giải phẫu số (`ENGINEERING_RESEARCH_ONLY`)
- **Cảnh báo y khoa:** KHÔNG PHẢI THIẾT BỊ Y TẾ (`CLINICAL_VALIDATION = NOT_ESTABLISHED`)

---

### 1. KHỞI ĐỘNG HỆ THỐNG

1. **Khởi chạy máy chủ cục bộ:**
   Chạy tệp batch `run_msk_therapy_os.bat` hoặc thực thi lệnh trong terminal:
   ```powershell
   cd D:\5Projects\msk-therapy-os
   C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe msk_therapy_os/server.py --port 8000
   ```
2. **Mở trình duyệt Web Atlas:**
   Truy cập theo URL:
   ```
   http://127.0.0.1:8000/character_v13/index.html
   ```

---

### 2. TỔNG QUAN BỐ CỤC GIAO DIỆN

```
┌─────────────────────────────────┬──────────────────────────────────────────┐
│  VIEWPORT 3D (Three.js WebGL)   │  BẢNG ĐIỀU KHIỂN UNIVERSAL ABS           │
│                                 │                                          │
│  - OrbitControls:               │  [1] Lớp Hiển Thị (5 Layers)             │
│    * Chuột trái: Xoay góc nhìn  │      - [x] Xương  [x] Cơ  [x] Da         │
│    * Chuột phải: Di chuyển pan  │      - [x] Huyệt vị   [x] Kinh lạc      │
│    * Con lăn: Phóng to / Thu nhỏ│                                          │
│                                 │  [2] Vận Động Khớp Đa Vùng               │
│  - Mô hình nhân vật toàn thân:  │      - Tay: Elbow (0-120°), Shoulder     │
│    * 53 Canonical Bones         │      - Chân: Knee (0-90°), Hip (-15-60°) │
│    * 9 Xương BodyParts3D        │      - Thân: Torso Twist (-30-30°)       │
│    * 10 Cơ BodyParts3D          │      - Nút: Tay 90°, Gối 60°, Đồng Thời! │
│    * Da thật MakeHuman toàn thân│                                          │
│    * 6 Mốc huyệt & 2 Đường kinh │  [3] Vóc Dáng (7 Morph Targets)          │
│                                 │      - Presets: Broader, Slender, Length │
│  - HUD Telemetry thời gian thực:│                                          │
│    * Biceps Co %, Bulge mm      │  [4] Thanh Tra Giải Phẫu (Inspector)     │
│    * Quads Căng %, Khe khớp mm  │      - Tên, FMA ID, Xương cha, Strategy  │
│    * Độ xuyên mesh: 0.00 mm     │                                          │
│    * Viewport FPS: ~60 native   │  [5] Quản Lý Dự Án: Lưu / Mở / Đặt Lại   │
└─────────────────────────────────┴──────────────────────────────────────────┘
```

---

### 3. HƯỚNG DẪN CÁC THAO TÁC CƠ BẢN

#### A. Thử nghiệm vận động đồng thời tay và chân (Simultaneous Motion)
1. Nhấp vào nút **⚡ Đồng Thời (Tay 90° + Gối 60°)** hoặc tự điều chỉnh thanh trượt:
   - Kéo **Elbow Flexion** lên $90.0^\circ$.
   - Kéo **Knee Flexion** lên $60.0^\circ$.
   - Kéo **Torso Twist** lên $15.0^\circ$.
2. Quan sát trực tiếp trên viewport 3D:
   - Cánh tay phải gập vuông góc, cơ nhị đầu phồng to $+14.1\%$ ($47.9\text{ mm}$).
   - Khớp gối phải gập $60^\circ$, cẳng chân gấp ra sau, cơ tứ đầu đùi giãn $+8.9\%$.
   - Mốc huyệt LI4 trên bàn tay nâng cao $+0.280\text{ m}$.
   - Mốc huyệt ST36 trên cẳng chân nâng cao $+0.041\text{ m}$.
   - Hai ống kinh lạc 3D uốn cong tự nhiên theo các khớp đang vận động.

#### B. Chuyển đổi 3 chế độ hiển thị chuyên sâu (Display Modes)
- **✨ Xuyên Thấu (Overlay):** Hiển thị toàn bộ các lớp (da trong mờ $40\%$, lộ rõ cơ xương và huyệt vị bên trong).
- **🦴 Cơ Xương (Musculoskeletal):** Ẩn hoàn toàn lớp da, tập trung khảo sát 9 xương và 10 cơ BodyParts3D.
- **👤 Da Thật (Living Skin):** Da MakeHuman hiển thị $100\%$ mờ đục tự nhiên như một nhân vật game sống động.

#### C. Thử nghiệm biến dạng vóc dáng (Morph Targets)
1. Nhấp nút preset **Vận Động Viên (Broader)** hoặc kéo thanh trượt `Broader = 0.8`.
2. Quan sát lớp da nở rộng bao bọc khối cơ bắp mà không gây đâm xuyên đa giác.
3. Nhấp nút **Chân Dài (LongLeg)** để kéo dài cẳng chân thêm $+5\%$.

#### D. Thanh tra giải phẫu (Anatomy Inspector)
1. Chọn một cấu trúc từ danh sách thả xuống (ví dụ: `Xương đùi Right Femur`, `Cơ thẳng đùi Rectus femoris`, hoặc `Huyệt Túc Tam Lý ST36`).
2. Bảng thông tin sẽ lập tức hiển thị tên tiếng Việt, tên tiếng Anh, mã FMA, xương gắn kết, chiến lược binding và nguồn dữ liệu DBCLS.

---

### 4. GIAO DIỆN LẬP TRÌNH TỰ ĐỘNG HÓA (PROGRAMMATIC API)

Browser console cung cấp đối tượng toàn cục `window.__UNIVERSAL_ABS_V13__`:

```javascript
// Kiểm tra trạng thái nạp
console.log("Model loaded:", window.__UNIVERSAL_ABS_V13__.isLoaded());

// Lấy thông tin khung xương (53 bones)
const sk = window.__UNIVERSAL_ABS_V13__.getSkeletonInfo();
console.log("Bone count:", sk.boneCount, "Has Leg Bones:", sk.hasLegBones);

// Đặt vận động gập khuỷu 90° và gập gối 60°
window.__UNIVERSAL_ABS_V13__.setJointAngle("lowerarm_r", "x", 90);
window.__UNIVERSAL_ABS_V13__.setJointAngle("calf_r", "x", 60);

// Đặt biến dạng vóc dáng
window.__UNIVERSAL_ABS_V13__.setMorphInfluence("Broader", 0.8);

// Lấy số liệu đo đạc hình học thực tế
const metrics = window.__UNIVERSAL_ABS_V13__.getEvaluatedMetrics();
console.log("Biceps Shorten:", metrics.biceps_shortening_pct, "%");
console.log("Quad Stretch:", metrics.quad_stretch_pct, "%");
console.log("Knee Gap:", metrics.knee_gap_mm, "mm");

// Đặt lại toàn bộ về thế nghỉ
window.__UNIVERSAL_ABS_V13__.resetPose();
```
