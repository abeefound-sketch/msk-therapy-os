# P9.3 FORENSIC AUDIT & ROOT CAUSE ANALYSIS: 14-CHANNEL MERIDIAN GEOMETRY & WEBGL INTEGRATION

**Author:** Principal Computational Geometry Engineer, Senior WebGL Engineer, Biomechanics Software Architect  
**Project:** MSK-Therapy-OS  
**Repository Branch:** `feat/p9.3-meridian-geometry-correction`  
**Reference Mesh:** BodyParts3D FJ2810 Canonical Ground Truth (`05b49233...`)  
**Upstream Source:** `acupuncture_3d.json` (SHA-256 checksum-locked)  
**Date:** October 2026

---

## 1. EXECUTIVE SUMMARY

An exhaustive forensic audit of the meridian path generation and WebGL/SVG visualization pipeline in `MSK-Therapy-OS` revealed systematic geometric distortions across all 14 channels (12 bilateral paired meridians + 2 midline channels). 

Prior to this engineering phase, meridians were rendered in the 3D Atlas Viewer using pre-baked static polylines (`surface_vertices` from an uncalibrated upstream dataset). While Phase 9.1 and Phase 9.2 successfully established authoritative, landmark-grounded spatial coordinates for acupoints on the BodyParts3D FJ2810 mesh, the meridian paths remained disconnected from the resolved points. 

Consequently:
1. **Geometric Divergence:** Acupoints resolved by P9/P9.2 deviate from the static meridian lines by up to **68.08 mm** in neutral pose (e.g. `LI4` is 67.55 mm off the line; `GB21` is 63.32 mm off; `PC6` is 58.21 mm off), and by over **91.12 mm** under joint kinematics.
2. **Kinematic Shearing & Mid-Air Floating:** In `pose_adjusted` mode, meridian polylines were sheared using crude Cartesian height thresholds ($y > 1.50\text{ m}$ for head, $y > 0.85\text{ m}$ for arms/torso) rather than adhering to rigid bone segments and joint rotational axes. This causes meridians to slice through the thoracic cavity or hover in mid-air off abducted limbs.
3. **Laterality Vulnerability:** Mirrored paths for bilateral channels were naively generated via simple coordinate reflection ($X \to -X$) without verifying anatomical landmark anchors (`LM_ACROMION_R` at $+0.188\text{ m}$, `LM_ACROMION_L` at $-0.188\text{ m}$), leading to side ambiguities and normal inversions.
4. **All-or-Nothing Occlusion Culling:** A naive whole-path camera-facing heuristic in `meridians.js` (`(facingCount / sampleCount) >= 0.35`) computed without surface normals causes complex channels (`BL`, `GB`, `ST`) to abruptly flicker or vanish entirely upon camera orbit, while penetrating segments remain rendered over foreground anatomy.

---

## 2. AUDIT METHODOLOGY & MEASUREMENT SETUP

To ensure absolute mathematical integrity and eliminate subjective visual impressions, an automated coordinate auditor (`scratch/audit_meridian_deviations.py`) measured the Euclidean distance between every resolved acupoint and the nearest vertex on its corresponding static meridian polyline on the BodyParts3D FJ2810 reference mesh ($H = 172.0\text{ cm}$, $W = 42.0\text{ cm}$).

$$\text{dist}(P_{\text{point}}, \mathcal{V}_{\text{polyline}}) = \min_{v \in \mathcal{V}_{\text{polyline}}} \| P_{\text{point}} - v \|_2$$

---

## 3. COMPREHENSIVE 14-CHANNEL GEOMETRIC DEVIATION MATRIX

The table below documents the empirical geometric divergence across all 14 channels in the canonical baseline state:

