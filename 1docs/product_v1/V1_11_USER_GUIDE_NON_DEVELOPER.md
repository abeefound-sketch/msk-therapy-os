# SỔ TAY HƯỚNG DẪN SỬ DỤNG DÀNH CHO NGƯỜI DÙNG KHÔNG CHUYÊN
## MSK-Therapy-OS · Product V1.0 Desktop Edition

Chào mừng bạn đến với **MSK-Therapy-OS V1.0** — Hệ thống Nghiên Cứu Giải Phẫu 3D, Hình Thể Tham Số & Chuyển Động Cơ Xương Khớp.  
Ứng dụng được thiết kế tối ưu cho các nhà nghiên cứu, giảng viên, sinh viên y khoa và chuyên viên vận động học trên môi trường Windows mà **không cần kiến thức lập trình hay kỹ năng sử dụng Blender**.

---

### 1. Khởi Động Ứng Dụng (1-Click Launch)
1. Mở thư mục dự án `MSK-Therapy-OS` trên máy tính của bạn.
2. Nhấp đúp chuột trái vào tệp:
   ```text
   run_msk_therapy_os.bat
   ```
3. Cửa sổ dòng lệnh sẽ tự động khởi động máy chủ cục bộ và trình duyệt web mặc định (Chrome, Edge hoặc Firefox) sẽ tự động mở trang làm việc tại:
   `http://127.0.0.1:8000/sandbox/p21/index.html`

> [!TIP]
> Bạn không cần cài đặt thêm bất kỳ phần mềm 3D nào khác. Toàn bộ mô hình chạy trực tiếp bằng công nghệ WebGL trên trình duyệt.

---

### 2. Các Thao Tác Cơ Bản Trên Khung Nhìn 3D
- **Xoay mô hình:** Nhấn giữ **chuột trái** và kéo để quay mô hình 360 độ.
- **Di chuyển góc nhìn (Pan):** Nhấn giữ **chuột phải** và kéo để dịch chuyển góc nhìn lên/xuống/trái/phải.
- **Phóng to / Thu nhỏ (Zoom):** Cuộn **bánh lăn chuột** tới hoặc lui.

---

### 3. Hướng Dẫn Sử Dụng Năm Tính Năng Cốt Lõi

#### A. Khám Phá Lớp Giải Phẫu (Anatomy Layers)
- Ở cột bên trái, đánh dấu hoặc bỏ đánh dấu các ô:
  - 🦴 **Hệ Xương (Bone):** Hiển thị toàn bộ khung xương.
  - 💪 **Hệ Cơ (Muscle):** Hiển thị các bó cơ vận động.
  - 🫀 **Nội Tạng (Viscera):** Hiển thị tim, phổi, gan, dạ dày...
  - 👤 **Lớp Da (Skin):** Điều chỉnh thanh trượt **"Độ mờ da"** (từ 0% đến 100%) để nhìn xuyên qua da vào các cấu trúc bên trong.
- **Kiểm tra thông tin chi tiết:** Nhấp chuột vào bất kỳ chiếc xương hoặc cơ bắp nào, bảng bên phải sẽ lập tức hiển thị tên quốc tế, mã số FMA và nguồn bản quyền.

#### B. Thay Đổi Hình Thể Tham Số (Parametric Body)
- Ở thẻ **"Hình Thể Tham Số"** (bên trái), nhấp vào một trong bốn nút mẫu:
  - **`[Baseline]`**: Vóc dáng chuẩn tham chiếu (Cao $1.73\text{m}$, tỷ lệ tay chuẩn).
  - **`[Slender]`**: Vóc dáng mảnh khảnh, cao ráo.
  - **`[Broader]`**: Vóc dáng vạm vỡ, chu vi bắp tay dày hơn.
  - **`[Longer Arm]`**: Cánh tay dài vượt trội.
- Hoặc bạn có thể tự tay kéo các thanh trượt **Chiều cao**, **Chiều dài tay** và **Chu vi tay** theo ý muốn.
- Khi muốn quay về chuẩn ban đầu, chỉ cần nhấp lại nút **`[Baseline]`**.

#### C. Khám Phá Huyệt Vị Động & Đường Kinh (Acupoints)
- Hệ thống tích hợp sẵn 3 mốc huyệt chi trên theo chuẩn WHO 2008:
  - **Hợp Cốc (`LI4`)**: Nằm trên xương đốt bàn tay II.
  - **Tí Nhu (`LI14`)**: Nằm trên bờ ngoài xương cánh tay.
  - **Kiên Ngung (`LI15`)**: Nằm trên mỏm cùng vai của xương bả vai.
- Đường kinh màu xanh lam tự động uốn lượn nối các huyệt vị này theo vị trí thực tế của cánh tay.
- Nếu bạn có tinh chỉnh vị trí huyệt, có thể nhấp nút **`[↩️ Undo]`** để quay lại hoặc **`[↪️ Redo]`** để làm lại.

#### D. Điều Khiển & Phát Lại Chuyển Động (Motion & Mouse Pose)
Ở góc dưới bên phải có thẻ **"Động Học & Tri Thức Y Văn"**:
1. **Chế độ xem video chuyển động (`🎬 Video 100f`):**
   - Nhấp nút **`▶ Phát`** để xem cánh tay chuyển động nâng lên và gập khuỷu theo dữ liệu video thực tế.
   - Kéo thanh trượt **Timeline (0–99)** để dừng lại ở từng khung hình cụ thể.
   - Quan sát xương cánh tay và bả vai di chuyển nhịp nhàng theo tỷ lệ cơ sinh học $2:1$.
2. **Chế độ kéo chuột tạo dáng (`🖐️ Mouse Pose`):**
   - Nhấp vào nút **`🖐️ Mouse Pose`**.
   - Kéo thanh trượt **"Nâng vai chuột"** ($0^\circ - 120^\circ$) hoặc **"Gập khuỷu chuột"** ($0^\circ - 130^\circ$) để trực tiếp điều khiển tư thế của cánh tay.
   - Nhấp nút **`↺ Trở về tư thế gốc`** để đưa tay về trạng thái buông thõng tự nhiên.

#### E. Lưu Dự Án & Xuất Báo Cáo Y Văn
- **Lưu phiên làm việc:** Nhấp vào nút **`[💾 Lưu Dự Án]`** ở thanh trên cùng để tải về tệp `.mskproj` chứa toàn bộ vóc dáng, tư thế và mốc huyệt hiện tại.
- **Mở lại dự án cũ:** Nhấp vào nút **`[📂 Mở Dự Án]`** và chọn tệp `.mskproj` đã lưu từ máy tính để tiếp tục làm việc.
- **Xuất báo cáo khoa học:** Nhấp vào nút **`[📄 Xuất Báo Cáo MSK-Therapy-OS V1.0]`** để xem và tải về bản tóm tắt nghiên cứu hoàn chỉnh định dạng Markdown.

---

### 4. Ranh Giới An Toàn & Khuyến Cáo
> [!WARNING]
> Phần mềm được phát hành với phạm vi `ENGINEERING_RESEARCH_ONLY` phục vụ mục đích nghiên cứu kỹ thuật tính toán và giảng dạy minh họa khoa học. Toàn bộ kết quả góc khớp và tọa độ huyệt vị **KHÔNG THAY THẾ CHẨN ĐOÁN LÂM SÀNG CỦA BÁC SĨ CHUYÊN KHOA** và không được sử dụng để tự ý điều trị trên người bệnh.
