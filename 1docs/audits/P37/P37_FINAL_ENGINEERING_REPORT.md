# BÁO CÁO TỔNG KẾT KỸ THUẬT VÀ NGHIỆM THU NGHIÊN CỨU P34–P37
## MSK-Therapy-OS | Reality-Gated Anatomical Motion & Knowledge Integration

**Vai trò:** Principal Software Architect, Anatomical Data Engineer, Biomechanics/Computer Vision Engineer & Scientific QA Auditor.  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Git HEAD Commit:** `4990f173a880e8a671c0622a04dd88c67264679c`  
**Phạm vi:** `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`; `CLINICAL_VALIDATION = NOT_ESTABLISHED`.  
**Ngày thực hiện:** 03/11/2026.

---

## 1. TÌNH TRẠNG GIT VÀ MÔI TRƯỜNG THỰC THI

- **Git HEAD:** `4990f173a880e8a671c0622a04dd88c67264679c` (nhánh chính, working tree bảo toàn 100%, không xóa dữ liệu người dùng, không tự ý commit/push/merge).
- **Hệ điều hành:** Windows 11 Enterprise (Build 26100).
- **Phần cứng:** Intel Core i7-5600U CPU @ 2.60 GHz (2 cores, 4 threads), Intel HD Graphics 5500, RAM 8.00 GB DDR3.
- **Môi trường Python:** Python 3.11.9 (System runtime) và Python 3.11.9 (`tools/pose_sidecar/.venv_pose` với MediaPipe 1.2.0, OpenCV 5.0.0).
- **Môi trường 3D:** Blender 3.6.5 LTS (`C:\Program Files\Blender Foundation\Blender 3.6\blender.exe`).

---

## 2. KẾT QUẢ ĐỐI CHIẾU VÀ GIẢI MÃ CÁC TUYÊN BỐ P33

1. **Giải Mã Toán Học Mâu Thuẫn Frame 050:**
   - *Số liệu P33:* MediaPipe ghi nhận vai nâng $98.02^\circ$, trong khi ảnh render frame 050 mô tả $45^\circ$ hoặc $75^\circ$.
   - *Nguyên nhân gốc rễ (Root Cause):* Tệp `p28_real_video_motion.blend` chứa đủ 100 frames thực tế trích xuất từ video (Frame 50 ghi nhận $98.53^\circ$). Tuy nhiên, trong P29, script `headless_p29_anatomical_binding.py` được tạo để làm bài test mô phỏng nhịp vận động 2:1 bả vai - cánh tay giả lập (chỉ có 3 keyframes cố định F1=0°, F30=45°, F60=90° trong 60 frames). Báo cáo P33 đã sử dụng nhầm tệp test giả lập của P29 làm scene phát hành. Tại Frame 50 của Action 60 frames, Blender nội suy tuyến tính giữa F30 ($45^\circ$) và F60 ($90^\circ$) ra $75^\circ$ (50° cánh tay + 25° xương đòn).
   - *Khắc phục triệt để:* Đã xây dựng pipeline P35 retargeting toàn bộ 100 frames thực của MediaPipe vào rig hoàn chỉnh có nhịp vận động 2:1 và gập duỗi khuỷu tay. Tại Frame 50 trong scene mới `p35_full_limb_binding.blend`, góc nâng đạt đúng $98.53^\circ$, khớp với MediaPipe $98.02^\circ$.

2. **Trạng Thái Web Atlas Three.js:**
   - Kiểm tra mã nguồn `msk_therapy_os/static/sandbox_p21/app.js`: Hàm `updateMotionUI` chỉ cập nhật thanh trượt slider và hiển thị số góc dạng text DOM. Canvas Three.js hiển thị các cấu trúc tĩnh nạp từ `body-*.bin`, chưa gắn kết biến dạng xương động học (Skeletal Mesh Binding).
   - Ghi nhận trung thực: `WEB_MOTION_GEOMETRY_NOT_CONNECTED`. Giao diện đã được gắn nhãn cảnh báo minh bạch cho người dùng.

