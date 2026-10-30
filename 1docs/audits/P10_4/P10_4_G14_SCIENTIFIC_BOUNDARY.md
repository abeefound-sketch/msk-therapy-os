# P10.4 SCIENTIFIC BOUNDARY & GATE G14 FAIL-CLOSED SPECIFICATION

**Milestone:** P10.4 — Independent Release Certification, Institutional Pilot Integration & Evidence Reproducibility  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Lead Auditor / Role:** Clinical Safety Auditor & Scientific Integrity Lead  
**Audit Date:** 2026-10-30  
**Gate P409 Verdict:** **PASS (STRICTLY FAIL-CLOSED)**  
**Gate G14 State:** **BLOCKED_EXTERNAL_DATA**

---

## 1. Executive Summary

Milestone P10.4 reaffirms and cryptographically seals the scientific and clinical boundaries of MSK-Therapy-OS. The system is engineered as an offline computational research platform. It is strictly barred from making clinical efficacy claims, autonomous diagnostic assertions, or needle puncture recommendations. Scientific Gate G14 remains strictly fail-closed as `BLOCKED_EXTERNAL_DATA`.

---

## 2. Immutable Scientific Invariants

The software architecture strictly enforces five foundational epistemological invariants:

```text
1. SYNTHETIC_TEST_SUCCESS != EMPIRICAL_VALIDATION
   Synthetic rehearsals and mathematical unit tests prove software robustness;
   they do NOT prove anatomical accuracy on real human populations.

2. TECHNICAL_CALIBRATION != INDEPENDENT_GROUND_TRUTH
   Internal geometric calibration to standard Chinese/WHO proportional cun models
   is an engineering reference, NOT independent empirical validation.

3. ANATOMICAL_LANDMARK_VALIDATION != CLINICAL_VALIDATION
   Even if an acupoint's physical surface location is empirically confirmed on imaging,
   this does NOT prove clinical efficacy, therapeutic action, or physiological mechanism.

4. ENGINEERING_READY != CLINICALLY_VALIDATED
   The software is engineered and ready to ingest multi-institutional research data,
   but cannot be deployed for clinical care without external regulatory clearance.

5. CT/MRI IMAGING != DIRECT ACUPOINT GROUND TRUTH
   Cross-sectional radiology images physical bones, muscles, and fascial boundaries.
   Acupuncture points are computationally inferred onto this physical substrate.
```

---

## 3. Mandatory Safety Restrictions

The following safeguards are hardcoded and non-configurable:

- **Needle Puncture Depth Guidance:** Strictly prohibited (`clinical_depth_guidance_allowed: False`). The system outputs 2D/3D surface landmarks only and will never advise on invasive penetration depth.
- **Autonomous Diagnosis:** Strictly prohibited (`autonomous_diagnosis_allowed: False`).
- **Treatment Prescription & Dosage:** Strictly prohibited. No electrical stimulation milliamperes or pulse frequency recommendations are generated.
- **Supervisory Hard-Stop:** SOAP note approvals and clinical triage referrals require verified human clinical supervisor credentials.

---

## 4. Prerequisites for Future Empirical Pilot Unlocking

Gate G14 cannot transition from `BLOCKED_EXTERNAL_DATA` to `UNLOCKED` until every item in the following multi-institutional checklist is satisfied with verifiable external evidence:

```text
┌────────────────────────────────────────────────────────────────────────┐
│             EXTERNAL EMPIRICAL VALIDATION PREREQUISITE CHECKLIST       │
├────────────────────────────────────────────────────────────────────────┤
│ [ ] 1. Prespecified Statistical Analysis Plan (SAP) formally registered│
│ [ ] 2. Executed Data Use Agreements (DUAs) with ≥2 academic hospitals  │
│ [ ] 3. Formal Institutional Review Board (IRB) ethics clearance        │
│ [ ] 4. Ingestion of ≥85 real patient cross-sectional scans (CT/MRI)    │
│ [ ] 5. Independent expert radiological annotations with COI screening  │
│ [ ] 6. Locked 30% holdout partition evaluated without data leakage     │
│ [ ] 7. Prespecified thresholds achieved (RMSE ≤ 4.0mm, P95 ≤ 6.0mm)    │
│ [ ] 8. Dual administrative sign-off by credentialed hospital officers  │
│ [ ] 9. Regulatory pre-market clearance for clinical decision support   │
└────────────────────────────────────────────────────────────────────────┘
```

Until all 9 prerequisites are completed, Gate G14 will remain fail-closed across all endpoints, UI badges, and SQLite tables.

---

## 5. Verification Verdict

Gate P409 is certified as **PASS** based on unbroken fail-closed boundary enforcement across the entire codebase. Gate G14 is formally registered as **BLOCKED_EXTERNAL_DATA**.
