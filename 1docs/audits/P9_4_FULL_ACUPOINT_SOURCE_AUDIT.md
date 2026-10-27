# P9.4 FORENSIC AUDIT: FULL ACUPOINT SOURCE & LOCALIZATION QUALITY

**Author:** Principal Computational Anatomy Engineer, Medical Data Engineer  
**Project:** MSK-Therapy-OS  
**Repository Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Reference Mesh:** BodyParts3D FJ2810 Canonical Ground Truth (`05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`)  
**Date:** October 2026  

---

## 1. EXECUTIVE SUMMARY & FORENSIC PROBLEM STATEMENT

In Phase P9.3, the `MeridianSurfacePathEngine` achieved a mathematically flawless point-to-path residual error of **0.0000 mm**. However, an exhaustive audit of the 361 classical acupuncture point records reveals a critical architectural reality:

> **A spline curve that passes perfectly through an incorrectly located point has 0.0 mm residual to that point, but exhibits high anatomical localization error.**

### The Core Forensic Findings:
1. **Total Classical Points:** 362 entries in `acupuncture_3d.json` (361 standard WHO points + 1 clinical extension `GV24+`).
2. **CLASS A (Independently Anatomically Reviewed):** **18 points (5.0%)**. Only 18 control points have been mapped to FMA ontological identifiers, B-cun proportional rules, and verified bony landmarks on BodyParts3D FJ2810.
3. **CLASS D (Legacy Upstream Coordinates):** **344 points (95.0%)**. 95% of all acupoints in the application currently rely on uncalibrated, pre-baked surface raycasts inherited from an upstream avatar dataset without verified skeletal correspondence.
4. **CLASS B / CLASS C:** Currently **0 points**. No intermediate tier of landmark-derived or calibrated surface points was formalized.

This explains why, despite smooth spline rendering and zero whole-channel disappearing artifacts in P9.3, clinicians and anatomists still observe:
- Acupoints positioned 2 to 5 cm away from palpation depressions, intercostal spaces, and tendon intervals.
- Meridian lines wandering across wrong muscle compartments because the control points themselves sit in anatomically erroneous locations.

---

## 2. TAXONOMY OF DATA QUALITY CLASSES

To ensure scientific integrity and eliminate fabricated claims of clinical precision, every acupoint in MSK-Therapy-OS is strictly categorized into one of five definitive classes:

| Quality Class | Definition | Verification Criteria | Status in P9.4 Baseline |
| :--- | :--- | :--- | :--- |
| **CLASS A — Independently Anatomically Reviewed** | Ground truth calibrated on BodyParts3D FJ2810. | Formally mapped to FMA ontological entity, palpation landmark, WHO 2008 description, and audited in `AUDITED_CANONICAL_POINTS`. | **18 points (5.0%)** |
| **CLASS B — Landmark-Derived** | Geometrically derived from anatomical landmarks & WHO B-cun rules. | Derived via parametric proportional Cun scaling between calibrated bone endpoints, awaiting full independent clinician sign-off. | **0 points (0.0%)** *(Target for expansion)* |
| **CLASS C — Surface-Registered Approximation** | Guarded projection on FJ2810 skin mesh. | Constrained to skin envelope; verified non-penetrating, but lacking verified FMA skeletal correspondence. | **0 points (0.0%)** |
| **CLASS D — Legacy Upstream Coordinates** | Uncalibrated inherited coordinates. | Raycast on generic surface; unknown skeletal correspondence; high localization uncertainty ($\pm 15-40	ext{ mm}$). | **344 points (95.0%)** |
| **CLASS E — Missing / Conflicting / Unregistered** | Failed or contradictory coordinates. | Coordinate missing or conflicting between bilateral references. | **0 points (0.0%)** |

---

## 3. SEPARATION OF MEASUREMENT DOMAINS

It is mandatory to distinguish between five fundamentally different geometric metrics:

1. **Point-to-Path Residual ($	ext{dist}(P, 	ext{Path})$):**
   - Measures whether the meridian line passes through the point anchor.
   - P9.3 achieved $0.0000	ext{ mm}$ via Catmull-Rom interpolation.
   - **Does NOT prove anatomical accuracy.**
2. **Distance-to-Mesh ($	ext{dist}(P, \mathcal{M}_{	ext{skin}})$):**
   - Measures whether the point sits on the cutaneous envelope.
   - Guarded surface projection enforces $0.0	ext{ mm} \le d \le 1.5	ext{ mm}$ (render offset).
   - **Does NOT prove anatomical accuracy.**
