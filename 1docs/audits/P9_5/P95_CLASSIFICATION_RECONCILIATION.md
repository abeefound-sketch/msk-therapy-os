# P9.5 AUDIT: ACUPOINT DATA QUALITY CLASSIFICATION RECONCILIATION

**Document ID:** P95-AUDIT-005  
**Project:** MSK-Therapy-OS  
**Milestone:** P9.5 Anatomical Accuracy Remediation & Evidence-Based Acupoint Validation  
**Author:** Principal Computational Anatomy Engineer, Python Backend Architect, Independent QA Auditor  
**Date:** October 2026  
**Reference Mesh:** BodyParts3D 4.0 FJ2810 (`05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`)  
**Status:** RECONCILED & AUDITED  

---

## 1. THE CLASSIFICATION DISCREPANCY FORENSIC ANALYSIS

A central objective of Task 01 is resolving the discrepancy between the published audit documentation and the running system:

### The Documented Conflict:
- **`1docs/audits/P9_4_361_ACUPOINT_DATA_QUALITY_MATRIX.md`:**  
  Reports: **18 Class A, 0 Class B, 0 Class C, 344 Class D** (Total: 362).
- **`1docs/specs/P9_4_REFERENCE_DRIVEN_MERIDIAN_ATLAS.md` & `1docs/audits/P9_4_FINAL_ENGINEERING_HANDOFF.md`:**  
  Reports: **18 Class A, 52 Class B, 0 Class C, 292 Class D** (Total: 362).

### The Root Cause Discovery:
1. **Pre-Rule Static Export vs Dynamic Rule Resolution:**  
   `P9_4_361_ACUPOINT_DATA_QUALITY_MATRIX.md` was drafted at the inception of Milestone P9.4 as an initial inventory snapshot of `acupuncture_3d.json`. At that moment, only 18 audited points (`AUDITED_CANONICAL_POINTS`) were formalized.
2. **Implementation of the 68 Authoritative Rules:**  
   During Milestone P9.4 execution, the team implemented `msk_therapy_os/point_localization_rules.py` containing 68 WHO 2008 parametric localization rules.
3. **Mathematical Overlap:**  
   $$\text{Total Rules} = 68$$
   $$\text{Overlap with Audited Class A Points} = 16$$
   $$\text{Class B Points} = 68 - 16 = 52$$
   $$\text{Class D Points Remaining} = 362 - 18 - 52 = 292$$
4. **Documentation Lag:**  
   When the SQLite seeding function (`migrate_p9_4_meridian_atlas_tables` in `msk_therapy_os/points.py`) and runtime spatial resolver (`msk_therapy_os/spatial_resolver.py`) incorporated `AcupointLocalizationEngine`, the live system began reporting 18 Class A, 52 Class B, 292 Class D. However, `P9_4_361_ACUPOINT_DATA_QUALITY_MATRIX.md` was never regenerated.

---

## 2. LINE-BY-LINE RECONCILIATION OF THE 52 CLASS B POINTS

The 52 points below were listed as Class D in the legacy matrix but are mathematically and geometrically resolved as Class B via WHO 2008 rules in the runtime engine:

