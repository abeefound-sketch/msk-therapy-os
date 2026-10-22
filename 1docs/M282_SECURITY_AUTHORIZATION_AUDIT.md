# MSK-Therapy-OS | Milestone M2.8.2 Identity, Authentication & Authorization Audit

**Document ID:** `M282-SEC-002`  
**Milestone:** `M2.8.2 Final Security & Acceptance Remediation`  
**Author:** Principal Security Engineer & Senior Systems Architect  
**Date:** October 22, 2026  
**Status:** ACCEPTED / PRODUCTION-READY  

---

## 1. Executive Summary

Milestone M2.8.2 eliminates client-trust vulnerabilities in MSK-Therapy-OS by introducing an offline, zero-cloud identity, authentication, and role-based access control (RBAC) subsystem. 

Prior releases relied on client-supplied role parameters (e.g., `author_role: "reviewer"` in JSON bodies) and evaluated clinical supervisor authority via superficial string checks (e.g., searching for `"MD"` or `"PT"` within arbitrary name strings).

Under M2.8.2:
1. Every mutating request is validated against a server-side session token (`Authorization: Bearer <token>`).
2. The user's role (`student`, `reviewer`, `admin`) is derived exclusively on the server from the authenticated session.
3. Clinical approvals and Tier 3/4 anatomical governance reviews are strictly bound to a database-backed `clinical_reviewers` registry requiring administrator credential verification (`VERIFIED_ACTIVE`), official license numbers, and licensing jurisdictions.
4. Mutating requests require session-bound CSRF tokens (`X-CSRF-Token`) and strictly reject untrusted or `null` origins with HTTP 403.

---

## 2. Authentication & Credential Architecture

### 2.1 Offline Password Hashing (PBKDF2-HMAC-SHA256)
MSK-Therapy-OS operates in air-gapped clinical and educational settings without external cloud dependencies. Password storage adheres to NIST SP 800-63B standards:
- **Algorithm:** PBKDF2 with HMAC-SHA256
- **Work Factor:** 100,000 iterations
- **Salt:** 16 bytes of cryptographically secure random bytes (`secrets.token_bytes(16)`)
- **Encoded Format:** `pbkdf2:sha256:100000$<salt_hex>$<hash_hex>`
- **Constant-Time Verification:** Python `hmac.compare_digest` to prevent timing analysis attacks.

### 2.2 Session Management & CSRF Tokens
- **Session Tokens:** 32-byte cryptographically secure random hex strings (`secrets.token_hex(32)`).
- **Session Duration:** 28,800 seconds (8 hours) for standard clinical work shifts.
- **CSRF Tokens:** Session-bound 32-byte hex strings. For every `POST`, `PUT`, or `DELETE` request, the server verifies `X-CSRF-Token` matches the active session. Requests with missing or mismatched CSRF tokens are rejected with **HTTP 403 Forbidden**.
- **Session Invalidation:** Explicit logout endpoint `/api/auth/logout` permanently deletes the session from the `auth_sessions` table.

```
+-----------------------------------------------------------------------------------------+
|                                    Client Request                                       |
+-----------------------------------------------------------------------------------------+
       |                                                    |
       v                                                    v
[Authorization: Bearer <session_token>]              [X-CSRF-Token: <csrf_token>]
       |                                                    |
       +----------------------------+-----------------------+
                                    |
                                    v
                     [Server Session Validator]
                                    |
         +--------------------------+--------------------------+
         |                                                     |
         v                                                     v
   Session Expired?                                  Token Matches Database?
   -> 401 Unauthorized                                -> 403 Forbidden
         |                                                     |
         +--------------------------+--------------------------+
                                    | Valid
                                    v
                  Derive Server Role & Identity
              (student / reviewer / admin)
```

---

## 3. Server-Enforced RBAC & Clinical Reviewer Registry

### 3.1 Role Hierarchy & Permissions

