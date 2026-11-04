# MSK-Therapy-OS — Upstream Feasibility Register
## P21: Open-Source Upstream Modules Evaluation & Feasibility Register

**Tài liệu ID:** `MSK-P21-UFR-001`  
**Ngày lập:** 2026-11-01  
**Phân loại:** `PLANNING_AND_FEASIBILITY_ONLY` (Chưa triển khai tại P19/P20)  
**Mục tiêu:** Thẩm định tính khả thi, giấy phép bản quyền, tính tương thích phần cứng và độ tin cậy hình học của các dự án nguồn mở tiềm năng trước khi cân nhắc tích hợp vào Milestone P21.  

---

### 1. Bảng Khảo Sát Tính Khả Thi Của Các Nguồn Thượng Nguồn (Upstream Register)

| Tên Dự Án / Repository | Mục đích xem xét | License Mã Nguồn | License Dữ Liệu / 3D Asset | Commit / Tag / Release | Khả năng chạy Offline Zero-CDN | Tương thích Windows Intel HD 5500 | Độ tin cậy hình học (Geometry Provenance) | Khuyến nghị thẩm định (P21 Gate) | Điểm chặn chính (Blockers) |
|---|---|---|---|---|:---:|:---:|---|:---:|---|
| **`JICio/tcm-3d`** | Nguồn gốc dữ liệu BodyParts3D FJ2810 surface projection hiện tại | MIT | CC-BY-4.0 (BodyParts3D DBCLS) | Commit `3d12c9b...` (tại `3refs/upstream/tcm-3d`) | **CÓ** (Local binary buffer) | **TỐT** (Vertex buffer tĩnh $\sim 25$k đỉnh, 60 FPS) | **RẤT CAO** đối với mặt da tĩnh; nhưng là mô hình nam giới Nhật Bản 172cm cố định | **ACCEPT_WITH_ISOLATION** (Dùng làm baseline đối chiếu) | Cần chứng minh tính tương thích tư thế (pose articulation) |
| **`Human Atlas (Open Anatomy / DBCLS)`** | Bộ dữ liệu giải phẫu phân đoạn 1,288 cấu trúc | CC-BY-4.0 | CC-BY-4.0 (FMA Ontology mapped) | Release 4.0 | **CÓ** (Từng chunk `body-*.bin`) | **TRUNG BÌNH** (Tổng dung lượng >50MB; cần tải từng chunk động) | **CAO** (Chuẩn phân loại FMA quốc tế) | **CONDITIONAL_EVALUATION** | Cần cơ chế nén hoặc LoD để không làm sập RAM 8GB / GPU tích hợp |
| **`TARA (Traditional Acupuncture Research Atlas)`** | Bản đồ số hóa các huyệt và đường kinh từ y văn | AGPL-3.0 hoặc GPL-3.0 (Cần xác thực) | NC (Non-Commercial) / Chưa rõ | Chưa được pin SHA | **CHƯA RÕ** | **CHƯA RÕ** | Đa số là tọa độ 2D sơ đồ hóa hoặc 3D gắn trên mesh riêng | **DEFER / QUARANTINE** | Rủi ro lây nhiễm giấy phép AGPL và hạn chế phi thương mại (NC) |
| **`WaterCMY/anatomy-3d`** | Dự án tham chiếu cấu trúc cơ quan nội tạng 3D | MIT | Không rõ bản quyền mô hình gốc | Snapshot P17 | **CÓ** | **TỐT** | Thiếu tài liệu nguồn gốc vector pháp tuyến | **REJECT_FOR_ACUPOINTS** (Chỉ giữ tham khảo hình họa) | Tọa độ không khớp hệ quy chiếu BodyParts3D |
| **`Three-Mesh-BVH`** | Thư viện gia tốc truy vấn va chạm và chiếu tia trên mặt tam giác Three.js | MIT | Không có asset đi kèm | v0.7.x | **CÓ** (Có thể vendor thành 1 file JS) | **XUẤT SẮC** ($< 2$ ms cho raycasting 50k tam giác trên CPU/GPU) | Thuần túy toán học hình học tính toán | **RECOMMEND_ADOPTION_P21** | Cần test bundle offline không phụ thuộc npm build toolchain |

---

### 2. Tiêu Chí Bắt Buộc Để Được Phê Duyệt Tích Hợp (P21 Gate Criteria)

Một dự án thượng nguồn CHỈ ĐƯỢC PHÉP tích hợp vào MSK-Therapy-OS tại Milestone P21 khi thỏa mãn toàn bộ 6 điều kiện tiên quyết sau:

1. **Minh bạch bản quyền (License Cleanliness):** Phải tương thích với giấy phép của MSK-Therapy-OS (ưu tiên MIT/Apache-2.0 cho code; CC-BY-4.0 cho dữ liệu). Tuyệt đối không chấp nhận các asset không rõ nguồn gốc hoặc có điều khoản cấm phân phối thương mại (NC) ngầm định.
2. **Khả năng hoạt động Offline 100%:** Toàn bộ thư viện, textures, binary mesh phải được lưu trữ nội bộ (vendored/local), không gọi bất kỳ external CDN, Google Fonts, hay telemetry server nào.
3. **Phù hợp ngân sách phần cứng mục tiêu:** Hoạt động ổn định trên cấu hình Intel Core i7-5600U, RAM 8GB, GPU Intel HD Graphics 5500; duy trì render $\ge 30$ FPS, mức chiếm dụng bộ nhớ RAM $< 300$ MB.
4. **Nguồn gốc hình học được xác minh (Cryptographic Provenance):** Mọi file 3D nhị phân phải có SHA-256 cố định, hệ quy chiếu tọa độ rõ ràng (Origin datum, Unit meters/mm, Handedness, Axes mapping).
5. **Cách ly trong Sandbox Dev:** Quá trình đánh giá phải diễn ra trong branch/worktree cô lập, không đưa thẳng vào production bundle.
6. **Không tự động chuyển thành khuyến cáo điều trị:** Các mô hình giải phẫu bổ sung chỉ đóng vai trò nghiên cứu hình thái, không được dùng để suy diễn độ sâu châm kim hoặc thao tác nắn chỉnh cột sống.
