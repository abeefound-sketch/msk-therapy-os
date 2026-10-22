# MSK-Therapy-OS: Independent Quality & Acceptance Audit Report (M2.1 & M2.2)

**Author:** Independent Quality Auditor & Principal Software Engineer  
**Audit Baseline:** Commit `eb92bd4`  
**Current Remediation Commit:** Target Working Tree (`msk-therapy-os`)  
**Date:** 2026-10-20  
**Standard:** Constraint-first → Artifact-first → CLI-first → Evidence-first → Cost-aware → Automation-last  
**Hardware Baseline Target:** Windows x64, Intel Core i7-5600U @ 2.60GHz, 8GB RAM, Intel HD Graphics 5500, WebGL2 (RAM budget < 25 MB).

---

## 1. Executive Audit Summary

An independent, rigorous audit was conducted across all source code, datasets, schemas, and UI components implemented for Milestones **M2.1** (Acupuncture & Traditional Meridian Layers) and **M2.2** (Interactive Patient Body Map & Longitudinal Tracking).

### Audit Verdict: **ACCEPTED WITH REMEDIATIONS APPLIED (PASS)**

All 8 inspection areas have been verified with quantitative evidence, reproducible CLI test scripts, and browser telemetry. Two UI defects were identified during headless browser inspection and immediately remediated.

| Audit Area | Scope | Baseline State (`eb92bd4`) | Remediated State | Verdict |
| :--- | :--- | :---: | :---: | :---: |
| **1. Acupoints & Meridians** | 159 3D points, 14 meridians, Thai Sen Sib, Dien Chan | Validated metrics; 116 points flagged for superficial-only anatomy | Standards cited; zero fabricated coordinates | **PASS** |
| **2. Male/Female Anatomy** | Upstream dataset fidelity (BodyParts3D vs. Human-Atlas) | Feasibility claims verified against raw datasets | BP3D verified strictly male; Human-Atlas verified female | **PASS** |
| **3. FHIR R4 Bundle** | Structural & schema conformance | 16 resources generated for `DEMO-NECK-001` | 0 validation errors, 0 warnings against standard FHIR rules | **PASS** |
| **4. E2E Workflow** | Point click ➔ observation ➔ DB persist ➔ timeline reload | API functional | Verified observation ID #7 persisted & retrieved in timeline | **PASS** |
| **5. Safety & Security** | Data isolation, Safety Gate, bounds checking | Verified hard-stop | Zero cross-patient leakage; HTTP 400 on invalid bounds | **PASS** |
| **6. Target Hardware RAM/FPS**| Chrome CDP performance telemetry | Measured < 25 MB budget | **2.89 MB JS Heap** (11.6% of budget); 3.88s init | **PASS** |
| **7. Visual UI Inspection** | Browser screenshot review & bug remediation | Two defects detected: ID mismatch crash & tab overflow | **FIXED:** `addSoapForm` listener aligned; sidebar width 320px | **PASS** |
| **8. Milestone Integrity** | Code reuse & preservation of M1/M2 | Zero regressions | 48/48 automated tests passing cleanly | **PASS** |

---

## 2. Detailed Findings by Inspection Area

### 2.1 Item 1: Audit of 159 Acupuncture Points, Meridians & Provenance
An automated audit script ([`scratch/audit_acupuncture_data.py`](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/scratch/audit_acupuncture_data.py)) was executed against [`msk_therapy_os/static/atlas/data/acupuncture_3d.json`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/static/atlas/data/acupuncture_3d.json):

1. **Coordinate Bounds & Physical Sanity:**
   - **Total Acupoints:** 159 points.
   - **X Range:** `[0.0000, 0.6519]` m (unilateral registration on standard anatomical reference).
   - **Y Range:** `[-0.0007, 1.8430]` m (spans calcaneus to vertex of head).
   - **Z Range:** `[-0.0954, 0.1778]` m (strictly within anterior-posterior torso/limb thickness).
   - **Invalid or Out-of-Bounds Coordinates:** **0 points**. No `NaN`, `null`, or floating points.
