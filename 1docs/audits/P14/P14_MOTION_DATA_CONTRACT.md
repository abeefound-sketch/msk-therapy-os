# P14 Motion Data Contract & OpenSim Pipeline Specification

**Milestone:** P14 — Evidence-Grounded Dynamic Biomechanics, Muscle Recruitment Visualization & Interactive MSK Education  
**Date:** October 31, 2026  
**Auditor / Architect:** Principal Systems Architect & Musculoskeletal Biomechanics Engineer  
**Status:** VALIDATED  

---

## 1. Executive Summary & Purpose

This document defines the strict data contract, ingestion constraints, coordinate semantics, and mathematical boundaries governing the integration of OpenSim motion files (`.mot`) and static optimization muscle activation files (`.sto`) within the MSK-Therapy-OS Education Studio.

To ensure computational integrity, prevent memory exhaustion, and guarantee zero misrepresentation of simulation data as human clinical measurements, all data passing through `msk_therapy_os/biomechanics_adapter.py` must comply with this specification.

---

## 2. Invariant Scientific Boundaries

The following non-negotiable architectural boundaries are enforced across all parsers, serializers, and visual presentation components:

```text
G14 = BLOCKED_EXTERNAL_DATA
clinical_depth_guidance_allowed = False
RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY
CLINICAL_VALIDATION = NOT_ESTABLISHED

ANATOMICAL_MODEL != SUBJECT_SPECIFIC_ANATOMY
ILLUSTRATIVE_KINEMATICS != MEASURED_KINEMATICS
MUSCLE_ACTION_DESCRIPTION != MUSCLE_ACTIVATION_MEASUREMENT
OPTIMIZED_MUSCLE_ACTIVATION != MEASURED_EMG
SIMULATED_FORCE != MEASURED_HUMAN_FORCE
POSTURE_VARIATION != CLINICAL_DIAGNOSIS
ANIMATION_SUCCESS != BIOMECHANICAL_VALIDATION
```

---

## 3. Storage & Motion File Syntax Standards

OpenSim storage (`.sto`) and motion (`.mot`) files are ASCII tab-delimited or whitespace-delimited tabular datasets. MSK-Therapy-OS parser (`OpenSimFormatParser`) implements strict compliance:

### 3.1 Header Specification
```text
<File_Name_or_Type>
version=1
nRows=<integer>
nColumns=<integer>
inDegrees=yes|no
endheader
time    <col_1>    <col_2>    ...    <col_n>
<t_0>   <val_0,1>  <val_0,2>  ...    <val_0,n>
...
```

### 3.2 Ingestion Security & Adversarial Guardrails
The parser enforces the following programmatic checks on every input buffer:
1. **File Size Bound:** Input payload must not exceed $10\text{ MB}$ (`10,485,760` bytes). Exceeding this raises `ValueError("OpenSim file exceeds 10MB safety limit")`.
2. **Mandatory Header Identification:** Buffer must contain recognized tokens (`nRows`, `nColumns`, `endheader`, or `version`).
3. **Leading Timestamp Column:** Column index 0 must be named `time` (case-insensitive).
4. **No Duplicate Headers:** Every column identifier must be unique. Duplicate columns immediately raise `ValueError`.
5. **Strict Monotonicity:** Time column values $t_i$ must satisfy $t_{i} > t_{i-1}$ strictly. Non-monotonic or decreasing time values raise `ValueError`.
6. **Finite Floating-Point Values:** Every parsed token must be finite. `NaN`, `+Inf`, `-Inf`, or unparseable string tokens raise `ValueError`.

---

## 4. Coordinate Definitions & Anatomical Degrees of Freedom

The shoulder rhythm engine maps OpenSim model coordinates into the 3D anatomical viewer. The canonical model coordinates follow the Seth Scapulothoracic Shoulder Model (Seth et al. 2016):

| Coordinate Name | Biological Joint | Degree of Freedom | Physiological Range (deg) | Model Bounds (deg) | Viewer Mapping |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `time` | N/A | Timeline (s) | $0.0 - 10.0$ | $0.0 - 2.0$ | Time scrubber |
| `arm_elevation` / `r_shoulder_elev` | Glenohumeral (GH) | Arm elevation in scapular plane | $0^\circ - 180^\circ$ | $0^\circ - 120^\circ$ | Humerus pivot local rotation $Z$ / $X$ |
| `arm_flexion` | Glenohumeral (GH) | Plane of elevation angle | $-30^\circ - 180^\circ$ | $0^\circ - 30^\circ$ | Scapular plane offset |
| `arm_rot` | Glenohumeral (GH) | Axial humeral rotation (Int/Ext) | $-90^\circ - 90^\circ$ | $0^\circ - 20^\circ$ | Humerus axial twist $Y$ |
| `scapula_upward_rot` | Scapulothoracic (ST) | Upward rotation | $-10^\circ - 60^\circ$ | $0^\circ - 41.2^\circ$ | Scapula pivot local rotation $Z$ |
| `scapula_anterior_tilt` | Scapulothoracic (ST) | Anterior (+) / Posterior (-) tilt | $-20^\circ - 40^\circ$ | $10^\circ \to -5^\circ$ | Scapula pivot local rotation $X$ |
| `scapula_internal_rot` | Scapulothoracic (ST) | Protraction / Internal rotation | $-10^\circ - 50^\circ$ | $15^\circ \to 20^\circ$ | Scapula pivot local rotation $Y$ |
| `clavicle_elev` | Sternoclavicular (SC) | Clavicular elevation | $-10^\circ - 40^\circ$ | $0^\circ - 14.5^\circ$ | Clavicle pivot local rotation $Z$ |

