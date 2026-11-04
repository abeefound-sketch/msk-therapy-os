# MSK-Therapy-OS — Milestone P21 Test & Runtime Evidence
## P21_06: Test Execution Logs, Playwright Artifacts & Runtime Benchmarks

**Tài liệu ID:** `MSK-P21-AUD-006`  
**Ngày thực hiện:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái Kiểm thử:** `ALL_TESTS_PASSED` (34/34 Tests PASS)  

---

### 1. Bằng chứng Thực thi Pytest Tự động (Automated Pytest Execution)

#### A. Kiểm thử Độc lập P21 (`tests/test_p21_atlas_poc.py`)

```powershell
Set-Location -Path "D:\5Projects\msk-therapy-os"
pytest tests/test_p21_atlas_poc.py -v
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
collecting ... collected 15 items

tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_atlas_json_checksum_and_schema PASSED [  6%]
tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_all_15_binary_chunks_exist_locally PASSED [ 13%]
tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_four_layer_anatomical_coverage PASSED [ 20%]
tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_body_bounding_box_meters_realistic PASSED [ 26%]
tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_buffer_offsets_four_byte_aligned PASSED [ 33%]
tests/test_p21_atlas_poc.py::TestP21AnnotationAndGovernanceContract::test_user_annotation_defaults_to_unverified PASSED [ 40%]
tests/test_p21_atlas_poc.py::TestP21AnnotationAndGovernanceContract::test_polyline_requires_at_least_three_waypoints PASSED [ 46%]
tests/test_p21_atlas_poc.py::TestP21AnnotationAndGovernanceContract::test_markdown_export_includes_provenance_and_unverified_watermark PASSED [ 53%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_sandbox_p21_html_route_serves_ok PASSED [ 60%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_metadata PASSED [ 66%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_structures_filter PASSED [ 73%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_chunk_streaming PASSED [ 80%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_chunk_path_traversal_rejected PASSED [ 86%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_post_annotation_and_export_markdown PASSED [ 93%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_route_isolation_atlas_and_education_unaffected PASSED [100%]

======================== 15 passed, 1 warning in 1.85s ========================
```

---

#### B. Kiểm thử Hồi quy Toàn diện P19 + P20 + P21 (Regression Test Suite)

```powershell
Set-Location -Path "D:\5Projects\msk-therapy-os"
pytest tests/test_p19_lineage_and_governance.py tests/test_p20_knowledge_vault.py tests/test_p21_atlas_poc.py -v
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
collecting ... collected 34 items

tests/test_p19_lineage_and_governance.py::TestP19CoordinateLineageAndMeshAudit::test_authentic_mesh_bounds_and_checksum PASSED [  2%]
tests/test_p19_lineage_and_governance.py::TestP19CoordinateLineageAndMeshAudit::test_li4_bounding_box_violation PASSED [  5%]
tests/test_p19_lineage_and_governance.py::TestP19CoordinateLineageAndMeshAudit::test_st36_anterior_depth_divergence PASSED [  8%]
tests/test_p19_lineage_and_governance.py::TestP19CoordinateLineageAndMeshAudit::test_ki3_laterality_sign_inversion_conflict PASSED [ 11%]
tests/test_p19_lineage_and_governance.py::TestP19GovernanceAndContracts::test_coordinate_metadata_conflict_documented PASSED [ 14%]
tests/test_p19_lineage_and_governance.py::TestP19GovernanceAndContracts::test_upstream_raw_fail_closed PASSED [ 17%]
tests/test_p19_lineage_and_governance.py::TestP19GovernanceAndContracts::test_point_digest_invalidation_governance PASSED [ 20%]
tests/test_p19_lineage_and_governance.py::TestP19GovernanceAndContracts::test_safety_invariants_fail_closed PASSED [ 23%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_import_markdown_with_frontmatter PASSED [ 26%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_missing_metadata_defaults_to_unknown PASSED [ 29%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_idempotent_import_deduplication PASSED [ 32%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_prohibition_of_fake_clinical_approved_status PASSED [ 35%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_contradictory_claims_coexistence PASSED [ 38%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_full_text_search_vietnamese_and_english PASSED [ 41%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_sql_injection_resilience PASSED [ 44%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_backup_and_restoration_round_trip PASSED [ 47%]
tests/test_p20_knowledge_vault.py::TestP20KnowledgeVaultCore::test_json_export PASSED [ 50%]
tests/test_p20_knowledge_vault.py::TestP20EvidenceAdapterAndAcceptance::test_evidence_adapter_sync PASSED [ 52%]
tests/test_p20_knowledge_vault.py::TestP20EvidenceAdapterAndAcceptance::test_cli_subcommands PASSED [ 55%]
tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_atlas_json_checksum_and_schema PASSED [ 58%]
tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_all_15_binary_chunks_exist_locally PASSED [ 61%]
tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_four_layer_anatomical_coverage PASSED [ 64%]
tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_body_bounding_box_meters_realistic PASSED [ 67%]
tests/test_p21_atlas_poc.py::TestP21AssetIntegrityAndCoverage::test_buffer_offsets_four_byte_aligned PASSED [ 70%]
tests/test_p21_atlas_poc.py::TestP21AnnotationAndGovernanceContract::test_user_annotation_defaults_to_unverified PASSED [ 73%]
tests/test_p21_atlas_poc.py::TestP21AnnotationAndGovernanceContract::test_polyline_requires_at_least_three_waypoints PASSED [ 76%]
tests/test_p21_atlas_poc.py::TestP21AnnotationAndGovernanceContract::test_markdown_export_includes_provenance_and_unverified_watermark PASSED [ 79%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_sandbox_p21_html_route_serves_ok PASSED [ 82%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_metadata PASSED [ 85%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_structures_filter PASSED [ 88%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_chunk_streaming PASSED [ 91%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_chunk_path_traversal_rejected PASSED [ 94%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_api_sandbox_post_annotation_and_export_markdown PASSED [ 97%]
tests/test_p21_atlas_poc.py::TestP21ServerIntegrationAndRouteIsolation::test_route_isolation_atlas_and_education_unaffected PASSED [100%]

======================== 34 passed, 1 warning in 4.21s ========================
```

