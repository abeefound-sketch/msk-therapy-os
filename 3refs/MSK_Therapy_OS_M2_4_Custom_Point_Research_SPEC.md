# MSK-Therapy-OS — M2.4 Custom Point Atlas & Reflexology Research Studio

**Document type:** Implementation-ready engineering specification and Coding Agent handoff  
**Version:** 1.0 · **Date:** 2026-10-22  
**Status:** PROPOSED — not implemented or independently accepted  
**Target project:** `D:\5Projects\msk-therapy-os`  
**Delivery principle:** **Constraint-first → Artifact-first → CLI-first → Evidence-first → Cost-aware → Automation-last**

> **Mission:** Extend the existing MSK-Therapy-OS learning and synthetic-case documentation platform so an operator can create an independent, versioned research atlas of points, lines, and zones; annotate front/profile facial diagrams; record *session-specific reactive findings*; relate those observations to proposed reflex maps; and inspect their longitudinal behavior without altering the verified anatomical atlas or misrepresenting traditional theory as established biological fact.

---

## 1. Background and source boundaries

### 1.1 Existing system — reported, not re-audited here

The uploaded `INTEGRATION_HANDOFF_M2_EXT.md` describes the following intended integration surfaces:

- Open Anatomy Atlas / BodyParts3D 4.0 as the anatomical 3D viewer.
- Separate traditional-meridian and Dien Chan namespaces / overlays (`meridians.js`).
- A Python standard-library HTTP server, REST endpoints and SQLite storage.
- `clinical_observations`, `therapy_sessions`, SOAP notes, synthetic `DEMO-*` cases, longitudinal timelines, Safety Gate and FHIR R4 export.
- A lightweight browser client running on an i7-5600U, 8 GB RAM, Intel HD 5500.

These are **handoff claims**, not independently verified implementation guarantees. The agent MUST inspect the checked-out source, migrations, tests, browser behavior, and actual Git revision before extending them. Do not assume the earlier code or schemas exactly match the handoff.

`MORPHOLOGY_FEASIBILITY.md` establishes an important boundary: external shape variation does not produce a medically valid, patient-specific internal anatomical atlas. **M2.4 does not require male/female volumetric reconstruction or body morphing.**

### 1.2 User-provided visual reference

The supplied Bùi Quốc Châu-style facial point chart contains:

- A **frontal facial view** and a **profile / oblique facial view**.
- Numbered point markers, overlapping point labels and grid references.
- Multiple facial regions and distinct visual marks.

Treat the illustration as a **source image to annotate**, not as a machine-verified point-location database. Exact point coordinates, numbers, meanings, reflex associations and source rights must be transcribed and reviewed individually. **Do not auto-extract and claim hundreds of validated point coordinates from the picture.**

The illustration displays a creator/copyright attribution. User upload is **not** permission to redistribute it commercially or bundle it in an open-source application. Use a license-cleared substitute or separately licensed source for distributable demo assets; permit local reference upload only under appropriate use rights.

### 1.3 Conceptual distinction to preserve

The following are **terms within the traditional Dien Chan / reflexology framework**, not verified anatomical structures:

| Concept | Software interpretation | Must NOT mean |
|---|---|---|
| **Định huyệt** (*reference/fixed point*) | Versioned point definition on a cited traditional diagram, optionally with a stable traditional point label | Automatically a physical nerve, vessel or clinical diagnosis |
| **Sinh huyệt** (*observed/reactive point*) | An observation recorded at a specific location, encounter and time, with a reproducible measurement method | A permanent new anatomical structure or automatically validated treatment point |
| **Đồ hình phản chiếu** (*reflex map*) | A theory-specific mapping from a facial area/point to a claimed corresponding body region | A verified anatomical or causal pathway |
| **Đồng ứng / phản chiếu hypotheses** | Explicit research assertions with sources, authorship and uncertainty | Established medical effects by default |

