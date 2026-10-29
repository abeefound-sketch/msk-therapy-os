# P9.9 WebGL Hardware Regression Report

## 1. Test Environment & Physical Silicon Details
- **Test Date:** 2026-10-28T04:01:56Z
- **Operating System:** Microsoft Windows 10 Pro 64-bit (Build 19045)
- **CPU:** Intel(R) Core(TM) i7-5600U CPU @ 2.60GHz (2 cores, 4 logical processors)
- **Physical GPU:** Intel(R) HD Graphics 5500 (Broadwell GT2 integrated GPU)
- **Driver Architecture:** Direct3D 11 via ANGLE (`ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11)`)
- **WebGL Context:** WebGL 2.0 (OpenGL ES 3.0 Chromium)
- **Max Texture Size:** 16,384 x 16,384 pixels
- **Browser Automation:** Playwright Chromium 1440x900 viewport, hardware acceleration flags enabled.

---

## 2. Performance Benchmark Metrics Comparison

| Performance Metric | P9.8 Baseline (Reported) | P9.9 Benchmark (Actual Measured) | Target Threshold | Status |
|---|---:|---:|---:|:---:|
| **Average Frame Rate (FPS)** | $30.7\text{ FPS}$ | **$40.9\text{ FPS}$** | $\ge 25.0\text{ FPS}$ | **PASS** |
| **Average Frame Time** | $32.57\text{ ms}$ | **$24.46\text{ ms}$** | $\le 40.0\text{ ms}$ | **PASS** |
| **95th Percentile Frame Time** | $37.20\text{ ms}$ | **$28.70\text{ ms}$** | $\le 45.0\text{ ms}$ | **PASS** |
| **Raycast Latency** | $0.005\text{ ms}$ | **$0.003\text{ ms}$** | $\le 5.0\text{ ms}$ | **PASS** |
| **Total Frames Sampled** | 60 | 60 | $\ge 60$ | **PASS** |
| **Synthetic Raycasts Executed**| 100 | 100 | $\ge 50$ | **PASS** |
| **WebGL Context Loss** | None (0) | None (0) | 0 | **PASS** |
| **Console Errors** | 0 | 0 | 0 | **PASS** |
| **Page Errors** | 0 | 0 | 0 | **PASS** |

---

## 3. Physical Hardware Visual Verification
Visual proof captured during live execution on Intel HD 5500 hardware:
- `01_p99_qa_studio_coverage_126_class_b.png`: Live coverage counters rendering 18 Class A, 126 Class B, 0 Class C, 218 Class D, 39.8% calibrated coverage.
- `02_p99_foot_medial_dequarantined_sp2_sp5.png`: Medial foot camera close-up displaying de-quarantined SP2, SP3, SP4, SP5 accurately aligned.
- `03_p99_kidney_distal_foot_plantar_ki1_ki6.png`: Distal foot and ankle view confirming downward-pointing plantar normal on KI1 and accurate medial malleolus / calcaneal positioning for KI2-KI6.
- `04_p99_wrist_palmar_crease_lu9_ht7_pc7.png`: Palmar wrist view showing LU9, PC7, HT7 aligned along the transverse distal wrist crease.
- `05_p99_webgl_hardware_benchmark_intel_hd5500.png`: Physical Intel HD 5500 hardware execution confirmation.

---

## 4. Hardware Stability & Robustness Assessment
During intense camera rotation and synthetic raycast stress tests (100 sequential raycasts across the canvas viewport):
- Zero stutter or dropped frame bursts observed.
- Memory consumption remained stable throughout the 60-frame loop.
- No WebGL context lost events occurred.
- The system achieves a stable 40.9 FPS on dual-core Broadwell Intel HD 5500 hardware, exceeding the 25 FPS minimum requirement by 63.6%.
