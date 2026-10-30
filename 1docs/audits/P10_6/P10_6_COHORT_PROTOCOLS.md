# DRAFT — INDEPENDENT SCIENTIFIC AND INSTITUTIONAL REVIEW REQUIRED
# MSK-THERAPY-OS AUDIT REPORT: P10.6-06
## Cohort-Specific Anatomical Imaging Protocols: Cohorts A, B & C (Gate P603B)

### Metadata
- **Document Title**: Clinical Imaging & Ground-Truth Annotation Protocols across Cohorts A, B & C
- **Document Identifier**: `PROT-MSK-OS-P10.6-COHORTS-v2.0-DRAFT`
- **Milestone**: P10.6 (Independent Statistical Truth Audit, Institutional Partnership Readiness & Scientific Evidence Governance)
- **Status**: **DRAFT — PENDING INDEPENDENT BIOSTATISTICAL & ETHICAL APPROVAL**
- **Effective Version**: `v2.0-DRAFT-P10.6`
- **Audit Date**: 2026-10-30
- **Classification**: CLINICAL IMAGING SPECIFICATION / PROTOCOL DRAFT

---

## 1. Executive Overview & Scope Invariants

This document establishes the binding acquisition parameters, subject eligibility criteria, anatomical landmark definitions, and double-blind quality control procedures for the three prespecified research validation cohorts:
- **Cohort A**: Abdominal Wall & Trunk (Helical Volumetric CT)
- **Cohort B**: Bilateral Knee Joint & Lower Extremity (Multi-Planar 1.5T / 3.0T MRI)
- **Cohort C**: Craniofacial & Head/Neck (Sub-Millimeter Helical CT with DICOM PS 3.15 Defacing)

```text
========================================================================================
NON-NEGOTIABLE CLINICAL SAFETY INVARIANTS
========================================================================================
1. RESEARCH ATLAS ONLY: Systems evaluates 3D anatomical surface registration accuracy.
2. ZERO NEEDLE DEPTH GUIDANCE: All invasive puncture depth calculations are strictly disabled.
3. RETROSPECTIVE DE-IDENTIFIED DATA ONLY: Zero prospective radiation exposure or patient contact.
========================================================================================
```

---

## 2. Cohort A: Abdominal Wall & Trunk Protocol

### 2.1 Primary Estimand & Purpose
Evaluates computational registration accuracy of the abdominal surface and midline fascial structures against volumetric helical CT ground truth under respiratory and soft-tissue deformability.

### 2.2 Eligible Subjects
- **Inclusion Criteria**:
  1. Adults aged 18–75 years.
  2. Contrast-enhanced or non-contrast helical abdominopelvic CT.
  3. Body Mass Index (BMI) stratified: Normal ($18.5\text{–}24.9$), Overweight ($25.0\text{–}29.9$), Obese Class I ($30.0\text{–}34.9$).
  4. End-expiratory breath-hold acquisition.
- **Exclusion Criteria**:
  1. Prior major open abdominal surgery with extensive midline laparotomy scarring.
  2. Severe abdominal wall hernias (ventral / umbilical) $>3.0\text{ cm}$.
  3. External drains, ostomies, or bulky bandages causing skin contour distortion.

### 2.3 Imaging Technical Criteria
- **Modality**: Helical Volumetric CT (Axial reconstruction).
- **Slice Thickness**: $\le 1.25\text{ mm}$ (contiguous, zero gap).
- **In-Plane Matrix**: $512 \times 512$ (pixel spacing $\le 0.8\text{ mm} \times 0.8\text{ mm}$).
- **Scan Range**: Xiphoid process superiorly to pubic symphysis inferiorly.
- **Tube Voltage**: $100\text{–}120\text{ kVp}$, automated tube current modulation.
- **Reconstruction Kernel**: Standard soft tissue kernel.

### 2.4 Anatomical Landmarks (12 Points per Subject)
1. `XIPHISTERNAL_JUNCTION` (Midline bony-cartilaginous border).
2. `PUBIC_SYMPHYSIS_SUPERIOR_CREST` (Midline superior edge of pubic crest).
3. `UMBILICUS_CENTER` (Centroid of cutaneous depression).
4. `LINEA_ALBA_MIDPOINT_1` (Midpoint between xiphoid and umbilicus).
5. `LINEA_ALBA_MIDPOINT_2` (Midpoint between umbilicus and pubic crest).
6. `ANTERIOR_SUPERIOR_ILIAC_SPINE_L` & `R` (Bony apex).
7. `COSTAL_MARGIN_LOWEST_POINT_L` & `R` (10th rib cartilage).
8. `MID_CLAVICULAR_LINE_ABDOMEN_L` & `R` (Vertical projection points).
9. `INGUINAL_MIDPOINT_L` (Midpoint of inguinal ligament).

### 2.5 Acceptance Criteria & Discrepancy Tolerance
- **Discrepancy Threshold**: $5.0\text{ mm}$ (soft-tissue compliance allowance).
- **Cohort Success Criterion**: Upper 95% Confidence Interval on mean error $\le 3.00\text{ mm}$.

---

## 3. Cohort B: Bilateral Knee & Lower Extremity Protocol

### 3.1 Primary Estimand & Purpose
Evaluates articulated skeletal registration, multi-planar joint positioning invariance, and bilateral anatomical symmetry under variable limb flexion.

### 3.2 Eligible Subjects
- **Inclusion Criteria**:
  1. Adults aged 18–65 years.
  2. Multi-planar knee or lower extremity MRI.
  3. Standardized positioning using a $15^\circ\text{–}20^\circ$ radiolucent flexion wedge under the popliteal fossa.
  4. Neutral ankle rotation ($0^\circ$ dorsiflexion/plantarflexion).
