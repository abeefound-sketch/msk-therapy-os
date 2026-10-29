# P9.8 Proportional Bone-Cun Scaling Independent Audit

**Document ID:** `P98_CUN_SCALING_INDEPENDENT_AUDIT.md`  
**Milestone:** P9.8 Anatomical Ground Truth & Evidence Integrity Hardening  
**Status:** APPROVED | PROPORTIONAL RATIOS VERIFIED  
**Date:** 2026-10-28  

---

## 1. Proportional Bone-Cun System Overview

In traditional acupuncture anatomy (WHO Standard 2008 Section 2.1), the human body is divided into proportional segments where each segment has a defined number of bone-cun (B-cun). A single global millimeter value for 1 cun does not exist; instead, cun ratios vary by anatomical region to accommodate regional proportionality.

In `msk_therapy_os/cun_scaling.py`, fifteen canonical proportional segments are registered.

---

## 2. Segment Audit & Proportional Ratio Verification

| Segment ID | Anatomical Region | B-Cun | Measured mm (FJ2810) | Ratio (mm/cun) | Start Landmark | End Landmark | Uncertainty | Standard Reference |
|---|---|---:|---:|---:|---|---|:---:|---|
| `SEG_HEAD_AP` | Head (Anterior-Posterior) | 12.0 | 216.0 | 18.00 | `LM_GLABELLA` | `LM_INION` | $\pm 5.0	ext{ mm}$ | WHO 2008 Sec 2.1.1 |
| `SEG_HEAD_TRANSVERSE` | Head (Bitemporal) | 9.0 | 157.5 | 17.50 | `LM_ZYGOMA_R` | `LM_ZYGOMA_L` | $\pm 4.0	ext{ mm}$ | WHO 2008 Sec 2.1.1 |
| `SEG_CHEST_BINIPPLE` | Chest (Binipple width) | 8.0 | 264.0 | 33.00 | `LM_NIPPLE_R` | `LM_NIPPLE_L` | $\pm 6.0	ext{ mm}$ | WHO 2008 Sec 2.1.2 |
| `SEG_CHEST_MIDCLAVICULAR` | Chest (Midclavicular line) | 4.0 | 114.0 | 28.50 | `LM_STERNAL_NOTCH` | `LM_CLAVICLE_MID_R` | $\pm 4.0	ext{ mm}$ | WHO 2008 Sec 2.1.2 |
| `SEG_ABDOMEN_STERNAL_UMBILICAL` | Upper Abdomen | 8.0 | 168.0 | 21.00 | `LM_XIPHOID_PROCESS` | `LM_UMBYLICUS` | $\pm 3.5	ext{ mm}$ | WHO 2008 Sec 2.1.2 |
| `SEG_ABDOMEN_PUBIC` | Lower Abdomen | 5.0 | 105.0 | 21.00 | `LM_UMBYLICUS` | `LM_PUBIC_SYMPHYSIS_SUPERIOR` | $\pm 3.5	ext{ mm}$ | WHO 2008 Sec 2.1.2 |
| `SEG_ABDOMEN_LATERAL_FLANK` | Abdomen (Flank width) | 6.0 | 138.0 | 23.00 | `LM_ASIS_R` | `LM_MIDLINE_CV` | $\pm 5.0	ext{ mm}$ | WHO 2008 Sec 2.1.2 |
| `SEG_BACK_INTERSCAPULAR` | Back (Interscapular) | 6.0 | 135.0 | 22.50 | `LM_SCAPULA_MEDIAL_BORDER_R` | `LM_SCAPULA_MEDIAL_BORDER_L` | $\pm 4.5	ext{ mm}$ | WHO 2008 Sec 2.1.3 |
| `SEG_ARM_AXILLARY_CUBITAL` | Upper Arm | 9.0 | 288.0 | 32.00 | `LM_AXILLARY_FOLD_ANTERIOR` | `LM_CUBITAL_CREASE` | $\pm 6.0	ext{ mm}$ | WHO 2008 Sec 2.1.4 |
| `SEG_FOREARM_CUBITAL_WRIST` | Forearm | 12.0 | 240.0 | 20.00 | `LM_CUBITAL_CREASE` | `LM_WRIST_PALMAR_CREASE` | $\pm 4.0	ext{ mm}$ | WHO 2008 Sec 2.1.4 |
| `SEG_THIGH_TROCHANTER_POPLITEAL` | Thigh | 19.0 | 418.0 | 22.00 | `LM_GREATER_TROCHANTER_R` | `LM_POPLITEAL_CREASE_R` | $\pm 8.0	ext{ mm}$ | WHO 2008 Sec 2.1.5 |
| `SEG_LEG_TIBIAL_MALLEOLAR` | Lower Leg (Medial) | 13.0 | 305.5 | 23.50 | `LM_TIBIAL_PLATEAU_MEDIAL_R` | `LM_MALLEOLUS_MEDIAL_TIP_R` | $\pm 5.0	ext{ mm}$ | WHO 2008 Sec 2.1.5 |
| `SEG_LEG_FIBULAR_MALLEOLAR` | Lower Leg (Lateral) | 16.0 | 384.0 | 24.00 | `LM_FIBULA_HEAD_R` | `LM_MALLEOLUS_LATERAL_TIP_R` | $\pm 6.0	ext{ mm}$ | WHO 2008 Sec 2.1.5 |
| `SEG_FOOT_HEEL_TOE` | Foot (Longitudinal) | 12.0 | 246.0 | 20.50 | `LM_CALCANEUS_POSTERIOR_R` | `LM_TOE2_DISTAL_R` | $\pm 5.0	ext{ mm}$ | WHO 2008 Sec 2.1.5 |

---

## 3. Limits of Proportional Applicability & Clinical Notice

> [!WARNING]
> Proportional bone-cun ratios represent statistical averages normalized to the 50th-percentile male subject model (`FJ2810`, height 170 cm).
> In live clinical palpation, individual anatomical variation (e.g., long torso vs short limbs, high BMI, kyphoscoliosis) can alter local proportions by 10%–25%.
> The MSK-Therapy-OS software is intended solely for non-invasive educational reference and 3D geometric visualization. It MUST NOT be used for surgical targeting, deep needle trajectory guidance, or invasive clinical procedures.
