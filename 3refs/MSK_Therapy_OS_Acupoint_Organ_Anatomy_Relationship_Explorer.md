# MSK-Therapy-OS — Acupoint–Organ–Anatomy Relationship Explorer

**Document type:** Product specification, UX/UI design, data architecture, and engineering handoff  
**Version:** 1.0 — Proposed, not implemented  
**Date:** 2026-10-22  
**Target:** MSK-Therapy-OS, Windows laptop (i7-5600U, 8 GB RAM, Intel HD 5500)  
**Method:** Constraint-first → Artifact-first → CLI-first → Evidence-first → Cost-aware → Automation-last

> **Core rule:** A physical anatomical relationship, a traditional medicine association, and a clinical effectiveness claim are **three different kinds of information**. Never present one as proof of another.

## 1. Product objective

Build a **bidirectional relationship explorer** that lets a learner:

1. Search for an **organ, muscle, bone, joint, nerve, vessel, body region, meridian, acupoint, symptom, or traditional reflex point**.
2. See relevant entities on the **existing Open Anatomy Atlas 3D viewer**, not a new anatomy renderer.
3. Understand **where an acupoint is described on the body surface** and which **anatomical structures are nearby** in the reference model.
4. Discover which points and channels are **traditionally associated with an organ or functional concept**, explicitly separated from physical proximity and published clinical evidence.
5. Record a **structure-linked finding** during a synthetic learning case, then inspect its longitudinal history.
6. Create and maintain **private research atlases**, including Dien Chan/Bùi Quốc Châu fixed points and patient-specific *sinh huyệt* observations, with distinct source and validation status.

### Answer the user's core question

**If the learner selects the stomach:** show the anatomical stomach mesh; alongside it, show *traditionally related concepts* (for example the **Stomach channel** in TCM) and points associated with that framework, *subject to verified source records*. Do **not** imply that the channel is a nerve, vessel, or a physical tube attached to the organ. Separately show clinical research indexed by **specific condition, intervention and outcome**, not by the organ's name alone.

**If the learner selects ST36 (Zusanli):** zoom to the **leg surface region**, locate the point using verified descriptive landmarks, and show nearby tibial/muscular structures **only when the dataset supports a validated mapping**. Show “Stomach channel” under **Traditional Associations**, not under “Anatomical Organ Connections.”

**If the learner selects GB21 (Jianjing):** focus the shoulder/upper trapezius region, show its traditional channel assignment, local reference muscles/bones, provenance, positional uncertainty, and a safety panel. Never infer a safe insertion depth or treatment protocol from the rendered mesh.

The examples above are **interaction requirements**, not a declaration that all coordinates, anatomical relationships, or clinical claims in the current project have been independently validated.

## 2. Fundamental knowledge separation

| Relationship category | Example | Meaning | UI treatment |
|---|---|---|---|
| **Physical anatomy** | A muscle attaches to a bone; an artery passes through a region | Anatomical relationship supported by an anatomy source | **Solid link**; blue/neutral “Anatomy” tag; reference ID and data source |
| **Surface locality / spatial proximity** | A named acupoint is described near a palpable landmark | Geometric/descriptive correspondence, not physiological function | **Dotted spatial marker**; indicate atlas/side, method, and positional confidence |
| **Traditional conceptual association** | ST36 belongs to the TCM Stomach channel | Relationship *within a traditional conceptual system* | **Dashed relationship in the side-panel graph**, “Traditional theory” tag; never draw as a physical internal connection |
| **Clinical research evidence** | A study evaluates an intervention for a particular condition/outcome | Research *about a defined intervention and outcome* | Separate “Research evidence” tab with citation, design, population, comparator, outcomes, certainty, limitations |
| **Patient observation** | A user reports tenderness at a mapped site on a given date | Case-specific recorded observation | “Observed” with date, method, operator and measurement; never auto-label “abnormal” without a defined rule |
| **Hypothesis / custom atlas** | A research library proposes an organ reflex association | User-authored, not verified | Purple/neutral “Hypothesis / Private research” tag, permission and version history |

