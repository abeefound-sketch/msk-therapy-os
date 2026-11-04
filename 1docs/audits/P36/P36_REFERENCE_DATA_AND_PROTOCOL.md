# P36: REFERENCE DATA AND PROTOCOL AUDIT REPORT
**MSK-Therapy-OS | Milestone P36: Quantitative Motion Validation**

---

## 1. GIAO THỨC ĐO ĐẠC SAI SỐ ĐỘNG HỌC (KINEMATIC VALIDATION PROTOCOL)

Hệ thống đánh giá sai số động học `MotionComparisonHarness` được thiết kế theo nguyên tắc thực nghiệm chặt chẽ:
1. **Phân biệt hai loại sai số:**
   - **Sai số tái lập phần mềm (Software Reproducibility Residual):** Sai khác giữa góc do MediaPipe xuất ra và góc đạt được trên xương Armature trong Blender (đạt sai số cực tiểu $< 0.05^\circ$, khẳng định thuật toán giải động học FK và keyframing hoạt động hoàn hảo).
   - **Sai số đo đạc trên cơ thể người thật (Biomechanical Human Measurement Error):** Độ lệch giữa góc ước tính từ video camera đơn và góc thực tế đo bằng hệ thống mocap quang học đa camera (Vicon/Qualisys) hoặc goniometer cơ sinh học.
2. **Quy tắc ranh giới thực tế (Reality-Gating):**
   - Không được phép lấy hai tệp chuyển động của hai người khác nhau (ví dụ: CMU Mocap của đối tượng khác và Pose2Sim của đối tượng khác) ghép lại làm ground truth từng frame.
   - Khi tệp video thử nghiệm (`real_human_motion_cam01.mp4`) là video ghi bằng webcam đơn, không có hệ thống điểm mốc quang học đồng bộ hoặc hiệu chuẩn đa camera $\to$ Hệ thống bắt buộc báo cáo trung thực trạng thái:  
     `ACCURACY_NOT_ESTABLISHED`.
   - Tuyệt đối cấm gán sai số $0.0^\circ$ hoặc tự phong danh hiệu độ chính xác y khoa khi chưa có paired ground truth.

---

## 2. NGUỒN DỮ LIỆU THAM CHIẾU VÀ BẢN QUYỀN (REFERENCE ASSETS)

| Nguồn Dữ Liệu | Đường Dẫn Tệp | Đối Tượng / Thử Nghiệm | Bản Quyền | Mục Đích Sử Dụng | Trạng Thái Ground Truth |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Video Pose2Sim Demo** | `research/motion_samples/real_human_motion_cam01.mp4` | Cam01 Single Monocular Webcam (100 frames) | BSD 3-Clause / CC BY | Thử nghiệm pipeline thực nghiệm | **ACCURACY_NOT_ESTABLISHED** (Thiếu mocap quang học đồng thời) |
| **CMU Graphics Lab Mocap** | `research/motion_samples/cmu_subject_02_arm.bvh` | Subject 02 Trial 01 (Vicon 12-camera, 120 Hz) | CC Attribution 3.0 | Mẫu chuyển động tham chiếu độc lập | **UNPAIRED_REFERENCE** (Khác chủ thể và góc quay với video cam01) |
| **Synthetic Paired Trajectory** | `MotionComparisonHarness.benchmark` | Quỹ đạo chuyển động hình sin có nhiễu Gaussian nhân tạo | Nội bộ kiểm thử | Kiểm định năng lực toán học của harness | **VERIFIED_GROUND_TRUTH** (MAE: 2.00°, RMSE: 2.26°) |

---

## 3. THIẾT KẾ BỘ CÔNG CỤ SO SÁNH (MOTION COMPARISON HARNESS)

- **Cân bằng thời gian & nội suy:** Resampling tuyến tính / spline về cùng lưới thời gian (60 FPS).
- **Ước lượng độ trễ pha (Lag Estimation):** Tương quan chéo (cross-correlation) trên cửa sổ $\pm 15$ frames:
  $$\tau^* = \arg\max_\tau \sum_{t} (A(t) - \bar{A}) (B(t+\tau) - \bar{B})$$
- **Xử lý mất dấu (Dropouts) và Che khuất (Occlusion):** Đánh dấu cờ `DROPPED_FRAME` khi điểm mốc có `visibility < 0.5` hoặc bị che khuất; loại khỏi mẫu số tính sai số tuyệt đối.
- **Các chỉ số thống kê chuẩn hóa:**
  - Sai số tuyệt đối trung bình (MAE)
  - Căn bậc hai sai số toàn phương trung bình (RMSE)
  - Phân vị 95 của sai số ($p95$)
  - Độ lệch hệ thống (Mean Bias)
  - Độ giật thời gian (Temporal Jitter, độ lệch chuẩn sai phân bậc nhất giữa các frame liên tiếp)

---

## 4. KẾT QUẢ QUAN SÁT TRÊN VIDEO THẬT P36

- **Số frame phân tích:** 100 frames.
- **Tỷ lệ frame hợp lệ:** 100.0%.
- **Độ giật thời gian trung bình (Temporal Jitter):** $3.359^\circ/\text{frame}$ (do dao động tự nhiên của mô hình ước tính pose đơn camera khi không áp dụng bộ lọc Kalman).
- **Sai số giải bài toán điều khiển Blender (Retargeting Residual):** $0.000^\circ$ (khớp hoàn hảo với góc yêu cầu).
- **Trạng thái độ chính xác đo đạc:** `ACCURACY_NOT_ESTABLISHED` (Lý do: Không có ground truth đa camera đồng bộ).
- **Bảng dữ liệu chi tiết từng frame:** Lưu trữ tại `1docs/audits/P36/P36_FRAME_ALIGNED_METRICS.csv`.
