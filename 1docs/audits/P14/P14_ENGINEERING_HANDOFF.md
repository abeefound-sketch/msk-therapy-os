# P14 Engineering Handoff & Architecture Guide

**Milestone:** P14 — Evidence-Grounded Dynamic Biomechanics, Muscle Recruitment Visualization & Interactive MSK Education  
**Date:** October 31, 2026  
**Auditor / Architect:** Principal Systems Architect & Lead Biomechanics Engineer  
**Branch:** `feat/p14-evidence-grounded-biomechanics-studio`  
**Status:** VALIDATED  

---

## 1. System Overview & Component Topology

Milestone P14 extends MSK-Therapy-OS with an evidence-grounded, dynamic 3D biomechanics simulation and education studio. The platform integrates authentic human anatomy from BodyParts3D v4.0 with validated multi-body OpenSim kinematics (Seth et al. 2016, 2019).

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        MSK-Therapy-OS Workstation                      │
│                                                                        │
│  ┌───────────────────────┐              ┌───────────────────────────┐  │
│  │   /atlas/ Clinical    │              │  /education/ Biomechanics │  │
│  │   Acupoint Workstation│              │  & Posture Studio (P14)   │  │
│  └───────────────────────┘              └─────────────┬─────────────┘  │
│                                                       │                │
│  ┌────────────────────────────────────────────────────▼─────────────┐  │
│  │                  Three.js r160 Kinematic Scene Graph             │  │
│  │                                                                  │  │
│  │   [Thorax] ──► [SC Pivot] ──► [Clavicle_R]                       │  │
│  │                       └──► [AC Pivot] ──► [Scapula_R]            │  │
│  │                                    └──► [GH Pivot] ──► [Humerus] │  │
│  └────────────────────────────────────────────────────▲─────────────┘  │
│                                                       │                │
│  ┌────────────────────────────────────────────────────┴─────────────┐  │
│  │                     OpenSim Data Engine (P14)                    │  │
│  │                                                                  │  │
│  │   • seth_shoulder_elevation.mot  (Coordinates, 0° to 120°)       │  │
│  │   • seth_shoulder_elevation.sto  (Static Optimization Muscle Act)│  │
│  │   • illustrative_rounded_elevation.mot (Posture Comparison)      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & File Manifest

### 2.1 3D Anatomical Assets
- `msk_therapy_os/static/education/models/shoulder_skeleton.glb` (386,856 bytes, SHA-256: `8b0a984c2a16b5745872b42ddc4e2b7dbbac02031cbe7324108b31b8af921cb4`): Contains authentic CT-derived osseous geometry for Thorax, Clavicle_R, Scapula_R, and Humerus_R.
- `msk_therapy_os/static/education/models/anatomy.glb` (8,866,748 bytes): Contains 255 muscular meshes comprising 54 anatomical muscle groups.

### 2.2 Biomechanical Data Fixtures
- `msk_therapy_os/data/biomechanics/seth_shoulder_elevation.mot`: Standardized OpenSim 4.0 motion file ($0^\circ \to 120^\circ$ humeral elevation).
- `msk_therapy_os/data/biomechanics/seth_shoulder_elevation.sto`: Static optimization muscle activations for Deltoids, Supraspinatus, Serratus Anterior, Trapezius, etc.
- `msk_therapy_os/data/biomechanics/illustrative_rounded_elevation.mot`: Synthetic altered kinematics illustrating persistent anterior tilt.
- Static mirror: `msk_therapy_os/static/education/data/` for offline HTTP client consumption.

### 2.3 Core Application Source Files
- `msk_therapy_os/biomechanics_adapter.py`: Python adapter with `OpenSimFormatParser`, `BiomechanicalScenarioManifest`, `ShoulderKinematicsValidator`, and bilingual `get_shoulder_education_curriculum()`.
- `msk_therapy_os/server.py`: Hardened local HTTP server with `/api/education/shoulder-lesson`, MIME type handling for `.mot`, `.sto`, `.glb`, and static asset streaming.
- `msk_therapy_os/static/education/anatomy_viewer.js`: Three.js r160 viewer managing the forward kinematic scene graph, timeline interpolation, muscle colormaps, and WebGL context lifecycle.
- `msk_therapy_os/static/education/shoulder_lab.js`: Studio UI controller managing the 8-stage curriculum, interactive 4-question quiz, dual-language switching, and dynamic angle/activation displays.
- `msk_therapy_os/static/education/index.html`: Responsive 3-column educational workspace with floating motion playback bar and scientific watermark banners.

---

## 3. Operational & Maintenance Directives

### 3.1 Running the Studio Offline
Start the workstation server:
```bash
python -m msk_therapy_os.server --port 8000
```
Open a browser to:
- P14 Advanced Biomechanics Studio: `http://localhost:8000/education/?v=p14`
- P13 Baseline Compatibility Mode: `http://localhost:8000/education/`
- Clinical Acupoint Atlas: `http://localhost:8000/atlas/`

### 3.2 Adding New Biomechanical Scenarios
To register an additional motion trajectory (e.g. abduction in frontal plane or external rotation):
1. Place validated `.mot` and `.sto` files into `msk_therapy_os/data/biomechanics/` and `msk_therapy_os/static/education/data/`.
2. Compute file SHA-256 hashes.
3. Append a `BiomechanicalScenarioManifest` record to `get_scenario_catalog()` in `msk_therapy_os/biomechanics_adapter.py`.
4. Ensure validation level is accurately marked (`ILLUSTRATIVE` or `OPENSIM_MODEL_GENERATED`).
5. Add `<option>` entry to `#scenario-select` in `index.html`.

---

## 4. Scientific Boundaries & Non-Negotiable Invariants

All future maintainers must preserve:
```python
G14 == "BLOCKED_EXTERNAL_DATA"
CLINICAL_DEPTH_GUIDANCE_ALLOWED is False
RELEASE_SCOPE == "ENGINEERING_RESEARCH_ONLY"
CLINICAL_VALIDATION == "NOT_ESTABLISHED"
```
No clinical diagnosis may be rendered from visual posture or rhythm ratios. All model predictions must retain explicit disclaimers:
`MATHEMATICAL MODEL ESTIMATE — NOT MEASURED EMG`.
