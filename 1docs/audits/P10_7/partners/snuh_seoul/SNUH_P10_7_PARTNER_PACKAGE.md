# MSK-THERAPY-OS — PROSPECTIVE RESEARCH COLLABORATION PACKAGE
## Partner Institution: Seoul National University Hospital (South Korea)
### Document Version: v1.0-RC-P10.7

> [!WARNING]
> **COLLABORATION STATUS: `PROSPECTIVE / NOT CONTACTED / NO COLLABORATION ESTABLISHED`**  
> This package is a draft proposal prepared solely for prospective academic review. **Seoul National University Hospital (SNUH) and Seoul National University College of Medicine have NOT been contacted, have NOT endorsed this software, and have NOT authorized any research activity or data transfer.** No communication may be transmitted without explicit written authorization from the human principal investigator.

---

## 1. One-Page Project Introduction
MSK-Therapy-OS is an offline, research-grade computational musculoskeletal anatomy and 3D registration platform. The software models musculoskeletal bone structures, soft tissue boundaries, and WHO standard acupuncture point coordinates on patient-specific radiological volumes.

The software has completed exhaustive synthetic regression testing (757 automated tests, 100% PASS). To establish empirical validity beyond synthetic verification, MSK-Therapy-OS seeks prospective collaboration with Seoul National University Hospital to assess 3D registration precision on retrospective de-identified clinical CT and MRI examinations under an executed institutional agreement and Institutional Review Board (IRB) clearance.

---

## 2. Research Rationale
South Korea is a global leader in integrating clinical musculoskeletal imaging and evidence-based traditional medicine. While meridian charts have been standardized internationally (WHO Western Pacific Region standard), 3D spatial alignment to patient-specific radiological anatomy has never been quantitatively validated across diverse body morphometries. This study provides an objective empirical foundation for computational meridian modeling.

---

## 3. Nonclinical Software Demonstration Scope
- **Regulatory Status:** Strictly research-use-only investigational software (`ENGINEERING_RESEARCH_ONLY`). Not approved or certified as a medical device by the Korean Ministry of Food and Drug Safety (MFDS).
- **Prohibited Functions:** Autonomous diagnosis, therapeutic clinical prescription, and needle puncture depth guidance are strictly prohibited (`clinical_depth_guidance_allowed: False`).
- **Demonstration Scope:** Offline 3D multiplanar visualization, automated landmark registration error computation, and reproducible statistical report generation.

---

