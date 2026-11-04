# MSK-Therapy-OS — Milestone P20 Acceptance Report
## P20: Knowledge Vault Foundation Final Acceptance & Evidence Verification

**Tài liệu ID:** `MSK-P20-ACC-001`  
**Ngày nghiệm thu:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Tình trạng Starter ZIP:** `STARTER_NOT_AVAILABLE` (Đã khảo sát toàn bộ thư mục và xác nhận không có file zip starter; hệ thống được xây dựng sạch từ đặc tả chuẩn hợp đồng P20)  
**Phán quyết tổng thể P20:** **`ENGINEERING_PASS_SCOPE_LIMITED`**  

---

### 1. Bảng Nghiệm Thu Bộ Dữ Liệu Tổng Hợp Bắt Buộc (Mandatory Synthetic Dataset)

| Tiêu chuẩn bắt buộc (Master Prompt) | Thực thể dữ liệu kiểm thử thực tế | Kết quả quan sát (Observed Result) | Trạng thái kỹ thuật | Bằng chứng thực tế |
|---|---|---|:---:|---|
| **1. Tài liệu tham khảo giải phẫu có citation hợp lệ** | `knowledge_vault/notes/anatomy_c7_landmark.md` | Doc `doc_36dc05756d6b`: mốc gai C7, citation `https://doi.org/10.1002/ca.23999`, tác giả Prof. H. R. Anatomist, license CC-BY-4.0 | **PASS** | `clm_8ffce38eba5c` (Tier 2 Cohort Evidence, Status SUPPORTED) |
| **2. Tài liệu khái niệm huyệt/kinh lạc gắn đúng namespace** | `knowledge_vault/notes/traditional_gv14_dazhui.md` | Doc `doc_3f41062b2e30`: Huyệt Đại Chùy (GV14), namespace `TRADITIONAL_MERIDIAN`, tác giả Lương y Trần Văn Tuệ | **PASS** | `clm_fe97231c00c8` (Tier 4 Classical Text, Status SUPPORTED) |
| **3. Hai claims mâu thuẫn cùng tồn tại và truy xuất đầy đủ** | `contested_meridian_conduction.md` | Claim 1 (`clm_d239d9913de8` - Thuyết mạc cơ Fascia) đối lập với Claim 2 (`clm_fdc5cfed94c8` - Thuyết phản xạ thần kinh). Quan hệ `rel_59b0f59a35c5` (`CONTRADICTS`) | **PASS** | Cả hai claim đều chuyển sang `CONTESTED`, được lưu giữ song song, không bị xóa bỏ; xuất hiện trong `conflict list` |
| **4. Bản ghi nguồn thiếu tác giả/URL hiển thị UNKNOWN** | `contested_meridian_conduction.md` (không có trường author và url trong frontmatter) | Document nạp vào lưu trữ `author: "UNKNOWN"`, `source_uri: "UNKNOWN"`. Không sinh dữ liệu giả | **PASS** | `tests/test_p20_knowledge_vault.py::test_missing_metadata_defaults_to_unknown` |
| **5. Import lặp cùng tệp (idempotent) & lịch sử audit** | Nạp lặp cùng nội dung tệp tin | Băm SHA-256 trùng khớp: hệ thống tái sử dụng `doc_id` cũ, ghi nhận hành động `IMPORT_IDEMPOTENT` vào `audit_events` | **PASS** | `tests/test_p20_knowledge_vault.py::test_idempotent_import_deduplication` |
| **6. Tìm kiếm tiếng Việt có dấu & tiếng Anh** | Tìm kiếm FTS5 và LIKE fallback | Tìm kiếm tiếng Việt `"Đại Chùy"` $\rightarrow$ 2 kết quả; `"thanh nhiệt"` $\rightarrow$ 1 kết quả. Tìm kiếm tiếng Anh `"vertebra prominens"` $\rightarrow$ 2 kết quả | **PASS** | `tests/test_p20_knowledge_vault.py::test_full_text_search_vietnamese_and_english` |
| **7. Tuyệt đối không tự cấp nhãn CLINICAL APPROVED** | Thử nghiệm chèn claim với status `CLINICAL_APPROVED` | Hệ thống chặn cứng tại hàm `add_claim()`, ném ra ngoại lệ `ValueError("Unauthorized claim status...")` | **PASS** | `tests/test_p20_knowledge_vault.py::test_prohibition_of_fake_clinical_approved_status` |