A reactive finding may be near a fixed reference point, coincide with one, or be recorded independently. Its measured status can vary across encounters; **absence of a recorded finding is NOT the same as a documented normal finding**.

---

## 2. Desired product outcome

A learner/researcher should be able to:

1. Create a personal point collection such as `DienChan-BQC-Research-v1`, or an independent experimental collection.
2. Add front and side diagrams with independent coordinate systems, image provenance, and a clear license status.
3. Zoom/pan and place numbered fixed reference points, self-defined points, paths and zones **manually** on these images.
4. Associate each definition with a cited traditional explanation, synonyms, observation protocol, proposed reflex-body link and reviewer status.
5. During a **synthetic training encounter**, mark a new reactive/sensitive finding anywhere on the diagram, including at locations that have no fixed point definition.
6. Record how, by whom and when the finding was assessed (e.g., tenderness rating, side, probe method, documented visual observation), without guessing a diagnosis.
7. Compare changes for the same mock patient across visits; distinguish *observed again*, *tested and not found*, and *not assessed*.
8. Explore a hypothesis on the map and compare the recorded reflex-point observations with independently measured pain/ROM/function over time.
9. Export/import research sets with versioning and provenance, without overwriting reference collections or silently promoting findings into reference points.
10. Retain the existing 3D anatomy and patient/visit learning workflow without regressions.

**User-visible product name:** `Custom Point Atlas & Research Studio`.

---

## 3. Scope, priority and exclusions

### P0 — Required for M2.4 acceptance

- Local creation, editing, duplication, archive and versioning of research point sets.
- High-resolution **front and side** diagram viewer with zoom/pan and accurate persistent annotations.
- Separate display layers: reference points; researcher-defined points/lines/zones; encounter observations; reflex hypotheses.
- Point/shape editor (point mandatory; polyline and polygon mandatory for reflex maps and pathways).
- Clear annotations, provenance, status, notes and save/reload.
- Encounter-specific reactive point observations linked to synthetic case + visit + diagram.
- Longitudinal timeline with explicit `positive`, `assessed_negative`, `not_assessed` distinction.
- Search/filter, JSON/CSV export, no original-data destruction, tests and browser evidence.
- Visible labels explaining that traditional reflex mappings are **hypotheses, not anatomy**.

### P1 — Valuable after P0

- Point-set import with conflict preview and reference deduplication.
- Additional views, bilateral mirroring **only when explicitly requested and reviewed**, regional templates and compare-two-versions mode.
- Structured hypothesis registry and descriptive research dashboards.
- Multiple-user roles after genuine authentication, RBAC and audit events exist.
- Inter-rater agreement analytics and calibration sessions.

### Deferred / out of scope

- Automatic point extraction from the uploaded chart via OCR/vision without expert review.
- Automatic transformation of 2D facial coordinates into 3D anatomical/clinical coordinates.
- Automatic discovery of “effective” acupuncture/reflex points or causality claims.
- Autonomous diagnosis, electrical stimulation parameters, acupuncture needle depth or treatment prescriptions.
- Modification or redistribution of upstream licensed data without a license audit.
- Actual patient data, multi-tenant deployment, cloud sync and public sharing before M3 security/privacy acceptance.
- AI agents, autonomous protocol generation and automated research conclusions (consider only after M4 safeguards).

---

## 4. Engineering architecture — reuse, do not rebuild

```text
Existing MSK-Therapy-OS Browser UI
 ├── Modern Anatomy: existing Open Anatomy Atlas / BodyParts3D 3D
 ├── Traditional Meridians: existing 3D overlays (unchanged in M2.4)
 └── NEW Research Studio (2D diagram coordinate space)
      ├── Point Set Library / Versions / Sources
      ├── Diagram Viewer + Shape Editor (front/profile)
      ├── Reference Points / Custom Hypothesis Layers
      ├── Reactive Finding Recorder (synthetic visit)
      └── Timeline / Descriptive Study Comparison
                         │
                 Existing Python local API
                         │
                 Additive SQLite migrations
          (point sets, diagrams, points, observations, audits)
```

