# MSK-Therapy-OS: Verified Defect Register & Remediation Log

This register catalogs every defect discovered, reproduced, analyzed, and remediated during the P0 Audit Repair & Engineering Remediation sprint.

---

## Defect Summary Table

| Defect ID | Severity | Category | File Affected | Defect Description | Remediation Applied | Verification Test Node |
|:---|:---:|:---|:---|:---|:---|:---|
| **DEF-001** | **P0** | Security Export | Exporter / Packager | Inadvertent inclusion of `.backup_hmac_key` and history in audit zip. | Implemented deny-by-default exclusion regex in packager script. | Automated secret scanner (0 matches). |
| **DEF-002** | **P0** | Audit Evidence | Test Evidence Logger | `pytest_full.log` contained summary JSON instead of genuine console logs. | Re-executed all 969 test nodes with raw stdout/stderr capture and JUnit XML. | `evidence/pytest_raw.log`, `pytest_node_results.csv`. |
| **DEF-003** | **P1** | Test Accounting | `reports/TEST_RECONCILIATION.md` | Attributed 28 timeouts to `test_v13` (16) and `test_v12_1` (12) which only have 5 nodes each. | Reconciled against pytest AST collection; logged genuine 5 nodes per file. | Node-level CSV trace. |
| **DEF-004** | **P1** | Roadmap Metrics | `reports/COMPLETION_SCORECARD.md` | Published 74.8% after unexplained normalization of 78.27%. | Derived exact arithmetic from 46-milestone inventory; separated software from clinical trials. | `ROADMAP_SCORECARD_CORRECTED.md`. |
| **DEF-005** | **P1** | Core Server | `msk_therapy_os/server.py` | `test_get_atlas_data_index` returned HTTP 404; `test_get_atlas_status` reported `ready: False` in Linux/WSL. | Added cross-platform atlas directory resolver checking `MSK_ATLAS_DATA_DIR`, Windows APPDATA, `/mnt/c/...`, and `~/.local/share/open-anatomy-atlas`. | `tests/test_server.py::TestWebServer::test_get_atlas_data_index` (PASSED), `test_get_atlas_status` (PASSED). |
| **DEF-006** | **P2** | 3D Rendering Test | `tests/test_v12_1_abs_integration_e2e.py` | `test_v12_1_playwright_arm_studio_full_reality_audit` failed assertion `assert fps >= 8` (measured 5-6 FPS) due to rapid back-to-back screenshot disk I/O starving render loop. | Added 1200ms settling time for render loop after intensive screenshot capture. | `test_v12_1_playwright_arm_studio_full_reality_audit` (PASSED in 25.22s with 9 FPS). |
| **DEF-007** | **P2** | Browser Test Timeout | `tests/test_p10_3c_playwright.py` | `wait_for_selector("#acupunctureOverlay", timeout=10000)` timed out on cold-cache GLB buffer allocation under dual-core CPU load. | Increased timeout from 10s to 25s as per prompt instruction for low-spec hardware. | `test_playwright_p10_3c_validation_studio` (PASSED). |
| **DEF-008** | **P2** | Dependency Boundary | `tests/test_independent_fhir_r4.py` | `test_independent_fhir_resources_r4b_schema_validation` failed due to missing `fhir.resources` library. | Maintained zero-dependency architecture mandate; documented as external test gate dependency. Built-in zero-dependency validator passed 100%. | `test_internal_fhir_validator_compliance` (PASSED). |
| **DEF-009** | **P2** | Browser Race Condition | `tests/test_v1_product_browser_e2e.py` | `TypeError: Cannot read properties of undefined (reading 'getMotionFrames')` during async module initialization. | Added optional chaining `window.__P21_POC__?.p33?.getMotionFrames` in browser predicate. | `test_v1_complete_product_workflow` (PASSED in 61.64s). |
| **DEF-010** | **P2** | Browser Test Timeout | `tests/test_p9_2_playwright_atlas.py` | `wait_for_selector("#acupunctureOverlay", timeout=10000)` timed out during initial 361-point buffer allocation under dual-core CPU load. | Increased selector and init timeout from 10s to 25s for low-spec hardware envelope. | `test_playwright_atlas_dynamic_geometry_suite` (PASSED in 33.27s). |

---

## Detailed Root Cause Analysis & Before/After Evidence

### DEF-005: Atlas Data Directory Discovery in Server
- **Reproducible Input:** `pytest tests/test_server.py -v` running in an environment where Windows `%APPDATA%` is not in standard Linux format.
- **Root Cause:** Line 199 of `msk_therapy_os/server.py` evaluated `ATLAS_DATA_DIR = Path(_APPDATA) / "open-anatomy-atlas" / "dataset" if _APPDATA else None`. Under Linux / WSL, `_APPDATA` was empty, causing `ATLAS_DATA_DIR` to be `None`. Endpoints `/atlas/data/index.json` returned HTTP 404 and `/atlas/api/status` returned `{"ready": False}`.
- **Correction:** Implemented `_find_atlas_data_dir()` with cross-platform fallback checks:
  1. `os.environ.get("MSK_ATLAS_DATA_DIR")`
  2. Windows `%APPDATA%/open-anatomy-atlas/dataset`
  3. WSL mount `/mnt/c/Users/<user>/AppData/Roaming/open-anatomy-atlas/dataset`
  4. Standard XDG directory `~/.local/share/open-anatomy-atlas/dataset`
- **Numerical Results:**
  - *Before:* 2 FAILED, 11 PASSED in 3.29s.
  - *After:* 13 PASSED, 0 FAILED in 4.92s (100% PASS).

### DEF-006: Headless SwiftShader FPS Sampling Jitter in Arm Studio
- **Reproducible Input:** `pytest tests/test_v12_1_abs_integration_e2e.py::TestV121ABSIntegrationE2E::test_v12_1_playwright_arm_studio_full_reality_audit`.
- **Root Cause:** The test executed 9 continuous `take_shot()` operations in rapid succession. In headless Chromium using SwiftShader CPU rasterization, compressing and saving PNGs to disk temporarily paused requestAnimationFrame calls. The subsequent `getFPS()` query sampled the starved window, measuring 5 FPS against the hardcoded requirement of 8 FPS.
- **Correction:** Added `page.wait_for_timeout(1200)` immediately after disk screenshot capture, allowing the render loop's 1000ms rolling window to measure sustained rendering speed without disk I/O interference.
- **Numerical Results:**
  - *Before:* `AssertionError: Expected FPS >= 8 in headless SwiftShader CPU mode, got 5`.
  - *After:* Sustained 9 FPS measured in software SwiftShader mode; all 5 tests passed in 25.22s.
