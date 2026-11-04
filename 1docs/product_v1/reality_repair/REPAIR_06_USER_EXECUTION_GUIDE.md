# HƯỚNG DẪN TỰ KIỂM CHỨNG DÀNH CHO KIỂM TOÁN VIÊN ĐỘC LẬP
## MSK-Therapy-OS V1.0 — Reality Repair Phase

**Phạm vi:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái thẩm định lâm sàng:** `CLINICAL_VALIDATION: NOT_ESTABLISHED`

---

### 1. KHỞI ĐỘNG ỨNG DỤNG THỰC TẾ

Kiểm toán viên độc lập có thể khởi động hệ thống theo một trong hai cách:

#### Cách 1: Sử dụng tệp thực thi tự động (Khuyến nghị trên Windows)
Nhấp đúp chuột vào tệp:
```cmd
D:\5Projects\msk-therapy-os\run_msk_therapy_os.bat
```

#### Cách 2: Khởi động trực tiếp bằng dòng lệnh Python
Mở PowerShell hoặc Command Prompt tại thư mục dự án và chạy:
```powershell
Set-Location "D:\5Projects\msk-therapy-os"
python msk_therapy_os/server.py --port 8199
```

Khi máy chủ khởi động thành công, mở trình duyệt (Google Chrome, Microsoft Edge hoặc Mozilla Firefox) tại địa chỉ:
```
http://localhost:8199/sandbox/p21/index.html
```

---

### 2. QUY TRÌNH KIỂM CHỨNG TỪNG HẠNG MỤC (MANUAL VERIFICATION STEPS)

#### Bước 1: Kiểm chứng Vị trí Huyệt Hợp Cốc (LI4)
1. Trên giao diện 3D, quan sát bàn tay phải của mô hình.
2. Tìm điểm cầu màu vàng hổ phách có nhãn **Hợp Cốc (LI4)**.
3. Bấm nút `🦾 Chi Trên Phải` trên thanh công cụ đỉnh màn hình (Viewport Toolbar).
4. Quan sát: Mốc LI4 bám chính xác vào bờ quay xương đốt bàn tay II phải (`Metacarpal_2_R`).
5. Kiểm tra danh sách điểm ở cột phải (Tab "Huyệt Vị"): Mốc LI4 được gắn nhãn xanh lục `CANONICAL (WHO 2008)`.
6. Tuyệt đối không còn bất kỳ điểm đánh dấu LI4 nào bám vào xương đòn trái (`Left clavicle`).

#### Bước 2: Kiểm chứng Rào chắn An toàn khi Gắn sai Cấu trúc
1. Chuyển sang chế độ `Đánh dấu huyệt thủ công` (bấm nút `🎯 Đánh Dấu Huyệt` ở cột trái, Tab "Công Cụ").
2. Nhấp chuột vào Xương đòn trái (`FJ3237`).
3. Trong hộp thoại mở ra, nhập mã huyệt là `LI4` và bấm **Xác Nhận Lưu Điểm**.
4. Quan sát: Điểm vừa tạo xuất hiện trong danh sách với viền đỏ và nhãn `INVALID_BINDING` kèm cảnh báo:  
   *⚠️ Gắn sai cấu trúc giải phẫu! Huyệt LI4 theo WHO 2008 bám trên Xương đốt bàn tay II, không thể gắn vào Xương đòn.*

#### Bước 3: Kiểm chứng Không Nhân Đôi Ma Trận (Zero Double Transform)
1. Ở cột bên trái, chuyển sang Tab **Hình Thể** (Tab 2).
2. Kéo thanh trượt `Chiều dài tay phải` lên mức tối đa `1.15x`.
3. Kéo thanh trượt `Chu vi tay phải` lên mức `1.20x`.
4. Quan sát trực tiếp trên khung nhìn 3D:
   - Cánh tay và cẳng tay dài và to ra một cách tự nhiên, tỷ lệ đồng nhất.
   - Đầu dưới xương cánh tay và đầu trên xương cẳng tay nối khít tại khớp khuỷu, không bị đứt rời hay phình to bất thường.
5. Bấm nút preset `Baseline`: Toàn bộ các thanh trượt trở về `1.00x` và chỉ số hoàn nguyên hiển thị:  
   `0.000000 m (Không trôi số học)`.

#### Bước 4: Kiểm chứng Động Học & Đường Kinh 3D
1. Ở cột bên phải, chuyển sang Tab **Động Học** (Tab 1).
2. Chuyển sang chế độ `🖐️ Mouse Pose`.
3. Kéo thanh trượt `Nâng vai chuột` lên $60^\circ$ và `Gập khuỷu chuột` lên $45^\circ$.
4. Quan sát:
   - Cánh tay nâng lên và cẳng tay gập lại mượt mà.
   - Cả 4 mốc huyệt `LI4`, `LI11`, `LI14`, `LI15` di chuyển đồng bộ theo xương.
   - Đường kinh Thủ Dương Minh Đại Trường (màu xanh dương) uốn cong liên tục nối liền 4 mốc trong không gian 3D.

#### Bước 5: Kiểm chứng Thanh Công Cụ Khung Nhìn (Viewport Navigation Toolbar)
1. Bấm `🦴 Ẩn Da Khi Vận Động`: Lớp da toàn thân lập tức biến mất, để lộ rõ khung xương và cơ bắp đang chuyển động mà không bị hiện tượng xương đâm xuyên qua da.
2. Bấm lại `🦴 Hiện Lớp Da`: Lớp da phục hồi độ mờ ban đầu (35%).
3. Bấm `🔍 Toàn Thân`: Camera tự động lùi xa và căn giữa toàn bộ cơ thể.
4. Chọn một cơ quan nội tạng (ví dụ Tim hoặc Gan) rồi bấm `👁️ Cô Lập`: Tất cả các cấu trúc khác bị ẩn đi, chỉ còn cơ quan được chọn hiển thị. Bấm lại để bỏ cô lập.

---

### 3. CHẠY BỘ KIỂM THỬ TỰ ĐỘNG PLAYWRIGHT E2E

Để máy tính tự động hóa toàn bộ quy trình kiểm toán 8 bước trên và chụp ảnh lưu bằng chứng:
```powershell
Set-Location "D:\5Projects\msk-therapy-os"
pytest tests/test_v1_reality_repair_e2e.py -v
```
Toàn bộ ảnh chụp màn hình sẽ được cập nhật tại thư mục:
```
D:\5Projects\msk-therapy-os\1docs\product_v1\reality_repair\evidence/
```