---

### 2. Kiểm Tra An Toàn & Bảo Mật Dữ Liệu (Security Audit)

1. **Chống SQL Injection:** Toàn bộ truy vấn đọc/ghi đều sử dụng Parameterized Queries (`?` placeholders). Thử nghiệm chuỗi injection `'; DROP TABLE documents; --` trong `test_sql_injection_resilience` chạy an toàn tuyệt đối mà không gây tổn hại cấu trúc bảng.
2. **Chống Path Traversal:** Việc lưu trữ bản sao nguồn trong `originals/` được đặt tên theo mã băm nội dung SHA-256 (`<sha256>_<doc_id>.md`), ngăn chặn việc dùng `../` để ghi đè tệp ngoài thư mục vault.
3. **Phân lập hoàn toàn cơ sở dữ liệu:** `knowledge_vault/vault.db` nằm riêng biệt và được đưa vào `.gitignore`. Không có bất kỳ truy cập hoặc tham chiếu nào tới cơ sở dữ liệu bệnh nhân `msk_therapy_os.sqlite3`.
4. **Không chứa PHI/PII:** Toàn bộ 12 tài liệu và 13 luận điểm trong kho là y văn học thuật công khai hoặc dữ liệu tổng hợp phục vụ kiểm thử.

---

### 3. Kết Quả Kiểm Thử Tự Động (Automated Test Execution)

- **Test Suite:** `tests/test_p20_knowledge_vault.py`
- **Lệnh thực thi:** `pytest tests/test_p20_knowledge_vault.py -v`
- **Kết quả:** **11 PASSED in 1.84s** (100% PASS, 0 fail, 0 error).
- **Các ca kiểm thử bao quát:**
  - `test_import_markdown_with_frontmatter`: PASS
  - `test_missing_metadata_defaults_to_unknown`: PASS
  - `test_idempotent_import_deduplication`: PASS
  - `test_prohibition_of_fake_clinical_approved_status`: PASS
  - `test_contradictory_claims_coexistence`: PASS
  - `test_full_text_search_vietnamese_and_english`: PASS
  - `test_sql_injection_resilience`: PASS
  - `test_backup_and_restoration_round_trip`: PASS
  - `test_json_export`: PASS
  - `test_evidence_adapter_sync`: PASS (Đồng bộ 9 mục từ `1docs/EVIDENCE.md` không làm đổi mtime của file)
  - `test_cli_subcommands`: PASS (stats, search, conflict list)

---

### 4. Bảng Đánh Giá Gates G1–G4 Cho Milestone P20

| Gate | Tiêu chí | Kết quả thực tế | Phán quyết | Ghi chú |
|---|---|---|:---:|---|
| **G1 (Functional)** | Khả năng nhập, phân loại, tìm kiếm, lưu mâu thuẫn, export và backup hoạt động thật | Hoàn thành qua CLI và Python API; 11/11 tests pass; có file DB và dump JSON | **PASS** | Độc lập hoàn toàn với Atlas |
| **G2 (Data Integrity)** | Toàn vẹn dữ liệu, SHA-256 bất biến, kiểm toán audit_events đầy đủ | 26 sự kiện audit được ghi nhận; backup kiểm tra tính toàn vẹn đạt `ok` | **PASS** | Zero silent overwrite |
| **G3 (Domain Validity)** | Tính xác thực y học của các luận điểm y văn | Dữ liệu bao gồm trích dẫn giải phẫu và y văn cổ truyền | **PENDING_EXPERT_REVIEW** | Các claim giữ trạng thái `UNREVIEWED` hoặc `CONTESTED` |
| **G4 (Independent Acceptance)** | Nghiệm thu độc lập ngoài nhóm phát triển | Toàn bộ log và tệp tin sao lưu đã được lưu trữ trong `1docs/audits/P20/evidence/` | **PENDING_INDEPENDENT_ACCEPTANCE** | Sẵn sàng cho kiểm toán viên độc lập tiếp nhận |
