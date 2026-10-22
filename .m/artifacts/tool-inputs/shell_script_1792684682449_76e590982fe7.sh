cat << 'EOF' > /tmp/msk-therapy-os-m3-roadmap-prompt.md
# MSK-Therapy-OS: Milestone M3 Architecture & Feature Upgrade Roadmap (Pro Review Packet)

## Goal
Provide an independent principal systems architecture review, clinical safety gap analysis, and concrete implementation roadmap for **Milestone M3 (Multi-Patient Clinical & Longitudinal Cohort Management)** and subsequent feature upgrades (M4 Biomechanics / 3D Kinematics, M5 Fascial Depth Slicing, M6 Interoperability Hub) of **MSK-Therapy-OS**.

---

## Attached source of truth (`msk-therapy-os-m3-roadmap-source.zip`)
- `SPEC.md`, `README.md`, `ENGINEERING_HANDOFF.md`: Architectural principles, hardware constraints, evidence gates, and verification baseline.
- `docs/M3_IMPLEMENTATION_READINESS.md`: Architecture specification and initial scope for Milestone M3.
- `docs/M282_FINAL_ACCEPTANCE_MATRIX.md`: Complete matrix of closed requirements for M2.8.2 (security, RBAC, SQLite recovery, clinical safety, WebGL draw call forensics).
- `docs/M282_SECURITY_AUTHORIZATION_AUDIT.md` & `docs/M282_CLINICAL_SAFETY_ENFORCEMENT.md`: Security and safety enforcement implementations.
- `docs/M282_SQLITE_RECOVERY_VALIDATION.md` & `docs/M282_WEBGL_PERFORMANCE_FORENSICS.md`: Recovery mechanisms and WebGL performance benchmarks on Intel HD 5500.
- `docs/ARCHITECTURE.md`, `docs/EVIDENCE.md`: 4-tier evidence library, ADRs (ADR-001 through ADR-009).
- `msk_therapy_os/`: Full Python source code (pure standard library + SQLite):
  - `auth.py`: PBKDF2-HMAC-SHA256 authentication, 8-hour sessions, verified reviewer registry.
  - `db.py`: Relational SQLite schema, foreign keys, demo seeders.
  - `safety.py`: Rule-based red flags screening (12 flags, FDA electrical contraindications, spinal manipulation ban).
  - `soap.py`: Student draft -> supervisor approval clinical note workflow.
  - `tracking.py`: Longitudinal visit tracking, session recording, HL7 FHIR R4 bundle export.
  - `points.py`: Custom acupoint authoring, spatial reference overrides, safe database restore.
  - `server.py`: Zero-pip HTTP server, REST endpoints, CORS/CSRF enforcement, atlas data serving.
  - `terminology.py`: Multilingual medical terminology registry (EN, ZH, VI).
- `msk_therapy_os/static/`: Front-end web UI (vanilla HTML5/CSS/JS, zero npm):
  - `index.html`: Interactive body map, clinical note editor, safety gate simulator.
  - `meridianEditor.js`: 3D custom point editor and spatial picking studio.
  - `atlas/`: Authentic 3D WebGL Open Anatomy Atlas integration.
- `tests/`: Automated unit and integration test suites.

---

## Context and constraints
1. **Target Hardware Baseline:** Windows 64-bit, Intel Core i7-5600U @ 2.60GHz, 8 GB RAM, Intel HD 5500 integrated graphics, 256 GB SSD. The application must run smoothly (>30 FPS 3D rendering) on this low-spec hardware without requiring external GPUs or cloud infrastructure.
2. **Zero-Dependency Philosophy:**
   - Backend: Strictly pure Python standard library + SQLite (zero pip dependencies).
   - Frontend: Vanilla HTML5 / CSS / WebGL / ES6 JavaScript (zero npm, zero build step/bundler).
3. **Regulatory & SaMD Scope Boundaries:**
   - MSK-Therapy-OS is a **learning and longitudinal documentation tool** for musculoskeletal therapy, Thai massage, and Dien Chan facial reflexology.
   - It is **strictly NOT an autonomous diagnostic device, treatment planner, or medical device (SaMD)** under FDA 2022 CDSS guidance or EU MDR Rule 11.
   - Prohibited actions: No autonomous differential diagnosis, no high-velocity spinal manipulation directives, no electrical device intensity auto-prescription.
   - Mandatory safety gate: Red flags hard-stop procedure suggestions and mandate specialist referral.
4. **Data Privacy & Governance:**
   - Offline-first operation. All baseline demonstrations use synthetic identifiers (`DEMO-*` or `PAT-2026-*`).
   - Atomic database backups using native SQLite backup API with SHA-256 pre-restore integrity validation.

