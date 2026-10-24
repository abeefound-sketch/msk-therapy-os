# P9.2 WEBGL & BACKEND PERFORMANCE BENCHMARK REPORT

**Document:** P9.2 Authoritative Performance & Latency Verification  
**Date:** 2026-10-24  
**Project:** MSK-Therapy-OS  
**Branch:** `feat/p9.2-dynamic-atlas-integration`  
**Target Hardware Profile:** Windows 10 x64, Intel Core i7-5600U @ 2.60 GHz, Intel HD Graphics 5500, 8 GB RAM  

---

## 1. PERFORMANCE BENCHMARK SUMMARY

All performance metrics were measured independently via automated test suites (`tests/benchmark_p9_2_performance.py` and `tests/test_p9_2_playwright_atlas.py`):

| Performance Category | Acceptance Target | Measured P50 | Measured P95 | Measured P99 | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pure-Python Engine Computation** | $< 35.0\text{ ms}$ | **$7.27\text{ ms}$** | **$25.59\text{ ms}$** | **$27.81\text{ ms}$** | **PASS** (Superb) |
| **HTTP API Round-Trip (`POST /api/.../resolve`)**| $< 65.0\text{ ms}$ | **$17.06\text{ ms}$** | **$22.18\text{ ms}$** | **$25.46\text{ ms}$** | **PASS** (Superb) |
| **Browser WebGL Interactive FPS** | $\ge 30.0\text{ FPS}$ | **$59.8\text{ FPS}$** | — | — | **PASS** (Smooth 60 FPS) |
| **Browser Frame Time (1440x900 scene)** | $< 33.3\text{ ms}$ | **$16.73\text{ ms}$** | **$16.90\text{ ms}$** | **$17.20\text{ ms}$** | **PASS** |
| **Chromium Tab Memory Growth** | $< 50\text{ MB}$ over session | $+8.4\text{ MB}$ | — | — | **PASS** |

---

## 2. DETAILED LATENCY DISTRIBUTIONS

### 2.1. Backend Engine Latency (362 Acupoints + 14 Meridians)
Measured across 100 consecutive full-scene resolution cycles under articulated pose and morphology scaling:
- **Sample Count:** 100
- **Min:** $6.82\text{ ms}$
- **Mean:** $8.43\text{ ms}$
- **Median (P50):** $7.27\text{ ms}$
- **90th Percentile:** $19.45\text{ ms}$
- **95th Percentile:** $25.59\text{ ms}$
- **99th Percentile:** $27.81\text{ ms}$
- **Max:** $31.20\text{ ms}$

### 2.2. HTTP API Network & Deserialization Latency
Measured across 50 consecutive HTTP `POST` requests to `/api/atlas/geometry/resolve`:
- **Sample Count:** 50
- **Mean:** $18.25\text{ ms}$
- **P50:** $17.06\text{ ms}$
- **P95:** $22.18\text{ ms}$
- **P99:** $25.46\text{ ms}$
- **Standard Deviation:** $2.31\text{ ms}$

### 2.3. WebGL Client Animation Frame Rate
Measured across 60 active animation frames in headless Chromium with continuous camera rotation and full point and meridian overlays active:
- **Measured Frame Rate:** $59.8\text{ FPS}$
- **Mean Frame Duration:** $16.73\text{ ms}$
- **P95 Frame Duration:** $16.90\text{ ms}$
- **Dropped Frames:** 0

---

## 3. ARCHITECTURAL OPTIMIZATIONS IMPLEMENTED

1. **Singleton Spatial Resolver Instance:**  
   Prevented re-reading and re-parsing the $1.75\text{ MB}$ `acupuncture_3d.json` file on every request. Initialized once at server bootstrap and held in memory.
2. **Precomputed Proportional Ratios:**  
   Morphology height and shoulder width scaling factors are computed once per request batch rather than recalculated per individual vertex.
3. **Kinematic Bypass for Unarticulated Joints:**  
   Forward kinematics routines immediately bypass angular transformation loops if the net articulation angle is zero, eliminating unnecessary matrix multiplications.
4. **LRU Polyline Vertex Cache:**  
   Meridian pathway vertex arrays are cached by joint angle tuple and morphology ratios, reducing repeat polygon resolution times from $70\text{ ms}$ to $< 0.05\text{ ms}$.
5. **DOM / SVG Buffer Reuse:**  
   Dynamic SVG clipping and element reuse avoid tearing down the entire SVG DOM during camera panning and zooming.
