# P9.5 FORENSIC BASELINE AUDIT: ACUPOINT INVENTORY & PRE-REMEDIATION BASELINE

**Document ID:** P95-AUDIT-001  
**Project:** MSK-Therapy-OS  
**Milestone:** P9.5 Anatomical Accuracy Remediation & Evidence-Based Acupoint Validation  
**Author:** Principal Computational Anatomy Engineer, Python Backend Architect, Independent QA Auditor  
**Date:** October 2026  
**Reference Mesh:** BodyParts3D 4.0 FJ2810 (`05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`)  
**Status:** BASELINE FROZEN & AUDITED  

---

## 1. EXECUTIVE SUMMARY & FORENSIC MANDATE

This forensic audit establishes the rigorous, immutable pre-remediation baseline for the 362 acupuncture point records within the **MSK-Therapy-OS** platform.
Milestone P9.5 succeeds Milestone P9.4 (Definitive Meridian Atlas) and addresses the critical P0 quality backlog regarding anatomical accuracy, classification discrepancy, and empirical verification.

### Working Principles Enforced:
Constraint-first → Artifact-first → Evidence-first → Test-first → Clinical Safety-first

### Primary Audit Findings:
1. **Total Unique Point Inventory:** Exactly **362 records** (361 standard classical WHO acupuncture points + 1 clinical extension record `GV24+` / Yintang).
2. **Quality Classification Discrepancy Resolved:**
   - In pre-P9.4 audit documentation (`P9_4_361_ACUPOINT_DATA_QUALITY_MATRIX.md`), the catalog was frozen at **18 Class A** and **344 Class D** (0 Class B).
   - In the P9.4 runtime engine (`spatial_resolver.py`, `point_localization_rules.py`, `points.py`), the formalization of 68 localization rules elevated 52 points, establishing the runtime state of:
     - **CLASS_A (Independently Audited Canonical Anchors):** **18 points (5.0%)**
     - **CLASS_B (Rule-Derived via WHO 2008 Standard):** **52 points (14.4%)**
     - **CLASS_C (Surface-Registered Calibrated Approximations):** **0 points (0.0%)**
     - **CLASS_D (Legacy Uncalibrated Surface Raycasts):** **292 points (80.7%)**
     - **TOTAL:** **362 points (100.0%)**
   - The discrepancy between the documentation matrix (344 Class D) and the specification (292 Class D) is forensic proof of an un-reconciled documentation snapshot prior to rule engine integration.
3. **Anatomical Anomaly Discovered in Legacy Data:**
   - Record `KI3` in `acupuncture_3d.json` contains a left-sided lateral coordinate (`X = -0.07589m`) in an otherwise strictly right-sided canonical avatar template (+X). This caused an inverted medial-lateral registration error in legacy releases, rectified when evaluated via the WHO 2008 rule engine.
4. **False Verification Metrics Identified:**
   - Database table `meridian_geometry_validation` previously seeded `anatomical_pass_rate = 100.0` and dashboard hardcoded `pass_rate = 100.0` and `route_status = VERIFIED_CORRIDOR` despite 292 points remaining uncalibrated Class D legacy raycasts.
   - P9.5 formally repudiates all hardcoded 100% metrics and establishes empirical, computed verification metrics.

---

## 2. SOURCE OF TRUTH & IMMUTABLE CHECKSUMS

Before any modifications are applied in Phase B, the SHA-256 hashes of all input data, rule engines, geometry solvers, and audit documents were computed and locked:

