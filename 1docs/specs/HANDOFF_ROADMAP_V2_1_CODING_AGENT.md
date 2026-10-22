# MSK-Therapy-OS — Roadmap V2.1 & Coding Agent Execution Handoff

**Date:** 2026-10-23  | **Role:** implementation handoff + cumulative execution log  
**Target live repository (not accessed here):** `D:\5Projects\msk-therapy-os`  
**Available source snapshot:** `msk-therapy-os-m3-roadmap-source.zip` (122 entries, 2026-10-22).  
**Status:** V2.1 accepted as a *plan*, not acceptance of the features. See `docs/ROADMAP_V2_1.md` and `docs/EXECUTION_V2_1.md` for actual results.

## 0. Mandatory first action on the real workstation

1. Inspect `git status --porcelain=v1`, `git log -1 --oneline`, checkout, tree, `SPEC.md`, `ENGINEERING_HANDOFF.md`, `docs/M282_FINAL_ACCEPTANCE_MATRIX.md`, actual M2.8.2 code. Preserve local modifications and branches; never silently reset or overwrite. The uploaded ZIP is a **snapshot**, not proof of live Git HEAD. Compare changed files before integrating this deliverable.
2. Establish baseline: `python -m unittest discover -s tests -v`, UI browser smoke (`/`, `/atlas/`, SOAP, Safety Gate, meridian editor, backup/restore), `sqlite3 PRAGMA integrity_check`, screenshots, current memory and FPS on Intel HD 5500. Some tests may be slow; record exact timeouts and failures rather than declaring PASS.
3. Make a separate feature branch/worktree; take SQLite backup with native backup API, verify SHA-256 and restore in scratch DB. No destructive migration or real patient records.
4. Review licenses for BodyParts3D, Open Anatomy Atlas, Dien Chan diagrams, model weights and any third-party package independently. Unlicensed source illustrations must not ship to a public Space.
5. Preserve all M2.8.2 acceptance/security constraints, safety hard-stops, FHIR semantics, existing CLI and APIs. Human clinical review is mandatory for teaching content.

## 1. V2.1 milestone mapping, sequencing and acceptance gates

`M2.3`, `M2.4`, `M2.5` are the **document names for proposed features**, not automatically completed repository milestones. The roadmap reserves new sequential IDs rather than rewriting the M2.8.2 history.

| Order | ID | Feature / vertical slice | Concrete acceptance gate |
|---|---|---|---|
| 0 | **Foundation / M3-F0** | Additive DB migration strategy, `source/provenance`, stable ontology namespace/IDs, optional synthetic case/visit references, negative isolation tests; full backup/restore. | Legacy regression and data migration/rollback pass; no new endpoint exposes real patient information. |
| 1 | **M2.9** | Evidence-typed Anatomy × Acupoint × Organ Relationship Explorer. SQLite typed entities/edges/sources; search by ID/name/alias; bidirectional relations; separate physical, spatial, traditional, research and observed assertions; Atlas Focus only when verified FMA+mesh mapping exists. | Search `Stomach` differentiates organ vs channel; `ST36`, `GB21`, `trapezius` resolve to typed records; unknown mapping abstains. Browser screenshot + tests. |
| 2 | **M2.10** | Custom Point Atlas & Research Studio (source document M2.4). 2D front/profile image version, immutable point-set revisions; point/line/polygon annotation, diagram-relative coordinates; reactive visit observations distinct from definitions; positive/assessed_negative/not_assessed; JSON/CSV export. | Create, edit, reopen, compare DEMO Day 1/3/7, export/import without collisions; legacy Atlas remains intact. |
| 3 | **M3-P0** | Multi-patient synthetic cases, real RBAC isolation, visits/ROM + pre/post objective deltas, PROMs, CTCAE adverse events, immutable audit, SOAP signoff, FHIR R4 `Patient`, `Encounter`, `Observation`, `Condition` only when recorded, `DocumentReference` only for approved note. | Cross-case access denied, backward compatibility, data recovery, supervised export. Do not onboard real patients without legal/security validation. |
| 4 | **M2.11** | Pose-to-Anatomy Explorer (source M2.5): licensed local image → MediaPipe Web *optional pinned* → uncertain 2D keypoints → manual correction → curated action-to-muscle graph → static Atlas reference highlight and timeline. | 3 licensed synthetic fixtures + an abstain fixture, manual correction survives reload, no fake muscle force/pathology, measured CPU latency. |
| 5 | **M2.12** | Three-photo Morphology Studio (source M2.3): front/side/back silhouettes + girths → adjustable low-poly **surface-only** avatar with editing/history and observation anchors. | Editable/saved/reopened illustrative avatar; Atlas remains independent; source photo licensing/privacy and target hardware checked. |
| 6 | **M4** | Joint kinematic arcs, later short video / optional validated OpenSim/OpenCap adapter, LOD + frame budget on HD5500. | Real browser profiling >30 FPS target where feasible, clear model-estimate labels; fallback if hardware insufficient. |
| 7 | **M5** | Reference anatomy skin/fascia/muscle/bone visibility, discrete opacity / slicing of source-verified meshes. | No claim of patient-specific tissue depth or safe instrument penetration; performance/mesh completeness verified. |
| 8 | **M6** | De-identified *synthetic-first* cohort dashboard, ROM/VAS/PROM summary, missing-data accounting, descriptive study and adverse-event trends, reviewed research export. | Reproducible calculations, source and consent checks, no observational causal-efficacy claim. |
| P0 parallel | **HF-DEMO** | Single-link web demo on Hugging Face Docker Spaces, immutable source assets, fake dataset, no credentials committed. | Container launches, HTTPS origin/auth rules safe, known Atlas dataset limitations surfaced, external browser smoke. **STOP only when an HF token/credential is actually required for authenticated deployment.** |