**Critical naming rule:** Distinguish **Stomach (anatomical organ)** from **Stomach channel (TCM concept)**, **Heart (anatomical organ)** from **Heart channel**, and so forth. Identical words must not collapse distinct graph nodes.

**Clinical claim rule:** A conventional medicine indication, a traditional indication, a biological mechanism hypothesis, and proven treatment efficacy are not interchangeable. Use “traditionally associated with” rather than “treats,” “stimulates,” or “restores the function of” an organ unless an independently reviewed claim supports the exact wording.

## 3. Screen and interaction design

### 3.1 Desktop layout

```text
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  MSK Therapy OS   [ Search: point / organ / muscle / symptom / FMA / alias... ]       │
│  Filters: [Anatomy] [Acupoints] [Meridians] [Research] [Patient DEMO only]           │
├─────────────────────┬────────────────────────────────┬────────────────────────────────┤
│ RESULT / NAVIGATION │  EXISTING 3D ANATOMY ATLAS     │ INSPECTOR                       │
│                     │                                │ Point / organ / structure name  │
│ • Search results    │ Reference male/female model   │ [Where?] [Traditional links]    │
│ • Category and      │ [Bones] [Muscles] [Nerves]     │ [Research] [Safety] [History]   │
│   source filters    │ [Vessels] [Organs] [Points]    │                                │
│ • Related points    │                                │ Source; version; confidence     │
│ • Related organs    │ [Focus] [Isolate] [X-ray]      │ Nearby structures (if verified) │
│ • Relation graph    │ [Anterior/Posterior]           │ Related concepts (distinct)     │
│   (conceptual)      │ [Surface / Deep]               │ [Add DEMO observation]          │
├─────────────────────┴────────────────────────────────┴────────────────────────────────┤
│  DEMO TIMELINE:  Day 1  ───── Day 3 ───── Day 7  │ Pain │ ROM │ Point sensitivity   │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

The inspector and relationship list should be collapsible. Do not place every point and every pathway on the screen at the same time. Preserve responsive behavior for a narrow laptop window.

### 3.2 Search behavior

- **One global search** with Vietnamese (including diacritic-insensitive terms), English, Latin, Pinyin, Chinese characters, established point codes, FMA identifiers, and common aliases where supported by curated sources.
- Search categories: **Organ**, **Muscle**, **Bone/Joint**, **Nerve/Vessel**, **Point**, **Channel**, **Condition/Symptom**, **Research library**.
- Results must expose **type + terminology source + certainty** before click, avoiding collisions between an organ and a similarly named channel.
- Support queries in both directions: `organ → points`, `point → nearby anatomy`, `muscle → surface points`, `channel → points`, and `patient → dated findings`.
- Default sort: direct ID/name match, then curated synonym, then verified anatomical region, then traditional concept relationship. **Never rank unverified organ-effect assertions as physical facts.**
- An absent relation must say **“Not documented in this source”**, not **“No relationship exists.”**

### 3.3 Six inspector tabs

| Tab | Contents | Required interaction |
|---|---|---|
| **Location** | Body side, anterior/posterior region, surface landmark description, 3D anchor quality, data source | Focus / isolate / display 2D reference if 3D is not validated |
| **Nearby anatomy** | Bones, joints, muscles, nerves, blood vessels physically in the reference region, each with FMA and atlas mesh provenance | Click a structure to focus it; show approximate relationship only when mapping supports it |
| **Traditional associations** | System (TCM / Thai Sen Sib / Dien Chan / private atlas), channel, named organ/functional association, cited text | Navigate concept graph, **not** a fake anatomical connection line |
| **Research evidence** | Specific condition, study type, intervention, comparator, outcome, certainty, adverse events, reference link | Filter by disease/outcome; distinguish no evidence from evidence of no effect |
| **Safety and uncertainty** | Proximity caution, unknown depth, contraindication evidence, source gaps, model limitations | Never show auto-suggested electrical parameters, needle depth, or therapeutic clearance |
| **Case history** | Dated annotations, pain scale, ROM, pressure sensitivity, functional measures, adverse responses | Record synthetic observation, reopen and compare visits |

### 3.4 Visual encoding (accessible and not misleading)

Use **shape and explicit text labels**, not color alone:

- Filled selected mesh: verified **physical anatomy**.
- Outlined surface marker: **point location in the reference atlas**.
- Dashed *2D side-panel graph* edge: **traditional relation**.
- Hollow circle with `?`: **unverified/approximate landmark**.
- Calendar dot: **actual recorded observation** (synthetic until compliance gates are complete).
- Reviewer badge: **source reviewed**; distinct from **clinically effective**.

A traditional meridian may be drawn as an **educational surface overlay**, but must be labeled conceptual; it must not appear to penetrate and connect real organs. Enable one pathway at a time by default. For point markers, respect depth/occlusion so points behind the body are hidden or clearly annotated as occluded.

## 4. User journeys

### Journey A — “Which points relate to the liver?”

1. Search **liver**.
2. Results split: **Liver (organ)** / **Liver channel (TCM)** / **Liver-related clinical conditions**.
3. Selecting **Liver (organ)** focuses the anatomical organ in the 3D Atlas.
4. The inspector shows **Anatomical relations** (physical neighboring structures; confirmed data only), and separately **Traditional associations** with sources and uncertainty.
5. Selecting **Liver channel** changes the 3D focus to the *documented surface path*, not to a simulated nerve or anatomical connection from skin to liver.
6. Any claims of effects on a liver condition appear only in **Research evidence**, with explicit population, intervention, and outcomes. A missing source yields “Not established / Not curated.”

### Journey B — “Which points are near the upper trapezius?”

1. Search **trapezius**; filter **Muscles**.
2. Focus and isolate trapezius in the reference atlas.
3. Open **Related surface points**. A point appears only if an editor has reviewed its source-landmark or region association.
4. Click **GB21**; show its stated landmark, location uncertainty, supporting atlas structure, and any safety warning.
5. In a synthetic patient record, enter “tenderness on palpation, left side, 5/10,” explicitly marked as *observed*, not as a diagnosis or proof of a traditional theory.
6. At the next synthetic visit, compare the same point with the same observation method.

### Journey C — “Find what relates to the wrist pulse”

1. Search **radial pulse** or **radial artery**.
2. Focus the **physical artery** and corresponding wrist region. Show palpation landmarks from validated anatomy descriptions.
3. Optional nearby **traditional points** are displayed only as cross-referenced surface landmarks, never as a substitute for vascular anatomy or a promise of safe massage near a vessel.
4. Present a **high caution** label for major vascular sites. No compression/manipulation protocol is generated from 3D geometry.

### Journey D — Custom research / Dien Chan

1. Select **My Research Atlases → Dien Chan** and choose an authorized 2D face diagram (front/side).
2. View stable numbered points as **source-defined theory**; record detected *sinh huyệt* independently for a synthetic visit.
3. Add sensitivity, observed appearance, date, image annotation, and confidence of localization.
4. Compare repeated observations without automatically labeling a reflex point as “normal,” “blocked,” or evidence of an organ condition.
5. Optionally create a candidate 3D link to a **surface** face model, pending validated landmark registration. Preserve the original 2D coordinate and source image version.

## 5. Data model: relationship graph on SQLite (no graph database required)

Do not merge the `meridians.js` renderer, FMA ontology and patient tables into one untyped JSON collection.

### 5.1 Required entities

| Entity | Essential fields |
|---|---|
| `knowledge_entities` | `id`, `kind`, `name`, `aliases`, `namespace`, `language`, `source_id`, `version` |
| `knowledge_relations` | `id`, `from_id`, `predicate`, `to_id`, `relation_class`, `assertion_status`, `source_id`, `reviewer_id`, `reviewed_at` |
| `sources` | `id`, `title`, `author_org`, `url_or_doi`, `version_or_year`, `license`, `retrieved_at`, `review_status` |
| `atlas_anchors` | `entity_id`, `atlas_version`, `coordinate_frame`, `body_side`, `mesh_id_FJ`, `concept_id_FMA`, `surface_landmark_method`, `position`, `verification_status`, `registration_notes` |
| `research_claims` | `id`, `condition_code`, `intervention`, `comparator`, `outcome`, `study_design`, `finding`, `certainty`, `source_id`, `review_status` |
| `research_collections` | `id`, `name`, `owner`, `visibility`, `version`, `source_license`, `created_at` |
| `clinical_observations` | **Existing table:** keep `case_id`, `visit_id`, `target_type`, `target_id`, and typed findings; add optional `source_relation_id`, `localization_method`, `observer`, `uncertainty`, `snapshot_version` via migrations |

**Identity/geometry rules:**

- **FMA** represents anatomical concepts. **FJ** identifies BodyParts3D mesh resources. Do not treat them as interchangeable IDs.
- A **point code** is not a geometric coordinate. Each mapping is specific to a **source, atlas/model version, side and positioning method**.
- `AT_SURFACE_OF`, `NEAR`, `INNERVATED_BY`, `PART_OF`, `TRADITIONALLY_ASSOCIATED_WITH`, `STUDIED_FOR`, and `OBSERVED_AT` are different predicates. They must not be silently converted into one another.
- A coordinate within human body bounds is **not evidence of correct anatomical registration**.
- For body-shape changes (height, adiposity, sex-reference model), **do not reuse absolute XYZ coordinates** without validated correspondence. Unknown anchors remain 2D/descriptive.
- Every externally exposed point set needs a rights/license review; source naming standards do not grant a license to reuse illustrations.

### 5.2 Example relation record (illustrative, review required)

```json
{
  "from_id": "TCM:ST36",
  "predicate": "BELONGS_TO_CHANNEL",
  "to_id": "TCM:STOMACH_CHANNEL",
  "relation_class": "traditional_theory",
  "assertion_status": "awaiting_source_review",
  "source_id": null,
  "anatomical_causation": false,
  "ui_label": "Traditional channel membership — not a physical organ connection"
}
```

This record is a **schema illustration**, not a verified clinical claim. Store actual citations and editorial approval before publishing as sourced content.

### 5.3 Data integrity constraints

- Foreign keys on every relationship and observation target.
- Unique (`namespace`, `external_id`, `version`) identifiers; preserve local `id` across edits.
- Immutable audit/history of corrections, including who changed a traditional association or a spatial anchor.
- **No implicit organ effects:** The graph cannot infer `ST36 treats the stomach` from `ST36 belongs to Stomach channel`.
- Patient records must remain isolated by case and authorized user. Current `DEMO-*` identifiers are a synthetic-only constraint, **not an access-control system**.
- Track scale/measurement units, side, camera/model coordinate conventions and point position uncertainty.

## 6. Integration into existing M2.1/M2.2

**Reuse now:**

- **Open Anatomy Atlas / BodyParts3D 4.0:** mesh display, layers, isolate/focus, structure search.
- `meridians.js`: existing point/path overlay, after fixing alignment/occlusion and evidence labels. Avoid a second renderer.
- Existing SQLite `clinical_observations` / `therapy_sessions`: synthetic observations and visit history.
- Existing SOAP UI, safety gate, longitudinal dashboard and FHIR R4 export flow.
- SQLite **FTS5** when available for bilingual search; a lightweight indexed fallback is acceptable.

**Add only:**

- `relationship_catalog.py`: source-qualified nodes and typed edges.
- `relationship_search.py`: entity search, aliases, relationship traversal, evidence filtering.
- A lightweight **Relationship Explorer inspector** in the current web UI.
- `anchor_registry.py`: reviewed, model-version-specific atlas anchors and 2D fallback.
- A migration for source IDs, relations, point-collection ownership, and observation provenance.
- Fixture datasets for a **small, clinically reviewed pilot slice** rather than bulk ingesting unreliable 3D positions.

**Suggested API contracts (names illustrative; inspect existing routes first):**

```http
GET /api/explore/search?q=stomach&type=organ
GET /api/explore/entities/{entity_id}
GET /api/explore/relations?entity_id=TCM:ST36&relation_class=traditional_theory
GET /api/explore/nearby?entity_id=TCM:ST36&atlas=bp3d40
GET /api/explore/evidence?entity_id=TCM:ST36&condition=...
GET /api/explore/case-timeline?case_id=DEMO-NECK-001&target_id=TCM:GB21
```

Endpoints must return explicit `status: verified | approximate | unverified | unavailable`, source attribution, data version, and an explanatory note. **Do not serve fabricated proximity rankings.**

## 7. Personalized anatomy: supported vs unsupported

Current project documents describe M2.3 as a feasibility study, not a validated individualized internal anatomy engine.

**Supported learning workflow:** Patient-specific surface location notes, selected reference sex/age body type, measured circumference, pain map, photos with consent and permissions after M3, and longitudinal annotations. A technician may adjust *observational surface landmarks* but cannot simply drag the whole nerve or organ mesh into a “clinically correct” position.

**Not supported by three clothed photos and measurements alone:** exact muscle and fascial boundaries, subcutaneous adipose depth at any point, neurovascular routes, or a safe acupuncture/electrical intervention depth. These require appropriate examination and sometimes imaging; the system must label model geometry as **reference anatomy**.

A future individual CT/MRI adapter belongs in a separately validated workflow; do not introduce a full imaging stack on the 8 GB pilot laptop for this feature.

## 8. Safety and clinical research boundaries

1. This is **educational software and synthetic case documentation** until clinical, regulatory, privacy, security and professional-scope gates are passed.
2. Clinical decisions must not be based on traditional organ-channel diagrams or approximate 3D point depth.
3. No autonomous diagnosis, point prescription, DDS current/amplitude instructions, needling depth/direction, or high-velocity spinal manipulation guidance.
4. Significant red flags, uncertainty about vascular/nerve locations, and device contraindications block procedure-related suggestions and route to appropriate qualified assessment.
5. **Do not claim meridians have “opened,” organs “detoxified,” or tissues “recovered”** merely because an acupoint score changed.
6. The outcome study feature must avoid post hoc efficacy conclusions: record intervention type, exposure, baseline, co-interventions, natural progression, consistent measures, missingness and adverse events. Observational improvement **does not establish causality**.
7. The current project handoff uses evidence badges for some points; **revalidate every badge against the actual cited study/outcome**, rather than inheriting a label from a third-party repo.

## 9. Implementation roadmap and evidence gates

| Phase | Scope | Acceptance evidence | Status |
|---|---|---|---|
| **P0 — Data/UX contract** | Typed relation taxonomy; canonical IDs; screen wireframe; seed library for ST36, GB21, organ and muscle examples; citation and license review | Documented schema, data provenance table, tests distinguishing organ vs channel | Proposed |
| **P1 — Bidirectional lookup MVP** | Search organ ↔ traditional concepts ↔ acupoints; point ↔ nearby anatomy; point inspector; atlas focus | Real browser video/screenshots and interaction logs; accurate source labels | Proposed |
| **P2 — Provenance and patient history** | Source inspector, uncertainty badge, add synthetic observation, timeline replay, private research collection | Save/reload same entity on Days 1/3/7; patient isolation; no legacy regression | Proposed |
| **P3 — Visual correctness and performance** | Fix occlusion, lazy-load point paths, context-aware layer defaults, responsive panel | Front/side/back screenshots; no off-body clipping without explicit approximate label; measured full browser-process/GPU memory | Proposed |
| **P4 — Clinical/privacy preparation (existing M3)** | Authentication, audit, privacy/consent, professional review, vetted device rules | Security review and risk acceptance before real patient entry | Deferred |
| **P5 — Hypothesis research tools** | Structured comparisons, descriptive trend summaries, export for qualified research review | Analysis provenance and confounding notes; no unsupervised effectiveness claims | Deferred |

### Strict pilot acceptance scenarios

1. **Organ to point:** Search **Stomach (organ)** and verify physical organ isolation; traditional point results must appear in **separate, correctly labeled** associations.
2. **Point to anatomy:** Search **GB21** and show upper-shoulder area, with only validated anatomy landmarks and honest positional uncertainty.
3. **Muscle to point:** Search **trapezius** and show an inspected list of reviewed point/region associations; no invented nerve/organ links.
4. **Concept collision:** Search **Heart**. UI must distinguish **anatomical heart** from **traditional Heart channel** without merging evidence or geometry.
5. **Unknown mapping:** For an unreviewed point, no fabricated 3D location, depth, adjacent blood vessel or claimed benefit appears. A documented 2D fallback is displayed.
6. **Longitudinal:** Create a synthetic left-shoulder observation linked to a stable target ID, reload, then display day-by-day trends and provenance.
7. **Regression:** Current SOAP, Safety Gate, anatomy layers, FHIR R4 export and demo cases continue to function.
8. **UX:** At target laptop viewport, tabs and toolbars do not clip; point labels do not obscure anatomy; the inspector remains usable with keyboard and screen reader labels.
9. **Evidence audit:** Each presented claim has a source and claim type; each source is checked for meaning, age, and permitted use.
10. **Security:** All APIs stay bound to localhost during demo; no real identifiers or uploaded patient images in this MVP.

## 10. Engineering deliverables

The coding agent should deliver:

- `docs/RELATIONSHIP_EXPLORER_SPEC.md` and `docs/RELATIONSHIP_TYPES.md`;
- the SQLite migration and source-typed fixture data;
- working organ/point/muscle bidirectional search, inspector tabs and reviewed atlas focus;
- synthetic observation integration with existing SOAP and timeline;
- screenshots of **Stomach → traditional links**, **GB21 → nearby anatomy**, **Trapezius → points**, and **unknown mapping fallback**;
- automated tests, full browser performance measurements, license register and documented limitations;
- a versioned PASS/FAIL/BLOCKED acceptance matrix, exact commands and Git commit.

**Do not declare “clinically verified” based on pixel coordinates, successful unit tests, point code matching or appealing UI.** The user must be able to see and understand precisely **what is anatomically real, what is traditionally asserted, what has been clinically studied, and what was actually observed in a particular case**.

## 11. Reference sources and provenance

### External references verified for this design

1. [Open Anatomy Atlas — official repository](https://github.com/CognitionLabSNUC/open-anatomy-atlas): rendering, layers, structure focus/isolation, search, and reference datasets.
2. [WHO — Standard Acupuncture Nomenclature](https://www.who.int/publications/i/item/9290611057): standard point naming; **nomenclature does not establish clinical efficacy or atlas-space coordinates**.
3. [WHO 2008 Standard Acupuncture Point Locations — standards reference](https://icmart.org/standards/): indexed international standard; verify licensed primary text for exact landmark descriptions before transcribing or publishing.
4. [NCCIH — Acupuncture: Effectiveness and Safety](https://www.nccih.nih.gov/health/acupuncture-effectiveness-and-safety): evidence/safety boundaries and intervention-specific claims.
5. [NCCIH — Traditional Chinese Medicine: What You Need To Know](https://www.nccih.nih.gov/health/traditional-chinese-medicine-what-you-need-to-know): evidence limitations and cautions.
6. [Foundational Model of Anatomy, official development repository](https://github.com/uw-sig/FMA): symbolic anatomical concepts and structural relationships; check the applicable data-use terms.
7. [HL7 FHIR R4 Observation](https://hl7.org/fhir/R4/observation.html): body site, point-in-time observations and longitudinal storage patterns.

### Existing project documents used as reported context

- `INTEGRATION_HANDOFF_M2_EXT.md` (2026-10-20): reported M2.1 3D points/meridians, M2.2 observations and FHIR export, `meridians.js`, existing API and patient-case design. **The handoff is an implementation claim, not independent validation.**
- `MORPHOLOGY_FEASIBILITY.md` (2026-10-20): limits of skin deformation, point registration, model sex differences, internal anatomy validity. **Feasibility conclusions and performance claims must be separately reproduced.**

---

**Recommended milestone name:** `M2.5 — Evidence-Typed Anatomy × Acupoint × Organ Relationship Explorer`  
**Architectural decision:** Extend the existing Open Anatomy Atlas + SQLite implementation. **Do not build a new renderer, do not deploy Neo4j, and do not merge unrelated repositories.**
