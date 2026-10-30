# P10.3B HOLDOUT ISOLATION & DATA LEAKAGE ADVERSARIAL AUDIT REPORT

**Milestone:** P10.3B — Independent Audit, Security Hardening & Empirical Pilot Readiness  
**Target Module:** [`msk_therapy_os/anatomical_validation.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py) (`HoldoutPartitionManager`)  
**Standard:** STARD 2015 / TRIPOD+AI Guidelines for Independent Model Evaluation  
**Role:** Quantitative Validation Engineer & Independent QA Lead  
**Audit Date:** 2026-10-30  
**Gate P304 Status:** **PASS**

---

## 1. Objective & Threat Model

In machine learning and computational anatomy, data leakage between calibration/training data and validation holdouts leads to overly optimistic performance claims and dangerous overfitting.

### Evaluated Threat Vectors:
1. **Observation-Level Splitting Flaw:** Splitting landmarks randomly such that the same individual's abdomen is calibrated while their extremities are validated, leaking individual morphology, bone dimensions, and BMI across splits.
2. **Longitudinal Rescan Leakage:** The same patient scanned at baseline ($T_0$) and follow-up ($T_1$) being assigned to different partitions.
3. **Post-Hoc Manifest Mutation:** An engineer moving high-error holdout subjects into the calibration pool to artificially lower the holdout RMSE.
4. **Summary Aggregation Probe:** Probing public REST summaries to reconstruct holdout landmark coordinates.

---

## 2. Architectural Defenses & Verification

### 2.1 Strict Subject-Level Partitioning
In [`HoldoutPartitionManager.create_three_way_partition`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py#L408):
- All partitioning operations act strictly on unique subject identifiers:
  $$\text{unique\_subjects} = \text{sorted}(\text{list}(\text{set}(\text{subjects})))$$
- Whether a subject has 1 observation or 50 longitudinal observations across multiple scans, the entire entity is assigned atomically to **exactly one partition**:
  $$\text{Partition}(S_i) \in \{\text{Calibration}, \text{Validation}, \text{Holdout}\}$$
- Enforced constraint:
  $$\text{Calibration} \cap \text{Validation} = \emptyset \land \text{Calibration} \cap \text{Holdout} = \emptyset \land \text{Validation} \cap \text{Holdout} = \emptyset$$

### 2.2 Cryptographic Manifest Locking & Tamper-Evident Verification
- When a partition is created, a SHA-256 manifest hash is generated over the canonical sorted subject lists:
  $$\text{Payload} = \text{partition\_id} \parallel \text{sorted}(\text{calib}) \parallel \text{sorted}(\text{val}) \parallel \text{sorted}(\text{holdout})$$
  $$\text{Checksum} = \text{SHA256}(\text{Payload})$$
- Added [`verify_partition_integrity(partition_id)`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py#L481). If any subject is surreptitiously added, deleted, or transferred post-lock, the recomputed checksum fails, and all dependent gate evaluations halt fail-closed.

### 2.3 Information Hiding in Validation Reports
- In [`validate_catalog(dataset_id)`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py):
  - Summary metrics only expose aggregate summary statistics (e.g. RMSE, MAE, 95th percentile, congruence rates) per cohort.
  - Raw landmark residual vectors for holdout subjects are masked from non-administrative endpoints.

---

## 3. Adversarial Leakage Simulation Matrix

| Test Scenario | Adversarial Action | Expected Result | Audit Verdict |
|---|---|---|---|
| **ADV-LEAK-01** | Longitudinal Scans ($T_0, T_1, T_2$) | All scans for `SUBJ_LONGITUDINAL_42` assigned to identical partition | **PASS** |
| **ADV-LEAK-02** | Overlap Injection Attempt | Manually force `SUBJ_01` into both Calibration and Holdout | Trapped by `verify_no_leakage_three_way` (`HOLDOUT_DATA_LEAKAGE_DETECTED`) | **PASS** |
| **ADV-LEAK-03** | Post-Lock Mutation | Mutate `holdout_subjects` list on a locked partition | Trapped by `verify_partition_integrity` (`False`) | **PASS** |
| **ADV-LEAK-04** | Partition Ratio Accuracy | 50% Calibration, 25% Validation, 25% Holdout split on $N=44$ | Partition sizes match target ratio within discrete rounding bounds | **PASS** |

---

## 4. Conclusion

Gate P304 is verified as **PASS**. The holdout management architecture guarantees zero subject-level data leakage, deterministic reproducibility, and cryptographic tamper resistance.