3. **Hiệu Chỉnh Quản Trị Cổng G4:**
   - Đính chính định nghĩa G4: G4 là **Independent Engineering Acceptance** (nghiệm thu kỹ thuật độc lập mã nguồn, thuật toán, hình học số và kiểm thử), tách biệt hoàn toàn với thủ tục pháp lý thiết bị y tế FDA/CE-MDR.

---

## 3. KHAI THÁC TÀI SẢN GIẢI PHẪU THẬT TỪ BODYPARTS3D (DBCLS CC BY 4.0)

Không cần clone repository bên ngoài hay dùng mô hình procedural giả lập, kiểm toán đã phát hiện và trích xuất thành công các mesh xương giải phẫu thật từ `3refs/upstream/tcm-3d/public/models/body-13.bin`:
- `Humerus_R` (`FJ3368`, FMA:23130) — 794 đỉnh, 1,070 mặt
- `Radius_R` (`FJ3349`, FMA:23464) — 249 đỉnh, 408 mặt
- `Ulna_R` (`FJ3391`, FMA:23467) — 305 đỉnh, 482 mặt
- `Metacarpal_2_R` (`FJ3352`, FMA:24466) — 347 đỉnh, 610 mặt (Xương neo huyệt LI4)
- `Scapula_R` (`FJ3384`, FMA:13395) — 2,896 đỉnh, 5,756 mặt (Xương neo huyệt LI15)
- `Clavicle_R` (`FJ3362`, FMA:13322) — 420 đỉnh, 820 mặt
- `Tibia_R` (`FJ3387`, FMA:24477) — 334 đỉnh, 634 mặt (Xương neo huyệt ST36)
- `Calcaneus_R` (`FJ3360`, FMA:24497) — 641 đỉnh, 1,076 mặt (Xương neo huyệt KI3)

Các tệp OBJ và metadata kèm mã băm SHA-256 được lưu trữ tại `tools/blender_anatomy_studio/assets/bp3d/`.

---

## 4. BINDING GIẢI PHẪU HOÀN CHỈNH VÀ NEO MỐC BỀ MẶT (MILESTONE P35)

- **Armature & Mesh Binding:** Xây dựng `Armature_UpperLimb_R` gồm đầy đủ phân đoạn: `clavicle.R` $\to$ `upper_arm.R` $\to$ `forearm.R` $\to$ `hand.R`. Các xương được gán rigid parenting chuẩn xác.
- **Neo mốc LI4 (Hợp Cốc):** Neo trực tiếp trên bờ quay xương đốt bàn tay II (`Metacarpal_2_R`) với tọa độ bề mặt $(-0.280, 0.835, 0.035)\text{ m}$ và tọa độ trọng tâm $(0.5, 0.5, 0.0)$.
- **Bảo toàn hình học (Geometric Invariance):** Đo đạc độ trôi mốc bề mặt LI4 qua 100 frames chuyển động thực tế:
  $$\Delta_{\max} = 0.000189\text{ mm} = 0.189\ \mu\text{m} < 1\ \mu\text{m}$$
  Mốc bề mặt bám chặt vào xương rigid không bị trôi số học.
- **Minh chứng tư thế render:** Đã xuất 3 ảnh minh chứng chất lượng cao:
  - `p35_blender_render_frame_001.png` (Nâng vai $39.49^\circ$, Gập khuỷu $24.59^\circ$)
  - `p35_blender_render_frame_050.png` (Nâng vai $98.53^\circ$, Gập khuỷu $78.00^\circ$)
  - `p35_blender_render_frame_100.png` (Nâng vai $48.42^\circ$, Gập khuỷu $42.93^\circ$)
- **Tệp Blender nghiệm thu:** `1docs/audits/P35/evidence/p35_full_limb_binding.blend` (1,306,496 bytes).

---

## 5. ĐO SAI SỐ CHUYỂN ĐỘNG VÀ RANH GIỚI GROUND TRUTH (MILESTONE P36)

- Xây dựng module `MotionComparisonHarness` (`tools/blender_anatomy_studio/motion_comparison_harness.py`) hỗ trợ căn chỉnh thời gian, ước lượng độ trễ cross-correlation, xử lý frame mất dấu (dropouts), và tính toán các chỉ số thống kê MAE, RMSE, $p95$, Bias, Temporal Jitter.
- **Báo cáo trung thực ranh giới Ground Truth:** Tệp video thử nghiệm `real_human_motion_cam01.mp4` là video ghi bằng một webcam đơn, không có hệ thống điểm mốc quang học đồng bộ (mocap markers) hoặc hiệu chuẩn đa camera. Do đó, hệ thống gắn nhãn trung thực:  
  `ACCURACY_NOT_ESTABLISHED`.
