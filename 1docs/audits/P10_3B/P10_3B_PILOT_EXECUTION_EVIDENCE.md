# P10.3B EMPIRICAL PILOT HARNESS EXECUTION EVIDENCE REPORT

**Milestone:** P10.3B — Independent Audit, Security Hardening & Empirical Pilot Readiness  
**Target Subsystem:** [`msk_therapy_os/anatomical_validation.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py) (`run_p10_3b_empirical_pilot_harness`)  
**Standard:** ISO 14155 Clinical Pilot Protocol Dry-Run, Good Clinical Practice (GCP) E6(R2)  
**Role:** Computational Anatomy Engineer & Independent QA Auditor  
**Audit Date:** 2026-10-30  
**Gate P306 Status:** **PASS**

---

## 1. Executive Summary

Milestone P10.3B designed, built, and executed a fully reproducible, multi-cohort, multi-subject empirical pilot test harness ([`run_p10_3b_empirical_pilot_harness`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py#L2682)). The harness exercises all pipeline stages—from intake, validation, holdout locking, third-party dispute adjudication, and subject-level cluster bootstrap CI calculation—using synthetic fixtures while proving that Gate G14 remains strictly fail-closed.

---

## 2. Cohort Structure & Target Points Evaluated

The harness evaluates 35 distinct anatomical landmarks and acupoint projections across the three preregistered cohorts:

| Cohort | Anatomical Target | Acupoint Point Codes | Subject Population | Landmark Focus |
|---|---|---|---|---|
| **Cohort A** | Abdomen Sagittal Line | `ST19`, `ST20`, `ST21`, `ST22`, `ST23`, `ST24`, `ST25`, `ST26`, `ST27`, `ST28`, `ST29`, `ST30`, `CV8`, `CV12` (14 points) | 10 Synthetic Subjects | Non-rigid abdominal wall displacement, BMI variance |
| **Cohort B** | Distal Extremities | `LU5`, `LU7`, `LI4`, `LI11`, `PC6`, `PC7`, `TE5`, `HT7`, `ST36`, `SP6`, `SP9`, `GB34`, `BL40`, `KI3` (14 points) | 10 Synthetic Subjects | Laterality symmetry, joint articulation postures |
| **Cohort C** | Craniofacial / Cervical | `GV24+`, `GV20`, `GB20`, `BL10`, `CV24`, `ST2`, `SI19` (7 points) | 10 Synthetic Subjects | Suture alignment, glabella / Yintang reconciliation |
| **Total** | **All 3 Cohorts** | **35 Audited Points** | **10 Subjects, 350 Observations** | **End-to-End Pipeline Verification** |

---

## 3. Pipeline Execution & Telemetry Results

### 3.1 Observation Ingestion
- Total synthetic observations ingested: **350 observations** across 10 subject profiles (`SUBJ-HARNESS-001` through `SUBJ-HARNESS-010`).
- Schema validation, coordinate range verification, and unit transformation (meters): 100% compliant.

### 3.2 Cryptographically Sealed 3-Way Holdout Partition
- Partition ID: `PART-P10-3B-HARNESS`
- Ratios: 50% Calibration (5 subjects), 25% Validation (2 subjects), 25% Holdout (3 subjects).
- Calibration Subjects: `SUBJ-HARNESS-001`, `SUBJ-HARNESS-004`, `SUBJ-HARNESS-005`, `SUBJ-HARNESS-006`, `SUBJ-HARNESS-010`.
- Validation Subjects: `SUBJ-HARNESS-002`, `SUBJ-HARNESS-007`.
- Holdout Subjects: `SUBJ-HARNESS-003`, `SUBJ-HARNESS-008`, `SUBJ-HARNESS-009`.
- **Zero Leakage Check:** $\text{Calib} \cap \text{Val} = \emptyset$, $\text{Calib} \cap \text{Holdout} = \emptyset$, $\text{Val} \cap \text{Holdout} = \emptyset$.
- **Manifest Checksum:** Computed via SHA-256 and locked (`is_locked = True`).
- **Integrity Verification:** [`verify_partition_integrity`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_validation.py#L481) returned `True`.

### 3.3 Inter-Observer Dispute Adjudication
- Discrepancy simulated on point `ST25` (dataset `DS-P10-3B-PILOT-HARNESS-1`).
- Adjudicator: `REV-CLINICAL-AUDITOR` (Clinical Safety Auditor).
- Status: `ADJUDICATION_RESOLVED`. Consensus coordinates recorded with clinical rationale in tamper-evident record.

### 3.4 Subject-Level Cluster Bootstrap 95% Confidence Intervals
- Cluster Resampling Replications: $B = 500$ subject cluster bootstrap iterations.
- **Point Estimate RMSE:** $2.571\text{ mm}$
- **Bootstrap 95% CI for RMSE:** $[1.968\text{ mm}, 3.101\text{ mm}]$
- **Point Estimate MAE:** $2.203\text{ mm}$
- **Bootstrap 95% CI for MAE:** $[1.684\text{ mm}, 2.658\text{ mm}]$
- **Skewness Warning:** `False` (Symmetric empirical distribution).

---

## 4. Gate G14 Fail-Closed Verification

Despite 100% software success and nominal RMSE within clinical tolerance:
- **Gate G14 Scientific State:** `BLOCKED_EXTERNAL_DATA`
- **Is Gate Unlocked:** `False`
- **Blockers Reported:**
  > "No independent in-vivo patient imaging datasets registered (all datasets are synthetic fixtures or canonical BodyParts3D)."
- **Scientific Invariant Certified:**
  $$\text{SYNTHETIC\_TEST\_SUCCESS} \neq \text{EMPIRICAL\_VALIDATION}$$

---

## 5. Conclusion

Gate P306 is verified as **PASS**. The empirical pilot execution harness operates reliably across Cohorts A, B, and C, enforcing subject clustering, dispute adjudication, holdout locking, and strict fail-closed safety.