**Preferred open-source candidates (evaluate and pin, do not blindly clone/merge):**

- **OpenSeadragon** — https://github.com/openseadragon/openseadragon — deep zoom/pan for 2D images (BSD-3-Clause).
- **Annotorious for OpenSeadragon** — https://annotorious.dev/guides/openseadragon-iiif/ — annotation editing. For current versions inspect `@annotorious/openseadragon`; do **not** assume the older `annotorious-v2-openseadragon` plugin is API-compatible with current releases. Verify license, bundle size, local offline loading and event hooks before adoption.
- **Open Anatomy Atlas** — reuse existing embedding for anatomical inspection, **not** for arbitrary 2D point placement.

**Integration rule:** Research Studio must have its own **2D image-space coordinate contract**. Do not feed normalized facial-chart coordinates into BodyParts3D's XYZ space. Existing 3D labels and structure IDs retain their original namespaces. If a 3D mapping is explored in a future milestone, require named registration landmarks, validated transform, independent reviewer approval and an error estimate; do not imply an anatomically precise mapping without those gates.

**Local-first cost:** Keep the current Python + SQLite backend, local web UI and small pinned static JS bundles. Avoid new server frameworks, Docker, cloud services, heavy models or a replacement WebGL renderer unless benchmarks demonstrate a necessity.

---

## 5. Data semantics and persistence contracts

### 5.1 Definitions vs. observations vs. hypotheses

These are different entities with different lifecycles:

- **Point definition:** a reusable coordinate + label on a specific diagram **version**. Can belong to a traditional source or to a user's research collection.
- **Reactive observation:** one encounter-time finding associated with a location and optionally a point definition; never updates the definition's coordinates implicitly.
- **Reflex hypothesis:** the researcher's asserted relationship between a point/zone and a body region or symptom, with citation and review status.
- **Clinical observation:** existing independent pain, movement, sensory or functional measurements recorded in the established M2.2 tracking model.

Definitions can be retired and versioned. Observations and source snapshots should remain historically interpretable.

### 5.2 Minimum relational schema (adapt names to repository conventions)

Use SQLite foreign keys, explicit transactions, safe additive migrations and strict constraints. Suggested logical tables:

| Table | Essential fields |
|---|---|
| `research_point_sets` | `id`, `slug`, `title`, `framework` (`dien_chan_bqc`, `tcm`, `sen_sib`, `custom`), `description`, `owner_scope`, `visibility` (`local_private` for demo), `status`, `current_version`, `created_at`, `updated_at` |
| `research_point_set_versions` | `id`, `set_id`, `version`, `parent_version_id`, `change_summary`, `author`, `created_at`, `is_locked` |
| `research_diagrams` | `id`, `set_version_id`, `view` (`front`, `left_profile`, `right_profile`, `other`), `asset_path`, `asset_sha256`, `width_px`, `height_px`, `license_status`, `copyright_credit`, `source_uri`, `calibration_status` |
| `research_point_definitions` | `id`, `set_version_id`, `diagram_id`, `local_code`, `name`, `geometry_type` (`point`, `polyline`, `polygon`), `geometry_json`, `side`, `status` (`draft`, `reviewed`, `disputed`, `retired`), `theory_namespace`, `source_ids`, `reviewer_id`, `reviewed_at` |
| `research_reactive_observations` | `id`, `case_id`, `visit_id`, `diagram_id`, `definition_id` **nullable**, `geometry_json`, `finding_state`, `tenderness_0_10` **nullable**, `method`, `operator`, `observed_at`, `laterality`, `raw_note`, `uncertainty_note`, `created_at` |
| `research_hypotheses` | `id`, `set_version_id`, `target_point_or_zone_id`, `proposed_body_region`, `proposition_text`, `framework`, `source_ids`, `confidence_label` (`traditional_claim`, `exploratory`, `evidence_reviewed`), `review_status`, `author` |
| `research_sources` | `id`, `title`, `author_or_org`, `url_or_catalog_reference`, `publication_year`, `license`, `retrieved_at`, `evidence_type`, `notes` |
| `research_change_log` | `id`, `entity_type`, `entity_id`, `action`, `actor`, `timestamp_utc`, `old_hash`, `new_hash`, `change_reason` |