---

## 5. Muscle Activation Data Contract (`.sto`)

Musculoskeletal static optimization files quantify estimated muscle activity. The data contract defines:

1. **Normalized Range:** Normalized muscle activation values $a_m(t)$ must lie within $[0.0, 1.0]$.
2. **Channel Mapping:**
   - `deltoid_anterior` $\to$ Anterior Deltoid
   - `deltoid_lateral` $\to$ Lateral / Middle Deltoid
   - `deltoid_posterior` $\to$ Posterior Deltoid
   - `supraspinatus` $\to$ Supraspinatus
   - `infraspinatus` $\to$ Infraspinatus
   - `subscapularis` $\to$ Subscapularis
   - `serratus_anterior` $\to$ Serratus Anterior
   - `trapezius_upper` $\to$ Upper Trapezius
   - `trapezius_lower` $\to$ Lower Trapezius
   - `pectoralis_minor` $\to$ Pectoralis Minor
   - `pectoralis_major` $\to$ Pectoralis Major
3. **Missing Data Handling:** If a muscle channel is queried that was not included in the optimization solve (e.g. Rhomboids or Levator Scapulae), the system MUST render:
   `"MUSCLE ACTIVATION DATA UNAVAILABLE"`
4. **Mandatory UI Watermarks:**
   - In Mode 1 (Anatomical Function): `ANATOMICAL FUNCTION — NOT COMPUTED ACTIVATION`
   - In Mode 2 (Model-Estimated Activity): `MATHEMATICAL MODEL ESTIMATE — NOT MEASURED EMG`
   - In Mode 3 (Scenario Comparison): `ILLUSTRATIVE POSTURE SCENARIO SIMULATOR (NOT A DIAGNOSTIC MEASUREMENT)`

---

## 6. Scenario Manifest Container

Every dataset exposed to the educational front-end is governed by a `BiomechanicalScenarioManifest` record:

```python
@dataclass
class BiomechanicalScenarioManifest:
    scenario_id: str
    scenario_title: str
    source_model: str
    source_model_version: str
    source_model_hash: str
    source_motion_file: str
    motion_file_hash: str
    model_license: str
    motion_data_origin: str
    generation_method: str
    coordinate_system: str
    joint_coordinate_names: List[str]
    angle_units: str
    time_units: str
    muscle_output_type: str  # "ESTIMATED_ACTIVATION" or "UNAVAILABLE"
    external_load_assumptions: str
    subject_specific: bool
    validation_level: str  # "ILLUSTRATIVE", "OPENSIM_MODEL_GENERATED", etc.
    scientific_references: List[str]
    known_limitations: List[str]
```

### Registered Datasets:
1. `SCENARIO-SETH-ELEVATION-01`:
   - Title: *OpenSim Seth Model — 0° to 120° Scapular-Plane Abduction*
   - Motion File: `msk_therapy_os/data/biomechanics/seth_shoulder_elevation.mot` (SHA-256: `64259b1fae9efae4179339e1eec709b19dfb4fb39642e1d7cf9be3c166d49c63`)
   - Muscle File: `msk_therapy_os/data/biomechanics/seth_shoulder_elevation.sto` (SHA-256: `ce9d1a884fa88d5e16541f5e2776c5b766c1f4e5bf5069f06ddae13c847d0f9d`)
   - Validation Level: `OPENSIM_MODEL_GENERATED`
2. `SCENARIO-ILLUSTRATIVE-ROUNDED-02`:
   - Title: *Illustrative Forward Shoulder Posture Elevation*
   - Motion File: `msk_therapy_os/data/biomechanics/illustrative_rounded_elevation.mot` (SHA-256: `a9354023dc4efc8c1eeef7f050b1c97a5f6a99252328baecbb56ba9c2ea24a25`)
   - Muscle File: None (`MUSCLE ACTIVATION DATA UNAVAILABLE`)
   - Validation Level: `ILLUSTRATIVE`

---

## 7. Verification Status

The data contract has been compiled and validated against the internal parser suite. Unit test assertions confirm:
- 10MB limit enforcement.
- Duplicate column header rejection.
- Monotonic timestamp verification.
- Scenario catalog registration and checksum matching.
