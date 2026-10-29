# P10.2 CLINICAL PILOT PROTOCOLS — COHORTS A, B, AND C
## Draft Empirical Validation Specifications for Independent Ground-Truth Acquisition

> **CLASSIFICATION:** RESEARCH PROTOCOL SPECIFICATION — DRAFT  
> **STATUS:** PENDING INSTITUTIONAL ETHICAL & DUA REVIEW — NOT FOR CLINICAL USE  
> **MILESTONE:** P10.2  
> **GOVERNANCE STATUS:** ENGINEERING SPECIFICATION ONLY — NO PATIENT DATA COLLECTED YET  
> **SCIENTIFIC INVARIANT:**  
> `TECHNICAL_CALIBRATION != INDEPENDENT_ANATOMICAL_GROUND_TRUTH != CLINICAL_VALIDATION`

---

## 1. Executive Protocol Overview & Regulatory Framing

This document establishes the formal preregistered validation protocols for the three independent anatomical pilot cohorts designed to benchmark MSK-Therapy-OS's computational atlas against empirical, high-resolution human in-vivo imaging (CT/MRI) and multi-observer optical surface digitizations.

Under the P10.2 governance architecture, these protocols provide the exact technical criteria that external institutional partners must satisfy prior to dataset ingestion. They ensure that subsequent evaluation of Gate G14 is objective, reproducible, and mathematically uncompromised by synthetic assumptions.

```
       +--------------------------------------------------------------+
       |   MSK-Therapy-OS Independent Validation Framework            |
       +--------------------------------------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                            |                            |
         v                            v                            v
  +--------------+             +--------------+             +--------------+
  |   Cohort A   |             |   Cohort B   |             |   Cohort C   |
  |  (Abdomen)   |             | (Extremities)|             |(Craniofacial)|
  |  ST19-ST30   |             |  Bilateral   |             | Yintang/GV24+|
  +--------------+             +--------------+             +--------------+
```

---

## 2. Cohort A Protocol: Abdominal Meridian Points (ST19 – ST30)

### 2.1 Scope & Validation Focus
- **Primary Region:** Ventral trunk / anterolateral abdominal wall.
- **Key Points:** Bilateral Stomach Meridian points ST19 (Burong) through ST30 (Qichong), along with reference midline landmarks (CV8 Umbilicus, CV16 Shenque/Xiphoid junction, CV2 Qugu/Pubic symphysis).
- **Core Scientific Questions:**
  1. How does variable abdominal wall thickness and subcutaneous adipose distribution (BMI stratification: normal, overweight, obese) affect horizontal cun metric proportional scaling (2 cun lateral to anterior midline)?
  2. Does the respiratory phase (end-expiration vs end-inspiration) introduce significant vertical displacement of upper abdominal points (ST19–ST21) relative to lower points (ST27–ST30)?

### 2.2 Eligibility Criteria
- **Inclusion Criteria:**
  - Adult subjects (aged 18–70 years).
  - Contrast or non-contrast abdominal/pelvic volumetric CT or 3D MRI scans acquired for diagnostic indications.
  - Slice thickness $\le 1.5\text{ mm}$ (isotropic or near-isotropic voxel reconstruction $\le 1.0 \times 1.0 \times 1.5\text{ mm}^3$).
  - Scan coverage: Superiorly from xiphisternal joint down to inferior margin of pubic symphysis.
- **Exclusion Criteria:**
  - Prior open abdominal surgery with major midline laparotomy scars or anatomical disruption.
  - Large abdominal ventral or incisional hernias disrupting rectus abdominis anatomy.
  - Significant ascites, large abdominal masses, or organomegaly displacing the anterior abdominal wall $> 15\text{ mm}$.
  - Severe motion artifacts (motion score $\ge 3$ on 1–5 scale).

### 2.3 Observation Procedure & Imaging Protocol
1. **Patient Positioning:** Supine, arms resting at sides or folded across upper thorax, neutral lumbar spine.
2. **Breathing Phase:** Helical CT acquisition during suspended end-expiration breath-hold.
3. **Fiducial Landmark Identification:**
   - Landmark L1: Inferior tip of Xiphisternal Joint.
   - Landmark L2: Center of Umbilical ring (CV8).
   - Landmark L3: Superior border of Pubic Symphysis at midline (CV2).
   - Landmark L4 & L5: Bilateral Anterior Superior Iliac Spines (ASIS).