**Important implementation constraints:**

- `case_id` and `visit_id` MUST reference existing **synthetic** case and visit tables; verify exact schema in the codebase first.
- Do not store names, dates of birth, photographs or other real patient identifiers in M2.4 demos.
- A diagram belongs to an immutable diagram **asset revision**, including SHA-256. Annotation coordinates must never silently migrate to a replaced/cropped image.
- Point codes are unique **within a point-set version**, not globally; do not accidentally merge BQC point `26` with an unrelated `26` from another system.
- Geometry uses a single, documented, validated JSON format; reject invalid NaN, Infinity, empty polylines, coordinates outside image bounds, duplicate IDs, missing references or contradictory statuses.
- `finding_state` must distinguish `observed_positive`, `assessed_negative`, and `not_assessed`; a numeric tenderness score of zero is not automatically equivalent to absent/not assessed.
- Missing data cannot be plotted as clinical improvement or a recovered/unblocked meridian.
- Updates to published/reviewed definitions create a new version and never rewrite historic visit references.
- Use `set_id + version_id + definition_id + diagram_id` for unambiguous joins. Avoid lookup by label alone.

### 5.3 Geometry contract

Use **image-relative normalized coordinates** independent of zoom and window size:

```json
{
  "space": "image_normalized_v1",
  "view": "front",
  "asset_sha256": "sha256-of-source-image",
  "type": "point",
  "coordinates": [0.4125, 0.2730]
}
```

- Origin = source image's upper-left; `u = image_pixel_x / width_px`, `v = image_pixel_y / height_px`; both in `[0, 1]`.
- Polylines = ordered array of 2D points; polygons = closed 2D ring(s), with validation.
- Front/profile charts have **independent transforms and coordinate systems**. No automatic mirroring/registration by assumption.
- Store source image native dimensions, orientation, asset hash and calibration version. Do not store raw DOM or page viewport positions as point coordinates.
- Pan, zoom, fullscreen, browser resizing and reloading must preserve the **same image-relative location**.
- Record spatial uncertainty: `manual_estimate`, `reference_digitized`, `reviewed`, `unverified`; this is not a medical accuracy certification.
- Overlapping labels require smart decluttering, selectable point list/search and highlight/isolation, not deletion of markers.

### 5.4 Illustrative JSON export (schema to finalize during implementation)

```json
{
  "schema_version": "msk-research-point-set/1.0",
  "set": {
    "id": "RSET-DEMO-BQC-01",
    "title": "Dien Chan Reference Study — Synthetic Demo",
    "framework": "dien_chan_bqc",
    "version": "1.0.0",
    "reference_not_clinically_validated": true
  },
  "diagrams": [{
    "id": "DGM-FRONT-01",
    "view": "front",
    "width_px": 1600,
    "height_px": 960,
    "asset_sha256": "REPLACE_WITH_VERIFIED_HASH",
    "license_status": "permission_required"
  }],
  "point_definitions": [{
    "id": "PNT-DEMO-26",
    "diagram_id": "DGM-FRONT-01",
    "local_code": "26",
    "name": "User-digitized reference example (not validated)",
    "geometry": {
      "space": "image_normalized_v1",
      "view": "front",
      "asset_sha256": "REPLACE_WITH_VERIFIED_HASH",
      "type": "point",
      "coordinates": [0.4125, 0.273]
    },
    "status": "draft"
  }]
}
```

**All numeric positions in this export example are invented demo values** to illustrate file structure and MUST NOT be treated as actual Bùi Quốc Châu point locations. The diagram dimensions, marker labels and asset hash are similarly placeholders until populated from a licensed source image.

---

## 6. UI and learning workflows

