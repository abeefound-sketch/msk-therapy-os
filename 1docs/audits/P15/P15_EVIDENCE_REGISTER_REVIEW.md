# P15 Evidence Register Review: EV-09 Through EV-16

**Milestone:** P15 — Cervicothoracic Biomechanics, Forward Head Posture & Upper Crossed Syndrome Studio  
**System:** MSK-Therapy-OS  
**Scope:** Engineering & Biomechanical Education / Research  
**Release Gate:** `ENGINEERING_RESEARCH_ONLY`  
**Clinical Status:** `CLINICAL_VALIDATION: NOT_ESTABLISHED`  

---

## 1. Overview & Verification Policy
Milestone P15 extends the biomechanical evidence register established in P13 (EV-01 to EV-04) and P14 (EV-05 to EV-08) by adding eight verified, peer-reviewed citations governing cervicothoracic kinematics, moment arms, suboccipital neuroanatomy, and reciprocal inhibition.

Every citation in MSK-Therapy-OS must satisfy:
1. Verifiable publication in peer-reviewed orthopedic, biomechanical, or physical therapy literature.
2. Direct attribution to quantitative or qualitative models exposed in the application.
3. Explicit educational demarcation preventing unverified translation into automated diagnostic claims.

---

## 2. Register of Evidence Items EV-09 to EV-16

| ID | Topic / Mechanism | Citation | Key Finding / Parameter Utilized | Application Binding |
|---|---|---|---|---|
| **EV-09** | Forward Head Biomechanics & Load | Hansraj KK. *Assessment of Stresses in the Cervical Spine Caused by Posture and Position of the Head.* Surg Technol Int. 2014;25:277-279. | Gravitational moment increases effective cervical load from ~10-12 lbs (0°) to 40 lbs (30°), 49 lbs (45°), and 60 lbs (60°). | Governs dynamic head load indicator and gravitational moment arm curve. |
| **EV-10** | Cervical Musculoskeletal Modeling | Vasavada AN, Li S, Delp SL. *Influence of muscle morphometry and moment arms on the moment-generating capacity of human neck muscles.* Spine. 1998;23(4):412-422. | Internal extensor moment arm averaged ~3.5 cm; 3D muscle architectures and paths across C1–C7. | Governs OpenSim dataset kinematics (`vasavada_cervical_flexion_extension.mot/.sto`). |
| **EV-11** | Craniovertebral Angle & Posture | Yip CH, Chiu TT, Poon AT. *The relationship between head posture and severity and disability of patients with neck pain.* Man Ther. 2008;13(2):148-154. | Normal CVA > 50°; CVA < 50° correlates with forward head translation and clinical neck disability index (NDI). | Metric `cva_deg` calculation and normal/moderate/marked classification. |
| **EV-12** | Deep Neck Flexor Motor Control | Jull G, Trott P, Potter H, et al. *A randomized controlled trial of exercise and manipulative therapy for cervicogenic headache.* Spine. 2002;27(17):1835-1843. | Low-load craniocervical flexion test (CCFT) preferentially recruits Longus Colli without SCM substitution. | Explains motor re-education stage in curriculum (Stages 4 & 7). |
| **EV-13** | Upper Crossed Syndrome | Janda V. *Muscles and Motor Control in Cervicothoracic Disorders.* Physical Therapy of the Cervical and Thoracic Spine. 1988:182-199. | Stereotypical crossed imbalance: hyperactive upper trap/levator/suboccipitals vs inhibited deep neck flexors/lower trap/serratus. | Basis of interactive UCS diagram and muscle activation colormaps. |
| **EV-14** | Suboccipital Proprioception | Kulkarni V, Chandy MJ, Babu KS. *Quantitative study of muscle spindles in suboccipital muscles of human fetuses.* Neurol India. 2001;49(4):355-359. | Rectus capitis posterior minor has extraordinarily high spindle density (up to 98 spindles/g), serving as a cranial kinesthetic sensor. | Suboccipital spindle density explanation and proprioceptive drift callouts. |
| **EV-15** | Levator Scapulae & Scapular Dyskinesis | Kibler WB, Ludewig PM, McClure PW, et al. *Clinical implications of scapular dyskinesis in shoulder injury: the 2013 consensus statement.* Br J Sports Med. 2013;47(14):877-885. | Scapular downward rotation/anterior tilt stretches levator scapulae under eccentric tension; coupled shoulder-neck dysfunction. | Dual-region kinematic chain coupling C1–C4 to superior scapular angle. |
| **EV-16** | Upper vs Lower Trapezius Balance | Cools AM, Declercq GA, Cambier DC, et al. *Trapezius activity and intramuscular balance during rehabilitative exercises in overhead athletes.* Am J Sports Med. 2007;35(10):1744-1751. | Optimal rehabilitation requires minimizing upper trapezius dominance while selectively activating lower trapezius and serratus anterior. | Stage 8 exercise selection and force-couple balance instruction. |

---

## 3. Epistemic Guardrails & Disclaimer Adherence
All evidence items EV-09 to EV-16 are explicitly tied to the project invariants:
- `ANATOMICAL_MODEL != SUBJECT_SPECIFIC_ANATOMY`
- `ILLUSTRATIVE_KINEMATICS != MEASURED_KINEMATICS`
- `OPTIMIZED_MUSCLE_ACTIVATION != MEASURED_EMG`
- `FORWARD_HEAD_VARIATION != STRUCTURAL_DEFORMITY_DIAGNOSIS`
- `ANIMATION_SUCCESS != BIOMECHANICAL_VALIDATION`