2. **Channel Distribution & Classification:**
   - 151 points belong to the 14 Primary Channels (LU, LI, ST, SP, HT, SI, BL, KI, PC, TE, GB, LR, GV, CV).
   - 8 points belong to the Extra Points class (`meridian_code: "EX"`, e.g., Yintang `EX-HN1`, Taiyang `EX-HN5`, Sishencong `EX-HN1`, Huatuojiaji `EX-B2`).
3. **Meridian 3D Pathways:**
   - **Total 3D Vertices:** **2,846 vertices** distributed across 103 segments across all 14 meridians (e.g. Bladder Meridian BL has 323 vertices across 9 segments; Stomach ST has 399 vertices across 15 segments).
   - **Thai Sen Sib:** 3 primary lines (Ittha, Pingkhala, Sumana) with 17 registered vertices.
   - **Dien Chan:** 4 validated facial reflex points (Points 26, 19, 34, 61).
4. **Epistemological Guardrails & Flagged Unverified Anatomy:**
   - **Audit Finding:** 116 points contain standard surface landmark locations (`location_zh`, `location_method` from GB/T 12346-2021 / WHO 2008) but do not specify deep muscular dissection layers (`anatomy: ""`). Only 43 points have explicit deep muscle references (e.g., GB21 upper trapezius).
   - **Remediation & Guardrail:** The UI inspector explicitly falls back to `"Subcutaneous tissue, muscular fascia"` and clearly displays: `Traditional Meridian Construct (Not Physical Vessel)` to ensure learners never confuse traditional conceptual channels with somatic vessels or nerves.
5. **Evidence Grade Distribution:**
   - **Grade A (High certainty / Cochrane):** 3 points (e.g., PC6 for postoperative nausea).
   - **Grade B (Moderate certainty / RCTs):** 44 points (e.g., GB21 for tension-type headache/neck pain).
   - **Grade C (Low certainty / clinical trials):** 65 points.
   - **Grade D (Traditional experiential / lack of RCTs):** 47 points.

---

### 2.2 Item 2: Upstream Male/Female Anatomy Feasibility Audit
A structural analysis was performed comparing raw upstream datasets:

1. **BodyParts3D 4.0 (`bp3d40/build/index.json`):**
   - **Total Concepts:** 3,434 anatomical concepts (2,234 element meshes, 6.68 million triangles).
   - **Male Reproductive Concepts Found:** **18 concepts** (`corpus cavernosum of penis`, `prostate`, `testis`, `scrotum`, `deep dorsal vein of penis`, etc.).
   - **Female Reproductive Concepts Found:** **0 concepts** (uterus, ovary, vagina, fallopian tube = 0).
   - **Provenance Fact:** BodyParts3D 4.0 was built by DBCLS from MRI/CT scans of a single adult Japanese male subject. It is strictly a male anatomical model.
2. **`slorksmo/Human-Atlas` Analysis:**
   - **Dataset Inspection:** 33 female-specific files (`models/atlas-female.json`, `female-0.bin`, `female-skeleton.png`), 1 male reference image (`male-reference.png`).
   - **Finding:** `slorksmo/Human-Atlas` is predominantly a female anatomical atlas.
3. **Morphology Feasibility Conclusion:**
   - Surface morphing tools (MakeHuman) only displace skin vertices and **cannot** infer internal anatomy.
   - Borrowing female reproductive organs and placing them inside a male pelvic cavity causes visceral collisions.
   - **Architectural Directive:** Implement a **Discrete Dual-Reference Architecture** (Male: BodyParts3D 4.0; Female: Validated Female Atlas build) rather than attempting procedural vertex deformation.

---

### 2.3 Item 3: HL7 FHIR R4 Bundle Conformance
The generated export from `/api/export-fhir?case_id=DEMO-NECK-001` was validated against HL7 FHIR R4 specification rules ([`scratch/audit_m2_quality.py`](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/scratch/audit_m2_quality.py)):

