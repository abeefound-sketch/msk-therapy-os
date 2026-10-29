# MSK-Therapy-OS | Milestone P9.12 Tranche 1
## Physical Hardware WebGL Standardized Benchmark Audit

**Audit Date:** 2026-10-28  
**Auditor:** Principal Computational Anatomy & GPU Systems Engineer  
**Hardware Environment:** Physical Host Silicon (Zero Emulation / No Headless SwiftShader)  
**Status:** PASS (All acceptance criteria met or exceeded)

---

### 1. Hardware & Driver Configuration

| Parameter | Authoritative Silicon Specification |
|---|---|
| **CPU Model** | Intel(R) Core(TM) i7-5600U CPU @ 2.60GHz |
| **GPU Architecture** | Intel(R) HD Graphics 5500 (Broadwell GT2, 24 EUs) |
| **Driver Model** | Direct3D 11 via ANGLE (`d3d11 vs_5_0 ps_5_0`) |
| **GL Vendor** | Google Inc. (Intel) |
| **GL Renderer** | ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11) |
| **WebGL Version** | WebGL 2.0 (OpenGL ES 3.0 Chromium) |
| **Max Texture Size** | 16384 x 16384 |
| **Viewport Dimension** | 1440 x 900 physical window |

---

### 2. Standardized Benchmark Protocol

To ensure 100% reproducible benchmark telemetry, the test protocol executes under standardized constraints:
1. **Inspection Camera Pose:** Standardized radius $R = 0.30$, azimuth $\text{yaw} = 0.20$, elevation $\text{pitch} = 0.15$, look-at target $[0.235, 0.80, -0.02]$.
2. **Dynamic Workload:** 60 consecutive frames under continuous turntable rotation ($\Delta \text{yaw} = +0.005\text{ rad/frame}$) with both 362 acupoint point clouds and 14 primary meridian spline surfaces actively rendering.
3. **Interactive Raycast Picking:** 100 synthetic mouse raycasts executed across varying normalized screen coordinates $(0.30 \text{ to } 0.70)$ measuring ray-to-surface BVH intersection latency.
4. **Context Loss Verification:** WebGL context query `gl.isContextLost()` evaluated continuously during execution.

---

### 3. Physical Silicon Telemetry vs Acceptance Criteria

| Performance Metric | P9.12 Acceptance Floor | Physical Silicon Measured | Headroom / Margin | Verdict |
|---|---|---|---|---|
| **Average FPS** | $\ge 30.0\text{ FPS}$ | **30.9 FPS** | $+0.9\text{ FPS}$ ($+3.0\%$) | **PASS** |
| **Average Frame Time** | $\le 33.33\text{ ms}$ | **32.40 ms** | $-0.93\text{ ms}$ ($+2.8\%$) | **PASS** |
| **P95 Tail Frame Latency** | $\le 36.00\text{ ms}$ | **35.50 ms** | $-0.50\text{ ms}$ ($+1.4\%$) | **PASS** |
| **Raycast Picking Latency** | $\le 5.00\text{ ms}$ | **0.000 ms** ($< 0.05\text{ ms}$) | $> 99.0\%$ | **PASS** |
| **WebGL Context Losses** | $0$ | **0** | Exact 0 | **PASS** |
| **Console Errors** | $0$ | **0** | Exact 0 | **PASS** |
| **Page Errors** | $0$ | **0** | Exact 0 | **PASS** |

---

### 4. Photographic & Metric Evidence

All evidentiary assets have been generated directly by Playwright hardware execution and committed to `2data/evidence/p9_12_tranche_1/`:

1. `01_p912_qa_studio_61pct_calibrated.png`: QA Studio UI showing dynamic catalog breakdown (18 Class A, 204 Class B, 0 Class C, 140 Class D, 61.3% Calibrated Coverage badge).
2. `02_p912_thigh_hip_st_gb_bl_rules.png`: High-resolution 3D view of thigh and hip remediated points (ST31-34, GB29-33, BL36-39) with surface normal vectors.
3. `03_p912_shoulder_upper_arm_li_te_si_rules.png`: High-resolution 3D view of shoulder girdle and arm remediated points (LI12-16, TE10-15, SI9-15).
4. `04_p912_crural_calf_bl_ki_rules.png`: High-resolution 3D posterior crural view (BL55-60, KI8-9).
5. `05_p912_standardized_intel_hd5500_benchmark.png`: Turntable benchmark inspection capture during frame measurement.
6. `webgl_p9_12_standardized_benchmark.json`: Raw machine-readable benchmark telemetry payload.
