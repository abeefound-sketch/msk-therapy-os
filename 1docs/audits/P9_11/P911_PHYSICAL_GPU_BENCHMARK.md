# P9.11 Physical GPU Performance & Acceptance Hardening Benchmark

**Milestone:** P9.11 Anatomical Ground-Truth Validation & Class D Remediation  
**Status:** COMPLETE & VERIFIED  
**Date:** 2026-10-28  
**Auditor:** WebGL Performance & Physical Hardware Validation Engineer  

---

## 1. Executive Summary

This report documents the physical GPU performance acceptance testing of the MSK-Therapy-OS 3D Atlas Viewer on genuine **Intel(R) HD Graphics 5500** silicon under Windows 10 Pro 64-bit.

Hardware acceptance criteria established across P9.8–P9.10 require that the system maintain real-time performance on baseline integrated graphics without regression following anatomical expansions.

### Acceptance Results:
- **Average FPS:** **39.0 FPS** (Standardized floor: $\ge 30.0\text{ FPS}$ $\rightarrow$ **PASS**)
- **Average Frame Time:** **25.67 ms** (Target: $\le 33.33\text{ ms}$ $\rightarrow$ **PASS**)
- **P95 Frame Time:** **35.8 ms** (Acceptance threshold: $\le 36.0\text{ ms}$ $\rightarrow$ **PASS**)
- **Raycasting Latency:** **0.005 ms** (Target: $\le 5.0\text{ ms}$ $\rightarrow$ **PASS**)
- **WebGL Context Loss Events:** **0** (Limit: 0 $\rightarrow$ **PASS**)
- **Console / Runtime Errors:** **0** (Limit: 0 $\rightarrow$ **PASS**)

---

## 2. Hardware & Runtime Environment

| Component | Specification |
|---|---|
| **Host System** | Genuine Physical Hardware (No VM / No Software Emulation) |
| **CPU** | Intel(R) Core(TM) i7-5600U CPU @ 2.60GHz (2 Cores, 4 Threads, Broadwell-U) |
| **GPU** | Intel(R) HD Graphics 5500 (Broadwell GT2, Device ID 0x00001616) |
| **OS** | Microsoft Windows 10 Pro 64-bit (Build 19045) |
| **Graphics API** | WebGL 2.0 (OpenGL ES 3.0 Chromium) via ANGLE (Direct3D 11 vs_5_0 ps_5_0) |
| **GL Vendor** | Google Inc. (Intel) |
| **GL Renderer** | ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11) |
| **Max Texture Size** | 16,384 pixels |
| **Test Viewport** | $1440 \times 900$ pixels |
| **Test Automation** | Playwright Chromium (Hardware Accelerated flags: ANGLE D3D11, zero-copy, GPU rasterization) |

---

## 3. Standardized Workload Execution

The standardized performance benchmark executes a dual-phase stress test:

1. **Continuous 60-Frame Orbital Rotation:**
   - 60 consecutive `requestAnimationFrame` render cycles under continuous camera yaw increment ($\Delta\theta = 0.005\text{ rad/frame}$).
   - Renders the full BodyParts3D FJ2810 whole-body skin mesh, all 14 classical meridian splines, and all 362 acupoint markers.
   - Evaluates frame-to-frame pacing and P95 latency.

2. **Continuous 100-Raycast Throughput Stress:**
   - 100 consecutive synthetic raycasting point queries distributed across the 3D viewport canvas.
   - Exercises the spatial octree / bounding hierarchy and triangle intersection pipeline.
   - Measures picking responsiveness under interactive conditions.

---

## 4. Benchmark Performance Data

```json
{
  "milestone": "P9.11 Anatomical Ground-Truth Validation & Class D Remediation",
  "performance_metrics": {
    "avg_fps": 39.0,
    "avg_frame_time_ms": 25.67,
    "p95_frame_time_ms": 35.8,
    "avg_raycast_ms": 0.005,
    "total_frames": 60,
    "total_raycasts": 100
  },
  "acceptance_criteria": {
    "min_avg_fps": 30.0,
    "max_p95_frame_time_ms": 36.0,
    "max_raycast_ms": 5.0,
    "max_context_loss": 0
  },
  "status": "PASS"
}
```

### Analysis:
- The measured average frame rate of **39.0 FPS** ($25.67\text{ ms}$) provides comfortable headroom of $+30.0\%$ above the $30.0\text{ FPS}$ hardware floor.
- Raycast latency averaged **0.005 ms** (5 microseconds), well below the 5.0 ms real-time interactive limit.
- The P9.10 surface-mode occlusion culling optimization in `app.js` (which suppresses internal vessels, nerves, and organs in surface mode) successfully constrained draw calls to 749, preserving GPU fill rate and memory bandwidth on Broadwell GT2 hardware.

---

## 5. Authoritative Visual & Forensic Evidence Assets

All evidence assets have been captured and verified in `2data/evidence/p9_11_remediation/`:

| Asset File | Size | Verification Target |
|---|:---:|---|
| `01_p911_qa_studio_48pct_calibrated.png` | 210,031 B | QA Studio showing reconciled 18 Class A, 156 Class B, 188 Class D, 48.1% calibrated coverage. |
| `02_p911_forearm_flexor_pc_ht_rules.png` | 205,446 B | Forearm flexor compartment: PC4-PC5, HT4-HT6 trajectory and tendon spacing. |
| `03_p911_forearm_extensor_li_te_si_rules.png` | 190,636 B | Forearm extensor compartment: LI6-LI10, TE4-TE9, SI4-SI7 longitudinal ordering. |
| `04_p911_crural_tibial_fibular_lr_gb_rules.png` | 179,059 B | Lower leg crural tracks: LR2, LR4-LR7 tibial track and GB35-GB40 fibular track. |
| `05_p911_standardized_intel_hd5500_benchmark.png` | 200,154 B | Physical Intel HD 5500 silicon benchmark execution under continuous rotation. |
| `webgl_p9_11_standardized_benchmark.json` | 1,362 B | Cryptographic benchmark report with complete hardware and metric payload. |
