# MSK-Therapy-OS — Knowledge Vault Contract Specification
## P20: Canonical Data Contracts & Operational Governance

**Tài liệu ID:** `MSK-P20-KVC-001`  
**Phiên bản:** `1.0.0`  
**Ngày hiệu lực:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Phạm Vi & Mục Đích

Tài liệu này xác lập hợp đồng dữ liệu chuẩn mực cho khối Knowledge Vault (P20). Knowledge Vault là hệ thống quản trị tri thức y khoa offline, hoạt động hoàn toàn độc lập với Anatomical Atlas 3D và cơ sở dữ liệu bệnh nhân lâm sàng, chịu trách nhiệm lưu trữ các nguồn văn bản, luận điểm khoa học, trích dẫn và các nhận định y học đối lập.

---

### 2. Định Nghĩa Thực Thể & Thuộc Tính Bắt Buộc

#### 2.1 Thực thể Tài Liệu (`documents`)
- `doc_id` (TEXT PRIMARY KEY): Định danh duy nhất toàn cục, tiền tố `doc_` kèm 12 ký tự hex ngẫu nhiên.
- `sha256_hash` (TEXT NOT NULL UNIQUE): Mã băm SHA-256 của nội dung tệp thô, phục vụ phát hiện trùng lặp bất biến (idempotent deduplication).
- `title` (TEXT NOT NULL): Tiêu đề tài liệu chuẩn hóa NFC.
- `author` (TEXT NOT NULL DEFAULT 'UNKNOWN'): Tên tác giả hoặc cơ quan phát hành. Nếu nguồn thiếu, bắt buộc ghi `UNKNOWN`, tuyệt đối không suy diễn.
- `publication_date` (TEXT NOT NULL DEFAULT 'UNKNOWN'): Năm hoặc ngày phát hành dạng ISO-8601 hoặc năm (YYYY).
- `document_type` (TEXT NOT NULL): Định dạng tài liệu (`MARKDOWN`, `PDF_METADATA`, `CLINICAL_NOTE`, `CLASSICAL_TEXT`).
- `namespace` (TEXT NOT NULL): Phân vùng dữ liệu (`ANATOMY_EVIDENCE`, `TRADITIONAL_MERIDIAN`, `DIEN_CHAN_REFLEX`, `BIOMECHANICS`, `CLINICAL_PROTOCOL`, `RESEARCH_NOTE`, `HISTORICAL_TEXT`).
- `language` (TEXT NOT NULL DEFAULT 'vi'): Mã ngôn ngữ theo ISO 639-1 (`vi`, `en`, `zh`).
- `source_uri` (TEXT NOT NULL DEFAULT 'UNKNOWN'): Đường dẫn URL hoặc mã DOI gốc.
- `original_path` (TEXT NOT NULL): Vị trí lưu trữ bản sao nguồn bất biến trong `originals/`.
- `license` (TEXT NOT NULL DEFAULT 'UNKNOWN'): Giấy phép sử dụng tài sản (`CC-BY-4.0`, `MIT`, `PUBLIC_DOMAIN`, `EDUCATIONAL_FAIR_USE`, `UNKNOWN`).
- `imported_at` (TEXT NOT NULL): Thời điểm nạp vào kho (ISO-8601 UTC).
- `raw_content` (TEXT NOT NULL): Toàn bộ nội dung văn bản thô chuẩn hóa Unicode NFC.
- `review_status` (TEXT NOT NULL DEFAULT 'UNREVIEWED'): Trạng thái kiểm duyệt (`UNREVIEWED`, `REVIEWED`, `RETRACTED`).

#### 2.2 Thực thể Luận Điểm (`claims`)
- `claim_id` (TEXT PRIMARY KEY): Tiền tố `clm_` kèm 12 ký tự hex.
- `doc_id` (TEXT NOT NULL FK): Khóa ngoại tham chiếu đến `documents(doc_id)`.
- `source_quote` (TEXT NOT NULL): Đoạn trích dẫn nguyên văn từ tài liệu nguồn.
- `claim_text` (TEXT NOT NULL): Luận điểm khoa học nguyên tử (Atomic Statement).
- `claim_type` (TEXT NOT NULL): Phân loại (`ANATOMICAL_LOCATION`, `MERIDIAN_PATHWAY`, `REFLEX_INDICATION`, `CONTRAINDICATION`, `BIOMECHANICAL_MECHANISM`, `HISTORICAL_ORIGIN`).
- `assertion_type` (TEXT NOT NULL): Bản chất luận điểm (`ASSERTION` - tuyên bố nguyên văn; `INFERENCE` - suy luận diễn dịch).
- `status` (TEXT NOT NULL DEFAULT 'UNREVIEWED'): Trạng thái thẩm định (`UNREVIEWED`, `SUPPORTED`, `CONTESTED`, `REJECTED`, `RETRACTED`).
  - *Lưu ý:* CẤM sử dụng trạng thái `CLINICAL_APPROVED` hoặc `ANATOMICAL_VERIFIED` tại tầng này.
- `evidence_tier` (TEXT NOT NULL): Bậc chứng cứ y học độc lập (`TIER_1_RCT`, `TIER_2_COHORT`, `TIER_3_CASE_REPORT`, `TIER_4_CLASSICAL_TEXT`, `TIER_5_EXPERT_OPINION`, `TIER_UNGRADED`).
- `created_by` (TEXT NOT NULL): Danh tính người tạo hoặc tiến trình nạp dữ liệu.
- `created_at` (TEXT NOT NULL): Thời gian tạo (ISO-8601 UTC).
- `uncertainty_notes` (TEXT): Ghi chú về biên độ sai số hoặc mức độ không chắc chắn.

#### 2.3 Thực thể Quan Hệ Đối Lập (`claim_relations`)
- `relation_id` (TEXT PRIMARY KEY): Tiền tố `rel_` kèm 12 ký tự hex.
- `source_claim_id` (TEXT NOT NULL FK): Luận điểm 1.
- `target_claim_id` (TEXT NOT NULL FK): Luận điểm 2.
- `relationship_type` (TEXT NOT NULL): Loại quan hệ (`CONTRADICTS`, `CORROBORATES`, `SPECIALIZES`, `SUPERSEDES`).
- `notes` (TEXT): Giải trình nguyên nhân mâu thuẫn hoặc bối cảnh áp dụng khác biệt.
- **Ràng buộc bảo tồn:** Khi quan hệ `CONTRADICTS` được thiết lập, cả hai luận điểm đều được chuyển sang trạng thái `CONTESTED` và lưu trữ song song. Cấm tự động xóa một bên.

#### 2.4 Bảng Ghi Kiểm Toán Bất Biến (`audit_events`)
- Cấu trúc append-only ghi lại toàn bộ sự kiện: `event_id`, `entity_type`, `entity_id`, `action`, `actor`, `before_state`, `after_state`, `rationale`, `timestamp`.
- Không có thao tác `DELETE` hay `UPDATE` nào trên bảng này.

---

### 3. Quy Tắc Tìm Kiếm Toàn Văn (Full-Text Search Specification)

1. Sử dụng module SQLite FTS5 với tokenizer `unicode61` (hỗ trợ dấu tiếng Việt đầy đủ).
2. Chuẩn hóa chuỗi tìm kiếm về dạng NFC (`unicodedata.normalize('NFC', query)`) trước khi truy vấn.
3. Cung cấp cơ chế tự động chuyển đổi sang truy vấn SQL `LIKE` khi FTS5 gặp lỗi cú pháp hoặc chạy trên môi trường SQLite rút gọn không tích hợp FTS5.
