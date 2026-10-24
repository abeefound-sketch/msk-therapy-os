# P9.2 FORENSIC AUDIT: ATLAS DYNAMIC GEOMETRY INTEGRATION & MERIDIAN SURFACE CONFORMITY

**Audit Date:** 2026-10-24  
**Project:** MSK-Therapy-OS (Musculoskeletal Therapy Operating System)  
**Branch:** `feat/p9.2-dynamic-atlas-integration`  
**Baseline Git HEAD:** `2e7fbd7` (feat(p9.1): repository reconciliation, independent geometric validation and anatomical error matrix)  
**Lead Investigators:** Principal WebGL Engineer, Computational Anatomy Engineer, Python Backend Architect, QA Automation Lead  

---

## 1. EXECUTIVE SUMMARY & FORENSIC FINDINGS

The MSK-Therapy-OS P9 and P9.1 milestones established rigorous computational anatomy modules:
1. `anatomical_registration.py`: Umeyama rigid/similarity alignment, pure-Python 3x3 SVD, residual error calculation.
2. `landmark_registry.py`: FMA-mapped anatomical landmark catalog on BodyParts3D FJ2810.
3. `cun_scaling.py`: WHO 2008 proportional B-cun/F-cun segment scaling adapted to patient anthropometry.
4. `pose_rigging.py`: Rodrigues kinematic joint transforms, physiological ROM monitoring, `UNCERTAIN_POSTURE_OFFSET` emission, and guarded surface raycast bounding.

However, a forensic audit of the frontend Atlas Viewer (`msk_therapy_os/static/atlas/meridians.js`) and backend HTTP routes (`msk_therapy_os/server.py`) reveals a critical integration gap: **The Atlas Viewer remains almost entirely decoupled from the dynamic positioning engines.** 

Specifically:
- The viewer loads a static JSON file (`acupuncture_3d.json`) on initialization.
- The layer mode switcher (`currentP9LayerMode`) is purely cosmetic: changing the dropdown updates the badge text in the UI but does not alter the coordinates passed to the renderer.
- The QA Inspector displays fabricated defaults (such as `< 0.5 mm` or `1.2 mm` residual error and synthetic B-cun strings) when data is missing.
- Meridian paths are rendered from pre-baked static polylines that do not recalculate when points move under morphology or pose variations.

This document identifies root causes, exact code locations, and specifies the authoritative remediation pipeline.

---

## 2. ROOT CAUSE AUDIT

### Root Cause A: Static Data Dependency
- **File:** `msk_therapy_os/static/atlas/meridians.js` (lines 443–473) & `msk_therapy_os/server.py` (lines 852–878)
- **Defect:** `meridians.js` issues a single `GET /api/acupuncture-3d`. On the backend, `/api/acupuncture-3d` reads `msk_therapy_os/static/atlas/data/acupuncture_3d.json` and overlays SQLite custom points.
- **Analysis:**
  - In `acupuncture_3d.json`, 350 out of 362 points are labeled with historical status `SURFACE_REGISTERED_FJ2810`. Only 11 are marked `VERIFIED_ANATOMICAL_ANCHOR` and 1 is marked `UNCERTAIN_POSTURE_OFFSET`.
  - When the client renders points, it directly reads `pt.position` from this static structure.
  - The dynamic P9 endpoints (`/api/registration/align`, `/api/cun/adapt`, `/api/pose/evaluate`) are never queried by `meridians.js` during standard viewing, layer switching, or model interaction.
- **Remediation:** Introduce an authoritative spatial resolution service `AnatomicalSpatialResolver` and endpoint `POST /api/atlas/geometry/resolve` that computes and returns authoritative coordinates across all supported layers.

---

### Root Cause B: Layer Switch Lacks Geometric Effect
- **File:** `msk_therapy_os/static/atlas/meridians.js` (lines 36, 2092–2096, 2220–2228)
- **Defect:** 
  ```javascript
  // Line 36
  let currentP9LayerMode = 'canonical';

  // Lines 2222-2227
  selP9LayerMode.addEventListener('change', (e) => {
    currentP9LayerMode = e.target.value;
    const b = document.getElementById('p9LayerBadge');
    if (b) b.textContent = currentP9LayerMode.toUpperCase();
    render(true);
  });
  ```
- **Analysis:**
  - Inside `render()` (lines 887–1380), the variable `currentP9LayerMode` is never checked.
  - The marker iteration loop (lines 1048–1101) directly projects `pt.position` regardless of whether `currentP9LayerMode` is set to `canonical`, `legacy_raycast`, `upstream_raw`, or `pose_adjusted`.
  - As a result, users switching between Canonical, Legacy, Upstream, and Pose modes see zero change in point positions or meridian geometry.
- **Remediation:** Wire `currentP9LayerMode` to the dynamic resolution cache. In each layer mode, render the verified layer-specific coordinates (`resolved_world_position`) and display distinct visual indicators and confidence flags.

---

### Root Cause C: QA Inspector Contains Fabricated Assumptions
- **File:** `msk_therapy_os/static/atlas/meridians.js` (lines 1776–1815)
- **Defect:**
  ```javascript
  // Lines 1790-1793
  const anchorName = pt.anchor_structure || 'BodyParts3D FJ2810 Skin Mesh';
  const fmaText = pt.fma_id ? `[${pt.fma_id}]` : '[FMA:7163 Human Body]';
  const errorMm = pt.residual_error_mm !== undefined ? `${pt.residual_error_mm.toFixed(1)} mm` : (isAnchor ? '< 0.5 mm' : '1.2 mm');
  const bCunRule = pt.bcun_rule || (pt.region === 'arm' ? 'Forearm 12 B-cun' : (pt.region === 'leg' ? 'Leg 16 B-cun' : 'Torso 8 B-cun'));
  ```
