# MSK-Therapy-OS: Constraint-First Engineering Handoff

**Version:** 0.1 (architecture and demo CLI)  
**Audience:** Implementing coding agent, tech lead, clinical reviewers.  
**Purpose:** A learning and longitudinal documentation tool for massage/DDS-device education, musculoskeletal anatomy, Thai massage, facial reflexology (Dien Chan), and manual therapy. **Not a diagnostic device or automated treatment planner.**

## 1. Executive decision (architecture compression)

Build **one new application repository**, not a monorepo containing three upstream codebases. Use existing applications/data behind adapters; ship only the functionality proven necessary. Start with standard-library Python CLI + SQLite for **synthetic demonstrations only**. Add a browser UI and real patient support only after security and professional review.

```
┌───────────────────────────────────────────────────────────┐
│ MSK-Therapy-OS: local-first learning & case workflow      │
│    CLI → optional thin web UI → optional AI Tutor          │
├───────────────┬────────────────────┬──────────────────────┤
│ AnatomyAdapter│ Assessment/Safety  │ Session/Progress     │
│ Atlas deep link│ rule-based red flags│ SOAP/ROM/pain trend  │
├───────────────┴────────────────────┴──────────────────────┤
│                    SQLite (prototype)                     │
│           FHIR export boundary (future adapter)           │
└───────────────────────────────────────────────────────────┘
External: Open Anatomy Atlas with BodyParts3D 4.0 (view/link, not bundled)
Optional later: Z-Anatomy dataset, Medplum FHIR API
```

## 2. Constraint-first

| Constraint | Engineering rule |
|---|---|
| Hardware | Windows 64-bit, Intel i7-5600U, 8 GB RAM, 238 GB SSD, Intel HD 5500. No heavy GPU or local LLM requirement. |
| Intended operator | Learner/technician under appropriate clinical supervision. No autonomous differential diagnosis, spinal manipulation directives, device intensity prescription or automatic patient-specific treatment plans. |
| Electrical devices | DDS is an ambiguous product label: require exact make/model, manufacturer manual, waveform, current limits, electrode configuration and regulatory status before any device-specific content. No generic claims that DDS equals TENS/NMES. |
| Patient safety | Intake must consider red flags and relevant device contraindications. Positive red flags hard-stop procedure suggestions and show urgent professional referral guidance. Rules are screening prompts, **not clearance or diagnosis**. |
| Privacy | V0 must use **synthetic data only**. Real patient data blocked pending consent, access control, encryption at rest/in transit, audit logs, retention and jurisdictional legal review. Do not send identifiable information to third-party AI by default. |
| Evidence | Every educational claim, recommendation or anatomical structure mapping must reference a vetted source with version/date/evidence tier. Separate evidence-based anatomy from traditional meridian/reflexology constructs. |
| Licensing | Atlas app MIT; BodyParts3D CC BY; Z-Anatomy CC BY-SA and some included meshes have NC restrictions. Must verify individual asset licenses prior to redistribution or commercial integration. Keep assets external during prototype. |
| Cost | Python standard library + SQLite; web-linked 3D atlas. No Kubernetes, Docker/Medplum stack, heavy RAG or local AI model in first milestone. |

## 3. Artifact-first: deliverables and contracts

Required repo artifacts, in order:

1. `SPEC.md` (this file): objectives, exclusions and acceptance gates.
2. `docs/ARCHITECTURE.md`: module boundaries, ADRs, threat model, integration map.
3. `docs/EVIDENCE.md`: source URLs, dates, evidence level, licensing and safety gates.
4. `msk_therapy_os/` CLI, with a deterministic synthetic-data workflow.
5. `tests/`: verifiable acceptance conditions.
6. `docs/FHIR_MAPPING.md` when real EHR integration is actually scoped.

### Domain boundaries (design targets)

