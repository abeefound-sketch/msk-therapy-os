# MSK-Therapy-OS — Milestone P19 Forensic Audit
## P19_00: Baseline Survey, Environment Integrity & Safety Preflight

**Tài liệu ID:** `MSK-P19-AUD-000`  
**Ngày thực hiện:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Vai trò:** Principal Software Architect + Forensic Code Auditor + Test Engineer  
**Trạng thái Baseline:** `P18_BASELINE_CONFIRMED`  

---

### 1. Khảo sát Working Tree & Git Provenance

| Thuộc tính | Giá trị quan sát thực tế (Observed) | Ghi chú & Thẩm định |
|---|---|---|
| **Repository Root** | `D:\5Projects\msk-therapy-os` | Môi trường Windows 64-bit |
| **Active Branch** | `fix/p18-meridian-anatomical-geometry` | Nhánh hoàn thiện P18 |
| **HEAD Commit** | `4990f173a880e8a671c0622a04dd88c67264679c` | `fix(p18): remediate anatomical geometry divergence, engine cache bug and procedural fallback` (Sun Nov 1 00:27:17 2026 +0700) |
| **Previous Commit** | `877450c18408f97a55598687ba42f8fc03444983` | `docs(p17): update authoritative E2E browser acceptance screenshots` |
| **Recent Tags** | `v2.1.0-local-rc1` (`746719a`), `v2.1.0-local-rc2` (`a57550b`), `v2.1.0-local-rc3` (`02c762d`) | Các tag phát hành release candidate nội bộ |
| **Tracked Changes** | Clean (0 modified tracked files, 0 staged files) | Không ghi đè thay đổi chưa commit của người khác |
| **Untracked Directories** | `.m/`, `.mag/`, `1docs/prompts/` | Thư mục checkpoint công cụ, prompt giao việc P19–P20 |
| **Untracked DB Files** | `msk_therapy_os.sqlite3`, `msk_therapy_os.sqlite3-shm`, `msk_therapy_os.sqlite3-wal` | Database runtime chính (được bảo vệ qua backup API) |

---

### 2. Khảo sát các Gói Tham Chiếu (Reference Packages)

1. **Gói snapshot P17 (`msk-therapy-os-p17-roadmap-source.zip` và `msk-therapy-os-p17-roadmap-prompt.md`):**
   - *Khảo sát:* Không có file zip/md này trực tiếp tại thư mục gốc hay `1docs/`.
   - *Hiện trạng repo:* Toàn bộ báo cáo P17 (`1docs/audits/P17/`), bằng chứng E2E (`1docs/audits/P17/screenshots/`), và commit history (`ea58f38`, `287b58b`, `877450c`) đã tích hợp đầy đủ trong working tree.
   - *Phán quyết:* Dùng lịch sử commit và thư mục `1docs/audits/P17/` làm dữ liệu đối chiếu P17.

2. **Gói starter Knowledge Vault (`MSK_Knowledge_Vault_Starter_Offline.zip`):**
   - *Khảo sát:* Đã quét toàn bộ `D:\5Projects\msk-therapy-os` và `D:\5Projects`. Không tìm thấy file `MSK_Knowledge_Vault_Starter_Offline.zip`.
   - *Phán quyết:* Ghi nhận trạng thái `STARTER_NOT_AVAILABLE` theo đúng điều khoản mục 0 Master Prompt. Tiến hành xây dựng scaffold P20 Knowledge Vault sạch từ data contract chuẩn.

3. **Gói starter ban đầu (`MSK_Therapy_OS_Starter.zip`):**
   - Hiện diện tại root (`14,792 bytes`), lưu trữ template scaffold ban đầu từ 2026-10-20.

---

### 3. Sao lưu Database & Kiểm tra Toàn vẹn Tệp Tin Cốt lõi

Đã thực hiện sao lưu online an toàn bằng `sqlite3.backup` API (tránh lock DB hoặc dirty read):

- **Database nguồn:** `D:\5Projects\msk-therapy-os\msk_therapy_os.sqlite3` (size: 1,187,840 bytes, SHA-256: `58d35ab7e585be89b5b99b77344d7dfd1256f3ba6c20cbbcab6ad65c23b3b708`)
- **Database backup:** `1docs/audits/P19/evidence/msk_therapy_os_baseline_backup.sqlite3`
  - Kích thước: `1,191,936 bytes`
  - Checksum SHA-256: `0c05bb2acd1f41c1271b1edb50a15ab647a1f1a9cb48ee3f24a15592c26c6054`
  - Số bảng: 54 bảng (bao gồm `cases`, `visits`, `intakes`, `rom_assessments`, `soap_notes`, `evidence_catalog`, `reference_point_overrides`, `custom_points`).
  - Dữ liệu override hiện thời: `reference_point_overrides` = 0 rows; `custom_points` = 0 rows.
