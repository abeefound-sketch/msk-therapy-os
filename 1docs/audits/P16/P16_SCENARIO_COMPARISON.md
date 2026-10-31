# P16 Audit: Interactive Scenario Comparison Engine

**Milestone:** P16 — Scientific Biomechanics Integrity, Muscle Mechanics & Interactive Self-Education Studio  
**Date:** 2026-10-31  
**Status:** AUDITED AND CERTIFIED  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Classification:** `ENGINEERING_RESEARCH_ONLY`  
**Gate G14 Status:** `BLOCKED_EXTERNAL_DATA`

---

## 1. Objective and Architectural Design

The Scenario Comparison Engine ([`compare_scenarios`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/biomechanics_adapter.py)) enables researchers, educators, and clinicians to contrast two distinct biomechanical movement patterns or postures side-by-side.

It computes explicit differences across:
1. **Kinematic Coordinate Deltas:** Difference in joint angles and translations ($\Delta \theta_i = \theta_{B,i} - \theta_{A,i}$).
2. **Gravitational Mechanics Deltas:**
   - $\Delta d_{\text{horizontal}} = d_{B} - d_{A}$ (in $\text{cm}$)
   - $\Delta M_{\text{gravity}} = M_{B} - M_{A}$ (in $\text{N}\cdot\text{m}$)
   - $\Delta F_{\text{extensor}} = F_{B} - F_{A}$ (in $\text{N}$)
   - $\Delta R_{\text{comp}} = R_{B} - R_{A}$ (in $\text{N}$)
3. **Epistemological Assumptions and Uncertainty:** Highlights 2D static modeling constraints.
4. **Non-Diagnostic Disclaimer:** Explicit warning that higher external torque is a physical lever effect, not diagnostic proof of structural damage or disease.

---

## 2. Exemplar Comparison: Neutral Alignment vs Forward Head Posture

Comparing `SCEN_VASAVADA_CERVICAL_FLEX_EXT` at $t = 1.0\text{ s}$ ($\text{CVA} = 53.0^\circ$) against `SCEN_ILLUSTRATIVE_FORWARD_HEAD` at $t = 1.0\text{ s}$ ($\text{CVA} = 33.0^\circ$):

```json
{
  "status": "SUCCESS",
  "scenario_a": {
    "scenario_id": "SCEN_VASAVADA_CERVICAL_FLEX_EXT",
    "title": "Vasavada Cervical Spine Flexion-Extension (-25° ext to +45° flex)"
  },
  "scenario_b": {
    "scenario_id": "SCEN_ILLUSTRATIVE_FORWARD_HEAD",
    "title": "Illustrative Forward Head Posture & Upper Crossed Dyssynergy"
  },
  "gravitational_mechanics_delta": {
    "delta_moment_arm_cm": 4.0,
    "delta_gravitational_moment_nm": 1.961,
    "delta_extensor_muscle_force_n": 56.0,
    "delta_compression_force_n": 56.0
  },
  "disclaimer": "ILLUSTRATIVE_SCENARIO_COMPARISON_ONLY: Differences in calculated torque and force reflect mathematical lever arm principles in static equilibrium. Higher calculated extensor demand DOES NOT constitute a clinical diagnosis of structural injury, cervical disc pathology, or mechanical impairment."
}
```

---

## 3. Visual Verification

The scenario comparison tool renders as a floating card (`#comparison-card`) above the 3D WebGL viewport:
- Displayed when the user clicks the "So Sánh Kịch Bản" / "Comparison" button (`#btn-mode-comparison`).
- Dismissed cleanly via the close button (`#btn-close-comparison`).
- Authoritative evidence captured in [`1docs/audits/P16/screenshots/02_p16_scenario_comparison.png`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P16/screenshots/02_p16_scenario_comparison.png).