### 6.1 Research Studio navigation

Proposed navigation: `Anatomy 3D | Meridian Learning | Research Studio | Synthetic Case Timeline`.

The new Research Studio contains:

1. **Library panel:** point sets, ownership, framework, version, reference status, create/duplicate/import/archive.
2. **Diagram viewport:** front/left/right views, zoom, pan, reset, grid overlay, coordinates, point/line/zone tools.
3. **Layer manager:** fixed reference points; user proposals; session-specific reactive observations; reflex regions; each independently toggleable.
4. **Inspector/editor:** local code, names (Vietnamese/other language), location, source, review status, observation method, evidence caveats, Edit/Save/Cancel.
5. **Synthetic case panel:** select `DEMO-*` and encounter; add observation or revisit existing one.
6. **Timeline/chart panel:** visits, observations, point status, intensity/functional data, protocol consistency and confounder notes.

Avoid the earlier UI failure modes: clipped tabs, skinny nested scrollbars, overlapping labels, mismatched current selection, uncontrolled layers and confusing 2D/3D coordinate overlays.

### 6.2 Workflow A — Create personal atlas

1. Create `My-Dien-Chan-Research` as **private research**, choose `dien_chan_bqc` or `custom` framework.
2. Enter author/source, license status, theoretical notes and whether an atlas image may be reused.
3. Attach a licensed **frontal** diagram and **profile** diagram. Preserve original resolution and hash.
4. Manually add a candidate reference point labeled `26` on the applicable view; mark as `draft` until reviewed. Add multiple independent candidate reflex regions or pathways.
5. Save. Reload the page. The annotations must remain aligned and fully editable in the research copy.
6. Create a new version to change an existing definition; older revisions remain exportable.

### 6.3 Workflow B — Record a dynamic *sinh huyệt* finding

1. Open `DEMO-NECK-001`, choose a visit and select a diagram view.
2. Select `Record Reactive Finding` and click anywhere on the image, **not only on numbered reference points**.
3. Record observation type (e.g., tenderness or visible finding), method, laterality, rating if reproducibly measured, operator, time and free-text notes. Include method limitations.
4. Optionally associate it with the nearest reference point **after manual confirmation**, not automatic nearest-neighbor equivalence.
5. Save. Display it only as an encounter observation (visually distinct from reference points).
6. On a later visit, record `observed_positive`, `assessed_negative` or `not_assessed` explicitly.
7. Compare the point observations with separately captured ROM/pain/function, but never infer that one caused changes in the other.

### 6.4 Workflow C — Test a reflex hypothesis as a research record

1. Link a definition/zone to a **traditional hypothesis** (e.g., proposed correspondence to the neck/shoulder region), and record its cited origin.
2. Define the **observable prediction** in neutral terms: measurable local sensitivity and independent neck-pain/ROM outcomes.
3. Compare synthetic sequential measurements and visualize missingness, measurement protocol changes and co-interventions.
4. Label outputs `descriptive exploratory analysis` and state that association is not proof of efficacy.
5. Support later export for independent research review; no AI-generated “validated point,” “meridian cleared” or “cure confirmed” status.

---

## 7. API and CLI contracts — proposed, not claims of existing routes

The agent must inspect the existing Python router and CLI conventions, then implement equivalent interfaces consistent with current code style. Paths below are **proposed resource contracts**, not commands that already work.

