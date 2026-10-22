# MSK-Therapy-OS — Project Source of Truth (SOT)

**Cập nhật:** 23/10/2026  
**Quy chuẩn áp dụng:** `D:\1docs\PROJECT_STRUCTURE_CANON.md` & `D:\1docs\GIT_REPO_CANON.md`  
**GitHub Repository:** `https://github.com/abeefound-sketch/msk-therapy-os.git`  
**Nhánh hoạt động:** `hardening/m2.8.2-final-gate`  

---

## 1. Project này là gì?

**MSK-Therapy-OS** là nền tảng Modular Monolith cục bộ (Local-First / Offline-First) phục vụ công tác đào tạo giải phẫu lâm sàng 3D, lượng giá vận động (ROM) và thực hành trị liệu cơ xương khớp (vùng cổ - vai - gáy).

Hệ thống kết hợp ba trụ cột chính:
1. **Giải phẫu học 3D (Atlas):** Tích hợp mô hình giải phẫu BodyParts3D (`FJ2810`), Open Anatomy Atlas WebGL renderer, hỗ trợ 3 chế độ hiển thị (*Surface Mode*, *Musculoskeletal Anatomy*, *Comparative Dual-Viewport*).
2. **Kinh lạc & Phản xạ học chuẩn hóa:** Bản đồ 362 huyệt đạo chuẩn WHO, hệ thống đường kinh lạc (Chính kinh, Kỳ kinh bát mạch Đốc Mạch / Nhâm Mạch) và phản xạ Diện Chẩn với tọa độ bề mặt chính xác 0.00 mm.
3. **Quy trình lâm sàng & Quản trị an toàn:** Quản trị hồ sơ bệnh án (SOAP Notes), xuất chuẩn dữ liệu y tế HL7 FHIR R4 Bundle, bảo mật xác thực danh tính ngoại tuyến PBKDF2-HMAC-SHA256, phân quyền RBAC và chặn cứng các chống chỉ định y khoa (Red Flags / STOP_AND_REFER).

---

## 2. Mục tiêu hiện tại là gì?

1. **Chuẩn hóa cấu trúc dự án:** Tuân thủ 100% chuẩn Canon `1docs / 2data / 3refs / 4incidents`, bảo lưu build journal `.m/` phục vụ phát triển agentic coding.
2. **Nghiệm thu toàn diện Milestone M2.8.2:** Bảo mật danh tính server-enforced RBAC, đăng ký chuyên gia lâm sàng thẩm định (`clinical_reviewers`), sao lưu & phục hồi SQLite an toàn bằng Native Backup API (loại bỏ hoàn toàn `shutil.copy2`), kiểm soát cờ đỏ lâm sàng và đo kiểm WebGL trung thực trên phần cứng thực tế (Intel HD Graphics 5500).
3. **Chuẩn bị nền tảng cho Milestone M3:** Đảm bảo toàn bộ 98 unit tests và 7 kịch bản E2E Playwright chạy xanh 100% không hồi quy trước khi bàn giao người dùng sáp nhập (merge) vào nhánh chính.

---

## 3. SOT / Quyết định quan trọng nằm ở đâu?

### Quy tắc ưu tiên chân lý (Truth Priority):
```text
1docs/ > 4incidents/ > 2data/ > 3refs/ > chat memory
```

### Danh mục tài liệu Source of Truth trong `1docs/`:
- **Đặc tả & Lộ trình thực thi (Specs & Roadmaps):**
  - [`specs/HANDOFF_ROADMAP_V2_1_CODING_AGENT.md`](specs/HANDOFF_ROADMAP_V2_1_CODING_AGENT.md): Roadmap V2.1 & biên bản bàn giao thực thi chi tiết M2.9 - M2.12 và M3-M6 cho coding agent.
  - [`specs/msk-therapy-os-v2.1-artifact-manifest.json`](specs/msk-therapy-os-v2.1-artifact-manifest.json): Bảng kê artifact đính kèm (patch, changed-files, snapshot).
  - [`specs/SPEC.md`](specs/SPEC.md) & [`specs/MSK_Therapy_OS_Engineering_Spec.md`](specs/MSK_Therapy_OS_Engineering_Spec.md): Đặc tả hệ thống gốc.
- **Kiến trúc & Quyết định nền tảng:**
  - [`ARCHITECTURE.md`](ARCHITECTURE.md): Kiến trúc Modular Monolith cục bộ, chia 3 phân hệ Atlas - Therapy - Research.
  - [`DECISIONS.md`](DECISIONS.md): Toàn bộ Architecture Decision Records (ADRs).
  - [`EVIDENCE.md`](EVIDENCE.md): Danh mục chứng cứ lâm sàng và y học chứng cứ (Tier 1 đến Tier 4).
