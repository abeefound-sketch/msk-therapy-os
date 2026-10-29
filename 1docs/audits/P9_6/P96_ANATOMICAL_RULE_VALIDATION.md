# P9.6 Phase 2 Anatomical Acupoint Remediation — Rule Validation Report

**Project:** MSK-Therapy-OS  
**Milestone:** P9.6 Phase 2 Remediation  
**Status:** APPROVED / 30 CALIBRATED RULES  
**Auditor:** Principal Computational Anatomy Engineer & Independent QA Auditor  
**Date:** 2026-10-28  
**Reference Mesh:** BodyParts3D 4.0 FJ2810  
**Ontological Standard:** WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008)  

---

## 1. Scope & Objective

Milestone P9.6 addresses the second wave of high-risk anatomical acupoint remediation, elevating exactly **30 Class D points to Class B** via rigorous, deterministic WHO 2008 mathematical rules and BodyParts3D FJ2810 canonical landmarks.

The 30 remediated points are partitioned into three high-risk anatomical groups:
- **Group A (Spleen Meridian - SP):** 8 points (`SP2, SP3, SP4, SP5, SP7, SP8, SP14, SP16`).
- **Group B (Kidney Meridian - KI):** 12 points (`KI12, KI13, KI14, KI15, KI17, KI18, KI19, KI20, KI21, KI22, KI23, KI24`).
- **Group C (Bladder Outer Column - BL):** 10 points (`BL41, BL42, BL43, BL44, BL45, BL46, BL47, BL48, BL49, BL50`).

---

## 2. Group A: Spleen Meridian Anatomical Specifications

### 2.1 Medial Foot & Ankle Bony Anchors (`SP2, SP3, SP4, SP5`)
- **SP2 (Dadu / 大都):**
  - *WHO 2008 Clause:* p. 77: "On the great toe, in the depression distal and inferior to the first metatarsophalangeal joint, at the border between the red and white flesh."
  - *FMA Anchor:* `FMA:34426` (First Metatarsophalangeal Joint Distoinferior)
  - *Landmark Reference:* `LM_MTP1_DISTAL_R` `[0.0732, 0.0261, 0.0781]`
  - *Method:* `JOINT_DEPRESSION`
  - *Tolerance:* 3.0 mm | *Uncertainty:* 6.0 mm
- **SP3 (Taibai / 太白):**
  - *WHO 2008 Clause:* p. 78: "On the medial aspect of the foot, in the depression proximal and inferior to the first metatarsophalangeal joint, at the border between the red and white flesh."
  - *FMA Anchor:* `FMA:34426` (First Metatarsophalangeal Joint Proximoinferior)
  - *Landmark Reference:* `LM_MTP1_PROXIMAL_R` `[0.0750, 0.0460, 0.0570]`
  - *Method:* `JOINT_DEPRESSION`
  - *Tolerance:* 3.0 mm | *Uncertainty:* 6.0 mm
- **SP4 (Gongsun / 公孙):**
  - *WHO 2008 Clause:* p. 78: "On the medial aspect of the foot, antero-inferior to the base of the first metatarsal bone, at the border between the red and white flesh."
  - *FMA Anchor:* `FMA:24497` (Base of First Metatarsal Bone Anteroinferior)
  - *Landmark Reference:* `LM_METATARSAL1_BASE_R` `[0.0739, 0.0670, 0.0393]`
  - *Method:* `LANDMARK_DEFINED`
  - *Tolerance:* 3.0 mm | *Uncertainty:* 6.0 mm
- **SP5 (Shangqiu / 商丘):**
  - *WHO 2008 Clause:* p. 79: "On the medial aspect of the foot, in the depression distal and inferior to the medial malleolus, midway between the tuberosity of the navicular bone and the tip of the medial malleolus."
  - *FMA Anchor:* `FMA:33862` (Navicular Tuberosity Anteroinferior Depression)
  - *Landmark Reference:* `LM_NAVICULAR_TUBEROSITY_R` `[0.0462, 0.0719, -0.0019]`
  - *Method:* `JOINT_DEPRESSION`
  - *Tolerance:* 3.0 mm | *Uncertainty:* 6.0 mm

