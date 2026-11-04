cat << 'EOF' > /tmp/msk-therapy-os-p17-roadmap-prompt.md
# MSK-Therapy-OS: Milestone P17 Architecture & Feature Upgrade Roadmap (Ask-a-Pro Packet)

## Goal
Conduct an independent principal systems architecture review, clinical safety boundary audit, and concrete engineering roadmap for upgrading **MSK-Therapy-OS** following the successful delivery and functional verification of **Milestone P17 (Real Functional Acceptance, Interactive Biomechanics Repair & Scientific UI Integrity)**.

---

## Attached Source of Truth (`msk-therapy-os-p17-roadmap-source.zip`)
- **System Specifications & Core Architecture:**
  - `README.md`, `1docs/SPEC.md`, `1docs/ARCHITECTURE.md`: Architectural principles, hardware constraints, evidence gates, and verification baseline.
  - `1docs/EVIDENCE.md`: 4-tier evidence library (WHO, NICE, IFOMPT, FDA, BodyParts3D 4.0, Z-Anatomy, Dien Chan Academy).
  - `1docs/specs/`: Specifications for anatomical meridian engine, 3D facial reflexology atlas, and OpenSim biomechanics adapter.
- **Authoritative Milestone Delivery & Acceptance Reports:**
  - `1docs/audits/P17/P17_EXECUTIVE_RELEASE_SUMMARY.md` & `1docs/audits/P17/P17_FINAL_ACCEPTANCE_MATRIX.md`: Complete P17 release ledger closing out all UI-renderer pipeline repairs, honest muscle modes (A/B/C/D), camera viewpoints, and Playwright verification.
  - `1docs/audits/P17/P17_MUSCLE_MODES_ACCEPTANCE.md` & `P17_RENDERER_STATE_VERIFICATION.md`: Forensics and implementation details of Mode A (cyan/amber/purple roles), Mode B (geometric limits banner), Mode C (OpenSim heatmap activation), and Mode D (force unavailable honesty).
  - `1docs/audits/P16/`, `P15/`, `P14/`, `P13/`: Cervicothoracic biomechanics, Forward Head Posture (FHP), Janda's Upper Crossed Syndrome (UCS), Scapulohumeral rhythm, and muscle mechanics inspector.
  - `p10_0_milestone_delivery_report.md` & `1docs/M282_FINAL_ACCEPTANCE_MATRIX.md`: Clinical safety gating, offline PBKDF2 authentication, verified supervisor registry, and native SQLite backup restore.
- **Core Backend Engine (`msk_therapy_os/` - Pure Python Standard Library + SQLite):**
  - `biomechanics_adapter.py`: Skeletal kinematics calculation, cervical moment arm & shear force derivations, muscle recruitment role mapping, OpenSim data loaders.
  - `anatomical_registration.py`, `landmark_registry.py`, `cun_scaling.py`: Parametric skeletal landmark registration and individual proportional cun scaling.
  - `meridian_route_graph.py` & `meridian_surface_engine.py`: 14 classical meridian topological graphs and B-spline surface projection engine.
  - `points.py` & `point_localization_rules.py`: 361 WHO classical acupoint localizations, raycast picking, and SQLite persistence.
  - `dien_chan/`: 3D facial reflexology atlas, 2D-to-3D landmark projection, and clinical condition protocol search.
  - `safety.py`: Rule-based screening for 12 clinical red flags, FDA electrical contraindications, and spinal manipulation ban.
  - `soap.py` & `clinical_proms.py`: Student draft -> instructor supervisory approval workflow, NDI, QuickDASH, RMDQ scoring, and CTCAE adverse event surveillance.
  - `tracking.py`: Longitudinal visit chronology and HL7 FHIR R4 Bundle export.
  - `auth.py`: PBKDF2-HMAC-SHA256 offline authentication, 8-hour sessions, and verified reviewer registry.
  - `server.py`: Zero-pip HTTP server with CORS/CSRF enforcement, REST endpoints, and atlas/education static asset serving.
- **Frontend & WebGL Studio (`msk_therapy_os/static/` - Vanilla HTML5/CSS/WebGL/JS, zero npm):**
  - `education/`: Three.js WebGL Education Studio (`anatomy_viewer.js`, `shoulder_lab.js`, `index.html`), 10 curriculum stages, kinematics scrubber, camera viewpoints, and muscle mechanics inspector.
  - `atlas/`: Open Anatomy 3D Atlas, adaptive marker scaling, and Dien Chan overlay.
- **Verification Suites (`tests/`):**
  - 806 unit and integration test cases across safety, auth, database, biomechanics, and FHIR export.
  - 24 automated Playwright browser test files verifying real DOM, camera, and WebGL rendering state.
- **One-Click Launchers:**
  - `start_app.py`, `start_studio.bat`, `create_desktop_shortcut.py`.

---

## Context and Constraints
1. **Target Hardware Baseline:** Windows 64-bit, Intel Core i7-5600U @ 2.60GHz, 8 GB RAM, Intel HD 5500 integrated graphics, 256 GB SSD. Smooth WebGL rendering (>30 FPS) without dedicated GPU or external cloud dependencies is mandatory.
2. **Zero-Dependency Philosophy:**
   - Backend: Strictly pure Python standard library + SQLite (zero pip dependencies).
   - Frontend: Vanilla HTML5 / CSS / WebGL / ES6 JavaScript (zero npm, zero bundler).