4. **Point Localization Procedure:**
   - Independent observers mark cutaneous projection points ST19–ST30 on 3D volumetric skin surface reconstruction based on the classical WHO proportional cun definitions (ST25 at umbilical level, 2 cun lateral; ST19–ST24 spaced 1 cun intervals superiorly; ST26–ST30 spaced 1 cun intervals inferiorly).

### 2.4 Independent Reference Measurement Standard
- Multi-planar CT reconstruction (MPR) verified by two board-certified musculoskeletal/abdominal radiologists.
- Voxel coordinates $(X, Y, Z)$ recorded in DICOM LPS frame, verified against bone/fascia anatomical landmarks (e.g. lateral border of rectus abdominis sheath).

### 2.5 Anatomical Alignment Method
- Rigid 3D Procrustes alignment using the 5 primary skeletal/cutaneous landmarks (Xiphoid, Umbilicus, Pubic symphysis, Left ASIS, Right ASIS) to register the subject frame to the standard BodyParts3D reference frame.
- Procrustes registration residual root-mean-square must be recorded.

### 2.6 Quality Control Thresholds
- Slice thickness: $\le 1.5\text{ mm}$.
- In-plane pixel spacing: $\le 0.8\text{ mm}$.
- Fiducial registration RMSE: $\le 3.0\text{ mm}$.
- Inter-observer spatial discrepancy: $\le 2.5\text{ mm}$.

### 2.7 Preregistered Analysis Plan
- Primary Endpoint: Root Mean Square Error ($\text{RMSE}$) between predicted model coordinates and consensus ground truth across ST19–ST30.
- Hypotheses:
  - $H_0$: $\text{RMSE} > 10.0\text{ mm}$ (Atlas fails acceptable precision threshold).
  - $H_1$: $\text{RMSE} \le 10.0\text{ mm}$ (Atlas meets acceptable threshold).
  - $H_{1,\text{high}}$: $\text{RMSE} \le 5.0\text{ mm}$ (Atlas achieves high precision benchmark).
- Subgroup analyses: BMI $< 25$, $25 \le \text{BMI} < 30$, $\text{BMI} \ge 30$.

### 2.8 Failure Rules & Abort Criteria
- Individual observation rejected if fiducial alignment residual $> 5.0\text{ mm}$.
- Subject excluded if breathing motion artifact induces $> 3.0\text{ mm}$ step artifact along the anterior abdominal contour.

### 2.9 Institutional Approvals & Governance
- Requires IRB / Institutional Ethics Committee approved protocol or formal non-human subject research (NHSR) exemption for anonymized retrospective data.
- Executed Data Use Agreement (DUA) specifying research-only, non-commercial use.

### 2.10 Acceptance Criteria & Dispute Resolution
- Dual independent review required for all point annotations.
- If spatial Euclidean distance between Observer 1 and Observer 2 is $> 3.0\text{ mm}$, an adjudicating Senior Radiologist must arbitrate or the observation is quarantined.

---

## 3. Cohort B Protocol: Bilateral Extremities (Upper & Lower Limbs)

### 3.1 Scope & Validation Focus
- **Primary Region:** Bilateral upper limbs (LI, LU, PC, HT, TE, SI channels) and lower limbs (ST, SP, BL, KI, GB, LR channels).
- **Core Scientific Questions:**
  1. What is the magnitude of left-to-right anatomical asymmetry under controlled postural conditions?
  2. How do joint flexion/extension angles (e.g. cubital joint $0^\circ$ vs $90^\circ$, knee joint $0^\circ$ vs $90^\circ$) shift superficial cutaneous landmarks relative to underlying osseous landmarks?

### 3.2 Eligibility Criteria
- **Inclusion Criteria:**
  - Adult subjects (aged 18–65 years).
  - Volumetric MRI or CT covering full limb segments (elbow-to-hand or knee-to-foot).
  - High-precision 3D optical surface scans ($\le 0.5\text{ mm}$ spatial accuracy) paired with anatomical palpation tags.