| Method | Proposed path | Outcome |
|---|---|---|
| `GET` | `/api/research/point-sets` | List sets, framework/version/status filters |
| `POST` | `/api/research/point-sets` | Create new demo-local set |
| `GET` | `/api/research/point-sets/{set_id}` | Return metadata, current version and diagrams |
| `POST` | `/api/research/point-sets/{set_id}/versions` | Fork immutable version |
| `POST` | `/api/research/diagrams` | Upload/attach image with rights metadata, hash and dimensions |
| `GET` | `/api/research/diagrams/{diagram_id}/annotations` | Definitions + active overlays (per version) |
| `POST` | `/api/research/points` | Add versioned point / polyline / polygon |
| `PATCH` | `/api/research/points/{definition_id}` | Edit draft or create new revision under reviewed version rules |
| `POST` | `/api/research/reactive-observations` | Record a synthetic visit-level finding |
| `GET` | `/api/research/timeline?case_id=DEMO-...` | Group findings by diagram, visit, point, assessed state |
| `POST` | `/api/research/hypotheses` | Register an explicit, sourced research proposition |
| `GET` | `/api/research/exports/{set_id}?format=json` | Versioned export with provenance |
| `GET` | `/api/research/exports/{set_id}?format=csv` | Tabular export with explicit columns and coordinate units |

- Enforce bounds and size limits on image uploads (allowlist verified PNG/JPEG/WebP, reject SVG with embedded active content, no arbitrary file paths, no external SSRF URLs by default).
- Reject missing/invalid diagram hash, invalid reference IDs, cross-case visit mismatch, invalid coordinates and unsupported geometry with clear HTTP errors.
- Preserve existing Safety Gate and read/write behaviors; new research routes must **never bypass** safety or patient case isolation.
- No real authentication exists merely because a browser selector has a role label. Until M3, treat local demo ownership as a **namespace for testing, not a security boundary**.
- No unauthenticated remote exposure: bind only to `127.0.0.1` for M2.4.

**CLI-first requirements:** implement inspection and deterministic seed/export/test commands. Suggested usage after repository inspection:

```powershell
cd D:\5Projects\msk-therapy-os
python -m msk_therapy_os research list-sets --db demo.sqlite3
python -m msk_therapy_os research seed-demo --db demo.sqlite3
python -m msk_therapy_os research export --db demo.sqlite3 --set-id RSET-DEMO-BQC-01 --output research-demo.json
python -m unittest discover -s tests -v
python -m msk_therapy_os serve --db demo.sqlite3 --port 8085
```

These commands specify the **required intended CLI behavior**; they are not asserted to exist in the current checkout. If CLI routing is not extensible, add a small subcommand module without breaking existing flags.

---

## 8. Research integrity, clinical safety and privacy

### Evidence provenance

- Every imported or manually transcribed reference definition records the **source title, author, edition/year if known, page/figure when available, source image hash, annotator and review state**.
- Any claim about anatomy, pathology, effectiveness, contraindications or point location gets an independently reviewable source. A traditional teacher's map is a source for **what the tradition claims**, not automatically proof that its diagnostic mechanism works.
- Do not assign Cochrane/WHO or clinical “Grade A/B” badges by association with a point's name; review the **exact intervention, indication, study population and result** before displaying grades.
- Do not create fictitious BQC point definitions, coordinates, outcomes or references.
- Preserve distinction between `Traditional Claim`, `User Hypothesis`, `Observed Finding`, `Reviewed Evidence`, and `Unknown` in the UI and exports.

### Data validity

- Simulated data must be marked `SYNTHETIC / DEMO` on every screen and export.
- Use an explicitly recorded assessment method, operator, laterality and time for repeated measures. Do not compare scores from incompatible scales as if identical.
- Record absent, positive and unassessed findings separately.
- No diagnosis of organ disease from facial markings; no claim that a “cleared meridian” is objectively established by a changed reactive-point score.
- Linking a point with existing `clinical_observations` never overwrites medically framed assessment entries.

### Privacy and permissions

- M2.4 uses fake `DEMO-*` patients **only**. No real patient face photos or personal health records.
- Scope point collections by demo-local owner namespace; prohibit accidental overwrites of curated reference sets.
- When future multi-user collaboration is added, require real login, RBAC, immutable audit, encryption, backup/restore and consent approved at the M3 gate. A shared workstation without user authentication does **not** provide research confidentiality.
- No network calls transmitting images, notes or data to external AI services in M2.4.

### FHIR boundary

