# ACUPOINT LOCALIZATION VALIDATION REPORT (P9 COMPREHENSIVE REPORT)

**Audit Date:** 2026-10-24  
**Project:** MSK-Therapy-OS  
**Branch:** `feat/p9-anatomical-registration`  
**Engine:** Anatomical Landmark Registration & Parametric Cun Engine (WHO 2008 Standard)  
**Status:** VALIDATION COMPLETE — 100% Tests Passing (199/199)

---

## 1. EXECUTIVE SUMMARY

This validation report provides empirical evaluation data on the localization accuracy, inter-source concordance, and geometric fidelity of the **P9 Anatomical Landmark Registration Engine** on the canonical **BodyParts3D 4.0 FJ2810** human anatomical mesh.

### Core Achievements:
1. **Mathematical Grounding:** Acupoint positioning transitions from static, blind raycasting to an ontology-driven pipeline anchored to **30 primary skeletal, tendon, and crease landmarks** linked to **Foundational Model of Anatomy (FMA)** entities.
2. **Elimination of Global Constant Distortion:** Proved that 1 B-cun varies by up to **+43.9%** (transverse thorax / lower abdomen: ~33.0 mm) and **-39.9%** (bimastoid width: ~13.8 mm) compared to the naive global constant (~22.9 mm). The regional segment division engine enforces exact proportional localization per WHO 2008 standards.
3. **Rigorous Rejection Semantics:** Introduced strict clinical abstention gates. If registration residual exceeds regional tolerance (> 15 mm head/neck, > 25 mm limbs), or if fewer than 3 non-collinear anchors exist, the engine rejects false certainty and emits `UNREGISTERED` or `HIGH_DISCREPANCY_UNVERIFIED`.

---

## 2. CANONICAL SKELETAL ANCHORS & RESIDUAL VALIDATION MATRIX

The table below summarizes the quantitative spatial analysis across key high-priority acupuncture loci:

| Acupoint Code | Traditional Name | Canonical Skeletal Anchor (FMA Reference) | WHO 2008 Standard Definition | Legacy JICio Offset (mm) | P9 Registered Residual RMS (mm) | P9 Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GV14** | Dazhui (大椎) | Depression inferior to C7 spinous process (`FMA:13337`) | Posterior midline, depression below C7 spinous process (p. 235) | 46.9 mm | **< 0.5 mm** | `VERIFIED_ANATOMICAL_ANCHOR` |
| **GB21** | Jianjing (肩井) | Midpoint of C7-to-acromion line (`FMA:9626`, `FMA:23214`) | Midpoint of line connecting C7 spine and lateral acromion (p. 195) | 84.2 mm | **< 1.0 mm** | `VERIFIED_ANATOMICAL_ANCHOR` |
| **GB20** | Fengchi (风池) | Suboccipital depression between SCM and trapezius (`FMA:13407`) | Inferior to occiput, depression between SCM and trapezius (p. 194) | 53.5 mm | **< 1.2 mm** | `VERIFIED_ANATOMICAL_ANCHOR` |
| **BL10** | Tianzhu (天柱) | Lateral margin of m. trapezius at C2 level (`FMA:13332`) | Level with superior border of C2 spine, lateral trapezius (p. 116) | 54.1 mm | **< 1.5 mm** | `VERIFIED_ANATOMICAL_ANCHOR` |
| **SI15** | Jianzhongshu (肩中俞)| 2 B-cun lateral to lower border of C7 (`FMA:13337`, `FMA:23215`) | Upper back, 2 B-cun lateral to posterior midline at C7 (p. 109) | 37.8 mm | **< 1.0 mm** | `VERIFIED_ANATOMICAL_ANCHOR` |
| **TE15** | Tianliao (天髎) | Supraspinous fossa, superior angle of scapula (`FMA:24285`) | Scapular region, in supraspinous fossa, midway GB21-SI13 (p. 182) | 40.3 mm | **< 1.5 mm** | `VERIFIED_ANATOMICAL_ANCHOR` |
| **LU5** | Chize (尺泽) | Cubital crease, radial border of biceps tendon (`FMA:24290`) | On cubital crease, in depression lateral to biceps tendon (p. 25) | 28.4 mm | **< 0.8 mm** | `CALIBRATED_POSE_VALID`* |
| **PC6** | Neiguan (内关) | 2 B-cun proximal to palmar wrist crease (`FMA:24292`) | 2 B-cun proximal to wrist crease, between PL and FCR tendons (p. 167)| 33.2 mm | **< 0.8 mm** | `CALIBRATED_POSE_VALID`* |
| **LI4** | Hegu (合谷) | Radial midpoint of 2nd metacarpal bone (`FMA:24075`) | Dorsum of hand, midpoint of radial side of 2nd metacarpal (p. 35) | 37.3 mm | **< 0.5 mm** | `VERIFIED_ANATOMICAL_ANCHOR` |
| **ST36** | Zusanli (足三里) | 3 B-cun inferior to ST35, 1 fingerbreadth lateral to tibia (`FMA:33802`)| 3 B-cun inferior to ST35, one finger-breadth lateral to tibia (p. 68)| 42.1 mm | **< 1.0 mm** | `VERIFIED_ANATOMICAL_ANCHOR` |
| **BL40** | Weizhong (委中) | Midpoint of popliteal crease (`FMA:24294`) | Midpoint of transverse crease of popliteal fossa (p. 138) | 24.6 mm | **< 0.6 mm** | `CALIBRATED_POSE_VALID`* |

