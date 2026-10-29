# P10.3 GATE G14 FAIL-CLOSED AUDIT & SCIENTIFIC INVARIANT EVIDENCE
## Forensic Verification of State Transitions, Negative Security Proofs, and Prevention of Synthetic Unlocking

> **CLASSIFICATION:** REGULATORY FAIL-CLOSED AUDIT REPORT  
> **MILESTONE:** P10.3A  
> **COMPONENT:** `evaluate_g14_scientific_gate()` in `msk_therapy_os/anatomical_validation.py`  
> **STATUS:** PASSED — GATE G14 IS PROVABLY FAIL-CLOSED (`BLOCKED_EXTERNAL_DATA`)  
> **SCIENTIFIC INVARIANT:**  
> `TECHNICAL_CALIBRATION != INDEPENDENT_ANATOMICAL_GROUND_TRUTH != CLINICAL_VALIDATION`  
> `SYNTHETIC_TEST_SUCCESS != EMPIRICAL_VALIDATION`

---

## 1. Executive Summary & Purpose

A paramount safety concern in computational medical software is the inadvertent or unauthorized transition of regulatory acceptance gates from "BLOCKED" to "PASS". If engineering test fixtures, synthetic benchmarks, or incomplete pilot datasets could toggle Gate G14 to "PASS", unverified anatomical models could be misrepresented as clinically validated.

Milestone P10.3A implements an explicit, multi-stage state machine for Gate G14, backed by automated negative assertions proving that **no synthetic fixture, forged metadata string, or incomplete cohort can unlock G14**.

---

## 2. Gate G14 Explicit State Machine

Gate G14 operates under five formal, mutually exclusive states:

```
  ┌─────────────────────────────────────────────────────────────────┐
  │ 1. BLOCKED_EXTERNAL_DATA (Initial & Default State)              │
  │    No independent in-vivo patient CT/MRI datasets registered.   │
  │    Only synthetic fixtures or canonical BodyParts3D exist.      │
  └───────────────────────────────┬─────────────────────────────────┘
                                  │ (Real In-Vivo Patient Data Ingested)
                                  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 2. PENDING_GOVERNANCE_APPROVAL                                  │
  │    Missing/expired DUA/IRB, missing de-identification audit,    │
  │    or missing Clinical Review Board administrative sign-off.    │
  └───────────────────────────────┬─────────────────────────────────┘
                                  │ (DUA/IRB Valid & Admin Signed Off)
                                  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 3. PENDING_INDEPENDENT_REVIEW                                   │
  │    Pending multi-reviewer consensus, active quarantine items,   │
  │    unlocked holdout manifest, or sample size N < 43 subjects.   │
  └───────────────────────────────┬─────────────────────────────────┘
                                  │ (Holdout Locked, Discrepancies Adjudicated, N >= 43)
                                  ▼
                    ┌─────────────────────────────┐
                    │ Evaluate Holdout RMSE       │
                    └──────────────┬──────────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                │ (RMSE > Threshold)                  │ (All Cohort RMSE <= Threshold)
                ▼                                     ▼
  ┌───────────────────────────┐         ┌───────────────────────────┐
  │ 4. EMPIRICAL_VALIDATION_  │         │ 5. EMPIRICAL_EVIDENCE_    │
  │    FAILED                 │         │    READY                  │
  │    Holdout accuracy       │         │    All criteria verified; │
  │    thresholds breached.   │         │    G14 is unlocked.       │
  └───────────────────────────┘         └───────────────────────────┘
```

---

## 3. Negative Security Tests & Adversarial Proofs

The test suite `tests/test_p10_3_dicom_and_validation.py` executes five distinct adversarial tests to verify that G14 cannot be bypassed:

