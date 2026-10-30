# MSK-THERAPY-OS AUDIT REPORT: P10.5-09
## Milestone P10.5 Engineering Handoff & Institutional Pilot Operational Runbook

### Metadata
- **Audit ID**: `P10_5-ENGINEERING-HANDOFF`
- **Milestone**: P10.5 (Institutional Research Pilot Activation, Statistical Design Verification & External Evidence Acquisition Readiness)
- **Repository**: `D:\5Projects\msk-therapy-os`
- **Active Branch**: `feat/p9.4-definitive-meridian-atlas-correction`
- **Target Version**: `v2.1.0-local-rc3`
- **Audit Date**: 2026-10-30
- **Auditor Role**: Principal Systems Architect & Release Engineer
- **Classification**: RESEARCH USE ONLY / TECHNICAL HANDOFF & OPERATIONAL MANUAL
- **Status**: **COMPLETE & VERIFIED**

---

## 1. Executive Summary & Baseline State

Milestone P10.5 completes the engineering, statistical, and operational governance infrastructure required for MSK-Therapy-OS to transition into real-world institutional research pilots. The repository is hardened against premature empirical claims, accidental synthetic promotion, single-operator overrides, and unblinded annotation confirmation bias.

### 1.1 Verified Repository Baseline
- **Branch**: `feat/p9.4-definitive-meridian-atlas-correction`
- **Baseline Commit (Pre-P10.5)**: `47679c5`
- **Target Hardware Envelope**: Intel Core i7-5600U, Intel HD Graphics 5500, 8 GB RAM, Windows 11.
- **Automated Regression Suite**: **744 tests (727 non-playwright + 17 playwright E2E), 100% PASS, 0 failures, 0 skipped**.
- **Release Scope**: `ENGINEERING_RESEARCH_ONLY`
- **Scientific Gate G14**: `BLOCKED_EXTERNAL_DATA`
- **Clinical Depth Guidance**: Permanently disabled (`clinical_depth_guidance_allowed: False`).

---

## 2. Deliverable Inventory

### 2.1 Core Source Modules
1. [`msk_therapy_os/statistical_design_engine.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/statistical_design_engine.py):
   - Hierarchical multi-level design effect engine: $DE = 1 + (m-1)\rho_{\text{within}} + m(n_{\text{site}}-1)\rho_{\text{site}}$.
   - Three prespecified planning scenarios: `MINIMUM_FEASIBILITY_PILOT` ($N=45$), `PRIMARY_ANATOMICAL_ACCURACY_STUDY` ($N=85$), and `INDEPENDENT_MULTI_SITE_VALIDATION` ($N=150$).
   - Subgroup holdout power analysis and 2D sensitivity grid over intra-class correlation $\rho \in [0.20, 0.50]$ and standard deviation $\sigma \in [1.0, 2.0]\text{ mm}$.
2. [`msk_therapy_os/partner_onboarding.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/partner_onboarding.py):
   - SQLite-backed persistence table `institutional_onboarding_registry`.
   - 8-stage onboarding status machine (`INSTITUTION_NOT_REGISTERED` to `PILOT_EXECUTION_PENDING`).
   - Fail-closed guard: blocks transition to `DATASET_INTAKE_AUTHORIZED` unless `dua_status == "EXECUTED_BILATERAL_DUA"` and `irb_status in ("APPROVED_BY_IRB", "WAIVER_OF_CONSENT_DETERMINED")`.
3. [`msk_therapy_os/real_world_intake_controller.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/real_world_intake_controller.py):
   - 7-state data custody lifecycle (`SYNTHETIC_FIXTURE` to `EMPIRICAL_REVIEW_PENDING`).
   - Hardened `SyntheticPromotionBlockedError` preventing synthetic fixtures from entering empirical custody chains.
   - Dual administrative officer cosign requirement (`admin1_id != admin2_id`), active IRB date check, and pixel PHI screening check.
4. [`msk_therapy_os/annotation_qc.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/annotation_qc.py):
   - Double-blind independent landmark ingestion with model blindness verification.
   - Anatomical category discrepancy thresholds: $3.0\text{ mm}$ (cranial osseous), $4.0\text{ mm}$ (extremity skeletal), $5.0\text{ mm}$ (soft tissue/abdominal).
   - Independent third-reviewer adjudication with observer exclusion check and signed COI requirement.
