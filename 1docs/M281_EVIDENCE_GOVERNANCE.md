# MSK-Therapy-OS | Milestone M2.8.1 Evidence Governance Audit Report

**Document ID:** `M281-GOV-001`  
**Milestone:** `M2.8.1 Acceptance Hardening`  
**Author:** Medical Data Architect, Evidence Ledger Specialist & Systems Auditor  
**Date:** October 22, 2026  
**Status:** ACCEPTED / STRICT COMPLIANCE ENFORCED  

---

## 1. Executive Summary

Milestone M2.8.1 hardens the clinical evidence governance framework governing 3D point localization in MSK-Therapy-OS. The system enforces strict architectural separation between **geometric surface registration** (which verifies that a coordinate mathematically intersects the BodyParts3D skin mesh) and **clinical anatomical review** (which requires human expert verification backed by recognized literature and explicit localization uncertainty tolerances).

All governance rules are verified via unit tests ([`tests/test_governance_reconciliation.py`](file:///D:/5Projects/msk-therapy-os/tests/test_governance_reconciliation.py) and [`tests/test_security_and_governance.py`](file:///D:/5Projects/msk-therapy-os/tests/test_security_and_governance.py)) and enforced automatically at the API and database levels.

---

## 2. Governance Tier Hierarchy & Enforcement Rules

```
+---------------------------+-----------------------------------+-----------------------------------------+
| Tier / Status             | Definition                        | Required Proof / Verification Criteria  |
+---------------------------+-----------------------------------+-----------------------------------------+
| VERIFIED_ANATOMICAL_ANCHOR| Classical WHO/National landmark   | Pre-baked canonical dataset coordinates |
| SURFACE_REGISTERED_FJ2810 | Algorithmic surface projection    | Raycast intersection with FJ2810 mesh   |
| GEOMETRY_VERIFIED         | User point snapped to 3D surface  | Valid 3D bounds and face index attached |
| ANATOMY_REVIEWED          | Human clinical expert approval    | Human reviewer + Credentials + Evidence |
| UNCERTAIN_POSTURE_OFFSET  | Posture-dependent discrepancy     | Flagged offset (>10mm) requiring review |
| UNVERIFIED                | Raw or uncalibrated input         | Provisional draft state                 |
+---------------------------+-----------------------------------+-----------------------------------------+
```

### 2.1 Rule 1: Clinical Credential Enforcement for `ANATOMY_REVIEWED`

Claims of `ANATOMY_REVIEWED` status cannot be self-certified without verified professional credentials.
* **Prohibited Reviewer Terms:** Any generic, automated, or algorithmic identity (e.g., `AI`, `System`, `Automated`, `Unknown`, `Bot`, `ChatGPT`, `Algorithm`, `None`) is immediately rejected with `ValueError`.
* **Credential Verification:** The reviewer string must contain at least one credential recognized by medical and physical medicine licensing boards:
  ```python
  ALLOWED_CLINICAL_CREDENTIALS = {
      "MD", "DO", "LAC", "PT", "DPT", "DC", "PHD", "MBBS", "FACP", "ND",
      "L.AC.", "D.P.T.", "M.D.", "D.O."
  }
  ```
* **Enforcement:** [`msk_therapy_os/points.py:validate_governance_tier()`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/points.py#L942) extracts tokenized alphabetic components and verifies intersection against `ALLOWED_CLINICAL_CREDENTIALS`.

### 2.2 Rule 2: Evidence Catalog & Standard Citation Requirement

* `ANATOMY_REVIEWED` points must supply an `evidence_id` that resolves to a registered entry in the relational `evidence_catalog` table (e.g., `EVID-A-001`, `EVID-A-002`, `EVID-G-001`) or a recognized national/international standard citation (`WHO-2008`, `GB/T 12346-2006`, `GB/T 12346-2021`, `BODYPARTS3D 4.0`).
* Points referencing unregistered or arbitrary string IDs are rejected with `ValueError`.

### 2.3 Rule 3: Physically Bounded Uncertainty Radius ($0.0 < r \le 25.0\text{ mm}$)

* Palpation and landmarking are subject to physiological anatomical variation.
* Clinical review claims must declare a non-zero, physically realistic localization uncertainty radius $r$:
  $$0.0\text{ mm} < r \le 25.0\text{ mm}$$
* Negative values, zero, or values exceeding 25.0 mm (which would span multiple dermatomes or anatomical compartments) are rejected.

### 2.4 Rule 4: Prohibition of `OFFICIAL_STANDARD` on User Custom Points

* The review status `OFFICIAL_STANDARD` is legally and clinically reserved for published national and international standards (WHO WPRO 2008 and GB/T 12346-2021).
* If an authored custom point in `lib_custom_user` attempts to set `review_status = 'OFFICIAL_STANDARD'`, the system rejects the operation, requiring `PENDING_EXPERT_REVIEW`, `PROVISIONAL`, or `EXPERT_VERIFIED`.

---

## 3. Database Schema & Audit Ledger Integration

Governance metadata is persisted across all point operations:

```sql
-- custom_points & reference_point_overrides schema additions
evidence_id TEXT REFERENCES evidence_catalog(evidence_id),
reviewer TEXT,
verification_method TEXT DEFAULT 'SURFACE_RAYCAST_INTERSECTION',
uncertainty_radius_mm REAL DEFAULT 0.0
```

Every point mutation (creation, nudging, relocation, override, or deletion) generates an immutable entry in `point_revisions` and is exposed via `/api/governance/evidence-ledger`:

```json
{
  "revision_id": 18,
  "point_id": "PT-MYO-NX-8335",
  "change_type": "CREATE",
  "author": "Clinical Educator",
  "reviewer": "Dr. Sarah Chen, MD",
  "verification_method": "SURFACE_RAYCAST_INTERSECTION",
  "uncertainty_radius_mm": 4.5,
  "evidence_id": "EVID-A-001",
  "evidence_title": "Open Anatomy Atlas: Web-based 3D Human Anatomy Viewer",
  "evidence_tier": 2,
  "notes": "Verified against C2-C3 occipital junction surface"
}
```

---

## 4. Integrity Check Audit Outcome

Running `run_database_integrity_check()` via `/api/governance/status` verifies:
* **SQLite PRAGMA integrity_check:** `ok`
* **SQLite PRAGMA foreign_key_check:** 0 violations
* **Reference Dataset Integrity:** Canonical `acupuncture_3d.json` SHA-256 matches `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df`
* **Governance Compliance:** 100% compliant; 0 unqualified reviewed points.
