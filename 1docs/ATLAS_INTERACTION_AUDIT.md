# Forensic Engineering Audit: 3D Atlas Interaction & Navigation Remediation

**Project:** `D:\5Projects\msk-therapy-os`  
**Branch:** `prototype/neck-shoulder-poc`  
**Date:** October 21, 2026  
**Auditor:** Principal Engineer & 3D Visualization Specialist  

---

## 1. Executive Summary & Root Cause Analysis

### 1.1 The Locked Rotation Center Defect
Prior to remediation, the 3D anatomical viewer locked camera rotation permanently around the full-body centroid $\mathbf{T}_{\text{init}} = [-0.00065, 0.86485, 0]$ (pelvis/navel level). 

When clinicians and learners attempted to inspect neck and shoulder structures (e.g. C7 vertebra, trapezius, acupoints GV14 at $y=1.435\,\text{m}$, GB21 at $y=1.419\,\text{m}$):
1. **Camera Zoom Drift:** Scrolling the wheel moved the camera along the ray toward $y=0.865\,\text{m}$. Neck structures drifted rapidly out of the top of the viewport.
2. **Orbit Disorientation:** Rotating the view revolved the camera around the pelvis, swinging neck/shoulder points off-screen in large circular arcs.
3. **Absence of Camera Pan:** Users were unable to right-drag or Shift+left-drag to position anatomical structures in the center of the canvas.
4. **Near-Plane Mesh Clipping:** Zooming closer than $0.5\,\text{m}$ clipped vertebral spines and dorsal surfaces because the camera near plane was scaled to full-body distances.

### 1.2 Mathematical & Architectural Remediation
We remediated all five defects cleanly across `msk_therapy_os/static/atlas/gl.js`, `app.js`, `meridians.js`, and `msk_therapy_os/static/index.html`.

---

## 2. Technical Remediation Implementation

### 2.1 View-Plane Camera Panning Mathematics
In `gl.js`, we replaced the flawed world-$Y$ translation with view-plane projected motion.

Given camera yaw $\psi$, pitch $\theta$, distance $d$, vertical FOV $\alpha$, and canvas height $H$:
$$\text{Scale } s = \frac{2 \cdot d \cdot \tan(\alpha / 2)}{H}$$
The camera's orthogonal view-plane vectors in world space:
$$\mathbf{R} = [\cos(\psi), 0, -\sin(\psi)]$$
$$\mathbf{U} = [-\sin(\theta)\sin(\psi), \; \cos(\theta), \; -\sin(\theta)\cos(\psi)]$$
Translation applied to target $\mathbf{T}$:
$$\Delta \mathbf{T} = -\mathbf{R} \cdot dx \cdot s + \mathbf{U} \cdot dy \cdot s$$

This guarantees that dragging in any camera orientation moves the 3D surface underneath the cursor 1:1 without shear, distortion, or vertical zoom drift.

### 2.2 Dynamic Target Centering & Acupoint Easing
In `meridians.js` and `app.js`:
- Selecting an acupoint (e.g., GV14 at $[0.0, 1.435, -0.111]$) immediately updates `camera.target` to that exact 3D coordinate and eases distance to $\le 0.48\,\text{m}$.
- Selecting an anatomical structure computes the bounding box centroid $\mathbf{C} = \frac{\mathbf{B}_{\min} + \mathbf{B}_{\max}}{2}$ and updates `camera.target` dynamically.
- Subsequent orbit and wheel zoom actions pivot directly around the selected structure.

### 2.3 Intelligent Zoom Limits & Near-Plane Depth Adjustment
In `gl.js`:
- Minimum zoom distance extended from $0.2\,\text{m}$ down to $0.04\,\text{m}$ ($4\,\text{cm}$).
- Near plane dynamically scales with camera distance:
  $$\text{near} = \min(0.015, \; \max(0.001, \; d \cdot 0.015))$$
  At $d = 0.145\,\text{m}$, $\text{near} = 0.0022\,\text{m}$ ($2.2\,\text{mm}$), preventing any near-plane clipping of vertebrae, ligaments, or acupuncture needles.

