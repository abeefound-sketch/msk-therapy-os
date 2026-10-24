# ANATOMICAL REGISTRATION BASELINE AUDIT (P9 BASELINE)

**Audit Date:** 2026-10-24  
**Project:** MSK-Therapy-OS  
**Branch:** `feat/p9-anatomical-registration`  
**Baseline Commit:** `v2.1.0-local-rc3` (`4f35602`)  
**Status:** FORENSIC BASELINE ESTABLISHED — P9 Commenced

---

## 1. PURPOSE & AUDIT CONTEXT

This audit establishes the empirical baseline of MSK-Therapy-OS's 3D Acupoint localization system prior to the architectural implementation of **P9: Anatomical Landmark Registration, Parametric Cun & Pose-Aware 3D Acupoint Engine**.

The system in `v2.1.0-local-rc3` passed all 174 automated unit/integration tests and technical security release gates, achieving 60.0 FPS WebGL rendering. However, clinical and graphics forensics demonstrate that:
1. Current point locations in `msk_therapy_os/static/atlas/data/acupuncture_3d.json` rely primarily on pre-baked surface raycasting from JICio/tcm-3d.
2. The existing `points.py` coordinates operate in static Euclidean space with a global bounding box check, lacking true bone-proportional cun (B-cun) regional scaling.
3. When patient morphology changes in `morphology_studio.py` (e.g. height, arm length, waist girth) or when joint postures flex in `pose_anatomy.py`, acupoints remain frozen on their original rest-pose triangles or become clinically unanchored.

---

## 2. REPOSITORY CODEBASE FORENSICS

### 2.1. `msk_therapy_os/points.py`
- **Schema State:**
  - Contains tables `point_libraries`, `custom_points`, `point_revisions`, `reference_point_overrides`, and `evidence_catalog`.
  - Supports registration statuses: `VERIFIED_ANATOMICAL_ANCHOR`, `SURFACE_REGISTERED_FJ2810`, `GEOMETRY_VERIFIED`, `ANATOMY_REVIEWED`, `UNCERTAIN_POSTURE_OFFSET`, `UNVERIFIED`.
  - Validates bounding envelope: $X \in [-0.35, 0.35]$, $Y \in [-0.05, 1.76]$, $Z \in [-0.25, 0.25]$.
- **Baseline Limitations Identified:**
  - No explicit table for **Anatomical Landmarks** (`anatomical_landmarks`) linked to FMA IDs and bone coordinates.
  - No registration metrics table storing residual RMS error per point or transformation matrices.
  - Coordinate validation is purely a box test; it does not verify whether an acupoint intended for the volar forearm is erroneously located on the dorsal surface or deep inside a muscle belly.

### 2.2. `msk_therapy_os/static/atlas/data/acupuncture_3d.json`
- **Dataset Composition:**
  - Total Points: 362 (361 classical points + Yintang EX-HN3).
  - Meridians: 14 channels (LU, LI, ST, SP, HT, SI, BL, KI, PC, TE, GB, LR, GV, CV).
  - Canonical Mesh Reference: BodyParts3D 4.0 FJ2810 skin mesh.
- **Baseline Accuracy Assessment:**
  - 82 points carry `SURFACE_REGISTERED_FJ2810` with verified surface distance $\le 0.5\text{ mm}$.
  - However, suboccipital and shoulder points exhibit significant clinical error against WHO 2008 bony definitions:
    - `GV14`: 46.9 mm displacement from the C7 spinous process depression.
    - `GB21`: 84.2 mm displacement from the C7-acromion midpoint.
    - `GB20`: 53.5 mm displacement from the suboccipital trapezius-SCM fossa.
    - `BL10`: 54.1 mm displacement from the C2 lateral trapezius margin.

### 2.3. `msk_therapy_os/pose_anatomy.py` (Pose-to-Anatomy Explorer)
- **Current State:**
  - Recognizes MediaPipe 33 landmarks and computes joint angles (cervical flexion, shoulder abduction, elbow flexion).
  - Maps joint angles to candidate muscle roles (agonist, antagonist, synergist) with clinical disclaimers.
- **Missing Integration in Baseline:**
  - Joint angle changes do NOT transform acupoint coordinates in the 3D Atlas.
  - Moving an arm in `pose_anatomy.py` leaves the 3D points in `acupuncture_3d.json` floating in static A-pose space.
  - No flag `UNCERTAIN_POSTURE_OFFSET` is dynamically attached to posture-sensitive points (e.g. LU5, BL40, PC6) when joint angles exceed calibration thresholds.

### 2.4. `msk_therapy_os/morphology_studio.py` (Morphology Studio)
- **Current State:**
  - Stores height, weight, and regional girths (chest, waist, hip, arm, thigh, calf).
  - Emits approximate 3D avatar deformation parameters.
- **Missing Integration in Baseline:**
  - No regional B-cun scaling calculation.
  - Changing patient height from 160 cm to 190 cm does not scale regional cun proportions (e.g. forearm 12 cun or lower leg 16 cun) based on bone segment proportions.

---

## 3. QUANTITATIVE BASELINE METRICS

| System Capability | Baseline Status (`v2.1.0-local-rc3`) | P9 Target Requirement |
| :--- | :--- | :--- |
| **Landmark Ontology** | Partial (hardcoded in research workbench) | Modular, extensible `landmark_registry.py` with 6 standard landmark types & FMA links |
| **Multi-Source Alignment** | Manual / Static offsets ($Y+0.86$) | Umeyama / Procrustes Landmark-based SVD transformation with RMS residual output |
| **Degenerate Configuration Rejection** | Absent (blindly calculates or crashes) | Explicit rank/collinearity detection emitting `UNREGISTERED` / `REQUIRES_REVIEW` |
| **B-Cun Proportional Scaling** | Absent (global static coordinates) | Regional segment division engine per WHO 2008 Standard |
| **Morphology Studio Integration** | Disconnected | Dynamic scaling responsive to patient anthropometric girths and segment lengths |
| **Pose-Aware Transformation** | Disconnected | Kinematic segment transformation with `UNCERTAIN_POSTURE_OFFSET` emission |
| **Guarded Raycasting** | Basic nearest-triangle snapping | Normal constraint ($\le 60^\circ$) + Anatomical region bounding containment |
| **Database Persistence** | Points & Revisions tables only | Versioned `anatomical_landmarks`, `cun_scaling_rules`, `registration_metrics` |
| **Atlas 3D QA UI** | Single comparative split view | Interactive QA Inspector overlay with residual error display and B-cun rules |

---

## 4. BASELINE CONCLUSION

The MSK-Therapy-OS platform possesses an exceptionally clean foundation (174 passing tests, zero external runtime pip dependencies, local-first SQLite architecture). The transition from static surface snapping to a **scientifically grounded, landmark-driven, parametric cun, and pose-aware acupoint engine** is essential to eliminate false clinical precision and establish transparent mathematical provenance.