### 2.2 Medial Tibial Border Proportional Segment (`SP7, SP8`)
Per WHO 2008 Section 2.1.5, the medial leg segment between the tip of the medial malleolus (`LM_MED_MALLEOLUS_R`) and the inferior border of the medial condyle of the tibia (`LM_TIBIA_MEDIAL_CONDYLE_R`) is defined as **13 B-cun**.
- **SP7 (Lougu / 漏谷):**
  - *WHO 2008 Clause:* p. 80: "On the tibial aspect of the leg, posterior to the medial border of the tibia, 6 B-cun superior to the prominence of the medial malleolus."
  - *FMA Anchor:* `FMA:24476` (Medial Tibial Border 6 cun superior to Medial Malleolus)
  - *Proportional Fraction:* $6.0 / 13.0 \approx 0.4615$
  - *Resolved Position:* `[0.054308, 0.241692, 0.001154]`
  - *Tolerance:* 4.0 mm | *Uncertainty:* 8.0 mm
- **SP8 (Diji / 地机):**
  - *WHO 2008 Clause:* p. 80: "On the tibial aspect of the leg, posterior to the medial border of the tibia, 3 B-cun inferior to SP9."
  - *FMA Anchor:* `FMA:24476` (Medial Tibial Border 3 cun inferior to SP9)
  - *Proportional Fraction:* $(13.0 - 3.0) / 13.0 = 10.0 / 13.0 \approx 0.7692$
  - *Resolved Position:* `[0.039846, 0.348154, -0.008077]`
  - *Tolerance:* 4.0 mm | *Uncertainty:* 8.0 mm

### 2.3 Abdominal Lateral Rectus Column (`SP14, SP16`)
- **SP14 (Fujie / 腹结):**
  - *WHO 2008 Clause:* p. 84: "In the lower abdominal region, 1.3 B-cun inferior to the center of the umbilicus, 4 B-cun lateral to the anterior midline."
  - *FMA Anchor:* `FMA:14557` (Lower Abdomen / Lateral Rectus Abdominis)
  - *Proportional Fraction:* $1.3 / 5.0 = 0.2600$ along `LM_UMBILICUS` $\to$ `LM_PUBIC_SYMPHYSIS`
  - *Lateral Offset:* 4.0 B-cun (`0.1320 m`)
  - *Resolved Position:* `[0.132000, 0.983880, 0.105760]`
  - *Tolerance:* 4.0 mm | *Uncertainty:* 8.0 mm
- **SP16 (Fuai / 腹哀):**
  - *WHO 2008 Clause:* p. 85: "In the upper abdominal region, 3 B-cun superior to the center of the umbilicus, 4 B-cun lateral to the anterior midline."
  - *FMA Anchor:* `FMA:14556` (Upper Abdomen / Lateral Rectus Abdominis)
  - *Proportional Fraction:* $3.0 / 8.0 = 0.3750$ along `LM_UMBILICUS` $\to$ `LM_XIPHOSTERNAL_JOINT`
  - *Lateral Offset:* 4.0 B-cun (`0.1320 m`)
  - *Resolved Position:* `[0.132000, 1.090500, 0.106750]`
  - *Tolerance:* 4.0 mm | *Uncertainty:* 8.0 mm

---

## 3. Group B: Kidney Meridian Anatomical Specifications

### 3.1 Lower Abdominal Parasagittal Line (`KI12–KI15`)
Located **0.5 B-cun** lateral to anterior midline along the 5 B-cun umbilical-pubic segment (`LM_UMBILICUS` to `LM_PUBIC_SYMPHYSIS`):

| Point | WHO 2008 Citation | Landmark Anchors | Proportional Fraction | Resolved Position [X, Y, Z] (m) | Tolerance / Uncertainty |
|---|---|---|---:|---|---|
| **KI15** (Zhongzhu) | p. 178: 1 cun inferior to umbilicus | Umbilicus $\to$ Pubic Symphysis | $1.0 / 5.0 = 0.20$ | `[0.016500, 0.993600, 0.107200]` | 3.0 mm / 6.0 mm |
| **KI14** (Siman) | p. 178: 2 cun inferior to umbilicus | Umbilicus $\to$ Pubic Symphysis | $2.0 / 5.0 = 0.40$ | `[0.016500, 0.961200, 0.102400]` | 3.0 mm / 6.0 mm |
| **KI13** (Qixue) | p. 177: 3 cun inferior to umbilicus | Umbilicus $\to$ Pubic Symphysis | $3.0 / 5.0 = 0.60$ | `[0.016500, 0.928800, 0.097600]` | 3.0 mm / 6.0 mm |
| **KI12** (Dahe) | p. 177: 4 cun inferior to umbilicus | Umbilicus $\to$ Pubic Symphysis | $4.0 / 5.0 = 0.80$ | `[0.016500, 0.896400, 0.092800]` | 3.0 mm / 6.0 mm |