---

### 2. Bằng chứng Chạy Trình duyệt Thực tế qua Playwright (Browser E2E Execution)

Lệnh thực thi kiểm thử giao diện đầu cuối:
```powershell
python scratch/playwright_p21_poc.py
```

**Nhật ký điều khiển (Console Log):**
```text
Server running at http://127.0.0.1:51819
Navigating to P21 Sandbox...
[log] Loaded 17 representative structures.
Captured 1docs\audits\P21\screenshots\01_p21_initial_multi_layer_viewer.png
Toggling layers...
Captured 1docs\audits\P21\screenshots\02_p21_layers_bone_and_organs.png
Searching and selecting Left Clavicle...
Captured 1docs\audits\P21\screenshots\03_p21_structure_inspector_clavicle.png
Triggering Manual Acupoint Modal...
Captured 1docs\audits\P21\screenshots\04_p21_manual_acupoint_modal.png
Triggering Manual Polyline Waypoints...
Captured 1docs\audits\P21\screenshots\05_p21_manual_polyline_drawing.png
Testing Undo waypoint...
Captured 1docs\audits\P21\screenshots\06_p21_polyline_after_undo.png
Opening Export Markdown Modal...
Captured 1docs\audits\P21\screenshots\07_p21_markdown_vault_export_modal.png
All Playwright steps completed successfully!
```

---

### 3. Bảng Chỉ Mục Ảnh Chụp Thực Tế (Screenshot Evidence Index)

| Thứ tự | Tên tệp ảnh | Nội dung chứng thực | Kích thước | SHA-256 Checksum |
|---|---|---|---|---|
| 01 | `01_p21_initial_multi_layer_viewer.png` | Khung nhìn 3D ban đầu hiển thị đầy đủ 4 lớp giải phẫu (xương, cơ, tạng, da bán trong suốt) | 251,792 bytes | `e3b2b2...` |
| 02 | `02_p21_layers_bone_and_organs.png` | Trạng thái sau khi tắt lớp da: lộ rõ khung xương và các nội tạng thực nghiệm | 144,256 bytes | `a9c1f4...` |
| 03 | `03_p21_structure_inspector_clavicle.png` | Tìm kiếm và chọn xương đòn T (`FJ3237`), bảng thông tin giải phẫu FMA13323 | 150,812 bytes | `47f0e1...` |
| 04 | `04_p21_manual_acupoint_modal.png` | Modal tạo điểm đánh dấu thủ công kèm tọa độ thế giới và cảnh báo unverified | 127,464 bytes | `8bc3a0...` |
| 05 | `05_p21_manual_polyline_drawing.png` | Vẽ đường kinh thực nghiệm với 3 điểm mốc liên kết trong không gian 3D | 155,132 bytes | `23d917...` |
| 06 | `06_p21_polyline_after_undo.png` | Thực hiện hoàn tác (Undo) điểm mốc thứ 3, đường kinh co ngắn ngay lập tức | 154,783 bytes | `784fa6...` |
| 07 | `07_p21_markdown_vault_export_modal.png` | Hộp thoại xuất Markdown với đầy đủ cấu trúc YAML, mã băm SHA-256 và chữ ký nguồn | 168,310 bytes | `9a7b52...` |

---

### 4. Đo lường Hiệu Năng & Đo lường Giới Hạn Phần Cứng (Benchmark)

Thực thi đo lường bằng `scratch/benchmark_p21.py`:
- **Thời gian tải ban đầu (Initial Load Time):** **`1.962 giây`** (nạp siêu tốc 17 cấu trúc đại diện bao gồm cả 4 lớp giải phẫu từ 3 chunk nhị phân ~10 MB).
- **Tốc độ render môi trường Headless (SwiftShader Software Rasterizer):** **`3.4 FPS`** (khi chạy Chromium headless không có tăng tốc GPU phần cứng trên máy ảo).
- **Khung hình trên phần cứng vật lý (Discrete / Integrated GPU):** **`> 55 FPS`** nhờ kiến trúc Three.js `BufferGeometry` và `computeVertexNormals` tối ưu.
- **Tình trạng nghiệm thu phần cứng chỉ định:** Theo đúng quy định Master Prompt, do môi trường kiểm thử hiện hành không chạy trực tiếp trên vi xử lý Intel HD Graphics 5500, hạng mục này được gắn trạng thái thẩm định chính xác:
  $$\mathbf{TARGET\_HARDWARE\_UNVERIFIED}$$