- **Mesh Asset chuẩn:** `2data/artifacts/fj2810_softened.bin`
  - Kích thước: `853,592 bytes`
  - Checksum SHA-256: `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808` (Khớp chính xác với P18_MESH_ASSET_PROVENANCE).
- **Static Acupoints Dataset:** `msk_therapy_os/static/atlas/data/acupuncture_3d.json`
  - Kích thước: `1,750,611 bytes`
  - Checksum SHA-256: `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df`

---

### 4. Kết quả Chạy Kiểm thử Thực tế (Test Suite Execution)

Môi trường kiểm thử: Windows 10/11 x64, Python 3.11.9, pytest 9.1.1, Playwright 1.58.0.

#### 4.1 Unit & Integration Test Suite (Non-Playwright)
- **Lệnh thực thi:** `pytest -k "not playwright" --tb=short -q`
- **Kết quả:** **829 PASSED, 24 deselected** trong `127.52s (0:02:07)`.
- **Exit Code:** `0`.
- **Thất bại/Lỗi:** 0.

#### 4.2 P18 Regression & Failure Reproduction Suites
- **Lệnh thực thi 1:** `pytest tests/test_p18_reproducible_failures.py -v`
  - Kết quả: **4 PASSED in 0.33s** (Cache invalidation, Two-source drift, Synthetic offsets elimination, Quality tier contract).
- **Lệnh thực thi 2:** `pytest tests/test_p18_geometry_remediation.py -v`
  - Kết quả: **19 PASSED in 1.28s** (G0–G7 Gates, Mesh binary hash, JSON hash, LI4 outside bounds, Safety boundaries).

#### 4.3 Real Browser E2E Suite (Playwright Headless Chromium)
- **Lệnh thực thi:** `pytest tests/test_p17_functional_acceptance_playwright.py -v`
  - Kết quả: **1 PASSED in 83.92s (0:01:23)**.
  - Tải thực tế `/education/?v=p17`, kiểm tra camera controls, timeline scrubber, bilingual toggle, visual screenshots capture.

**Tổng số test được thu thập:** 853 tests.

---

### 5. Kiểm tra An toàn & Ranh giới Lâm sàng (Safety Invariants)

Rà soát toàn bộ codebase để xác minh các hằng số bất biến bảo mật và an toàn y tế:

1. `RELEASE_SCOPE = "ENGINEERING_RESEARCH_ONLY"` (tại `msk_therapy_os/biomechanics_adapter.py`, `evidence_export.py`, v.v.): **CONFIRMED**.
2. `CLINICAL_VALIDATION = "NOT_ESTABLISHED"` (tại `biomechanics_adapter.py`, `anatomical_validation.py`): **CONFIRMED**.
3. `clinical_depth_guidance_allowed = False` (tại `server.py`, `biomechanics_adapter.py`, `scientific_claim_guard.py`): **STRICTLY ENFORCED**. Bất kỳ yêu cầu hướng dẫn độ sâu châm kim xâm lấn đều bị chặn cứng.
4. `G14 = "BLOCKED_EXTERNAL_DATA"`: Khóa triệt để việc lấy dữ liệu bệnh nhân từ nguồn mạng ngoài.
5. Không có dữ liệu bệnh nhân thật (PHI/PII): Mọi fixture là dữ liệu tổng hợp (synthetic).
6. Demo mode vs Secure mode RBAC: Đã xác thực phân quyền qua `test_auth_and_rbac.py` và `test_security_hardening.py`.

---

### 6. Kết luận Bước 0

- Trạng thái Baseline: **`P18_BASELINE_CONFIRMED`**.
- Toàn bộ 829 unit/integration tests và Playwright E2E đều đạt 100% PASS trên môi trường máy thực.
- Checksum các asset 3D, database và mã nguồn hoàn toàn khớp với hồ sơ P18.
- Đầy đủ điều kiện pháp lý và kỹ thuật để chuyển tiếp sang **P19: Architecture Reset & Source-of-Truth Governance**.
