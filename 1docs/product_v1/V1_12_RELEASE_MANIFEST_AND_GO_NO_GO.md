# BẢN GIAO NHẬN PHÁT HÀNH (RELEASE MANIFEST) & QUYẾT ĐỊNH GO/NO-GO
## MSK-Therapy-OS · Product V1.0 Release Candidate

**Ngày phê duyệt kỹ thuật:** 03/11/2026  
**Git HEAD:** `4990f173a880e8a671c0622a04dd88c67264679c` (với các bổ sung mã nguồn V1.0)  
**Phạm vi phát hành (Release Scope):** `ENGINEERING_RESEARCH_ONLY`  
**Độ xác thực lâm sàng (Clinical Validation):** `NOT_ESTABLISHED`

---

### 1. Danh Mục Thành Phần Bàn Giao (Release Artifacts)

#### A. Mã Nguồn Cốt Lõi (Core Source Code)
- `msk_therapy_os/asset_catalog.py`: Quản lý danh mục mô hình giải phẫu BodyParts3D, mã FMA và bản quyền.
- `msk_therapy_os/body_parametric/parametric_engine.py`: Động cơ hình thể tham số (3 sliders, 4 presets, joint registration, zero drift).
- `msk_therapy_os/dynamic_anchors/dynamic_anchor_manager.py`: Quản lý mốc huyệt bám động (LI4, LI14, LI15), đường kinh 3D, ngăn xếp Undo/Redo.
- `msk_therapy_os/motion_bridge/web_motion_controller.py`: Ánh xạ động học 100 frames MediaPipe theo nhịp 2:1 và điều khiển Mouse Pose.
- `msk_therapy_os/project_io/project_manager.py`: Lưu/mở tệp manifest `.mskproj` nguyên tử và xuất báo cáo Markdown.
- `msk_therapy_os/server.py`: Máy chủ HTTP tích hợp đầy đủ API endpoints GET/POST V1.0.
- `msk_therapy_os/static/sandbox_p21/`: Giao diện WebGL hoàn thiện (`index.html`, `app.js`, `style.css`).

#### B. Kịch Bản Khởi Động 1-Click (Desktop Launchers)
- `run_msk_therapy_os.bat`: Khởi động desktop 1-click cho người dùng Windows.
- `run_v1_product.ps1`: Tự động hóa PowerShell mở trình duyệt cục bộ.

#### C. Bộ Kiểm Thử Tự Động (Test Automation Suite)
- `tests/test_v1_parametric_body.py`: 6 tests đơn vị hình thể tham số $\to$ `PASS`.
- `tests/test_v1_dynamic_anchors.py`: 3 tests đơn vị mốc huyệt bám động $\to$ `PASS`.
- `tests/test_v1_project_io.py`: 4 tests đơn vị lưu trữ manifest $\to$ `PASS`.
- `tests/test_v1_product_browser_e2e.py`: Kiểm thử trình duyệt Playwright E2E toàn bộ 6 bước $\to$ `PASS`.
- Toàn bộ 92 unit tests hồi quy P19–P36 $\to$ `PASS 100%`.
- Kiểm thử trình duyệt hồi quy `test_p33_browser_e2e.py` $\to$ `PASS 100%`.

#### D. Bằng Chứng Thực Thi Thực Tế (Execution Evidence)
Lưu tại thư mục `1docs/product_v1/evidence/`:
1. `01_v1_atlas_baseline.png`: Giao diện Atlas 3D WebGL mặc định với các lớp giải phẫu.
2. `02_v1_parametric_morph_slender.png`: Khung nhìn sau khi áp dụng Preset Slender (cao $1.05\times$, tay $1.03\times$).
3. `03_v1_web_motion_frame50_connected.png`: Chuyển động 3D khung hình 50 (vai nâng $98^\circ$, khuỷu gập $80^\circ$, mesh và mốc LI4/LI14/LI15 xoay đồng bộ).
4. `04_v1_mouse_pose_interactive.png`: Điều khiển tạo dáng trực tiếp bằng chuột (vai $45^\circ$, khuỷu $60^\circ$).
5. `05_v1_knowledge_query_li4.png`: Tra cứu tri thức y văn huyệt Hợp Cốc (LI4) từ Knowledge Vault.
6. `06_v1_project_export_markdown.png`: Modal xem trước và xuất báo cáo Markdown đầy đủ provenance.