| Component / File Path | SHA-256 Checksum | Baseline Integrity Status |
| :--- | :--- | :--- |
| `msk_therapy_os/static/atlas/data/acupuncture_3d.json` | `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df` | **CANONICAL FROZEN** |
| `msk_therapy_os/spatial_resolver.py` | `d0e4ca0efd806405914351cfa192ad32d1a67b0cedda3ff8d5255707978012ae` | **BASELINE AUDITED** |
| `msk_therapy_os/point_localization_rules.py` | `08e70571dcf843ead13714e636c466ebd6313013cd30252865ca1dee2407fef6` | **BASELINE AUDITED** |
| `msk_therapy_os/landmark_registry.py` | `1a0c51245e632460faf37d477aeec5dced43e580668d1ce125590842a4ade663` | **BASELINE AUDITED** |
| `msk_therapy_os/cun_scaling.py` | `b33a1346e18c10f9fe4db3ee4e5e6f6100cd63915d31578efd2e3cedf8db14e6` | **BASELINE AUDITED** |
| `msk_therapy_os/points.py` | `82a04f021924a2f041258df7a78f7cd9a83dd74b311ea0366a391b1409eab348` | **BASELINE AUDITED** |
| `msk_therapy_os/meridian_route_graph.py` | `1ee2bc24cc1cee78aaffbd02c65c0a21260e786154e29d55f4c4860e581e1686` | **BASELINE AUDITED** |
| `msk_therapy_os/meridian_surface_engine.py` | `64bd2007ecac93189240d10d893d7e9268a20c3b974c55633f133e580f336237` | **BASELINE AUDITED** |
| `tests/test_p9_4_definitive_atlas.py` | `35ec674c49c01c0b6a949b762e24fa7161301f0f9f5cf7d0e16b8f6f7ea54a74` | **BASELINE 155 TESTS PASS** |
| `1docs/specs/P9_4_REFERENCE_DRIVEN_MERIDIAN_ATLAS.md` | `4d126ac87d9baf07a7cfa00fbe4fe4af4d580314e0a67a1393516b3e27e7a631` | **SPECIFICATION SOT** |
| `1docs/audits/P9_4_FINAL_ENGINEERING_HANDOFF.md` | `61c084aaa84cc694da6326005e040edc9369a48a595d08ce608b66ae97be5929` | **HANDOFF SOT** |
| `1docs/audits/P9_4_361_ACUPOINT_DATA_QUALITY_MATRIX.md` | `5a2304e0ebffcb26632bac1291143ee5669600a13efa1a9e3ee726aa64764c0b` | **PRE-P9.4 AUDIT SOT** |
| `1docs/audits/P9_4_FULL_ACUPOINT_SOURCE_AUDIT.md` | `a601c5b17aa26518015302745f1225854528f70fe12c1b02be95ca5fa8bfa503` | **FORENSIC AUDIT SOT** |

---

## 3. FULL INVENTORY AUDIT & CHANNEL DECOMPOSITION

The repository implements the standard 14 classical meridian channels. All 362 points were validated for code syntax, channel association, laterality, and coordinate domain:

| Meridian Code | Channel Name (EN / ZH / VI) | Classical Points | Extension Points | Total Records | Class A (Audited) | Class B (Rules) | Class D (Legacy) | Laterality |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **LU** | Lung / 手太阴肺经 / Kinh Phế | 11 | 0 | 11 | 1 | 10 | 0 | Bilateral (R/L) |
| **LI** | Large Intestine / 手阳明大肠经 / Kinh Đại Trường | 20 | 0 | 20 | 2 | 4 | 14 | Bilateral (R/L) |
| **ST** | Stomach / 足阳明胃经 / Kinh Vị | 45 | 0 | 45 | 2 | 0 | 43 | Bilateral (R/L) |
| **SP** | Spleen / 足太阴脾经 / Kinh Tỳ | 21 | 0 | 21 | 0 | 6 | 15 | Bilateral (R/L) |
| **HT** | Heart / 手少阴心经 / Kinh Tâm | 9 | 0 | 9 | 1 | 0 | 8 | Bilateral (R/L) |
| **SI** | Small Intestine / 手太阳小肠经 / Kinh Tiểu Trường | 19 | 0 | 19 | 0 | 5 | 14 | Bilateral (R/L) |
| **BL** | Bladder / 足太阳膀胱经 / Kinh Bàng Quang | 67 | 0 | 67 | 5 | 0 | 62 | Bilateral (R/L) |
| **KI** | Kidney / 足少阴肾经 / Kinh Thận | 27 | 0 | 27 | 0 | 8 | 19 | Bilateral (R/L) |
| **PC** | Pericardium / 手厥阴心包经 / Kinh Tâm Bào | 9 | 0 | 9 | 1 | 2 | 6 | Bilateral (R/L) |
| **TE** | Triple Energizer / 手少阳三焦经 / Kinh Tam Tiêu | 23 | 0 | 23 | 0 | 5 | 18 | Bilateral (R/L) |
| **GB** | Gallbladder / 足少阳胆经 / Kinh Đởm | 44 | 0 | 44 | 2 | 0 | 42 | Bilateral (R/L) |
| **LR** | Liver / 足厥阴肝经 / Kinh Can | 14 | 0 | 14 | 0 | 5 | 9 | Bilateral (R/L) |
| **GV** | Governor Vessel / 督脉 / Đốc Mạch | 28 | 1 (`GV24+`) | 29 | 3 | 2 | 24 | Sagittal Midline |
| **CV** | Conception Vessel / 任脉 / Nhâm Mạch | 24 | 0 | 24 | 1 | 5 | 18 | Sagittal Midline |
| **TOTAL** | **All 14 Channels** | **361** | **1** | **362** | **18** | **52** | **292** | **100% Coverage** |

