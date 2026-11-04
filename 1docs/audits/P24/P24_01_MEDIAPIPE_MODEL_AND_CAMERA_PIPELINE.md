# MSK-Therapy-OS — Milestone P24 Audit
## P24_01: MediaPipe Pose Landmarker Sidecar & Camera Pipeline Architecture

**Tài liệu ID:** `MSK-P24-AUD-001`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Kiến trúc Môi trường Tách biệt (Isolated Sidecar Architecture)

Hệ thống xử lý ước lượng tư thế từ video/camera được bố trí hoàn toàn độc lập tại `tools/pose_sidecar/`:
- **Không cài đặt thư viện vào Python nhúng của Blender 3.6.**
- **Không cài đặt thêm dependency làm xáo trộn runtime chính.**
- Giao tiếp giữa sidecar phân tích hình ảnh và Blender thông qua hợp đồng tệp tin tiêu chuẩn: `pose_observation.schema.json`.

---

### 2. Định danh Mô hình & Nguồn gốc (Model Provenance)

- **Mô hình cốt lõi:** Google MediaPipe Pose Landmarker (BlazePose Heavy model)
- **Phiên bản:** `v0.10.14`
- **Mã băm SHA-256 tham chiếu:** `9a7f34c2b8109d43e201bcf54d3910c228876fe019a89c31492ba61b490f845a`
- **Giấy phép:** Apache 2.0 (Google AI Edge)
- **Không gian tọa độ xuất xưởng:**
  * `landmarks_normalized`: Tọa độ hình chiếu $[0.0, 1.0]$ theo chiều rộng/cao ảnh $(X, Y)$ kèm độ sâu tương đối $Z$.
  * `landmarks_world_estimated`: Tọa độ không gian 3D giả lập (gốc tại tâm hông) tính bằng mét.

---

### 3. Thông số Hình học Camera Khảo sát (Camera Parameters)

- **Độ phân giải khung hình:** $1280 \times 720\text{ px}$ (Chuẩn HD 16:9).
- **Tiêu cự ước tính (Focal Length):** $f_x = f_y \approx 1050\text{ px}$.
- **Điểm chính (Principal Point):** $(c_x, c_y) = (640.0, 360.0)\text{ px}$.
- **Cảnh báo tính chính xác:** Tọa độ $Z$ chiều sâu từ camera đơn (monocular) mang độ bất định cao do thiếu thông tin lập thể đa góc nhìn (Stereo parallax).
