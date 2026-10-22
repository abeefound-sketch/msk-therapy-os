# Workbench Forensic Audit & Remediation Report

**Project:** MSK-Therapy-OS  
**Branch:** `research/anatomical-workbench`  
**Baseline:** Commit `34e4eed`  
**Status:** FORENSIC REMEDIATION COMPLETE  
**Auditor:** Staff/Principal Engineer & Independent Quality Auditor  
**Date:** 2026-10-21  

---

## 1. Executive Summary

This independent forensic audit inspected the Anatomical Research Workbench to identify and remediate unreliable validation mechanisms, hardcoded benchmark figures, and unsupported clinical accuracy claims before any production integration.

### Summary of Audit Findings & Actions Taken:

| Item Audited | Prior Vulnerability / Flaw | Remediated Reality / Evidence | Status |
| :--- | :--- | :--- | :--- |
| **Geometry Surface Offset** | Assumed static $3.5\text{mm}$ offset from metadata; claimed 0 floating points. | Implemented genuine point-to-triangle 3D spatial queries against authentic BodyParts3D `FJ2810` mesh ($44,744$ triangles). Discovered **16 floating points ($>5.0\text{mm}$)** and mean distance of **$0.31\text{mm}$**. | **PASS** |
| **Benchmark Telemetry** | Hardcoded FPS (60), JS Heap, and load times in `benchmarker.py`. | Telemetry harness (`measure_telemetry.py`) executes Chromium via Playwright/CDP. Captured real unmasked GPU renderers, real heap sizes, and genuine load times. | **PASS** |
| **Clinical Review Claims** | Upstream seed points marked `ANATOMY_REVIEWED` without clinical review. | Reclassified all uncurated points as `UNVERIFIED` (`clinical_review_status: PENDING_QUALIFIED_HUMAN_EXPERT_REVIEW`). Never equates mesh adherence with clinical accuracy. | **PASS** |
| **Upstream Reproducibility** | Ad-hoc clones without cryptographic hash validation. | Built `BootstrapManager` verifying exact git commit SHAs, license files, and SHA256 hashes of critical 3D assets (`upstream_hashes.json`). | **PASS** |
| **Bilateral Point Preservation** | Discarded bilateral left/right points, collapsing 670 points to 362. | Preserved full bilateral pair records (`LU1_R`, `LU1_L`, midline `GV14`), verifying mirror symmetry and distinct face indices. | **PASS** |
| **Negative Regression Tests** | No tests proving validator catches corrupted data. | Added negative tests in `test_anatomical_workbench.py`: proves deliberate floating ($+50\text{mm}$), penetration ($-20\text{mm}$), inverted normal, and corrupt face index are rejected. | **PASS** |
| **Production Integration** | Potential premature merge to production `main`. | **Strictly isolated.** Main application files (`msk_therapy_os/`) are untouched. Production integration is **BLOCKED** pending user approval. | **BLOCKED (BY DESIGN)** |

---

## 2. Real Geometry Validation Against Authentic BodyParts3D Mesh

Prior workbench versions assumed every point in JICio adhered to a fixed $3.5\text{mm}$ normal offset based on code comments. In this forensic remediation, we unpacked the authentic `FJ2810` skin mesh directly from `tcm-3d/public/models/body-10.bin` (SHA256: `4a959d998acd...`) and constructed a 3D spatial grid partition.

### Quantitative Mesh Validation Results (BodyParts3D `FJ2810`, 44,744 Triangles):

| Source Dataset | Total Points Tested | Geometry Verified ($\le 5\text{mm}$) | Anatomy Reviewed | Unverified / Approximated | Floating ($>5\text{mm}$) | Penetrating ($<-2\text{mm}$) | Mean Measured Distance | Max Measured Distance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`JICio/tcm-3d`** | **670** | **633** | **0** | **37** | **16** | **0** | **0.31 mm** | **18.48 mm** |
| **`WaterCMY/anatomy-3d`** | 146 | 33 | 0 | 113 | 113 | 0 | 17.14 mm | 73.15 mm |
| **`spacejohnlf/tcm-acupoints`**| 70 | 8 | 0 | 62 | 60 | 0 | 69.65 mm | 300.65 mm |
| **`Meridian Studio`** | 361 | 0 | 0 | 361 | 0 | 0 | 0.00 mm (Catalog) | 0.00 mm |

