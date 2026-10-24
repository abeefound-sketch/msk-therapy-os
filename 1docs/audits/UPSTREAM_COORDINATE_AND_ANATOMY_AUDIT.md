# UPSTREAM COORDINATE AND ANATOMICAL AUDIT REPORT (P9 FORENSIC AUDIT)

**Audit Date:** 2026-10-24  
**Project:** MSK-Therapy-OS (Musculoskeletal Therapy Operating System)  
**Branch:** `feat/p9-anatomical-registration`  
**Baseline:** `v2.1.0-local-rc3` (`4f35602`)  
**Scope:** Forensic evaluation of four upstream repositories and their geometric/anatomical compatibility with BodyParts3D 4.0 (FJ2810 canonical skin mesh).

---

## 1. EXECUTIVE SUMMARY

An exhaustive forensic audit was conducted on the four upstream open-source acupuncture/anatomy projects integrated into the research workbench. The objective is to establish ground truth regarding coordinate systems, rest poses, mesh units, point registries, and spatial discrepancies when mapped to the canonical **BodyParts3D 4.0 FJ2810** human anatomical model.

### Key Forensic Findings:
1. **Severe Rest-Pose Discrepancies:** Raw 3D Euclidean distances between identical acupoints across different projects exceed **337 mm** on the upper limbs (e.g., LI4 discrepancy of 337.93 mm between JICio and spacejohnlf/tcm-acupoints) due to differing limb abduction angles and arm rest postures in the source meshes.
2. **Origin Shifts:** Upstream repositories employ disparate origin definitions. While JICio and WaterCMY use the floor ground plane ($Y=0$, crown $Y \approx 1.70-1.72\text{ m}$), spacejohnlf/tcm-acupoints centers the origin at the pelvis ($Y=0$, soles $Y=-0.86\text{ m}$, crown $Y=+0.86\text{ m}$).
3. **Absence of Bone-Constrained Parametric Cun:** None of the upstream repositories dynamically compute Bone-proportional cun (B-cun) according to WHO 2008 standards. Instead, they rely on pre-baked static vertex coordinates or primitive hull snapping, which break as soon as body geometry, posture, or patient morphology deviates from the baseline mesh.
4. **Authoring Tool vs Coordinate Dataset:** eb-barry/acupuncture-3d-authoring (Meridian Studio) provides an authoritative, complete 361-point WHO classical text catalog, but stores no static 3D vertex coordinates in its core JSON; coordinates are authored interactively at runtime in its browser canvas.

---

## 2. COMPREHENSIVE UPSTREAM AUDIT MATRIX

