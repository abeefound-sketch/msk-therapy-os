# P16 Audit: Engineering Handoff & Maintenance Guide

**Milestone:** P16 — Scientific Biomechanics Integrity, Muscle Mechanics & Interactive Self-Education Studio  
**Date:** 2026-10-31  
**Status:** AUDITED AND CERTIFIED  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Classification:** `ENGINEERING_RESEARCH_ONLY`  
**Gate G14 Status:** `BLOCKED_EXTERNAL_DATA`

---

## 1. Codebase Modifications Overview

The transition from P15 to P16 introduced the following key engineering updates across the repository:

1. **`msk_therapy_os/biomechanics_adapter.py`:**
   - Implemented `calculate_cervical_gravitational_mechanics`: Disambiguates $W_{\text{head}}$, $d_{\text{horizontal}}$, $M_{\text{gravity}}$, $r_{\text{eff}}$, $F_{\text{extensor}}$, and $R_{\text{comp}}$. Explicitly reports `TISSUE_STRESS_MODEL_UNAVAILABLE`.
   - Updated `calculate_cervicothoracic_posture`: Integrates explicit physics calculations while preserving backward compatibility for P15 callers.
   - Implemented `MuscleMechanicsChannel` and `MUSCLE_CATALOG`: 14 comprehensive muscle entries across shoulder and cervicothoracic regions.
   - Implemented `get_muscle_mechanics_inspection`: Supports Modes A, B, C, D with mandatory empty states `MODEL_GEOMETRY_INSUFFICIENT` and `MUSCLE_FORCE_NOT_AVAILABLE`.
   - Implemented `compare_scenarios`: Side-by-side scenario kinematics and gravitational deltas.
   - Implemented `get_provenance_manifest`: Full cryptographic SHA-256 provenance for all 7 biomechanics datasets and `OPENSIM_LIVE_SIMULATION_BLOCKED` status.
   - Implemented `get_unified_education_curriculum`: 10-topic unified MSK curriculum, 5-question bilingual quiz, 3 red flag groups, and EV-01..EV-20 evidence register.
2. **`msk_therapy_os/server.py`:**
   - Added REST routing for `/api/education/unified-curriculum`, `/api/education/p16-curriculum`, `/api/education/provenance-manifest`, `/api/education/muscle-mechanics`, `/api/education/compare-scenarios`, `/api/education/cervical-mechanics`.
3. **`msk_therapy_os/static/education/anatomy_viewer.js`:**
   - Added multi-axis cervical rotation (C1-C2 axial rotation around Y, lower cervical rotation around Y, lateral bending around Z).
   - Refactored `_setupSkeleton` mesh collection into an array prior to iteration to prevent `scene.children` mutation errors during pivot parenting.
   - Expanded muscle activation colormapping for rotational and lateral bending muscle channels.
4. **`msk_therapy_os/static/education/index.html`:**
   - Integrated `#region-select` dropdown in top navigation.
   - Added new cervical rotational and lateral bending scenarios to `#scenario-select`.
   - Added Mode A, B, C, D and Comparison mode buttons.
   - Added `#cervical-metrics-group` with separated physical entity readouts.
   - Integrated `#comparison-card` and `#red-flags-card`.
5. **`msk_therapy_os/static/education/shoulder_lab.js`:**
   - Added P16 mode handling, unified 10-topic curriculum rendering, mode switching, comparison card rendering, and region toggling.
6. **Datasets (`msk_therapy_os/data/biomechanics/` and static mirror):**
   - Added `cervical_axial_rotation.mot` / `.sto`.
   - Added `cervical_lateral_bending.mot` / `.sto`.
7. **Test Suites:**
   - Added [`tests/test_p16_biomechanics_integrity.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p16_biomechanics_integrity.py) (12 tests).
   - Added [`tests/test_p16_playwright.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p16_playwright.py) (1 Playwright E2E test).

---

## 2. Local Verification Commands

To reproduce the full test suite and verify Milestone P16:

```bash
# 1. Activate project directory
cd D:\5Projects\msk-therapy-os

# 2. Run P16 Biomechanics Integrity Unit Tests
pytest tests/test_p16_biomechanics_integrity.py

# 3. Run all adapter unit tests (P13, P14, P15, P16)
pytest tests/test_p13_biomechanics_adapter.py tests/test_p14_biomechanics_adapter.py tests/test_p15_cervicothoracic_adapter.py tests/test_p16_biomechanics_integrity.py

# 4. Run all interactive browser Playwright tests
pytest tests/test_p13_education_playwright.py tests/test_p14_motion_playwright.py tests/test_p15_cervical_playwright.py tests/test_p16_playwright.py

# 5. Run complete non-Playwright regression suite (806 tests)
pytest -m "not playwright"
```

---

## 3. Deployment & Production Boundaries

When deploying or demonstrating the MSK-Therapy-OS Education Studio:
- **Never bypass Gate G14:** Remote data ingestion remains blocked (`BLOCKED_EXTERNAL_DATA`).
- **Never enable live clinical depth guidance:** Guidance remains locked to `False`.
- **Never claim medical certification:** Software is labeled `ENGINEERING_RESEARCH_ONLY` with `CLINICAL_VALIDATION: NOT_ESTABLISHED`.
- **Maintain offline integrity:** All 3D assets, Three.js libraries, and OpenSim motion datasets must continue to be served from local filesystem paths without internet dependencies.
