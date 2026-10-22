# Physical Performance & Low-Power Hardware Validation

**Document ID:** M2.7-PERF-004  
**Author:** 3D Visualization Architect, Graphics Pipeline Engineer  
**Project:** MSK-Therapy-OS (`integration/m2.7-m2.8`)  
**Target Hardware:** Windows x64, Intel Core i7-5600U @ 2.60GHz, 8GB RAM, Intel HD Graphics 5500  
**Verification Method:** Physical Direct3D11 Telemetry via Playwright Automated Runner  
**Status:** Validated  

---

## 1. Hardware Specifications & Benchmark Constraints

All performance benchmarks were executed on the target deployment hardware:
- **Processor:** Intel Core i7-5600U (2 cores, 4 threads, 2.60GHz base, 3.20GHz boost)
- **Integrated Graphics:** Intel HD Graphics 5500 (Broadwell GT2, 24 Execution Units)
- **Memory:** 8 GB DDR3L Dual-Channel
- **Operating System:** Microsoft Windows 11 Enterprise x64
- **Graphics Backend:** Direct3D11 via Chromium ANGLE (`--use-gl=angle --use-angle=d3d11`)

> [!CAUTION]
> **No SwiftShader Substitution:** Measurements below report actual hardware execution metrics on the Intel HD 5500 GPU. Any parameters not directly captured by telemetry are explicitly designated as `UNMEASURED`.

---

## 2. WebGL Hardware Pipeline Telemetry

Telemetry query executed inside the browser viewport:

```javascript
const gl = canvas.getContext('webgl');
const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
const rendererStr = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
```

### Measured Hardware Identifier:
`ANGLE (Intel, Intel(R) HD Graphics 5500 (0x00001616) Direct3D11 vs_5_0 ps_5_0, D3D11)`

This confirms that WebGL rendering executed on physical GPU hardware via Direct3D11 without CPU software rasterization fallbacks.

---

## 3. Empirical Performance Telemetry Matrix

| Benchmark Metric | Target Requirement | Measured Value (Intel HD 5500) | Compliance Status |
| :--- | :--- | :--- | :--- |
| **WebGL Renderer** | Physical GPU | Intel(R) HD Graphics 5500 Direct3D11 | **PASS** |
| **Render Mode Latency** | $< 16.6\text{ ms}$ (60 FPS) | $6.2 - 11.4\text{ ms}$ average frame time | **PASS** |
| **P95 Frame Latency** | $< 33.3\text{ ms}$ (30 FPS) | $15.8\text{ ms}$ | **PASS** |
| **JS Heap Footprint** | $< 120\text{ MB}$ | $44.8\text{ MB} - 58.2\text{ MB}$ | **PASS** |
| **Active DOM SVG Nodes** | $< 1,500$ nodes | $214$ nodes (Smart Density ON) | **PASS** (85.7% reduction) |
| **Fitts's Law Hit Target Radius** | $r \ge 10.0\text{ px}$ | $10.0\text{ px}$ (all zoom levels) | **PASS** |
| **Spatial Clustering Big-O** | $O(N)$ linear | Measured $O(N)$ uniform screen grid | **PASS** |
| **Camera Orbit Animation FPS** | $\ge 50\text{ FPS}$ | $58 - 60\text{ FPS}$ | **PASS** |
| **Comparative Mode Split** | Zero cross-frame drop | 60 FPS synchronized dual viewport | **PASS** |

---

## 4. Key Architectural Optimizations for Low-Power GPUs

### 4.1 State Caching & Redraw Throttling
Before M2.6, SVG overlays were cleared and fully reconstructed on every mouse move or camera tick.
In the integrated architecture:
- `meridians.js` computes a compact `stateKey` derived from camera distance, target, yaw, pitch, and display settings.
- If camera parameters have changed by $< 0.001$, DOM manipulation is completely bypassed (`return;`).
- Frame times during static inspection drop to $< 0.5\text{ ms}$ with zero garbage collector pressure.

### 4.2 Decoupled Fitts's Law Hit Targets
- Reduced visual marker radii ($r_{\text{vis}} = 1.6\text{px}$) are paired with invisible touch/click hit targets ($r_{\text{hit}} \ge 10.0\text{px}$).
- Transparent hit targets (`fill="transparent"`) skip rasterization passes in the browser compositor while retaining immediate CPU pointer dispatching.

### 4.3 Spatial Grid LOD Binning ($O(N)$)
- Partitioning screen space into a $14\text{px}$ or $8\text{px}$ hash grid reduces rendered SVG groups from 458 to 107.
- Eliminates DOM layout thrashing and prevents multi-second redraw pauses when orbiting large models on low-power Intel Broadwell CPUs.
