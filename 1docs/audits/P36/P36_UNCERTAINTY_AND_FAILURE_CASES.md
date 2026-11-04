# P36: UNCERTAINTY AND FAILURE CASES AUDIT
**MSK-Therapy-OS | Milestone P36: Quantitative Motion Validation**

---

## 1. PHÂN TÍCH BẤT ĐỊNH CỦA HỆ THỐNG CAMERA ĐƠN (MONOCULAR UNCERTAINTY)

1. **Bất định chiều sâu (Depth Ambiguity along Optical Axis):**
   - MediaPipe dự đoán tọa độ 3D landmarks từ ảnh 2D thông qua mạng nơ-ron học sâu được huấn luyện trên dữ liệu tổng hợp và bộ dữ liệu có nhãn.
   - Trục Z (chiều sâu vuông góc với mặt phẳng camera) có phương sai lớn hơn từ $3\times$ đến $5\times$ so với trục X và Y trong mặt phẳng chiếu. Khi người chuyển động quay ra ngoài mặt phẳng (out-of-plane rotation), góc nâng và góc gập có độ bất định tăng từ $\pm 3^\circ$ lên $\pm 12^\circ$.

2. **Chuyển động sấp / ngửa cẳng tay (Pronation / Supination):**
   - Giải phẫu học: Chuyển động sấp ngửa của cẳng tay là sự xoay của xương quay quanh xương trụ.
   - Thị giác máy tính camera đơn: MediaPipe chỉ xuất vị trí tâm khớp khuỷu (`RIGHT_ELBOW`) và tâm khớp cổ tay (`RIGHT_WRIST`). Hai điểm mốc này chỉ tạo thành một vector đoạn thẳng, **về mặt hình học hoàn toàn không thể xác định được góc tự quay quanh trục (torsion / roll) của cẳng tay**.
   - **Quy tắc an toàn lâm sàng:** Hệ thống đánh dấu dứt khoát chuyển động sấp/ngửa cẳng tay là:  
     `UNOBSERVABLE_FROM_SINGLE_CAMERA`  
     Cấm suy diễn hoặc tự bịa ra chuyển động sấp ngửa khi chỉ có 2 mốc khuỷu - cổ tay.

3. **Hiện tượng giật thời gian (Temporal Jitter):**
   - Đo đạc thực tế trên video `real_human_motion_cam01.mp4` ghi nhận jitter trung bình $3.359^\circ/\text{frame}$. Dao động tần số cao này do nhiễu pixel và phát hiện mốc độc lập từng frame. Khuyến nghị áp dụng bộ lọc One Euro Filter hoặc Unscented Kalman Filter khi chuyển sang ứng dụng lâm sàng thực tế.

---

## 2. CÁC TÌNH HUỐNG THẤT BẠI VÀ CƠ CHẾ FAIL-CLOSED (FAILURE MODES)

| Tình Huống Lỗi | Biểu Hiện Kỹ Thuật | Hành Vi Hệ Thống (Fail-Closed) | Ghi Chú & Bằng Chứng |
| :--- | :--- | :--- | :--- |
| **Che khuất chi (Occlusion)** | Cổ tay hoặc khuỷu tay bị thân mình che mất, `visibility < 0.5`. | Gắn cờ `is_occluded = True`, chuyển trạng thái thành `DROPPED_FRAME`. Không nội suy bừa bãi. | `motion_comparison_harness.py#L90-L105` |
| **Góc vượt giới hạn sinh lý** | Nhiễu phát hiện góc nâng $> 180^\circ$ hoặc gập khuỷu $< 0^\circ$. | Bộ kẹp giải phẫu (Anatomical Constraint Solver) kẹp chặt về ngưỡng ROM sinh lý Kapandji. | `tools/generate_p34_motion_trace.py#L48-L52` |
| **Lệch hệ tọa độ / Đơn vị** | Tọa độ điểm mốc tính bằng milimét ($> 5.0\text{ m}$) nạp vào hệ quy chiếu mét. | Ném ngoại lệ `UnitScaleDivergenceError`, từ chối nạp mesh/anchor. | `test_p35_negative_unit_scale_divergence` (PASS) |
| **Sai lệch phả hệ xương** | Cố tình neo mốc LI4 vào xương cánh tay hoặc xương đai vai. | Ném ngoại lệ `ValueError: ANATOMICAL BINDING VIOLATION`, cấm hoàn toàn. | `test_p35_negative_prohibited_surface_cross_binding` (PASS) |
| **Sửa đổi tệp mesh nguồn** | Tệp nhị phân mesh bị thay đổi bit (SHA-256 không khớp). | Ném ngoại lệ `AssetIntegrityError: STALE MESH HASH`. | `test_p35_negative_stale_mesh_hash` (PASS) |

---

## 3. RANH GIỚI VÀ TÌNH TRẠNG CỦA CÁC ENGINE BÊN NGOÀI (OPENSIM / POSE2SIM)

- **Nguyên tắc tích hợp:** Không cố ép cài đặt OpenSim (C++ / Python 3.8/3.9 wrapper) vào môi trường Python 3.6 LTS của Blender để tránh phá vỡ runtime.
- **Ranh giới:** OpenSim và Pose2Sim là các công cụ nghiên cứu phối hợp độc lập qua trung gian tệp chuyển tiếp (TRC / MOT / C3D).
- **Trạng thái thực tế:** Chưa tích hợp trực tiếp OpenSim API vào quy trình tự động do thiếu môi trường Conda OpenSim trên máy trạm Windows này. Ghi nhận trung thực:  
  `OPENSIM_ADAPTER_STATUS: RESEARCH_STUB_ONLY`.
  Tuyệt đối không tạo file log OpenSim giả mạo.
