# Milestone M2.8: Atlas Data Governance Specification & Protocol

**Document ID:** M2.8-GOV-003  
**Author:** Principal Software Architect, Senior Clinical Governance Specialist  
**Project:** MSK-Therapy-OS (`integration/m2.7-m2.8`)  
**Target Hardware:** Windows x64, Intel Core i7-5600U, 8GB RAM, Intel HD Graphics 5500  
**Status:** Approved & Enforced  

---

## 1. Governance Principles & Core Rules

1. **Immutable Ground Truth:** Canonical anatomical meshes (BodyParts3D 4.0 `FJ2810`) and standard point datasets (`acupuncture_3d.json`) are cryptographically sealed. In-place modification of reference files on disk is strictly prohibited.
2. **Separation of Geometry and Clinical Accuracy:**
   - Mathematical intersection with the 3D skin mesh confirms **geometric placement only** (`GEOMETRY_VERIFIED` or `SURFACE_REGISTERED_FJ2810`).
   - Geometric surface registration **does NOT constitute anatomical or clinical validation**.
3. **Qualified Human Review Requirement:**
   - Any point claiming `ANATOMY_REVIEWED` **must** record a named, qualified human clinician or anatomist (MD, LAc, PT, Anatomist).
   - Automated scripts, algorithms, or "AI" are rejected by schema constraints from claiming clinical anatomical review.
4. **Isolated Versioned Auditing:**
   - All practitioner coordinate modifications, relocations, or custom points are persisted separately in local SQLite tables (`reference_point_overrides`, `custom_points`, `point_revisions`).
   - Every mutation produces a non-destructive audit record detailing revision index, previous state, new state, author, reviewer, method, and uncertainty radius.
5. **Patient Data Isolation:**
   - Therapy module tables (`cases`, `visits`, `intakes`, `soap_notes`, `therapy_sessions`) have zero foreign keys connecting to the Atlas point registry or research workbench.
   - The application functions 100% offline without remote network calls or telemetry exfiltration.

---

## 2. Cryptographic Reference Integrity

Every boot sequence and automated audit evaluates the cryptographic hash of the canonical dataset:

```python
CANONICAL_REFERENCE_CHECKSUMS = {
    "acupuncture_3d.json": "47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df"
}
```

If the SHA-256 digest of `acupuncture_3d.json` diverges from this hash:
- The governance audit status immediately changes to `FAIL`.
- The system logs a `CORRUPTED_OR_MODIFIED` alert.
- The reference override layer refuses to apply overrides to unverified base data.

---

## 3. Governance Status Hierarchy

```
┌────────────────────────────────────────────────────────┐
│                   Governance Statuses                  │
├──────────────────────────┬─────────────────────────────┤
│ Status Code              │ Clinical Definition         │
├──────────────────────────┼─────────────────────────────┤
│ VERIFIED_ANATOMICAL_ANCHOR│ Calibrated against physical │
│                          │ BodyParts3D bony/muscular   │
│                          │ ground truth (e.g. C7 apex) │
├──────────────────────────┼─────────────────────────────┤
│ ANATOMY_REVIEWED         │ Validated by a named human  │
│                          │ expert against evidence     │
│                          │ catalog (EVID-A-xxx)        │
├──────────────────────────┼─────────────────────────────┤
│ GEOMETRY_VERIFIED        │ Verified 3D surface raycast │
│                          │ hit on FJ2810 (dist ≤ 0.5mm)│
├──────────────────────────┼─────────────────────────────┤
│ SURFACE_REGISTERED_FJ2810│ Pre-baked surface projection│
│                          │ on BodyParts3D skin mesh    │
├──────────────────────────┼─────────────────────────────┤
│ UNCERTAIN_POSTURE_OFFSET │ Discrepancy due to donor    │
│                          │ posture (supine vs standing)│
├──────────────────────────┼─────────────────────────────┤
│ UNVERIFIED               │ Heuristic or extrapolated   │
│                          │ landmark coordinates        │
└──────────────────────────┴─────────────────────────────┘
```

### 3.1 Strict Validation Function
```python
def validate_governance_tier(
    registration_status: str,
    reviewer: Optional[str] = None,
    evidence_id: Optional[str] = None,
    uncertainty_radius_mm: Optional[float] = None
) -> None:
    if registration_status not in VALID_GOVERNANCE_STATUSES:
        raise ValueError(f"Invalid registration status '{registration_status}'. Allowed: {VALID_GOVERNANCE_STATUSES}")

    if registration_status == "ANATOMY_REVIEWED":
        rev = (reviewer or "").strip()
        if not rev:
            raise ValueError("Anatomical review claims ('ANATOMY_REVIEWED') require a named qualified human reviewer.")
        
        rev_words = set(rev.lower().replace('-', ' ').replace('_', ' ').split())
        invalid_tokens = {'ai', 'system', 'automated', 'unknown', 'none', 'bot', 'algorithm', 'gpt', 'llm'}
        if rev_words & invalid_tokens or rev.lower() in invalid_tokens:
            raise ValueError(f"Reviewer '{rev}' is invalid. Human clinical governance requires qualified practitioner review, not automated systems.")
            
        if not (evidence_id or "").strip():
            raise ValueError("Anatomical review claims ('ANATOMY_REVIEWED') require an explicit evidence catalog reference or citation.")
        if uncertainty_radius_mm is not None and uncertainty_radius_mm < 0:
            raise ValueError(f"Uncertainty radius must be non-negative, got {uncertainty_radius_mm}mm.")
```

---

## 4. Evidence Ledger & Audit Trail

The Evidence Ledger table (`point_revisions` joined with `evidence_catalog`) records every coordinate adjustment:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Evidence Ledger                                 │
├──────┬──────────┬───────────┬──────────────┬───────────────┬────────────────┤
│ Rev# │ Point ID │ Operation │ Author       │ Reviewer      │ Evidence Ref   │
├──────┼──────────┼───────────┼──────────────┼───────────────┼────────────────┤
│ 148  │ CUST-01  │ CREATE    │ Clinical Eng │ Dr. Smith, MD │ EVID-A-002     │
│ 147  │ GB21     │ OVERRIDE  │ Practitioner │ Dr. Vance, PT │ EVID-A-001     │
│ 146  │ LI4      │ RELOCATE  │ Practitioner │ Supervised    │ EVID-G-001     │
└──────┴──────────┴───────────┴──────────────┴───────────────┴────────────────┘
```

The endpoint `GET /api/governance/evidence-ledger` exposes this audit history for independent quality assurance and regulatory scrutiny.

---

## 5. Database Integrity, Backup & Rollback Protocol

### 5.1 Automated Integrity Audit (`/api/governance/status`)
Executes:
1. `PRAGMA integrity_check` — Verifies B-tree structure, page consistency, and database file health.
2. `PRAGMA foreign_key_check` — Guarantees all foreign keys resolve cleanly.
3. Reference dataset hash verification against `CANONICAL_REFERENCE_CHECKSUMS`.
4. Schema audit ensuring `ANATOMY_REVIEWED` records satisfy human reviewer criteria.

### 5.2 Atomic Backup (`backup_database`)
Utilizes the SQLite Online Backup API (`db.backup(dest_db, pages=100)`):
- Creates consistent snapshot without locking write transactions.
- Output destination: `data/backups/backup_snapshot_<timestamp>.sqlite3`.

### 5.3 Rollback Procedure (`rollback_database`)
- Restores database state from a verified backup snapshot.
- Validates file headers and checksums prior to restoring.
- Tested and verified in automated test suite `tests/test_governance_reconciliation.py`.