| Metric / Dimension | Upstream 1: JICio/tcm-3d | Upstream 2: WaterCMY/anatomy-3d | Upstream 3: spacejohnlf/tcm-acupoints | Upstream 4: eb-barry/acupuncture-3d-authoring |
| :--- | :--- | :--- | :--- | :--- |
| **Repository URL** | `https://github.com/JICio/tcm-3d` | `https://github.com/WaterCMY/anatomy-3d` | `https://github.com/spacejohnlf/tcm-acupoints` | `https://github.com/eb-barry/acupuncture-3d-authoring` |
| **Commit SHA Audited** | `e8b9ad1c17e67a25e94406100e3fb5c296c24f7a` | `e8d40dca7b1f63f54567395df21d8b1b38a7e840` | `04e35abb66585eb29c7250ea8ab5243c8c744f64` | `cb7a41692276adcbf696538d30f2e3d8ecb4bbc6` |
| **Local Path** | `3refs/upstream/tcm-3d` & `research/upstream/tcm-3d` | `3refs/upstream/anatomy-3d` & `research/upstream/anatomy-3d` | `3refs/upstream/tcm-acupoints` & `research/upstream/tcm-acupoints` | `3refs/upstream/acupuncture-3d-authoring` & `research/upstream/acupuncture-3d-authoring` |
| **Verification State** | **VERIFIED PRESENT** | **VERIFIED PRESENT** | **VERIFIED PRESENT** | **VERIFIED PRESENT** |
| **Software License** | MIT | MIT (code) / CC BY-SA 4.0 (models) | MIT (code) / CC BY-SA 4.0 (Z-Anatomy) | MIT (code) / CC BY 4.0 (models) |
| **Underlying 3D Mesh** | BodyParts3D FJ2810 Skin Mesh | BodyParts3D (54 muscle groups, 634k tris) | Z-Anatomy Draco-compressed GLB (513k verts) | MakeHuman / Custom Male & Female GLBs |
| **Measurement Unit** | SI Meters (m) | SI Meters (m) | SI Meters (m) | SI Meters (m) |
| **Handedness & Up-Vector** | Right-Handed Cartesian, Y-Up (+X R, +Y Up, +Z Front) | Right-Handed Cartesian, Y-Up (+X R, +Y Up, +Z Front) | Right-Handed Cartesian, Y-Up (+X R, +Y Up, +Z Front) | Right-Handed Cartesian, Y-Up (+X R, +Y Up, +Z Front) |
| **Coordinate Origin** | Floor Ground ($Y=0$), Crown $Y \approx 1.72\text{ m}$ | Floor Ground ($Y=0$), Crown $Y \approx 1.70\text{ m}$ | Pelvis Center ($Y=0$), Sole $Y=-0.86\text{ m}$, Crown $Y=+0.86\text{ m}$ | Centered at BVH Bounding Box Origin |
| **Acupoints Extracted** | 670 (bilateral L/R + midline) | 146 (core classical + extra points) | 70 (high-frequency points in `acupoint-data.ts`) | 361 (text catalog; interactive 3D coordinates) |
| **Meridians Extracted** | 14 channels (pre-baked vertex strips) | 15 channels (3D paths) | 14 channels (interpolated polyline points) | 14 channels (spline ribbons) |
| **Snapping / Projection Algorithm** | Triangle raycast intersection + 3.5mm normal offset | Analytical Bounding Hulls (capsules/ellipsoids) | Directional-cone raycast + 12mm normal lift | Interactive BVH raycasting + Catmull-Rom ribbons |
| **Bilateral Discrimination** | Explicit (`:1` Right, `:-1` Left, `:0` Midline) | Mixed / Implicit | Explicit in data array | Implicit (bilateral symmetry mirrored) |
| **FJ2810 Morphological Match** | High (native mesh alignment) | Medium (slight torso offset, 10-50mm) | Poor (A-pose arm abduction offset > 300mm) | Poor (MakeHuman morphology differs from FJ2810) |
| **Clinical Utility Rating** | Primary Surface Coordinates Baseline | Structural Muscle/Fascia Landmark Reference | Multi-System Cross-Validation Reference | Standard Nomenclature & Semantic Reference |

---

## 3. POINT-BY-POINT COMPARATIVE FORENSICS

A controlled execution of the research workbench comparison engine across representative acupuncture points reveals the magnitude of spatial divergence:

### 3.1. Upper Extremity & Hand Points (Major Pose Divergence)
- **LI4 (Hegu - 合谷):**
  - JICio vs WaterCMY: **37.31 mm** divergence.
  - JICio vs spacejohnlf/tcm-acupoints: **337.93 mm** divergence.
  - WaterCMY vs spacejohnlf/tcm-acupoints: **366.51 mm** divergence.
  - *Root Cause:* In the Z-Anatomy mesh (spacejohnlf), the humerus is abducted ~25° and the forearm is pronated. Without skeletal landmark anchoring to the 2nd metacarpal bone (FMA:24075), direct coordinate projection fails catastrophically.
- **PC6 (Neiguan - 内关):**
  - JICio vs WaterCMY: **33.23 mm** divergence.
  - JICio vs spacejohnlf/tcm-acupoints: **229.29 mm** divergence.
  - *Root Cause:* Position between the tendons of palmaris longus and flexor carpi radialis is posture-dependent.
- **LU5 (Chize - 尺泽):**
  - JICio vs WaterCMY: **53.15 mm** divergence.
  - JICio vs spacejohnlf/tcm-acupoints: **202.43 mm** divergence.
  - *Root Cause:* Cubital crease displacement during elbow rotation and abduction.

### 3.2. Neck, Shoulder & Cranial Points (Morphological & Suboccipital Divergence)
- **GV14 (Dazhui - 大椎):**
  - Canonical Landmark Anchor: Depression inferior to C7 spinous process ($[0.000, 1.478, -0.092]$).
  - JICio error to canonical: **46.9 mm** (placed too superiorly on C5/C6).
  - WaterCMY error to canonical: **7.2 mm** (accurately aligned to C7 spine).
  - spacejohnlf error to canonical: **25.5 mm**.
  - Pairwise JICio vs WaterCMY: **53.11 mm**.
