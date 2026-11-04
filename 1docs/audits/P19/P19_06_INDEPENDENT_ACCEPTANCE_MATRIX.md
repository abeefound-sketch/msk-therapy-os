# MSK-Therapy-OS — Milestone P19 Independent Acceptance Matrix
## P19_06: Multi-Gate Verification Ledger (Gates G1–G4)

**Tài liệu ID:** `MSK-P19-IAM-006`  
**Ngày đánh giá:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Phán quyết tổng thể P19:** **`ENGINEERING_PASS_SCOPE_LIMITED`**  
*(Lý do: Đạt 100% G1 Kỹ thuật và G2 Dữ liệu toàn vẹn; G3 Kiểm định Y học và G4 Nghiệm thu độc lập bảo lưu trạng thái `PENDING` theo đúng quy tắc danh dự kỹ thuật, không tự cấp quyền)*

---

### Bảng Nghiệm Thu Đa Tầng (Gates G1–G4 Matrix)

| Milestone | Gate | Yêu cầu kiểm soát | Phương pháp kiểm chứng | Đường dẫn bằng chứng thực tế | Kết quả quan sát được | Người chịu trách nhiệm / Người duyệt | Phán quyết (Verdict) | Hành động tiếp theo |
|---|---|---|---|---|---|---|:---:|---|
| **P19** | **G1 (Functional)** | Bản đồ module, runtime entrypoints, các tuyến xử lý tọa độ hoạt động đầy đủ, không gãy đổ | Chạy toàn bộ 829 unit/integration tests + Playwright E2E browser thực tế | `1docs/audits/P19/P19_00_BASELINE_AND_EVIDENCE.md`, `1docs/audits/P19/evidence/` | 829/829 non-playwright tests PASS (0 fail); Playwright E2E test PASS (83.92s) | Lead Test Engineer | **PASS** | Tiếp tục duy trì regression gate cho P20 |
| **P19** | **G1 (Functional)** | Khả năng truy vết tọa độ 5 điểm mẫu LI4, ST36, KI3, GV14, GB21 | Chạy script đo đạc pháp y `scratch/trace_points_audit.py` trên authentic mesh | `scratch/trace_points_audit.py`, `1docs/audits/P19/P19_03_COORDINATE_LINEAGE.md` | Đo đạc chính xác sai lệch: LI4 (90.01mm, bay ngoài BBox), ST36 (53.28mm), KI3 (175.45mm, ngược trục X) | 3D Geometry Specialist | **PASS** | Bàn giao thông số cho kế hoạch P22 |
| **P19** | **G2 (Data Integrity)** | Tính toàn vẹn mã băm (SHA-256) của Mesh và Static Dataset; sao lưu an toàn SQLite | Tính toán mã băm SHA-256 bằng Python; tạo backup qua `sqlite3.backup` API | `1docs/audits/P19/evidence/msk_therapy_os_baseline_backup.sqlite3` | `fj2810_softened.bin`: `05b49233...`; `acupuncture_3d.json`: `47df1332...`; Backup DB: 54 tables, `0c05bb2a...` | Data Provenance Engineer | **PASS** | Bảo quản bản sao lưu trong thư mục evidence |
| **P19** | **G2 (Data Integrity)** | Loại bỏ toàn bộ dữ liệu giả lập, hằng số dịch chuyển ngầm $dx, dy, dz$ trong `upstream_raw` | Kiểm tra mã nguồn `spatial_resolver.py` và chạy negative test | `tests/test_p18_reproducible_failures.py::test_reproduce_upstream_raw_synthetic_offset_defect` | Phản hồi fail-closed chuẩn `UPSTREAM_TRANSFORM_UNAVAILABLE`, zero hằng số giả | Forensic Code Auditor | **PASS** | Duy trì cơ chế fail-closed |
| **P19** | **G2 (Data Integrity)** | Khắc phục triệt để lỗi lưu cache đường kinh lạc khi tọa độ huyệt bị thay đổi | Kiểm tra hàm băm `point_digest` trong cache key `MeridianSurfacePathEngine` | `tests/test_p18_geometry_remediation.py::test_meridian_engine_cache_invalidates_on_point_mutation` | Thay đổi tọa độ làm thay đổi digest $\rightarrow$ hủy cache cũ và tính lại ngay lập tức | Senior Software Architect | **PASS** | Đóng hoàn toàn lỗ hổng stale cache |
| **P19** | **G3 (Domain Validity)** | Tính chuẩn xác giải phẫu của 362 huyệt theo tiêu chuẩn WHO và vị trí trên cơ thể người thật | Đối chiếu y văn giải phẫu, tài liệu chuẩn WHO 2008 Western Pacific | `1docs/audits/P18/P18_ACUPOINT_RECONCILIATION.csv` | Phát hiện 130 điểm lệch $\ge 50$mm, 28 điểm lệch $\ge 100$mm giữa 2 nguồn nội bộ | Hội đồng Chuyên gia Y học Cổ truyền & Giải phẫu học | **PENDING_EXPERT_REVIEW** | Chưa được phép tuyên bố ANATOMICAL VERIFIED; chỉ lưu hành nghiên cứu |
| **P19** | **G3 (Domain Validity)** | Ranh giới an toàn lâm sàng: cấm châm cứu xâm lấn, cấm DDS, cấm chẩn đoán tự động | Rà soát hằng số an toàn `safety.py`, `biomechanics_adapter.py`, `server.py` | `tests/test_safety.py`, `tests/test_p18_geometry_remediation.py::test_clinical_safety_boundaries_preserved` | `clinical_depth_guidance_allowed = False`; `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY` khóa cứng | Clinical Safety Board | **PASS (Ranh giới bảo vệ)** | Giữ vững hàng rào an toàn |
| **P19** | **G4 (Independent Acceptance)**| Bằng chứng được nghiệm thu bởi kiểm toán viên / chuyên gia độc lập bên ngoài | Chuyển giao toàn bộ hồ sơ bằng chứng, lệnh tái lập, checksums và báo cáo pháp y | `1docs/audits/P19/P19_00` đến `P19_06` | Toàn bộ lệnh tái lập và bằng chứng đã sẵn sàng trong thư mục evidence | Độc lập bên ngoài (Independent Third Party) | **PENDING_INDEPENDENT_ACCEPTANCE** | Chờ kiểm định độc lập tiếp nhận |

---

### Phán Quyết Kết Luận

- Hệ thống MSK-Therapy-OS tại cột mốc P19 đã hoàn thành xuất sắc các yêu cầu kỹ thuật và tính toàn vẹn dữ liệu.
- Phân định rõ ràng: **Không có sự đánh lận giữa "test kỹ thuật chạy pass" với "vị trí giải phẫu đã được y học phê duyệt"**.
- Trạng thái phát hành nội bộ: **`ENGINEERING_PASS_SCOPE_LIMITED`**. Đủ điều kiện chuyển tiếp sang **P20 Knowledge Vault Foundation**.
