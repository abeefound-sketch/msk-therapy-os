# Postmortem: Methodological V8 Isolate Memory Double-Counting

**Ngày phát hiện:** 22/10/2026  
**Mức độ nghiêm trọng:** P1 (Reporting & Measurement Integrity)  
**Tập tin liên quan:** `prototype/benchmark_physical_performance.py`, `prototype/benchmark_webgl_draw_forensics.py`  
**Trạng thái:** RESOLVED  

---

## 1. Triệu chứng
Các báo cáo hiệu năng ban đầu tuyên bố ứng dụng tiêu thụ tới **318 MB** RAM bằng cách cộng dồn bộ nhớ:
- `Host Window usedJSHeapSize`: ~159 MB
- `Atlas Iframe usedJSHeapSize`: ~159 MB
- Tổng cộng: 159 MB + 159 MB = 318 MB.

## 2. Nguyên nhân gốc rễ (Root Cause)
1. Trong Google Chromium và trình thông dịch V8, các iframe có cùng nguồn gốc (same-origin, e.g. `http://127.0.0.1:8085` và `http://127.0.0.1:8085/atlas/`) được chạy bên trong **cùng một tiến trình hệ điều hành (Renderer OS Process)** và sử dụng **chung một V8 isolate heap pool**.
2. Khi gọi `window.performance.memory.usedJSHeapSize` từ trang cha và từ trang con trong iframe, Chromium trả về cùng một giá trị thống kê bộ nhớ của toàn bộ isolate.
3. Việc lấy hai giá trị này cộng lại là sai lầm kinh điển về phương pháp luận (Double-Counting Error), nhân đôi vô lý lượng bộ nhớ thực tế.

## 3. Giải pháp khắc phục
1. Giải thích minh bạch cơ chế chia sẻ V8 isolate trong tài liệu kiến trúc.
2. Đo kiểm trực tiếp heap thực tế qua giao thức Chrome DevTools Protocol (CDP): phát hiện các đối tượng JavaScript còn sống (reachable JS objects) chỉ chiếm **9.63 MB**; tổng dung lượng V8 isolate cam kết là **168.80 MB** (bao gồm các WebGL ArrayBuffers lưu trữ tọa độ đỉnh giải phẫu).
3. Đính chính toàn bộ báo cáo nghiệm thu và ma trận hiệu năng.
