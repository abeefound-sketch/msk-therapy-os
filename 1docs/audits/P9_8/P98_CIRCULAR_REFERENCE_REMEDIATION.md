# P9.8 Circular Reference Remediation & Landmark Provenance Hardening

**Document ID:** `P98_CIRCULAR_REFERENCE_REMEDIATION.md`  
**Milestone:** P9.8 Anatomical Ground Truth & Evidence Integrity Hardening  
**Status:** APPROVED | CIRCULARITY ELIMINATED & QUARANTINED  
**Date:** 2026-10-28  

---

## 1. Problem Statement: Circular Coordinate Derivations

In Milestone P9.6, thirty Class D points were elevated to Class B. Among these were four medial foot points along the Spleen channel:
- `SP2` (Dadu - distal to 1st metatarsophalangeal joint)
- `SP3` (Taibai - proximal to 1st metatarsophalangeal joint)
- `SP4` (Gongsun - base of 1st metatarsal bone)
- `SP5` (Shangqiu - depression anterior and inferior to medial malleolus, tuberosity of navicular)

To formulate localization rules for these points, four new landmarks were registered in `msk_therapy_os/landmark_registry.py`:
1. `LM_MTP1_DISTAL_R`
2. `LM_MTP1_PROXIMAL_R`
3. `LM_METATARSAL1_BASE_R`
4. `LM_NAVICULAR_TUBEROSITY_R`

### Forensic Residual Analysis:
When compared against the legacy raw positions in `acupuncture_3d.json`:
- `LM_MTP1_DISTAL_R` vs Legacy `SP2`: residual $= 0.0000	ext{ mm}$
- `LM_MTP1_PROXIMAL_R` vs Legacy `SP3`: residual $= 0.0000	ext{ mm}$
- `LM_METATARSAL1_BASE_R` vs Legacy `SP4`: residual $= 0.0000	ext{ mm}$
- `LM_NAVICULAR_TUBEROSITY_R` vs Legacy `SP5`: residual $= 0.0782	ext{ mm}$

**Scientific Diagnosis:** The landmarks were not derived from independent bone segmentations or anatomical imaging; rather, they were derived by sampling the very unverified legacy points they were supposed to calibrate. Defining a rule that places SP2 at `LM_MTP1_DISTAL_R` created a circular tautology:
$$	ext{Legacy Point } SP2 \longrightarrow 	ext{Landmark } LM \longrightarrow 	ext{Rule } SP2 \implies 	ext{Zero Verification Value}$$

---

## 2. Architectural Root Cause

The BodyParts3D 4.0 release (model `FJ2810`) provides an integrated skin boundary mesh (`skin_body.obj`) and major skeletal bones (femur, tibia, fibula, pelvis, skull, spine, rib cage, scapula, humerus, radius, ulna). However, **it lacks discrete 3D volume segmentations for individual tarsal bones (navicular, cuneiforms, cuboid) and metatarsal bases**. 

Without segmented boundaries for the 1st metatarsal base or navicular tuberosity, any landmark registered on the medial foot skin in `FJ2810` is an unverified surface approximation.

---

## 3. Remediation & Fail-Closed Quarantine Architecture

To ensure strict evidence integrity, P9.8 implemented three architectural remediation layers:

### Layer 1: AnatomicalProvenanceDependencyValidator
A pure-Python graph validator (`msk_therapy_os/landmark_dependency_validator.py`) that constructs a directed graph of all landmark-to-rule dependencies:
- Detects circular self-references where distance $< 1.0	ext{ mm}$ and landmark verification is ungrounded.
- Verifies FMA ontology mappings and reference standards.
- Classifies circularities into `UNDISCLOSED_CIRCULARITY` (critical failure) vs `QUARANTINED_CIRCULARITY` (safely blocked).

### Layer 2: Landmark Registry Status Quarantine
In `msk_therapy_os/landmark_registry.py`, the four circular landmarks were marked:
```python
verification_status = "BLOCKED_CIRCULAR_DEPENDENCY"
```
Their uncertainty radii were expanded from $\pm 3.0	ext{ mm}$ to $\pm 25.0	ext{ mm}$ to prevent misleading precision claims.

### Layer 3: Rule Solver Fail-Closed Enforcement
In `msk_therapy_os/point_localization_rules.py`:
- `resolve_point_location()` checks the verification status of all referenced landmarks. If any referenced landmark contains `"BLOCKED"`, resolution immediately returns `None` (fail-closed).
- The rules for `SP2, SP3, SP4, SP5` were explicitly set to `quality_class = "CLASS_D"`.
- When `resolve_point_location()` returns `None`, `SpatialResolver` falls back cleanly to `GEOMETRIC_SURFACE_APPROXIMATION` (legacy raycast) and marks the point as Class D.

---

## 4. Verification Results

Running `AnatomicalProvenanceDependencyValidator.validate_all()` produces:
- **Total Landmarks Audited:** 50
- **Total Rules Audited:** 120
- **Undisclosed Circularities:** **0** (ZERO)
- **Quarantined Circularities:** **4** (`SP2`, `SP3`, `SP4`, `SP5`)
- **Blocked Landmarks:** **4** (`LM_MTP1_DISTAL_R`, `LM_MTP1_PROXIMAL_R`, `LM_METATARSAL1_BASE_R`, `LM_NAVICULAR_TUBEROSITY_R`)
- **Missing Landmarks:** **0**
- **Validation Verdict:** **PASS (Integrity Hardened)**

---

## 5. Roadmap for P9.9 De-Quarantine

To legitimately de-quarantine and elevate `SP2, SP3, SP4, SP5` to Class B in a future milestone:
1. Acquire high-resolution segmented tarsal and metatarsal meshes (e.g., from NIH Visible Human Project or open CT/MRI foot segmentations).
2. Register the foot bone meshes to the BodyParts3D `FJ2810` reference coordinate frame using Iterative Closest Point (ICP).
3. Identify the true bony tuberosity of the navicular bone and 1st metatarsal base.
4. Raycast radially to the skin boundary to locate the soft-tissue palpation depression.
5. Re-register the landmarks with verifiable FMA IDs and independent provenance.
