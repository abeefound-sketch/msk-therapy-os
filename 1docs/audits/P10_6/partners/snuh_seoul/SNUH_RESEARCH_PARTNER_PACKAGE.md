# DRAFT — PROSPECTIVE RESEARCH COLLABORATION PROPOSAL
## Institutional Research Partner Package: Seoul National University Hospital, South Korea

### Document Metadata
- **Package ID**: `PARTNER-PKG-SNUH-v1.0-DRAFT`
- **Candidate Institution**: Seoul National University Hospital (SNUH) (Department of Radiology / Institute of Medical and Biological Engineering)
- **Jurisdiction**: Seoul, Republic of Korea (Personal Information Protection Act PIPA & Bioethics and Safety Act)
- **Status**: **PROSPECTIVE CANDIDATE ONLY — NON-BINDING DRAFT / NOT YET TRANSMITTED**
- **Date**: 2026-10-30
- **Classification**: CONFIDENTIAL RESEARCH EXPLORATION PROPOSAL

---

> [!IMPORTANT]
> **LEGAL & INSTITUTIONAL DISCLAIMER**:  
> Seoul National University Hospital (SNUH) is a prospective candidate research partner. **No formal agreement, institutional endorsement, data transfer, or clinical partnership has been executed.** This document constitutes an unapproved engineering proposal intended for prospective scientific peer dialogue and legal/ethical review. Zero emails or requests have been dispatched to SNUH personnel.

---

## 1. Research Collaboration Executive Brief
This proposal invites the Department of Radiology at Seoul National University Hospital to participate as a primary East Asian clinical imaging partner in an offline, retrospective computational anatomy validation study of **MSK-Therapy-OS**. The collaboration seeks to independently evaluate the spatial registration accuracy of computational musculoskeletal surface models against high-resolution, de-identified DICOM CT and MRI scans.

---

## 2. Proposed Study Rationale
Validation of 3D computational anatomical atlases across multi-ethnic populations is essential to ensure that geometric scaling and surface morphing algorithms perform reliably on East Asian body morphotypes. SNUH’s participation provides crucial geographic and anatomical diversity, ensuring that algorithmic accuracy is robust to morphological variation.

---

## 3. Institutional Fit & Required Expertise
SNUH is a premier tertiary academic medical center in Asia with world-class facilities in musculoskeletal imaging, computational medicine, and medical artificial intelligence. The study requires:
- Board-certified musculoskeletal radiologists experienced in Korean Society of Radiology standards.
- Clinical imaging researchers with access to retrospective PACS archives.
- Dedicated data management personnel familiar with PIPA-compliant pseudonymization protocols.

---

## 4. Cohort A/B/C Scope Allocation
SNUH is invited to contribute across three retrospective cohorts:
- **Cohort A (Abdomen/Trunk)**: $N = 15\text{–}30$ Helical CT scans ($\le 1.25\text{ mm}$ slice thickness).
- **Cohort B (Bilateral Extremities)**: $N = 15\text{–}25$ Knee MRI scans (1.5T or 3.0T, standardized wedge flexion).
- **Cohort C (Craniofacial)**: $N = 15\text{–}30$ High-resolution head/neck CT scans ($\le 1.0\text{ mm}$ slice thickness) with automated facial defacing.

---

## 5. Statistical Design Options
SNUH investigators may select between two study designs:
- **Option 1 (Primary Pilot Feasibility, Scenario 2)**: $N = 85$ total multi-center subjects (SNUH allocation: $\sim 42$ subjects), providing $>95\%$ holdout power for Craniofacial and Abdomen.
- **Option 2 (Confirmatory Subgroup Study, Scenario 3)**: $N = 115$ total multi-center subjects (SNUH allocation: $\sim 58$ subjects), ensuring $>90\%$ holdout power for all three cohorts independently.

---

## 6. Imaging Data Technical Specification
- **CT**: Helical volumetric reconstruction, $512 \times 512$ matrix, slice thickness $\le 1.25\text{ mm}$, soft tissue + bone kernel.
- **MRI**: 3D T1-weighted or Proton Density volumetric series, in-plane resolution $\le 0.5\text{ mm} \times 0.5\text{ mm}$, slice thickness $\le 2.0\text{ mm}$.
- **Storage Format**: Standard DICOM Part 10 files.

---

## 7. DICOM & De-Identification Requirements
In compliance with the Republic of Korea Personal Information Protection Act (PIPA) Article 28-2 (Pseudonymized Data) and DICOM PS 3.15 Annex E:
- Direct patient identifiers (Resident Registration Number, Name, Medical Record Number, Address, Contact details) must be completely de-identified.
- Automated optical character recognition (OCR) pixel screening must be certified to guarantee zero burned-in text.
- Cohort C cranial CT scans must be processed with automated facial defacing / skull-stripping algorithms.

---

## 8. Independent Observer Requirements
- Two independent, double-blind observers:
  - Observer A: Board-certified radiologist (Korean Board of Radiology).
  - Observer B: Senior anatomist or clinical imaging specialist.
