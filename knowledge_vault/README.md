# MSK-Therapy-OS — Knowledge Vault (Milestone P20)

Knowledge Vault là kho lưu trữ tri thức, y văn, bằng chứng và các luận điểm y học mâu thuẫn hoạt động hoàn toàn **offline**, độc lập với 3D Atlas và cơ sở dữ liệu bệnh nhân lâm sàng.

---

### 1. Cấu Trúc Thư Mục

```text
knowledge_vault/
├── README.md               # Tài liệu hướng dẫn sử dụng và vận hành
├── originals/              # Bản sao nguồn bất biến (lưu theo hash; TUYỆT ĐỐI KHÔNG CHỨA PHI)
├── notes/                  # Ghi chú tổng hợp dạng Markdown
├── schemas/                # Hợp đồng lược đồ cơ sở dữ liệu (vault_schema_v1.sql)
├── import_export/          # Bản sao lưu SQLite và các file kết xuất JSON
├── vault.db                # SQLite database cục bộ (được gitignore)
└── .gitignore              # Loại trừ vault.db và các file shm/wal
```

---

### 2. Nguyên Tắc Cốt Lõi (Non-Negotiable Principles)

1. **Bảo mật & Quyền riêng tư:** Tuyệt đối không lưu dữ liệu bệnh nhân thật (PHI/PII). Toàn bộ nội dung là y văn khoa học, mốc giải phẫu và luận điểm y học truyền thống.
2. **Lưu giữ quan điểm mâu thuẫn (Contradictory Viewpoints):** Khi hai tài liệu có kết luận đối lập (ví dụ vị trí huyệt hoặc cơ chế tác động), hệ thống **LƯU GIỮ CẢ HAI** dưới dạng quan hệ `CONTRADICTS`. Tuyệt đối không tự ý xóa bỏ hoặc hợp nhất âm thầm một góc nhìn.
3. **Trung thực về nguồn gốc:** Mọi metadata thiếu (tác giả, ngày công bố, URL) được ghi rõ là `UNKNOWN`, không suy diễn tự động.
4. **Không tự phong chuẩn lâm sàng:** Các luận điểm mang trạng thái `UNREVIEWED`, `SUPPORTED`, hoặc `CONTESTED`. Cấm tự cấp nhãn `CLINICAL_APPROVED`.

---

### 3. Hướng Dẫn Sử Dụng Bằng Dòng Lệnh (CLI Reference)

Mọi thao tác có thể thực hiện thông qua module Python:

```bash
# 1. Nhập một tài liệu Markdown
python -m msk_therapy_os.knowledge_vault import path/to/document.md --namespace ANATOMY_EVIDENCE --author "Tên Tác Giả"

# 2. Tìm kiếm toàn văn (hỗ trợ tiếng Việt có dấu và tiếng Anh)
python -m msk_therapy_os.knowledge_vault search "thần kinh giữa"
python -m msk_therapy_os.knowledge_vault search "carpal tunnel" --namespace BIOMECHANICS

# 3. Thêm một luận điểm (Claim) gắn với tài liệu
python -m msk_therapy_os.knowledge_vault claim add --doc doc_12345 --text "Huyệt Đại Chùy nằm ở chỗ lõm dưới gai đốt sống cổ C7" --quote "In the depression inferior to the spinous process of C7"

# 4. Ghi nhận quan hệ mâu thuẫn giữa hai luận điểm
python -m msk_therapy_os.knowledge_vault conflict add --claim1 clm_001 --claim2 clm_002 --notes "Khác biệt giữa mốc giải phẫu Tây y và thốn B-cun truyền thống"

# 5. Liệt kê các quan hệ mâu thuẫn
python -m msk_therapy_os.knowledge_vault conflict list

# 6. Sao lưu cơ sở dữ liệu an toàn (Online Backup)
python -m msk_therapy_os.knowledge_vault backup --out knowledge_vault/import_export/vault_backup.sqlite3

# 7. Khôi phục cơ sở dữ liệu
python -m msk_therapy_os.knowledge_vault restore --in knowledge_vault/import_export/vault_backup.sqlite3

# 8. Xem thống kê kho tri thức
python -m msk_therapy_os.knowledge_vault stats
```
