# MSK-THERAPY-OS V1.1 — BROWSER E2E TEST REPORT
## Báo cáo Kiểm thử Trình duyệt Thực tế End-to-End (Playwright Chromium)

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Kịch bản kiểm thử:** `tests/test_v11_character_pipeline_e2e.py`

---

### 1. TỔNG QUAN KỊCH BẢN KIỂM THỬ

Kịch bản E2E khởi chạy máy chủ thực tế trên cổng độc lập `8211`, sử dụng Chromium Playwright không giả lập (non-mocked WebGL runtime), thực hiện toàn bộ 9 bước kiểm chứng:

1. **Khởi động và Tải Model 3D:**
   - URL: `http://127.0.0.1:8211/character/index.html`
   - Nạp thành công `rigged_human_v11.glb` (16.49 MB) trong $1.76\text{ s}$.
   - Khởi tạo đối tượng `window.__CHARACTER_V11__`.
2. **Kiểm tra Hệ Thống Khung Xương (Armature):**
   - Số lượng xương phát hiện: 53 bones (chuẩn Game Engine Humanoid Rig).
   - Kiểm tra các xương thiết yếu: `clavicle_r`, `upperarm_r`, `lowerarm_r`, `hand_r`, `calf_r`, `thigh_r`, `spine_01..03`.
3. **Kiểm tra SkinnedMesh và Trọng số Da:**
   - Đỉnh hình học: 19.158 đỉnh, 18.486 đa giác.
   - Nhóm trọng số: 52 vertex groups hoạt động.
4. **Kiểm tra Biến dạng Gập Khuỷu Tay (0° -> 45° -> 90°):**
   - Đặt `lowerarm_r` góc quay trục X lần lượt là $0^\circ, 45^\circ, 90^\circ$.
   - Tọa độ bàn tay di chuyển chính xác theo hàm sin/cos của góc gập.
   - Khoảng cách hở khớp đo được: $0.000\text{ mm}$.
5. **Kiểm tra Dạng Vai và Gập Gối:**
   - Khớp vai dạng $45^\circ$, khớp gối gập $60^\circ$ mà không xảy ra biến dạng xé rách da.
6. **Kiểm tra Biến đổi Hình thể Tham số (GPU Morph Targets):**
   - Kích hoạt Height $= 0.8$, ShoulderWidth $= 0.7$, ArmLength $= 0.6$.
   - Hoàn nguyên về $0.00$ với độ trôi $0.000000\text{ m}$.
7. **Kiểm tra Chuyển đổi Ba Chế độ Hiển thị:**
   - `CHARACTER_MODE`: Da hiển thị $100\%$, xương giải phẫu ẩn.
   - `ANATOMY_MODE`: Da ẩn hoàn toàn, xương giải phẫu hiển thị $100\%$.
   - `OVERLAY_MODE`: Da bán trong suốt ($65\%$), xương hiển thị rõ bên trong.
8. **Kiểm tra Tọa độ Huyệt Vị Động (Dynamic Acupoints):**
   - Xác nhận mốc `LI4` bám theo xương bàn tay 2 phải (`hand_r`), di chuyển đồng bộ với bàn tay khi gập khuỷu.
9. **Thu thập 9 Minh chứng Ảnh chụp (Screenshots):**
   - Toàn bộ 9 tệp ảnh telemetry được lưu thành công tại `1docs/product_v11/evidence/`.

---

### 2. KẾT QUẢ THỰC THI (TEST RESULTS)

```
tests/test_v11_character_pipeline_e2e.py::TestV11CharacterPipelineE2E::test_character_api_metadata PASSED [ 20%]
tests/test_v11_character_pipeline_e2e.py::TestV11CharacterPipelineE2E::test_character_api_registrations PASSED [ 40%]
tests/test_v11_character_pipeline_e2e.py::TestV11CharacterPipelineE2E::test_character_api_acupoints_and_undo PASSED [ 60%]
tests/test_v11_character_pipeline_e2e.py::TestV11CharacterPipelineE2E::test_character_api_motion_summary PASSED [ 80%]
tests/test_v11_character_pipeline_e2e.py::TestV11CharacterPipelineE2E::test_character_browser_full_workflow PASSED [100%]

======================== 5 passed in 83.86s (0:01:23) =========================
```