### 3.2 Upper Abdominal Parasagittal Line (`KI17–KI21`)
Located **0.5 B-cun** lateral to anterior midline along the 8 B-cun xiphisternal-umbilical segment (`LM_UMBILICUS` to `LM_XIPHOSTERNAL_JOINT`):

| Point | WHO 2008 Citation | Landmark Anchors | Proportional Fraction | Resolved Position [X, Y, Z] (m) | Tolerance / Uncertainty |
|---|---|---|---:|---|---|
| **KI17** (Shangqu) | p. 179: 2 cun superior to umbilicus | Umbilicus $\to$ Xiphisternal | $2.0 / 8.0 = 0.250$ | `[0.016500, 1.069000, 0.108500]` | 3.0 mm / 6.0 mm |
| **KI18** (Shiguan) | p. 180: 3 cun superior to umbilicus | Umbilicus $\to$ Xiphisternal | $3.0 / 8.0 = 0.375$ | `[0.016500, 1.090500, 0.106750]` | 3.0 mm / 6.0 mm |
| **KI19** (Yindu) | p. 180: 4 cun superior to umbilicus | Umbilicus $\to$ Xiphisternal | $4.0 / 8.0 = 0.500$ | `[0.016500, 1.112000, 0.105000]` | 3.0 mm / 6.0 mm |
| **KI20** (Futonggu) | p. 181: 5 cun superior to umbilicus | Umbilicus $\to$ Xiphisternal | $5.0 / 8.0 = 0.625$ | `[0.016500, 1.133500, 0.103250]` | 3.0 mm / 6.0 mm |
| **KI21** (Youmen) | p. 181: 6 cun superior to umbilicus | Umbilicus $\to$ Xiphisternal | $6.0 / 8.0 = 0.750$ | `[0.016500, 1.155000, 0.101500]` | 3.0 mm / 6.0 mm |

### 3.3 Thoracic Intercostal Parasagittal Line (`KI22–KI24`)
Located **2.0 B-cun** lateral to anterior midline in the intercostal spaces between sternal angle (`LM_STERNAL_ANGLE`) and xiphisternal synchondrosis (`LM_XIPHOSTERNAL_JOINT`):

| Point | WHO 2008 Citation | Intercostal Space | Lateral Offset | Resolved Position [X, Y, Z] (m) | Tolerance / Uncertainty |
|---|---|---|---:|---|---|
| **KI22** (Bulang) | p. 182: 5th intercostal space | 5th Intercostal | 2.0 B-cun (`0.066 m`) | `[0.066000, 1.198000, 0.098000]` | 4.0 mm / 8.0 mm |
| **KI23** (Shenfeng) | p. 182: 4th intercostal space | 4th Intercostal | 2.0 B-cun (`0.066 m`) | `[0.066000, 1.250614, 0.092672]` | 4.0 mm / 8.0 mm |
| **KI24** (Lingxu) | p. 183: 3rd intercostal space | 3rd Intercostal | 2.0 B-cun (`0.066 m`) | `[0.066000, 1.303386, 0.087328]` | 4.0 mm / 8.0 mm |

---

## 4. Group C: Bladder Meridian Outer Column (`BL41–BL50`)

### 4.1 Anatomical Truth in Vertebral Alignment
The Bladder outer column points are located **3.0 B-cun lateral to the posterior midline**. A frequent flaw in naive algorithms is assuming sequential correspondence with thoracic vertebrae T1 through T10. 

**Authoritative verification against WHO 2008 disproves sequential T1-T10 indexing:**
1. **BL41 (Fufen):** Aligns with **T2** (not T1; T1 has no outer bladder point).
2. **BL42 to BL46:** Align sequentially with **T3, T4, T5, T6, T7**.
3. **The T8 Omission:** In both classical Chinese medicine and the WHO 2008 standard, **there is NO classical outer Bladder point at T8**. (The point below T8 is the extra point *Weiguanxiashu* M-BW-35, 1.5 cun lateral; no outer point exists).
4. **BL47 (Hunmen):** Skips T8 and aligns directly with the inferior border of the spinous process of **T9**!
5. **BL48 to BL50:** Align sequentially with **T10, T11, T12**.

### 4.2 Comprehensive Outer Column Specification Table

