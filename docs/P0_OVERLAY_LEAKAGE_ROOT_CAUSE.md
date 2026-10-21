# Root Cause Analysis: 3D Meridian Overlay Leakage, Zoom Clipping, and Comparative Viewport Misalignment

**Date:** 2026-10-21  
**Target Branch:** `prototype/neck-shoulder-poc`  
**Classification:** P0 Rendering Architecture Defect  
**Status:** REMEDIATED & VERIFIED  

---

## 1. Executive Summary

During high-magnification navigation (e.g., zooming into neck/shoulder acupoints such as GB21, LI14, SI14) and during Comparative Research Mode exploration, brightly colored SVG meridian and reflex pathways escaped the 3D WebGL stage container. The lines visually overflowed across the left Layers control panel, the application navigation topbar, and crossed the central comparative viewport divider into the western musculoskeletal anatomy display.

Rather than treating this as a cosmetic CSS z-index issue or arbitrarily hiding coordinates, an end-to-end graphics pipeline audit was conducted. The failure was determined to stem from four compounding architectural deficiencies across CSS containment, homogeneous camera projection mathematics, 2D viewport clipping, and comparative viewport scissoring.

---

## 2. Failure Reproduction & Quantitative Baseline

Automated Playwright reproduction (`prototype/reproduce_p0_overlay_leakage.py`) under headless Chromium Angle D3D11 confirmed the exact user-reported anomalies prior to remediation:

| Metric | Standalone Atlas (Zoomed) | Comparative Mode (Zoomed) | Host App (Zoomed) |
| :--- | :---: | :---: | :---: |
| **SVG Paths Leaking into Sidebar** (`pRect.left < sideRect.right`) | **6 paths** (`left: 232px < 320px`) | N/A (Escaped Left) | Visible bleed |
| **Negative Coordinate Values** ($x < 0$ or $y < 0$) | **414 vertices** (min $y = -508$) | **1,029 vertices** ($x = -705$, $y = -3906$) | Leaked outside iframe boundary |
| **Coordinates Crossing Comparative Divider** ($x < W / 2$) | N/A | **1,561 vertices** in Left Half | Misaligned cross-contamination |
| **ClipPath Viewport Conformance** | **None** (unclipped SVG overlay) | **None** (full-width overlay over 50/50 canvas) | None |

---

## 3. Detailed Root Causes

### Root Cause 1: CSS DOM Viewport Containment Failure
In `msk_therapy_os/static/atlas/style.css`:
```css
/* DEFECTIVE ORIGINAL */
.stage {
  grid-area: stage;
  position: relative;
}

.acupuncture-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: visible; /* CRITICAL: allowed rendered SVG paths to paint outside bounds */
  z-index: 5;
}
```
- `.acupuncture-overlay` had `overflow: visible`, explicitly allowing SVG vector paths whose computed screen coordinates extended beyond the container to render outside the viewport.
- `.stage` lacked `overflow: hidden` and `contain: paint`. As a consequence, whenever coordinates projected outside the stage (e.g. negative X/Y), the browser painted them across adjacent CSS grid areas (`sidebar` at grid-area `side`, `topbar` at grid-area `top`).

### Root Cause 2: Homogeneous Coordinate Division & Frustum Inversion
In `msk_therapy_os/static/atlas/meridians.js` and `gl.js`:
- In standard perspective 3D rendering, a world point $\mathbf{P}_w = (X, Y, Z, 1)^T$ transformed by view-projection matrix $\mathbf{M}_{vp}$ yields homogeneous clip coordinates $\mathbf{P}_c = (x_c, y_c, z_c, w_c)^T$.
- Normalized Device Coordinates (NDC) are obtained via perspective division:
  $$x_{ndc} = \frac{x_c}{w_c}, \quad y_{ndc} = \frac{y_c}{w_c}, \quad z_{ndc} = \frac{z_c}{w_c}$$
- When a polyline segment connects a vertex in front of the camera ($w_c > 0$) to a vertex behind or near the camera plane ($w_c \le 0$ or $w_c \to 0^+$), perspective division inverts the signs and causes coordinates to explode toward $\pm \infty$.
- The original code simply checked `p.z < 1.0` or `w > 0.001` per-vertex. It never clipped line segments against the near plane in homogeneous 4D space. A segment crossing the near plane had one end inverted, creating giant diagonal "spiders" across the screen.

