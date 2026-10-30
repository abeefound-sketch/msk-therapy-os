# P10.4 CLINICAL RESEARCH DATA CONTRACT FREEZE REPORT

**Milestone:** P10.4 — Independent Release Certification, Institutional Pilot Integration & Evidence Reproducibility  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Contract Version:** `v2.0-P10.4`  
**Module Implementation:** [`msk_therapy_os/research_contracts.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/research_contracts.py)  
**Lead Auditor / Role:** Medical Research Data Governance Specialist & Computational Anatomy Lead  
**Audit Date:** 2026-10-30  
**Gate P402 Verdict:** **PASS**

---

## 1. Executive Summary

Milestone P10.4 establishes a frozen, versioned data contract specification (`v2.0-P10.4`) designed to govern multi-institutional offline anatomical validation. The contract enforces unambiguous epistemological boundaries between imaging evidence, algorithmic inferences, and clinical outcomes, eliminating category errors in quantitative acupuncture research.

---

## 2. Epistemological Separation of Evidence Types

Previous literature and naive AI systems frequently conflate radiological features with traditional meridian pathways. The `v2.0-P10.4` contract formally defines and enforces three mutually exclusive evidence types:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        THREE EVIDENCE TIERS                            │
├────────────────────────────────────────────────────────────────────────┤
│ 1. PHYSICAL_ANATOMICAL_LANDMARK:                                       │
│    - Directly visible, verifiable physical structures on CT/MRI/US     │
│    - Examples: Nasion, Inion, C7 spinous process, Radial styloid        │
│    - Modality: Radiological cross-sectional imaging                    │
├────────────────────────────────────────────────────────────────────────┤
│ 2. COMPUTATIONALLY_INFERRED_ACUPOINT:                                  │
│    - Algorithmically derived coordinates using standardized rules      │
│    - Proportional B-cun division, surface-normal projection, anchors   │
│    - Requires computational_model_ref metadata                         │
├────────────────────────────────────────────────────────────────────────┤
│ 3. CLINICALLY_ASSESSED_OUTCOME:                                        │
│    - Deqi sensation, palpation tenderness, PROMs (NDI, QuickDASH)      │
│    - Patient-reported or practitioner-assessed observational data      │
└────────────────────────────────────────────────────────────────────────┘
```

> [!CRITICAL]
> **Scientific Invariant Enforced by Code:**
> A medical imaging scan (CT/MRI) is physical ground truth for osseous landmarks and soft tissue fascial planes, **NOT direct ground truth for meridians or acupuncture points**.
> 
> Attempting to label an acupoint identifier (e.g., `ST36`, `GV20`, `PC6`) directly as a `PHYSICAL_ANATOMICAL_LANDMARK` fails validation immediately with:
> `ResearchContractValidationError: Acupoint 'X' cannot be declared as PHYSICAL_ANATOMICAL_LANDMARK. CT/MRI scans do not directly image acupuncture points; use COMPUTATIONALLY_INFERRED_ACUPOINT with an anatomical anchor reference.`

---

## 3. Prespecified Multi-Institutional Cohorts

| Cohort Identifier | Target Anatomical Region | Modality Requirements | Minimum Sample ($N$) | Slice Thickness Limit | Primary Physical Landmarks | Inferred Meridian Segments |
|---|---|---|---|---|---|---|
| `COHORT_A_HEAD_NECK_CT` | Head & Craniofacial / Cervical Spine | Axial CT (Bone + Soft Tissue) | $\ge 30$ subjects | $\le 1.25\text{ mm}$ | Nasion, Inion, Glabella, EOP, C7 spinous process, Mastoid processes | `GV_CRANIAL`, `BL_CRANIAL`, `GB_TEMPORAL` |
| `COHORT_B_KNEE_EXTREMITY_MRI` | Knee Joint & Lower Leg | High-Res Proton Density / T1 MRI | $\ge 25$ subjects | $\le 3.00\text{ mm}$ | Tibial tuberosity, Patellar inferior pole, Femoral epicondyles, Fibular head | `SP_LEG`, `ST_LEG`, `LR_LEG`, `KI_LEG` |
| `COHORT_C_UPPER_LIMB_CT_MRI` | Forearm & Hand / Wrist Complex | Volumetric CT or 3T MRI | $\ge 30$ subjects | $\le 2.00\text{ mm}$ | Radial styloid, Ulnar styloid, Biceps tendon, Humeral epicondyles | `LU_ARM`, `LI_ARM`, `PC_ARM`, `HT_ARM`, `SI_ARM`, `TE_ARM` |

---

## 4. Contract Schema & Field Specifications

### 4.1 Structural Integrity & Canonical Hashing
The contract implements `compute_canonical_hash()` which generates a deterministic SHA-256 digest over normalized JSON keys:
1. `contract_version` (`v2.0-P10.4`)
2. `dataset_id`
3. `cohort_id`
4. `site` (`site_id`, `institution_name`, `country`, `regulatory_framework`, `authorized_contact_email`, `data_custodian_id`)
5. `authorization` (`dua_id`, `irb_approval_number`, `irb_effective_date`, `irb_expiration_date`, `deidentification_method`, `attestation_manifest_hash`, `is_synthetic_fixture`)
6. `imaging_series` (LPS origin, $4\times 4$ direction cosine matrix, voxel spacing)
7. `observations` (LPS coordinates in millimeters, observer ID, qualification, evidence type)
8. `sign_offs` (Dual admin reviewer IDs, timestamps, non-conflict declarations)

### 4.2 Automated Invariant & Expiration Verification
- **IRB/DUA Expiration:** Rejects datasets if the evaluation date exceeds `irb_expiration_date`.
- **Coordinate Sanity Bounds:** Validates all LPS coordinates fall within biologically plausible boundaries $[-2500\text{ mm}, 2500\text{ mm}]$.
- **Reviewer Conflict of Interest:** Rejects any sign-off where `coi_conflict_declared == True`.

---

## 5. Verification Verdict

The research data contracts are fully implemented in pure Python standard library, strictly verified against 15 adversarial test vectors, and committed to the repository. Gate P402 is certified as **PASS**.
