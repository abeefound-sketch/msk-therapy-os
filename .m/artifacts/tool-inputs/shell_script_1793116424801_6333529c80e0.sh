cat << 'EOF' > /tmp/msk-therapy-os-p9-4-roadmap-prompt.md
# MSK-Therapy-OS: Comprehensive Project Progress Audit & Feature Upgrade Roadmap (Ask-a-Pro Packet)

## Goal
Conduct an independent principal systems architecture review, clinical safety and regulatory boundary audit, and concrete feature upgrade roadmap for **MSK-Therapy-OS** following the completion of Milestone **P9.4 (Definitive Meridian Atlas Correction, Route Topology Validation, and QA Studio)**.

---

## Attached Source of Truth (`msk-therapy-os-p9-4-roadmap-source.zip`)
- **System Specifications & Architecture:**
  - `README.md`, `1docs/SPEC.md`, `1docs/ARCHITECTURE.md`: Foundational constraints, ADRs, module boundaries.
  - `1docs/EVIDENCE.md`: 4-tier evidence governance catalog (WHO, NICE, IFOMPT, FDA, BodyParts3D 4.0, Z-Anatomy, Dien Chan Academy).
  - `1docs/specs/P9_4_REFERENCE_DRIVEN_MERIDIAN_ATLAS.md` & `1docs/specs/P9_3_DYNAMIC_MERIDIAN_SURFACE_ENGINE.md`: Core specs for anatomical meridian reconstruction.
  - `1docs/specs/DIEN_CHAN_FACIAL_3D_ATLAS_SPEC.md`: Specification for 3D facial reflexology integration.
- **Audits & Engineering Handoffs:**
  - `1docs/audits/P9_4_FINAL_ENGINEERING_HANDOFF.md`: Latest handoff detailing P9.4 deliverables and validation results.
  - `1docs/audits/P9_4_14_CHANNEL_VISUAL_ACCEPTANCE.md` & `P9_4_ROUTE_TOPOLOGY_VALIDATION.md`: Topological validation of 14 classical meridians.
  - `1docs/audits/P9_4_361_ACUPOINT_DATA_QUALITY_MATRIX.md`: Complete error matrix and coordinate provenance for 361 WHO classical acupoints.
  - `1docs/audits/DIEN_CHAN_FINAL_HANDOFF.md`: Hand-off for facial reflexology 2D-to-3D registration.
  - `1docs/M282_FINAL_ACCEPTANCE_MATRIX.md` & `1docs/M282_SECURITY_AUTHORIZATION_AUDIT.md`: Security hardening, RBAC, and SQLite recovery audits.
- **Core Backend Engine (`msk_therapy_os/` - Pure Python Standard Library + SQLite):**
  - `meridian_route_graph.py` (66 KB) & `meridian_surface_engine.py` (21 KB): 14-meridian topological routing graph and surface-conforming B-spline interpolation.
  - `point_localization_rules.py` (61 KB) & `points.py` (104 KB): Classical proportional cun localization rules, spatial raycasting, and CRUD persistence.
  - `landmark_registry.py` (27 KB), `cun_scaling.py` (18 KB), `anatomical_registration.py` (17 KB): Parametric skeletal landmark registration and individual cun scaling.
  - `dien_chan/` (Facial registration, annotations, database, and condition protocol search).
  - `kinematics.py` (M4 3D joint range-of-motion arcs and physiological envelope comparison).
  - `tissue_layers.py` (M5 discrete tissue opacity: skin -> fascia -> muscle -> bone, planar slicing).
  - `clinical_proms.py`, `cohort_dashboard.py`, `research_studio.py` (M3/M6 PROMs: NDI/QuickDASH/RMDQ, CTCAE adverse event surveillance, cohort analytics).
  - `auth.py` (39 KB): PBKDF2-HMAC-SHA256 auth, 8h sessions, strict RBAC, verified clinical reviewer registry.
  - `safety.py`: Rule-based screening for 12 clinical red flags, FDA electrical contraindications, and spinal manipulation ban.
  - `soap.py`: Student draft -> instructor supervisory approval clinical note workflow.
  - `tracking.py`: Longitudinal visit chronology, treatment tracking, and HL7 FHIR R4 Bundle export.
  - `server.py` (97 KB): Zero-dependency HTTP server with CORS/CSRF protection, REST APIs, and atlas static serving.
- **Frontend & WebGL Atlas (`msk_therapy_os/static/` - Vanilla HTML5/CSS/WebGL/JS, zero npm):**
  - `atlas/meridians.js`: WebGL shader pipelines, adaptive LOD scaling, meridian route rendering, raycast picking, and Dien Chan projection.
  - `index.html`: Interactive clinical workspace, body map, SOAP editor, and cohort dashboard.
