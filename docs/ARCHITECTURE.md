# MSK-Therapy-OS: Architecture and Boundaries (Milestone M1)

## Context

MSK-Therapy-OS is a constraint-first clinical learning and longitudinal documentation system for musculoskeletal anatomy, manual therapy techniques, and electrical stimulation device education. It is explicitly an **educational and engineering proof-of-concept**. A medically safe production deployment requires independent clinical, privacy, security, and regulatory review. It **must never replace** a licensed clinical assessment or autonomously control electric stimulation equipment.

## Compression and Design Rules

1. **One repository** for orchestration and learning workflows. Treat source atlases as external assets and healthcare backends as optional adapters.
2. **Modular submodules with zero runtime dependencies:** Python standard library (`sqlite3`, `dataclasses`, `argparse`, `typing`, `pathlib`, `unittest`).
3. **Deterministic rule-based safety gating before AI:** Red flags and contraindications are explicit hard gates (`STOP_AND_REFER`). AI or screening heuristics cannot weaken or overrule safety flags.
4. **Namespace segregation:** Modern evidence-based anatomy (`ANATOMY_EVIDENCE`) is strictly segregated from traditional/cultural meridian (`TRADITIONAL_MERIDIAN`) and facial reflexology (`DIEN_CHAN_REFLEX`) schemas.
5. **No autonomous actions:** No automated diagnosis, no treatment prescriptions, no spinal manipulation directives, and no DDS dosage parameter calculations.

## Module Structure (Milestone M1)

```
msk_therapy_os/
├── __init__.py      # Package metadata and synthetic-data warnings
├── __main__.py      # Unified CLI parser and backwards-compatible dispatch
├── db.py            # SQLite schema initialization, foreign key PRAGMA, migrations, seed data
├── models.py        # Strongly-typed domain records and enums
├── safety.py        # Rule-based safety gate, red flags, modality contraindications, escalation guidance
├── evidence.py      # Curated 4-tier evidence catalog with provenance, review dates, and scopes
├── anatomy.py       # AnatomyAdapter with BodyParts3D FMA mapping, deep-linking, and namespace isolation
├── assessment.py    # Structured intake validation, scenario questionnaires, and objective ROM schema
├── soap.py          # Structured SOAP notes, student vs reviewer role permissions, and review audit trail
├── reporting.py     # Offline clinical education report generator with progress deltas and audit warnings
├── server.py        # Lightweight zero-dependency HTTP server for Milestone M2 Body-Map UI
└── static/          # Pure HTML5/CSS/Vanilla JS single-page application with 2D interactive SVG body-map
    └── index.html
```

## Component Contracts

| Component | Input | Output | Explicitly Excluded |
|---|---|---|---|
| `AnatomyAdapter` (`anatomy.py`) | Region, structure ID, namespace | Atlas deep link, BodyParts3D FMA ID, evidence citation | Inferring tissue pathology, nerve entrapment, or spinal subluxation from 3D coordinates |
| `SafetyEngine` (`safety.py`) | Reported red flags, proposed modality, contraindications | `STOP_AND_REFER` or `DOCUMENT_ONLY`, escalation rationale, evidence ID | Medical clearance, autonomous triage advice, softening of red flags |
| `Assessment` (`assessment.py`) | Intake questionnaire, joint-specific ROM (motion, side, angle, method) | Validated relational records, scenario queries | Diagnostic labeling, treating subjective palpation as objective fact |
| `SOAPManager` (`soap.py`) | S/O/A/P text sections, author role, supervisor feedback | Relational SOAP notes, review lifecycle (`DRAFT`, `SUPERVISED`, `APPROVED`) | Authorizing non-supervisory sign-off; generating autonomous treatment prescriptions |
| `EvidenceLibrary` (`evidence.py`) | Evidence ID, tier query (1-4) | Verified citations with DOI/URL, license, organization, review date | Unsubstantiated clinical efficacy claims |
| `ReportGenerator` (`reporting.py`) | Case ID | Structured Markdown report with synthetic banner, ROM progress, and audit gaps | Exporting unreviewed drafts as certified medical records |
| `WebServer` (`server.py`) | HTTP REST requests (cases, anatomy, safety, SOAP) | JSON payloads & interactive 2D SVG SPA | Multi-tenant auth, cloud syncing, unvetted external scripts |

## Evidence Tier Boundaries

1. **Tier 1 (Clinical Guidelines / Regulators / Systematic Reviews):** NICE NG59, IFOMPT Framework, US FDA Powered Muscle Stimulator 510(k) Guidance. Governs red flags, hard stops, and device contraindications.
2. **Tier 2 (Peer-Reviewed Anatomy & Reference Atlases):** BodyParts3D 4.0 (DBCLS), Open Anatomy Atlas (SNU), Z-Anatomy. Governs 3D anatomical structures and joint motion planes.
3. **Tier 3 (Manufacturer Manuals & Device Documentation):** Exact verified DDS specifications. Workflows locked until verified model, waveform, and current limits are supplied.
4. **Tier 4 (Traditional Practice & Cultural Schemas):** Traditional Thai Medicine (Sen Sib lines), Dien Chan Multireflexology. Cultural educational constructs; explicitly not equivalent to physical nerves, vessels, or pathology.

## Trust and Threat Boundaries

- **Synthetic Data Boundary:** All cases must match `DEMO-*`. The CLI, database, and report generators reject real patient identifiers. Free-text fields (`--note`, S/O/A/P) feature warnings that real patient information is strictly prohibited.
- **Role Permission Boundary:**
  - `student`: Can record intakes, add visits, enter ROM, and draft SOAP notes (`review_status = DRAFT`). Cannot approve or sign off notes.
  - `reviewer`: Supervising clinical instructor. Can create supervised notes, review student drafts, provide educational feedback, and set status to `APPROVED` or `REJECTED`.
- **Method Comparability Boundary:** The system audits ROM measurements across visits. When differing measurement tools (e.g., inclinometer vs. visual estimate) are detected for the same motion, the system issues a prominent method incomparability warning in reports.
- **Safety Escalation Boundary:** When a red flag or contraindication is present:
  - Disposition is locked to `STOP_AND_REFER`.
  - The SOAP Plan section is programmatically required to state referral/cessation of physical techniques before saving.
  - High-velocity thrust spinal manipulation is categorically rejected as a forbidden modality.

## Target Hardware and Performance

- **Target Profile:** Windows 64-bit, Intel Core i7-5600U, 8 GB RAM, Intel HD 5500 graphics.
- **CLI Footprint:** Memory usage < 25 MB RAM; execution time < 300 ms for full test suite (29 tests in ~0.26s).
- **Zero Heavy Dependencies:** No Docker, no Node.js server, no local neural network, no cloud API calls.
