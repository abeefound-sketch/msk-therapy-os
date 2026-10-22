# Smart Density Specification: Screen-Space Spatial Clustering & Multi-System Isolation

**Document ID:** M2.6-SPEC-003  
**Author:** Principal Frontend Engineer, Medical Data Architect  
**Project:** MSK-Therapy-OS (`prototype/neck-shoulder-poc`)  
**Status:** Implemented & Verified  

---

## 1. Overview and Design Objectives

The **Smart Density Manager** (`MarkerDensityManager`) introduces an intelligent, $O(N)$ level-of-detail (LOD) aggregation system for dense anatomical point fields. When viewing the human body from medium to long distances, multiple points can project into the same screen area, creating cognitive overload and visual occlusion.

### Strict Clinical and Functional Guarantees:
1. **Mathematical Point Conservation:** Total points must strictly satisfy:
   $$\text{Available} = \text{Visible} + \text{Clustered} + \text{Filtered}$$
   No points are ever dropped, leaked, or double-counted.
2. **Knowledge System Isolation:** WHO Standard Acupoints, Vietnamese Diên Chẩn Facial Reflex points, Extra points, and Custom Practitioner points must **never** be merged into the same cluster.
3. **Anatomical Bilateral Isolation:** Left-sided (`left`) and Right-sided (`right`) points must **never** be merged together across the sagittal midline plane.
4. **Anchor & Selection Priority:**
   - Actively selected points (`selectedCode`) are **never clustered** and remain individually rendered with animated selection halos.
   - Actively edited custom points (`editingPointId`) are **never clustered**.
   - Representative cluster markers prioritize points with `registration_status == 'VERIFIED_ANATOMICAL_ANCHOR'`.
5. **Interactive Zoom-to-Centroid Expansion:** Clicking any cluster badge initiates a smooth camera animation targeting the 3D centroid of all constituent points and zooming in to expand the cluster.

---

## 2. Spatial Binning Algorithm

The clustering algorithm runs in linear time $O(N)$ using a 2D screen-space uniform spatial hash grid:

```
Screen Point (x, y) ──► Bin Index:
  gx = floor(x / cell_size)
  gy = floor(y / cell_size)
  Hash Key = system + ":" + side + ":" + gx + ":" + gy
```

### 2.1 Dynamic Cell Sizing Based on Camera Scale
```javascript
const scale = this.scaleEngine.computeScale();
let cellSize = 0; // Off / Close-up

if (this.styleController.getSetting('smartDensity')) {
  if (scale < 0.6) {
    cellSize = 14; // Full-body view: coarse binning (14px)
  } else if (scale < 1.2) {
    cellSize = 8;  // Mid-range view: fine binning (8px)
  } else {
    cellSize = 0;  // Close-up: individual points, no clustering
  }
}
```

### 2.2 Binning Key Generation
```javascript
function getBinKey(pt, x, y, cellSize) {
  const gx = Math.floor(x / cellSize);
  const gy = Math.floor(y / cellSize);
  const system = pt.system || (pt.code.startsWith('DC_') ? 'dienchan' : 'who');
  const side = pt.side || 'midline';
  return `${system}:${side}:${gx}:${gy}`;
}
```

---

## 3. Representative Selection Logic

When $M > 1$ points fall into the same screen-space cell:
1. **Selection Bypass:** If one of the points matches `selectedCode` or `editingPointId`, it is extracted as an independent visible marker; remaining points form a cluster of size $M - 1$.
2. **Anchor Hierarchy:** The representative point for the cluster is chosen via deterministic priority:
   - Priority 1: `registration_status === 'VERIFIED_ANATOMICAL_ANCHOR'`
   - Priority 2: Primary meridian cardinal point (e.g., He-Sea, Yuan-Source, Shu-Stream)
   - Priority 3: Alphanumeric code sorting (ensures deterministic rendering across frames without visual jitter)

---

## 4. Visual Cluster Marker DOM Representation

A cluster is rendered as a composite SVG group `.acu-cluster-marker`:

```html
<g class="acu-cluster-marker" data-cluster-key="who:right:18:24" transform="translate(320, 194)">
  <!-- Expanded hit target for finger/stylus tapping -->
  <circle class="acu-cluster-hit" r="14" fill="transparent" pointer-events="all" />

  <!-- Outer pulsing ring indicating aggregated points -->
  <circle class="acu-cluster-base" r="7.2" fill="#00ffff" fill-opacity="0.35" stroke="#00ffff" stroke-width="1.2" />

  <!-- Inner core dot -->
  <circle class="acu-cluster-core" r="3.0" fill="#ffffff" />

  <!-- Count badge pill -->
  <rect class="acu-cluster-badge-bg" x="4" y="-12" width="16" height="11" rx="4" fill="#000000" fill-opacity="0.8" stroke="#00ffff" stroke-width="0.8" />
  <text class="acu-cluster-badge-text" x="12" y="-4" text-anchor="middle" font-size="8" fill="#00ffff">+3</text>
</g>
```

---

## 5. Click-to-Zoom Expansion Behavior

When a user clicks or taps on a cluster marker:
1. The 3D centroid of all member points is computed:
   $$\vec{C} = \frac{1}{K}\sum_{i=1}^K \vec{P}_i$$
2. The optimal target camera distance is calculated:
   $$d_{\text{target}} = \max\left(0.55\text{ m}, \quad d_{\text{current}} \times 0.60\right)$$
3. The renderer's camera transition is invoked:
   ```javascript
   renderer.flyTo({
     target: centroid,
     distance: dTarget,
     duration: 450 // ms smooth cubic easing
   });
   ```
4. As the camera dollies in, `pixelsPerMeter` increases, normalized scale $S$ surpasses $1.2$, `cellSize` drops to $0$, and the cluster smoothly dissolves into individual, cleanly spaced acupoint markers.
