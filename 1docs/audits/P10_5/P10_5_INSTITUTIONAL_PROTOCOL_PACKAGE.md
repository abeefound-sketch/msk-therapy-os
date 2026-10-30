# P10.5 INSTITUTIONAL PILOT RESEARCH PROTOCOL PACKAGE

> [!WARNING]
> **DOCUMENT STATUS: DRAFT — INSTITUTIONAL REVIEW REQUIRED**  
> *This clinical research protocol package is prepared for prospective academic hospital research teams, ethics review boards, and radiology departments. No clinical partnership, data transfer agreement, or institutional review board clearance has been executed. All sections are subject to institutional review and bilateral modification.*

**Milestone:** P10.5 — Institutional Research Pilot Activation, Statistical Design Verification & External Evidence Acquisition Readiness  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**System Version:** `v2.1.0-local-rc3`  
**Date:** 2026-10-30  
**Gate P503 Verdict:** **PASS (COMPREHENSIVE PROTOCOL PACKAGE SPECIFIED)**

---

## 1. Executive Summary & Clinical Research Context

MSK-Therapy-OS is an offline-first computational anatomy platform designed to visualize musculoskeletal landmarks and traditional meridian trajectories relative to anatomical structures. This protocol outlines an empirical observational study to evaluate the spatial concordance of algorithmically inferred acupuncture landmarks against expert radiological ground truth.

---

## 2. Cohort-Specific Clinical Protocols

### 2.1 Cohort A: Abdominal Landmarks
- **Primary Anatomical Targets:** Umbilicus, Xiphisternal junction, Pubic symphysis crest, Anterior superior iliac spine (ASIS), Costal margins. Traditional meridian correspondences: Ren (CV8, CV12), Kidney (KI11–KI16), Stomach (ST21–ST25), Spleen (SP13–SP15).
- **Imaging Modality & Parameters:** Axial helical CT; slice thickness $\le 1.25\text{ mm}$; pitch $\le 1.0$; $120\text{ kVp}$; automated tube current modulation; reconstructed on bone and standard soft-tissue kernels.
- **Positioning & Respiratory Control:** Patient supine, arms extended above head, scanned at comfortable end-expiratory breath-hold to standardize diaphragmatic position.
- **Body Habitus & Adipose Tissue Considerations:** Subcutaneous adipose tissue layer thickness measured at midline; cohort stratified into normal BMI ($18.5\text{–}24.9$) and overweight/obese ($25.0\text{–}34.9$).
- **Registration Methodology:** Affine rigid registration on vertebral column (L1–L5) and pelvic girdle, followed by non-rigid thin-plate spline deformation mapping on anterior fascial skin surface.
- **Measurement Uncertainty:** Anticipated soft-tissue surface uncertainty $\pm 2.5\text{ mm}$.
- **Exclusion Criteria:** Prior open abdominal surgery with major scarring, abdominal aortic aneurysm $>4.5\text{ cm}$, massive ascites, or active abdominal wall hernia.

### 2.2 Cohort B: Bilateral Extremities
- **Primary Anatomical Targets:** 
  - Knee & Lower Leg: Tibial tuberosity, Patellar inferior pole, Medial/Lateral femoral epicondyles, Fibular head, Medial malleolus tip.
  - Forearm & Wrist: Radial styloid, Ulnar styloid, Biceps distal tendon insertion, Medial/Lateral humeral epicondyles.
- **Positioning Standardization:** 
  - Knee: Positioned in dedicated extremity coil with standardized $15^\circ\text{–}20^\circ$ flexion wedge; foot secured in neutral alignment.
  - Forearm: Forearm supinated; wrist in neutral extension ($0^\circ$).
- **Modality & Parameters:** High-resolution 1.5T or 3T MRI (Proton Density / T1-weighted TSE, slice thickness $\le 2.5\text{ mm}$, matrix $\ge 384\times 384$) or Volumetric extremity CT ($\le 1.0\text{ mm}$).
- **Laterality & Bilateral Asymmetry Analysis:** Bilateral imaging required for each subject. Coordinate symmetry evaluated as:
  $$d_{\text{asym}} = \| p_{\text{left}} - \text{Reflect}(p_{\text{right}}) \|$$