- **Analysis:**
  - When `pt.residual_error_mm` is missing, the UI falsely claimed `< 0.5 mm` (if anchor) or `1.2 mm` (if not).
  - When `pt.bcun_rule` is missing, the UI synthesized rules based purely on coarse region strings (`Forearm 12 B-cun`, `Leg 16 B-cun`, `Torso 8 B-cun`).
  - When `pt.fma_id` is missing, it populated `[FMA:7163 Human Body]`.
  - This violates clinical documentation safety: displaying fictitious tolerances presents an illusion of verification for unmeasured points.
- **Remediation:**
  - Remove all hard-coded numerical fallback strings.
  - If a metric is not calculated or audited, display `None / Not Measured` or `UNKNOWN`.
  - Clearly separate status into:
    1. *Geometrically Registered* (physically snapped to FJ2810 skin triangle).
    2. *Anatomically Referenced* (anchored to documented FMA skeletal/tissue landmark).
    3. *Expert Reviewed* (signed off by verified clinical reviewer).
    4. *Clinically Validated* (empirical clinical measurement).

---

### Root Cause D: Meridian Paths Are Pre-Baked Polylines
- **File:** `msk_therapy_os/static/atlas/meridians.js` (lines 981–1010)
- **Defect:**
  ```javascript
  for (const p of m.paths || []) {
    const pts = p.surface_vertices || p.points;
    if (!pts || pts.length < 2) continue;
    // Projects pts directly
  }
  ```
- **Analysis:**
  - Meridians are rendered by iterating through `p.surface_vertices` loaded from `acupuncture_3d.json`.
  - These vertices represent static paths generated on a rest-pose mesh.
  - When acupoint positions shift (e.g., when scaled by Morphology Studio or when joint angles flex), the meridian line remains glued to the old coordinates, leading to complete visual and topological disconnection between the acupoint markers and the meridian pathway.
  - Furthermore, without continuous surface projection, polylines risk clipping inside concave mesh regions or penetrating bone structures.
- **Remediation:**
  - Implement a dynamic meridian surface conformity pipeline:
    `Acupoint Anchors → Segment Constraints → Mesh Surface Projection → Dynamic Polyline`.
  - When control points move, reconstruct the connecting path along the skin surface using mesh snapping (`snapToSkinSurface` or geodesic surface interpolation).
  - Explicitly display a disclosure tag: *"Meridian pathways are educational visualization approximations constrained to the skin surface."*

---

## 3. AUDIT MATRIX: CURRENT VS TARGET ARCHITECTURE

| Component | Current State (P9.1 Baseline) | Target State (P9.2 Implementation) |
| :--- | :--- | :--- |
| **Data Flow** | Static `acupuncture_3d.json` loaded once at startup. | Dynamic queries to `POST /api/atlas/geometry/resolve` driven by `AtlasSpatialState`. |
| **Layer Switch** | Updates UI badge only; zero coordinate changes. | Dynamically swaps coordinates among Canonical, Legacy, Upstream, and Pose layers. |
| **Residual Error** | Fabricated `< 0.5 mm` or `1.2 mm` strings. | Actual calculated RMS/residual or explicit `UNVERIFIED / NOT MEASURED`. |
| **B-Cun Rules** | Coarse fallback text by body region. | Exact WHO 2008 segment ID and calculated mm/cun ratio from `CunScalingEngine`. |
| **Pose Sensitivity** | Evaluated only in isolation via `/api/pose/evaluate`. | Full-scene spatial resolution emits `UNCERTAIN_POSTURE_OFFSET` with visual warnings. |
| **Meridian Geometry** | Static JSON vertex arrays. | Dynamic surface-conforming polylines updating with anchor coordinates. |
| **Bilateral Consistency**| Naive mirroring `[-x, y, z]` for positive X coordinates. | True independent bilateral instances with distinct left/right anatomical anchors. |

---

## 4. ACTION PLAN & VERIFICATION GATES

1. **Phase 1 (Backend Pipeline):**
   - Create `msk_therapy_os/spatial_resolver.py` (`AnatomicalSpatialResolver`).
   - Implement `POST /api/atlas/geometry/resolve` in `msk_therapy_os/server.py`.
   - Incorporate `AnatomicalRegistrationEngine`, `CunScalingEngine`, `PoseKinematicsRig`, and `GuardedSurfaceProjector`.
2. **Phase 2 (Frontend Integration):**
   - Refactor `msk_therapy_os/static/atlas/meridians.js` to manage `AtlasSpatialState`.
   - Implement asynchronous resolution with generation counters to prevent race conditions.
   - Implement layer-dependent coordinate selection in `render()`.
3. **Phase 3 (Surface-Conforming Meridians):**
   - Dynamically recompute meridian segments connecting moving acupoints.
   - Project intermediate path points to skin mesh surface normals.
4. **Phase 4 (QA Inspector Overhaul):**
   - Purge all fabricated strings. Display authentic provenance and measurement states.
5. **Phase 5 (Testing & Benchmarking):**
   - Unit and integration tests for `AnatomicalSpatialResolver`.
   - Playwright browser tests verifying real geometric displacement across layers, morphology, and pose.
   - Full regression across all 204 baseline tests.
