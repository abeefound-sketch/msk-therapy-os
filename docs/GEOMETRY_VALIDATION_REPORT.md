# Geometry Validation Report: Surface Adherence & Landmark Concordance

**Project:** MSK-Therapy-OS  
**Branch:** `research/anatomical-workbench`  
**Status:** VERIFIED EVIDENCE REPORT  
**Author:** Independent Quality Auditor & Tools Engineer  
**Date:** 2026-10-21  

---

## 1. Executive Summary

This report delivers the quantitative validation results produced by the `research.workbench validate` and `research.workbench compare` engines across all four upstream repositories. Every acupuncture point and meridian pathway was evaluated against:
1. **Skin Boundary Adherence:** Measurement of normal distance from the 3D surface mesh. Points $>5.0\text{mm}$ are flagged as `FLOATING`; points $<-2.0\text{mm}$ are flagged as `PENETRATING`.
2. **Pathway Continuity:** Measurement of inter-vertex step distances along meridian polylines. Jumps $>25.0\text{mm}$ are flagged as `DISCONTINUOUS`.
3. **Evidence Tagging:** Strict classification into `GEOMETRY_VERIFIED`, `ANATOMY_REVIEWED`, or `UNVERIFIED`.
4. **Anatomical Concordance:** Millimeter Euclidean distance against established osteological and myological ground-truth landmarks.

---

## 2. Upstream Quantitative Validation Summary

The table below summarizes the automated validation runs executed on the upstream datasets:

| Metric | `JICio/tcm-3d` | `eb-barry/MeridianStudio` | `WaterCMY/anatomy-3d` | `spacejohnlf/tcm-acupoints` |
| :--- | :--- | :--- | :--- | :--- |
| **Total Acupoints Extracted** | **362** | 361 | 146 | 70 |
| **Anatomy Reviewed** | 1 | 0 | 1 | 0 |
| **Geometry Verified** | **361** | 0 | 145 | 0 |
| **Unverified / Approximated** | 0 | 361 (Catalog only) | 0 | 70 |
| **Floating Points ($>5\text{mm}$)** | **0** | 0 | 0 | **70 (100%)** |
| **Penetrating Points ($<-2\text{mm}$)** | **0** | 0 | 0 | **0** |
| **Mean Surface Offset** | **3.49 mm** | 0.00 mm | 0.00 mm | **12.00 mm** |
| **Max Surface Offset** | **3.50 mm** | 0.00 mm | 0.00 mm | **12.00 mm** |
| **Pathway Step Warnings ($>25\text{mm}$)** | 44 (Leg/torso gaps) | 0 (Splines) | 117 (Sparse points) | 84 (Sparse points) |

### Key Validation Findings:
1. **JICio achieves 100% surface boundary compliance:** All 362 points lie exactly at the pre-baked $3.5\text{mm}$ normal offset on the BodyParts3D skin mesh (`FJ2810`), with zero floating or penetrating points.
2. **TCM-Acupoints suffers from systematic floating:** All 70 points are elevated by an arbitrary $12.0\text{mm}$ normal lift. While this avoids clipping inside the mesh, it creates severe visual detachment from the body silhouette.
3. **Meridian Studio provides the authoritative catalog:** 361 points accompanied by comprehensive anatomical localization descriptions, indications, and clinical precautions, designed for interactive 3D placement.

---

## 3. Neck–Shoulder Reference Scenario: Landmark Concordance

The Neck–Shoulder–Upper-Back region was evaluated across all systems against the canonical BodyParts3D osteological ground truths.

### 3.1 Point-by-Point Concordance Matrix

