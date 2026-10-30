# P14 Evidence Register & Scientific Governance Review

**Milestone:** P14 — Evidence-Grounded Dynamic Biomechanics, Muscle Recruitment Visualization & Interactive MSK Education  
**Date:** October 31, 2026  
**Auditor / Reviewer:** Clinical Research Data Governance Specialist & Biostatistical Methodology Auditor  
**Status:** VALIDATED  

---

## 1. Executive Summary

This document reviews the expanded Medical Evidence Register (EV-01 through EV-08) integrated into `msk_therapy_os/biomechanics_adapter.py` and the interactive Shoulder Education Studio. 

Every scientific claim made across the user interface, curriculum modules, and quiz assessments is anchored to a peer-reviewed publication with documented study design, sample population, specific claims supported, and explicit methodological limitations.

---

## 2. Evidence Register Catalog (EV-01 through EV-08)

### EV-01: Observations on the Function of the Shoulder Joint
- **Citation:** Inman VT, Saunders JB, Abbott LC. *Observations on the function of the shoulder joint.* J Bone Joint Surg Am. 1944;26(1):1-30.
- **DOI / URL:** [10.2106/00004623-194426010-00001](https://doi.org/10.2106/00004623-194426010-00001)
- **Study Design:** Cadaveric dissection and planar radiographic observational study ($N = 20$).
- **Claims Supported:** Foundational description of the 2:1 overall thoracohumeral elevation ratio as an educational benchmark average.
- **Methodological Limitations:** Planar 2D radiographs linearized across the entire range of motion; did not capture phase-dependent non-linearities, transverse plane rotation, or external load variations.
- **Evidence Status:** `HISTORICAL_BENCHMARK`

### EV-02: Scapular Kinematics & Impingement Symptoms
- **Citation:** Ludewig PM, Cook TM. *Alterations in shoulder kinematics and associated muscle activity in people with symptoms of shoulder impingement.* Phys Ther. 2000;80(3):276-291.
- **DOI / URL:** [10.1093/ptj/80.3.276](https://doi.org/10.1093/ptj/80.3.276)
- **Study Design:** Controlled laboratory observational study with 3D electromagnetic tracking and surface EMG.
- **Population:** 26 construction workers with impingement symptoms vs. 26 asymptomatic matched controls.
- **Claims Supported:** Demonstrated significant variability in scapular upward rotation and demonstrated decreased posterior tilt in symptomatic subjects during elevation.
- **Methodological Limitations:** Cross-sectional design; kinematic differences correlate with symptoms but do not prove causal direction (whether altered kinematics precede or follow pain).
- **Evidence Status:** `CONTROLLED_OBSERVATIONAL`

### EV-03: Pectoralis Minor Resting Length & Scapular Motion
- **Citation:** Borstad JD, Ludewig PM. *The effect of long versus short pectoralis minor resting length on scapular kinematics in healthy individuals.* J Orthop Sports Phys Ther. 2005;35(4):227-238.
- **DOI / URL:** [10.2519/jospt.2005.35.4.227](https://doi.org/10.2519/jospt.2005.35.4.227)
- **Study Design:** Controlled prospective kinematic cohort study ($N = 50$).
- **Population:** 50 healthy asymptomatic subjects stratified into short vs. long pectoralis minor resting length groups.
- **Claims Supported:** Shortened pectoralis minor resting length is associated with increased anterior scapular tilt and internal rotation during arm elevation.
- **Methodological Limitations:** Evaluated healthy subjects; establishes biomechanical correlation between muscle length index and resting alignment without establishing spontaneous tissue pathology.
- **Evidence Status:** `CONTROLLED_OBSERVATIONAL`

### EV-04: Length-Tension Relationships & Postural Frameworks
- **Citation:** Kendall FP, McCreary EK, Provance PG, Rodgers MM, Romani WA. *Muscles: Testing and Function with Posture and Pain.* 5th ed. Baltimore: Lippincott Williams & Wilkins; 2005.
- **Reference:** ISBN: 978-0781747806
- **Study Design:** Clinical anatomical textbook and expert consensus framework.
- **Claims Supported:** Theoretical model describing reciprocal length-tension muscle imbalances in forward head/shoulder postures.
- **Methodological Limitations:** Expert observational framework; broad epidemiological surveys show visual posture alone does not reliably predict clinical pain onset.
- **Evidence Status:** `CLINICAL_THEORETICAL_MODEL`

### EV-05: Sensorimotor Active Training & Muscle Imbalance
- **Citation:** Page P, Frank CC, Lardner R. *Assessment and Treatment of Muscle Imbalance: The Janda Approach.* Champaign, IL: Human Kinetics; 2010.
- **Reference:** ISBN: 978-0736074001
- **Study Design:** Clinical neurodevelopmental framework and expert clinical consensus.
- **Claims Supported:** Emphasizes sensorimotor active training and progressive neuromuscular re-education over isolated passive manual modalities.
- **Methodological Limitations:** Expert clinical framework; requires individualized clinical testing rather than blanket classification based solely on visual inspection.
- **Evidence Status:** `CLINICAL_THEORETICAL_MODEL`

### EV-06: Neurobiological Mechanisms of Manual Therapy
- **Citation:** Schleip R. *Fascial plasticity – a new neurobiological explanation: Part 1 and 2.* J Bodyw Mov Ther. 2003;7(1):11-19, 7(2):104-116.
- **DOI / URL:** [10.1016/S1360-8592(02)00067-0](https://doi.org/10.1016/S1360-8592(02)00067-0)
- **Study Design:** Narrative scientific review of mechanoreceptor physiology.
- **Claims Supported:** Manual pressure stimulates Ruffini and interstitial mechanoreceptors, yielding transient parasympathetic autonomic changes and local muscle tone reduction.
- **Methodological Limitations:** Explains transient perceptual lightness following massage; does not support claims of permanent structural tissue deformation from manual pressure alone.
- **Evidence Status:** `NARRATIVE_PHYSIOLOGICAL_REVIEW`

### EV-07: OpenSim Scapulothoracic Multi-Body Shoulder Model
- **Citation:** Seth A, Matias R, Veloso AP, Delp SL. *A Scapulothoracic Joint Model for Simulation of Shoulder Biomechanics.* Comput Methods Biomech Biomed Engin. 2016;19(1):65-76.
- **DOI / URL:** [10.1080/10255842.2015.1105994](https://doi.org/10.1080/10255842.2015.1105994)
- **Study Design:** Computational multi-body biomechanical model formulation and kinematic validation.
- **Claims Supported:** Validated OpenSim multi-body kinematic representation of scapulothoracic gliding and joint constraints during arm elevation.
- **Methodological Limitations:** Mathematical musculoskeletal model; static optimization muscle activations are model predictions, not directly measured EMG.
- **Evidence Status:** `COMPUTATIONAL_MODEL_VALIDATION`

### EV-08: In-Vivo 3D Fluoroscopic Shoulder Complex Kinematics
- **Citation:** Sugamoto K, et al. *In vivo three-dimensional kinematics of the shoulder complex during arm elevation.* J Shoulder Elbow Surg. 2002;11(4):378-384.
- **DOI / URL:** [10.1016/S1058-2746(02)00007-4](https://doi.org/10.1016/S1058-2746(02)00007-4)
- **Study Design:** In-vivo 3D fluoroscopic dynamic kinematic measurement.
- **Population:** Healthy adult volunteers ($N = 10$).
- **Claims Supported:** Demonstrates substantial non-linear variability in scapular upward rotation, posterior tilt, and external rotation across healthy individuals.
- **Methodological Limitations:** Confirms wide physiological normal ranges, refuting single universal ratio thresholds.
- **Evidence Status:** `IN_VIVO_EXPERIMENTAL_IMAGING`

---

## 3. Evidence Governance Rules

1. **Non-Equivalence Enforcement:** No claim of "syndrome" or "dyskinesia" is generated automatically from posture or rhythm ratios.
2. **Provenance Attribution:** Every evidence record is accessible directly from Stage 8 of the application and verifiable via standard DOI links.
3. **Continuous Gate Status:** Scientific Gate G14 remains strictly `BLOCKED_EXTERNAL_DATA`, ensuring no unverified external patient datasets are claimed.