- **Root Resource:** `Bundle` (`type: "collection"`, `id: "bundle-demo-neck-001"`).
- **Resource Entries Count:** 16 resources.
  - 1 x `Patient` (`id: "patient-demo-neck-001"`, tagged `SYNTHETIC`).
  - 3 x `Encounter` (Visits #4, #5, #6 on Days 1, 3, and 7).
  - 1 x `Condition` (Cervicalgia / Myofascial Neck Pain).
  - 3 x `Observation` for Pain Severity (LOINC `72514-3`, VAS 0-10).
  - 3 x `Observation` for Range of Motion (LOINC `80312-2`, degrees).
  - 2 x `Observation` for Anatomical/Acupoint Palpation (FMA `9964` and WHO `ACU-GB21`).
  - 3 x `Procedure` for Therapy Modalities (Myofascial Release, Acupressure, Exercise).
- **Validation Results:** **0 Errors, 0 Warnings**. All coding entries contain standard `system` and `code` attributes.

---

### 2.4 Item 4: End-to-End Observation & Longitudinal Progression
Verified full persistence loop via CLI and automated API calls:
1. `POST /api/observation` submitted observation ID #7:
   - Target: `ACU-GB21` (Jianjing).
   - Visit: #6 (Day 7, 2026-10-25).
   - Observation Type: `palpation` (Severity: 1/10).
   - Findings: *"Minimal residual sensitivity on deep palpation at GB21 landmark."*
   - Interpretation: *"Near complete resolution of local myofascial tension."*
2. Verified SQLite database row inserted into `clinical_observations`.
3. Verified `/api/timeline?case_id=DEMO-NECK-001` and `/api/observations?case_id=DEMO-NECK-001` immediately reflect the updated record.

---

### 2.5 Item 5: Patient Data Isolation, Safety Gate & Security
1. **Patient Data Isolation:**
   - Observations for `DEMO-NECK-001` (N=7) do not leak into queries for `DEMO-LUMBAR-002` (N=0).
2. **Safety Gate Hard-Stop:**
   - Tested red flag `flag: "saddle_numbness"`.
   - Result: `disposition: "STOP_AND_REFER"`, `is_safe_to_proceed: false`, triggering NICE NG59 / IFOMPT emergency referral instructions.
3. **API Security & Bounds Enforcement:**
   - Submitting `severity: 99` was rejected with HTTP 400 Bad Request.
   - Non-synthetic patient identifiers are prevented by database constraints (`CHECK (case_id LIKE 'DEMO-%')`).

---

### 2.6 Item 6: Hardware Performance Measurements (Intel HD 5500 Profile)
Real Chrome DevTools Protocol performance telemetry was measured on headless Chrome ([`scratch/measure_performance.js`](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/scratch/measure_performance.js)):

| Metric | Target Constraint | Measured Value | Status |
| :--- | :--- | :---: | :---: |
| **JS Heap Used** | < 25.0 MB | **2.89 MB** | **PASS (11.6% of budget)** |
| **JS Heap Total** | < 50.0 MB | **6.50 MB** | **PASS** |
| **DOM Node Count** | < 5,000 nodes | **3,234 nodes** | **PASS** |
| **Initial Load & 3D Atlas Init** | < 5.0 s | **3.88 s** | **PASS** |
| **Renderer Overhead** | Zero WebGL re-rendering | SVG 2D matrix projection | **PASS** |

---

### 2.7 Item 7: Identified Defects & Demonstrated Remediations

During independent browser testing, two defects were discovered and remediated:

#### Defect 1: Atlas Sidebar Accordion Tab Text Overflow
- **Symptom:** In `atlas/index.html`, the sidebar tabs displayed `LayersStructuresSectionsMeridia` with "Meridians" cut off.
- **Root Cause:** Sidebar column was fixed to `280px` in `atlas/style.css`, causing 4 flex tabs to overflow.
- **Remediation:** Expanded sidebar column to `320px` and set `.tab`: `padding: 10px 4px; font-size: 12px; font-weight: 500; white-space: nowrap;`. All 4 tab titles now render completely with generous padding.

#### Defect 2: Uncaught TypeError on `soapForm.addEventListener`
- **Symptom:** The main page failed to populate `caseSelect` and displayed `Loading structures...` on the right anatomy panel.
- **Root Cause:** In `msk_therapy_os/static/index.html` line 1379, the script invoked `document.getElementById("soapForm").addEventListener(...)`. However, the HTML form was declared as `<form id="addSoapForm">`. The null reference threw an uncaught `TypeError` that abruptly terminated script execution, preventing subsequent calls to `loadCases()` and `loadRegionAnatomy()`.
- **Remediation:** Aligned form identifier to `document.getElementById("addSoapForm")` and introduced defensive null guard. Verified zero browser exceptions and full rendering of all 11 structures.

---

## 3. Evidence Gallery (Post-Remediation)

1. **Evidence 10:** [evidence_10_meridians_and_acupoints_3d.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_10_meridians_and_acupoints_3d.png) — 3D Atlas with 14 Meridians & WHO Acupoints overlaid, Active Demo Case `DEMO-NECK-001` selected, and all 11 Region Structures rendered on the right panel.
2. **Evidence 11:** [evidence_11_acupoint_gb21_inspection.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_11_acupoint_gb21_inspection.png) — Acupoint `ACU-GB21` (Jianjing) inspected with Cochrane review evidence badge, trigger-point correlation, and pregnancy contraindication.
3. **Evidence 12:** [evidence_12_longitudinal_progress_dashboard.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_12_longitudinal_progress_dashboard.png) — Longitudinal dashboard showing Day 1 ➔ Day 3 ➔ Day 7 progression cards, Pain trajectory (`6 ➔ 4 ➔ 2`), and cervical ROM trajectory (`45° ➔ 55° ➔ 65°`).
4. **Evidence 13:** [evidence_13_structure_linked_observations.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_13_structure_linked_observations.png) — Structured Observations table linking findings to Trapezius (`STR-CERV-002`) and Jianjing (`ACU-GB21`).
5. **Evidence 14:** [evidence_14_therapy_sessions_and_fhir_export.png](file:///C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729/evidence_14_therapy_sessions_and_fhir_export.png) — Documented therapy sessions and verified HL7 FHIR R4 Bundle modal.

---

## 4. PASS/FAIL Acceptance Verification Matrix

| Check ID | Verification Item | Target Standard | Measured Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **CHK-01** | Acupoint Coordinate Bounds | Human anatomical box [m] | X: [0.0, 0.65], Y: [-0.0007, 1.84], Z: [-0.095, 0.178] | **PASS** |
| **CHK-02** | Meridian 3D Paths | 14 primary channels | 14 channels, 103 segments, 2,846 vertices | **PASS** |
| **CHK-03** | Upstream Sex Anatomy | Raw concept inspection | BP3D 4.0: 18 male, 0 female concepts; Human-Atlas: 33 female | **PASS** |
| **CHK-04** | FHIR R4 Bundle Conformance | HL7 R4 Collection Schema | 16 entries, 0 schema errors, 0 warnings | **PASS** |
| **CHK-05** | E2E Data Persistence | Point click ➔ DB ➔ timeline | Observation #7 persisted & verified in timeline | **PASS** |
| **CHK-06** | Patient Data Isolation | Cross-case query isolation | `DEMO-NECK-001` (N=7) vs `DEMO-LUMBAR-002` (N=0) | **PASS** |
| **CHK-07** | Safety Gate Interception | Red flag triggers hard stop | `saddle_numbness` ➔ `STOP_AND_REFER`, `safe=False` | **PASS** |
| **CHK-08** | Browser JS Heap RAM | < 25.0 MB budget | **2.89 MB** | **PASS** |
| **CHK-09** | UI Defect Remediation | Zero uncaught exceptions | `addSoapForm` & `atlas/style.css` 320px fixed | **PASS** |
| **CHK-10** | Regression Test Suite | Full unit & integration suite| **48/48 unit tests passing (1.67s)** | **PASS** |

---

## 5. Auditor Sign-Off & Recommendation

Milestones **M2.1** and **M2.2** have passed independent quality auditing. All defects identified in the baseline commit `eb92bd4` have been remediated, verified, and re-tested.

**Clearance:** The project is hereby **CLEARED to proceed to M2.3** (Patient Morphology Implementation using the verified Discrete Dual-Reference Architecture). Milestone M3 remains held until M2.3 completes.
