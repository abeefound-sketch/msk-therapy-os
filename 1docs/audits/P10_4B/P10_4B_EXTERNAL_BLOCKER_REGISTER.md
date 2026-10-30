# P10.4B ACTIONABLE EXTERNAL DEPENDENCY & BLOCKER REGISTER

**Milestone:** P10.4B — Institutional Pilot Activation, External Evidence Preparation & Scientific Readiness  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**System Version:** `v2.1.0-local-rc3`  
**Lead Auditor / Role:** Clinical Research Operations Architect & Governance Auditor  
**Audit Date:** 2026-10-30  
**Gate B408 Sub-Evaluation:** **PASS (ALL DEPENDENCIES EXPLICITLY TRACKED)**

---

## 1. Executive Summary

Milestone P10.4B creates an exhaustive, actionable register of all external organizational, legal, ethics, and radiological dependencies required before the MSK-Therapy-OS platform can proceed from `ENGINEERING_RESEARCH_ONLY` to empirical clinical validation.

```text
SCIENTIFIC BOUNDARY STATUS:
  G14                             = BLOCKED_EXTERNAL_DATA
  EXTERNAL_EMPIRICAL_VALIDATION   = NOT_PERFORMED
  CLINICAL_VALIDATION             = NOT_ESTABLISHED
  RELEASE_SCOPE                   = ENGINEERING_RESEARCH_ONLY
  clinical_depth_guidance_allowed = False
```

---

## 2. Actionable External Blocker Register

| Blocker ID | Responsible External Role / Entity | Required Document or Approval | Acceptance Criteria | Current Status | Evidence Location | Active Blocker Description | Next Authorized Engineering Action |
|---|---|---|---|---|---|---|---|
| **DEP-01** | **Independent Academic Biostatistician** | Signed Statistical Analysis Plan (SAP) Approval Form | Reviewer certifies sample size ($N \ge 85$), cluster design effect ($DE \approx 4.85$), and holdout power ($>99\%$). | **BLOCKED_EXTERNAL** | [`1docs/audits/P10_4B/P10_4B_PRESPECIFIED_SAP_DRAFT.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_PRESPECIFIED_SAP_DRAFT.md) | Requires external university biostatistician review. | Transmit draft SAP package to candidate academic statistician. |
| **DEP-02** | **Hospital Legal / Technology Transfer Office** | Executed Data Use Agreement (DUA / MTA) | Bilateral agreement governing retrospective de-identified imaging transfer, non-reidentification, and 3-year retention. | **BLOCKED_EXTERNAL** | [`1docs/audits/P10_4B/P10_4B_INSTITUTIONAL_PARTNER_PACKAGE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_INSTITUTIONAL_PARTNER_PACKAGE.md) | No external hospital DUA executed to date. | Deliver DUA discussion checklist to prospective hospital research office. |
| **DEP-03** | **Institutional Review Board (IRB / Ethics Committee)** | Formal Ethics Clearance or Waiver Determination | Written IRB protocol approval or formal 45 CFR 46.116(f) waiver of informed consent. | **BLOCKED_EXTERNAL** | [`1docs/audits/P10_4B/P10_4B_INSTITUTIONAL_PARTNER_PACKAGE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_INSTITUTIONAL_PARTNER_PACKAGE.md) | No clinical ethics submission approved yet. | Supply partner PI with technical narrative and offline safety specs. |
| **DEP-04** | **Hospital Radiology PACS Custodian** | De-identified In-Vivo Patient CT/MRI Series ($N \ge 85$) | High-resolution volumetric series ($\le 1.25\text{ mm}$ for CT, $\le 3.0\text{ mm}$ for MRI) with PS 3.15 de-identification certificate. | **BLOCKED_EXTERNAL** | [`msk_therapy_os/research_contracts.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/research_contracts.py) | No real patient scan series exist in repository. | Await execution of DEP-02 and DEP-03. |
| **DEP-05** | **Board-Certified Independent Radiologist** | Multi-Tier Landmark Annotations with Signed COI | Expert annotations for Cohorts A, B, and C in LPS coordinates; signed non-conflict attestation. | **BLOCKED_EXTERNAL** | [`msk_therapy_os/reviewer_workflow.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/reviewer_workflow.py) | No external clinical annotations registered. | Provide radiologist onboarding manual and coordinate schema. |
| **DEP-06** | **Institutional Clinical Research Board** | Dual Administrative Sign-Off | Cryptographically verified sign-off by two distinct credentialed administrators in SQLite. | **BLOCKED_EXTERNAL** | [`msk_therapy_os/multi_site_governance.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/multi_site_governance.py) | Blocked pending DEP-04 and DEP-05. | Await annotation adjudication. |
| **DEP-07** | **Independent Software Verification Auditor** | Pre-Evaluation Holdout Lock Verification | Verification that holdout partition ($30\%$) is tamper-sealed prior to empirical error evaluation. | **BLOCKED_EXTERNAL** | [`msk_therapy_os/anatomical_validation.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py) | Holdout partition awaiting real patient data. | Seal holdout hash upon ingestion. |
| **DEP-08** | **Regulatory Affairs / Medical Device Body** | Pre-Market Evaluation / Determination | Official determination regarding clinical decision support vs. research-only software. | **BLOCKED_EXTERNAL** | [`1docs/audits/P10_4B/P10_4B_G14_SCIENTIFIC_BOUNDARY.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4/P10_4_G14_SCIENTIFIC_BOUNDARY.md) | Premarket clearance not established. | Maintain research-only boundary. |

---

## 3. Engineering Invariant Regarding External Blockers

No engineering agent, developer, or internal script has the authority to transition any of the 8 external dependencies from `BLOCKED_EXTERNAL` to `PASS` without verified, cryptographically sealed documentation from an authorized external party.

Gate B408 is certified as **PASS** based on complete, actionable dependency tracking.
