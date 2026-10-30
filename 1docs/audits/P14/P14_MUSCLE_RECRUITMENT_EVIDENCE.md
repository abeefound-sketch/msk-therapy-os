# P14 Muscle Recruitment Evidence & Visualization Audit

**Milestone:** P14 — Evidence-Grounded Dynamic Biomechanics, Muscle Recruitment Visualization & Interactive MSK Education  
**Date:** October 31, 2026  
**Auditor / Engineer:** Principal Musculoskeletal Biomechanics Engineer & Scientific Content Auditor  
**Status:** VALIDATED  

---

## 1. Executive Summary & Purpose

This audit evaluates the muscle recruitment visualization pipeline implemented in `shoulder_lab.js` and `anatomy_viewer.js`. 

In historical educational software, muscle highlighting frequently conflates anatomical presence with physiological activation or measured EMG electrical signals. Milestone P14 establishes rigorous scientific transparency by strictly separating visualization into distinct operational modes, complete with non-negotiable watermark badges and explicit indicators when data is unavailable.

---

## 2. Three-Mode Visualization Architecture

### Mode 1: Anatomical Function (`ANATOMICAL_FUNCTION`)
- **Scientific Meaning:** Visualizes anatomical participation and orientation of muscular structures associated with a movement phase (e.g., Deltoid, Rotator Cuff, Trapezius, Serratus Anterior).
- **Mandatory UI Watermark:**
  `ANATOMICAL FUNCTION — NOT COMPUTED ACTIVATION`
- **Presentation:** Structural meshes retain original anatomical materials or focus highlights; no computed activation percentage or bioelectrical measurement is implied.

### Mode 2: Model-Estimated Muscle Activity (`MODEL_ESTIMATED`)
- **Scientific Meaning:** Renders normalized muscle activations derived from OpenSim static optimization (`seth_shoulder_elevation.sto`). Static optimization minimizes the sum of squared muscle activations ($\sum a_m^2$) or forces subject to multi-body equations of motion.
- **Mandatory UI Watermark:**
  `MATHEMATICAL MODEL ESTIMATE — NOT MEASURED EMG`
- **Dynamic Color Ramp:** Normalized activation $[0.0, 1.0]$ is mapped to an intuitive thermal spectrum:
  - Low ($0.0 - 0.3$): Blue (`#3b82f6`)
  - Moderate ($0.3 - 0.7$): Yellow (`#eab308`)
  - High ($0.7 - 1.0$): Red (`#ef4444`)
- **Missing Channel Handling:** If a muscle group was not solved in the static optimization routine (e.g. Pectoralis Minor in the glenohumeral elevation model), the interface strictly displays:
  `"MUSCLE ACTIVATION DATA UNAVAILABLE"` / `"DỮ LIỆU KÍCH HOẠT CHƯA CÓ TRONG MÔ HÌNH"`

### Mode 3: Scenario Comparison (`SCENARIO_COMPARISON`)
- **Scientific Meaning:** Contrasts standard kinematic motion against an illustrative forward shoulder posture elevation scenario (`illustrative_rounded_elevation.mot`).
- **Mandatory UI Watermark:**
  `ILLUSTRATIVE POSTURE SCENARIO SIMULATOR (NOT A DIAGNOSTIC MEASUREMENT)`
- **Presentation:** Demonstrates how altered resting alignment (anterior tilt and protraction) theoretically impacts subacromial clearance without attributing clinical disease to posture alone.

---

## 3. Mathematical Static Optimization Formulation

For clarity and scientific auditability, the OpenSim static optimization formulation used to compute estimated activations $a_m$ in `seth_shoulder_elevation.sto` is summarized:

$$\min_{a_m} J = \sum_{m=1}^{M} a_m^2$$
$$\text{subject to: } \sum_{m=1}^{M} [r_m(\mathbf{q}) \cdot F_m(a_m, l_m, v_m)] = \boldsymbol{\tau}_{\text{gen}}(\mathbf{q}, \dot{\mathbf{q}}, \ddot{\mathbf{q}})$$
$$0 \le a_m \le 1 \quad \forall m \in [1, M]$$

Where:
- $r_m(\mathbf{q})$ is the instantaneous muscle moment arm as a function of joint coordinates $\mathbf{q}$.
- $F_m(a_m, l_m, v_m)$ is the force-length-velocity contraction model.
- $\boldsymbol{\tau}_{\text{gen}}$ is the generalized torque required to produce the prescribed trajectory.

**Core Limitation:** Static optimization does not capture co-contraction, motor unit recruitment strategies, or individual reflex adaptations. It is a mathematical model estimate, not empirical surface or fine-wire electromyography.

---

## 4. UI Acceptance & Audit Results

1. **Watermark Enforcement:** Verified that switching between Mode 1, Mode 2, and Mode 3 immediately renders the required scientific watermark in both English and Vietnamese.
2. **Missing Data Handling:** Verified that querying Pectoralis Minor in Mode 2 displays `DATA UNAVAILABLE` with 0% fill, preventing false simulation claims.
3. **Dynamic Synchrony:** Verified that scrubbing the timeline slider at $t = 0.5\text{ s}$, $1.0\text{ s}$, and $1.8\text{ s}$ updates deltoid and supraspinatus activations in lockstep with humeral elevation.