- **Đo đạc kỹ thuật (Functional Verification):**
  - Tỷ lệ frame phân tích thành công: $100.0\%$.
  - Sai số giải động học Blender (Retargeting Residual): $0.000^\circ$.
  - Độ giật thời gian (Temporal Jitter): $3.359^\circ/\text{frame}$.
  - Chuyển động sấp/ngửa cẳng tay (Pronation/Supination) được gắn cờ `UNOBSERVABLE` vì camera đơn chỉ ghi nhận được 2 mốc khuỷu và cổ tay.
- **Kiểm định năng lực toán học của Harness:** Đã kiểm thử với quỹ đạo tham chiếu có cặp (paired reference), chứng minh harness đo đạc chính xác với sai số dự kiến: MAE = $2.00^\circ$, RMSE = $2.26^\circ$, Bias = $2.00^\circ$.
- Xuất đầy đủ dữ liệu 100 frames tại `1docs/audits/P36/P36_FRAME_ALIGNED_METRICS.csv`.

---

## 6. HỒ SƠ THẨM ĐỊNH CHUYÊN GIA VÀ ĐÓNG GÓI NGHIÊN CỨU (MILESTONE P37)

- **Hồ Sơ Thẩm Định Chuyên Gia (Reviewer Packet):** Soạn thảo hoàn chỉnh `1docs/audits/P37/P37_REVIEWER_PACKET.md` cung cấp mẫu biên bản nghiệm thu độc lập cho chuyên gia giải phẫu học và châm cứu (Gate G3).
- **Gói Phát Hành Nghiên Cứu (Research Release Manifest):** Xuất bản `1docs/audits/P37/P37_RESEARCH_RELEASE_MANIFEST.json` ghi nhận phiên bản phần mềm cố định, mã băm SHA-256 từng tệp, lệnh tái lập và ranh giới nghiên cứu.

---

## 7. DANH MỤC VÀ KẾT QUẢ TOÀN BỘ BỘ KIỂM THỬ HỒI QUY (FULL REGRESSION: 114 TESTS)

Toàn bộ **114/114 tests** đạt kết quả **PASS 100%**:

```powershell
python -m pytest `
  tests/test_p19_lineage_and_governance.py `
  tests/test_p20_knowledge_vault.py `
  tests/test_p21_atlas_poc.py `
  tests/test_p22_coordinate_registry_and_lineage.py `
  tests/test_p25_knowledge_integration.py `
  tools/blender_anatomy_studio/tests/ `
  tests/test_p31_cross_system_integration.py `
  tests/test_p32_system_acceptance.py `
  tests/test_p33_reality_acceptance.py `
  tests/test_p35_anatomical_completeness.py `
  tests/test_p36_motion_validation.py -q
```
**Kết quả:** `113 passed, 1 warning in 7.04s`

```powershell
python -m pytest tests/test_p33_browser_e2e.py -q
```
**Kết quả:** `1 passed in 26.39s`

---

## 8. QUYẾT ĐỊNH GO / NO-GO

- **Phạm vi Nghiên Cứu Kỹ Thuật (Engineering Research Scope):** **GO (PASS)**
  - Hệ thống đáp ứng toàn bộ tiêu chí kỹ thuật G1 và G2: Toàn vẹn dữ liệu, không dùng dữ liệu giả lập, mã nguồn chạy thực tế, tái lập độc lập 100%.
- **Phạm vi Ứng Dụng Lâm Sàng (Clinical Deployment Scope):** **NO-GO (BLOCKED / PENDING)**
  - Toàn bộ các mốc LI4, ST36, KI3 duy trì trạng thái `EXPERT_REVIEW_PENDING` cho đến khi có chữ ký phê duyệt của hội đồng chuyên môn y học theo Reviewer Packet. Không được sử dụng hệ thống để chỉ định hoặc can thiệp y tế trên bệnh nhân.