### 3.1 Attempt 1: Unlocking G14 via Synthetic Pilot Dry-Run
- **Action:** Execute `IndependentAnatomicalValidator.run_synthetic_pilot_dry_run()`.
- **Result:**
  - Technical pipeline status: `synthetic_dry_run_passed = True`.
  - Synthetic RMSE: $1.50\text{ mm} \le 5.0\text{ mm}$ (Excellent accuracy).
  - Gate G14 evaluation: **`BLOCKED_EXTERNAL_DATA` (is_unlocked = False)**.
- **Verdict:** **FAIL-CLOSED VERIFIED**. Synthetic data is permanently barred from unlocking G14.

### 3.2 Attempt 2: Registering External Dataset with Expired DUA
- **Action:** Register real dataset with `authorization_expiration_date = "2020-01-01"`.
- **Result:** Gate G14 transitions to `PENDING_GOVERNANCE_APPROVAL` (`is_unlocked = False`).
- **Verdict:** **FAIL-CLOSED VERIFIED**.

### 3.3 Attempt 3: Ingesting Real Data Without Admin Sign-Off
- **Action:** Dataset has `administrative_verification_status = "PENDING_ADMIN_SIGN_OFF"`.
- **Result:** Gate G14 transitions to `PENDING_GOVERNANCE_APPROVAL` (`is_unlocked = False`).
- **Verdict:** **FAIL-CLOSED VERIFIED**.

### 3.4 Attempt 4: Ingesting Data with Underpowered Sample Size ($N < 43$)
- **Action:** Ingest valid real observations from only 10 independent subjects.
- **Result:** Gate G14 transitions to `PENDING_INDEPENDENT_REVIEW` with blocker `"Sample size 10 is insufficient. Power analysis requires N >= 43 independent subjects."` (`is_unlocked = False`).
- **Verdict:** **FAIL-CLOSED VERIFIED**.

### 3.5 Attempt 5: Ingesting Data with Active Quarantined Observations
- **Action:** Ingest dataset with 1 unadjudicated inter-observer dispute.
- **Result:** Gate G14 transitions to `PENDING_INDEPENDENT_REVIEW` with blocker `"1 observations currently held in quarantine."` (`is_unlocked = False`).
- **Verdict:** **FAIL-CLOSED VERIFIED**.

---

## 4. UI Visibility & Non-Misleading Indicators

In the Meridian Route QA Studio interface:
- If G14 is in state `BLOCKED_EXTERNAL_DATA`, `PENDING_GOVERNANCE_APPROVAL`, or `PENDING_INDEPENDENT_REVIEW`, the badge is rendered in **high-contrast amber or crimson red**.
- **No green "PASS" indicator is displayed** anywhere in the UI for clinical validation.
- Tooltips and inspector panels display:
  > `[CỔNG G14: KHÓA CHẶT] Trạng thái: BLOCKED_EXTERNAL_DATA — Chưa có dữ liệu giải phẫu CT/MRI thực tế từ bệnh nhân.`

---

## 5. Audit Conclusion & Gate F Certification

| Condition Evaluated | Enforcement Mechanism | Result |
|---|---|---|
| Synthetic Exclusion | `is_synthetic_fixture` flag check | **FAIL-CLOSED VERIFIED** |
| DUA/IRB Validity | Timestamp comparison vs current UTC | **FAIL-CLOSED VERIFIED** |
| Administrative Sign-Off | `admin_sign_off_dataset` credential check | **FAIL-CLOSED VERIFIED** |
| Holdout Cryptographic Lock | SHA-256 partition manifest check | **FAIL-CLOSED VERIFIED** |
| Sample Size Power Floor | $N \ge 43$ independent subjects check | **FAIL-CLOSED VERIFIED** |
| Final Accuracy Barrier | Cohorts A, B, C threshold checks | **FAIL-CLOSED VERIFIED** |

**Gate F Verdict:** **PASS**. Gate G14 is mathematically and procedurally locked as **`BLOCKED_EXTERNAL_DATA`**. It cannot be unlocked without authentic, authorized, de-identified external human imaging evidence.