| Role | Permitted Actions | Prohibited Actions |
| :--- | :--- | :--- |
| **`student`** | Read catalog, draft SOAP notes, submit ROM/clinical observations, author unreviewed custom points. | Approve SOAP notes, verify clinical credentials, set Tier 3/4 reference overrides, trigger database backup/restore. |
| **`reviewer`** | All student actions, approve/reject SOAP notes, author and verify Tier 3/4 custom points, set reference point overrides. | Verify new clinical reviewers, trigger database backup/restore. |
| **`admin`** | All actions, clinical reviewer registry verification (`VERIFIED_ACTIVE`), database backup and safe online restore. | None (full administrative authority). |

### 3.2 Clinical Reviewers Database Registry
Superficial substring matching (`"MD"` or `"PT"` in reviewer names) has been eliminated. The system enforces database verification via the `clinical_reviewers` table:

```sql
CREATE TABLE IF NOT EXISTS clinical_reviewers (
    reviewer_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    display_name TEXT NOT NULL,
    primary_credential TEXT NOT NULL CHECK (primary_credential IN ('MD', 'DO', 'LAC', 'PT', 'DPT', 'DC', 'PHD', 'MBBS', 'ND')),
    license_number TEXT NOT NULL,
    licensing_jurisdiction TEXT NOT NULL,
    evidence_file_or_url TEXT,
    verification_status TEXT NOT NULL DEFAULT 'PENDING_REVIEW' CHECK (verification_status IN ('PENDING_REVIEW', 'VERIFIED_ACTIVE', 'REJECTED', 'SUSPENDED')),
    verified_by_admin TEXT REFERENCES users(user_id),
    verified_utc TEXT,
    notes TEXT,
    created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
```

### 3.3 Verification Governance
- When a SOAP note is approved via `/api/soap/review`, the server inspects the session user. If the user is not in `clinical_reviewers` with `verification_status == 'VERIFIED_ACTIVE'`, the approval is rejected with **HTTP 403** (`"Reviewer must have VERIFIED_ACTIVE status in clinical_reviewers registry"`).
- Reviewers with `PENDING_REVIEW` status (such as seeded user `dr_pending`) cannot approve clinical records or certify anatomical points until an administrator verifies them via `/api/auth/verify-reviewer`.

---

## 4. Origin & Request Boundary Protection

### 4.1 Strict Origin Verification
To protect local clinical records from cross-origin requests originating from internet-connected browser tabs:
- The server checks the `Origin` header on all mutating requests (`POST`, `PUT`, `DELETE`).
- **Rejected Origins:** External origins (`https://malicious.com`) and `null` origins (associated with sandboxed iframes or file:/// URIs attempting CSRF) are rejected with **HTTP 403 Forbidden**.
- **Permitted Origins:** Only trusted local addresses (`http://localhost:<port>`, `http://127.0.0.1:<port>`) matching the bound host port are accepted.

---

## 5. Verification Test Evidence

All authentication and RBAC controls were verified through automated integration tests in [`tests/test_auth_and_rbac.py`](file:///D:/5Projects/msk-therapy-os/tests/test_auth_and_rbac.py):

```
tests\test_auth_and_rbac.py::test_password_hashing_and_verification PASSED
tests\test_auth_and_rbac.py::test_user_authentication_success_and_failure PASSED
tests\test_auth_and_rbac.py::test_session_lifecycle_and_expiration PASSED
tests\test_auth_and_rbac.py::test_clinical_reviewer_registry_and_admin_verification PASSED
tests\test_auth_and_rbac.py::test_soap_approval_requires_verified_active_reviewer PASSED
tests\test_auth_and_rbac.py::test_soap_approval_red_flag_requires_documented_referral PASSED
tests\test_auth_and_rbac.py::test_session_recording_blocked_on_red_flags_without_referral PASSED
tests\test_auth_and_rbac.py::test_session_recording_spinal_manipulation_prohibited PASSED
tests\test_auth_and_rbac.py::test_fhir_export_marks_rejected_soap_entered_in_error PASSED
tests\test_auth_and_rbac.py::test_api_auth_login_me_logout_routes PASSED
tests\test_auth_and_rbac.py::test_api_csrf_and_origin_enforcement PASSED
```

**Result: 11 / 11 tests PASSED in 32.4s.**
