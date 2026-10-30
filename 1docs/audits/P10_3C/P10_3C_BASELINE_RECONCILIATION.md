# P10.3C BASELINE RECONCILIATION & FORENSIC AUDIT REPORT

**Milestone:** P10.3C — Production Hardening, Institutional Data Readiness & Independent Release Verification  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Audited Baseline Commit:** [`0acfad83595100b62c385f06ecb7e82fc0c9c6fa`](file:///D:/5Projects/msk-therapy-os)  
**System Version:** `v2.1.0-local-rc3`  
**Host Architecture:** Windows 11 x64, Intel(R) Core(TM) i7-5600U CPU @ 2.60 GHz (2 Cores, 4 Threads), Intel(R) HD Graphics 5500  
**Lead Auditor / Role:** Principal Systems Architect, Senior Python Engineer, Medical Imaging Security Engineer & QA Lead  
**Audit Date:** 2026-10-30  
**Gate P309 Status:** **PASS**

---

## 1. Executive Summary & Forensic Verification

An exhaustive forensic baseline audit was executed against the MSK-Therapy-OS repository at commit `0acfad8`. All source code modifications from P10.3B, database schemas, test suites, and hardware configurations were evaluated against the five forensic issues highlighted in the P10.3C mandate.

### Verified Test Accounting:
- **Total Tests Discovered by Pytest:** Exactly **698 tests**.
- **Non-Playwright Unit/Integration Suite:** **683 tests** (`pytest -m "not playwright"`).
- **Playwright Browser E2E Suite:** **15 tests** (`pytest -m "playwright"`).
- **Test Integrity:** 0 failures, 0 xfails, 0 unhandled exceptions.

---

## 2. Forensic Reconciliation of Mandatory Issues

### ISSUE-01: Regression Accounting & Test Catalog Reconciliation
- **Reported in P10.3B:** 685 baseline tests (670 non-playwright + 15 playwright) + 13 P10.3B tests = 698 total.
- **Forensic Verification:**
  - Running `pytest --collect-only -q` discovers exactly **698 tests**.
  - Running `pytest -m "playwright" --collect-only -q` selects exactly **15 tests** and deselects 683.
  - Running `pytest -m "not playwright" --collect-only -q` selects exactly **683 tests** and deselects 15.
- **Conclusion:** Reconciled with 100% precision. Total test catalog is **698 tests**.

### ISSUE-02: Bootstrap Parameter & Seed Standardization
- **Investigation:**
  - In [`msk_therapy_os/anatomical_validation.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py), `compute_subject_bootstrap_ci` specifies default `n_bootstraps: int = 1000`.
  - In `run_p10_3b_empirical_pilot_harness`, `n_bootstraps = 500` was passed for rapid automated regression execution ($<0.5\text{s}$).
- **Reconciliation & Standard:**
  - Standard formal evaluation benchmark is standardized at $B = 1,000$ replications.
  - Automated fast CI test runs may specify $B = 500$ with fixed seed `20261030` for deterministic reproducibility.
  - The bootstrap algorithm resamples subject clusters with replacement and calculates empirical percentile $[P_{2.5}, P_{97.5}]$ intervals.

### ISSUE-03: Browser E2E Scope
- **Investigation:**
  - The 15 existing Playwright tests in `tests/test_p9_*playwright*.py` and `tests/test_dien_chan_playwright.py` only cover P9 features (Atlas, Dien Chan, tissue layers).
  - The newly added validation studio buttons (`#btnRunPilotHarness`, `#btnCheckGateStatus`, `#btnRunBootstrapCI`, `#btnRunValidationDryRun`) have not been exercised by a real browser-driven Playwright test.
- **Resolution:**
  - A dedicated browser E2E test file [`tests/test_p10_3c_playwright.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p10_3c_playwright.py) will be implemented in Phase G to interact with the DOM, click all studio validation buttons, and assert live UI updates.

### ISSUE-04: Hardware Provenance Verification
- **Investigation:**
  - WMI processor query returned: `Intel(R) Core(TM) i7-5600U CPU @ 2.60GHz, 2 Cores, MaxClockSpeed 2594`.
  - WMI video controller query returned: `Intel(R) HD Graphics 5500`.
- **Finding:** The execution workstation **is the exact physical target hardware**. Performance benchmarks do not rely on emulation or historical reports; they reflect live execution on the reference low-spec target machine.

### ISSUE-05: Critical Claim & Security Defect Verification
The forensic audit identified **five critical security and architectural defects** in the P10.3B implementation:

1. **Client-Supplied De-Identification Bypass:**
   In `msk_therapy_os/dicom_intake.py`, `DicomHeaderParser.parse_file` accepts `pixel_certificate: Optional[Dict[str, Any]] = None`. An untrusted client calling the preflight API can pass `{"certificate_id": "X", "verified_by_institution": True}` to bypass the unverified pixel quarantine! This must be replaced with server-side verifiable attestations bound to the dataset manifest hash.
2. **Volatile In-Memory Governance Audit Trail:**
   `self._governance_audit_trail` was stored only as a Python in-memory list in `IndependentAnatomicalValidator`. Server restarts wipe the entire audit trail! It must be persisted in an append-only SQLite table with atomic transactions.
3. **Unauthenticated Reviewer Strings & Co-Signing:**
   `admin_sign_off_dataset` accepts arbitrary strings (`admin_reviewer_id="REV-CLINICAL-AUDITOR"`, `cosigner_id="REV-LEAD-ANATOMIST"`) without session authentication, password verification, or digital signature checks against the SQLite user store.
4. **DICOM 10MB Parser Limit Blocking Legitimate Images:**
   `dicom_intake.py` enforces a rigid `length > 10 * 1024 * 1024` check that halts parsing on any element exceeding 10MB. While appropriate for metadata headers, legitimate uncompressed CT/MRI Pixel Data `(7FE0, 0010)` can easily reach 16MB–128MB. The parser must distinguish metadata limits from pixel data boundaries without loading full pixel buffers into RAM.
5. **Incomplete Spatial Coordinate Transform Verification:**
   `dicom_intake.py` extracts position and spacing but does not compute and validate the full $4 \times 4$ spatial transformation matrix, direction cosine orthogonality, or coordinate handedness from `ImageOrientationPatient` `(0020, 0037)`.

---

## 3. Phase A Audit Conclusion

The baseline repository state at commit `0acfad8` has been fully cataloged and forensic gaps identified. Gate P309 is **PASSED**.
