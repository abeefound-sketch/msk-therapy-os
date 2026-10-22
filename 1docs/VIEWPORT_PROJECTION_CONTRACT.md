# Viewport Projection & Clipping Contract

**Specification Version:** 1.0.0  
**Status:** ACTIVE  
**Component:** `msk_therapy_os/static/atlas` (`gl.js`, `meridians.js`, `style.css`)  
**Scope:** 3D WebGL Camera Viewport to 2D SVG Acupuncture & Reflex Overlay Mapping  

---

## 1. Overview & Architectural Contract

The MSK-Therapy-OS 3D Atlas renders high-resolution anatomical meshes (bones, muscles, nerves, skin) using WebGL via Three.js while rendering interactive vector pathways (WHO Traditional Chinese Medicine 14 meridians, Thai Sen Sib energy lines, and Vietnamese Dien Chan facial reflex zones) as a high-performance SVG vector overlay.

To eliminate spatial divergence, visual leakage, and cross-viewport bleeding during continuous user interaction (orbit, pan, continuous mouse-wheel zoom, and split-screen comparative research), all 2D overlay rendering must strictly adhere to this **Viewport Projection Contract**.

---

## 2. Authoritative Viewport Descriptor

The WebGL renderer (`AtlasRenderer` in `gl.js`) is the **single source of truth** for stage dimensions, device pixel ratios, camera matrices, and active viewport boundaries.

### 2.1 Interface Definition
```typescript
interface ViewportDescriptor {
  x: number;                  // Viewport horizontal offset in CSS pixels
  y: number;                  // Viewport vertical offset in CSS pixels
  width: number;              // Active viewport width in CSS pixels
  height: number;             // Active viewport height in CSS pixels
  devicePixelRatio: number;   // Window device pixel ratio
  aspect: number;             // Aspect ratio (width / height)
  viewProjectionMatrix: Matrix4; // Camera View-Projection Matrix
  eye: Vector3;               // Camera world position
  mode: 'surface' | 'anatomy' | 'comparative'; // Current atlas visualization mode
  clippingBounds: [number, number, number, number]; // [minX, minY, maxX, maxY]
}
```

### 2.2 Viewport Bounds by Mode
| Mode | Target | Viewport `[x, y, width, height]` | Clipping Bounds `[minX, minY, maxX, maxY]` |
| :--- | :--- | :--- | :--- |
| **Surface Mode** | Full Stage | `[0, 0, W, H]` | `[0, 0, W, H]` |
| **Anatomy Mode** | Full Stage | `[0, 0, W, H]` | `[0, 0, W, H]` (Overlays hidden by default) |
| **Comparative Mode** | Right Overlay | `[Math.floor(W * 0.5), 0, Math.ceil(W * 0.5), H]` | `[Math.floor(W * 0.5), 0, W, H]` |

In **Comparative Mode**, the left half of the stage ($x \in [0, W/2]$) is reserved exclusively for Western Musculoskeletal Anatomy. The contract forbids any acupoint, pin, or meridian polyline segment from outputting coordinates with $x < W/2$.

---

## 3. Four-Tier Projection & Clipping Pipeline

```
3D World Coordinate P(X, Y, Z)
             │
             ▼
[Stage 1: Clip-Space Transformation]
             │ M_vp * P = (x_c, y_c, z_c, w_c)^T
             ▼
[Stage 2: Homogeneous 4D Near-Plane Clipping]
             │ Clamps segment (P0, P1) to w >= 0.005
             ▼
[Stage 3: Perspective Division & Screen Mapping]
             │ x_ndc = x_c / w_c,  y_ndc = y_c / w_c
             │ sx = x_offset + (x_ndc + 1) * 0.5 * vp_width
             │ sy = y_offset + (1 - y_ndc) * 0.5 * vp_height
             ▼
[Stage 4: 2D Liang-Barsky Segment Clipping & Topology Preservation]
             │ Parametric clipping t0, t1 in [minX, minY, maxX, maxY]
             │ Breaks lines on discontinuities; issues 'M' and 'L' commands
             ▼
[Stage 5: Hardware SVG ClipPath + CSS DOM Containment]
             │ <clipPath id="overlayViewportClip"><rect .../></clipPath>
             │ .stage { overflow: hidden; contain: paint; }
```

