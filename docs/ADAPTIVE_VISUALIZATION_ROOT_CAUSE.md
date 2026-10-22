# Root-Cause Analysis: 3D Acupoint & Meridian Visual Overcrowding

**Document ID:** M2.6-RCA-001  
**Author:** Principal Frontend Engineer, WebGL/SVG Rendering Architect  
**Project:** MSK-Therapy-OS (`prototype/neck-shoulder-poc`)  
**Target Hardware:** Windows x64, Intel Core i7-5600U, 8GB RAM, Intel HD Graphics 5500  
**Status:** Solved & Verified  

---

## 1. Executive Summary

In Milestone M2.5 and earlier iterations, users reported severe visual degradation when viewing the anatomical model at zoom levels typical for full-body inspection:
- Hundreds of bright cyan circles ($r \approx 4.5\text{px}$) covered the entire torso, limbs, and face.
- Meridian polyline trajectories crossed each other in dense bundles, completely obscuring underlying muscle, skeletal, and fascia geometry.
- Point selection was erratic due to overlapping hit regions without z-sorting or density controls.

This document formalizes the empirical investigation, root causes, mathematical formulation, and resolution for Milestone M2.6.

---

## 2. Empirical Baseline Reproduction

To ensure evidence-first debugging, a reproduction test harness (`prototype/reproduce_visual_overcrowding.py`) was executed against the clean baseline at full-body camera distance ($d = 2.4\text{m}$, FOV $32^\circ$, viewport $1024 \times 768$).

### 2.1 Quantitative Baseline Measurements

| Metric | Measured Baseline (Pre-M2.6) | Anatomical Context / Limit | Severity |
| :--- | :--- | :--- | :--- |
| **Rendered Acupoint Markers** | 458 SVG circle elements | 368 logical codes (bilateral) | CRITICAL |
| **Average Marker Radius** | $4.51\text{ px}$ | Fixed radius $4.5\text{ px}$ | HIGH |
| **Average Stroke Width** | $1.50\text{ px}$ | Fixed stroke $1.5\text{ px}$ | HIGH |
| **Total Marker Projected Area** | **$29,231.1\text{ px}^2$** | Model body projected area: **$35,748\text{ px}^2$** | **81.8% Occlusion** |
| **Visible Meridians Overlap** | 14 channels at 100% opacity | Fully opaque lines crossing | CRITICAL |
| **Console Errors** | 0 | Clean WebGL pipeline | PASS |

At full-body view, the acupoint markers alone occupied **81.8%** of the visible surface area of the patient's body. The human anatomy was rendered nearly invisible under a solid field of cyan dots.

---

## 3. Detailed Root Causes

### Root Cause 1: Screen-Space Fixed Radius Invariant to Camera Distance
Prior to M2.6, `meridians.js` rendered SVG circles with fixed attributes:
```javascript
// Pre-M2.6 fixed screen-space marker
circle.setAttribute('r', '4.5');
circle.setAttribute('stroke-width', '1.5');
```
In 3D perspective projection, as the camera dollies back from $d = 0.4\text{m}$ (close-up on shoulder/neck) to $d = 2.4\text{m}$ (full-body), the physical human body shrinks by a factor of:
$$\text{Scale Ratio} = \frac{d_{\text{close}}}{d_{\text{full}}} = \frac{0.4}{2.4} \approx 0.167$$
Because marker radius remained constant at $4.5\text{ px}$, the apparent physical diameter of an acupoint marker relative to human anatomy increased sixfold ($6\times$). At $d = 2.4\text{m}$, each acupoint marker had an apparent anatomical size of $\approx 6\text{ cm}$ in diameter—larger than an adult patella or clavicle head.

### Root Cause 2: Absence of Zoom-Dependent Level of Detail (LOD) / Spatial Clustering
All 458 bilateral points across 14 channels plus Extra points were evaluated and projected simultaneously into the SVG container. Even in anatomically dense regions (such as the cranium, ear, wrist, and foot where points are separated by $< 15\text{ mm}$ in 3D physical space), every point was drawn as an individual $4.5\text{ px}$ circle. In screen space at full-body view, inter-point screen distances dropped below $2\text{ px}$, causing massive overlapping and visual coalescing.