- **Exclusion Criteria**:
  1. Total or unicompartmental knee arthroplasty (metal susceptibility artifact).
  2. Acute high-energy peri-articular fractures or extensive soft-tissue hematoma.
  3. Severe joint contractures prohibiting $15^\circ$ flexion.

### 3.3 Imaging Technical Criteria
- **Modality**: 1.5T or 3.0T MRI.
- **Acquisitions**: 3D T1-weighted or Proton Density (PD) isotropic volumetric series, or high-resolution axial and sagittal 2D FSE.
- **Slice Thickness**: $\le 2.0\text{ mm}$ (3D isotropic) or $\le 3.0\text{ mm}$ (2D contiguous).
- **In-Plane Resolution**: $\le 0.5\text{ mm} \times 0.5\text{ mm}$.
- **FOV**: Standard knee field of view ($16\text{–}18\text{ cm}$).

### 3.4 Anatomical Landmarks (10 Points per Subject)
1. `TIBIAL_TUBEROSITY_APEX` (Most prominent anterior bony tubercle).
2. `PATELLA_INFERIOR_POLE` (Distal osseous apex of patella).
3. `PATELLA_SUPERIOR_POLE` (Proximal osseous border).
4. `MEDIAL_FEMORAL_EPICONDYLE` (Most prominent medial prominence).
5. `LATERAL_FEMORAL_EPICONDYLE` (Most prominent lateral prominence).
6. `HEAD_OF_FIBULA_STYLOID` (Osseous apex of fibular head).
7. `GERDY_TUBERCLE` (Anterolateral tibial insertion site).
8. `JOINT_LINE_ANTEROMEDIAL` (Medial meniscal joint space edge).
9. `JOINT_LINE_ANTEROLATERAL` (Lateral meniscal joint space edge).
10. `MEDIAL_MALLEOLUS_TIP` (Inferior bony apex).

### 3.5 Acceptance Criteria & Discrepancy Tolerance
- **Discrepancy Threshold**: $4.0\text{ mm}$ (skeletal landmark tolerance).
- **Cohort Success Criterion**: Upper 95% Confidence Interval on mean error $\le 3.00\text{ mm}$.

---

## 4. Cohort C: Craniofacial & Head/Neck Protocol

### 4.1 Primary Estimand & Purpose
Evaluates rigid cranial bone surface registration and fiducial localization against sub-millimeter volumetric CT ground truth.

### 4.2 Eligible Subjects & Privacy Defacing Mandate
- **Inclusion Criteria**:
  1. Adults aged 18–80 years.
  2. Volumetric maxillofacial, sinus, or cranial CT series.
  3. Slice thickness $\le 1.0\text{ mm}$.
- **Exclusion Criteria**:
  1. Extensive craniofacial reconstructive hardware spanning the orbital or zygomatic borders.
  2. Displaced cranial or facial fractures.
- **MANDATORY BIOMETRIC DEFACING**: All series must undergo automated DICOM PS 3.15 Annex E compliant facial defacing / skull-stripping to eliminate potential facial biometric re-identification while preserving osseous surface landmarks.

### 4.3 Imaging Technical Criteria
- **Modality**: Helical Volumetric Head/Neck CT.
- **Slice Thickness**: $\le 0.75\text{ mm}\text{–}1.0\text{ mm}$.
- **In-Plane Matrix**: $512 \times 512$ (pixel spacing $\le 0.5\text{ mm} \times 0.5\text{ mm}$).
- **Reconstruction Kernel**: Bone algorithm kernel (e.g., H70/B60) plus soft tissue kernel.

### 4.4 Anatomical Landmarks (13 Points per Subject)
1. `NASION` (Intersection of nasofrontal suture and sagittal plane).
2. `INION` (External occipital protuberance apex).
3. `GLABELLA` (Most prominent anterior point of forehead between brow ridges).
4. `BREGMA` (Intersection of coronal and sagittal sutures).
5. `MASTOID_PROCESS_L` & `R` (Inferior tip of mastoid).
6. `ZYGOMATIC_ARCH_LOWEST_POINT_L` & `R` (Inferior margin of zygoma).
7. `MENTON` (Most inferior point of mandibular symphysis).
8. `GONION_L` & `R` (Posterior-inferior angle of mandible).
9. `TRAGION_L` & `R` (Superior notch of tragus of ear).

### 4.5 Acceptance Criteria & Discrepancy Tolerance
- **Discrepancy Threshold**: $3.0\text{ mm}$ (rigid cranial bone tolerance).
- **Cohort Success Criterion**: Upper 95% Confidence Interval on mean error $\le 2.50\text{ mm}$.

---

## 5. Double-Blind Review & Third-Reviewer Adjudication Protocol

For all three cohorts, landmark annotations must follow the double-blind procedure implemented in [`AnnotationQualityControlEngine`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/annotation_qc.py#L75):
1. **Blinded Observer A** (Board-certified Radiologist) and **Blinded Observer B** (Senior Anatomist) independently locate landmarks without seeing model predictions or each other's coordinates.
2. If Euclidean distance $d \le \text{Threshold}$, consensus coordinate is assigned as the midpoint centroid:
   $$\mathbf{p}_{\text{consensus}} = \frac{\mathbf{p}_A + \mathbf{p}_B}{2}$$
3. If $d > \text{Threshold}$, pair is flagged as `DISCREPANCY_FLAGGED` and submitted to an independent **Third Reviewer (Adjudicator)** who is strictly disqualified from being Observer A or B, and has signed conflict-of-interest disclosures.
