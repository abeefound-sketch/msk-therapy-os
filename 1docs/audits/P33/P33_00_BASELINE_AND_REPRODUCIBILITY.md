# HỒ SƠ KIỂM TOÁN BASELINE VÀ TÍNH KHẢ LẬP (REPRODUCIBILITY AUDIT)
## Milestone P33: Independent Full-Stack Reality Acceptance & Research Release Hardening

> **TÀI LIỆU ID:** `MSK-P33-00-BASELINE-AND-REPRODUCIBILITY`  
> **PHIÊN BẢN HỆ THỐNG:** `1.0.0-research.p33`  
> **NGÀY THỰC HIỆN:** 2026-11-03  
> **AUDITOR ĐỘC LẬP / LEAD ARCHITECT:** Antigravity Autonomous Engineering & Systems Audit Agent  
> **PHẠM VI:** `ENGINEERING_RESEARCH_ONLY`  
> **KIỂM ĐỊNH LÂM SÀNG:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **GIT HEAD:** `4990f173a880e8a671c0622a04dd88c67264679c`  

---

## 1. MỤC TIÊU VÀ NGUYÊN TẮC KIỂM TOÁN P33

Milestone P33 được kích hoạt nhằm thực hiện một đợt **kiểm toán độc lập toàn diện (Independent Full-Stack Reality Check)** trên toàn bộ hệ thống MSK-Therapy-OS sau các giai đoạn P27–P32:
1. **Kiểm tra tính có thật của chuỗi dữ liệu (Reality Pipeline Audit):**
   - Video thật $\to$ Suy luận MediaPipe thời gian thực $\to$ Chuyển đổi góc khớp $\to$ Ràng buộc cơ sinh học $\to$ Armature $\to$ Mesh giải phẫu $\to$ Mốc huyệt bám động học.
   - Tuyệt đối không dùng lại kết quả landmarks đã lưu từ trước để giả lập việc suy luận mới.
2. **Hiệu chỉnh các tuyên bố hiệu năng (Benchmark Corrections):**
   - Tách bạch dứt khoát giữa **tốc độ tính toán thuật toán trong bộ nhớ (Headless Computational Throughput)** và **tốc độ dựng hình hiển thị tương tác (Interactive Viewport FPS)**.
   - Đo đạc chính xác thời gian khởi động lạnh (Cold Startup Time) của Blender thay vì chỉ đo thời gian đọc file nhị phân trong tiến trình đang mở.
   - Đo đạc chính xác mức RAM đỉnh thực tế (Peak Working Set RAM) của tiến trình bằng API hệ điều hành.
3. **Kiểm toán giao diện người dùng thực tế và luồng tri thức (Real UI & Knowledge Workflow):**
   - Kiểm tra giao diện Web Atlas và các API kết nối Knowledge Vault qua kiểm thử trình duyệt thực tế (E2E / DOM / State consistency).
4. **Kiểm toán quản trị dữ liệu và bản quyền nguồn (Data Governance & License Audit):**
   - Kiểm tra tính toàn vẹn của `knowledge_vault/vault.db` và `msk_therapy_os.sqlite3`.
   - Thử nghiệm sao lưu và phục hồi độc lập trong thư mục cách ly.
   - Thẩm tra bản quyền và giấy phép của từng tài sản thượng nguồn (BodyParts3D, Z-Anatomy, CMU Mocap, Pose2Sim, MediaPipe Task Model).

---

## 2. PHÂN TÍCH ĐỐI CHIẾU: TUYÊN BỐ P32 VS. THỰC TẾ KỸ THUẬT

| Hạng Mục | Tuyên Bố Tại P32 | Bản Chất Kỹ Thuật Thực Tế | Đánh Giá & Hướng Hiệu Chỉnh P33 |
| :--- | :--- | :--- | :--- |
| **Tốc độ khung hình Blender** | `11,562 FPS` | Vòng lặp `scene.frame_set(f)` trong Blender nền (`blender -b`) chỉ đánh giá đồ thị phụ thuộc (Dependency Graph) trong CPU RAM mà không hề gọi hàm swap buffer của OpenGL/Vulkan tới GPU màn hình. | **SỬA LẠI ĐÚNG ĐỊNH NGHĨA:** Ghi nhận là `Headless Depsgraph Evaluation Rate: ~11,000 frames/s`. Viewport FPS thực tế cần đo qua tiến trình hiển thị có GPU context hoặc ghi nhận `NOT_APPLICABLE_IN_HEADLESS`. |
| **Thời gian nạp scene Blender** | `9.3 ms` (0.0093 s) | Thời gian này chỉ là hàm `wm.open_mainfile()` nạp khối dữ liệu khi tiến trình Blender đã nằm sẵn trong bộ nhớ. Thời gian khởi động nguội từ dòng lệnh mất khoảng $1.5$–$2.5\text{ s}$. | **SỬA LẠI ĐÚNG ĐỊNH NGHĨA:** Ghi nhận cả hai chỉ số: `Cold Startup Time: ~1.8 s` và `In-Memory Scene Reopen Time: ~10 ms`. |
| **Mức chiếm dụng RAM** | `< 120 MB RAM` | Ước lượng trên một tiến trình đơn lẻ, chưa tính mức tiêu thụ đồng thời của Python Sidecar khi tải mô hình mạng nơ-ron MediaPipe Task (~300 MB) và dữ liệu video. | **SỬA LẠI ĐÚNG ĐỊNH NGHĨA:** Đo đỉnh RAM bằng `psutil` (Process Working Set) cho cả Blender và Python Sidecar. |
| **Khớp mốc huyệt (LI4)** | Gắn LI4 vào Humerus (ở P28) | Đã sửa ở P29 bằng cách cấm cross-binding và đánh dấu `ASSET_NOT_AVAILABLE` cho LI4/ST36/KI3, đồng thời dùng LI14 và LI15. | **XÁC NHẬN:** P29-P32 đã sửa đúng. P33 sẽ kiểm tra lại toàn bộ hierarchy và tính bất biến tọa độ. |
| **Độ chính xác lâm sàng** | Đã ghi nhận `ACCURACY_NOT_ESTABLISHED` | Camera đơn không có ground truth đo lường 3D đồng bộ. | **XÁC NHẬN:** Giữ vững nguyên tắc trung thực khoa học, không tự phong G3 hoặc G4. |

---

## 3. THIẾT LẬP MÔI TRƯỜNG THỰC THI CHO P33

- **Thư mục làm việc:** `D:\5Projects\msk-therapy-os`
- **Thư mục lưu trữ bằng chứng P33:** `1docs/audits/P33/evidence/`
- **Thư mục lưu trữ ảnh chụp bằng chứng:** `1docs/audits/P33/screenshots/`
- **Môi trường Python chính:** `Python 3.11.9` (`C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe`)
- **Môi trường Python Sidecar độc lập:** `D:\5Projects\msk-therapy-os\tools\pose_sidecar\.venv_pose\Scripts\python.exe`
- **Blender LTS:** `C:\Program Files\Blender Foundation\Blender 3.6\blender.exe`