### Stage 1 & 2: Homogeneous 4D Clip-Space Near-Plane Clipping
Given two consecutive vertices in a meridian polyline $\mathbf{C}_0 = (x_0, y_0, z_0, w_0)$ and $\mathbf{C}_1 = (x_1, y_1, z_1, w_1)$:
- If both $w_0 < w_{near}$ and $w_1 < w_{near}$ (where $w_{near} = 0.005$), the segment lies entirely behind the near clipping plane and is discarded immediately.
- If one endpoint is behind the plane ($w_0 < w_{near}$ and $w_1 \ge w_{near}$), the segment is parametrically clipped:
  $$t = \frac{w_{near} - w_0}{w_1 - w_0}, \quad \mathbf{C}' = \mathbf{C}_0 + t(\mathbf{C}_1 - \mathbf{C}_0)$$
- This prevents division by near-zero or negative $w$, eliminating coordinate inversion artifacts.

### Stage 3: Perspective Division and Screen Mapping
```javascript
const invW = 1.0 / c.w;
const ndcX = c.x * invW;
const ndcY = c.y * invW;
const sx = vp.x + (ndcX + 1.0) * 0.5 * vp.width;
const sy = vp.y + (1.0 - ndcY) * 0.5 * vp.height;
```

### Stage 4: 2D Liang-Barsky Parametric Viewport Clipping
The screen-space segment $(x_0, y_0) \to (x_1, y_1)$ is tested against `clippingBounds: [minX, minY, maxX, maxY]`:
```javascript
function clipSegment2D(x0, y0, x1, y1, bounds) {
  const [minX, minY, maxX, maxY] = bounds;
  const dx = x1 - x0;
  const dy = y1 - y0;
  let t0 = 0.0;
  let t1 = 1.0;

  const clip = (p, q) => {
    if (p === 0) return q >= 0;
    const r = q / p;
    if (p < 0) {
      if (r > t1) return false;
      if (r > t0) t0 = r;
    } else {
      if (r < t0) return false;
      if (r < t1) t1 = r;
    }
    return true;
  };

  if (clip(-dx, x0 - minX) &&
      clip( dx, maxX - x0) &&
      clip(-dy, y0 - minY) &&
      clip( dy, maxY - y0)) {
    return [
      clamp(x0 + t0 * dx, minX, maxX),
      clamp(y0 + t0 * dy, minY, maxY),
      clamp(x0 + t1 * dx, minX, maxX),
      clamp(y0 + t1 * dy, minY, maxY)
    ];
  }
  return null; // Segment lies completely outside clipping rectangle
}
```

### Stage 5: Topology Preservation (No Artificial Diagonals)
When consecutive segments are clipped:
- If a segment's start point $(cx_0, cy_0)$ matches the previous segment's end point within subpixel tolerance ($\Delta < 0.6\text{px}$), an `L` (line-to) SVG command is appended.
- If a break occurred (the polyline exited the viewport and re-entered, or traversed behind the camera), a new `M` (move-to) command is initiated at the clipped entry point.
- **Under no circumstances may an `L` command connect two non-contiguous entry/exit points across the viewport.**

---

## 4. Acupoint Circle & Pin Placement Contract

1. **Acupoint Markers (`<circle>`):**
   - Each acupoint is projected via `projectPoint(pos, vp, viewport)`.
   - If the projected point falls outside `viewport.clippingBounds` or behind the near plane, `projectPoint` returns `null`.
   - The renderer sets `display: none` or removes the element from rendering, preventing off-screen markers from cluttering the DOM or capturing mouse events.

2. **Selected Point Pin (`#pin`):**
   - The 3D selection indicator is positioned strictly at `[sx, sy]`.
   - If the target point is culled, clipped, or behind the camera, the pin is automatically hidden (`pin.style.display = 'none'`).

---

## 5. Automated Regression Verification Suite

Compliance with this contract is tested automatically via Playwright:
- `prototype/verify_p0_remediated_clipping.py`
- Test assertions:
  1. $\forall (x, y) \in \text{SVG } d: x \ge \text{clippingBounds.minX} \land x \le \text{clippingBounds.maxX}$
  2. $\forall (x, y) \in \text{SVG } d: y \ge \text{clippingBounds.minY} \land y \le \text{clippingBounds.maxY}$
  3. $\text{Path.left} \ge \text{Sidebar.right}$
  4. In Comparative Mode: $\forall (x, y) \in \text{RightOverlay}: x \ge W / 2$
  5. 0 instances of `NaN`, `Infinity`, or malformed path tokens.