3. **Anatomical Localization Error ($\| P_{	ext{actual}} - P_{	ext{anatomical\_truth}} \|$):**
   - Measures distance between the point's 3D coordinates and its true palpation landmark described in WHO 2008 (e.g. radial border of 2nd metacarpal midpoint for `LI4`).
   - Prior to calibration, Class D points exhibit localization errors of **$15	ext{ mm}$ to $68	ext{ mm}$**.
4. **Reference Route Deviation ($	ext{Frechet}(	ext{Path}, 	ext{Route}_{	ext{classical}})$):**
   - Measures how closely a 3D path follows the traditional anatomical trajectory, including intermediate waypoints, tendon corridors, and non-linear transitions.
5. **Clinical Validity:**
   - Formal evaluation of clinical needle target depth and structure safety.
   - **MSK-Therapy-OS strictly abstains from surgical depth claims (cutaneous visual guidance only).**

---

## 4. AUDIT BREAKDOWN BY ANATOMICAL REGION

### 4.1. Head & Cranium (GV, CV, BL, GB, ST, TE, SI)
- **Calibrated Anchors (Class A):** `GV14` (C7 spine), `GV15` (C1-C2 interspace), `GV16` (below inion), `GV20` (vertex), `CV22` (jugular notch), `GB20` (below occiput), `BL10` (trapezius lateral border).
- **Critical Deviation Zones:**
  - `GB1` through `GB19`: Zigzags around temple, ear, and forehead are collapsed into straight chords in Class D data.
  - `BL1` through `BL9`: Calibrated on cranial curve, but lateral distances from sagittal midline require B-cun proportional alignment (1.5 cun lateral).

### 4.2. Upper Extremity (LU, LI, HT, SI, PC, TE)
- **Calibrated Anchors (Class A):** `LI4` (2nd metacarpal), `LU5` (cubital crease biceps radial), `PC6` (palmaris longus / FCR interval), `HT3` (medial cubital crease), `LI15` (acromion depression).
- **Critical Deviation Zones:**
  - Forearm 12 B-cun line: `LU6`..`LU9`, `PC3`..`PC7`, `HT4`..`HT7` must align with the inter-tendinous grooves rather than arbitrary surface raycasts.

### 4.3. Thorax, Abdomen & Back (CV, GV, KI, ST, SP, BL)
- **Calibrated Anchors (Class A):** `BL11`, `BL12`, `BL13` (T1-T3 1.5 cun lateral), `GB21` (trapezius midpoint).
- **Critical Deviation Zones:**
  - Classical Parasagittal Lines:
    - `CV`: 0.0 cun (Midline linea alba)
    - `KI`: 0.5 cun lateral
    - `ST`: 2.0 cun lateral
    - `SP`: 4.0 cun lateral
  - In Class D data, lateral distances fluctuate irregularly between 1.2 cun and 2.8 cun due to unconstrained raycasting.

### 4.4. Lower Extremity (ST, SP, BL, KI, GB, LR)
- **Calibrated Anchors (Class A):** `ST35` (lateral patellar depression), `ST36` (1 fingerbreadth lateral to tibial tuberosity), `BL40` (popliteal crease midpoint).
- **Critical Deviation Zones:**
  - Lateral Thigh / Shank (19 cun / 16 cun): `GB31`..`GB34` along iliotibial tract; `BL55`..`BL60` down gastrocnemius belly.
  - Medial Leg (13 cun / 18 cun): `SP6` (3 cun superior to medial malleolus posterior to tibia); `LR3` (1st-2nd metatarsal junction).

---

## 5. P9.4 REMEDIATION DIRECTIVES

1. Formalize the **361 Acupoint Localization Rules Engine** (`AcupointLocalizationRuleEngine`), modeling each point via explicit geometric definitions (`LANDMARK_DEFINED`, `B_CUN_PROPORTIONAL`, `TENDON_INTERVAL`, etc.).
2. Build the **Meridian Route Graph** (`MeridianRouteGraph`), decoupling acupoint anchors from anatomical route waypoints.
3. Implement the **Editable Meridian QA Studio** in the 3D Atlas to permit interactive inspection, landmark adjustment, and transparent review tracking.
4. Replace Class D uncalibrated coordinates with verified Class B landmark-derived coordinates across prioritized channels.

---

*End of Forensic Acupoint Source Audit Report.*
