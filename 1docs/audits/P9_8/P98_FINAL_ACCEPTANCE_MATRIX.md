# P9.8 Final Engineering Acceptance Matrix

**Document ID:** `P98_FINAL_ACCEPTANCE_MATRIX.md`  
**Milestone:** P9.8 Anatomical Ground Truth & Evidence Integrity Hardening  
**Status:** APPROVED | 10/10 GATES PASS  
**Global Catalog Status:** PARTIAL_PASS (37.6% Calibrated, Fail-Closed Truth-in-Reporting)  
**Date:** 2026-10-28  

---

## 1. Acceptance Gates Evaluation

| Gate ID | Gate Name | Acceptance Criteria | Measured Result | Verdict |
|---|---|---|---|:---:|
| **G1** | **Dataset & Mesh Invariance** | SHA256 of `acupuncture_3d.json` and mesh `FJ2810` match canonical hashes bit-for-bit. | Dataset: `47df1332...`<br>Mesh: `05b49233...` | **PASS** |
| **G2** | **Total Inventory Integrity** | Exactly 362 points accounted for (361 WHO canonical + 1 GV24+ clinical extension). Zero lost points. | Exactly 362 points verified in SQLite and Python runtime. | **PASS** |
| **G3** | **Zero Undisclosed Circularity** | `AnatomicalProvenanceDependencyValidator` detects zero unquarantined circular references. | Undisclosed: 0<br>Quarantined: 4 | **PASS** |
| **G4** | **Spleen Foot Points Quarantine** | `SP2, SP3, SP4, SP5` downgraded to Class D; landmarks marked `BLOCKED_CIRCULAR_DEPENDENCY`. | Rule solver returns `None`; fallback to Class D. | **PASS** |
| **G5** | **Scapular & Cun Ratio Validation** | `LM_SCAPULA_MEDIAL_BORDER_R/L` grounded at $\pm 67.5	ext{ mm}$; 22.5 mm/cun ratio verified. | Transverse: 135 mm.<br>Inner BL: 33.75 mm.<br>Outer BL: 67.50 mm. | **PASS** |
| **G6** | **Authoritative Quality Truth** | Distribution reports exactly: 18 Class A (5.0%), 118 Class B (32.6%), 0 Class C, 226 Class D (62.4%). Total calibrated: 136 (37.6%). | Exact match across SQLite, Python, and dynamic API. | **PASS** |
| **G7** | **QA Studio Dynamic Metrics** | Zero hardcoded fallback counts in `meridians.js`. API offline emits `UNAVAILABLE` and `--`. | Confirmed via code audit and interactive test. | **PASS** |
| **G8** | **Physical Hardware Acceptance** | Sustained FPS $\ge 30.0$ on physical Intel HD Graphics 5500; raycast latency $\le 50	ext{ ms}$. | FPS: 30.7 FPS.<br>Raycast: < 1.0 ms.<br>Restore: 55.5 ms. | **PASS** |
| **G9** | **Clinical Safety Boundaries** | Explicit non-invasive educational disclaimers. Zero depth or surgical penetration claims. | Disclaimers present in API, UI, and docs. | **PASS** |
| **G10** | **Full Regression Test Suite** | 100% pass rate across milestone-specific (68/68) and repository-wide test suites (303/303). | 68/68 Milestone PASS.<br>303/303 Repo PASS. | **PASS** |

---

## 2. Global Catalog Truth-in-Reporting

- **Calibrated Acupoints:** 136 points (37.6%)
- **Uncalibrated Legacy Acupoints:** 226 points (62.4%)
- **Global Atlas Verdict:** **`PARTIAL_PASS`**

> [!IMPORTANT]
> MSK-Therapy-OS refuses to claim "100% Complete" or "Clinically Validated" for the global catalog while 226 points remain legacy geometric surface raycasts with $\pm 15-40	ext{ mm}$ uncertainty. This fail-closed posture is a core clinical safety requirement.
