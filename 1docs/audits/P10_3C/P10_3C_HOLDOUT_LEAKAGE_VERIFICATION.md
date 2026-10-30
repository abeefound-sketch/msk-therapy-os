# P10.3C HOLDOUT PARTITION & LEAKAGE VERIFICATION REPORT

**Milestone:** P10.3C — Production Hardening, Institutional Data Readiness & Independent Release Verification  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Target Module:** [`msk_therapy_os/anatomical_validation.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py)  
**Lead Auditor / Role:** Senior Computational Anatomy Engineer & Independent QA Auditor  
**Audit Date:** 2026-10-30  
**Gate P314 Status:** **PASS**

---

## 1. Executive Summary

In machine learning and computational anatomical calibration, data leakage between parameter tuning sets and validation sets produces overfitted, clinically invalid claims of accuracy. In Milestone P10.3C, the [`HoldoutPartitionManager`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py) was audited and hardened to guarantee mathematical disjointness, longitudinal leakage prevention, and cryptographic sealing of the independent holdout partition.

---

## 2. Partition Formulation & Mathematical Disjointness

Let the cohort of research subjects be denoted by $\mathcal{S} = \{S_1, S_2, \dots, S_N\}$.  
The partition manager divides $\mathcal{S}$ into Calibration $\mathcal{S}_{cal}$ (default 70%) and Independent Holdout $\mathcal{S}_{hold}$ (default 30%):

$$\mathcal{S}_{cal} \cup \mathcal{S}_{hold} = \mathcal{S}$$
$$\mathcal{S}_{cal} \cap \mathcal{S}_{hold} = \emptyset$$

### 2.1 Cryptographic Partition Manifest
Upon partition generation:
1. Subject identifier lists are canonicalized and sorted.
2. An SHA-256 manifest hash is calculated over the partition structure:
   $$\text{manifest\_checksum} = \text{SHA-256}(\mathcal{S}_{cal} \parallel \mathcal{S}_{hold} \parallel \text{split\_ratio})$$
3. The partition is immediately marked `is_locked = True`. Any subsequent attempt to alter subject membership fails closed.

---

## 3. Longitudinal Leakage Prevention

In longitudinal clinical protocols, a single patient may undergo repeated scans (e.g. baseline CT, follow-up MRI at 3 months).

### 3.1 Subject-Level vs. Observation-Level Partitioning
- **Vulnerability:** Partitioning at the image slice or observation level risks placing Subject A Visit 1 into Calibration and Subject A Visit 2 into Holdout. The model would memorize subject-specific skeletal landmarks, leaking ground truth.
- **Enforced Invariant:** MSK-Therapy-OS partitions strictly by `subject_pseudonym`. All observations, scans, and modalities originating from subject $S_k$ are assigned as an indivisible unit to either $\mathcal{S}_{cal}$ or $\mathcal{S}_{hold}$.

### 3.2 Automated Leakage Guard
The validator verifies partition containment before accepting any observation for evaluation:
```python
if is_holdout_evaluation and obs.subject_pseudonym in partition.calibration_subjects:
    raise SecurityLeakageError("Cross-partition contamination: Calibration subject detected in holdout evaluation.")
```

---

## 4. Negative Transition Enforcement

1. **Locked Holdout Tamper Protection:**  
   Modifying the calibration or holdout list invalidates the cryptographic checksum, permanently quarantining the partition.
2. **Dual Governance Authorization Required:**  
   Unlocking the holdout partition for independent unblinded auditing requires dual governance administrative sign-off (`CLINICAL_SAFETY_AUDITOR` + `LEAD_ANATOMIST`). Without dual sign-off, holdout observations remain in an inaccessible quarantine vault.

Gate P314 verification confirms zero data leakage and cryptographic sealing of the empirical holdout partition.
