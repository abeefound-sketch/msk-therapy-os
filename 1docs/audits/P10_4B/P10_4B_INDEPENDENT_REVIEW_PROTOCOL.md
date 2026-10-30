# P10.4B OFFLINE INDEPENDENT REVIEW PROTOCOL & WORKFLOW SPECIFICATION

**Milestone:** P10.4B — Institutional Pilot Activation, External Evidence Preparation & Scientific Readiness  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Workflow Engine:** [`msk_therapy_os/reviewer_workflow.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/reviewer_workflow.py)  
**Lead Auditor / Role:** Independent Software QA Lead & Clinical Research Operations Architect  
**Audit Date:** 2026-10-30  
**Gate B406 Verdict:** **PASS (WORKFLOW VERIFIED / EXTERNAL REVIEW PENDING)**

---

## 1. Executive Summary

Milestone P10.4B establishes a formalized, offline-first independent review workflow. This enables external adjudicators (independent biostatisticians, board-certified radiologists, and clinical ethics officers) to inspect evidence packages, verify cryptographic manifests, and record binding review determinations without developer interference or holdout data disclosure.

---

## 2. Reviewer Roles & Checklist Specifications

| Reviewer Role | Mandated Inspection Scope | Specific Verification Checkpoints |
|---|---|---|
| **External Biostatistician** | Statistical methodology, power, and sample allocation | - Verification of cluster bootstrap resampling ($B=1,000$).<br/>- Review of ICC design effect adjustments.<br/>- Multiplicity control (Bonferroni / Benjamini-Hochberg FDR).<br/>- Holdout sample size adequacy ($N_{\text{eff}} \ge 20$). |
| **Independent Radiologist** | DICOM de-identification and landmark accuracy | - DICOM PS 3.15 Safe Harbor conformance.<br/>- Defacing / facial reconstruction suppression.<br/>- LPS coordinate system compliance.<br/>- Physical osseous landmark accuracy. |
| **Clinical Ethics Auditor** | DUA, IRB, and regulatory compliance | - Valid, unexpired IRB approval and DUA.<br/>- Verified non-conflict of interest declarations.<br/>- Absence of real patient identifiers (PHI).<br/>- Strict enforcement of research-use boundary. |

---

## 3. Anti-Impersonation & Conflict-of-Interest Hard Guards

To guarantee independence:

1. **Developer / Coding Agent Exclusion:**
   [`IndependentReviewEngine`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/reviewer_workflow.py) inspects the reviewer identity. If `is_developer_or_internal_agent == True` or the reviewer ID matches internal agent patterns, the session is rejected immediately:
   ```python
   if reviewer.is_developer_or_internal_agent:
       raise ReviewerImpersonationError(
           f"Independence violation: Developer or internal agent identity '{reviewer.reviewer_id}' "
           f"is strictly barred from executing independent external review."
       )
   ```
2. **Mandatory Non-Conflict Declaration:**
   Reviewers must explicitly confirm `has_conflict == False` and provide a signed statement of independence before accessing the review dossier.

---

## 4. Privacy-Preserving Holdout Inspection

External reviewers can verify the integrity of the 30% locked holdout partition without exposing raw coordinates to potential leakage:
- Reviewers inspect the aggregate RMSE, Mean Error, and 95% Bootstrap CI.
- Reviewers verify the SHA-256 partition manifest hash.
- Individual holdout Cartesian coordinates remain redacted in reviewer export packages.

---

## 5. Review Record Sealing & Tamper Evidence

Upon completing their checklist, the reviewer issues an official verdict (`APPROVED`, `REVISION_REQUESTED`, or `REJECTED`). The review record is sealed with a deterministic SHA-256 digest (`IndependentReviewRecord.seal()`), providing tamper-evident proof of review completion.

---

## 6. Verification Verdict

The external review architecture is implemented, tested against adversarial impersonation attempts in `test_reviewer_workflow_developer_exclusion`, and ready for deployment. Gate B406 is certified as **PASS**.
