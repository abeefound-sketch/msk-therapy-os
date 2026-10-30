# P13-D: BIOMECHANICS DATA ADAPTER & KINEMATICS AUDIT
## Musculoskeletal Therapy OS (MSK-Therapy-OS) — Milestone P13
### OpenSim Motion Ingestion · Scapulohumeral Rhythm Verification · Invariant Bounds

- **Milestone:** P13 (Phase P13-D: Biomechanics Integration)
- **Document ID:** `1docs/audits/P13/P13_D_BIOMECHANICS_ADAPTER.md`
- **Implementation File:** [`msk_therapy_os/biomechanics_adapter.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/biomechanics_adapter.py)
- **Audit Date:** 2026-10-30
- **Auditor:** Musculoskeletal Biomechanics Integration Engineer & Principal Architect
- **Status:** APPROVED & TESTED

---

## 1. OBJECTIVE & INVARIANTS

The Biomechanics Adapter integrates quantitative musculoskeletal data structures into MSK-Therapy-OS to support biomechanical reasoning while enforcing scientific integrity boundaries:

```text
G14 = BLOCKED_EXTERNAL_DATA
clinical_depth_guidance_allowed = False
EDUCATIONAL_SIMULATION != PATIENT_SPECIFIC_MEASUREMENT
MODEL_PREDICTION != EMPIRICALLY_VALIDATED_MOTION
MUSCLE_HIGHLIGHT != MEASURED_MUSCLE_ACTIVATION
POSTURAL_APPEARANCE != MEDICAL_DIAGNOSIS
```

### Motion Data Truth Invariant:
A static polygon mesh (such as `anatomy.glb`) does not possess continuous volumetric dynamic deformation capabilities without a rigorously validated finite-element or multi-body musculoskeletal rig. Where arbitrary vertex morphing or unvalidated deformations could mislead clinicians or learners, the system explicitly reports:
```python
SHOULDER_MOTION_STATUS_UNAVAILABLE = "SHOULDER_MOTION_DATA_UNAVAILABLE"
```

---

## 2. OPENSIM DATA FORMAT INGESTION

The adapter implements [`OpenSimFormatParser`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/biomechanics_adapter.py), supporting both `.mot` (motion kinematics) and `.sto` (storage time-series):

### 2.1 Parser Specifications
1. **Header Processing:** Extracts OpenSim metadata blocks, verifies `inDegrees` flags (`yes`/`no`), parses row and column declarations (`nRows`, `nColumns`), and handles comments (`//`, `#`).
2. **Column Alignment:** Validates that the first column is monotonically increasing `time`, mapping all subsequent columns to distinct joint and coordinate DOFs.
3. **Data Integrity:** Rejects malformed rows with missing values or non-numeric tokens with descriptive line-numbered syntax exceptions.

### 2.2 Deterministic Interpolation
[`OpenSimMotionData.interpolate`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/biomechanics_adapter.py) provides deterministic $O(\log N)$ piecewise linear interpolation:
$$\hat{v}(t) = v_0 + \frac{t - t_0}{t_1 - t_0} (v_1 - v_0)$$
For queries outside the interval $[t_{\min}, t_{\max}]$, values are clamped to the boundary endpoints to prevent divergence.

---

## 3. PHYSIOLOGICAL RANGE VALIDATION & COORDINATES

The adapter checks all incoming kinematics against established literature bounds (Ludewig & Cook 2000, McClure et al. 2001, Inman et al. 1944):

| Coordinate Name | Biological Meaning | Valid Range (deg) | Evidence Reference |
| :--- | :--- | :--- | :--- |
| `arm_elevation` | Total thoracohumeral elevation | $[0.0, 180.0]$ | Inman et al. (1944) |
| `arm_flexion` | Sagittal humerothoracic flexion | $[-30.0, 180.0]$ | American Academy of Orthopaedic Surgeons (AAOS) |
| `scapula_upward_rot` | Scapular upward/downward rotation | $[-10.0, 60.0]$ | Ludewig & Cook (2000) |
| `scapula_anterior_tilt` | Scapular anterior/posterior tilt | $[-20.0, 40.0]$ | McClure et al. (2001) |
| `scapula_protraction` | Scapular protraction/retraction | $[-15.0, 45.0]$ | Borstad & Ludewig (2005) |
| `clavicle_elevation` | Sternoclavicular elevation | $[-10.0, 40.0]$ | Inman et al. (1944) |
| `clavicle_retraction` | Sternoclavicular retraction | $[-20.0, 40.0]$ | Ludewig et al. (2009) |

---

## 4. SCAPULOHUMERAL RHYTHM COMPUTATION

The method [`ShoulderKinematicsValidator.compute_scapulohumeral_rhythm`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/biomechanics_adapter.py) calculates the ratio between glenohumeral elevation and scapulothoracic upward rotation:

$$\text{Rhythm Ratio} = \frac{\theta_{\text{GH elevation}}}{\theta_{\text{ST upward rotation}}}$$

### Clinical Interpretation Categories:
1. **`PHYSIOLOGICAL_NORMAL_2_TO_1` ($1.6 \le \text{Ratio} \le 2.4$):** Normal rhythm coordinated by the serratus anterior and lower/upper trapezius force couple.
2. **`SCAPULAR_HYPOMOBILITY_DYSKINESIA` ($\text{Ratio} > 2.4$):** Insufficient scapular upward rotation relative to humeral elevation. Indicates pectoralis minor tightness or serratus anterior inhibition, common in rounded shoulder posture.
3. **`COMPENSATORY_EARLY_SHRUG` ($0.5 < \text{Ratio} < 1.6$):** Excessive early scapular elevation driven by an overactive upper trapezius and levator scapulae.

---

## 5. AUDIT VERDICT

The Biomechanics Adapter fulfills all Gate P13-D requirements:
- Provides robust OpenSim ingestion and interpolation.
- Performs rigorous coordinate validation and ratio computation.
- Enforces fail-closed scientific boundaries without pseudo-scientific extrapolation.
