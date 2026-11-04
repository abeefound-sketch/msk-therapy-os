# MSK-Therapy-OS — Milestone P19 Architecture Decision Records
## P19_05: Duplicate Engine Retirement, Isolation & Deprecation Strategy

**Tài liệu ID:** `MSK-P19-ADR-005`  
**Ngày phê duyệt:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái:** `ACCEPTED_AND_ENFORCED`  

---

### ADR-01: Cách Ly Dữ Liệu Baked Static JSON (`acupuncture_3d.json`) vs. Dynamic Resolver

- **Bối cảnh:** Hai nguồn tọa độ cùng tồn tại: Static JSON (362 huyệt chiếu bề mặt BodyParts3D) và `AnatomicalSpatialResolver` (suy luận B-cun theo mốc). Khi gọi `/api/acupuncture-3d`, backend đang hợp nhất cả hai.
- **Quyết định:** **ISOLATE**. Giữ nguyên cả hai nguồn ở Milestone P19. Static JSON đại diện cho baseline hình học bề mặt; Dynamic Resolver đại diện cho lớp giải thuật B-cun động.
- **Consumer thực tế:** `meridians.js`, `server.py`, `tools/forensics/compare_spatial_sources.py`.
- **Hành vi bảo toàn:** Trình duyệt vẫn tải dữ liệu bình thường thông qua `/api/acupuncture-3d` và cho phép chuyển layer minh bạch.
- **Kế hoạch tương lai (P22):** Trong P22, sau khi có dữ liệu kiểm định chuyên gia độc lập, sẽ thống nhất một pipeline chuyển đổi duy nhất (Unified Spatial Pipeline).
- **Kế hoạch Rollback:** Nếu chuyển đổi gặp lỗi, hoàn nguyên về static baked JSON ban đầu.
- **Hiệu năng & Offline:** Cả 2 đều chạy hoàn toàn local, không yêu cầu kết nối mạng, tải trong $< 15$ ms.

---

### ADR-02: Khai Tử Vĩnh Viễn Offsets Giả Trong Layer `upstream_raw`

- **Bối cảnh:** Trước P18, layer `upstream_raw` trong `spatial_resolver.py` cộng các hằng số giả $dx = -8$mm, $dy = +12$mm, $dz = -10$mm rồi tự xưng là delta model.
- **Quyết định:** **RETIRE_AND_FAIL_CLOSED**. Loại bỏ hoàn toàn các hằng số giả này. Thay bằng phản hồi lỗi tường minh `UPSTREAM_TRANSFORM_UNAVAILABLE`.
- **Consumer thực tế:** Tùy chọn layer "Upstream Raw" trên QA Inspector panel của `meridians.js`.
- **Hành vi bảo toàn:** Trả về tọa độ legacy gốc kèm lý do từ chối rõ ràng trong payload.
- **Bằng chứng kiểm thử:** Test `test_upstream_raw_synthetic_offsets_removed` trong `test_p18_geometry_remediation.py` đạt 100% PASS.
- **Tính an toàn:** Triệt tiêu hoàn toàn rủi ro dữ liệu rác hoặc giả mạo số đo y học.

---

### ADR-03: Cô Lập Mô Hình GLB Của Education Studio Khỏi Atlas Huyệt Đạo

- **Bối cảnh:** Thư mục `msk_therapy_os/static/education/models/` chứa 3 file `.glb` (`anatomy.glb`, `cervicothoracic_skeleton.glb`, `shoulder_skeleton.glb`). Có nguy cơ gây hiểu nhầm rằng các file này là mesh giải phẫu của Atlas huyệt.
- **Quyết định:** **ISOLATE**. Khóa ranh giới: các file `.glb` chỉ phục vụ duy nhất module Education Studio (`/education/`). Atlas 3D (`/atlas/`) không được import hoặc phụ thuộc vào các file này.
- **Consumer thực tế:** `msk_therapy_os/static/education/app.js`.
- **Hành vi bảo toàn:** Education Studio tiếp tục hoạt động đầy đủ với 4 mode tương tác A/B/C/D đã được nghiệm thu tại P17.

---

### ADR-04: Thay Thế Dần B-Cun Proportional Rules Đơn Thuần Bằng Khung Kiểm Định Mốc Đa Chiều (P22 Readiness)

- **Bối cảnh:** `point_localization_rules.py` tính vị trí theo tỷ lệ thốn thẳng hàng 1D, không xét đến độ cong lồi lõm phi tuyến của mặt da 3D, gây ra lỗi nghiêm trọng như ST36 bay trước xương chày 4.5 cm và KI3 ngược trục X lệch 175.45 mm.
- **Quyết định:** **DEPRECATE_AS_PRIMARY_SURFACE_SOURCE**. Đánh dấu các tọa độ suy ra từ `point_localization_rules.py` là `CLASS_B` (chỉ tham khảo tỷ lệ, KHÔNG đại diện cho tọa độ bề mặt thực). Tọa độ bề mặt bắt buộc phải qua phép chiếu mặt tam giác (`closest_point_on_surface`).
- **Kế hoạch di chuyển:** Giữ nguyên quy tắc để tính quan hệ giải phẫu tương đối, nhưng điểm chốt 3D phải được gắn với mốc xương (skeletal anchor) và chiếu lên mặt da thật ở P22.
- **Bằng chứng kiểm thử:** Đã có test tái lập lỗi `test_reproduce_two_spatial_sources_drift` trong `test_p18_reproducible_failures.py`.

---

### ADR-05: Tách Biệt Hoàn Toàn Cơ Sở Dữ Liệu Knowledge Vault Khỏi Cơ Sở Dữ Liệu Bệnh Nhân Lâm Sàng

- **Bối cảnh:** MSK-Therapy-OS cần kho tri thức offline (P20) để lưu trữ y văn, các quan điểm mâu thuẫn và trích dẫn. Nếu lưu chung vào `msk_therapy_os.sqlite3`, rủi ro trộn lẫn thông tin nghiên cứu với dữ liệu bệnh nhân (dù là synthetic) là rất cao.
- **Quyết định:** **SEPARATE_STORAGE**. Triển khai Knowledge Vault P20 với file database riêng biệt: `knowledge_vault/vault.db` (được đưa vào `.gitignore`).
- **Hợp đồng liên kết:** Liên kết tới `1docs/EVIDENCE.md` và Atlas chỉ thông qua các mã định danh (`doc_id`, `claim_id`, `point_code`), không thực hiện JOIN trực tiếp qua database lâm sàng.
- **Tính an toàn:** Đảm bảo triệt để nguyên tắc không rò rỉ dữ liệu, sẵn sàng đáp ứng các quy định bảo mật HIPAA/GDPR khi tiến lên các milestone lâm sàng (P25).
