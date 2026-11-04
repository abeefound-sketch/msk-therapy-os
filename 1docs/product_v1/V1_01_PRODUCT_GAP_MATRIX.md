# V1_01: PRODUCT GAP MATRIX (PACKAGES A–E)
**MSK-Therapy-OS V1.0 | Product Completion Roadmap**

---

## 1. BẢNG PHÂN TÍCH KHOẢNG TRỐNG SẢN PHẨM (PRODUCT GAP MATRIX)

| Gói Công Việc | Hiện Trạng Baseline P34–P37 | Khoảng Trống Kỹ Thuật & Trải Nghiệm (Gaps) | Giải Pháp Triển Khai V1.0 (Implementation) | Tiêu Chí Nghiệm Thu (Acceptance Criteria) |
| :--- | :--- | :--- | :--- | :--- |
| **Gói A: Atlas Foundation** | Web Atlas nạp 17 cấu trúc đại diện BodyParts3D, nhưng danh mục mặc định chỉ nạp đai vai trái, thiếu toàn bộ chi trên phải (`Humerus_R`, `Radius_R`, `Ulna_R`, `Metacarpal_2_R`). | Thiếu các xương cánh tay phải làm nền cho vertical slice; inspector mesh chưa thể hiện đầy đủ FMA concept và metadata bản quyền. | Nạp toàn bộ xương chi trên phải từ Chunk 13 (`body-13.bin`); nâng cấp inspector hiển thị real-time ID, Name, FMA, System, Chunk, License; toggle thật lớp BONE/MUSCLE/SKIN/ORGAN. | Browser Chromium mở 3D scene có đầy đủ xương chi trên phải thật; toggle thay đổi trực quan visibility của mesh; click mesh chọn đúng metadata. |
| **Gói B: Parametric Body & Registration** | Chưa có giao diện thanh trượt tham số hóa trong Web Atlas; chỉ có cấu trúc hình học cố định của BodyParts3D. | Người dùng không thể tùy biến chiều cao, chiều dài chi, vóc dáng; thiếu kiểm soát biến dạng và bảo toàn mốc bám. | Xây `ParametricBodyEngine` với 3 sliders: `height_scale`, `right_arm_length_ratio`, `right_arm_circumference_visual` và 4 presets (`baseline`, `slender`, `broader`, `longer_arm`). Cập nhật vị trí khớp thật trong Three.js. | Kéo slider thay đổi kích thước và vị trí đỉnh thật trên WebGL canvas; quay về baseline đạt sai số $< 10^{-6}\text{ m}$; không gãy mesh, không biến dạng cao su. |
| **Gói C: Dynamic Acupoints & Meridians** | Các điểm mốc hiển thị dạng hình cầu tĩnh; mốc LI4 trong Web Atlas cũ bị báo `ASSET_NOT_AVAILABLE` và chưa bám động khi xương quay. | Thiếu cơ chế cập nhật tọa độ world của huyệt khi morph/pose; thiếu đường kinh 3D động; thiếu tính năng chỉnh sửa thủ công và undo/redo. | Neo LI4 vào `Metacarpal_2_R` và LI14/LI15 vào `Humerus_R`/`Scapula_R`; điểm bám di chuyển cùng phân đoạn; bổ sung đường kinh Thủ Dương Minh Đại Trường động; thêm giao diện chỉnh sửa thủ công có lịch sử undo/redo. | Mốc LI4 và đường kinh di chuyển chính xác theo xương khi pose/morph; chỉnh sửa thủ công lưu lại phiên bản; trạng thái lâm sàng duy trì `EXPERT_REVIEW_PENDING`. |
| **Gói D: Real Motion & Mouse Pose** | **BLOCKER CHÍNH:** Timeline slider chỉ thay đổi số góc trên text DOM (`WEB_MOTION_GEOMETRY_NOT_CONNECTED`). 3D Mesh đứng yên. | Xương trong Three.js chưa được liên kết theo cấp bậc động học (Hierarchical Skeletal Scene Graph); chưa có điều khiển tư thế bằng chuột (Mouse Posing). | Thiết lập `ArmatureController` trong Three.js với các nhóm khớp `scapulaGroup` $\to$ `upperArmGroup` $\to$ `forearmGroup` $\to$ `handGroup`. Kết nối 100 frames MediaPipe với nhịp 2:1; thêm Mouse Posing handles. | Khi Play/kéo slider timeline, **các mesh xương và da trên Three.js Canvas thật sự xoay và dịch chuyển**; gỡ bỏ cảnh báo, chuyển sang `WEB_MOTION_GEOMETRY_CONNECTED`. |
| **Gói E: Unified Product & Persistence** | Giao diện còn phân mảnh giữa sandbox demo, thiếu lưu/mở dự án hoàn chỉnh, thiếu script chạy 1-click cho người dùng không biết kỹ thuật. | Người dùng phải gõ lệnh CLI; chưa lưu được dự án gồm cả morph, pose, mốc sửa và ghi chú; chưa đóng gói nghiệm thu. | Tích hợp giao diện sản phẩm thống nhất tại `/sandbox/p21/` (và `/atlas/`); xây `ProjectManager` lưu/mở tệp `.mskproj` JSON; tạo script `run_msk_therapy_os.bat` chạy 1-click cho Windows. | Thao tác 9 bước người dùng hoàn chỉnh không cần code; lưu dự án và mở lại khôi phục bit-exact morph, pose và mốc; Playwright E2E pass 100%. |

---

## 2. KẾ HOẠCH TRIỂN KHAI THEO THỨ TỰ PHỤ THUỘC

1. **Bước 1 (Giải quyết Blocker D & A):** Nạp xương chi trên phải vào Web Atlas Three.js, thiết lập cấu trúc xương phân cấp (Hierarchical Rigging), nối chuỗi 100 frames MediaPipe vào góc quay thực tế của Three.js Canvas $\to$ **Chuyển trạng thái sang `WEB_MOTION_GEOMETRY_CONNECTED`**.
2. **Bước 2 (Gói B):** Xây dựng bộ điều khiển tham số hình thể `ParametricBodyEngine` và 3 thanh trượt UI, cập nhật tỷ lệ chi và vị trí tâm khớp thời gian thực.
3. **Bước 3 (Gói C):** Gắn kết mốc LI4/LI14/LI15 và đường kinh 3D động bám theo xương chuyển động và hình thể mới; hỗ trợ chỉnh sửa thủ công và undo/redo.
4. **Bước 4 (Gói E):** Tích hợp quản lý dự án `.mskproj` (Save/Open), tra cứu Knowledge Vault, xuất báo cáo Markdown và script khởi động `run_msk_therapy_os.bat`.
5. **Bước 5 (Kiểm thử & Nghiệm thu):** Viết bộ kiểm thử E2E Playwright và Unit tests cho V1.0, đo hiệu năng FPS WebGL trên Intel HD 5500, chụp ảnh minh chứng và hoàn thiện tài liệu bàn giao.
