# P9.9 Forensic Baseline Audit & Reconciled Quality State

**Document ID:** `P99_BASELINE_FORENSIC_AUDIT.md`  
**Milestone:** P9.9 High-Resolution Foot & Wrist Skeletal Registration  
**Predecessor Milestone:** P9.8 Anatomical Ground Truth & Hardware Integrity Hardening  
**Status:** APPROVED | FORENSIC BASELINE RECONCILED  
**Date:** 2026-10-28  
**Audit Author:** Principal Computational Anatomy Engineer, Medical 3D Registration Specialist & Independent Evidence Auditor  
**Repository Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Base Commit:** `fee639e1b80d02ca8f28211d7bed84ed450cb908`  

---

## 1. Executive Summary & Verification Objective

The objective of Milestone P9.9 is to establish **high-resolution anatomical registration for the foot and wrist**, implement independent skeletal ground truth from discrete BodyParts3D 4.0 bone segmentations, resolve the four circular landmarks quarantined during Milestone P9.8 (`LM_MTP1_DISTAL_R`, `LM_MTP1_PROXIMAL_R`, `LM_METATARSAL1_BASE_R`, `LM_NAVICULAR_TUBEROSITY_R`), and remediate the distal extremities of the Spleen (`SP2–SP5`), Kidney (`KI1–KI6`), and wrist channels (`LU9, HT7, PC7`).

Prior to P9.9, the atlas relied on surface approximations for distal limb points because BodyParts3D release model `FJ2810` provided an integrated whole-body skin boundary without discrete tarsal/metatarsal bone segmentations in the default clinical atlas view. In P9.8, fail-closed quarantine was enforced, correctly downgrading `SP2–SP5` to Class D.

In P9.9, we audit and integrate discrete tarsal, metatarsal, carpal, and radius/ulna skeletal segmentations from the approved BodyParts3D 4.0 catalog, register them to the canonical reference frame, and derive independent, mathematically auditable landmarks.

---

## 2. Authoritative Dataset, Mesh & Hardware Verification

Prior to modifying repository source files, all cryptographic checksums, data structures, and host hardware were independently verified:

| Artifact / Hardware Component | Authoritative Path / Specification | Expected Value | Actual Runtime Value | Verification Status |
|---|---|---|---|:---:|
| **Canonical Point Dataset** | `msk_therapy_os/static/atlas/data/acupuncture_3d.json` | `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df` | `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df` | **VERIFIED_MATCH** |
| **BodyParts3D Canonical Mesh** | `2data/artifacts/fj2810_softened.bin` | `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808` | `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808` | **VERIFIED_MATCH** |
| **Canonical Mesh ID** | `CANONICAL_MESH_ID` | `FJ2810` | `FJ2810` | **VERIFIED_MATCH** |
| **Total Acupoint Inventory** | `acupuncture_3d.json` + `points.py` | 362 points (361 WHO + 1 GV24+ extension) | 362 points | **VERIFIED_MATCH** |
| **Physical Host GPU** | WMI `Win32_VideoController` / WebGL ANGLE | Intel(R) HD Graphics 5500 | Intel(R) HD Graphics 5500 (D3D11) | **AUTHENTIC_SILICON** |
| **Physical Host CPU** | WMI `Win32_Processor` | Intel(R) Core(TM) i7-5600U CPU @ 2.60GHz | Intel(R) Core(TM) i7-5600U @ 2.60GHz | **AUTHENTIC_SILICON** |
| **Host Operating System** | CIM `Win32_OperatingSystem` | Windows 10 Pro 64-bit | Windows 10 Pro 64-bit | **AUTHENTIC_HOST** |
| **Predecessor Test Baseline** | `python -m pytest tests/` | 312 passing tests | 312 passing tests (0 failures, 0 skips) | **ALL PASS (347.67s)** |

---

## 3. Predecessor Milestone Quality Distribution (P9.8 Baseline)

The authoritative catalog distribution entering Milestone P9.9 is:

| Quality Class | Quality Tier Name | Point Count | Percentage of Catalog | Verification Standard |
|---|---|---:|---:|---|
| **Class A** | Canonical Audited Anchors | 18 | 5.0% | Audited skeletal/palpation ground truth on BodyParts3D FJ2810 |
| **Class B** | WHO Rule-Derived Anchors | 118 | 32.6% | Parametric B-cun & anatomical rules over verified landmarks |
| **Class C** | Multi-Expert Calibrated | 0 | 0.0% | Multi-practitioner consensus (unpopulated in P9 series) |
| **Class D** | Legacy Uncalibrated Raycasts | 226 | 62.4% | Uncalibrated geometric surface raycasts ($\pm 15-40\text{ mm}$ uncertainty) |
| **Total Catalog** | — | **362** | **100.0%** | Complete classical catalog (361 WHO + 1 GV24+) |
| **Calibrated Total** | Class A + Class B | **136** | **37.6%** | **Global Status: `PARTIAL_PASS`** |

