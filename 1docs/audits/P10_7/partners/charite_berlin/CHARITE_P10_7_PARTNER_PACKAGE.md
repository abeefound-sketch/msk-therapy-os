# MSK-THERAPY-OS — PROSPECTIVE RESEARCH COLLABORATION PACKAGE
## Partner Institution: Charité – Universitätsmedizin Berlin (Germany / European Union)
### Document Version: v1.0-RC-P10.7

> [!WARNING]
> **COLLABORATION STATUS: `PROSPECTIVE / NOT CONTACTED / NO COLLABORATION ESTABLISHED`**  
> This package is a draft proposal prepared solely for prospective academic review. **Charité – Universitätsmedizin Berlin has NOT been contacted, has NOT endorsed this software, and has NOT authorized any research activity or data transfer.** No communication may be transmitted without explicit written authorization from the human principal investigator.

---

## 1. One-Page Project Introduction
MSK-Therapy-OS is an offline, research-grade computational anatomy and 3D musculoskeletal atlas platform. It integrates kinematic joint modeling, tissue-layer stratification (cutis, subcutis, fascia, periosteum), and traditional meridian acupoint geometric projections onto standard DICOM imaging coordinate systems.

The software has completed extensive synthetic verification (757 automated tests, 100% PASS). However, it adheres to the invariant that **synthetic test success does not constitute empirical validation**. To transition to empirical research validity, MSK-Therapy-OS seeks prospective collaboration with academic anatomical and radiology institutes to evaluate landmark registration accuracy against retrospective de-identified imaging under an executed Data Use Agreement (DUA) and Ethics Committee clearance.

---

## 2. Research Rationale
While computational acupuncture atlases have expanded theoretically, independent quantitative empirical validation using radiological ground truth remains nonexistent. Most literature relies on qualitative drawings or 2D diagrams. This prospective project aims to measure the exact 3D spatial discrepancy between traditional geometric localization rules and real human musculoskeletal anatomy visible on high-resolution clinical CT and MRI scans.

---

## 3. Nonclinical Software Demonstration Scope
- **Classification:** Strictly `ENGINEERING_RESEARCH_ONLY`.
- **Prohibitions:** Autonomous diagnosis, clinical therapy recommendation, and invasive needle puncture depth guidance are strictly prohibited (`clinical_depth_guidance_allowed: False`).
- **Demonstration Capability:** Visualizing 3D multiplanar cross-sections, landmark projection, skin surface conformity, and calculating spatial deviation metrics on synthetic or verified de-identified scans.

---