- Observers must remain fully blinded to model predictions.
- Inter-observer discrepancies exceeding category thresholds ($3\text{ mm}$ cranial, $4\text{ mm}$ extremity, $5\text{ mm}$ abdominal) are referred to a third senior clinical adjudicator.

---

## 9. Data Governance & Security Model
- **Offline First**: All validation tooling operates locally in an air-gapped staging directory (`EXTERNAL_QUARANTINED`). Zero internet egress or external cloud syncing.
- **Custody Audit Trail**: Every data movement, tag audit, and annotation attachment is recorded in an immutable, SHA-256 hashed SQLite ledger.

---

## 10. Data Use Agreement (DUA / MTA) Review Checklist
- [ ] Retrospective, de-identified research use scope strictly delimited.
- [ ] Explicit prohibition of patient re-identification attempts.
- [ ] Data ownership retained entirely by Seoul National University Hospital.
- [ ] Research use only classification: zero commercial medical device promotion.
- [ ] Data retention, expiration, and secure cryptographic erasure provisions.

---

## 11. Ethics & Institutional Review Board (IRB) Checklist
- [ ] Submission to the Institutional Review Board of Seoul National University Hospital (SNUH IRB).
- [ ] Application for retrospective waiver of informed consent under Bioethics and Safety Act guidelines for anonymized retrospective data.
- [ ] Institutional Data Review Board (DRB) approval for pseudonymized research data export.

---

## 12. Research Responsibilities Matrix
| Responsibility Area | MSK-Therapy-OS Research Team | SNUH Research Team |
|:---|:---:|:---:|
| Computational Registration Pipeline | Lead / Maintain | Review / Audit |
| De-Identified DICOM Extraction | Advisory | Lead / Execute |
| Double-Blind Expert Annotation | Prohibited (Developer Exclusion) | Lead / Execute |
| Independent Biostatistical Audit | Coordinate with 3rd Party | Audit / Co-Author |
| Scientific Publication Drafting | Joint Author | Joint Author / Senior PI |

---

## 13. Proposed Non-Binding Collaboration Workflow
1. Technical and protocol transmittal review by SNUH Radiology leads.
2. Legal counsel review of standard bilateral DUA via SNUH Medical Research Institute.
3. SNUH IRB submission for retrospective waiver.
4. Pilot staging sandbox deployment and test batch verification ($N = 5$).
5. Main study ingestion, double-blind annotation, and holdout locking.

---

## 14. Risk & Limitation Disclosure
- Research-Use Only: MSK-Therapy-OS is an engineering research tool, NOT an approved MFDS (Ministry of Food and Drug Safety) medical device.
- Zero Puncture Depth Guidance: Invasive clinical depth guidance is permanently disabled.
- Scientific Gate G14 remains `BLOCKED_EXTERNAL_DATA` until empirical data analysis is finalized.

---

## 15. Research Transmittal Manifest (Placeholder / Verification Record)
- **Target Institutional Unit**: Seoul National University Hospital, 101 Daehak-ro, Jongno-gu, Seoul 03080, Republic of Korea.
- **Proposed Clinical Contact (Placeholder)**: `[TO BE DESIGNATED BY SNUH DEPT OF RADIOLOGY]`
- **Proposed Radiology Lead (Placeholder)**: `[TO BE DESIGNATED BY SNUH MUSCULOSKELETAL SECTION]`
- **Research Governance Office (Public)**: SNUH Biomedical Research Institute, Seoul, Korea.

---

## 16. Draft Introduction Email (Unsent Template)
```text
Subject: Prospective Academic Collaboration: Computational Musculoskeletal Anatomy Validation

Dear Musculoskeletal Imaging & Radiology Faculty at Seoul National University Hospital,

We are writing to explore the potential for an academic research collaboration between your department 
and the MSK-Therapy-OS computational anatomy project.

We have developed an offline, open-source computational atlas pipeline for 3D anatomical surface registration. 
To rigorously establish its spatial accuracy across diverse patient populations, we have drafted a comprehensive 
Statistical Analysis Plan (SAP) and clinical imaging protocol (Cohorts A, B, and C) evaluating registration residuals 
against retrospective CT and MRI ground truth.

We would welcome an exploratory, non-binding technical dialogue with your faculty to discuss whether this study 
aligns with your academic research priorities. All imaging data would remain strictly de-identified, on-premises, 
and governed under bilateral DUA and SNUH IRB oversight.

A complete draft protocol package is available for your inspection.

Sincerely,
[Principal Investigator / Computational Anatomy Research Team]
MSK-Therapy-OS Research Project
```

---

## 17. Outstanding Decisions & Information Requests
1. Review of SNUH Data Review Board (DRB) requirements for de-identified DICOM research transfer.
2. Confirmation of standardized knee flexion wedge protocols routinely used in SNUH musculoskeletal MRI suites.
3. Designation of SNUH faculty collaborator for musculoskeletal annotation quality control.
