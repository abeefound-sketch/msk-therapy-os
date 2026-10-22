# Postmortem: Skin Opacity Slider Nonfunctional Due to HIDDEN_BY_DEFAULT Flag

**Ngày phát hiện:** 21/10/2026  
**Mức độ nghiêm trọng:** P1 (UI Control Misleading)  
**Tập tin liên quan:** `msk_therapy_os/static/atlas/app.js`, `msk_therapy_os/static/atlas/gl.js`  
**Trạng thái:** RESOLVED  

---

## 1. Triệu chứng
Giao diện thanh trượt hiển thị `Skin: 100%`, nhưng mô hình giải phẫu 3D trên màn hình vẫn chỉ hiển thị các bó cơ bắp lộ thiên mà không hề có lớp da bao bọc. Kéo thanh trượt từ 0% đến 100% không tạo ra bất kỳ thay đổi thị giác nào.

## 2. Nguyên nhân gốc rễ (Root Cause)
1. Trong `atlas/app.js`, danh mục lớp `skin` được xếp vào mảng `HIDDEN_BY_DEFAULT`.
2. Trong hàm dựng `gl.js`, shader chỉ thực hiện tính toán độ mờ `skinOpacity` khi cờ hiển thị lưới `mesh.visible` có giá trị `true`.
3. Do `mesh.visible` đang bị tắt (`false`) bởi cờ mặc định, biến đồng phục (uniform) `u_opacity` trong WebGL shader hoàn toàn không được truyền đến GPU, biến thanh trượt thành nút điều khiển trang trí vô tác dụng.

## 3. Giải pháp khắc phục
1. Tự động bật `mesh.visible = true` ngay khi `skinOpacity > 0` trong `setSkinOpacity()`.
2. Khi `skinOpacity === 0`, chuyển trạng thái `mesh.visible = false` để tối ưu hóa hiệu năng loại bỏ hoàn toàn draw call cho lớp da.
3. Đồng bộ trạng thái hai chiều giữa iframe Atlas và trang chủ qua `postMessage`.