- Existing FHIR export must keep working unchanged.
- Custom research constructs are not FMA anatomy IDs or automatically SNOMED/LOINC-coded clinical facts. If an export extension is needed later, use explicit local CodeSystem/identifier, provenance, and independently reviewed mapping; do not falsely assert FHIR conformance.

---

## 9. Test plan and acceptance criteria

Tests must run against the checked-out app and preserve existing tests. Provide **raw logs** and **real browser screenshots**, not invented test counts.

| ID | Requirement | Acceptance evidence |
|---|---|---|
| AC-01 | New personal atlas created without changing existing reference sets | DB records, API response, screenshot |
| AC-02 | Front/profile images attach with verified dimensions, hash and rights status | Import error/acceptance tests, image metadata |
| AC-03 | Manually placed point stays at the same image-relative location after zoom, pan, resize and reload | Automated coordinate assertions + screenshots at two zoom levels and 1366×768 viewport |
| AC-04 | Lines and zones can be drawn, selected, edited and exported | Browser E2E log + schema round trip |
| AC-05 | Two point collections can contain identical local codes without collision | Isolation test and UI labels |
| AC-06 | Reactive finding can be recorded **without** a reference point | Save/reload test, timeline screenshot |
| AC-07 | Explicit positive / assessed-negative / not-assessed statuses remain distinct | DB/schema tests, timeline legend |
| AC-08 | Synthetic Day 1/3/7 observations link correctly to visit IDs and replay in chronological order | Deterministic seed + E2E test + screenshot |
| AC-09 | Point definition edits create proper revisions; old observations remain linked to old revisions | Migration/version tests |
| AC-10 | Export/reimport reproduces geometry, labels, source and status without collisions | JSON schema validation, canonical diff |
| AC-11 | Malformed coordinates, oversized/non-image uploads, path traversal, broken references and unsafe text are rejected or escaped | Negative/security test logs |
| AC-12 | Existing M1/M2 3D anatomy, meridian layers, SOAP, timeline, FHIR and Safety Gate are intact | Full regression suite + browser smoke tests |
| AC-13 | UI clearly separates traditional claims from observed data and does not label diagram points as anatomical nerves or medical diagnoses | Screenshot and copy review |
| AC-14 | Browser remains responsive on target-class hardware; client assets load offline on localhost | Timed load and process-memory/GPU measurements, no-console-error recording |
| AC-15 | Original annotated chart is **not** bundled in redistributed artifacts absent verified rights | Asset inventory and license report |

**Primary manual demo scenario (mandatory):**

1. Start localhost UI with synthetic seed.
2. Create or open `RSET-DEMO-BQC-01`, switch `Front ↔ Profile` and zoom the selected image.
3. Add and save draft reference point `26` with a synthetic, explicitly **unvalidated** location (or use properly reviewed source data, if available).
4. Select `DEMO-NECK-001`, record synthetic reactive finding `S-001` as `observed_positive` at Visit 1, tenderness `7/10`, with method and notes; then record `4/10` at Visit 2; mark Visit 3 as `assessed_negative` **only if explicitly assessed**.
5. Reload app, select the same case and atlas; show all historical entries correctly attached to image/visit/version.
6. Display existing neck pain/ROM outcomes **separately** from reactive-point findings; show no “treatment proven” conclusion.
7. Export and reimport the research point set without touching existing anatomical/meridian data.
8. Capture a screenshot of each critical step and verify browser-console errors are absent.

**Performance measurements:** report both JS heap **and** total Chrome process memory (and GPU memory where available); never present JS heap alone as total RAM usage. Run at 1366×768 on the specified Windows machine if the agent actually has access; otherwise mark hardware validation **BLOCKED**, not PASS. Record browser/OS versions and measurement method.

---

## 10. Implementation plan and commit gates

### Gate M2.4-0 — Discovery and artifacts

