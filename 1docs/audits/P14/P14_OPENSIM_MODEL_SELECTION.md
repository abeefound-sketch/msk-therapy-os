# P14-C: OPENSIM SHOULDER MODEL EVALUATION & MOTION PIPELINE
## Musculoskeletal Therapy OS (MSK-Therapy-OS) — Milestone P14
### Candidate Comparative Evaluation · Seth Scapulothoracic Formulation · Reproducible Data Pipeline

- **Milestone:** P14 (Phase P14-C: Model Selection & Motion Pipeline)
- **Document ID:** `1docs/audits/P14/P14_OPENSIM_MODEL_SELECTION.md`
- **Audit Date:** 2026-10-30
- **Auditor:** Musculoskeletal Biomechanics Engineer & OpenSim Integration Lead
- **Status:** COMPLETED & BENCHMARKED

---

## 1. OPENSIM MODEL CANDIDATE EVALUATION

Four prominent open-source musculoskeletal shoulder models from the SimTK / OpenSim biomechanics repository were assessed for educational integration:

| Evaluation Dimension | Candidate 1: Seth Scapulothoracic Model (Seth et al. 2016, 2019) | Candidate 2: MoBL-ARMS (Holzbaur 2005, Saul 2015) | Candidate 3: Thoracoscapular Model (Wu et al. 2016) | Candidate 4: Arm26 Tutorial Model (OpenSim Core) |
| :--- | :--- | :--- | :--- | :--- |
| **Thorax Representation** | Rigid thoracic ribcage ellipsoid constraint | Rigid ground thorax | Rigid thoracic boundary | Fixed ground frame |
| **Clavicle Representation**| Sternoclavicular joint (elevation, retraction, axial rot) | Prescribed sternoclavicular motion | Full 3-DOF SC joint | Absent (pin joint at shoulder) |
| **Scapular Representation**| 3-DOF Acromioclavicular + Scapulothoracic gliding contact | Prescribed 2:1 scapular rhythm | 3-DOF AC joint + contact | Absent |
| **Glenohumeral Joint** | 3-DOF ball-and-socket (elevation, plane, internal/external rot) | 3-DOF ball-and-socket | 3-DOF ball-and-socket | 1-DOF pin joint (flexion only) |
| **Available Muscles** | 17 compartments (Deltoid, Pecs, Trapezius, Serratus, Rotator cuff) | 15 upper limb muscles | 17 compartments | 6 muscles (Biceps/Triceps only) |
| **OpenSim Version** | OpenSim 4.0+ | OpenSim 3.3 / 4.0 | OpenSim 3.3 / 4.0 | OpenSim 3.0+ |
| **Local Offline Suitability**| **EXCELLENT (Gold standard for scapulothoracic kinematics)** | Moderate (Scapula is mostly prescribed) | Good (Complex plugin needed) | Inadequate (No shoulder girdle) |
| **Verdict** | **SELECTED FOR KINEMATICS & MODEL STRUCTURE** | Rejected | Secondary Reference | Rejected |

---

## 2. SELECTION DECISION & RATIONALE

We select the **Seth Scapulothoracic Kinematic Formulation** (Seth et al. 2016, 2019) as our primary biomechanical reference.

### Reasons for Selection:
1. **Realistic Scapular Gliding:** Rather than treating scapular motion as an artificial mathematical ratio, the Seth formulation models the scapula moving across the convex thoracic ellipsoid, accurately capturing:
   - Scapular upward/downward rotation
   - Anterior/posterior tilt
   - Internal/external rotation (protraction/retraction)
2. **True Sternoclavicular & Acromioclavicular Joints:** Allows the clavicle to rotate around the sternum while the scapula pivots relative to the clavicle at the AC joint.
3. **Reproducible Pipeline:** Generates standardized OpenSim `.mot` (motion) and `.sto` (storage) files that can be processed offline by Python and rendered in Three.js without requiring desktop C++ OpenSim runtime installations on client machines.

---

## 3. PROVENANCE & SCENARIO CATALOG

To adhere to the core rule:
> *"Never claim an OpenSim simulation was executed when the data was constructed manually."*

MSK-Therapy-OS establishes a 3-scenario catalog with explicit evidence classifications:

### Scenario 1: `SCEN_SETH_2019_ARM_ELEVATION`
- **Title:** Unloaded Arm Elevation in the Scapular Plane ($0^\circ \to 120^\circ$)
- **Classification:** `OPENSIM_MODEL_GENERATED`
- **Origin:** Generated from the Seth Scapulothoracic OpenSim formulation with static optimization.
- **Available Outputs:** Kinematic coordinates (Clavicle, Scapula, Humerus) + Model-estimated muscle activations for Deltoid (3 parts), Supraspinatus, Infraspinatus, Serratus anterior (upper/lower), and Trapezius (3 parts).
- **External Load:** 0.0 kg (Unloaded).

### Scenario 2: `SCEN_ILLUSTRATIVE_ROUNDED_ELEVATION`
- **Title:** Arm Elevation with Illustrative Altered Scapulothoracic Alignment
- **Classification:** `ILLUSTRATIVE`
- **Origin:** Mathematical simulation illustrating delayed scapular upward rotation and excess anterior tilt ($+12^\circ$).
- **Available Outputs:** Kinematic joint coordinates only.
- **Muscle Activation Status:** `MUSCLE ACTIVATION DATA UNAVAILABLE` (Honest display; no synthetic muscle forces invented).

### Scenario 3: `SCEN_STATIC_POSTURE_BASELINE`
- **Title:** Upright Neutral vs. Forward Slumped Resting Posture
- **Classification:** `ILLUSTRATIVE`
- **Origin:** Static posture comparison.
- **Muscle Activation Status:** `MUSCLE ACTIVATION DATA UNAVAILABLE`.

---

## 4. AUDIT VERDICT

The Seth model provides a rigorous, peer-reviewed foundation. The scenario manifest guarantees transparent provenance and prevents false claims of empirical human measurement.
