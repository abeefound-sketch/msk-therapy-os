# P10.4B INSTITUTIONAL PARTNER ONBOARDING & PILOT PACKAGE — DRAFT

> [!WARNING]
> **DOCUMENT STATUS: EXTERNAL PARTNER REVIEW DRAFT**  
> *This documentation package is prepared for prospective academic hospitals, radiology departments, and research ethics committees. No institutional partnership, clinical ethics approval, or data transfer agreement has been executed. All sections are subject to institutional review and bilateral modification.*

**System Version:** `v2.1.0-local-rc3`  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Date:** 2026-10-30  
**Gate B403 Verdict:** **PASS (PARTNER PACKAGE READY FOR SUBMISSION)**

---

## 1. Research Project Executive Summary
MSK-Therapy-OS is an offline-first computational anatomy platform designed to assist musculoskeletal therapy practitioners, acupuncturists, and medical educators in visualizing 3D anatomical structures and standardized traditional meridian trajectories. This pilot research protocol seeks to rigorously evaluate the spatial concordance of computationally inferred acupoints relative to high-resolution cross-sectional radiology (CT and MRI).

---

## 2. Scientific Objectives and Limitations
- **Objective:** Evaluate Euclidean registration and surface localization errors against expert-annotated anatomical landmarks.
- **Strict Clinical Limitations:**
  - The software is strictly designated for **RESEARCH AND EDUCATIONAL USE ONLY**.
  - Does NOT diagnose clinical pathologies.
  - Does NOT prescribe medications or therapeutic interventions.
  - Does NOT recommend invasive needle puncture depths (`clinical_depth_guidance_allowed: False`).
  - Anatomical landmark registration does **NOT** prove physiological meridian existence or clinical acupuncture efficacy.

---

## 3. Cohort A/B/C Pilot Protocol
- **Cohort A (Craniofacial & Cervical Spine):** $\ge 30$ subjects, Axial CT $\le 1.25\text{ mm}$ slice thickness. Landmarks: Nasion, Inion, Glabella, EOP, C7 spinous process, Mastoid tips.
- **Cohort B (Knee & Lower Extremity):** $\ge 25$ subjects, High-Resolution Proton Density / T1 MRI $\le 3.0\text{ mm}$. Landmarks: Tibial tuberosity, Patella inferior pole, Femoral epicondyles, Fibular head.
- **Cohort C (Forearm & Wrist Complex):** $\ge 30$ subjects, CT or 3T MRI $\le 2.0\text{ mm}$. Landmarks: Radial styloid, Ulnar styloid, Biceps distal tendon, Humeral epicondyles.

---

## 4. Data Dictionary and Acquisition Requirements
- **File Format:** Standard DICOM Part 10 (`.dcm`).
- **Modality Tags:** CT `(0008,0060) == 'CT'` or MR `(0008,0060) == 'MR'`.
- **Coordinate Space:** LPS (Left-Posterior-Superior) Cartesian frame derived from `(0020,0032)` Image Position (Patient) and `(0020,0037)` Image Orientation (Patient).
- **Pixel Spacing:** In-plane resolution $\le 0.8\text{ mm}\times 0.8\text{ mm}$.

---

## 5. DICOM De-Identification & Biometric Privacy Checklist
Conforms to HIPAA 45 CFR § 164.514(b) Safe Harbor Profile and DICOM PS 3.15 Annex E:
- [ ] Patient Name `(0010,0010)` -> Cleaned or replaced with Pseudonym UUID.
- [ ] Patient ID `(0010,0020)` -> Replaced with Study Subject ID.
- [ ] Patient Birth Date `(0010,0030)` -> Suppressed or coarsened to year only if age $<89$.
- [ ] Accession Number `(0008,0050)` -> Suppressed.
- [ ] Institution Name `(0008,0080)` -> Coarsened or pseudonymized.
- [ ] Referring Physician `(0008,0090)` -> Suppressed.
- [ ] Private Tags `(gggg, eeee)` with odd group numbers -> Stripped completely unless certified free of PHI.
- [ ] Facial Reconstruction Rejection: Craniofacial volumetric CT scans must undergo defacing/skull-stripping if surface-rendered soft-tissue facial recognition is possible.

---

## 6. Data Use Agreement (DUA / MTA) Checklist
- [ ] Reciprocal non-disclosure terms.
- [ ] Strict prohibition on re-identification attempts.
- [ ] Explicit ownership statement: Source medical center retains all underlying intellectual property in raw imaging.
- [ ] Data retention limits: 3 years post-study completion, followed by certified digital shredding.
- [ ] Jurisdiction and regulatory governance (HIPAA, GDPR, or applicable national laws).

---

## 7. Institutional Review Board (IRB) Submission Checklist
- [ ] Protocol narrative describing retrospective de-identified imaging study.
- [ ] Request for Waiver of Informed Consent under 45 CFR 46.116(f) (minimal risk research using existing de-identified data).
- [ ] Principal Investigator and Co-Investigator CVs.
- [ ] Data security architecture description (offline storage, zero cloud transmission).

---

## 8. Observer & Reviewer Qualification Requirements
- **Primary Radiologist Observer:** Board-certified radiologist or computational anatomist with $\ge 3$ years experience in cross-sectional musculoskeletal imaging.
- **Independent Adjudicator:** Senior academic clinician with no commercial affiliation with the software project.

---

## 9. Conflict-of-Interest (COI) Declaration Template

```text
======================= COI DECLARATION (DRAFT) =======================
Reviewer Name: ____________________________________________________
Institutional Affiliation: _________________________________________
Study / Dataset ID: _______________________________________________

[ ] I DECLARE that I have NO commercial, financial, or personal 
    affiliation with the developers of MSK-Therapy-OS, and hold no 
    equity or intellectual property interests in the software.

[ ] I DECLARE the following potential conflict of interest:
    _________________________________________________________________
Signature: __________________________ Date: _______________________
=======================================================================
```

---

## 10. Dataset Transfer and Retention SOP
1. **Pre-Transfer De-identification:** Executed on hospital premises inside clinical firewall.
2. **Transfer Media:** Encrypted physical drive (AES-256) or isolated SFTP point-to-point tunnel.
3. **Receipt Verification:** Intake engine computes canonical SHA-256 manifest immediately upon arrival.
4. **Air-Gapped Processing:** Workstation operates strictly offline without internet connectivity.

---

## 11. Incident Response & Authorization Revocation SOP
If a data breach, PHI leakage, or ethics withdrawal occurs:
1. Institutional official sends signed revocation notification.
2. Governance engine executes `MultiSiteGovernanceManager.revoke_approval()`.
3. Affected dataset transitions immediately to `REVOKED` state; access blocked.
4. Secure digital eradication of local volume within 48 hours.

---

## 12. Pilot Responsibilities and Acceptance Matrix

| Responsibility Domain | Hospital / University Partner | MSK-Therapy-OS Engineering Team |
|---|---|---|
| **Ethics Approval** | Prepares and submits local IRB application | Supplies technical protocol & architecture specs |
| **Image De-identification** | Executes PS 3.15 de-identification on-site | Provides preflight validation scripts |
| **Landmark Annotation** | Expert radiologists place reference landmarks | Supplies coordinate schema and intake API |
| **Evaluation Execution** | Blinded review of holdout metrics | Executes automated pipeline and calculations |
| **Regulatory Sign-off** | Evaluates compliance with clinical standards | Supplies audited evidence packages |
