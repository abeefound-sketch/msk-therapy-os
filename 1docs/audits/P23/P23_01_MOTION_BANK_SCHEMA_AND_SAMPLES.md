# MSK-Therapy-OS — Milestone P23 Audit
## P23_01: Motion Bank Architecture, Parsers & Schema Compliance

**Tài liệu ID:** `MSK-P23-AUD-001`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Kiến trúc Bộ chuyển đổi Ngân hàng Chuyển động (Motion Bank Engine)

Module `tools/blender_anatomy_studio/motion_bank.py` cung cấp 2 bộ phân tích cú pháp chuẩn xác cho các định dạng chuyển động phổ biến:

```text
[OpenSim .mot File]  ───► MotionBank.parse_opensim_mot() ───┐
                                                            ├─► [MotionSequence Dict] ──► JSON Schema Validation
[CMU Mocap .amc File] ───► MotionBank.parse_cmu_amc()    ───┘
```

---

### 2. Sự Tuân thủ Hợp đồng Schema (Contract Validation)

Tất cả chuỗi chuyển động xuất ra đều được xác minh đạt chuẩn theo `contracts/motion_sequence.schema.json`:
- `schema_version`: `"1.0.0"`
- `source_type`: Phân loại rõ ràng `"OPENSIM_MOT"` hoặc `"CMU_MOCAP"`
- `fps`: Tần số khung hình đo lường thực tế (10.0 FPS cho OpenSim, 120.0 FPS cho CMU)
- `frames`: Mảng danh sách khung hình gồm thời gian `time_seconds`, góc xoay các khớp `joint_rotations`, độ tin cậy `confidence` (1.0 cho dữ liệu optical/simulated), và cờ quan sát `observable_flags`.
- `quality_metadata`: Ghi nhận `total_frames`, `dropped_frames`, danh sách các bậc tự do không quan sát được `unobservable_dofs`, và mã băm SHA-256 của tệp nguồn.

---

### 3. Đánh dấu Rõ ràng các Bậc Tự do Bất khả Khảo sát (Unobservable DOFs)

Hệ thống ghi nhận minh bạch:
- Chuyển động nâng cánh tay của OpenSim và dữ liệu mốc quang học cơ bản không ghi nhận được chuyển động xoay sấp/ngửa của cẳng tay quanh trục dọc:
  $$\text{observable\_flags}["\text{pronation\_supination}"] = \mathbf{False}$$
- Cờ `unobservable_dofs = ["right_forearm_pronation"]` được lưu trong metadata, tuyệt đối không tự bịa đặt dữ liệu chuyển động xoay cẳng tay.