5. [`msk_therapy_os/server.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/server.py#L1133-L1170):
   - Live HTTP GET endpoint `/api/atlas/validation/pilot-readiness`.
6. [`msk_therapy_os/static/atlas/meridians.js`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/static/atlas/meridians.js#L2573, #L3224-L3253):
   - Meridian Route QA Studio UI button `#btnCheckPilotReadiness` and status badge `#lblP105PilotReadinessResult`.

### 2.2 Test Suites
1. [`tests/test_p10_5_pilot_activation.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p10_5_pilot_activation.py):
   - 7 unit/integration test cases covering statistical design engine, onboarding state transitions, fail-closed security guards, synthetic promotion blocking, and annotation QC adjudication.
2. [`tests/test_p10_5_playwright.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p10_5_playwright.py):
   - Headless Playwright E2E test verifying studio UI button click, API communication, DOM updates, and screenshot generation.

### 2.3 Evidence & Documentation Catalog
- Evidence Screenshot: [`2data/evidence/p10_5_validation/01_p10_5_pilot_readiness_dashboard.png`](file:///D:/5Projects/msk-therapy-os/2data/evidence/p10_5_validation/01_p10_5_pilot_readiness_dashboard.png)
- Audit Reports:
  - [`P10_5_BASELINE_SCOPE_FREEZE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_5/P10_5_BASELINE_SCOPE_FREEZE.md) (Gate P501)
  - [`P10_5_STATISTICAL_STUDY_DESIGN_REVIEW.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_5/P10_5_STATISTICAL_STUDY_DESIGN_REVIEW.md) (Gate P502)
  - [`P10_5_INSTITUTIONAL_PROTOCOL_PACKAGE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_5/P10_5_INSTITUTIONAL_PROTOCOL_PACKAGE.md) (Gate P503)
  - [`P10_5_PARTNER_ONBOARDING_WORKFLOW.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_5/P10_5_PARTNER_ONBOARDING_WORKFLOW.md) (Gate P504)
  - [`P10_5_DATA_ACQUISITION_READINESS.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_5/P10_5_DATA_ACQUISITION_READINESS.md) (Gate P505)
  - [`P10_5_ANNOTATION_QUALITY_CONTROL.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_5/P10_5_ANNOTATION_QUALITY_CONTROL.md) (Gate P506)
  - [`P10_5_PILOT_DASHBOARD_EVIDENCE_EXPORT.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_5/P10_5_PILOT_DASHBOARD_EVIDENCE_EXPORT.md) (Phase G)
  - [`P10_5_FINAL_ACCEPTANCE_MATRIX.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_5/P10_5_FINAL_ACCEPTANCE_MATRIX.md) (Comprehensive Matrix)
  - [`P10_5_ENGINEERING_HANDOFF.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_5/P10_5_ENGINEERING_HANDOFF.md) (This document)

---

## 3. Operational Runbook & How-To Guides

### 3.1 Executing Automated Tests
To run the full regression test suite (non-playwright):
```powershell
cd D:\5Projects\msk-therapy-os
python -m pytest -m "not playwright" -q
```
Expected result: `727 passed`.

To run the full Playwright E2E browser test suite:
```powershell
cd D:\5Projects\msk-therapy-os
python -m pytest -m "playwright" -q
```
Expected result: `17 passed`.

Total automated tests: `744 passed in ~4 minutes`.

### 3.2 Launching the Local Server & Viewing the Pilot Readiness Studio
```powershell
cd D:\5Projects\msk-therapy-os
python -m msk_therapy_os.server --host 127.0.0.1 --port 8000
```
1. Open a modern web browser to `http://127.0.0.1:8000/atlas/meridians`.
2. Locate the QA Studio control toolbar on the left panel.
3. Click the **"Check Pilot Readiness (P10.5)"** button.
4. Verify the label displays: `READY FOR ONBOARDING (BLOCKED_EXTERNAL_DATA, 0/3 Partners Active)`.

### 3.3 Registering a Prospective Research Institution
```python
from msk_therapy_os.partner_onboarding import InstitutionalOnboardingManager

mgr = InstitutionalOnboardingManager("msk_therapy_os.sqlite3")
profile = mgr.register_prospective_institution(
    institution_id="INST-CHARITE",
    legal_name="Charité - Universitätsmedizin Berlin",
    country="Germany",
    primary_pi_name="Prof. Dr. med. Christian Meier",
    primary_pi_email="c.meier@charite.de",
    radiology_lead_name="Dr. med. Elena Becker",
    data_custodian_id="CUST-CHARITE-PACS-01",
    protocol_version="v1.0-P10.5",
)
print(f"Registered institution in status: {profile.status.value}")
```

### 3.4 Ingesting and Quarantining Real-World DICOM Data
```python
from msk_therapy_os.real_world_intake_controller import RealWorldIntakeController

controller = RealWorldIntakeController()
record = controller.register_incoming_dataset(
    dataset_id="DS-EXT-CHARITE-001",
    institution_id="INST-CHARITE",
    cohort_id="COHORT_A_ABDOMEN",
    is_synthetic=False,
    dua_id="DUA-CHARITE-2026-01",
    irb_number="EA4/092/26",
    irb_expiration_iso="2027-10-30",
    deid_attestation_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    pixel_phi_screened=True,
    raw_manifest_json='{"series_count": 10, "slice_count": 2500}',
)

# Step 1: Move to quarantine sandbox
record = controller.transition_to_quarantine(record.dataset_id, operator_id="DATA-STEWARD-01")

# Step 2: Dual administrative signoff
record = controller.authorize_quarantined_dataset(
    record.dataset_id,
    admin1_id="CHIEF-MEDICAL-OFFICER",
    admin2_id="DATA-PROTECTION-OFFICER",
)
```

### 3.5 Processing Double-Blind Annotations & Adjudication
```python
from msk_therapy_os.annotation_qc import (
    AnnotationQualityControlEngine,
    RawLandmarkCoordinate,
)

coord_a = RawLandmarkCoordinate(
    observer_id="OBS-RAD-01",
    observer_qualification="Board-Certified Radiologist",
    lps_coordinates_mm=(12.0, -45.0, 108.0),
    timestamp_utc="2026-10-30T10:00:00Z",
    is_blinded=True,
)

coord_b = RawLandmarkCoordinate(
    observer_id="OBS-ANAT-02",
    observer_qualification="Senior Anatomist",
    lps_coordinates_mm=(12.5, -45.8, 107.5),
    timestamp_utc="2026-10-30T11:00:00Z",
    is_blinded=True,
)

pair = AnnotationQualityControlEngine.process_annotation_pair(
    subject_id="SUBJ-CHARITE-001",
    cohort_id="COHORT_C_CRANIOFACIAL",
    landmark_id="NASION",
    coord_a=coord_a,
    coord_b=coord_b,
    landmark_category="CRANIAL_OSSEOUS",
)

print(f"QC Status: {pair.qc_status.value}, Consensus: {pair.final_consensus_lps_mm}")
```

---

## 4. Operational Invariants & Red Lines

All operators, clinical research coordinators, and engineering maintainers MUST obey the following non-negotiable invariants:
1. **Never override Scientific Gate G14**:
   - `G14` must remain `BLOCKED_EXTERNAL_DATA` until physical DICOM scans from external institutions are ingested and evaluated under executed DUA and approved IRB.
2. **Never promote synthetic test fixtures to empirical status**:
   - Synthetic fixtures are barred from empirical quarantine or validation pipelines (`SyntheticPromotionBlockedError`).
3. **Never present model coordinates to human annotators**:
   - Double-blind observers must place landmarks without visual or numerical prompting.
4. **Never provide clinical puncture depth guidance**:
   - The system is an anatomical research atlas; needle/puncture depth guidance is strictly prohibited (`clinical_depth_guidance_allowed: False`).
5. **Never commit directly to `main`**:
   - All work remains on `feat/p9.4-definitive-meridian-atlas-correction`.

---

## 5. Next Milestone Horizon (P10.6+)

With milestone P10.5 completed:
- **P10.6**: Activation of first institutional pilot upon receipt of executed external DUA and IRB waiver/approval.
- **P10.7**: Ingestion of real-world Cohort A/B/C DICOM datasets into the secure quarantine staging environment.
- **P10.8**: Double-blind annotation execution by board-certified radiologists.
- **P10.9**: Cryptographic locking of 30% holdout subjects and external independent biostatistical analysis.
- **P10.10**: Formal evaluation of Scientific Gate G14 lifting.
