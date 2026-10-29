# P9.14 Engineering Handoff & Architecture Transition Guide

**Project:** MSK-Therapy-OS  
**Milestone:** P9.14 — Independent Anatomical Ground-Truth Pilot & External Validation Framework  
**From:** Principal Computational Anatomy Engineer + Independent Scientific Validation Architect  
**To:** Lead Clinical AI Architect, Downstream Engineering Teams & Milestone P10 Leads  
**Date:** 2026-10-29  

---

## 1. Executive Summary & Repository State

Milestone P9.14 transitions MSK-Therapy-OS from *ground-truth ready* infrastructure to an *externally testable, mathematically rigorous, and independently reproducible* validation framework.

### Repository Baseline at Handoff
- **Git Branch:** `feat/p9.4-definitive-meridian-atlas-correction`
- **Catalog Status:** 362 Acupoints (361 Classical WHO 2008 + 1 Extended `GV24+`)
- **Technical Calibration Coverage:** 100% (18 Class A internal anchors, 344 Class B rule-derived)
- **Class C / Class D Remaining:** 0
- **Regression Test Suite:** 609/609 PASS (100%), 0 failures, 15 deselected Playwright tests
- **Empirical Ground-Truth Status:** `BLOCKED_EXTERNAL_DATA` (Zero external patient CT/MRI in repo)
- **Clinical Verification Status (Tier 4):** 0.0% (Zero clinical trials conducted; surgical depth strictly forbidden)

---

## 2. Architectural Deliverables & Source Map

The primary components implemented and hardened in P9.14:

```
msk_therapy_os/
├── anatomical_validation.py      # Core data contract, coordinate frame normalization, uncertainty propagation, pilot audits, SQLite persistence
├── server.py                     # Extended REST API endpoints (/api/atlas/validation/datasets, /evaluate, /independent-coverage, /evidence)
└── static/atlas/
    └── meridians.js              # QA Studio UI panel with separate technical calibration vs independent empirical ground-truth indicators

tests/
├── test_p9_14_ground_truth.py   # 20 automated tests covering all 17 mandated P9.14 test groups
├── test_p9_13_anatomical_validation.py # Predecessor P9.13 tests (9/9 PASS)
├── test_p9_13_falsification.py         # Predecessor P9.13 falsification tests (10/10 PASS)
└── test_p9_13_production_hardening.py  # Production hardening tests (7/7 PASS)

1docs/audits/P9_14/
├── P914_BASELINE_RECONCILIATION.md
├── P914_GROUND_TRUTH_DATA_CONTRACT.md
├── P914_INDEPENDENT_VALIDATION_PROTOCOL.md
├── P914_ST19_ST30_ANATOMICAL_PILOT.md
├── P914_BILATERAL_VALIDATION_REPORT.md
├── P914_CRANIAL_CERVICAL_VALIDATION_REPORT.md
├── P914_UNCERTAINTY_ERROR_MATRIX.csv
├── P914_EXTERNAL_EVIDENCE_COVERAGE.csv
├── P914_ADVERSARIAL_FALSIFICATION_REPORT.md
├── P914_FULL_REGRESSION_REPORT.md
├── P914_PRODUCTION_PERFORMANCE_REPORT.md
├── P914_FINAL_ACCEPTANCE_MATRIX.md
├── P914_EVIDENCE_MANIFEST.json
└── P914_ENGINEERING_HANDOFF.md

p9_14_milestone_delivery_report.md  # Root directory executive delivery report
```

---

## 3. How to Ingest External Validation Datasets

Downstream teams or academic partners wishing to validate MSK-Therapy-OS coordinates against in-vivo imaging or surface scans should use the following workflow:

```python
from msk_therapy_os.anatomical_validation import (
    IndependentAnatomicalValidator,
    ExternalGroundTruthDataset,
    GroundTruthObservation,
    GroundTruthModality,
    CoordinateFrame,
    MeasurementUnit,
)

validator = IndependentAnatomicalValidator()

# 1. Register Dataset Manifest
ds = ExternalGroundTruthDataset(
    dataset_id="DS-CLINICAL-MRI-2027",
    name="Prospective Multi-Center Volunteer MRI Acupoint Mapping",
    source_organization="Consortium for Integrative Computational Anatomy",
    version="1.0-MRI",
    license="CC BY 4.0",
    doi_or_url="https://doi.org/10.1016/j.clinbiom.2027.01.001",
    modality=GroundTruthModality.MRI_T1_ANATOMICAL,
    sample_size=30,
)
validator.register_dataset(ds)

# 2. Ingest Observations
obs = GroundTruthObservation(
    point_code="LI4",
    dataset_id="DS-CLINICAL-MRI-2027",
    canonical_position=(0.3415, 0.8118, 0.0821),
    uncertainty_radius_mm=1.0,
    subject_pseudonym="SUBJ-VOL-0012",
    coordinate_frame=CoordinateFrame.BP3D_CARTESIAN_METERS,
    unit=MeasurementUnit.METERS,
    observer_id="RAD-SPECIALIST-01",
)
validator.import_observations([obs], validate_contract=True)

# 3. Evaluate Validation Metrics
comparison = validator.validate_point("LI4", dataset_id="DS-CLINICAL-MRI-2027")
print(f"Residual: {comparison.residual_error_mm} mm, Class: {comparison.classification.value}")
```

---

## 4. Key Priorities & Road Ahead for Milestone P10

1. **Empirical In-Vivo Data Acquisition:** Establish institutional data sharing agreements with university radiology or biomechanics centers to obtain anonymized 3D CT/MRI scans with surface fiducials.
2. **Morphology-Aware Dynamic Scaling:** Transition the ST19..ST30 abdominal line from static $X = 0.0660\text{ m}$ to dynamic scaling parameterized by waist circumference and inter-ASIS distance.
3. **Multi-Center Clinical Consensus Protocol:** Design a prospective trial protocol to progress candidate points toward Tier 4 Clinical Verification.
4. **Maintenance of Fail-Closed Principles:** Continue to enforce zero fabricated passes, strict PII rejection, anti-conflict-of-interest checks, and non-invasive visual-only clinical governance.