3. **Medical Device & Clinical Governance Boundaries:**
   - MSK-Therapy-OS is a **learning, clinical documentation, and longitudinal cohort tracking platform**.
   - It is **strictly NOT an autonomous diagnostic tool or automated treatment planner** under FDA 2022 CDSS guidance or EU MDR Rule 11.
   - Prohibited behaviors: No automated differential diagnosis, no autonomous electrical dosage prescription, no high-velocity thrust manipulation recommendations.
   - Clinical Safety Hard Stops: Positive red flags immediately halt manual therapy recommendations and mandate physician referral.
4. **Data Privacy & Integrity:**
   - Offline-first execution. Synthetic identifiers (`DEMO-*`, `PAT-2026-*`).
   - Tamper-evident backups with HMAC-SHA256 authentication and native SQLite backup API restore.

---

## Please do:
1. **Evaluate Current Architectural Maturity & Cohesion:**
   - Review the codebase across Milestones M1 through P17.
   - Assess how well the 3D Biomechanics Education Studio, Anatomical 3D Meridian Atlas, Dien Chan Facial Reflexology, and Clinical Governance (SOAP / PROMs / Red Flags) interoperate.
2. **Clinical Safety & Regulatory CDSS Boundary Review:**
   - Audit the rule-based safety screening, CTCAE adverse event logging, and red-flag hard stops.
   - Provide concrete guidance on how to introduce guided educational learning, interactive tutoring, or case summarization without crossing into regulated SaMD (Class II/III medical device).
3. **Hardware & WebGL Performance Audit (Intel HD 5500):**
   - Review the WebGL pipeline, shader complexity, buffer pooling, and draw call management across `anatomy_viewer.js` and `meridians.js`.
   - Identify any performance traps or memory leak vectors when running continuous 60 FPS skeletal animations.
4. **Prioritized Feature Upgrade Roadmap (P18 - M7+):**
   - Evaluate and architect the next high-value upgrades:
     - **Feature A: 3D Virtual Goniometer & Interactive ROM Angle Arc Measurement Tool** (allowing students/practitioners to measure, manipulate, and log 3D joint angles directly in the WebGL scene).
     - **Feature B: Automated Offline PDF Clinical Case Report & Patient Education Leaflet Generator** (zero-pip or lightweight standalone generation of multi-page clinical summaries and exercise handouts).
     - **Feature C: Client-Side Offline Camera-Based Posture Screening** (evaluating feasibility of lightweight, offline pose landmark extraction for Forward Head Posture / Upper Crossed Syndrome intake).
     - **Feature D: Bi-directional FHIR R4 Interoperability & Sync Adapter** (expanding beyond current one-way JSON export to synchronize with open-source EHR servers like Medplum or HAPI FHIR).
5. **Concrete Technical Specifications for the Top 2 Upgrades:**
   - Provide full SQLite DDL, Python dataclass definitions, REST API contracts, and WebGL implementation strategies for the top 2 recommended upgrades.
6. **Actionable Implementation Sprints:**
   - Break down the top 2 upgrades into concrete engineering sprints with explicit acceptance criteria, safety gates, and automated test plans.

---

## Output Format
Deliver a comprehensive, decision-ready report structured as follows:
1. **Executive Architecture & Maturity Scorecard** (Grade by subsystem: Biomechanics Studio, Anatomical Atlas, Clinical Workflow, Security/RBAC, Performance/Hardware).
2. **Comprehensive Milestone Progression Ledger** (M1 through P17 status, capabilities, and verified evidence).
3. **Detailed Gap & Risk Analysis** (Table: `Subsystem | Current State | Risk / Gap | Recommended Solution`).
4. **Prioritized Feature Upgrade Roadmap (P18 - M7+)** (Table: `Upgrade | Clinical / Educational Value | Technical Complexity | Regulatory SaMD Risk | Acceptance Gate`).
5. **Concrete Technical Specifications for the Top 2 Upgrades** (SQLite DDL, Python dataclasses, API contracts, WebGL shaders/pipeline).
6. **Limitations & Exact Local Reproduction Commands** (List unverified assumptions and provide executable commands for local verification).

---

## Tail
Assume the attached `msk-therapy-os-p17-roadmap-source.zip` is the source of truth.
Tell me exactly which module should be modified first to implement the 3D Virtual Goniometer without breaking P17 backward compatibility.
EOF

# Copy prompt to Windows Desktop and Linux Desktop
cp /tmp/msk-therapy-os-p17-roadmap-prompt.md /mnt/c/Users/tuanh/Desktop/msk-therapy-os-p17-roadmap-prompt.md
cp /tmp/msk-therapy-os-p17-roadmap-prompt.md /home/tuan/Desktop/msk-therapy-os-p17-roadmap-prompt.md

ls -lh /mnt/c/Users/tuanh/Desktop/msk-therapy-os-p17-roadmap*