| Channel Code | Channel Name | Bilateral Side | Control Points | Polyline Vertices | Min Dist (mm) | Mean Dist (mm) | Max Dist (mm) | Worst-Case Acupoint & Deviation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LU** | Lung | Right | 11 | 238 | 3.50 | 6.27 | **34.00** | `LU5` (34.0 mm) |
| **LU** | Lung | Left | 11 | 238 | 3.40 | 7.14 | **34.14** | `LU5` (34.1 mm) |
| **LI** | Large Intestine | Right | 20 | 304 | 3.49 | 8.18 | **67.55** | `LI4` (67.6 mm) |
| **LI** | Large Intestine | Left | 20 | 304 | 3.37 | 9.04 | **68.08** | `LI4` (68.1 mm) |
| **ST** | Stomach | Right | 45 | 564 | 3.49 | 5.45 | **43.98** | `ST36` (44.0 mm) |
| **ST** | Stomach | Left | 45 | 562 | 2.20 | 5.68 | **43.58** | `ST36` (43.6 mm) |
| **SP** | Spleen | Right | 21 | 462 | 3.49 | 3.50 | 3.51 | `SP14` (3.5 mm) |
| **SP** | Spleen | Left | 21 | 468 | 1.76 | 3.62 | 5.10 | `SP17` (5.1 mm) |
| **HT** | Heart | Right | 9 | 198 | 3.50 | 7.26 | **37.31** | `HT3` (37.3 mm) |
| **HT** | Heart | Left | 9 | 198 | 2.78 | 7.39 | **37.35** | `HT3` (37.4 mm) |
| **SI** | Small Intestine | Right | 19 | 416 | 3.49 | 3.50 | 3.51 | `SI3` (3.5 mm) |
| **SI** | Small Intestine | Left | 19 | 420 | 2.98 | 3.87 | 4.90 | `SI19` (4.9 mm) |
| **BL** | Bladder | Right | 67 | 858 | 3.49 | 5.35 | **39.23** | `BL13` (39.2 mm) |
| **BL** | Bladder | Left | 67 | 874 | 2.70 | 5.80 | **39.04** | `BL13` (39.0 mm) |
| **KI** | Kidney | Right | 27 | 396 | 3.49 | 3.50 | 3.51 | `KI11` (3.5 mm) |
| **KI** | Kidney | Left | 27 | 400 | 2.11 | 3.84 | 10.37 | `KI4` (10.4 mm) |
| **PC** | Pericardium | Right | 9 | 204 | 3.49 | 11.57 | **58.21** | `PC6` (58.2 mm) |
| **PC** | Pericardium | Left | 9 | 206 | 3.51 | 11.87 | **57.29** | `PC6` (57.3 mm) |
| **TE** | Triple Energizer | Right | 23 | 340 | 3.49 | 3.50 | 3.51 | `TE6` (3.5 mm) |
| **TE** | Triple Energizer | Left | 23 | 348 | 3.03 | 4.41 | 6.24 | `TE15` (6.2 mm) |
| **GB** | Gallbladder | Right | 44 | 766 | 3.49 | 5.12 | **58.69** | `GB21` (58.7 mm) |
| **GB** | Gallbladder | Left | 44 | 774 | 2.96 | 6.39 | **63.32** | `GB21` (63.3 mm) |
| **LR** | Liver | Right | 14 | 318 | 3.49 | 3.50 | 3.51 | `LR5` (3.5 mm) |
| **LR** | Liver | Left | 14 | 316 | 1.54 | 3.30 | 8.76 | `LR13` (8.8 mm) |
| **GV** | Governor Vessel | Midline | 29 | 348 | 2.99 | 6.19 | **34.33** | `GV24+` (34.3 mm) |
| **CV** | Conception Vessel| Midline | 24 | 242 | 3.49 | 3.93 | **13.85** | `CV22` (13.8 mm) |

---

## 4. DETAILED ROOT CAUSE BREAKDOWN

### 4.1. Error A: Static Polyline Pipeline Disconnect
- **Manifestation:** In `msk_therapy_os/spatial_resolver.py` (`resolve_meridians`), when `layer_mode == "canonical"`, the resolver directly outputs `p_raw.get("surface_vertices")` from `acupuncture_3d.json`.
- **Root Cause:** In earlier development iterations, static spline polylines were digitized on a generic unrigged 3D avatar that did not match the BodyParts3D FJ2810 coordinate space. When P9.1/P9.2 registered acupoints like `LI4`, `PC6`, `GB21`, and `LU5` to true anatomical bony landmarks, the meridian paths were never regenerated to pass through these coordinates.
- **Visual Impact:** A user clicking on `LI4` sees the point located precisely on the second metacarpal bone, but the Large Intestine channel runs through empty air 6.7 cm away.

