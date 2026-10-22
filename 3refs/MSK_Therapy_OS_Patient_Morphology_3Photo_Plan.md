# MSK-Therapy-OS: Three-Photo Patient Morphology and Editable 3D Atlas

**Status:** Proposed engineering design, **not an implemented feature**  
**Target:** M2.3 (patient morphology) on Windows x64, Intel i7-5600U, 8 GB RAM, Intel HD 5500  
**Method:** Constraint-first → Artifact-first → CLI-first → Evidence-first → Cost-aware → Automation-last  
**Intended use:** Education, visualization, and longitudinal observation; **not individual anatomical reconstruction or autonomous diagnosis**.

## 1. Short answer

**Yes, a technician can take three clothed photos (front, side, and back), enter height, weight, waist/hip/chest circumferences, and generate an *approximate, editable 3D body-shape avatar*.** The technician can then adjust its visible proportions, landmarks, and region annotations manually.

**No, three clothed photographs and body measurements cannot accurately reveal the patient's actual internal muscles, fat compartments, blood vessels, nerves, lymphatics, or the depth/position of acupuncture points.** An anatomy atlas can be displayed alongside or transparently over this avatar, but those anatomical structures remain **reference illustrations**, not measured patient-specific anatomy. Treat any acupoint/meridian overlay as a separately labeled traditional educational representation.

The right product design is **a dual-model system**, not a fake personalized medical scan:

1. **Editable patient surface avatar:** approximate external body shape inferred from measurements and clothing-obscured images; user-refined.
2. **Independent reference anatomy atlas:** source-verified bones, muscles, vessels, nerves, etc., presented with their own specimen, licensing, and uncertainty labels.
3. **Structured, patient-specific observation layer:** actual measured circumferences, pain/ROM, palpable landmark observations, skin findings, and session notes, linked to dates and body regions.

## 2. What can and cannot be inferred

| Input/feature | Feasible now | Critical limitation |
|---|---|---|
| Front, side, back photos with clothing | Estimate silhouette, pose, some proportions; align an avatar | Loose clothing obscures the true surface, especially abdomen, hips, breasts, and thighs; photos are not a 3D scan |
| Height and chest/waist/hip circumferences | Constrain model scale and regional girth | Three circumferences do not uniquely specify body geometry |
| Weight and age | Descriptive patient metadata; optional coarse model prior | Neither gives measured body-fat percentage or tissue depth |
| Sex/anatomical reference preference | Select an available *reference* model | Gender identity is not anatomical ground truth; do not automatically equate the two |
| Blood type | Not needed for geometry or typical massage assessment | **Do not collect by default**; collect only for a separately justified clinical purpose |
| 3D skin/body outline | Generate an illustrative avatar with adjustable controls | Not a calibrated volumetric reconstruction |
| Fat distribution | Let operator *illustrate* apparent regional adiposity | Cannot quantify actual fat thickness or visceral fat from clothed photos |
| Muscle, bone, nerve, vascular/lymphatic layers | Render independent atlas reference layers | Not accurate patient-specific size, position, depth, or pathology |
| Traditional acupuncture points/meridians/Dien Chan | Show separately selectable, source-labeled educational annotations | No patient-specific point depth/clinical safety inference from appearance; never claim a channel is a physical vessel |
| Edema/lymphedema | Store circumferences, side-to-side difference, tissue observations, photos, trends | Images cannot stage or diagnose lymphedema; abnormal swelling needs qualified evaluation |

**Practical rule:** the application's 3D model may *resemble* the patient, but must never be labeled “patient-accurate anatomy.”

## 3. Recommended capture workflow

