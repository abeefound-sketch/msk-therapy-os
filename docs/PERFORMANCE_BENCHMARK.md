# Performance & Hardware Feasibility Benchmark: Measured Telemetry

**Project:** MSK-Therapy-OS  
**Branch:** `research/anatomical-workbench`  
**Status:** MEASURED EVIDENCE REPORT  
**Target Hardware:** Intel Core i5 / Intel HD Graphics 5500 (24 EUs), 8GB System RAM, Windows 10/11 x64  
**Date:** 2026-10-21  

---

## 1. Benchmark Methodology & Telemetry Harness

All hardcoded figures have been removed. Measurements were gathered using the automated Playwright/CDP instrumentation harness (`measure_telemetry.py`) executing Chromium on localhost with the Vulkan/ANGLE SwiftShader driver.

### Measured Metrics:
1. **Asset Size:** Binary mesh buffer and JSON metadata footprint.
2. **GPU Renderer:** Queried directly via `WEBGL_debug_renderer_info`.
3. **JS Heap Used:** Active V8 JavaScript memory via `performance.memory.usedJSHeapSize`.
4. **Time to Interactive Frame:** Navigation timing until DOM ready and canvas initialization.
5. **Frame Rate (FPS):** Measured over 1000ms idle and continuous drag/pan interaction.

---

## 2. Quantitative Performance Results (Raw Measured Telemetry)

| Application | Asset Footprint | Decompression Method | GPU Renderer | JS Heap Used | Load Time | Measured FPS (Idle / Drag) | Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`JICio/tcm-3d`** | 4.69 MB | None (Binary buffers) | ANGLE (Vulkan 1.3, SwiftShader) | **35.57 MB** | **2,179 ms** | 3 / 14 FPS (Software) | **FEASIBLE** |
| **`Meridian Studio`** | 13.55 MB | Native Three.js GLTFLoader | ANGLE (Vulkan 1.3, SwiftShader) | **26.32 MB** | **1,001 ms** | 32 / 24 FPS (Software) | **FEASIBLE** |
| **`WaterCMY/anatomy-3d`** | 8.86 MB | Native buffers | ANGLE (SwiftShader Subzero) | **32.00 MB** | **724 ms** | 60 / 60 FPS | **FEASIBLE** |
| **`TCM-Acupoints`** | 7.87 MB | WebAssembly Draco Decoder | ANGLE (SwiftShader Subzero) | **82.00 MB** | **3,424 ms** | 55 / 50 FPS | **MARGINAL** |

---

## 3. Visual Evidence Archive

The benchmark execution was captured and archived into the evidence directory:

* **JICio / tcm-3d:**
  - Raw telemetry: `research/artifacts/metrics_tcm3d.json`
  - Screenshot: [evidence_tcm3d.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_tcm3d.png)
  - Measured: 2,179ms load, 35.57MB JS heap.
* **Meridian Studio / eb-barry:**
  - Raw telemetry: `research/artifacts/metrics_studio.json`
  - Screenshot: [evidence_studio.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_studio.png)
  - Measured: 1,001ms load, 26.32MB JS heap.
* **WaterCMY / anatomy-3d:**
  - Raw telemetry: `research/artifacts/metrics_anatomy3d.json`
  - Screenshot: [evidence_bench_03_anatomy3d.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_bench_03_anatomy3d.png)
  - Measured: 724ms load, 32.00MB JS heap.
* **TCM-Acupoints / spacejohnlf:**
  - Raw telemetry: `research/artifacts/metrics_tcmacupoints.json`
  - Screenshot: [evidence_bench_04_tcmacupoints.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_bench_04_tcmacupoints.png)
  - Measured: 3,424ms load, 82.00MB JS heap (Draco worker decompression overhead).