- **Exclusion Criteria:**
  - History of limb fracture, severe osteoarthritis, joint contracture, or congenital limb anomaly.
  - Unilateral atrophy or hypertrophy (e.g. post-stroke hemiparesis, lymphedema).
  - Metallic implants creating substantial CT/MRI susceptibility artifacts.

### 3.3 Observation Procedure
1. Standardized neutral limb posture:
   - Upper extremity: Forearm supinated, elbow extended at $0^\circ$ or standardized $90^\circ$ flexion on positioning wedge.
   - Lower extremity: Supine, patella facing vertical, ankle at $90^\circ$ neutral dorsiflexion.
2. Palpation and marking of bony epicondyles, malleoli, and styloid processes using radiopaque/optical multi-modality fiducial markers.

### 3.4 Independent Reference Measurement Standard
- Combined 3D optical stereophotogrammetry registered with volumetric bone CT/MRI reconstructions.
- Coordinate frame: LPS DICOM, converted to BodyParts3D standard meters.

### 3.5 Anatomical Alignment Method
- Segmental affine/rigid registration anchored to bony landmarks (e.g., medial/lateral humeral epicondyles + radial styloid for forearm; tibial tuberosity + medial/lateral malleoli for lower leg).

### 3.6 Quality Control Thresholds
- Joint angle deviation from nominal: $\le 3^\circ$.
- Marker localization uncertainty: $\le 1.0\text{ mm}$.
- Left/right registration consistency check: residual symmetry error $\le 2.0\text{ mm}$.

### 3.7 Preregistered Analysis Plan
- Primary Endpoint: Bilateral error differential $\Delta_{L-R} = |\text{RMSE}_L - \text{RMSE}_R|$.
- Assessment of whether proportional cun rules maintain bilateral symmetry within $\pm 2.5\text{ mm}$.

### 3.8 Failure Rules & Abort Criteria
- Inadvertent limb rotation or postural movement between scans $> 5^\circ$ triggers exclusion.
- Sub-millimeter fiducial displacement $> 2.0\text{ mm}$ between modality registrations triggers data quarantine.

### 3.9 Institutional Approvals & Governance
- Standard IRB protocol with informed consent for prospective optical scanning, or IRB-waived retrospective imaging transfer under formal DUA.

### 3.10 Acceptance & Escalation Criteria
- Two independent observers mark bilateral point pairs.
- If laterality discrepancy exceeds $4.0\text{ mm}$, case is reviewed by musculoskeletal anatomy specialist.

---

## 4. Cohort C Protocol: Craniofacial and Cervical Region (GV24+, Yintang, Head/Neck)

### 4.1 Scope & Validation Focus
- **Primary Region:** Craniofacial midline, forehead, orbit, auricle, and cervical spine (C1–C7).
- **Key Points:** EX-HN3 (Yintang), GV24 (Shenting), GV20 (Baihui), GB20 (Fengchi), BL1 (Jingming), ST1 (Chengqi).
- **Core Scientific Questions:**
  1. Yintang / GV24+ provenance: Clarify the precise anatomical boundary between extra point EX-HN3 (glabella midpoint between eyebrows) and classical GV24/GV24+ along the frontal midline.
  2. How do cranial index variations (brachycephalic vs dolichocephalic) alter anterior-posterior cun division along the sagittal midline?

### 4.2 Eligibility Criteria
- **Inclusion Criteria:**
  - High-resolution volumetric Head/Neck CT or 3D T1-weighted MRI ($\le 1.0\text{ mm}$ isotropic voxels).
  - Clear visualization of soft tissue nasion, glabella, trichion (anterior hairline), inion, external auditory meatus, and cervical spinous processes.
- **Exclusion Criteria:**
  - Facial trauma, craniotomy, extensive plastic/reconstructive surgery.
  - Severe cervical spine deformity (kyphoscoliosis, major spondylolisthesis).

### 4.3 Observation Procedure
1. Positioning: Head positioned in standardized head-holder with Frankfurt horizontal plane perpendicular to table.
2. Anatomic landmarks:
   - Nasion (nasofrontal suture depression).
   - Glabella (most prominent midline point between eyebrows).
   - Trichion (midline anterior hairline boundary).
   - Inion (external occipital protuberance).
   - Bilateral Tragus and Outer Canthi.