**Dependency order:** Foundation → M2.9 → M2.10; M3 safety/security before public write APIs and actual-patient data; then M2.11/M2.12; M4/M5; M6. HF containerization may run concurrently, but public anonymous **read-only demo** is the default. Do not claim M3 complete merely because DEMO case table exists.

## 2. Architecture invariants

- Backend: Python stdlib + SQLite; frontend: vanilla JS/WebGL. Existing Open Anatomy Atlas is the only reference anatomy renderer. Do not add a second renderer, Neo4j or incompatible server framework without measured need.
- Separate **four geometry domains:** diagram-normalized `u,v` (2D charts), photo landmarks (`PHOTO_2D`), surface avatar (`PATIENT_SURFACE_3D`), canonical atlas (`REFERENCE_ATLAS_3D`). Each mapping requires version, method, coordinate system, uncertainty, and provenance; no automatic clinical geometric registration.
- Typed evidence: `physical_anatomy`, `surface_proximity`, `traditional_association`, `clinical_research`, `patient_observation`, `hypothesis`. A point on a named “Stomach channel” is not a physical pipe connected to the organ. Candidate muscle role from a pose is **not measured muscle activation**.
- Stable FMA concept IDs are **not** FJ/BodyParts3D mesh keys. A missing mapping is `UNAVAILABLE`, not guessed from a point name or approximate XYZ.
- Teaching/demos only with `DEMO-*`; never public patient faces or identifiable records. Do not prescribe needle depth, electrical intensity, spinal manipulation, autonomous diagnosis or therapy.
- All sources, assets, and association edges require license, date, version, claim class, and reviewer/review state. Bùi Quốc Châu chart screenshot requires explicit redistribution permission before bundling.

## 3. Immediate file-level tasks

- `msk_therapy_os/db.py`: additive `CREATE TABLE IF NOT EXISTS`, foreign keys and `user_version` governance; no destructive alteration of existing tables; migrate existing demo data without collisions.
- `msk_therapy_os/relationship_catalog.py` (new): typed knowledge entities, source/provenance, validated relations; standard-library search/inspect APIs, additive seeded *synthetic placeholders only*, never unverified medical claims.
- `msk_therapy_os/server.py`: implement read-only `/api/explore/search`, `/api/explore/entities/{id}`, `/api/explore/relations`; then research endpoints with authorization and cross-case checks. Keep old routes working.
- `msk_therapy_os/static/*`: add collapsible explorer with correct label/evidence source; ensure existing Atlas iframe/object lifecycle intact. 2D research editor separate from atlas mesh coordinates.
- `msk_therapy_os/research_studio.py` (new): point set, diagram revision, annotations, reactive observations with signed visit joins; transaction-safe export with controlled formats.
- `tests/test_relationship_explorer.py`, `tests/test_research_studio.py`: migration, injection, unknown relation, anatomical vs traditional separation, permission denied, namespace collision, round-trip, failed requests, cross-case leaks.
- `Dockerfile`, `.dockerignore`, `.gitignore`, `README.md`, `docs/HUGGINGFACE_DEPLOYMENT.md`: pure-Python Docker image, bind `0.0.0.0:$PORT` inside container; no HF token committed; explicit warning about ephemerality and data persistence; read-only DEMO safe mode required before public release.
- `docs/EXECUTION_V2_1.md`: actual tests, failures, measured browser hardware, commit IDs, asset limitations, known blockers. Never fabricate tests or completion.

