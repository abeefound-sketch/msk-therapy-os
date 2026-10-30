# DRAFT — PROSPECTIVE RESEARCH COLLABORATION PROPOSAL
## Institutional Research Partner Package: Massachusetts General Hospital / Harvard Medical School Research Ecosystem, USA

### Document Metadata
- **Package ID**: `PARTNER-PKG-MGH-HARVARD-v1.0-DRAFT`
- **Candidate Institution**: Massachusetts General Hospital (MGH) / Mass General Brigham (Department of Radiology & Division of Musculoskeletal Imaging)
- **Jurisdiction**: Boston, Massachusetts, United States (US HIPAA Privacy Rule 45 CFR § 164.514 & Common Rule 45 CFR 46)
- **Status**: **PROSPECTIVE CANDIDATE ONLY — NON-BINDING DRAFT / NOT YET TRANSMITTED**
- **Date**: 2026-10-30
- **Classification**: CONFIDENTIAL RESEARCH EXPLORATION PROPOSAL

---

> [!IMPORTANT]
> **LEGAL & INSTITUTIONAL DISCLAIMER**:  
> Massachusetts General Hospital / Mass General Brigham is a prospective candidate research partner. **No formal agreement, institutional endorsement, data transfer, or clinical partnership has been executed.** This document constitutes an unapproved engineering proposal intended for prospective scientific peer dialogue and legal/ethical review. Zero emails or requests have been dispatched to MGH/Harvard personnel.

---

## 1. Research Collaboration Executive Brief
This proposal invites the Division of Musculoskeletal Imaging and Intervention at Massachusetts General Hospital to participate as a primary North American clinical imaging partner in an offline, retrospective computational anatomy validation study of **MSK-Therapy-OS**. The collaboration seeks to independently evaluate the spatial registration accuracy of computational musculoskeletal surface models against high-resolution, de-identified DICOM CT and MRI scans.

---

## 2. Proposed Study Rationale
Computational anatomical models in medical navigation and physical therapy planning often exhibit localized registration bias across diverse patient somatotypes. Independent validation against high-resolution radiological ground truth is required to quantify surface accuracy, determine landmark error confidence intervals, and ensure statistical reproducibility under rigorous statistical oversight.

---

## 3. Institutional Fit & Required Expertise
MGH / Mass General Brigham is an internationally recognized leader in radiological science, quantitative imaging biomarkers, and musculoskeletal anatomy. The study requires:
- Board-certified musculoskeletal radiologists with expertise in advanced joint and soft-tissue MRI/CT.
- Clinical research coordinators familiar with Mass General Brigham IRB submission processes.
- Imaging research core staff proficient in HIPAA Safe Harbor and Expert Determination de-identification.

---

## 4. Cohort A/B/C Scope Allocation
MGH is invited to contribute across three retrospective cohorts:
- **Cohort A (Abdomen/Trunk)**: $N = 15\text{–}30$ Helical CT scans ($\le 1.25\text{ mm}$ slice thickness).
- **Cohort B (Bilateral Extremities)**: $N = 15\text{–}25$ Knee MRI scans (1.5T or 3.0T, standardized wedge flexion).
- **Cohort C (Craniofacial)**: $N = 15\text{–}30$ High-resolution head/neck CT scans ($\le 1.0\text{ mm}$ slice thickness) with automated facial defacing.

---

## 5. Statistical Design Options
MGH investigators may select between two study designs:
- **Option 1 (Primary Pilot Feasibility, Scenario 2)**: $N = 85$ total multi-center subjects (MGH allocation: $\sim 42$ subjects), providing $>95\%$ holdout power for Craniofacial and Abdomen.
- **Option 2 (Confirmatory Subgroup Study, Scenario 3)**: $N = 115$ total multi-center subjects (MGH allocation: $\sim 58$ subjects), ensuring $>90\%$ holdout power for all three cohorts independently.

---

## 6. Imaging Data Technical Specification
- **CT**: Helical volumetric reconstruction, $512 \times 512$ matrix, slice thickness $\le 1.25\text{ mm}$, soft tissue + bone kernel.
- **MRI**: 3D T1-weighted or Proton Density volumetric series, in-plane resolution $\le 0.5\text{ mm} \times 0.5\text{ mm}$, slice thickness $\le 2.0\text{ mm}$.
- **Storage Format**: Standard DICOM Part 10 files.

---

## 7. DICOM & De-Identification Requirements
In compliance with US HIPAA Privacy Rule (45 CFR § 164.514(b) Safe Harbor Method) and DICOM PS 3.15 Annex E:
- All 18 direct identifiers (Name, MRN, Dates of service, Telephone, Geocodes) must be permanently redacted before export.
- Automated optical character recognition (OCR) pixel screening must be certified to guarantee zero burned-in annotations.
- Cohort C cranial CT scans must be processed with automated facial defacing / skull-stripping algorithms.

