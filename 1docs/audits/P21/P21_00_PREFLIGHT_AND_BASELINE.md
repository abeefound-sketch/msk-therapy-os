# MSK-Therapy-OS — Milestone P21 Forensic Preflight
## P21_00: Baseline Survey, Environment Integrity & Safety Preflight

**Tài liệu ID:** `MSK-P21-AUD-000`  
**Ngày thực hiện:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Vai trò:** Principal 3D Anatomical Systems Architect + Forensic Code Auditor + Test Automation Engineer  
**Trạng thái Baseline:** `P20_BASELINE_PRESERVED`  

---

### 1. Khảo sát Working Tree & Git Provenance

Thực hiện kiểm tra hiện trạng mã nguồn trước khi can thiệp:

| Thuộc tính | Giá trị quan sát thực tế (Observed) | Ghi chú & Thẩm định |
|---|---|---|
| **Repository Root** | `D:\5Projects\msk-therapy-os` | Môi trường Windows 11 64-bit |
| **Active Branch** | `fix/p18-meridian-anatomical-geometry` | Nhánh hoàn thiện P18, duy trì liên tục cho P19–P21 |
| **HEAD Commit** | `4990f173a880e8a671c0622a04dd88c67264679c` | `fix(p18): remediate anatomical geometry divergence, engine cache bug and procedural fallback` (Sun Nov 1 00:27:17 2026 +0700) |
| **Trạng thái Working Tree** | Dirty có kiểm soát (Uncommitted P19 & P20 deliverables preserved) | Bảo vệ toàn bộ tài liệu và code P19/P20, không stash/reset |
| **Tệp tin P19 đang giữ** | `1docs/audits/P19/*`, `1docs/ROADMAP_P19_P26_GATED.md`, `tests/test_p19_lineage_and_governance.py` | Toàn vẹn 100%, 8/8 test passed |
| **Tệp tin P20 đang giữ** | `msk_therapy_os/knowledge_vault/*`, `knowledge_vault/*`, `1docs/P20_*`, `tests/test_p20_knowledge_vault.py` | Toàn vẹn 100%, 11/11 test passed |

---

### 2. Kiểm tra Kết quả Rerun Test Suite P19 & P20

Thực hiện kiểm tra tái xác nhận độc lập tại thời điểm bắt đầu P21:

```powershell
Set-Location -Path "D:\5Projects\msk-therapy-os"
pytest tests/test_p19_lineage_and_governance.py tests/test_p20_knowledge_vault.py -v
```

**Kết quả quan sát thực tế:**
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: D:\5Projects\msk-therapy-os
configfile: pytest.ini
plugins: anyio-4.14.1, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 19 items

tests/test_p19_lineage_and_governance.py::TestP19CoordinateLineageAndMeshAudit::test_authentic_mesh_bounds_and_checksum PASSED [  5%]
tests/test_p19_lineage_and_governance.py::TestP19CoordinateLineageAndMeshAudit::test_li4_bounding_box_violation PASSED [ 10%]
tests/test_p19_lineage_and_governance.py::TestP19CoordinateLineageAndMeshAudit::test_st36_anterior_depth_divergence PASSED [ 15%]
tests/test_p19_lineage_and_governance.py::TestP19CoordinateLineageAndMeshAudit::test_ki3_laterality_sign_inversion_conflict PASSED [ 21%]
tests/test_p19_lineage_and_governance.py::TestP19GovernanceAndContracts::test_coordinate_metadata_conflict_documented PASSED [ 26%]
tests/test_p19_lineage_and_governance.py::TestP19GovernanceAndContracts::test_upstream_raw_fail_closed PASSED [ 31%]
tests/test_p19_lineage_and_governance.py::TestP19GovernanceAndContracts::test_point_digest_invalidation_governance PASSED [ 36%]
tests/test_p19_lineage_and_governance.py::TestP19GovernanceAndContracts::test_safety_invariants_fail_closed PASSED [ 42%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_import_markdown_with_frontmatter PASSED [ 47%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_missing_metadata_defaults_to_unknown PASSED [ 52%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_idempotent_import_deduplication PASSED [ 57%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_prohibition_of_fake_clinical_approved_status PASSED [ 63%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_contradictory_claims_coexistence PASSED [ 68%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_full_text_search_vietnamese_and_english PASSED [ 73%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_sql_injection_resilience PASSED [ 78%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_backup_and_restoration_round_trip PASSED [ 84%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_json_export PASSED [ 89%]
tests/test_p20_knowledge_vault.py::TestP20EvidenceAdapterAndAcceptance::test_evidence_adapter_sync PASSED [ 94%]
tests/test_p20_knowledge_vault.py::TestP20EvidenceAdapterAndAcceptance::test_cli_subcommands PASSED [100%]

============================= 19 passed in 2.66s ==============================
```

---

### 3. Khảo sát Kho Dữ liệu Upstream Có sẵn trong Workspace

Kiểm tra thư mục `3refs/upstream/` hiện hữu:

| Upstream Directory | Vai trò & Nguồn gốc | Tệp tin 3D chính | Tổng dung lượng | Trạng thái kỹ thuật |
|---|---|---|---|---|
| `3refs/upstream/tcm-3d` | BodyParts3D 4.0 via ashemag/human-atlas | `atlas.json` + `body-0.bin` .. `body-14.bin` | ~59 MB (15 chunks) | **Sẵn sàng 100% offline**, 2,234 cấu trúc giải phẫu có FMA ID |
| `3refs/upstream/tcm-acupoints` | Z-Anatomy via hpfrei / spacejohnlf | `public/models/body.glb` | 8.25 MB | Draco-compressed GLB, chủ yếu xương/cơ |
| `3refs/upstream/anatomy-3d` | BodyParts3D muscle subset via WaterCMY | `models/anatomy.glb` | 9.29 MB | 54 nhóm cơ + xương; thiếu nội tạng |
| `3refs/upstream/acupuncture-3d-authoring` | Meridian Studio via spacejohnlf | `female-character.glb`, `male_character.glb` | 24.5 MB & 13.9 MB | Chỉ có mesh bề mặt da (Skin-only); không có xương/cơ/tạng |

---

### 4. Thiết lập Ranh giới An toàn và Nguyên tắc P21

1. **Tuyệt đối không sửa đổi runtime `/atlas/`:** Toàn bộ công tác P21 được triển khai độc lập trong thư mục sandbox `msk_therapy_os/static/sandbox_p21/` và endpoint `/sandbox/p21/`, không làm gián đoạn hay thay đổi bất kỳ dòng mã nào của hệ thống `/atlas/` đang chạy.
2. **Không sửa công thức tọa độ huyệt cũ:** Không cố gắng điều chỉnh các công thức nội suy procedural trong P21. Mọi điểm đánh dấu trong P21 là do người dùng tương tác đặt trực tiếp (`USER_ANNOTATED_UNVERIFIED`).
3. **Không dùng hình học giả lập:** Tuyệt đối không sinh hình cầu, khối trụ (cylinder) hay ellipsoid để giả vờ làm xương hay tạng. Sử dụng trực tiếp mesh tam giác thực từ BodyParts3D 4.0.
4. **Phân biệt rõ cấp phép mã nguồn và cấp phép dữ liệu:** Mã nguồn (MIT) không tự động cấp quyền sở hữu dữ liệu 3D (CC-BY 4.0 hoặc CC-BY-SA 4.0).
5. **Fail-Closed khi đổi mesh:** Không âm thầm dịch chuyển tọa độ khi đổi mô hình; bắt buộc lưu kèm SHA-256 của asset và cấu trúc mesh gắn kết.