| Point Code | Channel | Classical Name (ZH / VI) | Localization Method | Primary Landmark Anchor | Proportional Rule / WHO Clause |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LU1** | LU | 中府 / Trung Phủ | `PARASAGITTAL_LINE` | `LM_STERNAL_ANGLE` | 6 B-cun lateral, 1st intercostal space |
| **LU2** | LU | 云门 / Vân Môn | `JOINT_DEPRESSION` | `LM_ACROMION_R` | Infraclavicular fossa medial to coracoid |
| **LU3** | LU | 天府 / Thiên Phủ | `B_CUN_PROPORTIONAL` | `LM_AXILLARY_FOLD_ANT_R` | Arm 9 B-cun, 3 cun inferior to axillary fold |
| **LU4** | LU | 侠白 / Hiệp Bạch | `B_CUN_PROPORTIONAL` | `LM_AXILLARY_FOLD_ANT_R` | Arm 9 B-cun, 4 cun inferior to axillary fold |
| **LU6** | LU | 孔最 / Khổng Tối | `B_CUN_PROPORTIONAL` | `LM_CUBITAL_CREASE_R` | Forearm 12 B-cun, 5 cun inferior to cubital crease |
| **LU7** | LU | 列缺 / Liệt Khuyết | `B_CUN_PROPORTIONAL` | `LM_RADIAL_STYLOID_R` | Superior to radial styloid process 1.5 cun |
| **LU8** | LU | 经渠 / Kinh Cừ | `B_CUN_PROPORTIONAL` | `LM_WRIST_CREASE_PALMAR_R` | Radial artery groove 1.0 cun proximal to wrist |
| **LU9** | LU | 太渊 / Thái Uyên | `JOINT_DEPRESSION` | `LM_WRIST_CREASE_PALMAR_R` | Radial end of wrist crease, radial artery lateral |
| **LU10** | LU | 鱼际 / Ngư Tế | `MUSCLE_BORDER` | `LM_WRIST_CREASE_PALMAR_R` | Midpoint of 1st metacarpal radial border |
| **LU11** | LU | 少商 / Thiếu Thương | `LANDMARK_DEFINED` | `LM_WRIST_CREASE_PALMAR_R` | Radial nail corner of thumb 0.1 cun |
| **LI1** | LI | 商阳 / Thương Dương | `LANDMARK_DEFINED` | `LM_WRIST_CREASE_PALMAR_R` | Radial nail corner of index finger 0.1 cun |
| **LI5** | LI | 阳溪 / Dương Khê | `JOINT_DEPRESSION` | `LM_RADIAL_STYLOID_R` | Anatomical snuffbox between EPL and EPB |
| **LI11** | LI | 曲池 / Khúc Trì | `SKIN_CREASE` | `LM_LAT_EPICONDYLE_HUMERUS_R` | Lateral end of cubital crease |
| **LI20** | LI | 迎香 / Nghênh Hương | `JOINT_DEPRESSION` | `LM_GLABELLA` | Nasolabial groove level with midpoint of ala nasi |
| **SP1** | SP | 隐白 / Ẩn Bạch | `LANDMARK_DEFINED` | `LM_MED_MALLEOLUS_R` | Medial nail corner of great toe 0.1 cun |
| **SP6** | SP | 三阴交 / Tam Âm Giao | `B_CUN_PROPORTIONAL` | `LM_MED_MALLEOLUS_R` | 3 B-cun superior to medial malleolus, tibia posterior border |
| **SP9** | SP | 阴陵泉 / Âm Lăng Tuyền | `JOINT_DEPRESSION` | `LM_MED_MALLEOLUS_R` | Depression inferior to medial condyle of tibia |
| **SP10** | SP | 血海 / Huyết Hải | `B_CUN_PROPORTIONAL` | `LM_PATELLA_INFERIOR_R` | 2 B-cun superior to patellar base, vastus medialis |
| **SP15** | SP | 大横 / Đại Hoành | `PARASAGITTAL_LINE` | `LM_UMBILICUS` | 4 B-cun lateral to center of umbilicus |
| **SP21** | SP | 大包 / Đại Bao | `PARASAGITTAL_LINE` | `LM_AXILLARY_FOLD_ANT_R` | Midaxillary line, 6th intercostal space |
| **SI1** | SI | 少泽 / Thiếu Trạch | `LANDMARK_DEFINED` | `LM_WRIST_CREASE_PALMAR_R` | Ulnar nail corner of little finger 0.1 cun |
| **SI3** | SI | 后溪 / Hậu Khê | `JOINT_DEPRESSION` | `LM_WRIST_CREASE_PALMAR_R` | Ulnar border 5th metacarpophalangeal depression |
| **SI8** | SI | 小海 / Tiểu Hải | `JOINT_DEPRESSION` | `LM_MED_EPICONDYLE_HUMERUS_R` | Depression between olecranon and medial epicondyle |
| **SI11** | SI | 天宗 / Thiên Tông | `B_CUN_PROPORTIONAL` | `LM_ACROMION_R` | Infraspinous fossa midpoint (1/3 scapular spine) |
| **SI19** | SI | 听宫 / Thính Cung | `JOINT_DEPRESSION` | `LM_MASTOID_R` | Depression anterior to tragus midpoint |
| **KI1** | KI | 涌泉 / Dũng Tuyền | `B_CUN_PROPORTIONAL` | `LM_CALCANEUS_POST_R` | Sole depression anterior 1/3 between 2nd/3rd metatarsal |
| **KI3** | KI | 太溪 / Thái Khê | `JOINT_DEPRESSION` | `LM_MED_MALLEOLUS_R` | Depression between medial malleolus and Achilles tendon |
| **KI6** | KI | 照海 / Chiếu Hải | `JOINT_DEPRESSION` | `LM_MED_MALLEOLUS_R` | 1 B-cun inferior to prominence of medial malleolus |
| **KI7** | KI | 复溜 / Phục Lưu | `B_CUN_PROPORTIONAL` | `LM_MED_MALLEOLUS_R` | 2 B-cun superior to medial malleolus, anterior to Achilles |
| **KI10** | KI | 阴谷 / Âm Cốc | `TENDON_INTERVAL` | `LM_POPLITEAL_CREASE_R` | Medial popliteal crease between semitendinosus/membranosus |
| **KI11** | KI | 横骨 / Hoành Cốt | `PARASAGITTAL_LINE` | `LM_PUBIC_SYMPHYSIS` | Superior border of pubic symphysis, 0.5 cun lateral |
| **KI16** | KI | 盲俞 / Hoang Du | `PARASAGITTAL_LINE` | `LM_UMBILICUS` | Level with umbilicus, 0.5 B-cun lateral to anterior midline |
| **KI27** | KI | 俞府 / Du Phủ | `PARASAGITTAL_LINE` | `LM_JUGULAR_NOTCH` | Inferior to clavicle, 2.0 B-cun lateral to anterior midline |
| **PC3** | PC | 曲泽 / Khúc Trạch | `SKIN_CREASE` | `LM_CUBITAL_CREASE_R` | Cubital crease medial to biceps brachii tendon |
| **PC7** | PC | 大陵 / Đại Lăng | `SKIN_CREASE` | `LM_WRIST_CREASE_PALMAR_R` | Distal wrist crease between palmaris longus and FCR |
| **TE1** | TE | 关冲 / Quan Xung | `LANDMARK_DEFINED` | `LM_WRIST_CREASE_PALMAR_R` | Ulnar nail corner of ring finger 0.1 cun |
| **TE5** | TE | 外关 / Ngoại Quan | `TENDON_INTERVAL` | `LM_WRIST_CREASE_PALMAR_R` | 2 B-cun proximal to dorsal wrist crease between radius/ulna |
| **TE14** | TE | 肩髎 / Kiên Liêu | `JOINT_DEPRESSION` | `LM_ACROMION_R` | Depression posterior to lateral acromion |
| **TE17** | TE | 翳风 / Ế Phong | `JOINT_DEPRESSION` | `LM_MASTOID_R` | Depression between mastoid process and mandible angle |
| **TE23** | TE | 丝竹空 / Ti Châu Không | `JOINT_DEPRESSION` | `LM_GLABELLA` | Depression at lateral end of eyebrow |
| **LR1** | LR | 大敦 / Đại Đôn | `LANDMARK_DEFINED` | `LM_MED_MALLEOLUS_R` | Lateral nail corner of great toe 0.1 cun |
| **LR3** | LR | 太冲 / Thái Xung | `JOINT_DEPRESSION` | `LM_MED_MALLEOLUS_R` | Dorsum of foot between 1st and 2nd metatarsal bases |
| **LR8** | LR | 曲泉 / Khúc Tuyền | `SKIN_CREASE` | `LM_POPLITEAL_CREASE_R` | Medial knee superior to medial end of popliteal crease |
| **LR13** | LR | 章门 / Chương Môn | `LANDMARK_DEFINED` | `LM_ASIS_R` | Directly inferior to free end of 11th rib |
| **LR14** | LR | 期门 / Kỳ Môn | `PARASAGITTAL_LINE` | `LM_STERNAL_ANGLE` | 6th intercostal space, mammillary line 4 cun lateral |
| **GV4** | GV | 命门 / Mệnh Môn | `LANDMARK_DEFINED` | `LM_L4_SPINE` | Posterior midline, inferior to L2 spinous process |
| **GV20** | GV | 百会 / Bách Hội | `LANDMARK_DEFINED` | `LM_VERTEX_CROWN` | Vertex cranium at sagittal suture intersection |
| **CV2** | CV | 曲骨 / Khúc Cốt | `LANDMARK_DEFINED` | `LM_PUBIC_SYMPHYSIS` | Anterior midline, superior border of pubic symphysis |
| **CV4** | CV | 关元 / Quan Nguyên | `B_CUN_PROPORTIONAL` | `LM_UMBILICUS` | Anterior midline, 3 B-cun inferior to umbilicus |
| **CV8** | CV | 神阙 / Thần Khuyết | `LANDMARK_DEFINED` | `LM_UMBILICUS` | Center of umbilicus |
| **CV12** | CV | 中脘 / Trung Quản | `B_CUN_PROPORTIONAL` | `LM_UMBILICUS` | Anterior midline, 4 B-cun superior to umbilicus |
| **CV17** | CV | 膻中 / Đản Trung | `LANDMARK_DEFINED` | `LM_JUGULAR_NOTCH` | Anterior midline on sternum, 4th intercostal space |

