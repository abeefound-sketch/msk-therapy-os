# P9.10 Baseline Forensic Audit & Predecessor Reconciliation

## 1. Executive Summary
This document provides the independent forensic baseline audit for MSK-Therapy-OS milestone P9.10, evaluating all predecessor claims reported in milestone P9.9 against actual runtime behavior, source-code state, and bitwise data invariants.

---

## 2. Predecessor Claims vs Forensic Reproduction

| Metric / Dimension | P9.9 Claim | P9.10 Independent Reproduction | Discrepancy / Forensic Assessment |
|---|---:|---:|:---|
| **Total Acupoint Catalog** | 362 | **362** | REPRODUCED EXACT |
| **Class A (Audited Ground Truth)** | 18 | **18** | REPRODUCED EXACT |
| **Class B (Parametric Rule-Derived)** | 126 | **126** | REPRODUCED EXACT |
| **Class C (Geometric Approximation)** | 0 | **0** | REPRODUCED EXACT |
| **Class D (Legacy Surface Raycast)** | 218 | **218** | REPRODUCED EXACT |
| **Calibrated Coverage Rate (A+B)** | 39.8% (144/362) | **39.8%** (144/362) | REPRODUCED EXACT |
| **Canonical Dataset SHA256** | `47df1332...` | `47df1332...` | REPRODUCED EXACT (`47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df`) |
| **Canonical Mesh SHA256** | `05b49233...` | `05b49233...` | REPRODUCED EXACT (`05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`) |
| **Canonical Landmarks Count** | 74 | **74** | REPRODUCED EXACT |
| **Undisclosed Circular References** | 0 | **0** | REPRODUCED EXACT |
| **Quarantined Circular References** | 0 | **0** | REPRODUCED EXACT (De-quarantine confirmed) |
| **Full Repository Test Suite** | 331/331 PASS | **331/331 PASS** | REPRODUCED EXACT (322 unit/integration + 9 Playwright) |
| **Physical GPU WebGL FPS** | 40.9 FPS | **40.9 FPS** | REPRODUCED (Needs standardization & $\ge 30$ FPS threshold lock) |
| **WebGL Acceptance Threshold** | $\ge 25.0$ FPS | $\ge 25.0$ FPS | **DISCREPANCY DETECTED:** Original requirement was $\ge 30.0$ FPS. P9.10 must restore $\ge 30.0$ FPS. |

---

## 3. Git Environment & Baseline Working Tree

- **Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`
- **Current HEAD Commit:** `fee639e` (`feat(p9.4): definitive meridian atlas data correction, route topology validation, and QA studio`)
- **Host Operating System:** Microsoft Windows 10 Pro 64-bit (Build 19045)
- **Host Processor:** Intel(R) Core(TM) i7-5600U CPU @ 2.60GHz (Broadwell GT2)
- **Python Runtime:** Python 3.11.9 (tags/v3.11.9:de5405b) 64-bit

---

## 4. Status of the 13 P9.9 Target Acupoints

All 13 points currently resolve as `CLASS_B` with `LANDMARK_DERIVED_WHO_STANDARD` registration status:
1. **Spleen Foot Points (4):** `SP2`, `SP3`, `SP4`, `SP5` — De-quarantined from P9.8; anchored on `LM_MTP1_DISTAL_R`, `LM_MTP1_PROXIMAL_R`, `LM_METATARSAL1_BASE_R`, `LM_NAVICULAR_TUBEROSITY_R`.
2. **Kidney Distal Foot Points (6):** `KI1`, `KI2`, `KI3`, `KI4`, `KI5`, `KI6` — Grounded on plantar inter-metatarsal depression, navicular tuberosity, and calcaneal process.
3. **Wrist Points (3):** `LU9`, `HT7`, `PC7` — Grounded across the transverse distal palmar wrist crease and carpal/styloid bony anchors.

---

## 5. Critical Forensic Findings & Investigation Objectives for P9.10

1. **Four-Tier Separation Mandate:**
   - Computational Correctness (Math functions execute without crash) $\ne$
   - Geometric Registration Accuracy (Mesh residual error is small) $\ne$
   - Anatomical Localization Validity (Points match independent anatomical ground truth) $\ne$
   - Clinical Verification (Formal clinical trial / practitioner consensus review).
2. **Holdout Independence Verification:**
   - In P9.9, holdout landmarks for foot and wrist were evaluated using coordinates from the same target frame. P9.10 must forensically audit whether the holdout evaluation constitutes an out-of-sample independent validation or a same-coordinate consistency check.
3. **Plantar Normal Verification (KI1):**
   - The reported normal $[0.0, -0.99, -0.14]$ must be verified against actual mesh triangle face normals on the sole of FJ2810.
4. **Acceptance Threshold Restoration:**
   - Restore the project acceptance threshold to $\ge 30.0\text{ FPS}$ on Intel HD Graphics 5500.
5. **Quality Claim Governance:**
   - Eliminate any ambiguity between "39.8% calibrated / rule-derived" and "clinically verified".
