# P9.8 Physical WebGL Hardware Acceptance Report

**Document ID:** `P98_PHYSICAL_GPU_ACCEPTANCE.md`  
**Milestone:** P9.8 Anatomical Ground Truth & Evidence Integrity Hardening  
**Status:** APPROVED | PHYSICAL HARDWARE ACCEPTED  
**Date:** 2026-10-28  
**Reference Silicon Target:** Intel(R) HD Graphics 5500 (Broadwell GT2)  

---

## 1. Hardware Identification & Host Environment

The benchmark was executed on the physical host hardware:
- **Processor:** Intel(R) Core(TM) i7-5600U CPU @ 2.60GHz (Broadwell-U, 2 cores / 4 threads)
- **Integrated GPU:** Intel(R) HD Graphics 5500 (PCI ID `0x00001616`)
- **Driver Version:** `20.19.15.5126` (WDDM 2.0)
- **Video Memory:** 1024 MB dedicated / shared system memory
- **System Memory:** 8.00 GB DDR3
- **Operating System:** Microsoft Windows 10 Pro 64-bit (Build 19045)
- **Browser Runtime:** Chromium (Playwright headless) with `--use-gl=angle --use-angle=d3d11 --ignore-gpu-blocklist`
- **WebGL Context:** WebGL 2.0 (OpenGL ES 3.0 Chromium)
- **Unmasked Renderer:** `ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11)`

---

## 2. Benchmark Performance Metrics

Automated test `tests/test_p9_8_playwright_integrity.py` executed the full 3D interactive atlas scene with all 14 classical meridians, 362 acupoint markers, skin mesh rasterization, and QA Studio instrumentation active.

| Performance Metric | Acceptance Target | Measured Physical Value | Margin / Assessment | Evaluation |
|---|---|---|---|:---:|
| **Sustained Render Rate (FPS)** | >= 30.0 FPS | **30.7 FPS** | +0.7 FPS above minimum | **PASS** |
| **Frame Time (p50 Median)** | <= 33.3 ms | **32.0 ms** | Smooth frame pacing | **PASS** |
| **Frame Time (p95 Upper Bound)** | <= 66.7 ms | **46.2 ms** | Well within acceptable jitter | **PASS** |
| **Raycast Picking Latency** | <= 50.0 ms | **< 1.0 ms** | Instantaneous point query | **PASS** |
| **WebGL Context Restore Time** | <= 200.0 ms | **55.5 ms** | Clean state recovery | **PASS** |
| **Max Texture Size** | >= 8192 | **16384** | High-resolution support | **PASS** |
| **Max Viewport Dimensions** | >= 1440 x 900 | **16384 x 16384** | Fully supported | **PASS** |

---

## 3. Visual Evidence Captures

Five high-resolution visual evidence assets were generated and saved in `2data/evidence/p9_8_integrity/`:
1. `01_p98_qa_studio_dynamic_coverage_118_class_b.png`: Full QA Studio panel displaying live dynamic metrics (18 Class A, 118 Class B, 0 Class C, 226 Class D, 37.6% Calibrated).
2. `02_p98_spleen_circular_reference_quarantined_class_d.png`: High-angle close-up of medial foot showing SP2, SP3, SP4, SP5 rendered fail-closed as Class D.
3. `03_p98_scapular_interscapular_paraspinal_calibrated.png`: Posterior back view demonstrating Bladder inner column (33.75 mm) and outer column (67.50 mm) tracking the medial scapular border at 22.5 mm/cun.
4. `04_p98_conception_vessel_midline_invariance.png`: Anterior frontal view demonstrating zero lateral deviation along the sternum and linea alba (X = 0.000 mm).
5. `05_p98_intel_hd5500_physical_hardware_benchmark.png`: Perspective rendering of full 3D body atlas with active GPU hardware acceleration.

---

## 4. Hardware Acceptance Verdict

**VERDICT: PASS | PHYSICAL INTEL HD 5500 SILICON ACCEPTED**  
The MSK-Therapy-OS 3D WebGL Atlas demonstrates sustained performance above 30 FPS on the reference physical Intel HD 5500 GPU, ensuring accessible clinical visualization on standard clinic PC hardware without discrete GPU requirements.
