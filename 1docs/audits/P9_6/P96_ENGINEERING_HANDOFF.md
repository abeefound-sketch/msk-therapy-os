# P9.6 Phase 2 Anatomical Remediation — Engineering Handoff & System Reference

**Project:** MSK-Therapy-OS  
**Milestone:** P9.6 Phase 2 Anatomical Acupoint Remediation  
**Status:** COMPLETED & AUDITED  
**Auditor / Author:** Principal Computational Anatomy Engineer & Python Backend Architect  
**Date:** 2026-10-28  
**Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Base Dataset SHA-256:** `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df`  
**Canonical Mesh ID:** `FJ2810`  

---

## 1. Executive Summary

Milestone P9.6 delivers the second phase of high-risk anatomical acupoint remediation, elevating **30 Class D points to Class B** via deterministic WHO 2008 mathematical rules anchored to BodyParts3D FJ2810 landmarks.

### Key Milestones Achieved:
1. **Reconciliation of 35-Candidate Scope:**
   - 30 selected points elevated to `CLASS_B` (`SP2-SP5, SP7, SP8, SP14, SP16`, `KI12-KI15, KI17-KI24`, `BL41-BL50`).
   - 4 points deferred to `CLASS_D` with documented clinical/anatomical rationales (`SP12, SP13, KI25, KI26`).
   - 1 point (`KI16`) reconciled as pre-existing Class B from P9.5.
   - Triple Energizer (TE) points strictly excluded from P9.6.
2. **Bladder Outer Column Vertebral Alignment:**
   - Eradicated naive sequential indexing (T1-T10).
   - Enforced WHO 2008 alignment: `BL41` at T2, `BL42-BL46` at T3-T7, classical skip of T8, and `BL47-BL50` at T9-T12.
3. **Landmark Registry Extension:**
   - Added 5 canonical reference anchors in `landmark_registry.py` (`LM_MTP1_DISTAL_R`, `LM_MTP1_PROXIMAL_R`, `LM_METATARSAL1_BASE_R`, `LM_NAVICULAR_TUBEROSITY_R`, `LM_TIBIA_MEDIAL_CONDYLE_R`).
4. **Authoritative Quality State:**
   - **Class A:** 18 points (5.0%)
   - **Class B:** 102 points (28.2%)
   - **Class C:** 0 points (0.0%)
   - **Class D:** 242 points (66.9%)
   - **Total Calibrated (A + B):** 120 points (33.1%)
   - **Total Catalog:** 362 points (100.0%)
5. **Zero Breaking Changes:**
   - 100% test pass rate across all 44 regression tests and Playwright visual browser tests.
   - Base dataset `acupuncture_3d.json` SHA-256 strictly preserved.

---

## 2. Modified & Created Artifacts

### Core Repository Files:
- `msk_therapy_os/landmark_registry.py`: Added 5 new foot/ankle/tibia canonical landmarks with FMA IDs and uncertainty bounds.
- `msk_therapy_os/point_localization_rules.py`: Added 30 new WHO 2008 localization rules covering Groups A, B, and C.
- `msk_therapy_os/points.py`: Updated `class_d_warning` to dynamically format uncalibrated counts and updated audit status to `P9.6_PHASE_2_REMEDIATION_PARTIAL`.
- `msk_therapy_os/static/atlas/meridians.js`: Updated coverage dashboard fallback UI defaults to 18 Class A, 102 Class B, 242 Class D, and 33.1% verified.
- `tests/test_p9_5_anatomical_remediation.py`: Updated assertions to support forward progress (72 $\to$ 102 Class B).
- `tests/test_p9_6_anatomical_remediation.py`: Dedicated 16-test comprehensive suite validating P9.6 rules, reconciliation, vertebral alignment, and symmetry.
- `tests/test_p9_6_playwright_remediation.py`: Playwright browser suite capturing 5 high-resolution WebGL visual evidence screenshots.

### Deliverables in `1docs/audits/P9_6/`:
- `P96_BASELINE_AUDIT.md`: Pre-P9.6 audit, SHA-256 verification, and baseline metrics.
- `P96_CANDIDATE_SELECTION_MATRIX.csv`: Detailed evaluation of all 35 candidates with selections, deferrals, and rationales.
- `P96_ANATOMICAL_RULE_VALIDATION.md`: Full documentation of the 30 rules, WHO clauses, FMA anchors, and resolved coordinates.
- `P96_ACUPOINT_PROVENANCE_MATRIX.csv`: Complete 362-point matrix updated with P9.6 quality classes and coordinates.
- `P96_COORDINATE_CHANGELOG.csv`: Before/after coordinates and euclidean displacement deltas for the 30 remediated points.
- `P96_GEOMETRY_REGRESSION.md`: Symmetry (0.000 mm error), midline invariance (0.00 mm), outward normals, and route continuity.
- `P96_TEST_EXECUTION_REPORT.md`: Test execution results across all test suites (45 tests passed).
- `P96_EVIDENCE_MANIFEST.json`: Visual evidence manifest with hashes and reproduction commands.
- `P96_FINAL_ACCEPTANCE_MATRIX.md`: Final evaluation against acceptance gates G1 through G10.
- `P96_ENGINEERING_HANDOFF.md`: This engineering handoff document.

### Visual Evidence in `2data/evidence/p9_6_remediation/`:
- `01_p96_qa_studio_coverage_102_class_b.png`
- `02_p96_spleen_medial_foot_leg_calibrated.png`
- `03_p96_kidney_abdominal_thoracic_columns_calibrated.png`
- `04_p96_bladder_outer_column_t2_t12_calibrated.png`
- `05_p96_bilateral_symmetry_dual_view.png`

---

## 3. Operational Runbook

### 3.1 Verification Commands
```powershell
# 1. Run all definitive atlas and remediation regression suites
pytest tests/test_p9_4_definitive_atlas.py tests/test_p9_5_anatomical_remediation.py tests/test_p9_6_anatomical_remediation.py

# 2. Run Playwright browser visual evidence suite
pytest tests/test_p9_6_playwright_remediation.py

# 3. Verify base dataset integrity invariant
python -c "import hashlib; assert hashlib.sha256(open('msk_therapy_os/static/atlas/data/acupuncture_3d.json', 'rb').read()).hexdigest() == '47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df'"
```

### 3.2 Rollback Procedure
If rollback is required:
```powershell
# Revert working directory changes
git restore msk_therapy_os/landmark_registry.py msk_therapy_os/point_localization_rules.py msk_therapy_os/points.py msk_therapy_os/static/atlas/meridians.js tests/test_p9_5_anatomical_remediation.py
```

---

## 4. Proposed Roadmap for Phase 3 (Milestone P9.7)

With 120 points (33.1%) now calibrated, Phase 3 should target:
1. **Stomach Meridian (ST) Lower Extremity:** `ST31` through `ST45` (anterior thigh, patellar ligament, lateral tibial border, dorsum of foot).
2. **Gallbladder Meridian (GB) Lower Extremity:** `GB31` through `GB44` (iliotibial band, fibular shaft, lateral ankle, dorsum of foot).
3. **Triple Energizer (TE) Forearm & Cranial:** `TE1` through `TE23` (extensor forearm interval, olecranon depression, retro-auricular curve).
4. **Resolution of Deferred Candidates:** High-density CT surface mesh anchoring to unlock `SP12, SP13` (inguinal crease) and `KI25, KI26` (sternoclavicular rib angle).
