# MSK-THERAPY-OS V1.1 — MEDIAPIPE MOTION RETARGETING
## Báo cáo Chuyển tiếp Động học MediaPipe sang Nhân vật 3D (100 Frames)

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Bộ điều hợp:** `msk_therapy_os/character_motion_retarget.py`

---

### 1. QUY TRÌNH CHUYỂN TIẾP ĐỘNG HỌC (KINEMATIC RETARGETING PIPELINE)

Chuỗi 100 frames thực tế trích xuất từ video chuyển động thực nghiệm (`real_human_motion_cam01.mp4`) được chuyển tiếp sang hệ xương MakeHuman 53 bones:

$$\mathbf{Landmarks\ (33\ MP\ Points)} \longrightarrow \mathbf{Joint\ Angles\ (\text{deg})} \longrightarrow \mathbf{Scapulohumeral\ Rhythm\ (2:1)} \longrightarrow \mathbf{Bones\ (Euler\ XYZ)} \longrightarrow \mathbf{SkinnedMesh}$$

- **Ranh giới quan sát (Observability Boundary):**
  - **Observable DOF:** Góc gập khuỷu (`right_elbow_flexion_deg`) và góc nâng vai (`right_shoulder_elevation_deg`) được đo trực tiếp từ mặt phẳng chuyển động phía trước camera.
  - **Non-observable DOF:** Góc sấp/ngửa cẳng tay (`forearm_pronation`) từ camera đơn diện mạo (2D monocular) không thể xác định chính xác mà không có cảm biến độ sâu; hệ thống đánh dấu cờ `forearm_pronation_observable: False` và không tự suy đoán.

---

### 2. KẾT QUẢ ĐO ĐẠC TRÊN CHUỖI 100 FRAMES THỰC TẾ

| Chỉ số Động học | Giá trị Đo đạc | Ghi chú Khoa học |
| :--- | :--- | :--- |
| **Tổng số khung hình** | 100 frames ($0.00\text{ s} \to 1.65\text{ s}$) | Tần số lấy mẫu $60\text{ FPS}$ |
| **Độ tin cậy trung bình (Mean Confidence)** | **$99.82\%$** | Không có khung hình nào bị drop landmarks |
| **Biên độ gập khuỷu (Elbow Flexion Range)** | $24.59^\circ \longrightarrow 80.44^\circ$ | Nằm trong ngưỡng sinh lý an toàn $[0^\circ, 145^\circ]$ |
| **Biên độ nâng vai (Shoulder Elevation Range)** | $39.49^\circ \longrightarrow 98.02^\circ$ | Áp dụng nhịp xương bả vai - cánh tay 2:1 |
| **Phân bổ nhịp Scapulohumeral tại $98.02^\circ$** | Cánh tay (`upperarm_r`): $75.35^\circ$ <br> Xương đòn (`clavicle_r`): $22.67^\circ$ | Tỷ lệ $2:1$ sau $30^\circ$ khởi đầu |
| **Sai số Retargeting Residual** | **$< 1.8^\circ$** | Khớp sinh lý mượt mà, không giật khung hình |

---

### 3. KHẢ NĂNG KẾT HỢP VỚI HÌNH THỂ THAM SỐ (PARAMETRIC MORPHING)

Chuyển động MediaPipe được tính toán dưới dạng ma trận góc xoay (Local Rotation Matrices), do đó hoàn toàn độc lập với chiều dài đoạn chi. Khi người dùng thay đổi chiều cao, độ rộng vai hay chiều dài tay thông qua Morph Targets, chuỗi cử động 100 khung hình vẫn thực thi chính xác trên vóc dáng mới mà không bị biến dạng khớp hay đứt gãy da.