## 4. Hard security gates for Hugging Face

- Existing demo APIs expose case data without consistently requiring a real authenticated identity; local-only tests **do not** authorize Internet exposure. Before deploying, enforce a dedicated public-demo read-only mode (or complete multi-user server-side RBAC), block mutation/upload endpoints by default, disable local backup/restore APIs, add origin/host sanity checks, and scrub secrets.
- No real patient data, emails, identifiers, private keys or medical images in the Space repository or persistent volume. Any future clinical edition needs different hosting and security, legal and operations review.
- The ZIP omits the full BodyParts3D atlas dataset: document what renders offline with included assets and how the licensed full dataset would be installed. A web page responding 200 is not proof that anatomical mesh loading works.
- Hugging Face Space disk is ephemeral without correctly configured durable storage; do not claim SQLite safety on a mounted object store without transaction/locking validation. Demo seed DB can be reconstructed on boot and is disposable.
- Token gate: **Do all possible work without secrets first.** Request an HF token only for authenticated repo creation/push/deploy after packaging and local build/smoke tests. Never print/log the token.

## 5. Exact repeatable commands for agent (verify path)

```powershell
cd D:\5Projects\msk-therapy-os
git status --porcelain=v1
git log -1 --oneline
python -m unittest discover -s tests -v
python -m msk_therapy_os init --db demo.sqlite3
python -m msk_therapy_os seed-demo --db demo.sqlite3
python -m msk_therapy_os serve --db demo.sqlite3 --port 8085
# Browser: http://127.0.0.1:8085/ and /atlas/
```

For Docker after local smoke, no token needed: `docker build -t msk-therapy-os:demo .`, `docker run --rm -p 7860:7860 -e PORT=7860 -e MSK_PUBLIC_DEMO_READONLY=1 msk-therapy-os:demo`.

## 6. Definition of done & handoff rules

Every milestone requires code, migration evidence, negative tests, browser screenshots, hardware measurements (if hardware accessible), exact local commands, license inventory, safety review and acceptance matrix (PASS/PARTIAL/FAIL/BLOCKED). Full completion **must not** be asserted from writing a roadmap. Never assume old acceptance results apply to a new branch. Stop/ask only for truly required credentials or blocked legal permissions; otherwise implement as far as time and tools allow and record exact remaining tasks. 

## 7. Source-to-roadmap traceability

- `msk-therapy-os-m3-roadmap-prompt.md`: M3 cohort/FHIR/PROM/CTCAE; M4 dynamic arcs; M5 fascia; M6 analytics; reference hardware and safety.
- `MSK_Therapy_OS_Acupoint_Organ_Anatomy_Relationship_Explorer(1).md`: M2.9 typed knowledge, search, evidence tabs, anatomical vs traditional source separation.
- `MSK_Therapy_OS_M2_4_Custom_Point_Research_SPEC(1).md`: M2.10 2D annotation, versioned point sets, dynamic sinh huyệt, assessed-negative semantics, licensing.
- `MSK_Therapy_OS_M2_5_Pose_to_Anatomy_SPEC(1).md`: M2.11 landmarks, abstention, static reference Atlas mapping, optional MediaPipe and license review.
- `MSK_Therapy_OS_Patient_Morphology_3Photo_Plan(1).md`: M2.12 illustrative external avatar, no internal reconstruction claim.
- Existing M2.8.2 security, FHIR, WebGL and SQLite recovery reports in `docs/` are *baseline documents to re-verify*, not an excuse to skip new regression tests.