## 4. Research Protocol Draft
Governed by protocol freeze candidate [`P10_7_PROTOCOL_FREEZE_CANDIDATE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_7/P10_7_PROTOCOL_FREEZE_CANDIDATE.md):
- **Cohort A:** Head & Cervical Spine CT ($N=30$)
- **Cohort B:** Knee Joint & Extremity MRI ($N=25$)
- **Cohort C:** Upper Extremity CT/MRI ($N=30$)
- **Holdout Partition:** Strict $30\%$ holdout subset sealed cryptographically until algorithm predictions are locked.

---

## 5. Statistical Design Scenarios
Four prespecified scenarios evaluated:
1. **Feasibility Pilot ($N=45$):** Min subgroup power $58.7\%$ ($z$).
2. **Primary Clinical Pilot ($N=85$ - Recommended):** Min subgroup power $81.6\%$ ($z$) / $\approx 74.2\%$ ($t$).
3. **Confirmatory Multi-Center Study ($N=115$):** Min subgroup power $88.9\%$ ($z$) / $\approx 84.1\%$ ($t$).
4. **Expanded Multi-Center Study ($N=150$):** Min subgroup power $97.4\%$ ($z$).

---

## 6. Imaging & Annotation Data Specifications
- **Modality Protocols:** High-resolution volumetric CT ($\le 1.25\text{ mm}$ slice thickness) and 1.5T/3T MRI ($\le 3.0\text{ mm}$ slice thickness).
- **Coordinate System:** DICOM LPS coordinates in millimeters.
- **Dual Reader Consensus:** Independent annotation by two certified radiologists with a third senior radiologist adjudicating discrepancies $>2.0\text{ mm}$ (CT) or $>2.5\text{ mm}$ (MRI).

---

## 7. Privacy & De-Identification Requirements (South Korea PIPA & Bioethics Act)
- **Legal Compliance:** Personal Information Protection Act (PIPA Article 28-2 pseudonymous data processing for scientific research) and the Bioethics and Safety Act.
- **Pseudonymization:** Complete removal of direct identifiers (Resident Registration Number, Name, Hospital Patient ID, Address, Contact Information).
- **Facial Defacing:** Volumetric cranial CT series must be defaced prior to export.

---

## 8. Institutional DUA / SNUH IRB Review Checklist
- [ ] SNUH Institutional Review Board (IRB) submission for retrospective pseudonymous data research approval or exemption.
- [ ] Bilateral Data Transfer / Research Collaboration Agreement executed through SNUH Medical Research Collaboration Center (MRCC).
- [ ] Verification of pseudonymization protocol by SNUH Information Security Office.
- [ ] Deployment of local air-gapped compute environment at SNUH Biomedical Research Institute.

---

## 9. Proposed Collaboration Responsibilities
| Stakeholder | Responsibilities |
| :--- | :--- |
| **SNUH Research Team** | Case identification from PACS archive, pseudonymization, dual independent radiologist annotation. |
| **MSK-Therapy-OS Team** | Provision of air-gapped software package, calibration support, automated metric calculation. |
| **Joint Committee** | Sealed holdout unblinding oversight, biostatistical analysis, joint manuscript co-authorship. |

---

## 10. Independent Observer Requirements
Participating radiologists must hold Korean Board of Radiology certification with musculoskeletal subspecialty training and have zero commercial affiliation with MSK-Therapy-OS.

---

## 11. Data Custody & Security Architecture
- **Local Air-Gapped Compute:** Software operates on an isolated terminal within the SNUH Biomedical Research Institute.
- **Zero Ingestion Risk:** Zero cloud communication, telemetry, or external network transmission.
- **Encrypted Local Storage:** All output matrices and logs stored in encrypted local SQLite files.

---

## 12. Risk Disclosures
1. Software outputs represent experimental 3D geometry and do not constitute clinical findings.
2. Does not assess clinical therapeutic effects, meridian energetics, or patient health outcomes.
3. Not cleared for medical diagnostic or interventional use.

---

## 13. Research Timeline Dependencies
1. **Months 1–2:** SNUH IRB review and bilateral research agreement execution.
2. **Months 3–4:** PACS data extraction, pseudonymization, and radiologist landmark annotation ($N=85$).
3. **Month 5:** Blinded algorithmic prediction, holdout unblinding, statistical evaluation.
4. **Month 6:** Preparation of academic report for international peer-reviewed publication.

---

## 14. Questions for Prospective SNUH Collaborators
1. Under PIPA Article 28-2, does the SNUH IRB require explicit informed consent for retrospective pseudonymous CT/MRI secondary use in non-commercial academic research?
2. Does the SNUH Biomedical Research Institute have a standardized air-gapped Linux research server environment for offline container deployment?
3. What is the institutional timeline for review through the SNUH Medical Research Collaboration Center (MRCC)?

---

## 15. Draft Outreach Email
```text
Subject: Academic Research Collaboration Inquiry: Independent Empirical Validation of 3D Musculoskeletal Anatomical Registration

Dear Prof. Dr. [Radiology Chair / Biomedical Research Institute Director Name],

I am writing to explore potential academic research collaboration with Seoul National University Hospital regarding an investigator-initiated empirical validation study of a 3D computational musculoskeletal anatomy atlas.

The MSK-Therapy-OS initiative has developed an open-source, air-gapped computational anatomy platform that projects musculoskeletal landmarks and WHO standard meridian geometries onto patient-specific CT and MRI coordinate systems. The software has completed comprehensive synthetic verification (757 automated tests, 100% pass) and has been structured for independent radiological evaluation.

We are proposing an academic retrospective study to evaluate 3D registration precision against de-identified clinical CT and MRI scans annotated by independent musculoskeletal radiologists. The platform operates strictly offline within your institutional environment with zero cloud data transmission, under full compliance with South Korea's Personal Information Protection Act (PIPA Article 28-2) and the Bioethics and Safety Act.

Our complete Protocol Freeze Candidate and Institutional Submission Package is available for your review:
- Protocol Version: v1.0-RC-P10.7
- Proposed Sample Size: Primary Pilot N=85 across Cranial CT, Knee MRI, and Forearm CT/MRI
- Scope: Strictly non-clinical research software (zero diagnostic or therapeutic guidance)

If this research aligns with your department's scientific priorities, we would welcome the opportunity to schedule a brief introductory virtual meeting with your research team.

Sincerely,

[Authorized Human Research Coordinator Name]
MSK-Therapy-OS Research Initiative
[Institutional Email / Contact Information]
```

---

## 16. Document Transmittal Manifest
1. `P10_7_PROTOCOL_FREEZE_CANDIDATE.md` (Manifest SHA-256: `7a1da2a0f959ea7ab5125c37f8e996b5abec318e9d3978c3150f65a6944f3a31`)
2. `P10_7_STATISTICAL_REPRODUCIBILITY.md`
3. `P10_7_INDEPENDENT_REVIEW_PACKAGE.md`
4. `reproduce_p10_7_review_statistics.py`
5. `SNUH_P10_7_PARTNER_PACKAGE.md` (This document)