| Point Code & Traditional Name | Canonical Landmark $[X, Y, Z]$ (m) | JICio Coordinates $[X, Y, Z]$ | JICio Error (mm) | WaterCMY Coordinates $[X, Y, Z]$ | WaterCMY Error (mm) | TCM-Acupoints Coordinates $[X, Y, Z]$ | TCM-Acupoints Error (mm) | Agreement Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`GV14`** (大椎) | `[0.000, 1.478, -0.092]` | `[0.000, 1.435, -0.111]` | **46.9 mm** | `[0.000, 1.482, -0.086]` | **7.2 mm** | `[0.000, 1.460, -0.110]` | **25.5 mm** | DEVIATING |
| **`GB21`** (肩井) | `[0.142, 1.436, -0.012]` | `[0.083, 1.471, -0.061]` | **84.2 mm** | `[0.113, 1.484, -0.050]` | **67.7 mm** | `[0.140, 1.360, 0.000]` | **77.0 mm** | DISCREPANT |
| **`GB20`** (风池) | `[0.068, 1.582, -0.076]` | `[0.034, 1.541, -0.074]` | **53.5 mm** | `[0.038, 1.610, -0.063]` | **43.0 mm** | `[0.080, 1.480, -0.080]` | **102.8 mm** | DISCREPANT |
| **`BL10`** (天柱) | `[0.038, 1.572, -0.084]` | `[0.020, 1.521, -0.078]` | **54.1 mm** | `[0.035, 1.618, -0.067]` | **49.1 mm** | `[0.050, 1.460, -0.100]` | **113.8 mm** | DISCREPANT |
| **`SI15`** (肩中俞) | `[0.075, 1.455, -0.095]` | `[0.045, 1.443, -0.114]` | **37.8 mm** | N/A (Not in 146 set) | — | N/A (Not in 70 set) | — | DEVIATING |
| **`TE15`** (天髎) | `[0.128, 1.442, -0.045]` | `[0.100, 1.460, -0.068]` | **40.3 mm** | N/A (Not in 146 set) | — | N/A (Not in 70 set) | — | DEVIATING |

### Overall Accuracy Summary:
* **WaterCMY Mean Error:** **41.78 mm** (closest on `GV14` at $7.2\text{mm}$).
* **JICio Mean Error:** **52.80 mm** (tight surface adherence, but cervical spine seed points are positioned 1–2 vertebral levels lower than the classic C7 vertebra prominens).
* **TCM-Acupoints Mean Error:** **79.75 mm** (discrepancy amplified by head/neck anatomical posture in Z-Anatomy).

---

## 4. Root Cause Analysis of Anatomical Discrepancies

1. **`GV14` (Dazhui) Height Variation:**
   - In classical acupuncture, `GV14` is located immediately below the spinous process of C7.
   - On the BodyParts3D skeletal model, the C7 spinous process is located at $Y = 1.478\text{m}$.
   - WaterCMY placed `GV14` at $Y = 1.482\text{m}$ (within $7.2\text{mm}$ error).
   - JICio placed `GV14` at $Y = 1.435\text{m}$ ($43\text{mm}$ inferior), locating it near T2/T3.
   - **Remediation:** Calibrate `GV14` to the C7 osteological landmark using the Meridian Studio editor adapter.

2. **`GB21` (Jianjing) Mediolateral Drift:**
   - WHO standard defines `GB21` at the midpoint of the line connecting C7 (`GV14`) and the acromion ($X \approx 0.142\text{m}$).
   - JICio placed `GB21` at $X = 0.083\text{m}$, drifting toward the medial root of the neck.
   - **Remediation:** Shift lateral coordinate outward by $0.05\text{m}$ along the upper trapezius ridge to align with the true acromioclavicular midpoint.

3. **Suboccipital Cluster (`GB20` & `BL10`):**
   - JICio suboccipital coordinates are shifted medially ($X=0.034\text{m}$ vs landmark $X=0.068\text{m}$).
   - **Remediation:** Label as `GEOMETRY_VERIFIED` but flag as `PENDING_ANATOMICAL_CALIBRATION` in UI inspector so clinicians are explicitly informed of the educational approximation.
