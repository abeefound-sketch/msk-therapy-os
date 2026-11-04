# MSK-Therapy-OS — Master Architecture Status Report P21–P26
## Blender Anatomical Studio · Source-of-Truth · Constrained Motion · MediaPipe · OpenSim · Clinical Governance

**Tài liệu ID:** `MSK-P21-P26-STATUS-MASTER`  
**Ngày phát hành:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Môi trường Thực nghiệm:** Intel(R) Core(TM) i7-5600U @ 2.60GHz · Intel(R) HD Graphics 5500 · RAM 7.89 GB · Windows 11 · Blender 3.6.5 LTS · Python 3.11.9  

---

### 1. Bảng Tổng Hợp Trạng Thái và Quyết Định Từng Milestone (P21–P26)

| Milestone | Tên Hạng Mục | Kết Quả Triển Khai Thực Tế | Cổng G1–G4 | Quyết Định Điều Hành |
|---|---|---|---|---|
| **P21** | **Blender Anatomical Studio PoC** | - Add-on Blender 3.6 hoàn chỉnh tại `tools/blender_anatomy_studio/`.<br>- Nạp mesh giải phẫu thật (`shoulder_skeleton.glb`, `anatomy.glb`).<br>- Phân loại 4 lớp (Bone, Muscle, Organ, Skin), ẩn/hiện, cô lập lớp xương.<br>- Đặt 3 huyệt mốc `LI4`, `ST36`, `KI3` gắn kết bề mặt với mã băm SHA-256.<br>- Dựng tuyến kinh 3D Polyline với 4 waypoint và tính năng Undo.<br>- Dựng Armature cánh tay, IK solver và giới hạn góc quay Kapandji.<br>- Xuất trọn gói JSON schema, Markdown note và file `.blend` (2.2 MB).<br>- Tái mở và nạp lại scene sạch khớp 100% tọa độ không sai lệch.<br>- Kết xuất 2 ảnh bằng chứng thực tế PNG. | G1: **PASS**<br>G2: **PASS**<br>G3: **PENDING**<br>G4: **PENDING** | $$\mathbf{CONDITIONAL\_GO}$$ (Chuyển sang P22) |
| **P22** | **Anatomical Source-of-Truth & Lineage** | - Xây dựng hệ quy chiếu chuẩn `CANONICAL_BODYPARTS3D_FRAME` (mét, Y-up).<br>- Thiết lập ma trận chuyển đổi đồng nhất 4×4 hoàn nguyên số học ($< 10^{-12}\text{ m}$).<br>- Truy xuất phả hệ học thuật đầy đủ cho `LI4`, `ST36`, `KI3` (WHO 2008, GB/T 12346-2021, FMA:23910/24476/51111).<br>- Bộ kiểm thử fail-closed kích hoạt chính xác cho 4 kịch bản lỗi: lệch đơn vị (mm vs m), đảo dấu trục X (Right vs Left), sai lệch mã băm mesh, và tuyến kinh thiếu điểm.<br>- Tuyệt đối không dùng ngưỡng hình học $<15\text{ mm}$ để tự nhận đúng y học. | G1: **PASS**<br>G2: **PASS**<br>G3: **PENDING**<br>G4: **PENDING** | $$\mathbf{CONDITIONAL\_GO}$$ (Chuyển sang P23) |
| **P23** | **Motion Bank & Constrained Human Motion** | - Tải thành công dữ liệu quang học thực tế từ CMU Mocap database (`02.asf`, `02_01.amc` với 10,293 dòng đo lường Vicon 120 FPS).<br>- Phân tích thành công dữ liệu cơ sinh học OpenSim (`seth_shoulder_elevation.mot`).<br>- Xây dựng `JointConstraintRegistry` với dẫn chiếu Kapandji 2007 (khuỷu $0^\circ$–$145^\circ$) và Seth 2016 (vai $0^\circ$–$180^\circ$).<br>- Kiểm thử tính bất biến chiều dài xương: độ lệch tối đa $0.0000\text{ mm}$ qua 19 góc thử nghiệm.<br>- Đánh dấu rõ ràng bậc tự do sấp/ngửa cẳng tay là `UNOBSERVABLE`. | G1: **PASS**<br>G2: **PASS**<br>G3: **PENDING**<br>G4: **PENDING** | $$\mathbf{CONDITIONAL\_GO}$$ (Chuyển sang P24) |
| **P24** | **MediaPipe Pose Import & Reconstruction** | - Môi trường sidecar độc lập tại `tools/pose_sidecar/pose_estimator.py`.<br>- Ánh xạ 33 mốc MediaPipe sang các khớp giải phẫu.<br>- Thiết lập Ma trận Khả năng Quan sát (`OBSERVABILITY_MATRIX`).<br>- Kiểm thử quyết định số học: tái lập chính xác các góc $0^\circ, 45^\circ, 90^\circ$ sai số $< 0.1^\circ$.<br>- Kiểm thử trường hợp che khuất 15 frames: bác bỏ tính toán fail-closed với trạng thái `REJECTED_DUE_TO_OCCLUSION`, cấm tự sinh tư thế ảo. | G1: **PASS**<br>G2: **PASS**<br>G3: **PENDING**<br>G4: **PENDING** | $$\mathbf{CONDITIONAL\_GO}$$ (Chuyển sang P25) |
| **P25** | **Knowledge Vault Integration & Governance** | - Tái sử dụng 100% database SQLite P20 (`msk_therapy_os.sqlite3`), không tạo DB thứ hai.<br>- Module cầu nối `StudioKnowledgeBridge` tra cứu chéo mốc huyệt, khớp và chuỗi chuyển động.<br>- Xuất báo cáo Markdown tổng hợp dẫn chiếu y văn không chứa PII.<br>- Giữ nguyên các bất biến an toàn: `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`, `CLINICAL_VALIDATION = NOT_ESTABLISHED`. | G1: **PASS**<br>G2: **PASS**<br>G3: **PENDING**<br>G4: **PENDING** | $$\mathbf{CONDITIONAL\_GO}$$ (Chuyển sang P26) |
| **P26** | **Patient-Specific Research Protocol** | - Xác lập giao thức nghiên cứu nhân trắc học tỷ lệ đoạn chi (Segment Scaling Ratio).<br>- Phân tích các yếu tố gây nhiễu thực tế: trượt mô mềm (STA $10$–$30\text{ mm}$), biến thiên BMI.<br>- Thiết lập khung đánh giá độc lập (Limits of Agreement, RMSE, MAE, ICC).<br>- Ranh giới đạo đức: Cấm đưa thông tin định danh bệnh nhân thật (PII/PHI) vào dự án. | G1: **PASS**<br>G2: **PASS**<br>G3: **BLOCKED**<br>G4: **BLOCKED** | $$\mathbf{RESEARCH\_ONLY}$$<br>$$\mathbf{NO\_CLINICAL\_GO}$$ |