---

## 3. PROVENANCE DEMARCATION: RULE-DERIVED vs INDEPENDENTLY-VERIFIED

Milestone P9.5 establishes strict clinical and forensic boundaries between:
1. **CLASS A — Independently Verified ($n=18$):**  
   Coordinates have been individually compared against BodyParts3D FJ2810 osteological landmarks and corroborated by multi-expert anatomical review. Residual errors and clinical uncertainties are bounded to $\le 5.0\text{ mm}$ tolerance.
2. **CLASS B — Rule-Derived ($n=52$, expanding to $n=72$ in Phase B):**  
   Coordinates are parametrically computed via WHO 2008 standard proportional division. They are scientifically grounded, reproducible, and verifiable, but **must not be misrepresented as independently hand-verified expert anchors**.
3. **CLASS D — Legacy Raycast ($n=292$, reducing to $n=272$ in Phase B):**  
   Uncalibrated historical data. Uncertainty is high ($\pm 15-40\text{ mm}$). Strictly tagged with educational disclaimers.

---

## 4. THE SPECIAL CASE OF RECORD `GV24+` (YINTANG / EX-HN3)

- **Classical WHO Standard (2008):**  
  Classifies Yintang as an Extra Point of the Head and Neck (`EX-HN3`). The standard Governing Vessel contains exactly 28 points (`GV1` through `GV28`).
- **National Standard of China (GB/T 12346-2006 / 2021):**  
  Formally integrated Yintang into the Governing Vessel as a meridian point between Shenting (`GV24`) and Suliao (`GV25`).
- **MSK-Therapy-OS Representation:**  
  The dataset designates this point as `GV24+` with name *Yintang / 印堂*, preserving compatibility with 14-channel viewers while maintaining fidelity to WHO 361-point classical inventories.
- **Classification Status:**  
  `GV24+` is grounded directly on the Glabella (`LM_GLABELLA`, $X=0.000, Y=1.625, Z=0.089$).

---

## 5. SUMMARY OF RECONCILIATION

The classification count reconciliation is conclusively established as follows:

| Stage | Class A | Class B | Class C | Class D | Total Points | Verified % (A only) | Derived % (A+B) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pre-P9.4 Baseline Snapshot** | 18 | 0 | 0 | 344 | 362 | 5.0% | 5.0% |
| **P9.4 Post-Rules Runtime** | 18 | 52 | 0 | 292 | 362 | 5.0% | 19.3% |
| **P9.5 Remediation Target** | 18 | 72 | 0 | 272 | 362 | 5.0% | 24.9% |

Reconciliation certified by Computational Anatomy Quality Assurance Lead.
