# Postmortem: 3D Meridian Overlay Leakage and Comparative Viewport Misalignment

**Ngày phát hiện:** 21/10/2026  
**Mức độ nghiêm trọng:** P0 (Rendering / UI Integrity)  
**Tập tin liên quan:** `msk_therapy_os/static/atlas/meridians.js`, `msk_therapy_os/static/atlas/gl.js`  
**Trạng thái:** RESOLVED  

---

## 1. Triệu chứng
Khi người dùng phóng to (zoom) mô hình giải phẫu 3D tại chế độ Surface hoặc Musculoskeletal, các đường kinh lạc có màu sắc sặc sỡ tràn ra ngoài khung canvas 3D, đè lên thanh bên Layers và các phần tử UI khác. Ở chế độ Comparative, mô hình giải phẫu và các điểm huyệt/đường kinh bề mặt bị lệch tâm nghiêm trọng.

## 2. Nguyên nhân gốc rễ (Root Cause)
1. **Thiếu Scissor Test trong WebGL:** Canvas 3D vẽ đè ra toàn bộ khung nhìn mà không kích hoạt `gl.enable(gl.SCISSOR_TEST)` và không cập nhật `gl.scissor()` tương ứng với kích thước viewport thực tế khi người dùng kéo thanh trượt chia đôi màn hình.
2. **Sai lệch ma trận chiếu trong chế độ Comparative:** Chế độ so sánh chia đôi màn hình tính toán `aspectRatio` dựa trên toàn bộ chiều rộng canvas thay vì một nửa chiều rộng (`canvas.width / 2`), dẫn đến ma trận hình chiếu `perspective` bị méo và lệch tọa độ đối xứng sagital.

## 3. Giải pháp khắc phục
1. Kích hoạt `gl.enable(gl.SCISSOR_TEST)` trước mỗi lần dựng khung hình trong `gl.js`, thiết lập vùng cắt chính xác theo viewport hiển thị.
2. Cập nhật hàm tính toán camera trong `meridians.js` và `gl.js` để truyền đúng kích thước từng nửa viewport (`width / 2`) cho ma trận chiếu.
3. Bổ sung kịch bản kiểm thử Playwright tự động zoom 3.5x và so sánh điểm ảnh để bảo vệ không bị hồi quy.