---

## 4. AUDIT OF LOCALIZATION RULES & RUNTIME APPLICATION

The localization rules engine (`msk_therapy_os/point_localization_rules.py`) contains **68 authoritative rules**.
An exhaustive execution test was conducted against `AcupointLocalizationEngine`:
- **Rules evaluated:** 68 / 68 (100% execution pass rate; 0 runtime exceptions).
- **Overlap with Class A (`AUDITED_CANONICAL_POINTS`):** Exactly 16 rules (`LI4`, `LU5`, `BL40`, `PC6`, `HT3`, `ST35`, `GV14`, `GB21`, `GB20`, `ST36`, `LI15`, `BL10`, `BL11`, `BL12`, `BL13`, `CV22`).
- **Active Class B Points:** $68 - 16 = 52$ points.
- **Audited Class A Points lacking rules in rule engine:** Exactly 2 points (`GV15`, `GV16`), which are defined as canonical anchors directly in `AUDITED_CANONICAL_POINTS`.

---

## 5. RECONCILIATION OF THE 52 CLASS B POINTS

The 52 points resolved as Class B in the P9.4 runtime are:
`CV12`, `CV17`, `CV2`, `CV4`, `CV8`, `GV20`, `GV4`, `KI1`, `KI10`, `KI11`, `KI16`, `KI27`, `KI3`, `KI6`, `KI7`, `LI1`, `LI11`, `LI20`, `LI5`, `LR1`, `LR13`, `LR14`, `LR3`, `LR8`, `LU1`, `LU10`, `LU11`, `LU2`, `LU3`, `LU4`, `LU6`, `LU7`, `LU8`, `LU9`, `PC3`, `PC7`, `SI1`, `SI11`, `SI19`, `SI3`, `SI8`, `SP1`, `SP10`, `SP15`, `SP21`, `SP6`, `SP9`, `TE1`, `TE14`, `TE17`, `TE23`, `TE5`.

In `P9_4_361_ACUPOINT_DATA_QUALITY_MATRIX.md`, these 52 points were listed as Class D because that document was produced from a pre-rule static export. 
In the P9.5 provenance matrix and reconciliation report, each of these 52 points is verified with its exact WHO clause and parametric formula.

---

## 6. GEOMETRIC & COORDINATE FRAME INTEGRITY

1. **Coordinate Frame:** Right-Handed Cartesian ($+X$ Right, $+Y$ Superior/Up, $+Z$ Anterior/Front).
2. **Units:** Strict SI Meters ($[m]$).
3. **Bounding Box Enclosure:**
   - $X \in [-0.0759, +0.2860]\text{ m}$ (Excluding KI3 legacy anomaly: $X \in [0.0000, +0.2860]\text{ m}$ for right-side template)
   - $Y \in [+0.0031, +1.7188]\text{ m}$
   - $Z \in [-0.1442, +0.1245]\text{ m}$
4. **Anatomical Envelope Compliance:** All 362 coordinates fall strictly within the defined `BODY_ENVELOPE` ($X \in [-0.35, +0.35]$, $Y \in [-0.05, +1.76]$, $Z \in [-0.25, +0.25]$).

---

## 7. BASELINE AUDIT SIGN-OFF

The baseline state is formally certified as:
- **CLASS_A:** 18 (Independently Verified Canonical Anchors)
- **CLASS_B:** 52 (Landmark-Derived WHO Standard)
- **CLASS_C:** 0
- **CLASS_D:** 292 (Legacy Surface Raycast - Uncalibrated)
- **TOTAL:** 362 points

Signed off by Independent QA Audit & Computational Anatomy Engineering Team.
