# Postmortem: Downstream Therapy Session Bypass on Active Red Flags

**Ngày phát hiện:** 22/10/2026  
**Mức độ nghiêm trọng:** P0 (Clinical Safety / Contraindication Enforcement)  
**Tập tin liên quan:** `msk_therapy_os/tracking.py`, `msk_therapy_os/soap.py`  
**Trạng thái:** RESOLVED  

---

## 1. Triệu chứng
Hệ thống hiển thị cảnh báo cờ đỏ lâm sàng (`STOP_AND_REFER` / `safe_to_proceed = False`) trên giao diện khi người bệnh có triệu chứng chèn ép tủy cổ hoặc thiếu máu não hệ sống nền. Tuy nhiên, người dùng/học viên vẫn có thể gọi endpoint `/api/session` để tạo một buổi trị liệu thực tế (châm cứu/xoa bóp/nắn bóp) mà không có bất kỳ rào chắn nào ngăn chặn ở tầng backend.

## 2. Nguyên nhân gốc rễ (Root Cause)
1. Cơ chế sàng lọc an toàn (`safety.py`) chỉ đóng vai trò khuyến cáo hiển thị trên giao diện người dùng (UI warning) mà chưa được kết nối trực tiếp làm điều kiện tiền đề (pre-condition) trong luồng nghiệp vụ ghi nhận can thiệp tại `record_session()` và `review_soap_note()`.
2. Thiếu kiểm tra thẩm quyền bác sĩ chuyên khoa: Học viên có thể tự phê duyệt kế hoạch mà không cần bằng chứng chuyển tuyến ngoại viện.

## 3. Giải pháp khắc phục
1. **Chặn cứng ở tầng Backend:** Trong `record_session()` ([`tracking.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/tracking.py)), nếu lượt khám có cờ đỏ (`flag != 'none'`) mà phần ghi chú chưa có từ khóa xác nhận chỉ định chuyên khoa (`referral`, `cleared`, `physician`), hệ thống lập tức ném ngoại lệ `ValueError` và chặn đứng giao dịch.
2. **Cấm tuyệt đối nắn chỉnh cột sống:** Cấm hoàn toàn modality `spinal_manipulation` trên toàn hệ thống.
3. **Chặn duyệt SOAP Note:** Người giám sát chỉ có thể phê duyệt SOAP Note cờ đỏ khi có ghi nhận chỉ định chuyển tuyến trong phần phản hồi.
4. **Đánh dấu lỗi FHIR R4:** Các lượt khám bị từ chối hoặc chưa duyệt xuất ra FHIR Encounter với trạng thái `entered-in-error` (nullified).