### Root Cause 3: Unbounded Polyline Stroke & Opacity Overlap
Meridian polylines were rendered at uniform stroke width ($2.5\text{ px}$) and full opacity across all 14 channels simultaneously. When viewing the torso or spine, multiple channels (e.g., Bladder 1st line, Bladder 2nd line, Governor Vessel, Kidney meridian) run in close parallel trajectories ($\Delta x \approx 1.5 - 3.0\text{ cm}$), collapsing into an indistinguishable multicolored band.

### Root Cause 4: Disconnect Between Hit Target Size and Visual Size
Earlier attempts to shrink point radii caused user complaints that points were impossible to click or hover. This stemmed from coupling visual SVG geometry directly with DOM event dispatching: shrinking `r` to $1.8\text{ px}$ reduced the hit target area from $\pi(4.5)^2 \approx 63.6\text{ px}^2$ down to $\pi(1.8)^2 \approx 10.2\text{ px}^2$, violating Fitts's Law for precision targeting.

---

## 4. Mathematical Formulation & Architecture Solution

To permanently solve this without perturbing anatomical XYZ coordinates:

1. **Dynamic Apparent Scale ($\text{pixelsPerMeter}$):**
   We define physical reference vector $\vec{v}_{\text{ref}} = [0, 0.10, 0]^T$ ($10\text{ cm}$) at the 3D camera target:
   $$\vec{p}_0 = \text{project}(\vec{c}_{\text{target}}), \quad \vec{p}_1 = \text{project}(\vec{c}_{\text{target}} + \vec{v}_{\text{ref}})$$
   $$\text{pixelsPerMeter} = \frac{\|\vec{p}_1 - \vec{p}_0\|_2}{0.10}$$
   Normalized scale ratio relative to reference distance ($1.2\text{ m}$):
   $$S = \text{clamp}\left(\frac{\text{pixelsPerMeter}}{S_{\text{ref}}}, 0.18, 3.5\right)$$

2. **Bounded Non-Linear Visual Geometry:**
   - Visual radius:
     $$r_{\text{vis}} = \text{clamp}\left(r_{\text{base}} \cdot S^{0.65}, 1.5\text{ px}, 5.5\text{ px}\right)$$
   - Stroke width:
     $$w_{\text{stroke}} = \text{clamp}\left(w_{\text{base}} \cdot S^{0.5}, 0.8\text{ px}, 2.2\text{ px}\right)$$
   - Polyline width:
     $$w_{\text{line}} = \text{clamp}\left(w_{\text{line, base}} \cdot S^{0.45}, 1.0\text{ px}, 3.8\text{ px}\right)$$

3. **Decoupled Fitts's Law Hit Targets:**
   Each acupoint marker is rendered as a composite SVG group containing:
   - Visual element: $r_{\text{vis}} \in [1.5, 5.5]\text{ px}$
   - Transparent hit target: $r_{\text{hit}} = \max(r_{\text{vis}} + 7\text{ px}, 10.0\text{ px})$, `fill="transparent"`, `pointer-events="all"`
   This maintains an effective click/touch target area of at least $314\text{ px}^2$ at all zoom levels.

4. **Screen-Space Spatial Grid Clustering ($O(N)$):**
   Screen space is partitioned into a uniform hash grid with cell size $\Delta_{\text{grid}} \in [8, 14]\text{ px}$. Points falling within the same cell are clustered deterministically, while preserving anatomical anchors, active selections, and bilateral laterality.

---

## 5. Summary of Remediation Results

| Metric | Before (M2.5) | After (M2.6 Smart Density ON) | Improvement |
| :--- | :--- | :--- | :--- |
| **Visible Point Elements** | 458 markers | 107 items (representative + clusters) | **76.6% reduction** |
| **Average Marker Radius** | $4.51\text{ px}$ | $1.61\text{ px}$ | **64.3% smaller** |
| **Total Visual Footprint** | $29,231\text{ px}^2$ | $4,663\text{ px}^2$ | **84.0% less clutter** |
| **Hit Target Radius** | $4.5\text{ px}$ | $\ge 10.0\text{ px}$ | **122% larger touch target** |
| **Channel Clutter** | 14 channels @ 100% | 1 active @ 100%, 13 @ 18% dim | Clear clinical hierarchy |
| **Coordinate Integrity** | 100% preserved | 100% preserved | Zero coordinate rebaking |
