# P13: ENGINEERING HANDOFF & OPERATIONS MANUAL
## Musculoskeletal Therapy OS (MSK-Therapy-OS) — Milestone P13
### Open-Source Anatomy & Biomechanics Studio · System Operations · Maintainer Guide

- **Milestone:** P13 (Open-Source Anatomy & Functional Biomechanics Integration)
- **Document ID:** `1docs/audits/P13/P13_ENGINEERING_HANDOFF.md`
- **Branch:** `feat/p13-interactive-msk-education-studio`
- **Baseline Commit:** `3ed2495`
- **Audit Date:** 2026-10-30
- **Auditor:** Principal Software Architect & Release Engineer
- **Status:** APPROVED & HANDOFF READY

---

## 1. COMPONENT DIRECTORY MAP

Milestone P13 introduces the following modular assets and services into MSK-Therapy-OS:

```text
msk-therapy-os/
├── msk_therapy_os/
│   ├── biomechanics_adapter.py               <-- OpenSim parser, interpolation, coordinate validator
│   ├── server.py                             <-- Updated MIME types (.glb) & routes (/education/, API)
│   ├── data/
│   │   └── biomechanics/
│   │       └── sample_shoulder_elevation.mot  <-- Reference OpenSim motion kinematics dataset
│   └── static/
│       ├── atlas/
│       │   └── index.html                    <-- Navigation bridge linking to /education/
│       └── education/
│           ├── index.html                    <-- Isolated Education Studio UI shell
│           ├── anatomy_viewer.js             <-- Three.js r160 viewer, raycaster & lifecycle manager
│           ├── shoulder_lab.js               <-- Interactive 6-stage curriculum & posture lab
│           ├── LICENSE-MODEL.md              <-- CC BY-SA 2.1 JP model license notice
│           ├── models/
│           │   └── anatomy.glb               <-- BodyParts3D/Z-Anatomy derivative mesh (8.86 MB)
│           └── vendor/
│               └── three/                    <-- Localized Three.js r160 ES6 modules & addons
├── tests/
│   ├── test_p13_biomechanics_adapter.py      <-- 15 unit & integration tests
│   └── test_p13_education_playwright.py     <-- Playwright E2E browser test with visual screenshots
└── 1docs/audits/P13/
    ├── P13_A_ARCHITECTURE_AUDIT.md
    ├── P13_B_OPEN_SOURCE_FEASIBILITY.md
    ├── P13_B_ASSET_PROVENANCE_REGISTER.md
    ├── P13_B_LICENSE_COMPATIBILITY.md
    ├── P13_B_ARCHITECTURE_DECISION.md
    ├── P13_C_VIEWER_INTEGRATION.md
    ├── P13_D_BIOMECHANICS_ADAPTER.md
    ├── P13_D_ANATOMICAL_MODEL_MAPPING.md
    ├── P13_E_SHOULDER_LESSON.md
    ├── P13_E_MEDICAL_EVIDENCE_REGISTER.md
    ├── P13_F_HARDWARE_BENCHMARK.md
    ├── P13_F_REGRESSION_REPORT.md
    ├── P13_FINAL_ACCEPTANCE_MATRIX.md
    ├── P13_ENGINEERING_HANDOFF.md
    └── screenshots/
        └── 01_p13_shoulder_education_studio.png
```

---

## 2. SYSTEM OPERATION & USAGE INSTRUCTIONS

### 2.1 Launching the Local Server
From the project root on Windows x64:
```powershell
python -m msk_therapy_os serve --port 8000
```

### 2.2 Navigating to the Studio
- **Education Studio Directly:** Navigate your browser to `http://localhost:8000/education/`.
- **From Clinical Workstation:** Navigate to `http://localhost:8000/atlas/` and click the **"🎓 Edu Studio"** button on the top navigation bar or the **"🎓 Education"** tab on the sidebar.

### 2.3 Running the Verification Suites
- **Unit and Integration Tests:**
  ```powershell
  python -m pytest tests/test_p13_biomechanics_adapter.py -v
  ```
- **Playwright Browser Test:**
  ```powershell
  python -m pytest tests/test_p13_education_playwright.py -v
  ```
- **Full Non-Playwright Regression Test Suite:**
  ```powershell
  python -m pytest tests/ -m "not playwright" -q
  ```

---

## 3. IMMUTABLE SYSTEM BOUNDARIES & GOVERNANCE

Any future modifications or extensions must honor the following invariants:

1. **Gate G14 Protection:**
   The educational studio is an isolated teaching aid. It must NEVER be used to bypass or satisfy `G14 = BLOCKED_EXTERNAL_DATA`.
2. **Clinical Record Isolation:**
   Educational slider interactions, muscle tone adjustments, or posture scores must NEVER write to patient tables in `therapy.db`, alter SOAP notes, or overwrite objective ROM records.
3. **Attribution Preservation:**
   If `anatomy.glb` is updated, the CC BY-SA 2.1 Japan notices for DBCLS BodyParts3D and Z-Anatomy must be maintained in the UI footer and documentation.
