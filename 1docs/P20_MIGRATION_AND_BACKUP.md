# MSK-Therapy-OS — Knowledge Vault Migration & Backup Guide
## P20: SQLite Online Backup, Atomic Recovery & Schema Versioning

**Tài liệu ID:** `MSK-P20-MBG-002`  
**Phiên bản:** `1.0.0`  
**Ngày hiệu lực:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Chính Sách Quản Lý Di Cư Lược Đồ (Schema Migration Policy)

- Mọi thay đổi cấu trúc bảng của `vault.db` phải được lập phiên bản trong bảng `schema_migrations`:
  ```sql
  CREATE TABLE IF NOT EXISTS schema_migrations (
      version INTEGER PRIMARY KEY,
      applied_at TEXT NOT NULL
  );
  ```
- Phiên bản hiện tại là `V1` (Milestone P20).
- Các script migration bắt buộc phải:
  1. Chạy trong một giao dịch đơn nhất (`BEGIN TRANSACTION ... COMMIT`).
  2. Bật cờ `PRAGMA foreign_keys = ON;` trước khi thực thi.
  3. Có khả năng idempotent (chạy lặp lại không làm lỗi hệ thống).

---

### 2. Quy Trình Sao Lưu Cơ Sở Dữ Liệu An Toàn (Online Backup Procedure)

Để tránh tình trạng khóa file (database locked) hoặc đọc phải dữ liệu bẩn (dirty reads) trong khi ứng dụng đang chạy ở chế độ WAL, Knowledge Vault sử dụng **SQLite Online Backup API** (`sqlite3.backup`):

```python
def backup_database(self, backup_path: str | Path) -> Tuple[str, str, int]:
    src = self._get_conn()
    dst = sqlite3.connect(str(backup_path))
    src.backup(dst)
    dst.close()
    src.close()
    
    # Tính mã băm SHA-256 sau khi sao lưu
    sha = hashlib.sha256(Path(backup_path).read_bytes()).hexdigest()
    return str(backup_path), sha, os.path.getsize(backup_path)
```

**Lệnh thực hiện qua CLI:**
```bash
python -m msk_therapy_os.knowledge_vault backup --out knowledge_vault/import_export/vault_backup_20261101.sqlite3
```

---

### 3. Quy Trình Khôi Phục Cơ Sở Dữ Liệu Nguyên Tử (Atomic Restoration Procedure)

Trước khi ghi đè dữ liệu vào database hoạt động, hệ thống bắt buộc kiểm tra tính toàn vẹn của tệp sao lưu:

1. Kết nối tới tệp sao lưu nguồn và thực thi:
   ```sql
   PRAGMA integrity_check;
   ```
   Nếu kết quả trả về khác `ok`, từ chối khôi phục ngay lập tức để tránh làm hỏng database.
2. Kiểm tra ràng buộc khóa ngoại:
   ```sql
   PRAGMA foreign_key_check;
   ```
3. Áp dụng sao lưu trực tiếp sang file đích qua `sqlite3.backup`.

**Lệnh thực hiện qua CLI:**
```bash
python -m msk_therapy_os.knowledge_vault restore --in knowledge_vault/import_export/vault_backup_20261101.sqlite3
```

---

### 4. Kết Xuất Toàn Bộ Dữ Liệu Sang JSON (JSON Vault Export)

Để bảo đảm khả năng di chuyển dữ liệu (data portability) và kiểm toán bên ngoài mà không cần cài đặt SQLite:
```bash
python -m msk_therapy_os.knowledge_vault export --out knowledge_vault/import_export/vault_dump.json
```
Tệp JSON chứa toàn bộ tài liệu, luận điểm, trích dẫn, quan hệ mâu thuẫn và nhật ký kiểm toán `audit_events`.
