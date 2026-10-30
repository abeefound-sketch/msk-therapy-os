# DRAFT — PROSPECTIVE RESEARCH COLLABORATION PROPOSAL
## Institutional Research Partner Package: Charité – Universitätsmedizin Berlin, Germany

### Document Metadata
- **Package ID**: `PARTNER-PKG-CHARITE-v1.0-DRAFT`
- **Candidate Institution**: Charité – Universitätsmedizin Berlin (Department of Radiology / Institute of Functional Anatomy)
- **Jurisdiction**: Berlin, Federal Republic of Germany (EU GDPR & German Federal Data Protection Act BDSG)
- **Status**: **PROSPECTIVE CANDIDATE ONLY — NON-BINDING DRAFT / NOT YET TRANSMITTED**
- **Date**: 2026-10-30
- **Classification**: CONFIDENTIAL RESEARCH EXPLORATION PROPOSAL

---

> [!IMPORTANT]
> **LEGAL & INSTITUTIONAL DISCLAIMER**:  
> Charité – Universitätsmedizin Berlin is a prospective candidate research partner. **No formal agreement, institutional endorsement, data transfer, or clinical partnership has been executed.** This document constitutes an unapproved engineering proposal intended for prospective scientific peer dialogue and legal/ethical review. Zero emails or requests have been dispatched to Charité personnel.

---

## 1. Research Collaboration Executive Brief
This proposal invites the Department of Radiology and the Institute of Functional Anatomy at Charité – Universitätsmedizin Berlin to participate as a primary European clinical imaging partner in an offline, retrospective computational anatomy validation study of **MSK-Therapy-OS**. The collaboration seeks to independently evaluate the spatial registration accuracy of computational musculoskeletal surface models against high-resolution, de-identified DICOM CT and MRI scans.

---

## 2. Proposed Study Rationale
Computational anatomical atlases and surface projection algorithms frequently suffer from geometric errors when translated to heterogeneous patient populations. Independent validation on real-world European clinical imaging data is necessary to quantify surface registration accuracy, assess anatomical symmetry, and establish the limits of computational body mapping.

---

## 3. Institutional Fit & Required Expertise
Charité Berlin represents one of Europe's largest university hospitals with renowned expertise in musculoskeletal imaging, high-resolution volumetric CT/MRI acquisition protocols, and digital anatomy. The study requires:
- Board-certified musculoskeletal radiologists with experience in multi-planar CT/MRI landmarking.
- Academic anatomists experienced in surface fascia and skeletal anatomy.
- Dedicated PACS data custodian familiar with automated DICOM de-identification pipelines.

---

## 4. Cohort A/B/C Scope Allocation
Charité is invited to contribute across three retrospective cohorts:
- **Cohort A (Abdomen/Trunk)**: $N = 15\text{–}30$ Helical CT scans ($\le 1.25\text{ mm}$ slice thickness).
- **Cohort B (Bilateral Extremities)**: $N = 15\text{–}25$ Knee MRI scans (1.5T or 3.0T, standardized $15^\circ\text{–}20^\circ$ wedge flexion).
- **Cohort C (Craniofacial)**: $N = 15\text{–}30$ High-resolution head/neck CT scans ($\le 1.0\text{ mm}$ slice thickness) with automated facial defacing.

---

## 5. Statistical Design Options
Charité investigators may select between two study designs:
- **Option 1 (Primary Pilot Feasibility, Scenario 2)**: $N = 85$ total multi-center subjects (Charité allocation: $\sim 42$ subjects), providing $>95\%$ holdout power for Craniofacial and Abdomen.
- **Option 2 (Confirmatory Subgroup Study, Scenario 3)**: $N = 115$ total multi-center subjects (Charité allocation: $\sim 58$ subjects), ensuring $>90\%$ holdout power for all three cohorts independently.

---

## 6. Imaging Data Technical Specification
- **CT**: Helical volumetric reconstruction, $512 \times 512$ matrix, slice thickness $\le 1.25\text{ mm}$, soft tissue + bone kernel.
- **MRI**: 3D T1-weighted or Proton Density volumetric series, in-plane resolution $\le 0.5\text{ mm} \times 0.5\text{ mm}$, slice thickness $\le 2.0\text{ mm}$.
- **Storage Format**: Standard DICOM Part 10 files.

---

## 7. DICOM & De-Identification Requirements
In compliance with EU GDPR (Regulation EU 2016/679) and DICOM PS 3.15 Annex E Basic Application Confidentiality Profile:
- All 18 HIPAA / GDPR direct identifiers (Name, Patient ID, DOB, Admission dates, Referring Physician) must be cryptographically cleansed prior to transfer.
- Automated OCR pixel screening must be certified to guarantee zero burned-in text.
- Cohort C cranial CT scans must be processed with automated facial defacing / skull-stripping algorithms.

---

## 8. Independent Observer Requirements
- Two independent, double-blind observers:
  - Observer A: Board-certified radiologist (Facharzt für Radiologie).
  - Observer B: Senior anatomist (Institut für Anatomie).
