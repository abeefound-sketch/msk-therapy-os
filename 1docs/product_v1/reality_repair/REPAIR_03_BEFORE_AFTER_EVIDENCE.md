# BẰNG CHỨNG ĐỐI CHIẾU TRƯỚC VÀ SAU SỬA CHỮA (BEFORE/AFTER EVIDENCE)
## MSK-Therapy-OS V1.0 — Reality Repair Phase

**Phạm vi:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái thẩm định lâm sàng:** `CLINICAL_VALIDATION: NOT_ESTABLISHED`

---

### 1. BẢNG TỔNG HỢP ĐỐI CHIẾU TRƯỚC VÀ SAU

| Tiêu Chí Kiểm Toán | Trước Khi Sửa Chữa (Pre-Repair V1.0) | Sau Khi Sửa Chữa (Post-Repair V1.0) | Kết Quả Đánh Giá |
| :--- | :--- | :--- | :--- |
| **Vị trí mốc LI4 (Hợp Cốc)** | Gắn trên Xương đòn trái `FJ3237` (Vùng ngực/cổ trái `[0.045, 1.412, 0.021] m`). | Bám chuẩn xác trên Xương đốt bàn tay II phải `FJ3352` (`[-0.280, 0.835, 0.035] m`). | **PASS** (Khớp 100% WHO 2008) |
| **Bảo vệ gắn sai giải phẫu** | Chấp nhận lưu mọi cấu trúc bừa bãi không cảnh báo. | Kích hoạt `INVALID_BINDING` và cảnh báo đỏ nếu LI4 không gắn vào Metacarpal II. | **PASS** (Bảo vệ tính toàn vẹn) |
| **Tỷ lệ scale cẳng tay (Length: 1.15, Circum: 1.20)** | Cẳng tay bị nhân đôi $1.15^2 = 1.3225$; $1.20^2 = 1.440$. Bàn tay bị nhân ba ($1.5209; 1.728$). | Khớp giữ nguyên $(1.0, 1.0, 1.0)$; Vỏ hiển thị nhận chính xác $(1.20, 1.15, 1.20)$. | **PASS** (Triệt tiêu Double Transform) |
| **Khoảng cách tâm khớp khuỷu** | Bị đứt gãy khớp khi scale hoặc xoay (lệch $> 11\text{ cm}$). | Nối khít tại tâm khớp giải phẫu `[-0.190, 1.122, -0.024] m` với sai số $< 1.3\text{ mm}$. | **PASS** (Bảo toàn chuỗi động học) |
| **Độ hoàn nguyên nhân trắc học** | Kéo thanh trượt rồi về Baseline có nguy cơ trôi dạt tọa độ. | Hoàn nguyên chính xác $0.000000\text{ m}$ (Không trôi số học). | **PASS** (Zero Drift) |
| **Phân tầng danh mục Tạng** | Hiển thị 1.491 Tạng chung chung gây nhầm lẫn. | Phân định minh bạch: 249 Tạng chính (Core) + 1.242 Mạch máu & Thần kinh. | **PASS** (Minh bạch dữ liệu) |
| **Đường kinh Thủ Dương Minh 3D** | 18 đường polyline rác tích lũy từ test tự động cũ. | Dọn sạch kho lưu trữ; tạo đường kinh 3D động kết nối `LI4 -> LI11 -> LI14 -> LI15`. | **PASS** (Đồng bộ chuyển động thật) |
| **Bố cục giao diện người dùng** | Cuộn trang dọc kéo dài, khó kiểm soát các nhóm công cụ. | Tái cấu trúc Tabs 2 bên + Thanh công cụ Navigation Toolbar trực quan. | **PASS** (Triệt tiêu cuộn trang) |

---

### 2. SỐ LIỆU ĐO ĐẠC TOÁN HỌC & ĐỒ HỌA THREE.JS