1. **Consent and access controls first.** Until M3 privacy/security gates pass, prototype using synthetic or consented nonclinical test images under an approved process; do **not** upload real patient photos into the current demo. Photos can identify a person even if the face is cropped.
2. Take **front, left-or-right side, and back** photos in consistent lighting. Camera approximately level, subject standing neutrally, feet visible, arms slightly separated, no forced posture. Capture distance and camera height consistently; include a calibration marker or reliable height measurement. Do not require undressing; fitted clothing helps but is optional.
3. Enter *only relevant data*: height, weight, chest/waist/hip circumference; optionally segment circumferences (upper arm, thigh, calf), relevant age range, measurement date, side, and operator. Record units, measurement protocol and whether measurements are self-reported or taken in clinic.
4. **Pose and silhouette extraction:** use a lightweight existing pose-landmark and segmentation tool to estimate visible body outline. Reject low-confidence or obstructed views, and allow manual correction of landmarks and silhouette.
5. **Template fitting:** choose a licensed parametric external-body template, fit height and girth constraints, then optionally minimize the discrepancy between the projected template outline and silhouettes in each view. Expose a confidence/fit-quality indicator; avoid asserting a unique reconstruction.
6. **Technician correction:** use sliders and draggable handles to adjust apparent shoulders, torso depth, abdomen, hip width, limb girths and posture. Preserve the input photos, entered measurements and a full edit history. Changes should update the *surface avatar only*.
7. **Attach observations:** clicking a body region or verified landmark opens a visit-specific annotation card. Measurements and clinical observations remain independent from the appearance of the avatar.
8. **Review and save:** show the reconstructed avatar side by side with the three images and a fit report. Mark the representation **“Illustrative / Manually Adjusted / Not Validated for Internal Anatomy.”**

### Image capture quality checks

- Detect clipped feet/head, substantial pose differences, camera tilt, heavy occlusion or unusually loose garments.
- Detect if front, side, and rear silhouettes disagree too much for stable template fitting.
- Require operator review if body measurements conflict with projected outline.
- **Do not estimate clinical adipose thickness, edema volume, acupuncture depth, or organ positions from these photos.**

## 4. What the technician will be able to edit

**Proposed “Morphology Studio” controls:**

- Preset template: adult male/female/neutral *external avatar* as available and license-cleared; reference anatomy chosen separately.
- Surface parameters: height, shoulder width, chest, waist, hips, apparent abdomen prominence, upper-arm/thigh/calf girths, overall posture and basic asymmetry.
- Visual region tools: mark swelling location, draw an annotation, adjust left/right outlines, place a *reported/palpated* landmark with source and confidence.
- 3D controls: rotate, zoom, isolate regions, show/hide clothing silhouette, transparency, compare photo projection, reset/undo/redo, and save versions.
- Side-by-side model display: **reference anatomy** on one side and **editable patient surface** on the other; optional transparent overlay with a persistent “reference only” label.
- Region/landmark annotations: store muscle or acupoint *reference IDs*, where applicable, **without claiming the exact patient-specific subcutaneous location**. Distinguish a stable traditional atlas point from a patient-specific tenderness/sinh-huyet observation.

**Do not allow manual morphing of internal organs, nerves, blood vessels, or skeletal joints and then label them clinically validated.** When an overlay is geometrically incompatible or uncertainty is too high, disable exact-point snapping and show “reference position unavailable.”

## 5. Minimal architecture: reuse instead of rebuilding

```text
3 clothed photos + measurements
              |
              v
       Capture & QA UI
              |
   Pose/silhouette adapter
              |
              v
    External-avatar fitter  <-----> Manual morphology editor
              |                          |
              +---- Versioned avatar ----+
                            |
        +-------------------+--------------------+
        |                   |                    |
        v                   v                    v
   Patient surface     Reference anatomy   Observation anchors
   (approximate)       (Atlas only)        (measured/reported)
        |                   |                    |
        +-------------------+--------------------+
                            |
                    SOAP + timeline
                     SQLite initially
```

### Open-source building blocks to inspect first

