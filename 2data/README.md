# 2data — Project Data Workspace

Thư mục lưu trữ dữ liệu thực tế của dự án MSK-Therapy-OS theo quy chuẩn `PROJECT_STRUCTURE_CANON.md`.

## Cấu trúc thư mục

- `demo.sqlite3`: Cơ sở dữ liệu SQLite cục bộ chứa đầy đủ dữ liệu mẫu đã seed (bệnh án, ROM, SOAP notes, danh mục huyệt đạo chuẩn và tài khoản người dùng/chuyên gia thẩm định).
- `backups/`: Thư mục lưu trữ các bản sao lưu SQLite an toàn được tạo bởi Native Backup API (`backup_conn.backup(target_conn)`), kèm theo file checksum SHA-256 đối chứng (`*.sha256`).
- `artifacts/`: Toàn bộ các báo cáo JSON đầu ra, metrics đo đạc phần cứng thực tế và kết quả xuất HL7 FHIR R4 Bundle.
- `evidence/`: Bộ sưu tập ảnh chụp màn hình bằng chứng kiểm thử UI E2E, giao diện đa thiết bị responsive (Mobile, Tablet, Desktop, Full HD) và kiểm chứng WebGL.
