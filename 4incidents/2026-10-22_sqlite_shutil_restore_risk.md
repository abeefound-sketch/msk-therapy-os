# Postmortem: SQLite Corruption Risk from shutil.copy2 on Live Databases

**Ngày phát hiện:** 22/10/2026  
**Mức độ nghiêm trọng:** P0 (Database Integrity / Reliability)  
**Tập tin liên quan:** `msk_therapy_os/points.py`, `msk_therapy_os/server.py`  
**Trạng thái:** RESOLVED  

---

## 1. Triệu chứng
Khi thực hiện khôi phục (restore) cơ sở dữ liệu từ bản sao lưu qua API `/api/governance/restore`, mã nguồn sử dụng hàm sao chép file `shutil.copy2(backup_path, live_db_path)`. Trên hệ điều hành Windows khi server đang mở kết nối hoặc trong chế độ ghi nhật ký Write-Ahead Logging (WAL), thao tác này dẫn tới lỗi hệ thống `WinError 32: The process cannot access the file because it is being used by another process`, hoặc làm rách trang đĩa (torn pages), gây hỏng cấu trúc B-tree của SQLite.

## 2. Nguyên nhân gốc rễ (Root Cause)
1. Thao tác sao chép file ở tầng hệ điều hành (`shutil.copy2`) hoàn toàn mù tịt về trạng thái nội bộ của engine cơ sở dữ liệu SQLite (các trang trong cache bộ nhớ, các lock đang giữ, các giao dịch đang dang dở).
2. Khi đè một file database khác lên file đang mở, SQLite không được thông báo để flush cache hay giải phóng con trỏ file, dẫn đến xung đột khóa trên Windows và nguy cơ hỏng dữ liệu không thể phục hồi.

## 3. Giải pháp khắc phục
1. **Loại bỏ hoàn toàn `shutil.copy2`:** Thay thế bằng API sao lưu trực tuyến nguyên bản của SQLite:
   ```python
   with sqlite3.connect(backup_path) as bkp_conn:
       with sqlite3.connect(live_db_path) as live_conn:
           bkp_conn.backup(live_conn)
   ```
2. **Khóa bảo trì toàn server (Maintenance Lock):** Khi restore, thiết lập cờ `IS_MAINTENANCE_ACTIVE = True`. Mọi yêu cầu HTTP đến trong lúc này nhận về phản hồi `HTTP 503 Service Unavailable` và header `Retry-After: 5`.
3. **Quy trình thẩm định đa tầng trước khi restore:** Kiểm tra đường dẫn an toàn, xác thực mã băm SHA-256, chạy `PRAGMA integrity_check` và `PRAGMA foreign_key_check` trên file backup trước khi đồng bộ.
4. **Snapshot hoàn tác nguyên tử (Atomic Rollback):** Tự động tạo bản chụp an toàn của database sống trước khi chép; nếu có bất kỳ lỗi nào xảy ra trong quá trình restore, snapshot sẽ được hoàn tác ngay lập tức.