### 4.4 Independent Reference Measurement Standard
- Sub-millimeter cranial CT/MRI multi-planar reconstructions verified against cephalometric standards.

### 4.5 Anatomical Alignment Method
- Rigid 6-degrees-of-freedom registration anchored to rigid bony cranial landmarks (Nasion, Sella turcica, Basion, Porion).

### 4.6 Quality Control Thresholds
- Isotropic voxel size: $\le 1.0\text{ mm}$.
- Cranial rigid registration RMSE: $\le 1.5\text{ mm}$.
- Inter-observer landmark identification error: $\le 1.5\text{ mm}$.

### 4.7 Preregistered Analysis Plan
- Evaluation of Yintang (EX-HN3) localization relative to Glabella and nasion-trichion distance.
- Primary Endpoint: Model-predicted Yintang vs consensus empirical ground truth. Target RMSE $\le 3.0\text{ mm}$.
- Assessment of sagittal midline deviation: Lateral bias $\Delta X$ must be statistically indistinguishable from $0$ ($p > 0.05$).

### 4.8 Failure Rules & Abort Criteria
- Motion blur obscuring soft-tissue skin surface contours at nasion or glabella causes rejection.
- Registration error $> 2.0\text{ mm}$ across cranial base landmarks invalidates subject.

### 4.9 Institutional Approvals & Governance
- IRB approval under head/neck research protocol.
- Defacing / facial surface obfuscation or secure HIPAA-compliant data enclave required to protect craniofacial biometric privacy.

### 4.10 Acceptance Criteria & Dispute Resolution
- Discrepancies between observers $> 2.0\text{ mm}$ for Yintang / GV24 require joint review with anatomical specialist.

---

## 5. Summary Matrix of Cohort Protocol Specifications

| Dimension | Cohort A (Abdomen) | Cohort B (Extremities) | Cohort C (Craniofacial) |
|---|---|---|---|
| **Primary Region** | ST19–ST30, CV midline | Bilateral upper/lower limbs | Glabella, Yintang, GV24+, GB20 |
| **Imaging Modality** | Abdomino-pelvic CT/MRI | CT/MRI + 3D Optical Scan | Head/Neck CT / 3D T1 MRI |
| **Slice Thickness** | $\le 1.5\text{ mm}$ | $\le 1.5\text{ mm}$ (scan $\le 0.5\text{ mm}$) | $\le 1.0\text{ mm}$ isotropic |
| **Key Variable** | Adipose thickness, breathing | Joint posture, limb symmetry | Cranial index, sagittal midline |
| **Primary Fiducials** | Xiphoid, Umbilicus, Pubic, ASIS | Epicondyles, styloids, malleoli | Nasion, Inion, Tragus, Porion |
| **Registration Target**| RMSE $\le 3.0\text{ mm}$ | RMSE $\le 2.0\text{ mm}$ | RMSE $\le 1.5\text{ mm}$ |
| **Accuracy Threshold** | Target $\le 10\text{ mm}$ (opt $\le 5\text{ mm}$) | Target $\le 10\text{ mm}$ (opt $\le 5\text{ mm}$) | Target $\le 5\text{ mm}$ (opt $\le 3\text{ mm}$) |
| **Governance Req** | DUA + IRB (Retrospective) | DUA + IRB (Prospective/Retro) | DUA + IRB + Facial Biometric Enclave |
| **Current Status** | DRAFT — READY FOR PARTNERS | DRAFT — READY FOR PARTNERS | DRAFT — READY FOR PARTNERS |

---

## 6. Regulatory Affirmation & Next Steps

These protocols do **NOT** constitute active clinical research by the software engineering team, but define the strict scientific intake requirements for future academic clinical collaborations.

Until genuine empirical data sets matching these criteria are formally ingested, audited, and processed through the blinded validation engine:
- Gate G14 remains strictly **`BLOCKED_EXTERNAL_DATA`**.
- Milestone P10.2 certifies **Protocol & Architecture Readiness**.
