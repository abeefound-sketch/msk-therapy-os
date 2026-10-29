# P9.6 Phase 2 Anatomical Remediation — Forensic Baseline Audit

**Project:** MSK-Therapy-OS  
**Milestone:** P9.6 Phase 2 Anatomical Acupoint Remediation  
**Status:** PASS / BASELINE_VERIFIED  
**Auditor:** Principal Computational Anatomy Engineer & Independent QA Auditor  
**Date:** 2026-10-28  
**Reference Mesh:** BodyParts3D 4.0 FJ2810 (`05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`)  
**Base Dataset:** `msk_therapy_os/static/atlas/data/acupuncture_3d.json` (`47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df`)  

---

## 1. Executive Summary

Prior to executing any code modifications in Milestone P9.6, a forensic baseline audit was conducted on the repository state following the completion of Milestone P9.5 (`feat/p9.4-definitive-meridian-atlas-correction`, commit `fee639e1b80d02ca8f28211d7bed84ed450cb908`).

The baseline verification established:
1. **Total Catalog Inventory:** Exactly 362 distinct acupoint keys are registered across the 14 classical channels (361 classical WHO points + 1 classical extra extension `GV24+` Yintang).
2. **Quality Class Distribution (Pre-P9.6 Baseline):**
   - **CLASS_A (Independently Audited Canonical Anchors):** 18 points (5.0%)
   - **CLASS_B (Parametric WHO 2008 Rule-Derived):** 72 points (19.9%)
   - **CLASS_C (Provisional Geometry):** 0 points (0.0%)
   - **CLASS_D (Uncalibrated Legacy Surface Raycasts):** 272 points (75.1%)
   - **Total Points:** 362 (100.0%)
3. **Candidate Pool Reconciliation:** The P9.6 specification proposed an initial candidate pool of 35 points across Spleen (SP), Kidney (KI), and Bladder Outer Column (BL). Investigation revealed that `KI16` (Huangshu) was already calibrated to Class B in P9.5. Exactly 30 points from the remaining 34 Class D candidates were selected for anatomical calibration, while 5 points (`SP12, SP13, KI25, KI26, KI16`) were deferred or reconciled with rigorous clinical justifications.
4. **Triple Energizer (TE) Exclusion:** Although the prompt title mentioned TE, no TE points were enumerated in the task scope. Following strict change-control rules, TE was explicitly excluded from P9.6.

---

## 2. Invariant Hashes & Cryptographic Integrity

| Target File | Expected SHA-256 | Verified SHA-256 | Verification Status |
|---|---|---|---|
| `acupuncture_3d.json` | `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df` | `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df` | **MATCH (UNTOUCHED)** |
| Canonical Mesh FJ2810 | `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808` | `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808` | **MATCH (VALIDATED)** |

---

## 3. Pre-P9.6 vs Post-P9.6 Target Distribution

| Metric | P9.5 Baseline State | P9.6 Target Elevation | Post-P9.6 Realized State | Variance |
|---|---:|---:|---:|---:|
| **Class A (Audited Anchors)** | 18 (5.0%) | 0 | 18 (5.0%) | 0 |
| **Class B (WHO 2008 Rules)** | 72 (19.9%) | +30 | 102 (28.2%) | +30 (+8.3%) |
| **Class C (Provisional)** | 0 (0.0%) | 0 | 0 (0.0%) | 0 |
| **Class D (Legacy Raycasts)** | 272 (75.1%) | -30 | 242 (66.9%) | -30 (-8.3%) |
| **Total Calibrated (A + B)** | 90 (24.9%) | +30 | 120 (33.1%) | +30 (+8.3%) |
| **Total Catalog** | 362 (100.0%) | 0 | 362 (100.0%) | 0 |

---

## 4. Candidate Pool Forensic Evaluation

| Group | Candidate Codes | Total in Pool | Selected for P9.6 | Deferred / Reconciled | Justification Summary |
|---|---|---:|---:|---:|---|
| **Group A: Spleen (SP)** | `SP2, SP3, SP4, SP5, SP7, SP8, SP12, SP13, SP14, SP16` | 10 | 8 | 2 (`SP12, SP13`) | Medial foot bony landmarks and tibia proportional segment (13 cun) are fully defined. SP12/SP13 deferred due to groin soft-tissue curvature. |
| **Group B: Kidney (KI)** | `KI12-KI26` | 15 | 12 | 3 (`KI16, KI25, KI26`) | KI16 previously calibrated in P9.5. KI12-KI24 calibrated via 0.5/2.0 cun parasagittal lines. KI25/KI26 deferred due to subclavicular rib facet congestion. |
| **Group C: Bladder Outer (BL)** | `BL41-BL50` | 10 | 10 | 0 | 3.0 cun parasagittal back column. Non-sequential vertebral alignment verified: T2-T7 and T9-T12; T8 omitted per WHO 2008. |
| **Total** | | **35** | **30** | **5** | **Exact match to engineering quota** |

---

## 5. Automated Verification Commands

To reproduce the baseline verification independently:
```powershell
# 1. Verify SHA-256 of raw canonical dataset
python -c "import hashlib; assert hashlib.sha256(open('msk_therapy_os/static/atlas/data/acupuncture_3d.json', 'rb').read()).hexdigest() == '47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df'"

# 2. Run definitive atlas and P9.5 regression tests
pytest tests/test_p9_4_definitive_atlas.py tests/test_p9_5_anatomical_remediation.py
```
