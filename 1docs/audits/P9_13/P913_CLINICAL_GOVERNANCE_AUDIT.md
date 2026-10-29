# MSK-Therapy-OS | Clinical Governance, Cardinality & Safety Audit
**Document ID:** `P913_CLINICAL_GOVERNANCE_AUDIT`  
**Milestone:** P9.13 Production Hardening & Ground-Truth Readiness  
**Status:** COMPLETE & RATIFIED  
**Auditor:** Independent Clinical Safety & Software Verification Auditor  

---

## 1. Core Clinical Governance Premise

### 1.1 The Crucial Distinction
> **100% Technical Calibration is NOT synonymous with Clinical Verification.**

In Milestone P9.12 Tranche 3, all 362 acupoint locations were calibrated through parametric B-cun rules anchored to BodyParts3D FJ2810 anatomical landmarks. While this resolved the engineering problem of eliminating legacy uncalibrated surface raycasts (0 Class D points remaining), it **does not** constitute multi-center clinical consensus or randomized clinical trial verification.

Under Milestone P9.13, MSK-Therapy-OS formalizes this boundary into enforceable, immutable contracts:
- **`CALIBRATED_COVERAGE`:** $100.0\%$ (18 Class A anchors + 344 Class B parametric points).
- **`TIER_4_CLINICAL_VERIFICATION`:** Strictly $0.0\%$ ($0$ points).
- **`CLINICAL_DEPTH_GUIDANCE_ALLOWED`:** Strictly `False` across all 362 points.

---

## 2. Catalog Cardinality Reconciliation: 361 vs 362

A fundamental audit question addressed in P9.13 is the discrepancy between the standard WHO 361 classical acupoints and the 362 entries maintained in MSK-Therapy-OS.

### 2.1 The Standard 361 Classical Meridian Acupoints (WHO 2008)
The World Health Organization 2008 Western Pacific Region standard (*WHO Standard Acupuncture Point Locations in the Western Pacific Region*) specifies 361 classical acupuncture points distributed across 14 channels:

| Meridian Channel | Code | WHO Standard Count | System Point Count | Note |
|---|---|---:|---:|---|
| Lung | LU | 11 | 11 | Complete classical channel |
| Large Intestine | LI | 20 | 20 | Complete classical channel |
| Stomach | ST | 45 | 45 | Complete classical channel |
| Spleen | SP | 21 | 21 | Complete classical channel |
| Heart | HT | 9 | 9 | Complete classical channel |
| Small Intestine | SI | 19 | 19 | Complete classical channel |
| Bladder | BL | 67 | 67 | Complete classical channel |
| Kidney | KI | 27 | 27 | Complete classical channel |
| Pericardium | PC | 9 | 9 | Complete classical channel |
| Triple Energizer | TE | 23 | 23 | Complete classical channel |
| Gallbladder | GB | 44 | 44 | Complete classical channel |
| Liver | LR | 14 | 14 | Complete classical channel |
| Conception Vessel | CV | 24 | 24 | Complete Ren Mai channel |
| Governor Vessel | GV | 28 | **29** | Includes 28 classical + 1 midline extra point (`GV24+`) |
| **Total** | | **361** | **362** | Full catalog |

### 2.2 The 362nd Record: `GV24+` (Yintang / M-HN3)
- **Origin:** In Chinese National Standard GB/T 12346-2006 and 2021, as well as the BodyParts3D digital reference mesh, the classical extra point **Yintang** (EX-HN3 / M-HN3) is integrated directly onto the anterior cranial midline of the Governor Vessel (Du Mai) trajectory between the medial ends of the eyebrows, denoted as `GV24+` (midline between GV24 Shenting and the nasion).
- **P9.13 Resolution:**
  - The catalog preserves all 362 records to avoid breaking existing relational keys, 3D mesh bindings, and downstream client integrations.
  - The API and coverage dashboard explicitly expose:
    - `"standard_catalog_count": 361`
    - `"extended_catalog_count": 1`
    - `"extended_points": ["GV24+"]`
  - This ensures 100% interoperability with both strict WHO 361-point validators and 362-point national/BodyParts3D schemas.

---

## 3. Clinical Safety & Depth Guidance Prohibition

### 3.1 Anatomical Hazards of Invasive Depth Inference
Surface landmark localization provides external boundary coordinates on the epidermis. Inferring internal needle insertion depth or angle from surface coordinates poses severe clinical hazards:
1. **Pneumothorax Risk:** Points over the thorax and apical lung regions (e.g. `BL13` Feishu, `GB21` Jianjing, `KI25` Shencang) lie within $15-25\text{ mm}$ of the parietal pleura in asthenic individuals.
2. **Visceral Puncture Risk:** Upper abdominal points (e.g. `CV12` Zhongwan, `ST21` Liangmen) lie anterior to the stomach and liver; deep insertion can cause peritonitis or vascular hemorrhage.
3. **Spinal Cord / Dural Risk:** Upper cervical posterior midline points (`GV15` Yamen, `GV16` Fengfu) lie adjacent to the foramen magnum and cisterna cerebellomedullaris. Inappropriate needle trajectory risks puncturing the medulla oblongata or spinal cord.

### 3.2 Systemic Fail-Closed Guardrails
To prevent any clinical misapplication:
1. `clinical_depth_guidance_allowed` is hardcoded to `False` in all uncertainty matrices and API responses.
2. The UI displays an un-dismissible clinical safety banner:
   > *"Visual and educational guidance only. Strictly non-invasive; zero surgical or procedural depth claims."*
3. The system enforces an absolute refusal to provide 3D needle depth trajectory calculations.

---

## 4. Audit Sign-Off

The clinical safety and governance architecture of MSK-Therapy-OS complies with international software safety standards for medical education and visualization. No clinical claims are made, and all points remain strictly non-invasive.