- Inspect branch, commit, current UI, SQLite schema, endpoint conventions and existing test evidence.
- Review image rights; choose licensed sample assets for redistributable seed.
- Evaluate pinned OpenSeadragon + current Annotorious combination using a throwaway local proof of concept; document actual package versions and licenses.
- Produce `docs/M2_4_ARCHITECTURE_ADR.md`, `docs/M2_4_SCHEMA.md`, `docs/M2_4_SOURCE_REGISTER.md`, `docs/M2_4_ACCEPTANCE_MATRIX.md` **before major code changes**.

### Gate M2.4-A — Point Set Studio

- Add additive schema migration, set CRUD/versioning and static 2D annotation editor.
- Deliver AC-01–05, AC-10 and AC-15 with working browser demo.

### Gate M2.4-B — Dynamic research observations

- Implement encounter-specific reactive findings, visit linkage, explicit assessment states and longitudinal timeline.
- Deliver AC-06–09 and safe export; run integration tests.

### Gate M2.4-C — Validation and handoff

- Fix reproducible visual issues; complete negative/security tests, source attribution, regression and performance checks.
- Deliver AC-11–14, screenshots and final acceptance matrix.
- Commit incremental changes with descriptive Git messages. No M3/M4 tasks until M2.4 is accepted.

**Stop conditions:** missing rights to redistribute charts; missing source for alleged point coordinates; uncaught data-loss migration; real patient data observed in demo; unsafe remote exposure; existing Safety Gate broken. Block or narrow the feature rather than fabricate evidence.

---

## 11. Required final handoff artifacts

Create or update these files **inside the working repository**:

```text
docs/M2_4_ARCHITECTURE_ADR.md
 docs/M2_4_SCHEMA.md
 docs/M2_4_SOURCE_REGISTER.md
 docs/M2_4_ACCEPTANCE_MATRIX.md
 docs/M2_4_TEST_REPORT.md
 docs/M2_4_USER_GUIDE.md
 docs/M2_4_KNOWN_LIMITATIONS.md
 tests/test_research_point_sets.py
 tests/test_reactive_observations.py
 tests/test_research_exports.py
 evidence/m2_4/              # screenshots, browser logs, benchmark raw data
```

Names may be adapted to existing repository conventions, but all artifact **contents** are required.

**Coding Agent final response must report:** Git commit(s), files changed, migration commands, exact localhost URL, server status, real commands run and observed output, browser screenshots, each AC PASS/FAIL/BLOCKED, unresolved issues, asset licensing status, and steps to stop/restart the local server. No self-awarded “100% complete” without independent visual and data acceptance.

---

## 12. External references and implementation notes

- Existing project handoff supplied by user: `INTEGRATION_HANDOFF_M2_EXT.md` (2026-10-20). Reference for reported M2.1/M2.2 capabilities, not proof of independent validation.
- Existing feasibility study supplied by user: `MORPHOLOGY_FEASIBILITY.md` (M2.3). Reference for body-model deformation limitations.
- User-supplied Bùi Quốc Châu facial diagram (frontal/profile). Visual reference only; precise mapping and redistribution rights **not established**.
- OpenSeadragon official repository: https://github.com/openseadragon/openseadragon
- OpenSeadragon viewer and coordinate API: https://openseadragon.github.io/docs/
- OpenSeadragon overlay examples: https://openseadragon.github.io/examples/ui-overlays/
- Current Annotorious OpenSeadragon integration: https://annotorious.dev/guides/openseadragon-iiif/
- Current Annotorious installation guidance: https://annotorious.dev/installation/

**License note:** OpenSeadragon's code is BSD-3-Clause; any annotation library versions and the **underlying facial diagrams/data** must receive an independent license check. A dependency's permissive license never grants rights to a third-party medical or traditional-therapy illustration.

---

## 13. Single-sentence implementation directive

**Build a source-traceable, versioned 2D custom-point research studio that treats traditional fixed-point definitions, encounter-specific reactive findings and exploratory reflex hypotheses as separate entities, integrates with synthetic longitudinal observations, reuses licensed open-source annotation tooling, preserves the existing 3D anatomy application, and provides reproducible browser acceptance evidence.**
