# MSK-THERAPY-OS — PROSPECTIVE RESEARCH COLLABORATION PACKAGE
## Partner Institution: Massachusetts General Hospital / Harvard Medical School (USA)
### Document Version: v1.0-RC-P10.7

> [!WARNING]
> **COLLABORATION STATUS: `PROSPECTIVE / NOT CONTACTED / NO COLLABORATION ESTABLISHED`**  
> This package is a draft proposal prepared solely for prospective academic review. **Massachusetts General Hospital, Mass General Brigham, and Harvard Medical School have NOT been contacted, have NOT endorsed this software, and have NOT authorized any research activity or data transfer.** No communication may be transmitted without explicit written authorization from the human principal investigator.

---

## 1. One-Page Project Introduction
MSK-Therapy-OS is an offline, research-grade computational musculoskeletal anatomy and 3D registration platform. Developed with an engineering-first methodology, the platform maps osseous structures, soft tissue boundaries, and traditional meridian geometry onto patient-specific volumetric coordinate systems.

The platform has undergone rigorous synthetic regression testing (757 automated tests, 100% PASS), satisfying all internal engineering criteria. Because internal verification is epistemologically distinct from empirical clinical validity, MSK-Therapy-OS seeks prospective collaboration with academic medical centers to evaluate landmark registration accuracy on retrospective de-identified imaging under an executed Data Use Agreement (DUA) and Institutional Review Board (IRB) determination.

---

## 2. Research Rationale
Modern integrative medicine and acupuncture research frequently investigate anatomical correlates of traditional acupoints (e.g., neurovascular bundles, intermuscular fascial planes). However, spatial localization software lacks rigorous empirical benchmarking against radiological ground truth. This collaboration provides an objective, reproducible metric of 3D registration accuracy on real clinical CT and MRI examinations.

---

## 3. Nonclinical Software Demonstration Scope
- **FDA Regulatory Boundary:** Strictly non-clinical, non-diagnostic investigational research software (`ENGINEERING_RESEARCH_ONLY`). Not cleared or approved under FDA 510(k), De Novo, or PMA pathways.
- **Safety Invariant:** Zero autonomous diagnosis, zero clinical treatment prescription, zero invasive needle puncture depth guidance (`clinical_depth_guidance_allowed: False`).
- **Demonstration Scope:** Offline visual multiplanar inspection, automated 3D landmark error calculation, and reproducible statistical report generation.

---

