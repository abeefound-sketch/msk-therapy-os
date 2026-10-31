# P17 Root Cause Analysis: Interactive Biomechanics & UI Integrity Failures

## Executive Summary

Prior to Milestone P17, the MSK-Therapy-OS Education Studio suffered from severe UI-to-renderer decoupling and misleading visual presentation. When users clicked Modes A, B, C, and D, the interface appeared visually identical, with static progress bars permanently displayed. Forensic code tracing revealed five primary architectural root causes.

---

## 1. Root Cause 1: Static `#muscle-recruitment-list` Uncoupled from Visual Mode State

### Mechanism
In `msk_therapy_os/static/education/index.html`, `#muscle-recruitment-list` was statically embedded with pre-populated HTML bars:
```html
<div id="muscle-recruitment-list">
    <!-- Deltoid 45%, Supraspinatus 62%, Levator 22%, Suboccipital 18% -->
</div>
```
In `shoulder_lab.js`, `setMode(mode, activeBtn)` updated text banners and empty state notices, but **never toggled the visibility of `#muscle-recruitment-list`**.
### Consequence
When the user clicked Mode A (Anatomy), Mode B (Geometry), Mode C (Activation), or Mode D (Force), the static list with `45%`, `62%`, `22%`, and `18%` remained permanently visible. The user saw identical progress bars in all four modes.
### Resolution
- In `index.html`, initialized `#muscle-recruitment-list` with `style="display: none;"`.
- In `shoulder_lab.js`, explicitly hide `#muscle-recruitment-list` in Modes A, B, D, and Comparison. Show it **only** in Mode C when an active `.sto` dataset exists.

---

## 2. Root Cause 2: Unrecognized Mode Strings in `anatomy_viewer.js`

### Mechanism
In `anatomy_viewer.js`, `setVisualMode(mode)` contained only two legacy branches:
```javascript
setVisualMode(mode) {
    this.currentMode = mode;
    if (mode === 'ANATOMICAL_FUNCTION') {
        this.clearHighlights();
    } else if (mode === 'MODEL_ESTIMATED') {
        this.seek(this.currentTime);
    }
}
```
In `shoulder_lab.js`, the event handlers passed:
- `MODE_A_ANATOMICAL_PARTICIPATION`
- `MODE_B_GEOMETRIC_CHANGE`
- `MODE_C_ESTIMATED_ACTIVATION`
- `MODE_D_ESTIMATED_FORCE`
### Consequence
For Modes A, B, and D, `anatomy_viewer.js` had no matching handler and called `this.clearHighlights()`. As a result, the 3D meshes always reset to the exact same default terracotta tone (`#b55a5a`).
### Resolution
Expanded `setVisualMode(mode, params)` to fully support all P16/P17 modes:
- **Mode A**: Distinguishes Agonists (cyan `#38bdf8`), Synergists (amber `#f59e0b`), Stabilizers (purple `#a855f7`), and dims non-participating muscles (opacity 0.20).
- **Mode B**: Dims muscles (opacity 0.22) to highlight skeletal joint pivots, showing `MODEL_GEOMETRY_INSUFFICIENT`.
- **Mode C**: Applies static optimization heat-map ramp (blue $\to$ yellow $\to$ red) synchronized with `.sto` timestamps.
- **Mode D**: Neutral tone with explicit `MUSCLE_FORCE_NOT_AVAILABLE` empty state.

---

## 3. Root Cause 3: Broken Mode Condition in Kinematic Seek Loop

### Mechanism
In `anatomy_viewer.js`, `seek(t)` contained:
```javascript
if (this.currentMode === 'MODEL_ESTIMATED') {
    this._applyMuscleActivationColors(muscleActivations);
}
```
Because P16/P17 set `this.currentMode` to `'MODE_C_ESTIMATED_ACTIVATION'`, the conditional check evaluated to `false`.
### Consequence
During playback or timeline scrubbing in Mode C, `_applyMuscleActivationColors` was never invoked. The 3D model remained static in default color even while `.sto` data was being parsed.
### Resolution
Updated the conditional to:
```javascript
if (this.currentMode === 'MODE_C_ESTIMATED_ACTIVATION' || this.currentMode === 'MODEL_ESTIMATED') {
    this._applyMuscleActivationColors(muscleActivations);
}
```

---

## 4. Root Cause 4: Missing Cervicothoracic Skeleton Geometry

### Mechanism
In `index.html`, the asset loader was hardcoded to:
```javascript
skeletonUrl: './models/shoulder_skeleton.glb'
```
`shoulder_skeleton.glb` contains only four meshes (`Thorax`, `Clavicle_R`, `Scapula_R`, `Humerus_R`). It contains **no cervical vertebrae and no cranium**.
In contrast, `cervicothoracic_skeleton.glb` contains nine articulated nodes: `Thorax`, `Cervical_Lower` (C3-C7), `Cervical_Upper` (C1-C2), `Skull_Cranium`, `Clavicle_R`, `Scapula_R`, `Humerus_R`, `Levator_Scapulae`, and `Suboccipital_Muscles`.
### Consequence
When the user selected cervical motion scenarios (e.g., Vasavada cervical flexion/extension), the neck and head bones were completely missing from the 3D scene.
### Resolution
Updated `index.html` to dynamically load `cervicothoracic_skeleton.glb` for all unified and cervicothoracic views, ensuring complete 3D skeletal geometry is rendered.

---

## 5. Root Cause 5: Inadequate Camera Framing and Viewport Crowding

### Mechanism
The default camera position was hardcoded at `(-0.25, 1.48, 1.05)` with target `(-0.10, 1.38, -0.02)` (focused on the right shoulder). Additionally, camera view buttons passed `'shoulder'` instead of `'anterior'` to `resetCamera()`, which had no handler for front view.
The floating `.player-bar` overlay was 130px tall with 14px vertical padding and 12px gaps, blocking the lower 30% of the canvas.
### Consequence
The 3D anatomical model appeared off-center, small, and obscured by the oversized controls bar.
### Resolution
- Centered camera on `(0.0, 1.44, 0.0)` with FOV 40 and adaptive distance (0.88 for unified, 0.65 for cervical, 0.72 for shoulder), filling ~75% of the viewport.
- Compacted `.player-bar` to 65px height with sleek styling (`rgba(11, 19, 34, 0.90)`).
- Implemented `setCameraView(viewName, region)` with full support for anterior, posterior, and lateral views.