| Component | Reuse decision | Role and caveat |
|---|---|---|
| [Open Anatomy Atlas](https://github.com/CognitionLabSNUC/open-anatomy-atlas) | **KEEP** | 3D reference anatomy, not a per-patient morphable body. BodyParts3D 4.0 is a low-cost renderer option. |
| [MakeHuman](https://github.com/makehumancommunity/makehuman) | **EVALUATE / ADAPT** | Human *surface* proportions and editable parametric controls. Prefer pre-generated low-poly, license-reviewed templates/export for use in existing WebGL viewer; do not run Blender or MakeHuman per visit. |
| [MediaPipe](https://github.com/google-ai-edge/mediapipe) | **EVALUATE / ADAPT** | Browser pose landmarks and image segmentation. Accuracy on clothed subjects and this specific CPU must be benchmarked; current API/model distribution must be checked. |
| [three-mesh-bvh](https://github.com/gkjohnson/three-mesh-bvh) | **OPTIONAL** | Fast raycast/picking and surface queries for stable-mesh annotations; animated/morphed meshes require recalculation/refit or a different anchoring approach. |
| [3D Slicer](https://github.com/Slicer/Slicer) | **DEFER / EXTERNAL** | Clinical imaging segmentation when actual appropriately obtained CT/MRI exists. Not necessary for a three-photo surface-avatar prototype. |
| [SMPL-X](https://github.com/vchoutas/smplx) | **RESEARCH ONLY until cleared** | Useful parametric-body research, but the published license is non-commercial scientific research; do not assume free commercial use. |

**No new monolithic medical simulator is required.** Build an `EditablePatientMorphology` adapter around the current MSK-Therapy-OS, preserving the Atlas, acupoint library, patient observation engine and SOAP timeline. Check **code, mesh, model weights, and datasets separately for licenses**.

## 6. Registration: the essential engineering boundary

Create three distinct coordinate systems:

- `PHOTO_2D`: pixel coordinates and camera view metadata, plus annotated image landmarks.
- `PATIENT_SURFACE_3D`: approximate model coordinates, surface topology/version, manually corrected landmark anchors.
- `REFERENCE_ATLAS_3D`: the original BodyParts3D anatomical specimen coordinates and IDs.

Use explicit, versioned mappings: `photo ↔ patient surface` and separately `patient surface landmark ↔ reference atlas landmark`. **A landmark association is not a patient-specific measurement of an underlying structure.** Never copy raw FMA/FJ mesh coordinates or acupuncture coordinates straight into a personalized avatar and assume exact correspondence.

Anchors on a fixed or deformable mesh may use a local polygon reference plus barycentric weights **only if topology is stable and the anchor is correctly registered**. On remeshing, reproject and revalidate. For traditional meridians, retain source points and landmark descriptions separately from the editable surface visualization. A mesh-snap is a *rendering operation*, not clinical validation.

The clinician/technician should be able to see whether an annotation is **observed**, **measured**, **self-reported**, **source atlas**, **algorithm estimated**, or **manually approximated**, with timestamp and author.

## 7. Data model (illustrative synthetic example)

```json
{
  "case_id": "DEMO-MORPH-001",
  "capture_id": "DEMO-CAPTURE-001",
  "captured_on": "2026-10-22",
  "consent_status": "SYNTHETIC_DEMO_ONLY",
  "photos": ["front", "side_left", "back"],
  "measures": {
    "height_cm": 168,
    "weight_kg": 78,
    "chest_cm": 102,
    "waist_cm": 96,
    "hip_cm": 105,
    "calf_left_cm": 41,
    "calf_right_cm": 39,
    "measured_by": "demo_operator",
    "measurement_protocol": "DEMO_PROTOCOL_V1"
  },
  "surface_avatar": {
    "source": "licensed_external_template",
    "template_version": "demo-v1",
    "fit_method": "measurement_constrained_plus_manual_review",
    "fit_quality": "UNVERIFIED_DEMO",
    "edits": [{"region": "abdomen", "parameter": "surface_prominence", "value": 0.3}]
  },
  "anatomy_overlay": {
    "source": "BodyParts3D_4.0",
    "status": "REFERENCE_ONLY_NOT_PATIENT_SPECIFIC"
  },
  "observations": [{
    "visit": "DEMO-VISIT-001",
    "region": "left_calf",
    "kind": "measured_circumference",
    "value_cm": 41,
    "annotation_origin": "operator_measured"
  }]
}
```

Use linked database tables rather than duplicating full records on every visit. Include provenance, missing values, template version, units, author, method and confidence. Preserve prior models for comparisons rather than silently rewriting historic visits. **Avoid collecting blood group, government IDs or unrelated sensitive data.**

## 8. Longitudinal tracking and research

For each follow-up visit, optionally repeat standard-view photos and **repeat objective measures with the same protocol**. Visualize:

- Front/side/back before-and-after silhouettes, with camera/perspective comparability warnings.
- Changes in measured regional circumferences and side-to-side differences, timestamped alongside pain and functional scores.
- Clickable *observation* heatmaps for tenderness, skin changes, measured swelling and other user-entered findings.
- Traditional atlas points/meridians in a distinct overlay, with changing **observed tenderness or symptoms** rather than assertions that a meridian has “opened.”
- Missing-data flags, adverse-event entries, referral notes, and method/observer changes.

A longitudinal trend is not proof that massage, DDS, or a traditional theory caused improvement. Any effectiveness study requires a qualified protocol, consistent outcomes, comparison strategy and safety oversight.

## 9. Safety, privacy, and scope limits

- **Do not deploy this to real patients on the existing demo stack.** Patient photos and medical histories require consent, access controls, encrypted storage/transfer, audit logs, backups, retention rules and applicable legal review. Keep development fixtures synthetic until the M3 safety/privacy gate passes.
- Three photos and anthropometrics do not provide depth guidance for needles, DDS electrodes, high-force pressure or spinal manipulation. **Never generate treatment intensity, needle depth or anatomical clearance from the fitted avatar.**
- For swelling, sudden unilateral changes, suspected infection or thrombosis, prioritize qualified assessment. The model must not infer or stage lymphedema from photos alone.
- Clinical source labeling must remain separate from traditional acupuncture, Sen Sib or Dien Chan schemas. User-generated experimental points are not validated anatomical entities.
- The patient's right to decline photography or use an alternative manual 2D body map should be supported.

## 10. Delivery plan and acceptance gates

### M2.3a — Thin prototype (synthetic only)

- Add 3-view photo import/capture screen with capture-quality guidance, manual landmarks and typed measurements.
- Load a low-poly external avatar template and adjust surface dimensions to measurements.
- Provide operator sliders/drag handles, side-by-side silhouette comparison, undo/redo, and explicit illustrative labels.
- Save/reload a versioned avatar and connect it to the existing DEMO case and timeline.
- Run on the target Windows PC; capture real browser evidence and report **total Chrome process memory, GPU memory if available, load time, interaction responsiveness**, not only JavaScript heap.

### M2.3b — Robust annotation and comparison

- Add photo/mesh point tagging, side-specific landmarks, edema/girth measurement sites, and history overlays.
- Support repeat photos and measurements under a documented consistent measurement protocol.
- Preserve separation of three coordinate spaces and provenance for every visible marker.
- Add data-isolation, migration, invalid-input, poor-photo, refit and regression tests.

### M3 — Safe real-patient pilot preparation, not automatic launch

- Implement consent, accounts and roles, encryption, audit, export/delete, recovery, incident workflows and professional review.
- Validate against clinical assessment standards and local privacy/health regulations before any real use.
- Where clinically justified, support an *external* 3D Slicer workflow using actual imaging; do not require it for normal visits.

### Definition of Done for the prototype

1. With **three synthetic clothed-view images** and entered measurements, user can create a *visually plausible* adjustable external avatar without invented internal anatomy.
2. User can modify torso/limb girth, posture and landmark positions, then save, reload and revert the edit history.
3. Screens clearly distinguish **patient surface approximation**, **reference anatomy**, **traditional overlays** and **observed/measured findings**.
4. Two demo visits with different girth measurements show a correct time-linked comparison; no cross-case data leakage.
5. Three-photo fitting failure is shown plainly when images are obstructed; manual-only fallback works.
6. All existing Atlas, SOAP, safety and FHIR regression tests pass and are independently re-run.
7. Reproducible screenshots, raw performance logs, unit and browser tests are committed; no unsupported “patient-specific anatomy” claims.

## 11. Key decision for the coding agent

> **Extend, do not rebuild.** Implement a patient-specific **external surface editor and observation tracker**, not a fictional internal anatomical reconstruction. Reuse a licensed body template, optional lightweight landmark detection, the existing Atlas renderer, SQLite and the current SOAP/timeline APIs. Implement M2.3a with synthetic assets first, test manually in the browser, and keep M3 patient privacy/safety gates explicit. If 3-photo fitting is unreliable on target hardware, ship measurement-driven manual fitting instead and label the limitation.

## References / provenance

**Existing project documents (user-provided):** `MORPHOLOGY_FEASIBILITY.md`, `INTEGRATION_HANDOFF_M2_EXT.md`. The former correctly warns against treating skin morphing as clinically valid internal anatomy; its proposed male/female model completeness and low-memory performance require independent validation.

**External technical sources:**

- Open Anatomy Atlas: https://github.com/CognitionLabSNUC/open-anatomy-atlas
- MakeHuman: https://github.com/makehumancommunity/makehuman
- MediaPipe pose and segmentation: https://github.com/google-ai-edge/mediapipe ; https://github.com/google-ai-edge/mediapipe-samples-web
- Three.js spatial queries: https://github.com/gkjohnson/three-mesh-bvh
- 3D Slicer medical image segmentation: https://github.com/Slicer/Slicer
- SMPL-X noncommercial research license: https://github.com/vchoutas/smplx

**Source caution:** These references document upstream capabilities. They do **not** establish that the proposed three-photo fitting workflow has been implemented, validated on the target laptop, or approved for clinical decisions.