---

## Please do:
1. **Inspect Attached Source & Architecture:**
   - Review `docs/M3_IMPLEMENTATION_READINESS.md`, `msk_therapy_os/models.py`, `msk_therapy_os/db.py`, `msk_therapy_os/tracking.py`, and `msk_therapy_os/points.py`.
   - Identify architectural gaps, scalability bottlenecks, or missing relational abstractions for transitioning from a single-scenario demo to a multi-patient cohort tracking system.

2. **Milestone M3 Deep Architecture Design:**
   - Design the relational database schema extensions for M3:
     - Multi-patient profiles (`cases` / `patients`) with role-based access isolation.
     - Longitudinal session chronology with pre/post objective measurement deltas ($\Delta\text{ROM}$, $\Delta\text{VAS Pain}$).
     - Standardized Patient-Reported Outcome Measures (PROMs: PROMIS-10, Neck Disability Index, QuickDASH).
     - CTCAE-based Adverse Event surveillance logging tied to clinical safety escalation.
   - Provide concrete SQL DDL and Python dataclass definitions compatible with the zero-dependency standard library constraint.

3. **FHIR R4 Interoperability Expansion:**
   - Review the current FHIR export in `msk_therapy_os/tracking.py`.
   - Specify enhancements for exporting multi-patient bundles: `Patient`, `Condition`, `Observation` (pre/post ROM with LOINC/SNOMED-CT codes), `Encounter`, and `DocumentReference` for approved SOAP notes.

4. **Future Milestones Roadmap (M4, M5, M6):**
   - Propose an architectural blueprint for upcoming feature milestones:
     - **Milestone M4: 3D Joint Range-of-Motion & Kinematic Arc Simulation** (rendering dynamic ROM arcs on 3D joint centers in WebGL without performance degradation on Intel HD 5500).
     - **Milestone M5: Anatomical Layer Slicing & Palpation Depth Modeling** (multi-layer visualization: skin -> superficial fascia -> deep muscle -> skeletal structures with discrete opacity control).
     - **Milestone M6: Clinical Research Cohort Analytics & Evidence Synthesis Hub** (offline statistical aggregation of treatment outcomes, anonymized research data export).

5. **Clinical Safety & Regulatory Guardrails:**
   - Conduct a regulatory risk assessment: How to implement educational AI tutoring or guided learning without crossing into regulated SaMD (FDA 2022 CDSS guidance / EU MDR)?
   - Detail the required disclaimers, supervisory sign-off mechanisms, and clinical audit logging.

6. **Actionable Implementation Plan:**
   - Break down Milestone M3 into 3-4 concrete, verifiable work packages (Sprints) with explicit acceptance criteria and automated test strategies.

---

## Output format
Deliver the review with clear, decision-ready sections:
1. **Executive Summary & Architectural Health Assessment**
2. **Comprehensive Gap Analysis Table:**
   `Area | Current Implementation | Milestone M3 Requirement | Architectural Gap | Recommended Solution`
3. **Database Schema & Domain Model Specifications:**
   Concrete SQLite DDL and Python dataclasses for multi-patient management, longitudinal metrics, and adverse events.
4. **FHIR R4 Mapping Specification:**
   Resource structures, LOINC/SNOMED terminology bindings, and bundle assembly logic.
5. **Prioritized Feature Upgrade Roadmap (M3 -> M6):**
   `Milestone / Work Package | Target Capabilities | Technical Complexity | Performance / Regulatory Risk | Acceptance Gate`
6. **WebGL Optimization Strategy for Low-End Intel HD 5500:**
   Draw call management, buffer pooling, and LOD techniques for 3D kinematic overlays.
7. **Limitations & Exact Local Commands:**
   List any unverified assumptions and provide exact local Python/test commands for the local team to run.

---

## Tail
Assume the attached `msk-therapy-os-m3-roadmap-source.zip` is the source of truth.
Tell me exactly which files, schema definitions, and API endpoints should be modified first to launch Milestone M3 without breaking M2.8.2 backward compatibility.
EOF

cp /tmp/msk-therapy-os-m3-roadmap-prompt.md /mnt/c/Users/tuanh/Desktop/msk-therapy-os-m3-roadmap-prompt.md
cp /tmp/msk-therapy-os-m3-roadmap-prompt.md /home/tuan/Desktop/msk-therapy-os-m3-roadmap-prompt.md
ls -lh /mnt/c/Users/tuanh/Desktop/msk-therapy-os-m3-roadmap*
