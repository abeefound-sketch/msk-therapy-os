# P10.3 THREE-WAY DATA ISOLATION & HOLDOUT INTEGRITY AUDIT
## Subject-Level Partitioning, Cryptographic Locking, Site Isolation, and Anti-Leakage Verification

> **CLASSIFICATION:** DATA ISOLATION & VALIDATION INTEGRITY AUDIT  
> **MILESTONE:** P10.3A  
> **COMPONENT:** `HoldoutPartitionManager` in `msk_therapy_os/anatomical_validation.py`  
> **STATUS:** PASSED — ABSOLUTE HOLDOUT ISOLATION ENFORCED

---

## 1. Executive Summary & Regulatory Objectives

A frequent failure mode in machine learning and computational medicine is data leakage between model tuning sets and validation sets. When images from the same patient or scans from the same session appear in both calibration and evaluation sets, reported accuracy is artificially inflated.

Milestone P10.3A implements a strict, tamper-evident subject-level partitioning architecture:
1. **Subject-Level Unit of Partitioning:** Data points are split exclusively by pseudonymous subject (`subject_pseudonym`), never by individual image, slice, or observation.
2. **50 / 25 / 25 Three-Way Partition:**
   - 50% Calibration Set (Parameter tuning, proportional cun scaling).
   - 25% Validation Set (Internal validation and hyperparameter selection).
   - 25% Holdout Set (Strictly blinded, evaluated only once for Gate G14).
3. **Cryptographic Locking:** The holdout manifest is locked using a SHA-256 checksum.
4. **Site-Level External Holdout:** Support for holding out an entire clinical institution or scanner domain.
5. **Post-Evaluation Freezing:** Any modification to calibration parameters after holdout exposure permanently invalidates the evaluation.

---

## 2. Subject-Level Partitioning Architecture

```
                       Entire Subject Population (N Subjects)
                                         │
                         ┌───────────────┼───────────────┐
                         │ (50%)         │ (25%)         │ (25%)
                         ▼               ▼               ▼
                 ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                 │ Calibration  │ │  Validation  │ │   Holdout    │
                 │     Set      │ │     Set      │ │     Set      │
                 └──────────────┘ └──────────────┘ └──────┬───────┘
                                                          │
                                               [lock_holdout_partition()]
                                                          │
                                                          ▼
                                               ┌─────────────────────┐
                                               │ Cryptographically   │
                                               │ Locked Manifest     │
                                               │ (SHA-256 Checksum)  │
                                               └─────────────────────┘
```

### Mathematical Anti-Leakage Proof:
For any partition $\mathcal{P} = (\mathcal{C}, \mathcal{V}, \mathcal{H})$:
$$\mathcal{C} \cap \mathcal{V} = \emptyset, \quad \mathcal{V} \cap \mathcal{H} = \emptyset, \quad \mathcal{C} \cap \mathcal{H} = \emptyset$$
$$\mathcal{C} \cup \mathcal{V} \cup \mathcal{H} = \mathcal{S}_{\text{total}}$$
The method `verify_no_leakage_three_way()` algorithmically asserts this condition. Injected overlap tests confirm that any overlapping subject immediately halts execution with `HOLDOUT_DATA_LEAKAGE_DETECTED`.

---

## 3. Cryptographic Manifest Locking & Post-Evaluation Freezing

### 3.1 Lock Mechanism:
Before any evaluation against the holdout set occurs, an authorized administrator must call `lock_holdout_partition(partition_id, admin_reviewer_id)`.
- The method computes:
  $$\text{Hash} = \text{SHA-256}(\text{partition\_id} \,\|\, \text{sorted}(\mathcal{H}) \,\|\, \text{admin\_id})$$
- The manifest records `is_locked = True`, `locked_by = admin_id`, and `locked_sha256 = Hash`.

### 3.2 Freeze Rule:
Once the holdout partition is exposed to `validate_catalog()`, `mark_holdout_evaluated()` freezes the partition. Any subsequent attempt to add new subjects, re-lock, or modify calibration parameters raises `HOLDOUT_ALREADY_EVALUATED`.

---

## 4. Site-Level External Holdout (Multi-Center Generalizability)

When validation involves multiple hospital sites (e.g. Hospital A with Siemens CT scanners, Hospital B with GE CT scanners, Hospital C with Philips CT scanners):
- The method `create_site_level_partition()` assigns an entire clinical center (e.g. Hospital C) exclusively to the holdout partition.
- This tests domain generalization across differing scanner reconstruction algorithms and radiologist acquisition protocols, preventing cross-site calibration bias.

---

## 5. Audit Conclusion & Gate D Certification

| Verification Test | Test Description | Result |
|---|---|---|
| Split Ratio Consistency | 50% Calib / 25% Valid / 25% Holdout | **PASS** |
| Zero Leakage Assertion | Subject sets mutually disjoint | **PASS** |
| Injected Leakage Detection | Overlapping subject triggers ValueError | **PASS** |
| Cryptographic Manifest Lock | SHA-256 hash generated and verified | **PASS** |
| Post-Evaluation Freezing | Re-tuning after exposure blocked | **PASS** |
| Site-Level Holdout Isolation | Entire external hospital held out | **PASS** |

**Gate D Verdict:** **PASS**. Subject-level holdout isolation and anti-leakage defenses are 100% operational.
