# P16 Audit: Muscle Mechanics Inspector & Mode Verification

**Milestone:** P16 — Scientific Biomechanics Integrity, Muscle Mechanics & Interactive Self-Education Studio  
**Date:** 2026-10-31  
**Status:** AUDITED AND CERTIFIED  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Classification:** `ENGINEERING_RESEARCH_ONLY`  
**Gate G14 Status:** `BLOCKED_EXTERNAL_DATA`

---

## 1. Architectural Overview of Muscle Mechanics Modes

The Muscle Mechanics Inspector provides four distinct visualization modes, each governed by strict scientific validation boundaries to prevent misleading users:

```text
+----------------------------------------------------------------------------------------------------+
|                                  MUSCLE MECHANICS INSPECTOR MODES                                  |
+----------------------------------------------------------------------------------------------------+
| Mode A: ANATOMICAL PARTICIPATION  -> Origin, Insertion, Primary Actions, Functional Roles         |
| Mode B: GEOMETRIC CHANGE          -> Mandatory Empty State: MODEL_GEOMETRY_INSUFFICIENT            |
| Mode C: ESTIMATED ACTIVATION      -> Static Optimization [0.0..1.0] with Watermark Banner          |
| Mode D: ESTIMATED FORCE           -> Mandatory Empty State: MUSCLE_FORCE_NOT_AVAILABLE             |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Mode-by-Mode Specification & Empty State Audits

### Mode A: Anatomical Participation (`MODE_A_ANATOMICAL_PARTICIPATION`)
- **Scientific Purpose:** Visualizes which muscles anatomically participate in the observed movement based on standard anatomical texts (Gray's Anatomy, Moore's Clinically Oriented Anatomy).
- **Returned Data:** Muscle ID, English and Vietnamese nomenclature, anatomical functional role (`AGONIST`, `ANTAGONIST`, `SYNERGIST`, `STABILIZER`), primary action list, skeletal origin, and skeletal insertion.
- **Scientific Guard:** Absolutely no fabricated activation percentages or force numbers. `normalized_activation = null` and `estimated_force_n = null`.

### Mode B: Geometric Change (`MODE_B_GEOMETRIC_CHANGE`)
- **Scientific Purpose:** Evaluates dynamic muscle-tendon length changes and 3D line-of-action wrapping curves.
- **Enforced Boundary:** The rigid osseous surface meshes (BodyParts3D) in the client application lack volumetric fiber wrapping cylinders and via-point curves.
- **Mandatory Empty State:**
  - Status: `MODEL_GEOMETRY_INSUFFICIENT`
  - Empty State Code: `MODEL_GEOMETRY_INSUFFICIENT`
  - UI Notice: *"Continuous 3D muscle line-of-action wrapping curves and dynamic fiber length changes require discrete musculoskeletal path definitions which are unmeshed in the current rigid osseous surface model."*
  - Muscles array: Strictly empty (`[]`).

### Mode C: Estimated Activation (`MODE_C_ESTIMATED_ACTIVATION`)
- **Scientific Purpose:** Displays normalized mathematical muscle activations ($a \in [0.0, 1.0]$) derived from pre-computed static optimization (`.sto`) datasets.
- **Mandatory Disclaimers:**
  - Persistent Watermark Banner: `MATHEMATICAL MODEL ESTIMATE — NOT MEASURED EMG`
  - Badge text: `Chế độ C: Kích Hoạt (Ước tính mô hình)`
  - If a scenario lacks a pre-computed `.sto` file, returns mandatory empty state `MUSCLE_ACTIVATION_NOT_AVAILABLE`.

### Mode D: Estimated Force in Newtons (`MODE_D_ESTIMATED_FORCE`)
- **Scientific Purpose:** Assesses true contractile muscle force in Newtons ($F = a \cdot F_{\text{max}} \cdot f(l, v)$).
- **Enforced Boundary:** Calculating individual muscle forces in Newtons requires live OpenSim dynamic equilibrium solving and physiological cross-sectional area (PCSA) parameterization, which is blocked in this offline environment.
- **Mandatory Empty State:**
  - Status: `MUSCLE_FORCE_NOT_AVAILABLE`
  - Empty State Code: `MUSCLE_FORCE_NOT_AVAILABLE`
  - UI Notice: *"Individual muscle force calculation in Newtons requires live OpenSim dynamic equilibrium solving with validated physiological cross-sectional area (PCSA) and force-length-velocity parameterization, which is blocked offline. Multiplying generic activation by arbitrary constants is strictly rejected to preserve scientific biomechanical validity."*
  - Muscles array: Strictly empty (`[]`).

---

## 3. Automated Verification Results

All 4 modes and their empty states were verified via:
1. Backend unit tests: [`tests/test_p16_biomechanics_integrity.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p16_biomechanics_integrity.py)
2. Interactive Chromium browser E2E tests: [`tests/test_p16_playwright.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p16_playwright.py)

Both suites passed with 100% compliance.