---

### 2. Thống Kê Ma Trận Kiểm Thử Tự Động Hóa (Automated Test Metrics)

Toàn bộ các bộ kiểm thử được thực thi và vượt qua 100%:

```powershell
pytest tests/ tools/ -v
```

1. **Bộ kiểm thử kế thừa P19–P21 (34 tests):**
   - `tests/test_p19_lineage_and_governance.py`: 8/8 PASSED
   - `tests/test_p20_knowledge_vault.py`: 11/11 PASSED
   - `tests/test_p21_atlas_poc.py`: 15/15 PASSED
2. **Bộ kiểm thử kiến trúc mới P21–P25 (33 tests):**
   - `tools/blender_anatomy_studio/tests/test_p21_blender_studio.py`: 9/9 PASSED
   - `tests/test_p22_coordinate_registry_and_lineage.py`: 9/9 PASSED
   - `tools/blender_anatomy_studio/tests/test_p23_motion_bank_and_rig.py`: 6/6 PASSED
   - `tools/pose_sidecar/test_p24_pose_sidecar.py`: 5/5 PASSED
   - `tests/test_p25_knowledge_integration.py`: 4/4 PASSED

**TỔNG CỘNG:** **67 / 67 BÀI TEST VƯỢT QUA (100% PASS RATE)** trong thời gian thực thi tích lũy dưới 30 giây.

---

### 3. Vị trí Lưu trữ Bằng chứng và Artifacts

- **Bản Demo Blender Hoàn chỉnh:**  
  [p21_studio_export.blend](file:///D:/5Projects/msk-therapy-os/1docs/audits/P21/evidence/p21_studio_export.blend) (2,202,700 bytes)
- **Hình ảnh Bằng chứng Thực tế:**  
  - [01_blender_36_anatomical_studio_poc.png](file:///D:/5Projects/msk-therapy-os/1docs/audits/P21/screenshots/01_blender_36_anatomical_studio_poc.png)
  - [02_blender_arm_rig_flexed_pose.png](file:///D:/5Projects/msk-therapy-os/1docs/audits/P21/screenshots/02_blender_arm_rig_flexed_pose.png)
- **Dữ liệu Chuyển động Thật Thượng nguồn:**  
  - `research/motion_samples/02.asf` (CMU Skeleton)
  - `research/motion_samples/02_01.amc` (CMU Motion Trial, 273 KB)
  - `msk_therapy_os/data/biomechanics/seth_shoulder_elevation.mot` (OpenSim Shoulder Trial)
- **Hợp đồng Dữ liệu Schema:**  
  `tools/blender_anatomy_studio/contracts/`
- **Tài liệu Báo cáo Kiểm toán Đầy đủ:**  
  `1docs/audits/P21/`, `1docs/audits/P22/`, `1docs/audits/P23/`, `1docs/audits/P24/`, `1docs/audits/P25/`, `1docs/audits/P26/`.
