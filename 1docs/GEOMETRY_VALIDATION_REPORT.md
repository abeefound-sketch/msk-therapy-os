# Geometry Validation Report: Authentic Surface Adherence & Landmark Concordance

**Project:** MSK-Therapy-OS  
**Branch:** `research/anatomical-workbench`  
**Status:** FORENSIC EVIDENCE REPORT  
**Author:** Independent Quality Auditor & Tools Engineer  
**Date:** 2026-10-21  

---

## 1. Executive Summary

This report delivers the quantitative validation results produced by the `research.workbench validate` engine across all four upstream repositories. Every acupuncture point and meridian pathway was evaluated against:
1. **Authentic Mesh Distance Measurement:** Real mathematical point-to-triangle 3D spatial queries against the authentic BodyParts3D `FJ2810` skin mesh ($44,744$ triangles, SHA256: `4a959d998acd...`).
2. **Boundary Adherence Rules:** Points $>5.0\text{mm}$ are flagged as `FLOATING`; points $<-2.0\text{mm}$ are flagged as `PENETRATING`.
3. **Normal Alignment & Face Index Verification:** Angular dot product against local mesh face normals and verification of recorded face indices.
4. **Pathway Continuity:** Measurement of inter-vertex step distances along meridian polylines ($>25.0\text{mm}$ flagged as broken segments).
5. **Strict Clinical Demarcation:** Points are classified as `GEOMETRY_VERIFIED` (graphics metric only) or `UNVERIFIED`. `ANATOMY_REVIEWED` is reserved strictly for documented qualified human expert clinical review.

---

## 2. Upstream Quantitative Validation Summary (Authentic Mesh Intersection)

| Metric | `JICio/tcm-3d` | `eb-barry/MeridianStudio` | `WaterCMY/anatomy-3d` | `spacejohnlf/tcm-acupoints` |
| :--- | :--- | :--- | :--- | :--- |
| **Total Acupoints Extracted** | **670 (Bilateral)** | 361 | 146 | 70 |
| **Geometry Verified ($\le 5\text{mm}$)**| **633 (94.5%)** | 0 | 33 (22.6%) | 8 (11.4%) |
| **Anatomy Reviewed (Clinical)** | **0 (None documented)** | 0 | 0 | 0 |
| **Unverified / Approximated** | **37 (5.5%)** | 361 (Catalog only) | 113 (77.4%) | 62 (88.6%) |
| **Floating Points ($>5\text{mm}$)** | **16 (2.4%)** | 0 | 113 (77.4%) | 60 (85.7%) |
| **Penetrating Points ($<-2\text{mm}$)** | **0** | 0 | 0 | 0 |
| **Mean Measured Mesh Distance** | **0.31 mm** | 0.00 mm | **17.14 mm** | **69.65 mm** |
| **Max Measured Mesh Distance** | **18.48 mm** | 0.00 mm | **73.15 mm** | **300.65 mm** |
| **Pathway Step Warnings ($>25\text{mm}$)** | 44 (Leg/torso gaps) | 0 (Splines) | 117 (Sparse points) | 84 (Sparse points) |

### Key Forensic Discoveries:
1. **JICio Surface Conformance:** $633$ of the $670$ bilateral points lie in close contact with the BodyParts3D skin mesh (mean distance **$0.31\text{mm}$**).
2. **Identification of 16 Floating Outliers in JICio:** While previously assumed to have 0 floating points, real point-to-triangle queries reveal that $16$ points on high-curvature extremities (auricle, toes, distal phalanges) float between $5.2\text{mm}$ and $18.48\text{mm}$ off the surface mesh. These have been flagged as `UNVERIFIED`.
3. **Face Index Permutation:** Recorded `faceIndex` values in JICio do not match the true closest triangle on `FJ2810` due to mesh relaxation during their pre-bake script. True closest faces are computed and stored in `canonical_acupuncture_v2.json`.
4. **Zero Clinical Reviews Documented:** Neither JICio nor the other three upstreams document qualified human clinical anatomical review for their 3D coordinates. All $670$ points are therefore marked with `clinical_review_status: PENDING_QUALIFIED_HUMAN_EXPERT_REVIEW`.

---

## 3. Neck–Shoulder Reference Scenario: Landmark Concordance

The Neck–Shoulder–Upper-Back region was evaluated across all systems against academic anatomical ground truths (WHO Standard Acupuncture Point Locations 2008 & Terminologia Anatomica).

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
* **JICio Mean Error:** **52.80 mm** (tight surface adherence, but cervical seeds sit 1–2 vertebral levels lower than C7).
* **TCM-Acupoints Mean Error:** **79.75 mm** (discrepancy amplified by head/neck posture in Z-Anatomy).