### 4.2. Error B: Bilateral Coordinate Flipping & Laterality Flaws
- **Manifestation:** Left-side meridians in `spatial_resolver.py` and `meridians.js` rely on mirroring $X \to -X$.
- **Root Cause:** While the human body exhibits macro bilateral symmetry, coordinate mirroring fails when:
  1. Asymmetrical posture kinematics occur (e.g. right arm raised $45^\circ$, left arm neutral). Mirroring right-side arm vertices without re-evaluating left-side joint angles results in deformed, disconnected limbs on the left side.
  2. Surface normals are inverted: a pure reflection transforms a right-handed tangent frame into a left-handed frame, reversing normal directions unless proper cross-product parity is enforced.

### 4.3. Error C: All-or-Nothing Occlusion Thresholding
- **Manifestation:** Meridians abruptly disappear when rotating the 3D model, or show rear segments shining through solid torso mesh.
- **Root Cause:** In `msk_therapy_os/static/atlas/meridians.js` (lines 1139-1147):
  ```javascript
  let facingCount = 0;
  let sampleCount = 0;
  const step = Math.max(1, Math.floor(poly.length / 16));
  for (let i = 0; i < poly.length; i += step) {
    if (isFacingCamera(poly[i], r)) facingCount++;
    sampleCount++;
  }
  const pathFacing = sampleCount > 0 && (facingCount / sampleCount) >= 0.35;
  if (!r.xray && !pathFacing) continue;
  ```
  1. The loop tests only 16 points along polylines consisting of 300 to 800 vertices.
  2. `isFacingCamera` is evaluated with `normal = null`, falling back to a crude 2D horizontal plane test: `h = pos[0]*dx + pos[2]*dz`.
  3. If less than 35% of samples face the camera, the entire polyline is discarded. For wrapping channels (`BL`, `GB`, `ST`), orbiting across the $35\%$ threshold causes the entire line to vanish in one frame.
  4. Conversely, if 35% pass, the remaining 65% of back-facing segments are rendered directly over the front of the body with full opacity.

### 4.4. Error D: Source-to-Target Kinematic Shearing
- **Manifestation:** Moving joints causes meridians to detach from limbs or pierce the torso.
- **Root Cause:** In `spatial_resolver.py` (lines 653-673):
  ```python
  if y > 1.50:
      v_reg = "head_neck"
  elif y > 0.85:
      v_reg = "arm" if abs(v[0]) > 0.16 else "torso"
  else:
      v_reg = "lower_extremity"
  ```
  1. Arm detection using `y > 0.85` and `abs(x) > 0.16` classifies proximal forearm and shoulder joints arbitrarily based on height rather than skeletal hierarchy.
  2. In abduction/flexion poses, vertices on the arm are rotated around the shoulder joint without considering elbow flexion, while points near the elbow are split between different coordinate frames.
  3. Under $45^\circ$ shoulder abduction $+ 45^\circ$ elbow flexion, the distance between `LI4` and the LI polyline escalates from 67.55 mm to **91.12 mm**.

---

## 5. REMEDIATION STRATEGY & ARCHITECTURAL REQUIREMENTS (P9.3)

To definitively solve these root causes:
1. **Dynamic Point-Anchored Corridor Reconstruction:** Implement `MeridianSurfacePathEngine` that reconstructs the 14 channels by connecting sequentially resolved control points (`resolved_points`), using centripetal Catmull-Rom splines projected directly onto the body surface envelope.
2. **Skeletal Hierarchy Binding:** Bind every polyline segment to specific anatomical bone segments (`hand`, `forearm`, `upper_arm`, `shoulder_girdle`, `torso`, `thigh`, `shank`, `foot`) matching the kinematic chains of its bounding control points.
3. **Per-Vertex Surface Normal Propagation:** Compute outward-facing unit surface normals $\vec{N}$ for every generated vertex on the meridian path.
4. **Segment-Level WebGL/SVG Depth & Occlusion:** Refactor `meridians.js` to render paths segment-by-segment:
   - Front-facing segments ($\vec{N} \cdot \vec{V}_{\text{camera}} > 0$): full opacity with optional glow.
   - Rear-facing / occluded segments ($\vec{N} \cdot \vec{V}_{\text{camera}} \le 0$): attenuated depth styling (e.g. 15% opacity or dashed) or hidden according to display settings.
   - Zero whole-channel disappearance.

---

*End of Forensic Audit Report.*
