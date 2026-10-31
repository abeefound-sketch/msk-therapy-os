# P16 Audit: Cervical Gravitational Force & Equilibrium Model Validation

**Milestone:** P16 — Scientific Biomechanics Integrity, Muscle Mechanics & Interactive Self-Education Studio  
**Date:** 2026-10-31  
**Status:** AUDITED AND CERTIFIED  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Classification:** `ENGINEERING_RESEARCH_ONLY`  
**Gate G14 Status:** `BLOCKED_EXTERNAL_DATA`

---

## 1. Physical Assumptions and Equilibrium Formulation

The static biomechanical equilibrium of the human head atop the cervical spine is formulated about the C7-T1 joint center in the sagittal plane:

$$\sum M_{\text{sagittal}} = 0 \implies M_{\text{gravity}} - M_{\text{extensor}} = 0$$

Where:
- $W_{\text{head}} = m_{\text{head}} \cdot g = 5.0\text{ kg} \times 9.80665\text{ m/s}^2 = 49.03\text{ N}$.
- $d_{\text{horizontal}}$ is the horizontal distance between the line of gravity passing through the cranial center of mass (approximated near the sella turcica / external acoustic meatus) and the transverse axis of rotation at C7-T1.
- In neutral posture (Craniovertebral Angle $\text{CVA} \approx 55^\circ$), $d_{\text{horizontal}} \approx 0.025\text{ m}$ ($2.5\text{ cm}$).
- In severe anterior translation / forward head posture ($\text{CVA} \approx 30^\circ$), $d_{\text{horizontal}}$ increases to approximately $0.075\text{ m}$ ($7.5\text{ cm}$).
- $M_{\text{gravity}} = W_{\text{head}} \cdot d_{\text{horizontal}}$:
  - Neutral ($\text{CVA} = 55^\circ$): $49.03\text{ N} \times 0.025\text{ m} = 1.226\text{ N}\cdot\text{m}$.
  - Severe ($\text{CVA} = 30^\circ$): $49.03\text{ N} \times 0.075\text{ m} = 3.677\text{ N}\cdot\text{m}$.

### Internal Equilibrium
To counterbalance $M_{\text{gravity}}$, the posterior extensor muscle group (Splenius capitis/cervicis, Semispinalis capitis/cervicis, Upper Trapezius, Longissimus, and Suboccipitals) must generate an equal and opposite internal extension moment:

$$M_{\text{internal}} = F_{\text{extensor}} \cdot r_{\text{eff}} = M_{\text{gravity}}$$

Using the established anatomical moment arm from Vasavada et al. (1998) ($r_{\text{eff}} = 0.035\text{ m} = 3.5\text{ cm}$):

$$F_{\text{extensor}} = \frac{M_{\text{gravity}}}{r_{\text{eff}}}$$

- Neutral: $F_{\text{extensor}} = \frac{1.226\text{ N}\cdot\text{m}}{0.035\text{ m}} = 35.0\text{ N}$.
- Severe: $F_{\text{extensor}} = \frac{3.677\text{ N}\cdot\text{m}}{0.035\text{ m}} = 105.1\text{ N}$.

### Joint Axial Compression
Applying static force equilibrium in the vertical direction ($\sum F_y = 0$):

$$R_{\text{comp}} = W_{\text{head}} + F_{\text{extensor}}$$

- Neutral: $R_{\text{comp}} = 49.03\text{ N} + 35.0\text{ N} = 84.1\text{ N}$.
- Severe: $R_{\text{comp}} = 49.03\text{ N} + 105.1\text{ N} = 154.1\text{ N}$.

---

## 2. Comparison to Hansraj (2014) Findings

| Parameter | Hansraj (2014) Conceptual Model | P16 Verified Physics Model | Forensic Biomechanical Assessment |
| :--- | :--- | :--- | :--- |
| **Independent Variable** | Flexion tilt angle ($0^\circ, 15^\circ, 30^\circ, 45^\circ, 60^\circ$) | Craniovertebral Angle & anterior translation ($d_{\text{horizontal}}$) | Hansraj varied angular inclination; P16 models horizontal translation & CVA. |
| **Reported Metric** | "Weight on spine" in pounds ($12, 27, 40, 49, 60\text{ lbs}$) | Separate $W_{\text{head}}$ ($\text{N}$), $M_{\text{grav}}$ ($\text{N}\cdot\text{m}$), $F_{\text{ext}}$ ($\text{N}$), $R_{\text{comp}}$ ($\text{N}$) | Hansraj labeled moment/force as "weight", misleading lay audiences. P16 separates all physical entities. |
| **Moment Arm** | Inferred from neck geometry | $r_{\text{eff}} = 3.5\text{ cm}$ (Vasavada et al. 1998 cadaveric/model benchmark) | P16 grounds muscle moment arm in peer-reviewed anatomical literature. |
| **Tissue Stress** | Implied disc vulnerability | Explicitly marked `TISSUE_STRESS_MODEL_UNAVAILABLE` | Stress ($\text{MPa}$) cannot be computed without patient-specific cross-sectional disc area. |

---

## 3. Explicit Model Limitations & Assumptions

The following assumptions are programmatically documented in the adapter output:
1. **2D Sagittal Static Equilibrium:** Analysis assumes $\sum M = 0$ around C7-T1. Dynamic acceleration effects (e.g. rapid head turning or whiplash) are excluded.
2. **Lumped Extensor Equivalent:** Multiple posterior muscle layers are modeled as a single effective muscle group acting at $r_{\text{eff}} = 3.5\text{ cm}$.
3. **Zero Antagonist Co-contraction:** Assumes minimal co-contraction of anterior scalenes and sternocleidomastoid during quiet standing. Real-world co-contraction would further increase joint axial compression.
4. **Passive Structures:** Ligamentous tension (ligamentum nuchae, posterior longitudinal ligament) is neglected at moderate flexion angles where active muscle forces dominate.
5. **Rigid Cranium:** The head is treated as a rigid mass with invariant center-of-gravity relative to the atlanto-occipital joint.

---

## 4. Verification Evidence

All equations were verified through automated unit tests in [`tests/test_p16_biomechanics_integrity.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p16_biomechanics_integrity.py), validating:
- Strict mathematical conservation of units and quantities.
- Monotonic increase of extensor force and compression with decreasing CVA.
- Robust numeric input guards rejecting `NaN` and `Inf` with explicit `ValueError`.
- Programmatic output of `TISSUE_STRESS_MODEL_UNAVAILABLE`.