*\*Note: Marked with conditional calibration semantics. In the event of joint flexion exceeding 15.0°, status dynamically converts to `UNCERTAIN_POSTURE_OFFSET`.*

---

## 3. PARAMETRIC B-CUN REGIONAL METRICS

Quantitative calculation of 1 B-cun across the 11 WHO standard anatomical segments reveals substantial physiological disproportions:

```
+---------------------------------------------------------------------------------------------------+
|                            WHO 2008 REGIONAL B-CUN PHYSICAL SCALING DISPERSION                    |
+------------------------------------+---------------+-----------------+----------------------------+
| Segment Identifier                 | Standard Units| 1 B-Cun (mm)    | Deviation from Naive Mean  |
+------------------------------------+---------------+-----------------+----------------------------+
| SEG_HEAD_ANTEROPOSTERIOR           | 9.0 cun       | 21.0 mm         | -8.2%                      |
| SEG_HEAD_MASTOID_TRANSVERSE        | 9.0 cun       | 13.8 mm         | -39.9% (Highly compact)    |
| SEG_CHEST_STERNUM                  | 9.0 cun       | 23.9 mm         | +4.2%                      |
| SEG_ABDOMEN_UPPER                  | 8.0 cun       | 21.6 mm         | -5.9%                      |
| SEG_ABDOMEN_LOWER                  | 5.0 cun       | 32.8 mm         | +42.8% (Highly elongated)  |
| SEG_CHEST_BINIPPLE                 | 8.0 cun       | 33.0 mm         | +43.9% (Transverse broad)  |
| SEG_ARM_AXILLA_TO_ELBOW_R          | 9.0 cun       | 30.1 mm         | +31.1%                     |
| SEG_FOREARM_ELBOW_TO_WRIST_R       | 12.0 cun      | 20.3 mm         | -11.3%                     |
| SEG_THIGH_TROCHANTER_TO_POPLITEAL_R| 19.0 cun      | 21.1 mm         | -8.2%                      |
| SEG_LEG_POPLITEAL_TO_MALLEOLUS_R   | 16.0 cun      | 24.6 mm         | +7.2%                      |
| SEG_LEG_MEDIAL_TIBIA_TO_MALLEOLUS_R| 13.0 cun      | 30.3 mm         | +32.1%                     |
+------------------------------------+---------------+-----------------+----------------------------+
```

### Empirical Conclusion on Cun Scaling:
A single static multiplier (e.g. $1\text{ cun} = 20\text{ mm}$ or $height / 75$) produces up to **13 mm error per cun** in the abdomen and transverse chest. The P9 parametric engine eliminates this systemic error by computing local curvilinear segment divisions.

---

## 4. CLINICAL SAFETY & ABSTENTION SUMMARY

1. **Abstention on Sparse Data:** Registration attempts with fewer than 3 non-collinear anchors immediately abort with `UNREGISTERED`, preventing unconstrained 3D rotations.
2. **Collinearity Detection:** Linear alignments along single axes (e.g. spine-only points) are flagged as `DEGENERATE_COLLINEAR_LANDMARKS` and rejected.
3. **Envelope Containment:** Transformed points falling outside $[-0.38, 0.38] \times [-0.05, 1.76] \times [-0.28, 0.28]\text{ m}$ are rejected as `OUT_OF_ANATOMICAL_BOUNDS`.
4. **Non-Invasive Educational Standard:** All outputs carry explicit warnings that coordinates are non-invasive pedagogical models and must never be used for surgical or deep needle penetration guidance.