---

## 8. Independent Observer Requirements
- Two independent, double-blind observers:
  - Observer A: Board-certified musculoskeletal radiologist (ABR certified).
  - Observer B: Senior clinical anatomist or musculoskeletal fellow.
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
- [ ] Data ownership retained entirely by Massachusetts General Hospital / Mass General Brigham.
- [ ] Research use only classification: zero commercial medical device promotion.
- [ ] Data retention, expiration, and secure cryptographic erasure provisions.

---

## 11. Ethics & Institutional Review Board (IRB) Checklist
- [ ] Submission to Mass General Brigham Human Research Committee (MGB IRB).
- [ ] Application for retrospective waiver of informed consent (45 CFR 46.116(f)) for minimal-risk de-identified imaging research.
- [ ] Radiation Safety Committee consultation (confirming zero prospective radiation exposure).

---

## 12. Research Responsibilities Matrix
| Responsibility Area | MSK-Therapy-OS Research Team | MGH Research Team |
|:---|:---:|:---:|
| Computational Registration Pipeline | Lead / Maintain | Review / Audit |
| De-Identified DICOM Extraction | Advisory | Lead / Execute |
| Double-Blind Expert Annotation | Prohibited (Developer Exclusion) | Lead / Execute |
| Independent Biostatistical Audit | Coordinate with 3rd Party | Audit / Co-Author |
| Scientific Publication Drafting | Joint Author | Joint Author / Senior PI |

---

## 13. Proposed Non-Binding Collaboration Workflow
1. Technical and protocol transmittal review by MGH Musculoskeletal Radiology leads.
2. Legal counsel review of standard bilateral DUA via Mass General Brigham Innovation Office.
3. Mass General Brigham IRB submission for retrospective waiver.
4. Pilot staging sandbox deployment and test batch verification ($N = 5$).
5. Main study ingestion, double-blind annotation, and holdout locking.

---

## 14. Risk & Limitation Disclosure
- Research-Use Only: MSK-Therapy-OS is an engineering research tool, NOT an FDA-cleared 510(k) medical device.
- Zero Puncture Depth Guidance: Invasive clinical depth guidance is permanently disabled.
- Scientific Gate G14 remains `BLOCKED_EXTERNAL_DATA` until empirical data analysis is finalized.

---

## 15. Research Transmittal Manifest (Placeholder / Verification Record)
- **Target Institutional Unit**: Massachusetts General Hospital, 55 Fruit Street, Boston, MA 02114, USA.
- **Proposed Clinical Contact (Placeholder)**: `[TO BE DESIGNATED BY MGH DEPT OF RADIOLOGY]`
- **Proposed Radiology Lead (Placeholder)**: `[TO BE DESIGNATED BY MGH DIVISION OF MUSCULOSKELETAL IMAGING]`
- **Institutional Research Office (Public)**: Mass General Brigham Clinical Research Office, Boston, MA.

---

## 16. Draft Introduction Email (Unsent Template)
```text
Subject: Prospective Academic Collaboration: Computational Musculoskeletal Anatomy Validation

Dear Musculoskeletal Imaging & Radiology Faculty at Massachusetts General Hospital,

We are writing to explore the potential for an academic research collaboration between your imaging 
research group and the MSK-Therapy-OS computational anatomy project.

We have developed an offline, open-source computational atlas pipeline for 3D anatomical surface registration. 
To rigorously establish its spatial accuracy, we have drafted a comprehensive Statistical Analysis Plan (SAP) 
and clinical imaging protocol (Cohorts A, B, and C) evaluating registration residuals against retrospective 
CT and MRI ground truth.

We would welcome an exploratory, non-binding technical dialogue with your faculty to discuss whether this 
study aligns with your academic research priorities. All imaging data would remain strictly de-identified, 
on-premises, and governed under bilateral DUA and MGB IRB oversight.

A complete draft protocol package is available for your inspection.

Sincerely,
[Principal Investigator / Computational Anatomy Research Team]
MSK-Therapy-OS Research Project
```

---

## 17. Outstanding Decisions & Information Requests
1. Determination of preferred DICOM de-identification tooling utilized by MGH Imaging Research Core (e.g., CTP / RSNA Clinical Trial Processor).
2. Clarification of MGB IRB review timeline for retrospective de-identified imaging waivers.
3. Designation of MGH faculty collaborator for musculoskeletal annotation oversight.
