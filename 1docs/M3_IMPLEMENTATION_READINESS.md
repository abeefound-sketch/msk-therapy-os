# Milestone M3: Implementation Readiness & Architecture Specification

**Document ID:** M3-SPEC-001  
**Author:** Principal Software Architect, Clinical Systems Specialist  
**Project:** MSK-Therapy-OS (`integration/m2.7-m2.8`)  
**Status:** Architecture Specification Ready — Awaiting User Acceptance of M2  

---

## 1. Readiness Assessment

With the successful completion, empirical validation, and data governance verification of Milestones M2.7 and M2.8:
- The 3D Atlas foundation is stabilized, auto-scaling, and verified against BodyParts3D 4.0 ground truth.
- Canonical reference datasets are cryptographically protected (SHA-256) and reconciled across international and national standards.
- Point authoring, versioned auditing, and evidence-linking operate reliably on local SQLite.
- Multilingual localization (EN, ZH, VI) and responsive multi-device layouts (375px–1920px) are fully verified.

The core platform is **architecturally sound and ready to proceed to Milestone M3: Multi-Patient Clinical & Longitudinal Cohort Management**.

---

## 2. Milestone M3 Scope & Architecture Specification

Milestone M3 advances MSK-Therapy-OS from a single-scenario educational prototype into a robust, multi-patient clinical learning and cohort tracking platform.

### 2.1 Planned M3 Capabilities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Milestone M3: Core Modules                            │
├─────────────────────┬───────────────────────────┬───────────────────────────┤
│ 1. Cohort Mgmt      │ 2. Patient Timelines      │ 3. Longitudinal Tracking  │
├─────────────────────┼───────────────────────────┼───────────────────────────┤
│ • Multi-Patient DB  │ • Longitudinal Chronology │ • Pre / Post ROM Deltas   │
│ • Anonymized Ident  │ • Visit Milestones        │ • Pain Numeric Rating VAS │
│ • Cohort Tagging    │ • Modality Progression    │ • Standardized PROMIS-10  │
│ • FHIR Patient Res  │ • Clinician Sign-off      │ • Adverse Event Reporting │
└─────────────────────┴───────────────────────────┴───────────────────────────┘
```

#### A. Multi-Patient Records & Cohort Management
- Extend `cases` table to support arbitrary local patient profiles with anonymized synthetic identifiers (`PAT-2026-XXXX`).
- Role-based data partitioning between educational simulation mode and clinical practice mode.
- Export full cohort datasets in standardized FHIR R4 Patient and Encounter bundles.

#### B. Patient-Specific Timelines & Session History
- Dedicated interactive timeline UI mapping treatment encounters across weeks and months.
- Sequential comparison of treatment modalities (Manual Tuina, Acupressure, ROM exercises, Thermal therapy).
- Longitudinal audit trail tracking clinician adjustments to palpated loci.

#### C. Before / After Objective Measurements
- Quantitative delta calculations:
  $$\Delta \text{ROM} = \text{ROM}_{\text{post}} - \text{ROM}_{\text{pre}}$$
  $$\Delta \text{Pain} = \text{VAS}_{\text{post}} - \text{VAS}_{\text{pre}}$$
- Visual range-of-motion arc indicators rendered on 3D joint articulation centers (cervical rotation, shoulder abduction).

#### D. Adverse Event & Safety Surveillance
- Structured Adverse Event reporting form (CTCAE-based grading for musculoskeletal manipulation and needle insertion).
- Direct linkage to Red Flags Safety Gate for mandatory escalation and physician referral.

#### E. Structured Research Comparisons
- Side-by-side cohort outcome evaluation against published benchmarks (e.g. NICE NG59 low back pain guidelines, Cochrane reviews).
- Strict evidence tier attribution: claims must cite specific catalog IDs (`EVID-G-xxx`, `EVID-A-xxx`).

---

## 3. Strict Architectural Boundaries & Non-Goals

To maintain clinical safety, medical device regulatory compliance, and architectural focus:

> [!CAUTION]
> **Definitive Architectural Non-Goals for Milestone M3:**
> 1. **No Automated AI Treatment Recommendations:** M3 will NOT generate diagnostic claims or autonomous treatment prescriptions.
> 2. **No Posture Sensors or Wearable IoT:** External Bluetooth hardware, IMU accelerometers, or live camera computer vision are outside M3 scope.
> 3. **Educational vs. Clinical Decision Support Boundary:** The application acts as a structured clinical training workbench and documentation ledger. It is **NOT** a certified Clinical Decision Support System (CDSS) or Class II/III medical device. Clinical responsibility remains with the licensed human practitioner.

---

## 4. Acceptance Authority Statement

Completion and transition to Milestone M3 are subject to explicit user review:

**STATUS: READY FOR USER ACCEPTANCE**
