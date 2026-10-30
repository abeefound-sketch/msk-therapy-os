# P10.4 MULTI-INSTITUTIONAL GOVERNANCE & ACCESS CONTROL REPORT

**Milestone:** P10.4 — Independent Release Certification, Institutional Pilot Integration & Evidence Reproducibility  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Governance Engine:** [`msk_therapy_os/multi_site_governance.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/multi_site_governance.py)  
**Lead Auditor / Role:** Security Auditor & Clinical Research Data Governance Specialist  
**Audit Date:** 2026-10-30  
**Gate P404 Verdict:** **PASS**

---

## 1. Executive Summary

Milestone P10.4 implements an enterprise-grade multi-institutional governance framework backed by SQLite. The framework enforces cryptographically authenticated administrative roles, strict site-level data isolation, mandatory conflict-of-interest (COI) declarations for independent adjudicators, and tamper-evident approval revocations.

---

## 2. Multi-Site Architecture & Schema

The governance subsystem establishes four dedicated SQLite tables with strict foreign key constraints and validation rules:

1. `multi_site_registry`:
   - Tracks participating research institutions (`site_id`, `institution_name`, `country`, `regulatory_framework`, `data_custodian_id`, `status`).
   - Allowed statuses: `ACTIVE`, `SUSPENDED`, `DECOMMISSIONED`.
2. `multi_site_admins`:
   - Stores credentialed administrators bound to specific sites.
   - Enforces SHA-256 salted password hashes (`sha256$salt$hash`).
   - Rejects unauthenticated strings or plain booleans.
3. `multi_site_coi_declarations`:
   - Records reviewer conflict-of-interest disclosures for each study/dataset.
   - Any declaration with `has_conflict == 1` immediately disqualifies the reviewer from adjudication.
4. `multi_site_dataset_approvals`:
   - Enforces dual administrative sign-off (`primary_admin_id` and distinct `secondary_cosigner_id`).
   - Calculates cryptographic `approval_hash`.
   - Tracks `effective_date_iso` and `expiration_date_iso`.
   - Supports explicit `REVOKED` state with audited rationale.

---

## 3. Security Invariants & Threat Mitigation

### 3.1 Cross-Site Isolation Enforcement
In multi-institutional pilots, an administrator from Hospital Alpha must NEVER be able to authorize, modify, or inspect datasets belonging to Hospital Beta.

In [`MultiSiteGovernanceManager.authorize_dataset_dual_admin`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/multi_site_governance.py), the site ID of both signers is checked against the target dataset's site ID:
```python
if p_admin.site_id != site_id:
    raise CrossSiteAccessViolationError(
        f"Cross-site access violation: Primary admin {primary_admin_id} belongs to site {p_admin.site_id}, cannot authorize site {site_id}"
    )
```

Negative test `test_multi_site_cross_site_isolation_enforced` verified that attempting to sign off across site boundaries raises `CrossSiteAccessViolationError`.

### 3.2 Dual Sign-Off & Self-Cosigning Prohibition
To eliminate single-point compromise and insider threat, the governance engine mandates two distinct administrators:
```python
if primary_admin_id == secondary_admin_id:
    raise GovernanceAuthorizationError("Curator self-cosigning prohibited: Secondary admin must be distinct")
```

### 3.3 Adjudicator Conflict-of-Interest Screening
Before an observer or reviewer's annotations can be incorporated into the empirical validation pipeline, their eligibility is queried via `check_reviewer_eligibility()`. If a financial, commercial, or institutional conflict is recorded, the reviewer is disqualified.

### 3.4 Approval Expiration & Revocation Propagation
All authorizations have strict calendar boundaries. If `current_date > expiration_date`, `verify_approval_validity()` returns `False`. If a Data Use Agreement is suspended or revoked by an institutional official, the approval record status transitions to `REVOKED`, immediately blocking dataset downstream access.

---

## 4. Verification Verdict

All governance controls were verified against negative test fixtures in `tests/test_p10_4_adversarial_and_governance.py` with zero security bypasses. Gate P404 is certified as **PASS**.