## 4. Research Protocol Draft
Governed by protocol freeze candidate [`P10_7_PROTOCOL_FREEZE_CANDIDATE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_7/P10_7_PROTOCOL_FREEZE_CANDIDATE.md):
- **Cohort A:** Head & Cervical Spine CT ($N=30$)
- **Cohort B:** Knee & Lower Extremity MRI ($N=25$)
- **Cohort C:** Upper Extremity CT/MRI ($N=30$)
- **Holdout Partition:** Sealed $30\%$ holdout subset with unblinded analysis conducted only after prediction registration lock.

---

## 5. Statistical Design Scenarios
Evaluated under four conditional planning scenarios:
1. **Scenario 1: Feasibility Pilot ($N=45$):** Min subgroup power $58.7\%$ ($z$).
2. **Scenario 2: Primary Clinical Pilot ($N=85$ - Recommended):** Min subgroup power $81.6\%$ ($z$) / $\approx 74.2\%$ ($t$).
3. **Scenario 3: Confirmatory Study ($N=115$):** Min subgroup power $88.9\%$ ($z$) / $\approx 84.1\%$ ($t$).
4. **Scenario 4: Multi-Site Study ($N=150$):** Min subgroup power $97.4\%$ ($z$).

---

## 6. Imaging & Annotation Data Specifications
- **DICOM Protocols:** High-resolution volumetric CT ($\le 1.25\text{ mm}$ slice thickness) and 1.5T/3T MRI ($\le 3.0\text{ mm}$ slice thickness).
- **Coordinate Reference:** DICOM LPS coordinate system in millimeters.
- **Independent Reading:** Dual independent annotation by board-certified radiologists with consensus tie-breaking for inter-reader discrepancies $>2.0\text{ mm}$ (CT) or $>2.5\text{ mm}$ (MRI).

---

## 7. Privacy & De-Identification Requirements (US HIPAA & Common Rule)
- **Legal Standards:** US Health Insurance Portability and Accountability Act (HIPAA) Privacy Rule (45 CFR § 164.514(b)(2) Safe Harbor de-identification method).
- **Identifiers Scrubbed:** All 18 Protected Health Information (PHI) identifiers removed prior to study intake.
- **Common Rule Compliance:** Designed for expedited review or Not Human Subjects Research (NHSR) determination under 45 CFR § 46.104(d)(4) (secondary research use of identifiable private information or biospecimens).

---

## 8. Institutional DUA / IRB Review Checklist
- [ ] Mass General Brigham IRB submission for retrospective de-identified imaging secondary use determination.
- [ ] Bilateral Data Use Agreement (DUA) executed through Partners HealthCare / MGB Research Management.
- [ ] HIPAA De-Identification Certification signed by MGB institutional data manager.
- [ ] Verification of local air-gapped processing node within MGB research intranet.

---

## 9. Proposed Collaboration Responsibilities
| Stakeholder | Responsibilities |
| :--- | :--- |
| **MGH Research Team** | Case retrieval from PACS research archive, DICOM de-identification, dual radiologist annotation. |
| **MSK-Therapy-OS Team** | Provision of air-gapped software package, algorithmic calibration, statistical analysis execution. |
| **Joint Committee** | Holdout unblinding oversight, interpretation of findings, joint manuscript drafting. |

---

## 10. Independent Observer Requirements
Annotating radiologists must hold an active Massachusetts medical license, ABR board certification, and fellowship training in musculoskeletal radiology, with zero financial relationship to MSK-Therapy-OS.

---

## 11. Data Custody & Security Architecture
- **On-Premise Deployment:** Executed on an isolated, non-networked workstation or within the Mass General Brigham Enterprise Research Infrastructure & Services (ERIS) secure compute cluster.
- **Zero Ingestion Risk:** The software contains zero outbound networking libraries; telemetry and auto-updates are disabled.
- **Local Persistence:** All logs, model outputs, and metrics reside in local encrypted SQLite volumes.

---

## 12. Risk Disclosures
1. Software outputs represent experimental computational geometry.
2. The software does not measure electrical conductivity, acupuncture channel impedance, or clinical efficacy.
3. Not cleared for medical diagnostic or therapeutic decision-making.

---

## 13. Research Timeline Dependencies
1. **Months 1–2:** IRB determination and DUA execution.
2. **Months 3–4:** PACS query, automated de-identification, and radiologist landmark marking ($N=85$).
3. **Month 5:** Blinded algorithm execution, holdout unblinding, statistical modeling.
4. **Month 6:** Final report and joint academic dissemination.

---

## 14. Questions for Prospective MGH / Harvard Collaborators
1. Does the MGB IRB consider retrospective de-identified and defaced imaging secondary research to qualify for NHSR (Not Human Subjects Research) status?
2. Does MGB prefer data processing within an isolated ERIS Linux VM or on a dedicated physical research terminal?
3. What is the institutional turnaround timeline for bilateral DUA execution through MGB Research Management?

---

## 15. Draft Outreach Email
```text
Subject: Academic Research Inquiry: Independent Radiological Validation of 3D Computational Musculoskeletal Anatomy Atlas

Dear Dr. [Radiology / Integrative Medicine Research Director Name],

I am writing to inquire about potential academic collaboration with Massachusetts General Hospital and the Harvard Medical School research community regarding an investigator-initiated validation study of a 3D computational anatomy atlas.

The MSK-Therapy-OS project has engineered an open-source, air-gapped computational anatomy platform that projects musculoskeletal landmarks and traditional meridian geometry onto patient-specific CT and MRI coordinate systems. The codebase has completed comprehensive synthetic verification (757 automated tests, 100% pass) and has been structured specifically for independent empirical evaluation.

We are proposing an academic retrospective study to quantify spatial registration accuracy against de-identified clinical CT and MRI scans annotated by independent musculoskeletal radiologists. The system operates strictly offline within institutional infrastructure with zero cloud data transmission, in full alignment with HIPAA Safe Harbor and 45 CFR § 46 requirements.

Our complete Protocol Freeze Candidate and Institutional Submission Package is available for your inspection:
- Protocol Version: v1.0-RC-P10.7
- Proposed Sample Size: Primary Pilot N=85 across Cranial, Extremity, and Abdominal cohorts
- Classification: Strictly non-clinical research software (zero diagnostic or therapeutic guidance)

If this research methodology is of interest to your group, we would be pleased to coordinate a brief introductory call with your research team.

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
5. `MGH_HARVARD_P10_7_PARTNER_PACKAGE.md` (This document)