#### 2.1. Kiểm chứng triệt tiêu Double Transform (Length Ratio = 1.15, Circumference = 1.20):
Dữ liệu trích xuất trực tiếp từ Three.js `matrixWorld` thông qua runtime Playwright:
```json
{
  "upperArmGroup_scale": [1.0, 1.0, 1.0],
  "forearmGroup_scale": [1.0, 1.0, 1.0],
  "handGroup_scale": [1.0, 1.0, 1.0],
  "upperArm_worldScale": [1.200000, 1.150000, 1.200000],
  "forearm_worldScale":  [1.200000, 1.150000, 1.200000],
  "hand_worldScale":     [1.200000, 1.150000, 1.200000]
}
```
*Kết luận:* Hệ số nhân đôi sai lệch: **$1.000000$ (Sai số Double Transform: $0.000000\%$)**.

#### 2.2. Kiểm chứng tiếp xúc tâm khớp giải phẫu (Anatomical Pivot Alignment):
Tọa độ tâm khớp đo được trên thế giới Three.js (Hệ tọa độ mét):
- **Khớp ức đòn (Sternoclavicular Joint):** `[-0.010, 1.410, 0.001] m`
- **Khớp ổ chảo - cánh tay (Glenohumeral Joint):** `[-0.190, 1.395, -0.024] m`
- **Khớp khuỷu (Elbow Humeroradial/ulnar Joint):** `[-0.190, 1.122, -0.024] m`
- **Khớp cổ tay (Radiocarpal Joint):** `[-0.250, 0.894, -0.006] m`

Khi cánh tay co giãn tỷ lệ $l = 1.15$:
$$\text{Chiều dài cánh tay cơ sở} = 1.395 - 1.122 = 0.273\text{ m}$$
$$\Delta Y = -0.273 \times 1.15 = -0.31395\text{ m}$$
$$\text{Tọa độ Y khớp khuỷu thực tế} = 1.395 - 0.31395 = 1.08105\text{ m}$$
Kết quả đo thực tế từ `joints["elbow"][1]`: **$1.08105\text{ m}$**. Độ lệch: **$0.00000\text{ m}$**.

---

### 3. DANH MỤC BẰNG CHỨNG ẢNH CHỤP THỰC TẾ (SCREENSHOT TELEMETRY)

Tất cả ảnh chụp được tạo tự động bởi Playwright trong quá trình chạy test live `tests/test_v1_reality_repair_e2e.py`:

1. **repair_01_initial_layout.png:**  
   Giao diện V1.0 sau khi tái cấu trúc: Viewport Toolbar 5 nút bấm ở trên đỉnh, hệ thống 3 Tabs cột trái (Lớp Mô, Hình Thể, Công Cụ) và 3 Tabs cột phải (Động Học, Huyệt Vị, Chi Tiết), banner cảnh báo an toàn lâm sàng rõ ràng.
2. **repair_02_zero_double_transform.png:**  
   Mô hình khi điều chỉnh thanh trượt vóc dáng ($1.15\times$ độ dài cánh tay, $1.20\times$ chu vi). Xương cánh tay và cẳng tay phóng to tỷ lệ mà không bị bóp méo, khớp khuỷu nối khít hoàn hảo.
3. **repair_03_flexed_meridian_kinematics.png:**  
   Cánh tay ở tư thế nâng vai $60.0^\circ$, gập khuỷu $45.0^\circ$. Đường kinh Thủ Dương Minh Đại Trường (`LI4 -> LI11 -> LI14 -> LI15`) biến dạng và uốn lượn liên tục theo chuyển động của cánh tay và cẳng tay.
4. **repair_04_viewport_focus_arm.png:**  
   Khung nhìn camera sau khi bấm nút `🦾 Chi Trên Phải` trên Viewport Toolbar. Camera tự động di chuyển và căn giữa trọn vẹn chuỗi khớp từ đai vai tới mu bàn tay.
5. **repair_05_skin_hidden_for_kinematics.png:**  
   Khung nhìn sau khi bấm `🦴 Ẩn Da Khi Vận Động`. Vỏ da toàn thân tĩnh được ẩn hoàn toàn, lộ rõ chuyển động của các xương và cơ chi trên mà không bị hiện tượng xương đâm xuyên qua da.
6. **repair_06_final_verified_state.png:**  
   Trạng thái nghiệm thu cuối cùng của Web Atlas với độ hoàn nguyên nhân trắc học $0.000000\text{ m}$, toàn bộ các lớp mô đồng bộ.