#### E. Hồ Sơ Tài Liệu Nghiệm Thu (Audit Documentation)
1. `1docs/product_v1/V1_00_BASELINE.md`: Báo cáo hiện trạng hệ thống và tiền kiểm tra.
2. `1docs/product_v1/V1_01_PRODUCT_GAP_MATRIX.md`: Ma trận khoảng trống 5 gói A–E.
3. `1docs/product_v1/V1_02_OPEN_SOURCE_LICENSE_COMPATIBILITY.csv`: Kiểm toán bản quyền mở (BodyParts3D CC BY 4.0, MakeHuman CC0).
4. `1docs/product_v1/V1_03_ARCHITECTURE_AND_DATA_CONTRACTS.md`: Kiến trúc 5 giai đoạn biến đổi và data contracts.
5. `1docs/product_v1/V1_04_A_ATLAS_ACCEPTANCE.md`: Nghiệm thu Gói A.
6. `1docs/product_v1/V1_05_B_MORPH_ACCEPTANCE.md`: Nghiệm thu Gói B.
7. `1docs/product_v1/V1_06_C_DYNAMIC_ANCHORS_ACCEPTANCE.md`: Nghiệm thu Gói C.
8. `1docs/product_v1/V1_07_D_MOTION_WEBGL_ACCEPTANCE.md`: Nghiệm thu Gói D (Giải quyết dứt điểm WEB_MOTION_GEOMETRY_NOT_CONNECTED).
9. `1docs/product_v1/V1_08_E_PRODUCT_E2E_ACCEPTANCE.md`: Nghiệm thu Gói E.
10. `1docs/product_v1/V1_09_PERFORMANCE_AND_LIMITATIONS.md`: Báo cáo đo đạc hiệu năng FPS, RAM và giới hạn.
11. `1docs/product_v1/V1_10_G1_G4_MATRIX.md`: Ma trận đối soát 4 cổng G1–G4.
12. `1docs/product_v1/V1_11_USER_GUIDE_NON_DEVELOPER.md`: Sổ tay hướng dẫn cho người dùng không kỹ thuật.
13. `1docs/product_v1/V1_12_RELEASE_MANIFEST_AND_GO_NO_GO.md`: Bản giao nhận phát hành này.

---

### 2. Quyết Định Phát Hành (GO / NO-GO DECISION)

Dựa trên kết quả thực thi độc lập và toàn diện trên mã nguồn, dữ liệu thực tế và môi trường runtime:

- **G1 Functional Acceptance:** `GO (PASS)` — Tất cả các tính năng của năm gói A, B, C, D, E hoạt động đúng như đặc tả.
- **G2 Data Integrity & Provenance:** `GO (PASS)` — Toàn vẹn mã băm, không trôi dạt số học khi hoàn nguyên, dẫn chiếu nguồn WHO và FMA minh bạch.
- **G3 Domain Validity:** `CONDITIONAL HOLD (PENDING)` — Duy trì trung thực trạng thái chờ thẩm định chuyên khoa y tế độc lập. Không tự phê duyệt khống.
- **G4 Independent Engineering Acceptance:** `GO (PASS)` — Vượt qua 100% các bài kiểm thử hồi quy kỹ thuật và trình duyệt E2E, ranh giới an toàn được khóa chặt ở mức `ENGINEERING_RESEARCH_ONLY`.

### QUYẾT ĐỊNH CHÍNH THỨC:
$$\mathbf{GO}\text{ for Research Release (ENGINEERING\_RESEARCH\_ONLY)}$$

Hệ thống **MSK-Therapy-OS Product V1.0** chính thức đạt điều kiện đóng gói và bàn giao kỹ thuật phục vụ mục đích nghiên cứu tính toán giải phẫu và giảng dạy khoa học.
