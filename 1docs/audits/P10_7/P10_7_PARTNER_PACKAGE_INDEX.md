# MSK-THERAPY-OS — P10.7 INSTITUTIONAL PARTNER PACKAGE INDEX

**Milestone:** P10.7 — Scientific Protocol Lock, External Review Submission Readiness & Research Partnership Handoff  
**Lead Operations Architect:** Clinical Research Operations Engineer & Governance Auditor  
**Date:** 2026-10-30  
**Overall Status:** `PROSPECTIVE / NOT CONTACTED / NO COLLABORATION ESTABLISHED`  

---

## 1. Master Partner Submission Inventory

This index registers the three prospective research partnership packages prepared for external submission review. Each package contains all 16 mandatory operational sections, tailored legal/privacy frameworks, and un-contacted prospective status disclosures.

| Institution Identifier | Legal Name | Jurisdiction & Regulatory Law | Primary Cohort Scope | Package Location | Verified Status | Blockers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INST-CHARITE-BERLIN** | Charité – Universitätsmedizin Berlin | Germany / EU (GDPR Art. 89, BDSG § 27) | Cohort A (Cranial CT) & Cohort B (Knee MRI) | [`partners/charite_berlin/CHARITE_P10_7_PARTNER_PACKAGE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_7/partners/charite_berlin/CHARITE_P10_7_PARTNER_PACKAGE.md) | `PROSPECTIVE / UNCONTACTED` | 8 / 8 Pending |
| **INST-MGH-HARVARD** | Massachusetts General Hospital / Harvard | USA (HIPAA Safe Harbor, Common Rule 45 CFR § 46) | Cohort B (Knee MRI) & Cohort C (Upper Extremity) | [`partners/mgh_harvard/MGH_HARVARD_P10_7_PARTNER_PACKAGE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_7/partners/mgh_harvard/MGH_HARVARD_P10_7_PARTNER_PACKAGE.md) | `PROSPECTIVE / UNCONTACTED` | 8 / 8 Pending |
| **INST-SNUH-SEOUL** | Seoul National University Hospital | South Korea (PIPA Art. 28-2, Bioethics Act) | Cohort A (Cranial CT) & Cohort B (Knee MRI) | [`partners/snuh_seoul/SNUH_P10_7_PARTNER_PACKAGE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_7/partners/snuh_seoul/SNUH_P10_7_PARTNER_PACKAGE.md) | `PROSPECTIVE / UNCONTACTED` | 8 / 8 Pending |

---

## 2. Institutional Jurisdictional Comparison Matrix

| Governance Dimension | Charité Berlin (Germany) | MGH / Harvard (USA) | SNUH Seoul (South Korea) |
| :--- | :--- | :--- | :--- |
| **Primary Data Law** | EU GDPR + German BDSG | HIPAA Privacy Rule + Common Rule | PIPA (Personal Information Protection Act) |
| **Secondary Research Exemption** | BDSG § 27 (Scientific Research) | 45 CFR § 46.104(d)(4) (NHSR or Expedited) | PIPA Article 28-2 (Pseudonymous Processing) |
| **De-Identification Requirement** | Full pseudonymization + Cranial defacing | HIPAA Safe Harbor 18-element removal | Direct identifier removal + Cranial defacing |
| **Bilateral Agreement** | EU Standard Contractual Clauses / DUA | Mass General Brigham Bilateral DUA | SNUH MRCC Research Collaboration Agreement |
| **Local Compute Target** | Air-gapped Linux Docker within campus | MGB ERIS Linux research cluster or terminal | SNUH Biomedical Research Institute terminal |
| **Institutional Contact** | Unresolved (Pending human coordinator) | Unresolved (Pending human coordinator) | Unresolved (Pending human coordinator) |

---

## 3. Strict Operating Invariants for External Engagement

1. **Zero Automated Communications:** The software and coding agent have NOT sent and CANNOT send automated emails or transmissions.
2. **Authorized Human Outbound Communication Only:** Any contact must be initiated by an authorized human research coordinator.
3. **No Representation of Endorsement:** No document or UI element may claim institutional endorsement or partnership until a bilateral agreement is formally executed.

**Gate P704 Status:** PASS