---

## 4. Candidate Pool Census for Milestone P9.9

The milestone target candidate pool consists of **13 points** across three functional anatomical groups:

| Group | Point Code | Name (EN) | Channel | P9.8 Class | P9.8 Landmark Dependency Status | P9.9 Objective |
|---|---|---|---|:---:|---|---|
| **Spleen Foot** | `SP2` | Dadu | Spleen | **Class D** | `LM_MTP1_DISTAL_R` (`BLOCKED_CIRCULAR_DEPENDENCY`) | De-quarantine via independent 1st MTP joint geometry; elevate to Class B |
| **Spleen Foot** | `SP3` | Taibai | Spleen | **Class D** | `LM_MTP1_PROXIMAL_R` (`BLOCKED_CIRCULAR_DEPENDENCY`) | De-quarantine via 1st metatarsal neck geometry; elevate to Class B |
| **Spleen Foot** | `SP4` | Gongsun | Spleen | **Class D** | `LM_METATARSAL1_BASE_R` (`BLOCKED_CIRCULAR_DEPENDENCY`) | De-quarantine via 1st metatarsal base & medial cuneiform; elevate to Class B |
| **Spleen Foot** | `SP5` | Shangqiu | Spleen | **Class D** | `LM_NAVICULAR_TUBEROSITY_R` (`BLOCKED_CIRCULAR_DEPENDENCY`) | De-quarantine via navicular tuberosity & medial malleolus; elevate to Class B |
| **Kidney Foot** | `KI1` | Yongquan | Kidney | **Class B** | `LM_CALCANEUS_POST_R` / `LM_MED_MALLEOLUS_R` (provisional) | Re-anchor to true plantar metatarsal interval; revalidate Class B |
| **Kidney Foot** | `KI2` | Rangu | Kidney | **Class D** | No rule in registry (legacy raycast) | Establish rule anteroinferior to navicular tuberosity; elevate to Class B |
| **Kidney Foot** | `KI3` | Taixi | Kidney | **Class B** | `LM_MED_MALLEOLUS_R` / `LM_CALCANEUS_POST_R` | Re-anchor between medial malleolus & Achilles tendon; revalidate Class B |
| **Kidney Foot** | `KI4` | Dazhong | Kidney | **Class D** | No rule in registry (legacy raycast) | Establish rule posteroinferior to malleolus on calcaneus; elevate to Class B |
| **Kidney Foot** | `KI5` | Shuiquan | Kidney | **Class D** | No rule in registry (legacy raycast) | Establish rule 1 cun below KI3 at medial calcaneus; elevate to Class B |
| **Kidney Foot** | `KI6` | Zhaohai | Kidney | **Class B** | `LM_MED_MALLEOLUS_R` / `LM_CALCANEUS_POST_R` | Re-anchor 1 cun directly inferior to medial malleolus; revalidate Class B |
| **Wrist Line** | `LU9` | Taiyuan | Lung | **Class B** | `LM_WRIST_CREASE_PALMAR_R` (provisional) | Re-anchor between radial styloid & scaphoid tubercle; revalidate Class B |
| **Wrist Line** | `HT7` | Shenmen | Heart | **Class D** | No rule in registry (legacy raycast) | Establish rule on ulnar crease radial to FCU / proximal to pisiform; elevate to Class B |
| **Wrist Line** | `PC7` | Daling | Pericardium | **Class B** | `LM_WRIST_CREASE_PALMAR_R` | Re-anchor at palmar crease midpoint between FCR & PL tendons; revalidate Class B |

### Candidate Reconciliation Summary:
- **Already Class B (re-validation targets):** 5 points (`LU9, PC7, KI1, KI3, KI6`)
- **Currently Class D (eligible elevation targets):** 8 points (`SP2, SP3, SP4, SP5, KI2, KI4, KI5, HT7`)
- **Net Gain Potential:** $+8$ points $\implies 144$ Class A+B points ($39.8\%$ coverage).
- **Governance Constraint:** Elevation to Class B occurs **strictly upon satisfactory evidence** of independent skeletal grounding.
