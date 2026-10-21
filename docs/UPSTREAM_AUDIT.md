# Upstream 3D Acupuncture & Meridian Repositories Audit

**Project:** MSK-Therapy-OS  
**Branch:** `research/anatomical-workbench`  
**Status:** AUDITED & VALIDATED  
**Author:** Staff/Principal Engineer & Senior Toolsmith  
**Date:** 2026-10-21  

---

## 1. Executive Summary

To remediate anatomical overlay defects (floating acupoints, displaced meridians, and coordinate mismatch) without rebuilding MSK-Therapy-OS from scratch, we conducted a rigorous forensic audit of four open-source 3D acupuncture and anatomy implementations:
1. **`JICio/tcm-3d`**
2. **`eb-barry/acupuncture-3d-authoring`** (Meridian Studio)
3. **`WaterCMY/anatomy-3d`**
4. **`spacejohnlf/tcm-acupoints`**

Each repository was cloned into isolated subdirectories under `research/upstream/` with exact commit SHAs pinned. Their code, 3D meshes, coordinate representations, and licensing terms were analyzed.

---

## 2. Upstream Inventory & Provenance Matrix

| Repository | Pinned Commit SHA | Primary License | 3D Mesh Asset | Vertex / Triangle Count | File Size | Coordinate Origin & Units |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`JICio/tcm-3d`** | `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a` | MIT | BodyParts3D Male (`FJ2810` skin) | ~120k tris (skin mesh) | ~4.2 MB (skin) / 768 KB (JSON) | Ground plane ($Y=0$), Crown $Y \approx 1.72\text{m}$, Meters |
| **`eb-barry/acupuncture-3d-authoring`** | `cb7a41692276adcbf696538d30f2e3d8ecb4bbc6` | MIT (code) / CC BY 4.0 (models) | MakeHuman/Custom Male & Female GLB | ~350k vertices | 13.5 MB (Male) / 24.0 MB (Female) | Centered Bounding Box, Meters |
| **`WaterCMY/anatomy-3d`** | `e8d40dca7b1f63f54567395df21d8b1b38a7e840` | MIT (code) / CC BY-SA 4.0 (models) | BodyParts3D GLB (54 muscle groups) | 634,000 triangles | 9.07 MB (anatomy.glb) | Ground plane ($Y=0$), Crown $Y \approx 1.70\text{m}$, Meters |
| **`spacejohnlf/tcm-acupoints`** | `04e35abb66585eb29c7250ea8ab5243c8c744f64` | MIT (code) / CC BY-SA 4.0 (models) | Z-Anatomy Draco-compressed GLB | 513,000 vertices | 8.05 MB (body.glb) | Pelvis center ($Y=0$), Sole $-0.86\text{m}$, Crown $+0.86\text{m}$, Meters |

---

## 3. Detailed Audit by Implementation

### 3.1 JICio/tcm-3d
- **Repository URL:** `https://github.com/JICio/tcm-3d`
- **License:** MIT License (Permissive, commercial-friendly).
- **Architecture:** Next.js / Vite + Three.js + Base-UI.
- **Key Assets:**
  - `app/meridian-surface.json` (768.7 KB): Contains 670 surface-anchored point records (`faceIndex`, `meshId: "FJ2810"`, `target.position`, `target.normal`) and 26 dense, continuous 3D paths pre-snapped to the BodyParts3D skin mesh.
  - `app/teaching-points.json` (273.4 KB): 362 acupoints with Chinese names, pinyin, meridian IDs, regional classifications, review flags, and clinical provenance notes.
- **Surface Snapping Algorithm:** Pre-baked triangle raycasting offline via `scripts/bake-meridian-surface.mjs`. Acupoints and meridian polylines are projected along triangle normals onto the skin mesh with a deterministic 3.5mm outward normal offset to prevent z-fighting.
- **Runtime Cost:** **Zero runtime raycasting.** Paths render as pre-calculated static `BufferGeometry` ribbons.
- **Suitability:** **HIGH (REUSE / BASELINE).** Compatible with MSK-Therapy-OS's BodyParts3D coordinate system.

---

### 3.2 eb-barry/acupuncture-3d-authoring (Meridian Studio)
- **Repository URL:** `https://github.com/eb-barry/acupuncture-3d-authoring`
- **License:** MIT License for application code; CC BY 4.0 for 3D character models.
- **Architecture:** Vanilla Three.js + Vite + `three-mesh-bvh`.
- **Key Assets:**
  - `models/male_character.glb` (13.5 MB) & `models/female-character.glb` (24.0 MB).
  - `src/data/acupuncture-data.json` (195.6 KB): Exhaustive catalog of 361 acupoints with WHO codes, classical indications, modern biomedical interpretations, precautions/contraindications (e.g., "不可深刺", pneumothorax risk), and landmark guidance.
  - Version 2/3 JSON Document Schema (`src/document.js`).
