# MSK-Therapy-OS | Milestone P9.12 Tranche 2
## Deliverable 10: Physical GPU Performance & WebGL Benchmark Report

**Milestone:** P9.12 Tranche 2  
**Date:** 2026-10-28  
**Physical Hardware Target:** Intel(R) HD Graphics 5500 (Broadwell GT2 Silicon)  
**Backend Graphics API:** Direct3D 11 via Chromium ANGLE  
**Test Suite:** `tests/test_p9_12_t2_playwright_benchmark.py`  
**Telemetry File:** `2data/evidence/p9_12_tranche_2/webgl_p9_12_t2_standardized_benchmark.json`  
**Hardware Acceptance Status:** **PASS (All 4 Hardware Gates Satisfied)**

---

## 1. Hardware Environment Specification

```json
{
  "unmaskedVendor": "Google Inc. (Intel)",
  "unmaskedRenderer": "ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11)",
  "webglVersion": "WebGL 2.0 (OpenGL ES 3.0 Chromium)",
  "maxTextureSize": 16384,
  "maxRenderbufferSize": 16384,
  "maxViewportDims": [32767, 32767],
  "aliasedLineWidthRange": [1, 1]
}
```

---

## 2. Benchmark Workload & Execution Protocol

The benchmark executes an automated, standardized protocol:
1. **Model Loading:** Full BodyParts3D FJ2810 anatomical mesh with all 14 primary meridians active and 362 rendered points.
2. **Animation Loop:** 120 consecutive `requestAnimationFrame` cycles with continuous orbital yaw rotation (`yaw += 0.01` rad/frame).
3. **Raycast Workload:** 50 consecutive screen-space raycasting pick queries evaluated at viewport center $(X_{\text{mid}}, Y_{\text{mid}})$.
4. **Context Loss Monitoring:** Hardware event listener attached to `#viewport` monitoring for `webglcontextlost` events.

---

## 3. Quantitative Telemetry & Hardware Gate Verification

| Metric | Target / Gate | Physical Measured Result | Margin | Status |
|:---|:---|---:|---:|:---|
| **Average Framerate** | $\ge 30.0\text{ FPS}$ | **40.78 FPS** | $+10.78\text{ FPS}$ ($+35.9\%$) | **PASS** |
| **P95 Frame Time** | $\le 36.0\text{ ms}$ | **32.10 ms** | $-3.90\text{ ms}$ (Under threshold) | **PASS** |
| **Mean Frame Time** | $\le 33.3\text{ ms}$ | **24.52 ms** | $-8.78\text{ ms}$ (Smooth rendering) | **PASS** |
| **Raycast Pick Latency** | $\le 5.0\text{ ms}$ | **< 0.5 ms** | $-4.50\text{ ms}$ (Instantaneous pick) | **PASS** |
| **WebGL Context Losses** | Strictly 0 | **0** | Zero loss | **PASS** |

---

## 4. Visual Evidence Manifest

All 7 authoritative evidentiary screenshots and telemetry JSON were captured and verified in `2data/evidence/p9_12_tranche_2/`:

1. `01_p912_t2_cranial_gv_bl_alignment.png` (Cranial Superior-Posterior View)
2. `02_p912_t2_gb_temporal_auricular_topology.png` (GB Temporal Auricular Topology)
3. `03_p912_t2_facial_st_li_localization.png` (Facial ST & LI Localization)
4. `04_p912_t2_orbital_safety_boundaries.png` (Orbital Margin Safety Boundaries)
5. `05_p912_t2_cervical_si_te_st_transitions.png` (Cervical SI, TE, ST Transitions)
6. `06_p912_t2_qa_studio_76pct_calibrated.png` (Full QA Studio Dashboard with 76.5% Calibrated Coverage)
7. `07_p912_t2_standardized_intel_hd5500_benchmark.png` (Hardware Benchmark Telemetry & Final Frame)
8. `webgl_p9_12_t2_standardized_benchmark.json` (Structured JSON Telemetry)

---

## 5. Conclusion

The WebGL rendering pipeline demonstrates full hardware stability and exceeds the physical Intel HD Graphics 5500 performance floor without shader stutter or GPU context drops.
