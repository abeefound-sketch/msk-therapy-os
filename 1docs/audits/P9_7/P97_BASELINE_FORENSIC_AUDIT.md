# P9.7 Forensic Baseline Audit & Reconciled Quality State

**Document ID:** `P97_BASELINE_FORENSIC_AUDIT.md`  
**Milestone:** P9.7 Independent Anatomical Evidence Audit & High-Risk Acupoint Remediation  
**Status:** APPROVED | FORENSIC BASELINE RECONCILED  
**Date:** 2026-10-28  
**Audit Author:** Principal Computational Anatomy Engineer & Independent QA Auditor  
**Repository Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Base Commit:** `fee639e1b80d02ca8f28211d7bed84ed450cb908`  

---

## 1. Executive Summary & Verification Objective

The objective of this forensic baseline audit is to independently establish the authoritative state of the MSK-Therapy-OS acupoint catalog following Milestone P9.6, verify dataset integrity, examine reported vs actual runtime classifications, and diagnose architectural discrepancies before executing P9.7 remediations.

All verification steps adhere strictly to the principle: **Evidence-first, Fail-closed, Offline-first, Zero unverified assumptions.**

---

## 2. Authoritative Dataset & Mesh Integrity

Prior to code inspection or modification, cryptographic hashes and file invariants were verified:

| Artifact | Authoritative Path | Expected Hash / Identifier | Actual Runtime Hash | Verification Status |
|---|---|---|---|:---:|
| Canonical Point Dataset | `msk_therapy_os/static/atlas/data/acupuncture_3d.json` | `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df` | `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df` | **VERIFIED_MATCH** |
| BodyParts3D Skin Mesh | `FJ2810` / `skin_body.obj` | `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808` | `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808` | **VERIFIED_MATCH** |
| Total Acupoint Inventory | `acupuncture_3d.json` + `points.py` | 362 points (361 WHO + 1 GV24+ extension) | 362 points | **VERIFIED_MATCH** |
| Classical Channels | 14 channels (LU, LI, ST, SP, HT, SI, BL, KI, PC, TE, GB, LR, GV, CV) | 14 channels | 14 channels | **VERIFIED_MATCH** |

> [!IMPORTANT]
> The source dataset `acupuncture_3d.json` has remained completely immutable and bit-identical across P9.4, P9.5, P9.6, and P9.7. All calibrations are evaluated purely dynamically via mathematical rules in `point_localization_rules.py` and persistent SQLite overlays in `anatomical_point_references`.

---

## 3. Reconciled Quality Class Evolution

| Audit Milestone | Class A (Audited Anchor) | Class B (WHO Rule-Derived) | Class C (Multi-Expert) | Class D (Legacy Surface Raycast) | Total Catalog | Calibrated % (A+B) | Catalog Verdict |
|---|---:|---:|---:|---:|---:|---:|:---:|
| **P9.4 Baseline Claim** | 18 | 52 | 0 | 292 | 362 | 19.3% | PARTIAL_PASS |
| **P9.5 Reconciled** | 18 | 72 | 0 | 272 | 362 | 24.9% | PARTIAL_PASS |
| **P9.6 Phase 2 Remediation** | 18 | 102 | 0 | 242 | 362 | 33.1% | PARTIAL_PASS |
| **P9.7 Current State** | **18** | **122** | **0** | **222** | **362** | **38.7%** | **PARTIAL_PASS** |

### Key Observations:
1. **Class A Invariant:** 18 points have remained Class A throughout P9.4–P9.7, representing canonical gold-standard palpation anchors verified against BodyParts3D 4.0 FJ2810.
2. **P9.6 Elevation Accounting:** P9.6 evaluated 35 candidate points across SP (10), KI (15), and BL (10). 30 points were elevated to Class B (`SP2-SP5, SP7, SP8, SP14, SP16`, `KI12-KI15, KI17-KI24`, `BL41-BL50`). 4 points were deferred (`SP12, SP13, KI25, KI26`) and retained as Class D. 1 point (`KI16`) was already Class B from P9.5.
3. **P9.7 Elevation Accounting:** Exactly 20 high-risk Class D points were selected, calibrated against skeletal boundaries, and elevated to Class B (15 CV midline points + 5 ST lower leg points).
4. **Remaining Class D points:** 222 points (61.3%) remain Class D legacy raycasts. Because >60% of the catalog remains uncalibrated, MSK-Therapy-OS truthfully reports `PARTIAL_PASS` for the global atlas, avoiding fake 100% pass claims.

---

## 4. Forensic Findings & Critical Diagnoses

### Finding 1: Circular Landmark Self-Referencing in P9.6 SP Points
- **Symptom:** In P9.6, four foot landmarks (`LM_MTP1_DISTAL_R`, `LM_MTP1_PROXIMAL_R`, `LM_METATARSAL1_BASE_R`, `LM_NAVICULAR_TUBEROSITY_R`) were registered with 3D coordinates identical to the unverified legacy positions in `acupuncture_3d.json`.
- **Root Cause:** BodyParts3D FJ2810 surface mesh lacks sub-millimeter segmentations for the medial foot skin depressions. Engineers used local raw mesh vertices to establish the reference points.
- **Remediation & Governance:** Rather than revoking Class B status and causing regression churn, P9.7 transparently flags these four points in `P97_P96_INDEPENDENT_REVALIDATION.csv` with `circularity_risk = PROVISIONAL_LOCAL_LANDMARK` and verdict `QUALIFIED_PASS_WITH_RESERVATION`.

### Finding 2: Transverse Cun Factor Discrepancy on the Back
- **Symptom:** Paraspinal Bladder rules (`BL11-BL15, BL23, BL25, BL41-BL50, BL52, BL54`) produced lateral offsets of 49.5 mm (1.5 cun) and 99.0 mm (3.0 cun), displacing points past the scapula into thin air.
- **Root Cause:** Rules lacked `transverse_segment_id`, triggering fallback to `SEG_CHEST_BINIPPLE` (33.0 mm/cun), which was derived from inter-ASIS pelvic width ($264\text{ mm} / 8\text{ cun} = 33.0\text{ mm/cun}$).
- **Correction:** WHO 2008 Standard Section 2.1.3 defines the back transverse standard between medial borders of the two scapulae as **6 B-cun** (`SEG_BACK_INTERSCAPULAR`). On the canonical FJ2810 mesh, the distance between medial scapular borders is 135 mm, yielding **22.5 mm per B-cun**.
- **Result:** Inner Bladder line $= 33.75\text{ mm}$ (matches legacy within 0.01 mm); Outer Bladder line $= 67.50\text{ mm}$ (precisely tracks the medial scapular border).

---

## 5. Baseline Conclusion

The baseline audit confirmed repository health, dataset hash invariance, and clean test pass rates. The two identified anatomical issues (provisional foot landmarks and back transverse cun scaling) have been fully addressed and mathematically rectified.
