# P15 Engineering Handoff & Architecture Notes

**Milestone:** P15 — Cervicothoracic Biomechanics, Forward Head Posture & Upper Crossed Syndrome Studio  
**System:** MSK-Therapy-OS  
**Scope:** Engineering & Biomechanical Education / Research  
**Release Gate:** `ENGINEERING_RESEARCH_ONLY`  
**Clinical Status:** `CLINICAL_VALIDATION: NOT_ESTABLISHED`  
**Target Branch:** `feat/p15-cervicothoracic-biomechanics-studio`  

---

## 1. Architectural Enhancements Summary

Milestone P15 extends MSK-Therapy-OS from an isolated shoulder biomechanics environment (P13/P14) into a **coupled cervicothoracic and shoulder girdle kinematic and neuromuscular platform**.

### Key Deliverables:
1. **Unified 3D Skeletal Asset:**
   `msk_therapy_os/static/education/models/cervicothoracic_skeleton.glb` (1.54 MB)
   - Merges BodyParts3D C1–C7, T1–T4, Occiput/Cranium, Clavicle, Scapula, Humerus, Levator Scapulae, and Suboccipital muscle groups.
   - Preserves 9 named scene graph nodes for independent kinematic transform manipulation.
2. **Dynamic Biomechanical Engine:**
   - Integrated in `msk_therapy_os/biomechanics_adapter.py`:
     - `calculate_cervicothoracic_posture(forward_head_mm, cva_deg, rounded_shoulder_pct)`
     - Models coupled cranial moment arm growth ($d = d_0 + \Delta d$), gravitational moments ($M = W \cdot d$), and extensor holding forces ($F_{\text{ext}} = M / d_{\text{internal}}$).
     - Incorporates Janda's reciprocal inhibition colormapping.
3. **OpenSim Biomechanical Motion & Storage Datasets:**
   - `vasavada_cervical_flexion_extension.mot/.sto` (OpenSim standard format, 21 frames).
   - `illustrative_forward_head_posture.mot/.sto` (OpenSim standard format, 21 frames).
4. **Three.js Kinematic Animation & Visualization:**
   - Dynamic pivots for C7–T1 base, Atlanto-axial (AA), and Atlanto-occipital (AO) joints in `anatomy_viewer.js`.
   - Real-time muscle activation heatmaps across SCM, Scalenes, Splenius, Suboccipital, Levator Scapulae, Upper/Lower Trapezius, and Serratus Anterior.
5. **Interactive Educational Curriculum & Self-Assessment:**
   - 8-stage interactive lesson detailing the clinical paradox of neck-shoulder pain recurrence, suboccipital spindle density, Janda's UCS, and DNF motor re-education.
   - 4-question interactive comprehension quiz with real-time feedback.

---

## 2. File Organization & Paths

```text
D:\5Projects\msk-therapy-os\
├── msk_therapy_os/
│   ├── biomechanics_adapter.py       # Cervicothoracic math, scenarios, curriculum
│   ├── server.py                     # API routing for cervicothoracic lesson
│   ├── data/biomechanics/            # Canonical .mot / .sto storage
│   │   ├── vasavada_cervical_flexion_extension.mot
│   │   ├── vasavada_cervical_flexion_extension.sto
│   │   ├── illustrative_forward_head_posture.mot
│   │   └── illustrative_forward_head_posture.sto
│   └── static/education/
│       ├── anatomy_viewer.js         # Three.js scene hierarchy, pivots, colormaps
│       ├── shoulder_lab.js           # Lab controller, scenario switching, quiz UI
│       ├── index.html                # Cervical controls, metric readouts, bars
│       ├── models/
│       │   └── cervicothoracic_skeleton.glb # 1.54 MB unified GLB
│       └── data/                     # Web-accessible mirrors of .mot / .sto files
├── tests/
│   ├── test_p15_cervicothoracic_adapter.py # 10 unit tests for P15 backend logic
│   └── test_p15_cervical_playwright.py     # Playwright E2E browser tests
└── 1docs/audits/P15/                 # Audit reports, kinematic analysis, screenshots
    ├── P15_BASELINE_VERIFICATION.md
    ├── P15_CERVICOTHORACIC_ASSET_AUDIT.md
    ├── P15_CERVICAL_KINEMATIC_CHAIN.md
    ├── P15_JANDA_UPPER_CROSSED_SYNDROME.md
    ├── P15_EVIDENCE_REGISTER_REVIEW.md
    ├── P15_FINAL_ACCEPTANCE_MATRIX.md
    ├── P15_ENGINEERING_HANDOFF.md
    ├── P15_EXECUTIVE_RELEASE_SUMMARY.md
    └── screenshots/
        ├── 01_p15_cervicothoracic_biomechanics_studio.png
        └── 02_p15_forward_head_kinematics.png
```

---

## 3. Maintenance Instructions & Extension Guide

### Adding New Muscle Pathways
To incorporate additional muscular structures (e.g., Rhomboids or Pectoralis Minor) into the 3D model:
1. Extract authentic BodyParts3D parts using `extract_parts_from_chunks()` in a scratch script.
2. Ensure consistent meters-scale and coordinate registration ($Y$-up, origin at thorax/pelvis base).
3. Assign mesh to named node in the GLB scene hierarchy.
4. Add corresponding muscle channel to `OpenSimMuscleActivation` and register entry in `_applyMuscleActivationColors()` in `anatomy_viewer.js`.

### Retaining Invariants
Under no circumstances should user input from webcam or phone camera be tied to a clinical diagnosis without passing through the locked G14 institutional review pipeline. All educational modules must explicitly preserve `ENGINEERING_RESEARCH_ONLY` headers.