- **Segment Registration:** Segmental articulated rigid-body registration (Femur, Tibia/Fibula, Foot treated as separate kinematic links).
- **Exclusion Criteria:** Prior orthopedic joint replacement hardware, severe post-traumatic bony deformity, severe fixed flexion contracture.

### 2.3 Cohort C: Craniofacial Landmarks
- **Primary Anatomical Targets:** Nasion, Inion, Glabella, External Occipital Protuberance (EOP), Mastoid process tips, C7 spinous process, Anterior and Posterior hairline anchors. Traditional meridian correspondences: Du (GV14–GV24), Bladder (BL1–BL10), Gallbladder (GB1–GB20).
- **Imaging Modality:** High-resolution volumetric CT ($\le 1.0\text{ mm}$ isotropic voxels) or 3D T1-weighted MPRAGE MRI ($\le 1.0\text{ mm}^3$).
- **Facial Biometric Privacy & Defacing:** Mandatory skull-stripping or ear/nose surface-cropping according to DICOM PS 3.15 Annex E safe harbor rules, ensuring that 3D facial recognition algorithms cannot reconstruct recognizable patient faces.
- **Registration Methodology:** Rigid-body registration based on osseous landmarks of the cranial vault and skull base.
- **Exclusion Criteria:** Extensive craniotomy, craniofacial dysmorphism, extensive dental artifact obscuring cranial base.

---

## 3. Suite of Thirteen Prespecified Research Documents (DRAFT)

| Document Name | Functional Scope | Key Controls & Invariants |
|---|---|---|
| **DOC-01: Research Protocol Narrative** | Complete study background, objectives, and ethical framework. | Defines research-use boundaries; excludes clinical guidance. |
| **DOC-02: Statistical Analysis Plan (SAP)** | Prespecified hypotheses, endpoints, power, and LMM estimators. | Bonferroni / FDR control; model-lock before holdout unblinding. |
| **DOC-03: Dataset Specification** | JSON and DICOM header schemas for multi-site data. | Conforms to `v2.0-P10.4` research data contract. |
| **DOC-04: Imaging Acquisition SOP** | Detailed scanner positioning and parameter guidelines. | Limits slice thickness; enforces breath-hold and positioning wedges. |
| **DOC-05: Observer Training Manual** | Anatomical landmark identification atlas with CT/MRI cross-sections. | Prohibits showing model predictions to observers. |
| **DOC-06: Adjudication Protocol** | Rules for third-reviewer resolution of inter-observer discrepancies. | Inter-observer thresholds: $3\text{ mm}$ cranial, $5\text{ mm}$ extremity/abdomen. |
| **DOC-07: Data Management Plan** | Air-gapped offline storage, backup, and cryptographic verification. | 100% offline-first; encrypted AES-256 local storage. |
| **DOC-08: Privacy & Security Risk Assessment** | Assessment of re-identification risks and mitigation strategies. | DICOM PS 3.15 Safe Harbor conformance; 18 PHI tags stripped. |
| **DOC-09: DUA/MTA Review Checklist** | Standardized bilateral legal agreement template. | Retrospective de-identified data; 3-year retention; no re-ID. |
| **DOC-10: IRB Submission Checklist** | Complete ethics review packet for expedited review / waiver. | 45 CFR 46.116(f) waiver of consent narrative. |
| **DOC-11: Inclusion / Exclusion Matrix** | Standardized cohort-specific medical criteria. | Eliminates gross anatomical deformities and metallic artifacts. |
| **DOC-12: Protocol Deviation SOP** | Protocol violation recording and sensitivity analysis policy. | Deviations logged in immutable SQLite audit table. |
| **DOC-13: Evidence Acceptance Matrix** | Formal acceptance criteria for study completion. | RMSE $\le 4.0\text{ mm}$, Mean $\le 3.0\text{ mm}$, P95 $\le 6.0\text{ mm}$. |

---

## 4. External Dependency Declaration

All 13 documents in this protocol package are formally marked **DRAFT — INSTITUTIONAL REVIEW REQUIRED**. No clinical trial or data collection may commence until bilateral signatures and institutional ethics clearances are obtained.

Gate P503 is certified as **PASS**.
