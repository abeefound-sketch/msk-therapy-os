# 4incidents — Incident Logs & Postmortems

Thư mục ghi nhận toàn bộ các lỗi nghiêm trọng, sự cố kiến trúc, phân tích nguyên nhân gốc rễ (Root Cause Analysis - RCA) và bài học kinh nghiệm trong quá trình phát triển MSK-Therapy-OS theo quy chuẩn `PROJECT_STRUCTURE_CANON.md`.

## Nguyên tắc ghi nhận sự cố:
Mỗi khi phát hiện hoặc xử lý một lỗi nghiêm trọng (P0/P1), kỹ sư phụ trách phải chưng cất thành tài liệu postmortem theo mẫu:
1. **Mô tả hiện tượng & Mức độ ảnh hưởng:** Triệu chứng hiển thị hoặc rủi ro dữ liệu/lâm sàng.
2. **Bằng chứng tái hiện lỗi:** Test case hoặc hình ảnh chứng minh lỗi tồn tại thực tế.
3. **Nguyên nhân gốc rễ (Root Cause):** Phân tích ở cấp độ mã nguồn, pipeline đồ họa hoặc luồng giao tiếp.
4. **Giải pháp khắc phục triệt để:** Bản vá kiến trúc giải quyết tận gốc, không dùng giải pháp ngụy tạo thẩm mỹ (cosmetic workaround).
5. **Biện pháp phòng ngừa hồi quy:** Bài kiểm thử tự động bảo vệ vĩnh viễn không để lỗi lặp lại.

## Danh mục Postmortems chính:
- [`2026-10-21_p0_meridian_overlay_leakage.md`](2026-10-21_p0_meridian_overlay_leakage.md): Tràn đường kinh lạc ra ngoài viewport khi zoom và lệch tâm viewport Comparative.
- [`2026-10-21_skin_opacity_hidden_flag.md`](2026-10-21_skin_opacity_hidden_flag.md): Điều khiển độ mờ da Skin 100% không hiển thị do cờ khởi tạo `HIDDEN_BY_DEFAULT`.
- [`2026-10-22_v8_memory_double_counting.md`](2026-10-22_v8_memory_double_counting.md): Sai lầm phương pháp luận cộng dồn bộ nhớ V8 isolate giữa trang chủ và iframe (159MB + 159MB = 318MB ảo).
- [`2026-10-22_sqlite_shutil_restore_risk.md`](2026-10-22_sqlite_shutil_restore_risk.md): Rủi ro hỏng cơ sở dữ liệu và lỗi khóa file WinError 32 do dùng `shutil.copy2` trên database đang mở.
- [`2026-10-22_clinical_red_flag_bypass.md`](2026-10-22_clinical_red_flag_bypass.md): Lỗ hổng cho phép tạo buổi trị liệu manual therapy trên bệnh án cờ đỏ mà thiếu xác nhận chuyển tuyến.
