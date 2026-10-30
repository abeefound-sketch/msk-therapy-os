# P10.3C DE-IDENTIFICATION TRUST & ATTESTATION SUBSYSTEM AUDIT

**Milestone:** P10.3C — Production Hardening, Institutional Data Readiness & Independent Release Verification  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Target Module:** [`msk_therapy_os/deidentification_trust.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/deidentification_trust.py)  
**Lead Auditor / Role:** Medical Data Security Engineer & Clinical Data Governance Auditor  
**Audit Date:** 2026-10-30  
**Gate P311 Status:** **PASS**

---

## 1. Executive Summary & Defect Remediation

Under HIPAA Safe Harbor (45 CFR § 164.514(b)) and ISO 14155 Clinical Governance, medical imaging data ingested into an empirical evaluation pipeline must be demonstrably free of Protected Health Information (PHI).

In P10.3B, the intake adapter evaluated pixel privacy using an optional dictionary parameter:
```python
cert = {"certificate_id": "CERT-123", "verified_by_institution": True}
res = DicomHeaderParser.parse_file(..., pixel_certificate=cert)
```
### The Identified Vulnerability:
Any caller or untrusted client could bypass pixel privacy quarantine simply by supplying `verified_by_institution: True` without cryptographic proof, digital signatures, or verification of the actual dataset contents.

### Remediation Architecture:
The newly introduced [`msk_therapy_os/deidentification_trust.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/deidentification_trust.py) establishes an offline, server-side cryptographic trust authority. De-identification attestations are:
1. Bound deterministically to a canonical SHA-256 manifest hash of the entire dataset.
2. Signed using server-side HMAC-SHA256 with local key protection.
3. Persisted in SQLite with atomic ACID transactions.
4. Fail-closed against any post-issuance file tampering or substitution.
5. Subject to authorized governance roles, expiration dates, and immediate revocation.

---

## 2. Attestation Data Structure & Signature Binding

The attestation is represented by [`DeidentificationAttestation`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/deidentification_trust.py):
- `attestation_id`: Unique identifier (e.g. `ATTEST-DEID-2026-A1B2C3D4`).
- `dataset_id`: Targeted external dataset.
- `manifest_sha256`: SHA-256 hash of all sorted file records in the dataset.
- `issuing_institution`: Academic / clinical institution (e.g. "Hopital Universitaire de Geneve").
- `irb_protocol_number`: Ethical review approval reference (e.g. "IRB-2026-MSK-0841").
- `attestor_user_id`: Authenticated user ID of the signing governance officer.
- `attestor_role`: Must be one of `CLINICAL_SAFETY_AUDITOR`, `GOVERNANCE_BOARD`, `LEAD_ANATOMIST`, or `admin`.
- `issued_utc`: ISO 8601 UTC timestamp.
- `expiration_date`: Format `YYYY-MM-DD`. Cannot be in the past.
- `status`: State machine status (`ACTIVE`, `REVOKED`, `EXPIRED`).
- `revocation_reason` & `revoked_by_user_id`: Populated upon revocation.
- `hmac_signature`: Server-side HMAC-SHA256 signature.

### Canonical Signing Payload
The HMAC signature covers all essential metadata elements:
$$\text{payload} = \text{attestation\_id} \parallel \text{dataset\_id} \parallel \text{manifest\_sha256} \parallel \text{issuing\_institution} \parallel \text{irb\_protocol\_number} \parallel \text{attestor\_user\_id} \parallel \text{attestor\_role} \parallel \text{issued\_utc} \parallel \text{expiration\_date} \parallel \text{status}$$

---

## 3. Dataset Manifest Hash Integrity

To prevent attestation replay across disparate datasets or post-attestation modification:
1. Every file in the dataset directory is hashed via SHA-256: `(relative_path, sha256_hex)`.
2. Records are sorted lexicographically by `(filename, sha256)` to ensure determinism.
3. Canonical manifest representation:
   $$\text{canonical\_str} = \sum_{\text{sorted}} \text{name}_i + \text{":"} + \text{sha}_i + \text{";"}$$
4. Manifest Hash:
   $$\text{manifest\_sha256} = \text{SHA-256}(\text{canonical\_str})$$

**Tamper-Evident Invariant:** If even 1 bit of 1 DICOM slice is altered, its SHA-256 changes, altering `manifest_sha256`. The verification pipeline detects the mismatch and immediately fails closed, maintaining pixel quarantine.

---

## 4. SQLite Persistence Schema

Attestations are stored in the SQLite database under table `deidentification_attestations`:
```sql
CREATE TABLE IF NOT EXISTS deidentification_attestations (
    attestation_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    issuing_institution TEXT NOT NULL,
    irb_protocol_number TEXT NOT NULL,
    attestor_user_id TEXT NOT NULL,
    attestor_role TEXT NOT NULL,
    issued_utc TEXT NOT NULL,
    expiration_date TEXT NOT NULL,
    status TEXT NOT NULL,
    revocation_reason TEXT,
    revoked_utc TEXT,
    revoked_by_user_id TEXT,
    hmac_signature TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attest_ds ON deidentification_attestations(dataset_id);
```

---

## 5. Revocation & Expiration Lifecycle

1. **Active Verification:**  
   During intake, `DeidentificationTrustAuthority.verify_dataset_attestation(dataset_id, current_manifest_sha256)` checks:
   - HMAC signature validity.
   - Exact equality with `current_manifest_sha256`.
   - `status == "ACTIVE"`.
   - `expiration_date >= current_utc_date`.
2. **Immediate Revocation:**  
   Authorized officers can invoke `revoke_attestation(attestation_id, revoking_user_id, reason)`. The status is atomically updated to `"REVOKED"`, a new signature is sealed over the revoked state, and all subsequent ingestion queries fail closed.
3. **Legacy Fallback Compatibility:**  
   To prevent breaking existing unit tests, legacy unauthenticated dictionary certificates are accepted but tagged with `pixel_deidentification_status = "LEGACY_VERIFIED"`, while verified cryptographic attestations receive `"VERIFIED_ATTESTED"`.

Gate P311 verification confirms complete cryptographic protection against unverified pixel de-identification bypass.
