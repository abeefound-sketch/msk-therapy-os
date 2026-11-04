# P37: MA TRẬN NGHIỆM THU BỐN CỔNG ĐỘC LẬP (G1–G4 GATE ACCEPTANCE MATRIX)
**MSK-Therapy-OS | Milestone P34–P37: Anatomy Motion Verification**

---

## 1. ĐỊNH NGHĨA QUẢN TRỊ CÁC CỔNG NGHIỆM THU (GOVERNANCE DEFINITIONS)

- **G1: Functional Verification (Nghiệm Thu Tính Năng Kỹ Thuật):**
  - Hệ thống chạy thực tế trên môi trường mục tiêu (Windows 11, Blender 3.6.5 LTS, Python 3.11, MediaPipe 1.2.0).
  - Không sử dụng dữ liệu giả lập (mock/synthetic pose) để tuyên bố tính năng thực.
  - Toàn bộ test suites (unit, integration, E2E browser) đạt 100% PASS.
  - Thẩm quyền: Coding Agent và Kỹ sư triển khai được phép xác nhận kết quả kiểm thử.

- **G2: Data Integrity & Provenance (Toàn Vẹn Dữ Liệu & Nguồn Gốc):**
  - Hợp đồng dữ liệu chuẩn, mã băm SHA-256 xác thực ở cấp độ từng tệp asset.
  - Phả hệ giấy phép (License Lineage) minh bạch (CC BY 4.0, CC BY-SA 4.0, Apache 2.0).
  - Quá trình chuyển đổi tọa độ hoàn nguyên ($< 10^{-9}\text{ m}$) và sao lưu/phục hồi bit-exact 100%.
  - Trạng thái các hệ thống được báo cáo trung thực (ví dụ: `WEB_MOTION_GEOMETRY_NOT_CONNECTED`, `ACCURACY_NOT_ESTABLISHED`).
  - Thẩm quyền: Coding Agent được phép xác nhận dựa trên bằng chứng kiểm toán mã nguồn và dữ liệu.

- **G3: Domain Validity (Tính Hợp Lệ Chuyên Môn Y Học & Giải Phẫu):**
  - Thẩm định vị trí mốc huyệt, ranh giới an toàn, nhịp vận động cơ sinh học trên cơ thể người sống / tử thi / siêu âm.
  - Thẩm quyền: **CHỈ CÓ CHUYÊN GIA ĐỦ NĂNG LỰC** (Bác sĩ Châm cứu, Giảng viên Giải phẫu học có chứng chỉ) mới có quyền thẩm định và ký duyệt.
  - **Coding Agent TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ DUYỆT.** Mọi mốc LI4/ST36/KI3 bắt buộc giữ trạng thái:  
    `EXPERT_REVIEW_PENDING`.

- **G4: Independent Engineering Acceptance (Nghiệm Thu Kỹ Thuật Độc Lập):**
  - Kiểm toán độc lập toàn bộ mã nguồn, thuật toán, công thức toán và quy trình kiểm thử bởi một kỹ sư / kiểm toán viên phần mềm bên ngoài (External Reviewer).
  - *Lưu ý hiệu chỉnh:* Không nhầm lẫn G4 với phê duyệt thiết bị y tế FDA/CE-MDR.
  - Thẩm quyền: Bên kiểm toán độc lập bên ngoài. Coding Agent chỉ chuẩn bị Reviewer Packet và bằng chứng tái lập; trạng thái giữ:  
    `INDEPENDENT_ACCEPTANCE_PENDING`.

- **Regulatory & Clinical Deployment Gate (Ngoài Phạm Vi P34–P37):**
  - Áp dụng khi hệ thống nâng phạm vi lên chẩn đoán/điều trị lâm sàng (thử nghiệm RCT, đăng ký FDA 510(k)/CE-MDR).
  - Hiện tại phạm vi bất biến của dự án là:  
    `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`; `CLINICAL_VALIDATION = NOT_ESTABLISHED`.

---

## 2. MA TRẬN ĐÁNH GIÁ CHI TIẾT TỪNG MILESTONE (P34–P37)

| Milestone | Phạm Vi Thực Thi | G1: Functional | G2: Data Integrity | G3: Domain Validity | G4: Independent Acceptance | Quyết Định Kỹ Thuật | Bằng Chứng Minh Chứng |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **P34** | Đối chiếu độc lập, giải mã mâu thuẫn Frame 050, audit giấy phép từng tệp. | **PASS** | **PASS** | **PENDING** | **PENDING** | **DONE** | `P34_00_BASELINE_AND_REPRO.md`, `P34_01_P33_CLAIM_TO_RUNTIME_MATRIX.md`, `P34_02_ASSET_AND_LICENSE_LINEAGE.csv`, `P34_03_MOTION_FRAME_TRACE.csv` |
| **P35** | Trích xuất xương BodyParts3D, bind bàn tay + cẳng tay + cánh tay, neo mốc LI4/ST36/KI3. | **PASS** | **PASS** | **PENDING** | **PENDING** | **DONE** | `p35_full_limb_binding.blend`, `p35_full_limb_evidence.json`, 3 ảnh render, `P35_ASSET_COMPOSITION_AND_ANCHORING.md`, 11/11 tests pass. |
| **P36** | Đo sai số động học `MotionComparisonHarness`, xác lập ranh giới đơn camera và ground truth. | **PASS** | **PASS** | **PENDING** | **PENDING** | **DONE** | `P36_FRAME_ALIGNED_METRICS.csv`, `P36_REFERENCE_DATA_AND_PROTOCOL.md`, `P36_UNCERTAINTY_AND_FAILURE_CASES.md`, 5/5 tests pass. |
| **P37** | Đóng gói nghiên cứu, chuẩn bị Reviewer Packet, đồng bộ Web Atlas và chạy toàn bộ hồi quy. | **PASS** | **PASS** | **PENDING** | **PENDING** | **DONE** | `P37_REVIEWER_PACKET.md`, `P37_RESEARCH_RELEASE_MANIFEST.json`, `P37_FINAL_ENGINEERING_REPORT.md`, 114/114 regression tests pass. |

---

## 3. TỔNG KẾT QUYẾT ĐỊNH GO / NO-GO

- **Quyết Định Kỹ Thuật (Engineering Research Scope):** **GO (PASS)**
  - Tất cả các rào cản kỹ thuật G1 và G2 đã được hoàn thành 100% với bằng chứng số và thực nghiệm có thể tái lập độc lập.
  - Không còn hiện tượng mâu thuẫn số liệu Frame 050; toàn bộ chuỗi chuyển động 100 frames từ video qua MediaPipe vào Blender 3.6 LTS đã đồng bộ và thông suốt.
- **Quyết Định Lâm Sàng / Triển Khai Y Tế (Clinical Scope):** **NO-GO (BLOCKED / PENDING)**
  - Hệ thống duy trì nghiêm ngặt ranh giới nghiên cứu kỹ thuật (`ENGINEERING_RESEARCH_ONLY`).
  - Toàn bộ các mốc LI4, ST36, KI3 giữ nguyên trạng thái `EXPERT_REVIEW_PENDING` chờ chuyên gia giải phẫu học và châm cứu thẩm định độc lập theo hồ sơ Reviewer Packet.