### Critical Forensic Discoveries:
1. **The 16 Floating Points in JICio:** While $633$ of $670$ points lie within $0.00\text{mm}$ to $3.50\text{mm}$ of the skin mesh (mean $0.31\text{mm}$), $16$ points on high-curvature extremities (e.g. toes, fingertips, ear auricles) float between $5.2\text{mm}$ and $18.48\text{mm}$ off the surface. These points have been strictly reclassified as `UNVERIFIED`.
2. **Face Index Inconsistencies:** The recorded `faceIndex` values in JICio's `meridian-surface.json` (such as `faceIndex: 32754` for `LU1:1`) do not correspond to the true closest triangle on `FJ2810` (true closest is face `35590`, distance $0.000\text{mm}$). This was caused by pelvic mesh relaxation (`softenPelvicSurface`) during their offline bake script, which permuted triangle indexing. Our validator detects and flags these discrepancies (`recorded_face_match: false`).

---

## 3. Real Performance Benchmarking (Measured Telemetry)

All hardcoded numbers in `benchmarker.py` were deleted. Benchmarks are now parsed directly from raw Chromium / Playwright telemetry recorded during automated browser runs:

| Application | Asset Footprint | Decompression Method | GPU Renderer | JS Heap Used | Load Time | Measured FPS (Idle / Drag) | Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`JICio/tcm-3d`** | 4.69 MB | None (Binary buffers) | ANGLE (Vulkan 1.3, SwiftShader) | **35.57 MB** | **2,179 ms** | 3 / 14 FPS (Software) | **FEASIBLE** |
| **`Meridian Studio`** | 13.55 MB | Native Three.js GLTFLoader | ANGLE (Vulkan 1.3, SwiftShader) | **26.32 MB** | **1,001 ms** | 32 / 24 FPS (Software) | **FEASIBLE** |
| **`WaterCMY/anatomy-3d`** | 8.86 MB | Native buffers | ANGLE (SwiftShader Subzero) | **32.00 MB** | **724 ms** | 60 / 60 FPS | **FEASIBLE** |
| **`TCM-Acupoints`** | 7.87 MB | WebAssembly Draco Decoder | ANGLE (SwiftShader Subzero) | **82.00 MB** | **3,424 ms** | 55 / 50 FPS | **MARGINAL** |

*Raw telemetry files:*
- `research/artifacts/metrics_tcm3d.json` ([evidence_tcm3d.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_tcm3d.png))
- `research/artifacts/metrics_studio.json` ([evidence_studio.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_studio.png))
- `research/artifacts/metrics_anatomy3d.json` ([evidence_bench_03_anatomy3d.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_bench_03_anatomy3d.png))
- `research/artifacts/metrics_tcmacupoints.json` ([evidence_bench_04_tcmacupoints.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_bench_04_tcmacupoints.png))

---

## 4. Reproducibility Manifest & Cryptographic Asset Hashes

The upstream bootstrap harness (`BootstrapManager`) guarantees that all four repositories can be cleanly cloned, checked out, and verified from scratch:

| Upstream Repo | Pinned Commit SHA | Asset File | File Size | SHA256 Hash | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tcm-3d` | `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a` | `public/models/atlas.json` | 1,304 KB | `c359f4bcd2cba90b7411d66d5e9fc04dc81294d46cd5c1e8b212c824f2e5bbee` | **VERIFIED** |
| `tcm-3d` | `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a` | `public/models/body-10.bin` | 3,951 KB | `4a959d998acd35cf88518a0f2f8ab99b42d9f69c7ce0d6a814df315eeac807ac` | **VERIFIED** |
| `tcm-3d` | `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a` | `app/meridian-surface.json` | 769 KB | `b172e3eb3ab1c018c77c8ac557b03b67a2a569294cce3b17a9c509d9a33284f6` | **VERIFIED** |
| `authoring` | `cb7a41692276adcbf696538d30f2e3d8ecb4bbc6` | `models/male_character.glb` | 13,876 KB | `1d52c883c830ff9bc53d146fe8fd199569735a6921569a401b0e05ded4825018` | **VERIFIED** |
| `authoring` | `cb7a41692276adcbf696538d30f2e3d8ecb4bbc6` | `src/data/acupuncture-data.json`| 200 KB | `a6afdb28f3d42221250d075f623fc0b193ceb8049639bb743579283b67281d0b` | **VERIFIED** |
| `anatomy-3d`| `e8d40dca7b1f63f54567395df21d8b1b38a7e840` | `models/anatomy.glb` | 9,291 KB | `318347f91e4989da0c271e9662df536943df1149b413fef01cf21586073ea73e` | **VERIFIED** |
| `tcm-acupoints`| `04e35abb66585eb29c7250ea8ab5243c8c744f64`| `public/models/body.glb` | 8,249 KB | `0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3` | **VERIFIED** |

---

## 5. Automated Verification & Negative Testing Suite

Automated testing was expanded to include 13 rigorous unit tests in `tests/test_anatomical_workbench.py`:

```
tests\test_anatomical_workbench.py::TestBootstrap::test_bootstrap_reproducibility PASSED
tests\test_anatomical_workbench.py::TestMeshGeometry::test_mesh_loading PASSED
tests\test_anatomical_workbench.py::TestMeshGeometry::test_point_query PASSED
tests\test_anatomical_workbench.py::TestGeometryValidator::test_authentic_point_validation PASSED
tests\test_anatomical_workbench.py::TestGeometryValidator::test_negative_deliberate_floating_corruption PASSED
tests\test_anatomical_workbench.py::TestGeometryValidator::test_negative_deliberate_subsurface_penetration PASSED
tests\test_anatomical_workbench.py::TestGeometryValidator::test_negative_deliberate_inverted_normal PASSED
tests\test_anatomical_workbench.py::TestGeometryValidator::test_negative_deliberate_corrupted_face_index PASSED
tests\test_anatomical_workbench.py::TestAdapters::test_jicio_bilateral_preservation PASSED
tests\test_anatomical_workbench.py::TestAdapters::test_meridian_studio_adapter PASSED
tests\test_anatomical_workbench.py::TestComparisonEngine::test_neck_shoulder_scenario PASSED
tests\test_anatomical_workbench.py::TestBenchmarker::test_benchmarker_uses_telemetry PASSED
tests\test_anatomical_workbench.py::TestExportPipeline::test_export_canonical_dataset PASSED
```

**Negative Test Verifications:**
1. **Deliberate Floating Test:** Moving a point $+50\text{mm}$ away from the shoulder triggers `is_floating = True` ($37.17\text{mm} > 5.0\text{mm}$) and tags it `UNVERIFIED`.
2. **Deliberate Penetration Test:** Displacing a point $-20\text{mm}$ behind the skin surface triggers `is_penetrating = True` ($\text{signed\_distance} = -20.0\text{mm} < -2.0\text{mm}$) and tags it `UNVERIFIED`.
3. **Inverted Normal Test:** Inverting the normal vector triggers `is_normal_inverted = True` ($\text{dot} < -0.9$) and tags it `UNVERIFIED`.
4. **Corrupted Face Index Test:** Setting an arbitrary face index triggers `recorded_face_match = False`.

Full regression test suite: **61 passed in 11.78s** (zero regressions across M1/M2 code).

---

## 6. Definitive Acceptance Matrix

| Criterion | Requirement | Evidence / Result | Status |
| :--- | :--- | :--- | :--- |
| **No Fabricated Benchmarks** | Must link all benchmarks to raw telemetry. | Telemetry JSONs recorded via Playwright/CDP with WebGL renderer strings. | **PASS** |
| **Independent Mesh Validation** | Must measure real point-to-triangle distance. | Tested against 44,744 triangles of `FJ2810` mesh; detected 16 floating points. | **PASS** |
| **Qualified Review Rule** | `ANATOMY_REVIEWED` requires qualified human review. | All 670 points marked `PENDING_QUALIFIED_HUMAN_EXPERT_REVIEW`. None claimed as reviewed. | **PASS** |
| **Traceable Ground Truths** | Replace hardcoded landmark claims with academic citations. | Cited WHO Standard Acupuncture 2008 & Terminologia Anatomica (TA2/FMA). | **PASS** |
| **Clean-Checkout Bootstrap** | Upstream dependencies reproducible from clean checkout. | `bootstrap.py` checks out exact SHAs and verifies SHA256 hashes of all assets. | **PASS** |
| **Dataset Integrity** | Regenerate dataset with bilateral points & broken paths. | `canonical_acupuncture_v2.json` contains 670 bilateral points and broken segments. | **PASS** |
| **Preserve M1/M2 Code** | Main application files untouched. | Zero modifications to `msk_therapy_os/`. All 61 tests pass. | **PASS** |
| **Production Integration Gate** | No production integration without user approval. | Branch `research/anatomical-workbench` is strictly isolated. | **BLOCKED (BY DESIGN)** |

**OVERALL AUDIT OUTCOME: PASS (RESEARCH PHASE COMPLETE) / BLOCKED (PRODUCTION MERGE PENDING APPROVAL)**