| Point Code | Name (EN / ZH) | Vertebral Anchor Level | WHO 2008 Page | FMA ID | Segment Fraction (`LM_C7_SPINE` $\to$ `LM_L4_SPINE`) | Resolved Coordinates [X, Y, Z] (m) | Surface Normal [Nx, Ny, Nz] |
|---|---|---|---|---|---:|---|---|
| **BL41** | Fufen / 附分 | Inferior to **T2** spine | p. 139 | `FMA:54209` | 0.100 | `[0.0990, 1.4334, -0.0910]` | `[0.59077, 0.59674, -0.54303]` |
| **BL42** | Pohu / 魄户 | Inferior to **T3** spine | p. 139 | `FMA:54210` | 0.150 | `[0.0990, 1.4111, -0.0905]` | `[0.59173, 0.59771, -0.54093]` |
| **BL43** | Gaohuang / 膏肓 | Inferior to **T4** spine | p. 140 | `FMA:54211` | 0.200 | `[0.0990, 1.3888, -0.0900]` | `[0.59269, 0.59867, -0.53881]` |
| **BL44** | Shentang / 神堂 | Inferior to **T5** spine | p. 141 | `FMA:54212` | 0.250 | `[0.0990, 1.3665, -0.0895]` | `[0.59364, 0.59964, -0.53668]` |
| **BL45** | Yixi / 譩譆 | Inferior to **T6** spine | p. 141 | `FMA:54213` | 0.300 | `[0.0990, 1.3442, -0.0890]` | `[0.59460, 0.60060, -0.53454]` |
| **BL46** | Geguan / 膈关 | Inferior to **T7** spine | p. 142 | `FMA:54214` | 0.350 | `[0.0990, 1.3219, -0.0885]` | `[0.59555, 0.60157, -0.53239]` |
| **BL47** | Hunmen / 魂门 | Inferior to **T9** spine (*T8 skipped*) | p. 142 | `FMA:54215` | **0.450** | `[0.0990, 1.2773, -0.0875]` | `[0.59746, 0.60349, -0.52806]` |
| **BL48** | Yanggang / 阳纲 | Inferior to **T10** spine | p. 143 | `FMA:54216` | 0.500 | `[0.0990, 1.2550, -0.0870]` | `[0.59841, 0.60445, -0.52587]` |
| **BL49** | Yishe / 意舍 | Inferior to **T11** spine | p. 143 | `FMA:54217` | 0.550 | `[0.0990, 1.2327, -0.0865]` | `[0.59936, 0.60541, -0.52368]` |
| **BL50** | Weicang / 胃仓 | Inferior to **T12** spine | p. 144 | `FMA:54218` | 0.600 | `[0.0990, 1.2104, -0.0860]` | `[0.60031, 0.60637, -0.52148]` |

---

## 5. Justification for Deferred Candidates (5 Points)

| Point Code | Channel | Classical Name | Status | Anatomical & Clinical Hazard Rationale |
|---|---|---|---|---|
| **SP12** | SP | Chongmen (冲门) | `CLASS_D` | Inguinal crease femoral triangle transition. High local mesh curvature on FJ2810. Proximity to femoral artery and femoral nerve creates critical risk; deferred pending high-resolution pelvic soft-tissue model. |
| **SP13** | SP | Fushe (府舍) | `CLASS_D` | 0.7 B-cun superior to SP12. Bound directly to SP12 inguinal baseline; deferred together with SP12 to preserve regional continuity. |
| **KI25** | KI | Shencang (神藏) | `CLASS_D` | 2nd intercostal space 2.0 cun lateral. Sternocostal angle congestion on FJ2810 creates ambiguity between 2nd costal cartilage and 2nd intercostal space; deferred pending CT-derived thoracic cage boundary re-anchoring. |
| **KI26** | KI | Yuzhong (彧中) | `CLASS_D` | 1st intercostal space 2.0 cun lateral. Subclavicular transition requires high-density clavicle boundary facet model. |
| **KI16** | KI | Huangshu (肓俞) | `CLASS_B` | Already calibrated to Class B in P9.5 milestone with canonical landmark `LM_UMBILICUS` (0.5 cun lateral); reconciled as pre-existing Class B, not part of P9.6 elevation delta. |

---

## 6. Verification Signoff

The 30 localization rules defined above have been tested via automated property-based unit tests (`tests/test_p9_6_anatomical_remediation.py`), achieving 100% test pass rate with zero unresolved symbols or broken coordinate references.