## 4. Research Protocol Draft
The research protocol follows the versioned protocol freeze candidate specification [`P10_7_PROTOCOL_FREEZE_CANDIDATE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_7/P10_7_PROTOCOL_FREEZE_CANDIDATE.md):
- **Cohort A:** Head & Neck CT (Evaluation of cranial midline and parasagittal landmarks).
- **Cohort B:** Knee Joint & Extremity MRI (Evaluation of peri-articular landmarks).
- **Cohort C:** Upper Extremity CT/MRI (Evaluation of distal forearm landmarks).
- **Holdout Partition:** Strict $30\%$ holdout sealed prior to registration prediction lock.

---

## 5. Statistical Design Scenarios
Charité review is invited across four prespecified sizing scenarios:
1. **Feasibility Pilot ($N=45$):** 15 subjects/cohort; min subgroup power $58.7\%$ (Workflow and DICOM transfer test).
2. **Primary Clinical Pilot ($N=85$ - Recommended):** 30 A / 25 B / 30 C; min subgroup power $81.6\%$ ($z$) / $\approx 74.2\%$ ($t$).
3. **Confirmatory Multi-Center Study ($N=115$):** 40 A / 35 B / 40 C; min subgroup power $88.9\%$ ($z$).
4. **Expanded Multi-Center Study ($N=150$):** 50 A / 50 B / 50 C; min subgroup power $97.4\%$ ($z$).

---

## 6. Imaging & Annotation Data Specifications
- **Modality Requirements:** Volumetric axial CT ($\le 1.25\text{ mm}$ slice thickness) and 1.5T/3T MRI ($\le 3.0\text{ mm}$ slice thickness).
- **Format:** Uncompressed standard DICOM Part 10 files.
- **Annotation Requirements:** 3D coordinates $(X, Y, Z)$ marked by two independent board-certified radiologists using Charité's standard PACS/MPR viewer.

---

## 7. Privacy & De-Identification Requirements (EU GDPR & German BDSG)
- **Legal Basis:** EU General Data Protection Regulation (GDPR) Article 6(1)(e), Article 9(2)(j), and German Federal Data Protection Act (BDSG § 27).
- **De-Identification:** Full DICOM PS 3.15 Annex E anonymization; removal of all direct patient identifiers (Name, DOB, Patient ID, Address, Accession Number).
- **Defacing:** High-resolution cranial CT scans must undergo facial surface defacing prior to transmission to prevent 3D photographic reconstruction.

---

## 8. Institutional DUA / Ethikkommission Review Checklist
- [ ] Ethikkommission der Charité formal review application or determination of exemption for retrospective de-identified secondary data.
- [ ] Bilateral Data Use Agreement (DUA) between Charité legal counsel and project sponsor.
- [ ] Data Protection Impact Assessment (DPIA) signed by Charité Data Protection Officer (Datenschutzbeauftragter).
- [ ] Verification of local air-gapped processing node within Charité campus intranet.

---

## 9. Proposed Collaboration Responsibilities
| Stakeholder | Responsibilities |
| :--- | :--- |
| **Charité Clinical Team** | Retrospective case selection, de-identification, PACS extraction, dual independent radiologist landmark marking. |
| **MSK-Therapy-OS Team** | Provision of air-gapped software Docker container, local technical calibration support, automated statistical metric calculation. |
| **Joint Committee** | Independent holdout unblinding, statistical review, joint co-authorship of peer-reviewed publication. |

---

## 10. Independent Observer Requirements
Radiologists must have active German Facharzt für Radiologie certification or equivalent musculoskeletal imaging fellowship training, with no financial or consulting ties to MSK-Therapy-OS.

---

## 11. Data Custody & Security Architecture
- **Air-Gapped Processing:** The software executes on an on-premise workstation or local server within Charité's network.
- **Zero Cloud Egress:** No telemetry, analytics, or image slices are transmitted externally.
- **Audit Logging:** Every registration run and metric calculation is recorded in an immutable local SQLite audit database.

---

## 12. Risk Disclosures
1. **Computational Tool Only:** MSK-Therapy-OS is not a medical device and is not CE-marked.
2. **No Clinical Guidance:** Software output must never be used to guide patient procedures, injections, or acupuncture needle insertions.
3. **Research Boundary:** Results serve solely to evaluate geometric modeling accuracy.

---

## 13. Research Timeline Dependencies
1. **Stage 1 (Month 1–2):** DUA execution and Ethikkommission clearance.
2. **Stage 2 (Month 3):** Imaging selection, de-identification, and facial defacing ($N=85$).
3. **Stage 3 (Month 4):** Dual independent radiologist annotation and consensus adjudication.
4. **Stage 4 (Month 5):** Air-gapped algorithm execution, sealed holdout unblinding, and statistical metric compilation.
5. **Stage 5 (Month 6):** Manuscript preparation for peer-reviewed journal submission.

---

## 14. Questions for Prospective Charité Collaborators
1. Does the Ethikkommission der Charité consider retrospective, fully de-identified and defaced cranial CT scans exempt from formal patient consent under BDSG § 27?
2. Does Charité prefer on-premise execution via a sealed Linux Docker container or a dedicated physical research laptop?
3. Which musculoskeletal MRI sequences (T1 vs Proton Density Fat-Suppressed) are routinely preferred for knee tuberosity and epicondyle localization?

---

## 15. Draft Outreach Email
```text
Subject: Prospective Academic Research Collaboration: Quantitative Radiological Validation of 3D Musculoskeletal Landmark Atlas

Dear Prof. Dr. [Radiology / Anatomy Chair Name],

I am writing to explore potential academic research collaboration with Charité – Universitätsmedizin Berlin regarding a quantitative validation study of an offline 3D computational musculoskeletal anatomy atlas.

The MSK-Therapy-OS project has established an open-source, air-gapped software platform designed to register canonical anatomical landmarks and traditional acupoint projections onto patient-specific CT and MRI coordinate systems. The software has completed exhaustive synthetic verification (757 tests, 100% pass) and is ready for independent empirical evaluation.

We are proposing an academic, investigator-initiated study to evaluate registration accuracy against retrospective de-identified CT and MRI scans annotated by independent radiologists. The software is designed to execute entirely on-premise within your institutional firewall with zero cloud data transmission, under full compliance with EU GDPR Article 89 and German BDSG regulations.

We have compiled a complete Protocol Freeze Candidate and Institutional Submission Package, available for your review:
- Protocol Version: v1.0-RC-P10.7
- Proposed Sample Size: Primary Pilot N=85 (30 Cranial CT / 25 Knee MRI / 30 Forearm CT-MRI)
- Boundary: Strictly non-clinical research (zero diagnostic or needle-depth claims)

If this research aligns with your department's interests, we would welcome the opportunity to schedule a brief introductory video conference with your research team.

Sincerely,

[Authorized Human Research Coordinator Name]
MSK-Therapy-OS Research Initiative
[Institutional Email / Contact Details]
```

---

## 16. Document Transmittal Manifest
1. `P10_7_PROTOCOL_FREEZE_CANDIDATE.md` (Manifest SHA-256: `7a1da2a0f959ea7ab5125c37f8e996b5abec318e9d3978c3150f65a6944f3a31`)
2. `P10_7_STATISTICAL_REPRODUCIBILITY.md`
3. `P10_7_INDEPENDENT_REVIEW_PACKAGE.md`
4. `reproduce_p10_7_review_statistics.py`
5. `CHARITE_P10_7_PARTNER_PACKAGE.md` (This document)
