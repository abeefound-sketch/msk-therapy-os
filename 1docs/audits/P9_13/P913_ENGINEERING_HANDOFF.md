# MSK-Therapy-OS | Milestone P9.13 Engineering Handoff
**Document ID:** `P913_ENGINEERING_HANDOFF`  
**Milestone:** P9.13 Production Hardening & Ground-Truth Readiness  
**Target Audience:** Clinical AI Integration Team, Next Milestone Engineers  
**Date:** 2026-10-29  

---

## 1. System State & Architectural Baseline

Following completion of Milestone P9.13, MSK-Therapy-OS has transitioned from purely *technically calibrated* to an **independently auditable, scientifically falsifiable, and production-hardened** platform.

### Summary Metrics
| Metric | Value | Architectural Guarantee |
|---|---:|---|
| **Total Acupoints in Catalog** | 362 | Preserved across all relational tables |
| **Standard Classical Points** | 361 | Strictly conforms to WHO 2008 Western Pacific Standard |
| **Extended Classical Points** | 1 | `GV24+` (Yintang / M-HN3) on cranial midline |
| **Class A Canonical Anchors** | 18 | BodyParts3D 4.0 FJ2810 standard adult male reference |
| **Class B Parametric Points** | 344 | WHO 2008 B-cun rules anchored to skeletal landmarks |
| **Class C / Class D Points** | 0 | Zero uncalibrated legacy raycasts remaining |
| **Calibrated Coverage** | 100.0% | Complete mathematical & geometric calibration |
| **Tier 4 Clinical Verification** | Strictly 0.0% | Fail-closed governance; zero clinical claims |
| **Non-Playwright Regression** | 589 / 589 | 100% PASS across historical test suite |
| **Physical Intel HD 5500 FPS** | 57.4 FPS | $\ge 30.0\text{ FPS}$ standard floor |
| **P95 Frame Time** | 24.0 ms | $\le 38.0\text{ ms}$ ceiling |
| **Raycast Latency** | 0.005 ms | $\le 5.0\text{ ms}$ ceiling |

---

## 2. Key Codebase Changes & Newly Added Modules

### 2.1 Core Module: `msk_therapy_os/anatomical_validation.py`
Provides the `IndependentAnatomicalValidator` engine:
- `AnatomicalVerificationTier`: 5 hierarchical tiers (`TECHNICALLY_CALIBRATED`, `GEOMETRICALLY_VALIDATED`, `ANATOMICALLY_CORROBORATED`, `INDEPENDENTLY_VERIFIED`, `CLINICALLY_VERIFIED`).
- `GroundTruthModality`: 7 origin modalities (`CT_3D_SURFACE`, `MRI_T1_ANATOMICAL`, `ULTRASOUND_HIGH_FREQUENCY`, `CADAVERIC_MEASUREMENT`, `EXPERT_CONSENSUS_PALPATION`, `BODYPARTS3D_DIGITAL_REFERENCE`, `SYNTHETIC_TEST_FIXTURE`).
- `AnatomicalErrorClassification`: 5 residual error categories (`CONGRUENT` $\le 3\text{mm}$, `ACCEPTABLE_CLINICAL_TOLERANCE` $3-8\text{mm}$, `BORDERLINE` $8-15\text{mm}$, `OUTLIER_ANOMALY` $>15\text{mm}$, `INDEPENDENT_GROUND_TRUTH_UNAVAILABLE`).
- `generate_full_362_provenance_matrix()`: Generates the authoritative 362-point provenance matrix.
- `generate_anatomical_uncertainty_matrix()`: Calculates spatial uncertainty bounds and enforces `clinical_depth_guidance_allowed: False`.
- `run_metamorphic_transformation_test()`: Validates $SE(3)$ metamorphic rigid invariance.

### 2.2 Coverage Dashboard & API Updates (`msk_therapy_os/points.py`)
`get_meridian_atlas_coverage_dashboard` now exposes:
- `"standard_catalog_count": 361`
- `"extended_catalog_count": 1`
- `"extended_points": ["GV24+"]`
- In `governance_semantic_metadata`: `"independent_ground_truth_status": "INDEPENDENT_GROUND_TRUTH_UNAVAILABLE"`, `"anatomical_falsification_status": "FALSIFICATION_FRAMEWORK_ACTIVE"`.
- In `quality_assurance`: `"audit_status": "P9.13_PRODUCTION_HARDENED"`.

### 2.3 REST API Endpoints (`msk_therapy_os/server.py`)
- `GET /api/atlas/validation/provenance`: Returns the 362-point provenance matrix (filterable by `channel_code`).
- `GET /api/atlas/validation/report`: Returns independent ground-truth evaluation statistics and regional error distributions.
- `GET /api/atlas/validation/uncertainty`: Returns spatial uncertainty boundaries and clinical depth prohibition.

---

## 3. Mandatory Instructions for Future Engineers

1. **Never Elevate to Tier 4 Without External Empirical Evidence:**
   Any promotion to `INDEPENDENTLY_VERIFIED` or `CLINICALLY_VERIFIED` requires a registered external dataset (`CT_3D_SURFACE`, `MRI_T1_ANATOMICAL`, `CADAVERIC_MEASUREMENT`, or `EXPERT_CONSENSUS_PALPATION`) with verified reviewer credentials.
2. **Preserve Synthetic Fixture Quarantine:**
   Never set `is_synthetic_fixture = False` on synthetic unit test fixtures.
3. **Preserve 362 Record Cardinality:**
   Do not delete `GV24+` to make the catalog count 361. Both 361 classical points and 1 extended point must be preserved.
4. **Preserve Surgical Depth Guidance Prohibition:**
   Do not attempt to infer needle insertion depth from surface landmark coordinates. Surface landmarks do not account for individual variations in subcutaneous adipose depth or visceral displacement.