- `AnatomyAdapter`: structure ID/name, body region, source/version, license and atlas deep link. Never pretend 3D location by itself diagnoses a condition.
- `Intake`: case pseudonym, age band, consent status, symptom onset/region, pain scale, functional limits, medications/conditions, prior care, relevant safety concerns, practitioner identity and timestamp. Clinical reviewer owns intake fields.
- `Assessment`: objective measures such as ROM (degrees, side, method), pain (0–10, time), neuro symptoms as reported, palpation observations clearly labeled subjective. No inferred vertebral displacement or compressed nerve diagnosis.
- `Safety`: transparent rule-based flags and escalation guidance; flags override treatment suggestions and are never weakened by an LLM.
- `Session`: visit date, S/O/A/P headings, delivered modality (if within trained scope), intervention parameters from actual device/operator records (not AI-generated), patient response, adverse effects, next appointment/referral.
- `Progress`: per-case timelines with before/after measurements, method comparability and missing-data warnings.
- `EvidenceLibrary`: explicit title/URL/organization/year/license/claim/evidence quality/reviewed-on; provenance for every nontrivial educational statement.
- `FHIRAdapter`: export `Patient`, `Encounter`, `QuestionnaireResponse`, `Observation`, `DocumentReference` where appropriate after a validated mapping and qualified review; do not treat a prototype export as clinical interoperability certification.
- `AITutor`: opt-in *read-only* explanation grounded in the case plus citations. It may suggest learning topics and clinician-validated assessment questions, not diagnoses, high-velocity manipulations, treatment prescriptions or electrical dosages.

### Evidence tier boundaries

1. Clinical guidelines / regulator / systematic reviews for benefits, contraindications, decisions.
2. Peer-reviewed anatomy, credible anatomy atlases and textbooks for anatomy/motion.
3. Manufacturer manual and trained operator documentation for exact device behavior (insufficient alone to prove clinical efficacy).
4. Traditional meridian and Dien Chan resources presented as separate cultural/practice schemas **without established equivalence to nerves, fascial lines or anatomical disease mechanisms**.

## 4. CLI-first: exact commands (shipped in starter)

From repo root (Windows PowerShell: use `py -3` instead of `python` when needed):

```bash
python -m msk_therapy_os init --db demo.sqlite3
python -m msk_therapy_os seed-demo --db demo.sqlite3
python -m msk_therapy_os cases --db demo.sqlite3
python -m msk_therapy_os add-visit --db demo.sqlite3 --case DEMO-NECK-001 --date 2026-10-19 --pain 6 --rom 42 --region neck --flag none --note 'Synthetic assessment only'
python -m msk_therapy_os timeline --db demo.sqlite3 --case DEMO-NECK-001
python -m msk_therapy_os atlas
python -m unittest discover -s tests -v
```

Unsafe-screening demonstration:

```bash
python -m msk_therapy_os add-visit --db demo.sqlite3 --case DEMO-NECK-001 --date 2026-10-20 --pain 8 --rom 25 --region neck --flag progressive_weakness --note 'Synthetic flag exercise'
```

Expected: `STOP_AND_REFER`; no suggestions about massage/DDS or manipulation. CLI is a **teaching/engineering demo only**, never use it to store real patient details.

## 5. Evidence-first: tests and acceptance criteria

| Gate | Testable requirement | Status at handoff |
|---|---|---|
| CLI functionality | Init/seed/add/timeline succeed on stdlib Python | Test in starter |
| Input validation | Reject invalid dates, pain outside 0–10, implausible ROM, unknown flags/cases | Test in starter |
| Safety gating | Defined red flags always yield `STOP_AND_REFER` independent of pain score | Test in starter |
| Consent/privacy | No genuine patient data accepted for production | V0 policy: demo only; hardening pending |
| Anatomy link | Correct external atlas URL; no dataset bundling or GPU dependency for CLI | Provided; interactive integration not implemented |
| Audit | Every future clinical write records actor, timestamp, change provenance | **Not yet implemented: blocks patient deployment** |
| Educational material | 100% of substantive claims in curated library have source URI, review date and evidence tier | **Not yet implemented** |
| FHIR interoperability | Verified round trip for case/visit/measurement with approved mapping | **Not yet implemented** |
| DDS safety | Manufacturer-specific instructions and qualified sign-off before device workflow | **Blocked until exact device model and manual** |
| Clinical approval | Qualified reviewer signs safety rules, workflows and instruction boundaries | **Not yet implemented: blocks patient deployment** |

## 6. Cost-aware dependency decisions

