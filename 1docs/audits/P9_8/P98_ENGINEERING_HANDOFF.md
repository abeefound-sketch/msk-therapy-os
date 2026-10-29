# P9.8 Engineering Handoff & Milestone Summary

**Document ID:** `P98_ENGINEERING_HANDOFF.md`  
**Milestone:** P9.8 Anatomical Ground Truth & Evidence Integrity Hardening  
**Predecessor Milestone:** P9.7 Independent Anatomical Evidence Audit  
**Successor Milestone Candidate:** P9.9 High-Resolution Foot & Upper Extremity Calibration  
**Status:** APPROVED & SIGNED OFF  
**Date:** 2026-10-28  

---

## 1. Executive Summary

Milestone P9.8 focused on **evidence integrity, eliminating circular reasoning, and authenticating physical hardware performance**. 

Key accomplishments include:
1. **Quarantine of Circular Spleen Foot Points:** Identified and quarantined circular dependencies in `SP2, SP3, SP4, SP5`. Marked four reference landmarks as `BLOCKED_CIRCULAR_DEPENDENCY` and downgraded points from Class B to Class D.
2. **Implementation of Provenance Dependency Validator:** Delivered `AnatomicalProvenanceDependencyValidator` in `msk_therapy_os/landmark_dependency_validator.py` with zero undisclosed circularities.
3. **Hardened Scapular & Interscapular Calibration:** Grounded medial scapular landmarks at $\pm 67.5	ext{ mm}$ and calibrated 19 paraspinal Bladder rules to the WHO 22.5 mm/cun ratio.
4. **Dynamic QA Studio Coverage Dashboard:** Removed hardcoded fallback counts (`18`, `122`, `222`, `38.7%`) from `meridians.js`. Replaced with neutral `--` placeholders and live dynamic fetch with `UNAVAILABLE` fallback.
5. **Physical Hardware Verification on Target Silicon:** Direct physical execution on the target **Intel Core i7-5600U with Intel HD Graphics 5500** achieving 30.7 FPS in full interactive 3D WebGL2 mode.
6. **Full Test Suite Reconciliation:** Reconciled platform test accounting (303 tests total, 68 milestone tests, 100% pass rate).

---

## 2. Authoritative Architecture & Repository State

- **Branch:** `feat/p9.4-definitive-meridian-atlas-correction`
- **Canonical Dataset Hash:** `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df`
- **BodyParts3D Mesh Hash:** `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`
- **Quality Distribution:**
  - Class A (Canonical Anchors): **18** (5.0%)
  - Class B (WHO Rule-Derived): **118** (32.6%)
  - Class C (Multi-Expert): **0** (0.0%)
  - Class D (Uncalibrated Legacy): **226** (62.4%)
  - Total Catalog: **362** points (361 WHO + 1 GV24+)
  - Total Calibrated: **136** points (37.6%)
  - Global Catalog Status: **`PARTIAL_PASS`**

---

## 3. Residual Risks & Disclosures

1. **226 Legacy Class D Points:** Over 62% of the catalog remains uncalibrated legacy raycasts. These points carry $\pm 15-40	ext{ mm}$ spatial uncertainty.
2. **Lack of Discrete Tarsal/Metatarsal Meshes in BodyParts3D FJ2810:** High-risk distal extremity points cannot be elevated without high-resolution skeletal segmentations.
3. **Clinical Boundary Hard Stop:** The atlas provides surface visualization only. It MUST NOT be used for invasive needle depth guidance.

---

## 4. Proposed P9.9 Milestone Scope

To expand anatomical coverage safely:
1. **Acquire & Register Foot/Ankle Segmentations:** Import open-source tarsal/metatarsal segmentations to de-quarantine `SP2, SP3, SP4, SP5` and calibrate `KI1-KI6`.
2. **Upper Extremity Hand & Wrist Remediation:** Calibrate carpal landmarks (`LM_PISIFORM`, `LM_SCAPHOID_TUBERCLE`, `LM_HAMATE_HOOK`) to calibrate LU9, HT7, PC7, SI4, LI5.
3. **Target Calibration Elevation:** Elevate 20–25 Class D points to Class B with verified skeletal grounding, aiming for ~42% total calibrated coverage.