### Root Cause 3: Complete Absence of 2D Viewport Boundary Clipping
- Even when points were in front of the camera, zooming into the model caused distant points of the continuous meridian polylines (such as bladder meridian points on the feet or sacrum when focusing on the neck) to project to extreme off-screen pixel coordinates (e.g., $x = -3600, y = 5200$).
- The renderer directly concatenated these into SVG `d` paths:
  ```svg
  <path d="M 450 320 L 420 310 L -1200 4500 L -3600 8900" />
  ```
- Because SVG path segments were not clipped to the viewport rectangle $[0, 0, W, H]$, the browser's 2D vector rasterizer attempted to stroke paths spanning thousands of pixels across the window layout.

### Root Cause 4: Asymmetric Viewport Scissoring in Comparative Research Mode
- In Comparative Mode, the WebGL canvas scissored the screen into two independent viewports:
  - Left viewport ($x \in [0, W/2]$): Western Musculoskeletal Anatomy (bones, muscles, nerves).
  - Right viewport ($x \in [W/2, W]$): Surface Anatomy + Acupoints + Meridian overlays.
- However, the SVG overlay remained a single full-width element ($[0, W]$).
- When meridian polylines were projected using the right-side camera, the projected 2D coordinates were calculated relative to the canvas origin without clipping to $x \ge W/2$.
- Consequently, meridian lines intended exclusively for the right surface viewport rendered all the way across the central divider into the left anatomical viewport, completely destroying the visual separation contract between Eastern meridians and Western musculoskeletal structures.

---

## 4. Multi-Tier Defense-in-Depth Solution Architecture

To guarantee zero leakage under all camera angles, zooms, and window resize events, a 4-tier containment architecture was implemented:

```
+-------------------------------------------------------------------------------+
| Tier 1: Homogeneous 4D Clip-Space Near-Plane Clipping (w >= 0.005)             |
|   - Prevents division-by-zero, negative W inversion, and coordinate explosion |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
| Tier 2: 2D Liang-Barsky Segment Clipping Against Viewport Bounds              |
|   - Single Mode: Bounds = [0, 0, Width, Height]                               |
|   - Comparative Mode: Bounds = [Width / 2, 0, Width, Height]                   |
|   - Clamps segment endpoints and preserves topology without false diagonals   |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
| Tier 3: SVG Hardware ClipPath Container                                       |
|   - <clipPath id="overlayViewportClip"><rect id="overlayClipRect"/></clipPath> |
|   - Dynamic synchronization with WebGL stage / comparative right pane         |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
| Tier 4: CSS DOM Layout Containment                                            |
|   - .stage { overflow: hidden; contain: paint; }                              |
|   - .acupuncture-overlay { overflow: hidden; contain: paint; }                |
+-------------------------------------------------------------------------------+
```

---

## 5. Summary of Remediated Files

1. `msk_therapy_os/static/atlas/style.css`:
   - Enforced `overflow: hidden; contain: paint;` on `.stage` and `.acupuncture-overlay`.
   - Guaranteed that even in extreme edge cases, DOM painting is strictly contained within the stage grid area.

2. `msk_therapy_os/static/atlas/gl.js`:
   - Implemented `getViewportDescriptor(target = 'overlay')` providing the single source of truth for viewport dimensions, camera projection matrix, mode, and `clippingBounds`.
   - Updated `project()` to validate near plane ($w > 0.005$) and finite NDC before screen space conversion.

3. `msk_therapy_os/static/atlas/meridians.js`:
   - Added SVG `<defs>` with dynamic `<clipPath id="overlayViewportClip">`.
   - Implemented `clipSegmentNearPlane()` in 4D clip space.
   - Implemented `clipSegment2D()` using parametric Liang-Barsky line clipping with subpixel clamping.
   - Implemented `projectAndClipPolyline()` preserving path topology and breaking line segments when jumping across clipping boundaries.
   - Restricted acupoints (`#groupPoints circle`) and pin marker (`#pin`) to valid viewport bounds.
   - Separated comparative UI elements (divider, badges) into `#groupComparativeOverlay` outside the clipping group.