- **Kiểm toán & Báo cáo kỹ thuật (Audits):**
  - [`M282_SECURITY_AUTHORIZATION_AUDIT.md`](audits/M282_SECURITY_AUTHORIZATION_AUDIT.md): Kiểm toán bảo mật PBKDF2, RBAC, CSRF, origin check.
  - [`M282_SQLITE_RECOVERY_VALIDATION.md`](audits/M282_SQLITE_RECOVERY_VALIDATION.md): Kiểm chứng khôi phục SQLite online, maintenance lock HTTP 503, rollback snapshot.
  - [`M282_CLINICAL_SAFETY_ENFORCEMENT.md`](audits/M282_CLINICAL_SAFETY_ENFORCEMENT.md): Chặn cứng chuyển tuyến cờ đỏ, cấm nắn chỉnh cột sống (spinal manipulation).
  - [`M282_WEBGL_PERFORMANCE_FORENSICS.md`](audits/M282_WEBGL_PERFORMANCE_FORENSICS.md): Đo kiểm hiệu năng WebGL thực tế (draw calls, triangles, V8 isolate pool).
- **Ma trận nghiệm thu (Acceptance Matrices):**
  - [`M282_FINAL_ACCEPTANCE_MATRIX.md`](matrices/M282_FINAL_ACCEPTANCE_MATRIX.md): Ma trận truy xuất nguồn gốc 100% yêu cầu kỹ thuật và bằng chứng kiểm thử.

---

## 4. Cách test / chạy / checkpoint là gì?

### 4.1 Khởi động máy chủ phát triển (Development Server):
```bash
# Khởi chạy server chính tại cổng 8080:
python -m msk_therapy_os.server 2data/demo.sqlite3 8080

# Hoặc khởi chạy server prototype cổ - vai - gáy tại cổng 8085:
python prototype/server.py 2data/demo.sqlite3 8085
```
Truy cập giao diện chính: `http://127.0.0.1:8085/`  
Truy cập 3D Anatomy Atlas: `http://127.0.0.1:8085/atlas/`

### 4.2 Chạy bộ kiểm thử tự động (Automated Pytest Suite):
```bash
# Thực thi toàn bộ 98 kiểm thử đơn vị & tích hợp:
python -m pytest tests/
```

### 4.3 Chạy kiểm thử lâm sàng trình duyệt thực (Browser E2E Suite):
```bash
# Khởi động server trước, sau đó chạy kịch bản Playwright:
python prototype/test_clinical_workflows_e2e.py
```

### 4.4 Chạy đo kiểm hiệu năng WebGL phần cứng:
```bash
python prototype/benchmark_webgl_draw_forensics.py
```

### 4.5 Quy trình Checkpoint / Commit theo Canon:
```bash
git add -A
git commit -m "<loại>: <mô tả ngắn gọn>"
git push
```
- `feat:` Tính năng mới
- `fix:` Sửa lỗi
- `docs:` Cập nhật tài liệu SOT trong `1docs/`
- `data:` Cập nhật dữ liệu trong `2data/`
- `incident:` Ghi nhận postmortem trong `4incidents/`
- `chore:` Cấu hình, bảo trì repo

---

## 5. Điều gì KHÔNG được làm?

1. **Tuyệt đối không biến đổi lưới da và tọa độ chuẩn:** Không được sửa đổi file lưới chuẩn BodyParts3D `FJ2810` và dataset `acupuncture_3d.json` chuẩn WHO; các hiệu chỉnh phải đi qua cơ chế Reference Point Overrides lưu trong SQLite.
2. **Không phê duyệt SOAP note có cờ đỏ khi thiếu hồ sơ chuyển tuyến:** Người giám sát chỉ được duyệt ca bệnh `STOP_AND_REFER` khi trong ghi chú phản hồi có văn bản xác nhận chỉ định chuyên khoa từ bác sĩ ngoại thần kinh/chấn thương chỉnh hình.
3. **Tuyệt đối cấm thao tác giật nắn cột sống vận tốc cao (`spinal_manipulation`):** Đây là kỹ thuật có rủi ro cao (chấn động tủy, bóc tách động mạch đốt sống), nghiêm cấm học viên thực hiện trong môi trường đào tạo cơ sở.
4. **Không xóa hoặc đưa `.m/` vào `.gitignore`:** Thư mục `.m/` là build journal lịch sử xây dựng sản phẩm của coding agent, phải luôn được lưu giữ và backup lên GitHub.
5. **Không đưa Secrets vào repository:** Tuyệt đối không commit private keys, mật khẩu, JWT secret hay file `.env` vào kho mã nguồn.
6. **Không đưa dữ liệu thô vào `1docs/`:** Dữ liệu số, database, file đo đạc thô phải lưu tại `2data/`; chỉ chưng cất kết luận và chính sách đã qua phân tích vào `1docs/`.