- **Verification Suites (`tests/`):**
  - 36 automated test files spanning units, integration, security, and Playwright E2E visual regressions.

---

## Context and Constraints
1. **Target Hardware Baseline:** Windows 64-bit, Intel Core i7-5600U @ 2.60GHz, 8 GB RAM, Intel HD 5500 integrated GPU, 256 GB SSD. Smooth 3D WebGL rendering (>30 FPS) without dedicated GPU or external cloud dependencies is mandatory.
2. **Zero-Dependency Architecture:**
   - Backend: Strictly pure Python standard library + SQLite (zero pip dependencies).
   - Frontend: Pure vanilla HTML5 / CSS / WebGL / ES6 JavaScript (zero npm, zero bundler).
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
1. **Evaluate Current Multi-Milestone Architectural Maturity:**
   - Review the codebase and documents across Milestones M1 -> M2 -> M2.8.2 -> M3 -> M6 -> P8 -> P9.1 -> P9.4.
   - Assess the architectural cohesion between the anatomical 3D atlas, the Dien Chan facial reflexology engine, the clinical documentation workflow (SOAP/PROMs), and the security/governance layer.
2. **Audit Anatomical & Geometric Precision (P9 - P9.4):**
   - Evaluate the anatomical landmark registration, parametric cun scaling, 361 acupoints localization rules, and 14 canonical meridian route graphs.
   - Identify potential edge cases, lateral symmetry pitfalls, or topological discontinuities in complex regions (e.g., Gallbladder auricular zigzag, Bladder inner/outer lumbar column branching).
3. **Clinical Safety & Regulatory CDSS Compliance:**
   - Audit the rule-based safety screening, CTCAE adverse event logging, and red-flag hard stops.
   - Specify guardrails for introducing interactive AI tutoring or automated case summarization without triggering Class II/III SaMD regulations.
4. **Identify Gaps & Technical Debt:**
   - Analyze potential bottlenecks on low-spec Intel HD 5500 hardware (buffer management, draw call frequency, WebGL context loss).
   - Identify database indexing, schema normalization, or concurrency areas needing refinement.
5. **Formulate a Concrete Feature Upgrade Roadmap:**
   - Propose the next generation of high-value features for MSK-Therapy-OS (e.g., P10 / M7 onwards), evaluating:
     - Automated offline PDF clinical report generator (using standard library or standalone tools).
     - Camera/Photo-based posture landmark extraction (offline client-side without heavy neural networks).
     - Real-time physiological joint articulation & goniometer simulation in WebGL.
     - Multi-lingual terminology expansion and localized patient education leaflets.
     - Bi-directional FHIR R4 server synchronization adapter.
6. **Actionable Implementation Sprints:**
   - Break down the top 3 recommended feature upgrades into concrete engineering sprints with explicit acceptance gates, schema changes, and test strategies.

---

## Output Format
Deliver a comprehensive, decision-ready report structured as follows:
1. **Executive Architecture & Maturity Scorecard** (Grade by subsystem: Anatomical Atlas, Clinical Workflow, Security/RBAC, Performance/Hardware, Interoperability).
2. **Comprehensive Milestone Progression Matrix** (M1 through P9.4 status, capabilities, and verified evidence).
3. **Detailed Gap & Risk Analysis** (Table: `Subsystem | Current State | Risk / Gap | Recommended Solution`).
4. **Prioritized Feature Upgrade Roadmap (P10 - M7+)** (Table: `Feature / Milestone | Clinical / Educational Value | Technical Complexity | Regulatory SaMD Risk | Acceptance Gate`).
5. **Concrete Technical Specifications for the Top 2 Upgrades** (SQLite DDL, Python dataclass definitions, API contracts, WebGL shaders/pipeline).
6. **Limitations & Exact Local Reproduction Commands** (List unverified assumptions and provide executable commands for local verification).

---

## Tail
Assume the attached `msk-therapy-os-p9-4-roadmap-source.zip` is the source of truth.
Tell me exactly which subsystem or module provides the highest return on investment (ROI) for the next upgrade sprint without breaking backward compatibility or exceeding the low-spec hardware envelope.
EOF

# Copy prompt to Windows Desktop and Linux Desktop
cp /tmp/msk-therapy-os-p9-4-roadmap-prompt.md /mnt/c/Users/tuanh/Desktop/msk-therapy-os-p9-4-roadmap-prompt.md
cp /tmp/msk-therapy-os-p9-4-roadmap-prompt.md /home/tuan/Desktop/msk-therapy-os-p9-4-roadmap-prompt.md

ls -lh /mnt/c/Users/tuanh/Desktop/msk-therapy-os-p9-4-roadmap*