| Piece | Decision now | Trigger for adding it |
|---|---|---|
| Open Anatomy Atlas | Use externally as browser-based teaching aid; favor BodyParts3D 4.0 | Embed only after proving stable APIs/performance and license compliance |
| Z-Anatomy source | Do not duplicate clone in app | Needed additional anatomical structures, confirmed licensing, GPU performance |
| Medplum | No full-stack self-hosted instance on this 8 GB laptop during V0 | Multi-operator workflows, FHIR interoperability and secured patient deployment |
| OpenSim | Exclude | Validated biomechanical modeling feature impossible with simpler tools |
| Vector database, LLM agent | Exclude | Curated knowledge, testable RAG evals and a measurable learning benefit |
| Cloud hosting | Exclude | Completed privacy assessment, need for remote collaboration |

## 7. Automation-last milestones

**M0: Spec + runnable CLI (this handoff).** Demo cases; pain/ROM visit logs; conservative safety flag; no real patient information.

**M1: Evidence and assessment engine.** Create reviewed anatomical content and scenario-based assessment questionnaires; attach source details and specific body regions. Add structured SOAP, permissions for student vs reviewer, offline reports. Get clinical review of red flags and modalities.

**M2: Body-map learning UI.** Browser frontend, Open Anatomy Atlas adapter, region selection and structure ID mappings. Measure responsiveness on target i7/Intel HD 5500; degrade gracefully to 2D diagrams.

**M3: Safe pilot.** Consent workflow, encrypted storage, backups, RBAC, audit trail, device-specific safety reference, adversarial safety tests, qualified supervision. Only after these gates may non-synthetic records be considered, according to local law.

**M4: Optional AI Tutor.** Retrieval over curated evidence, citation display, controlled access, abstention, red flag overriding and 100-case evaluation. Never route patient identifiers to public AI services absent authorization.

**M5: FHIR/Medplum and automation.** Implement mappings once interoperability is needed; automate documentation/QA after observing a stable manual workflow. No automated diagnosis or device control.

## 8. Explicit non-goals

- No autonomous diagnosis, risk score as medical clearance, treatment prescription or auto-adjusting DDS hardware.
- No high-velocity cervical/spinal manipulation teaching workflow from text/video alone.
- No claim of proven physical meridians or equating Dien Chan points with anatomical nerves.
- No real patient use or HIPAA/GDPR/local compliance claim based on a synthetic demo.
- No API integration requiring credentials in this starter.

## 9. Decisions requiring human review

- Exact DDS model, manufacturer manual, training qualification and local regulatory classification.
- Intended jurisdiction and professional scope of practice.
- Whether this is educational-only, clinician-supervised case documentation, or a regulated product.
- Who approves clinical content and maintains evidence currency.

## 10. Verified upstream references (as of 2026-10-19)

- Open Anatomy Atlas: https://github.com/CognitionLabSNUC/open-anatomy-atlas (MIT application; external BodyParts3D/Z-Anatomy data; high-res requires modern GPU).
- Z-Anatomy: https://github.com/Z-Anatomy/Models-of-human-anatomy (Blender atlas; CC BY-SA; mixed licenses in assets).
- Medplum: https://github.com/medplum/medplum (Apache 2.0 for much of platform; full-stack compose includes Postgres, Redis, server, app).
- HL7 FHIR R4 QuestionnaireResponse: https://hl7.org/fhir/R4/questionnaireresponse.html
- US FDA powered muscle stimulator guidance (not a blanket assessment of DDS): https://www.fda.gov/regulatory-information/search-fda-guidance-documents/guidance-document-powered-muscle-stimulator-510ks-guidance-industry-fda-reviewersstaff-and

## 11. Handoff instructions for implementation agent

1. Inspect repo and run existing unit tests. Report actual output; never claim tests succeeded without running them.
2. Maintain no external runtime dependencies through M0/M1 unless justified by benchmark or necessary feature.
3. Implement each feature via one acceptance test, one small code change, one documented evidence/decision record.
4. Preserve strict synthetic-data-only banner until all production safety/security gates are complete.
5. Never produce simulated evidence of therapy effectiveness; learning outcomes need a legitimate evaluation design.
6. Stop on missing device model/manual or clinical sign-off, rather than inventing DDS settings.
7. Provide concise handoff each iteration: changed files, commands run, test output, unverified claims, risks and next gate.