- Neither observer may be exposed to model-predicted coordinates.
- Inter-observer discrepancies exceeding category thresholds ($3\text{ mm}$ cranial, $4\text{ mm}$ extremity, $5\text{ mm}$ abdominal) are referred to a third senior clinical adjudicator.

---

## 9. Data Governance & Security Model
- **Offline First**: All validation tooling operates locally in an air-gapped staging directory (`EXTERNAL_QUARANTINED`). Zero internet egress or external cloud syncing.
- **Custody Audit Trail**: Every data movement, tag audit, and annotation attachment is recorded in an immutable, SHA-256 hashed SQLite ledger.

---

## 10. Data Use Agreement (DUA / MTA) Review Checklist
- [ ] Retrospective, de-identified research use scope strictly delimited.
- [ ] Explicit prohibition of patient re-identification attempts.
- [ ] Data ownership retained entirely by Charité – Universitätsmedizin Berlin.
- [ ] Research use only classification: zero commercial medical device promotion.
- [ ] Data retention, expiration, and secure cryptographic erasure provisions.

---

## 11. Ethics & Institutional Review Board (IRB / IEC) Checklist
- [ ] Submission to the Ethics Committee of Charité (Ethikkommission der Charité – Universitätsmedizin Berlin).
- [ ] Application for retrospective waiver of informed consent for fully anonymized archival imaging data.
- [ ] Data Protection Officer (Datenschutzbeauftragter) consultation and endorsement.

---

## 12. Research Responsibilities Matrix
| Responsibility Area | MSK-Therapy-OS Research Team | Charité Research Team |
|:---|:---:|:---:|
| Computational Registration Pipeline | Lead / Maintain | Review / Audit |
| De-Identified DICOM Extraction | Advisory | Lead / Execute |
| Double-Blind Expert Annotation | Prohibited (Developer Exclusion) | Lead / Execute |
| Independent Biostatistical Audit | Coordinate with 3rd Party | Audit / Co-Author |
| Scientific Publication Drafting | Joint Author | Joint Author / Senior PI |

---

## 13. Proposed Non-Binding Collaboration Workflow
1. Technical and protocol transmittal review by Charité Radiology / Anatomy leads.
2. Legal counsel review of standard bilateral DUA.
3. Charité Ethics Committee submission for retrospective waiver.
4. Pilot staging sandbox deployment and test batch verification ($N = 5$).
5. Main study ingestion, double-blind annotation, and holdout locking.

---

## 14. Risk & Limitation Disclosure
- Research-Use Only: MSK-Therapy-OS is an engineering research tool, NOT an approved medical device.
- Zero Puncture Depth Guidance: Invasive clinical depth guidance is permanently disabled.
- Scientific Gate G14 remains `BLOCKED_EXTERNAL_DATA` until empirical data analysis is finalized.

---

## 15. Research Transmittal Manifest (Placeholder / Verification Record)
- **Target Institutional Unit**: Charité – Universitätsmedizin Berlin, Charitéplatz 1, 10117 Berlin, Germany.
- **Proposed Clinical Contact (Placeholder)**: `[TO BE DESIGNATED BY CHARITÉ DEPT OF RADIOLOGY]`
- **Proposed Radiology Lead (Placeholder)**: `[TO BE DESIGNATED BY CHARITÉ MUSCULOSKELETAL RADIOLOGY]`
- **Data Protection Officer (Public)**: Datenschutzbeauftragte der Charité, Charitéplatz 1, 10117 Berlin.

---

## 16. Draft Introduction Email (Unsent Template)
```text
Subject: Prospective Research Proposal: Retrospective Computational Anatomy Validation (MSK-Therapy-OS)

Dear Colleagues at the Department of Radiology and Institute of Functional Anatomy,

We are writing to explore the potential for an academic research collaboration between your department 
and the MSK-Therapy-OS computational anatomy project.

We have developed an offline, open-source computational atlas pipeline for 3D anatomical surface registration. 
To rigorously establish its spatial accuracy, we have drafted a comprehensive Statistical Analysis Plan (SAP) 
and clinical imaging protocol (Cohorts A, B, and C) evaluating registration residuals against retrospective 
CT and MRI ground truth.

We would welcome an exploratory, non-binding technical dialogue with your musculoskeletal imaging and anatomy 
faculty to discuss whether this study aligns with your research priorities. All imaging data would remain 
strictly de-identified, on-premises, and governed under bilateral DUA and Charité Ethics Committee oversight.

A complete draft protocol package is available for your inspection.

Sincerely,
[Principal Investigator / Computational Anatomy Research Team]
MSK-Therapy-OS Research Project
```

---

## 17. Outstanding Decisions & Information Requests
1. Formal confirmation of preferred scan resolution parameters for knee MRI protocols at Charité.
2. Determination of whether Charité Ethics Committee requires formal full review or expedited waiver for retrospective de-faced CT datasets.
3. Identification of designated Charité radiology faculty co-investigator.