### 2.4 Multi-Touch State Machine
In `app.js`, an `activePointers` map tracks all simultaneous pointer contacts:
- **1 Finger / Mouse:** Orbit drag (left button) or Pan drag (right button / Shift+left).
- **2 Fingers:** Simultaneous pinch-to-zoom ($\text{ratio} = \Delta \text{dist}$) and two-finger pan ($\Delta \text{center}$).

### 2.5 Navigation Controls
Added buttons and keyboard shortcuts across both standalone viewer and host application:
- **Full Body:** (`Home` key / `#btnFullBody`): Frames full body bounding box ($d \approx 3.69\,\text{m}, y \approx 0.865\,\text{m}$).
- **Focus Selected:** (`F` key / `#btnFocusSelected`): Returns camera directly to frame the currently active structure or acupoint ($d \approx 0.15\text{--}0.54\,\text{m}$).

---

## 3. Playwright Verification Suite & Browser Evidence

Executed automated verification script `prototype/verify_interaction.py` with Chrome D3D11 GPU acceleration. All 11 automated test cases passed.

| # | Test Scenario | Verified Condition | Measurement | Result |
|---|---|---|---|---|
| 1 | Right-Drag Pan | Target translates along view plane | $\Delta x = -0.437\,\text{m}, \Delta y = -0.291\,\text{m}$ | **PASS** |
| 2 | Shift+Left Pan | Target translates without mouse right click | Restores or pans smoothly | **PASS** |
| 3 | Acupoint Dynamic Target | Camera centers on GV14 at C7 level | $\mathbf{T} = [0, 1.435, -0.111], d = 0.48\,\text{m}$ | **PASS** |
| 4 | Zoom-to-Detail | Close inspection without mesh clipping | $d = 0.145\,\text{m}, \text{near} = 2.2\,\text{mm}$ | **PASS** |
| 5 | Orbit Around GV14 Pivot | Target remains locked at C7 during rotation | $\mathbf{T} = [0, 1.435, -0.111]$ (0 drift) | **PASS** |
| 6 | Full Body Framing Button | Re-frames entire atlas scene | $\mathbf{T} = [0, 0.865, 0], d = 3.69\,\text{m}$ | **PASS** |
| 7 | Focus Selected Button | Reframes GV14 from full body view | $\mathbf{T} = [0, 1.435, -0.111], d = 0.54\,\text{m}$ | **PASS** |
| 8 | Structure Centroid Focus | Centers on Trapezius / cervical structure | $\mathbf{T} = [0.073, 1.277, -0.089], d = 1.54\,\text{m}$ | **PASS** |
| 9 | Touch Gesture Pointer | Two-finger pinch updates camera dist | $d = 1.537\,\text{m} \to 1.258\,\text{m}$ | **PASS** |
| 10 | Host Toolbar Synchronization | Host buttons postMessage to iframe | Full Body & Focus triggered | **PASS** |
| 11 | Clinical Workflow Integrity | SOAP, Safety Gate, ROM observation | Zero console errors, 61/61 tests pass | **PASS** |

---

## 4. Visual Evidence Artifacts

- `research/artifacts/evidence_interaction_pan_right_drag.png`
- `research/artifacts/evidence_interaction_acupoint_target_gv14.png`
- `research/artifacts/evidence_interaction_zoomed_neck_detail.png`
- `research/artifacts/evidence_interaction_orbit_neck.png`
- `research/artifacts/evidence_interaction_full_body.png`
- `research/artifacts/evidence_interaction_refocus_selected.png`
- `research/artifacts/evidence_interaction_structure_focus.png`
- `research/artifacts/evidence_interaction_main_app.png`

---

## 5. Clinical Safety & Regression Compliance

- **Pytest Suite:** 61 passed in 12.18s ($100\%$ pass rate).
- **Safety Gate Integration:** Verified red-flag screening against cervical radiculopathy, active myelopathy signs, and cauda equina criteria remains fully functional.
- **SOAP & ROM Clinical Record:** Dynamic observation logging and FHIR JSON exports are completely unaffected.
- **Live Local Server:** Running stably at `http://127.0.0.1:8085/` for interactive acceptance testing.