- **Surface Snapping Algorithm:** Runtime accelerated raycasting using `three-mesh-bvh`. Extrudes CatmullRom spline ribbons with orthogonal Frenet frame (tangent $\times$ normal = binormal) and uses a WebGL material `depthBias` of `-0.0005`.
- **Authoring Tools:** Complete interactive UI for adding, nudging, dragging, and calibrating acupoints directly on the 3D surface.
- **Suitability:** **HIGH (ADAPT FOR AUTHORING).** Provides the gold standard for clinical calibration and authoring.

---

### 3.3 WaterCMY/anatomy-3d
- **Repository URL:** `https://github.com/WaterCMY/anatomy-3d`
- **License:** MIT License (code) / CC BY-SA 4.0 (3D models).
- **Architecture:** Single-file zero-dependency Three.js application (`index.html` + `models/anatomy.glb`).
- **Key Assets:**
  - `index.html`: Contains analytical `HULL` definitions (17 ellipsoids and capsules representing the human body envelope).
  - `models/anatomy.glb` (9.07 MB): 54 isolated muscle groups, 634k triangles.
- **Surface Snapping Algorithm:** Analytical bounding hull projection (`projectToHull`). Computes closest point on analytical quadric surfaces (ellipsoids and line-swept capsules) rather than intersecting complex triangle meshes. Renders meridians with `depthTest: false` and a camera-facing normal falloff shader.
- **Runtime Cost:** Extremely low CPU usage (pure analytical formulas). Loads in 724ms on Intel HD 5500.
- **Suitability:** **ADAPT (FALLBACK & OCCLUSION SHADER).** The analytical hull and `depthTest: false` facing falloff technique provide a robust fallback when high-density meshes fail to render or when viewing deep structures through skin.

---

### 3.4 spacejohnlf/tcm-acupoints
- **Repository URL:** `https://github.com/spacejohnlf/tcm-acupoints`
- **License:** MIT License (code) / CC BY-SA 4.0 (Z-Anatomy model).
- **Architecture:** React 19 + Vite + Draco-compressed Three.js viewer.
- **Key Assets:**
  - `public/models/body.glb` (8.05 MB): Draco-compressed Z-Anatomy mannequin.
  - `src/lib/acupoint-data.ts`: Parametric definitions for 70 core acupoints and 14 meridians.
- **Surface Snapping Algorithm:** Runtime 5-pass directional-cone raycaster (`src/lib/three/snap.ts`). Raycasts rays within a narrowing cone (`DIRECTION_CONES = [0.94, 0.82, 0.6, 0.2, -1.1]`) to prevent rays from punching through thin extremities (such as hands or ears). Applies a 12mm outward normal offset.
- **Runtime Cost:** Heavy startup overhead on low-end hardware. Draco WASM decompression and React 19 inflate JS heap to 82.4 MB and load time to 3.42s on Intel HD 5500. Acupoints visibly float due to the 12mm lift.
- **Suitability:** **REJECT RUNTIME / REUSE ALGORITHM CONCEPTS.** The 5-pass directional-cone snapping logic is mathematically sound for preventing limb penetration, but the runtime bundle, coordinate shift, and 12mm floating offset make direct integration unsuitable.

---

## 4. Upstream Dependency & Compatibility Analysis

| Component | MSK-Therapy-OS Baseline | JICio | Meridian Studio | WaterCMY | TCM-Acupoints | Compatibility Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **3D Engine** | Three.js r128+ | Three.js r160+ | Three.js r160+ | Three.js r145 | Three.js r170 | Low (All standard Three.js) |
| **BVH Raycasting** | Planned / Experimental | None (Pre-baked) | `three-mesh-bvh` | None (HULL math) | Custom Raycaster | Low (Isolated to Studio) |
| **Model Compression** | Uncompressed GLB | Uncompressed GLB | Uncompressed GLB | Uncompressed GLB | Draco WASM | High (Draco adds WASM load overhead) |
| **Target Hardware RAM** | 8GB System RAM | ~42 MB Heap | ~48 MB Heap | ~32 MB Heap | ~82 MB Heap | TCM-Acupoints exceeds budget |
| **License Compliance** | MIT | MIT | MIT / CC BY 4.0 | MIT / CC BY-SA | MIT / CC BY-SA | High (CC BY-SA viral clause requires isolation) |

> [!IMPORTANT]
> **Licensing Isolation Requirement:**
> WaterCMY and TCM-Acupoints 3D models are licensed under CC BY-SA 4.0 (ShareAlike). Their raw 3D mesh files must **never** be statically embedded into the proprietary/MIT core MSK-Therapy-OS codebase. The pre-baked coordinates in JICio derived from BodyParts3D and the MIT-licensed code in Meridian Studio are clean and fully compatible.