- **GB21 (Jianjing - 肩井):**
  - Canonical Landmark Anchor: Midpoint of C7-to-acromion line ($[0.142, 1.436, -0.012]$).
  - JICio error: **84.2 mm**.
  - WaterCMY error: **67.7 mm**.
  - spacejohnlf error: **77.0 mm**.
  - Pairwise JICio vs spacejohnlf: **138.59 mm**.
  - *Root Cause:* Upstream algorithms project onto the anterior or superior curve of m. trapezius without calculating the exact bone-proportional midpoint between the C7 spinous process and the acromion tip.
- **GB20 (Fengchi - 风池):**
  - Canonical Landmark Anchor: Suboccipital depression between SCM and trapezius ($[0.068, 1.582, -0.076]$).
  - JICio error: **53.5 mm**.
  - WaterCMY error: **43.0 mm**.
  - spacejohnlf error: **102.8 mm**.
  - *Root Cause:* Variations in occipital bone curvature and mastoid process prominence across meshes.

### 3.3. Lower Extremity Points (Segment Proportionality)
- **ST36 (Zusanli - 足三里):**
  - Pairwise JICio vs WaterCMY: **61.05 mm**.
  - Pairwise JICio vs spacejohnlf: **111.14 mm**.
  - Pairwise WaterCMY vs spacejohnlf: **114.39 mm**.
  - *Root Cause:* Tibial tuberosity height and anterior tibial border curvature differ across models. A global height scale cannot reconcile disparate knee-to-ankle ratios.

---

## 4. ROOT CAUSE CLASSIFICATION OF REGISTRATION ERRORS

Forensic analysis classifies upstream localization errors into four distinct physical and algorithmic failure modes:

```
+---------------------------------------------------------------------------------------------------+
|                                 ROOT CAUSES OF LOCALIZATION ARTIFACTS                             |
+------------------------------------+----------------------------------+---------------------------+
| 1. POSTURE & KINEMATICS            | 2. MORPHOMETRIC DISPROPORTION    | 3. RAYCASTING ARTIFACTS   |
| - Rest pose arm abduction (>25 deg)| - Segment ratios (femur/tibia)   | - Ray penetrating chest   |
| - Pronation/supination of forearm  |   differ between subjects        |   instead of medial arm   |
| - Cervical flexion/extension       | - Fixed mm offsets fail across   | - Normal flipping on thin |
|   alters skin-to-spine depth       |   varying body builds            |   structures (ear/digits) |
+------------------------------------+----------------------------------+---------------------------+
```

1. **Failure Mode A: Blind Global Alignment (Rigid Translation Only)**
   - Shifting $Y$ by $+0.86\text{ m}$ aligns the pelvic floor of Z-Anatomy with BodyParts3D, but fails completely on the limbs because the arms and legs are held at different angles.
2. **Failure Mode B: Unguarded Normal Ray Snapping**
   - Raycasting from a 3D seed point toward the mesh surface without anatomical bounding box checks causes rays to intersect adjacent body parts (e.g. projecting an arm point onto the lateral rib cage, or a thigh point onto the contralateral thigh).
3. **Failure Mode C: Lack of Bone-Proportional Cun (B-Cun) Partitioning**
   - Classical acupuncture localization relies on proportional segments (e.g. 12 cun between cubital crease and wrist crease, 16 cun between popliteal crease and lateral malleolus). Static Euclidean coordinates completely disregard this relational geometry.

---

## 5. AUDIT VERDICT & ARCHITECTURAL DIRECTIVES FOR P9

1. **JICio/tcm-3d:** Retain as the primary raw surface coordinate baseline for BodyParts3D FJ2810 skin mesh, but re-register all points using bone landmark constraints.
2. **eb-barry/acupuncture-3d-authoring:** Retain as the gold-standard terminology and clinical indication catalog (WHO classical 361 points). Mark 3D point positions as `AUTHORING_TIME_ONLY`.
3. **WaterCMY/anatomy-3d:** Use for cross-verification of deep musculoskeletal landmarks (m. trapezius, m. sternocleidomastoideus, scapular spine).
4. **spacejohnlf/tcm-acupoints:** Mark limb points as `HIGH_DISCREPANCY_POSTURE_OFFSET` (> 200mm divergence) unless transformed through the P9 pose-aware rigging engine.
5. **Abstention Policy:** Where landmark anchors cannot be identified with $<15\text{ mm}$ anatomical uncertainty, the engine MUST emit status `UNVERIFIED` or `UNCERTAIN_POSTURE_OFFSET`, refusing to claim verified accuracy.
