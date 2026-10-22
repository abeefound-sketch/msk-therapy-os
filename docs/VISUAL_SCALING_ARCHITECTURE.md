# Visual Scaling Architecture: Dynamic Perspective Projection & LOD Engine

**Document ID:** M2.6-ARCH-002  
**Author:** 3D Visualization Architect, WebGL Graphics Pipeline Specialist  
**Project:** MSK-Therapy-OS (`prototype/neck-shoulder-poc`)  
**Status:** Implemented & Verified  

---

## 1. Architectural Principles

1. **Geometry-Preserving:** Under no circumstances are 3D anatomical coordinates ($X, Y, Z$) modified to achieve visual clarity. Coordinates represent physical anatomical structures anchored to the BodyParts3D human model.
2. **Deterministic Screen-Space Mapping:** Scaling calculations occur strictly in normalized screen space per frame, derived directly from the WebGL camera's projection and view matrices.
3. **Decoupled Visual and Interaction Bounds:** Adheres to ISO 9241-9 / Fitts's Law ergonomics by guaranteeing a minimum interactive hit radius ($r \ge 10\text{px}$) regardless of visual rendering radius.
4. **Zero Heap Allocation in Render Loops:** Caches math vectors and transformation states to maintain 60 FPS on low-power Intel HD Graphics 5500 GPUs.

---

## 2. Dynamic Scale Calculation Pipeline

```
┌─────────────────────────────────┐
│     WebGL Camera Parameters     │
│   Eye, Target, FOV, Aspect      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│       VisualScaleEngine         │
│ Project 10cm vector at Target   │
│ Compute pixelsPerMeter          │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Scale Normalization & Clamping│
│  S = clamp(PPM / PPM_ref,       │
│            0.18, 3.5)           │
└────────────────┬────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ Point Marker │   │Polyline Line │
│    Sizing    │   │    Sizing    │
└───────┬──────┘   └──────┬───────┘
        │                 │
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│  Hit Target  │   │Channel Dim & │
│  Generation  │   │  Highlight   │
└──────────────┘   └──────────────┘
```

### 2.1 The `pixelsPerMeter` Metric

Rather than relying on arbitrary Euclidean distance from the camera eye to target (which breaks when panning or tilting), `VisualScaleEngine` computes the actual screen projection of a standard physical meter at the camera's focus plane:

```javascript
class VisualScaleEngine {
  constructor(renderer) {
    this.renderer = renderer;
    this.referenceDistance = 1.2; // meters
    this.basePPM = 350.0;         // calibrated baseline pixels per meter
  }

  computeScale() {
    const r = this.renderer;
    if (!r || !r.camera) return 1.0;

    // Anchor at camera target
    const tgt = r.camera.target || [0, 0, 0];
    const p0 = r.projectToScreen(tgt[0], tgt[1], tgt[2]);
    const p1 = r.projectToScreen(tgt[0], tgt[1] + 0.10, tgt[2]);

    if (!p0 || !p1) return 1.0;

    const dy = Math.hypot(p1.x - p0.x, p1.y - p0.y);
    const ppm = dy / 0.10; // pixels per physical meter

    // Normalized scale factor relative to comfortable medium view
    const rawScale = ppm / this.basePPM;
    return Math.max(0.18, Math.min(rawScale, 3.5));
  }
}
```

### 2.2 Sizing Curves and Clamping Functions

To prevent markers from becoming invisible dust motes when fully zoomed out or ballooning into gigantic disks when zoomed close, a sub-linear power curve is applied:

$$r_{\text{vis}}(S) = \text{clamp}\left(r_{\text{base}} \cdot S^{0.65}, \quad r_{\min}, \quad r_{\max}\right)$$

$$w_{\text{stroke}}(S) = \text{clamp}\left(w_{\text{base}} \cdot S^{0.50}, \quad w_{\min}, \quad w_{\max}\right)$$

$$w_{\text{line}}(S) = \text{clamp}\left(w_{\text{base, line}} \cdot S^{0.45}, \quad 1.0\text{ px}, \quad 3.8\text{ px}\right)$$

Where:
- $r_{\text{base}} = 3.2\text{ px}$, $r_{\min} = 1.5\text{ px}$, $r_{\max} = 5.5\text{ px}$
- $w_{\text{base}} = 1.4\text{ px}$, $w_{\min} = 0.8\text{ px}$, $w_{\max} = 2.2\text{ px}$
- $w_{\text{base, line}} = 2.0\text{ px}$

---

## 3. Zoom Thresholds & LOD Behavior

| Viewport Zoom State | Camera Distance ($d$) | Normalized Scale ($S$) | Visual Radius ($r_{\text{vis}}$) | Stroke Width | Line Width | Cluster Grid Size |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Full-Body (Far)** | $d \ge 1.8\text{ m}$ | $0.18 - 0.50$ | $1.5 - 2.2\text{ px}$ | $0.8 - 1.1\text{ px}$ | $1.0 - 1.6\text{ px}$ | $14\text{ px}$ (High) |
| **Regional (Medium)**| $0.8\text{ m} \le d < 1.8\text{ m}$ | $0.50 - 1.40$ | $2.2 - 3.8\text{ px}$ | $1.1 - 1.6\text{ px}$ | $1.6 - 2.5\text{ px}$ | $8\text{ px}$ (Fine) |
| **Close-Up (Near)** | $d < 0.8\text{ m}$ | $1.40 - 3.50$ | $3.8 - 5.5\text{ px}$ | $1.6 - 2.2\text{ px}$ | $2.5 - 3.8\text{ px}$ | Disengaged ($0\text{ px}$) |

---

## 4. Interaction Ergonomics (Fitts's Law Compliance)

In traditional web applications, mouse events are bound directly to visible SVG primitives. When an acupoint's visible radius is reduced to $1.6\text{ px}$, acquiring the point with a mouse pointer requires sub-pixel dexterity ($W = 3.2\text{ px}$ target width).

Milestone M2.6 solves this via decoupled SVG grouping:
```html
<g class="acu-marker-group" data-code="LU7" transform="translate(452, 218)">
  <!-- Invisible interaction target ensuring Fitts's law target acquisition -->
  <circle class="acu-hit-target" r="10.0" fill="transparent" pointer-events="all" />
  
  <!-- Precision visual dot -->
  <circle class="acu-marker-circle" r="1.6" stroke-width="0.9" fill="#00ffff" />

  <!-- Animated focus halo (visible only when selected) -->
  <circle class="acu-focus-halo" r="9.0" stroke="#00e5ff" stroke-dasharray="3,2" />
</g>
```

### Performance & Memory Overhead:
- Transparent hit targets incur zero paint cost in the browser graphics pipeline because WebKit / Blink / Gecko skip rasterization for `fill="transparent"`, maintaining fast screen updates.
- Hit testing remains active on the CPU layout tree, guaranteeing instantaneous point selection, hover tooltips, and context menus.
