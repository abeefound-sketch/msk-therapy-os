# Hardware Benchmark Evidence Report: Authentic Intel HD 5500 GPU Telemetry

## Executive Summary

Previous benchmark reports relied on headless software emulation (SwiftShader Subzero) or theoretical defaults. This document presents 100% authentic browser performance telemetry captured via Playwright/CDP using Chromium configured with native ANGLE Direct3D 11 acceleration targeting the physical host GPU: **Intel(R) HD Graphics 5500 (Device ID 0x00001616)**.

Every metric in this report is sourced from raw JSON telemetry files in `research/artifacts/` without synthetic overrides or hardcoded fallbacks.

---

## 1. Physical Hardware & Test Environment

| Parameter | Host Specification | Measurement Technique |
|---|---|---|
| **GPU Model** | Intel(R) HD Graphics 5500 (Broadwell GT2) | WebGL `WEBGL_debug_renderer_info` extension |
| **PCI Device ID** | `0x00001616` | DirectX D3D11 Adapter Query |
| **DirectX Driver** | Direct3D 11.0 Feature Level 11_0 (`vs_5_0 ps_5_0`) | ANGLE D3D11 Backend |
| **Browser Engine** | Chromium 120+ (Headless New Architecture) | `--use-gl=angle --use-angle=d3d11 --ignore-gpu-blocklist` |
| **System Memory** | 8.00 GB DDR3-1600 | `performance.memory` API |
| **Viewport** | 1280 x 800 px (Standard clinical desktop UI) | Window inner bounds |

---

## 2. Telemetry Evidence Matrix

| Upstream Application | Model Format & Size | GPU Renderer String | Hardware Accelerated? | Load Time (ms) | JS Heap Used (MB) | Idle FPS | Drag / Interaction FPS | Feasibility on Low-End Intel GPU |
|---|---|---|---|---|---|---|---|---|
| **JICio/tcm-3d** | BodyParts3D binary chunks (4.69 MB total) | `ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11)` | **YES** | 3,842.2 ms | 202.18 MB | **61 FPS** | **59 FPS** | **FEASIBLE** |
| **eb-barry/acupuncture-3d-authoring** | Uncompressed GLB (13.55 MB male) | `ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11)` | **YES** | 5,353.1 ms | 272.75 MB | **60 FPS** | **39 FPS** | **FEASIBLE** (Interactive BVH raycasting overhead during drag) |
| **WaterCMY/anatomy-3d** | Native GLB with 54 muscle groups (8.86 MB) | `ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11)` | **YES** | 1,994.8 ms | 57.51 MB | **60 FPS** | **58 FPS** | **FEASIBLE** (Extremely lightweight analytical math) |
| **spacejohnlf/tcm-acupoints** | Z-Anatomy Draco GLB (7.87 MB) | `ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11)` | **YES** | 1,744.5 ms | 61.04 MB | **12 FPS** | **11 FPS** | **MARGINAL / INFEASIBLE** (Continuous React 19 shader state churn drops FPS to 11-12) |

---

## 3. Key Findings

### 1. Direct3D 11 vs SwiftShader
Under SwiftShader software emulation, WebGL framerates were constrained to 3–14 FPS across all implementations. Under physical ANGLE Direct3D 11 acceleration:
- JICio maintains a locked 59–61 FPS.
- WaterCMY maintains 58–60 FPS.
- Meridian Studio drops from 60 FPS idle to 39 FPS during continuous mouse drag due to CPU-bound BVH raycasting.
- TCM-Acupoints suffers from an internal React 19 render loop that re-triggers Three.js frame updates continuously, resulting in 11–12 FPS even with physical GPU acceleration.

### 2. Memory Consumption
- JICio loads full BodyParts3D binary chunks into typed arrays, occupying 202 MB heap.
- Meridian Studio loads the full 13.5MB GLB plus BVH tree structures, peaking at 272 MB.
- WaterCMY operates with the smallest memory footprint (57.5 MB heap).

### 3. Traceability to Raw Artifacts
- `research/artifacts/metrics_tcm3d.json`
- `research/artifacts/metrics_studio.json`
- `research/artifacts/metrics_anatomy3d.json`
- `research/artifacts/metrics_tcmacupoints.json`
- Visual evidence screenshots: `evidence_tcm3d.png`, `evidence_studio.png`, `evidence_anatomy3d.png`, `evidence_tcmacupoints.png`

---

## 4. Architectural Decision

1. **Production Runtime Client**: Use JICio's pre-baked static surface coordinates. Delivering pre-baked coordinates achieves **59 FPS on low-end Intel HD 5500 integrated graphics** with zero runtime raycasting overhead.
2. **Clinical Calibration Mode**: Meridian Studio's BVH raycasting engine is retained strictly for optional user calibration / authoring modal, where 39 FPS interaction is acceptable for point-nudging workflows.
3. **Reject TCM-Acupoints Engine**: The React 19 render loop causes severe stuttering (11 FPS) on standard integrated GPUs and is rejected for production atlas rendering.
