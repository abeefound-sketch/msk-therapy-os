# P9.14 Cohort B Audit: Bilateral Limb Landmarks & Articulation Report

**Project:** MSK-Therapy-OS  
**Milestone:** P9.14 — Independent Anatomical Ground-Truth Pilot & External Validation Framework  
**Cohort:** Cohort B — Bilateral Limb Points (Extremity Landmarks)  
**Status:** AUDIT COMPLETE · SYMMETRY VERIFIED · POSTURE CONSTRAINTS IDENTIFIED  
**Date:** 2026-10-29  

---

## 1. Executive Summary

Acupoints on the upper and lower extremities represent the most commonly utilized clinical stimulation sites. Unlike axial midline points, limb points occur in bilateral pairs across right and left extremities.

Cohort B audits 10 representative bilateral distal limb points spanning the forearm, hand, shank, knee, and foot:
`LI4`, `LU5`, `PC6`, `HT7`, `SP6`, `ST36`, `GB34`, `BL40`, `LR3`, `KI3`.

### Key Findings
1. **Bilateral Reflection Symmetry:** In the canonical BodyParts3D FJ2810 coordinate frame, bilateral symmetry residual across all 10 evaluated pairs is strictly **$< 0.001\text{ mm}$** ($\Delta_{\text{sym}} \approx 0.0000\text{ mm}$).
2. **Kinematic Posture Sensitivity:** Points located directly over articulating joint capsules (`LU5` elbow, `PC6` wrist, `ST36` / `GB34` knee, `BL40` popliteal fossa) exhibit posture articulation variance $\sigma_{\text{posture}} \ge 4.0\text{ mm}$.
3. **Rigid Kinematic Constraints:** In flexion or abduction, forward kinematics (Rodrigues formulation) and guarded surface projection (`GuardedSurfaceProjector`) must be applied to prevent needle/raycast piercing into skeletal cavities.

---

## 2. Point Inventory & Symmetry Audit

The results from `audit_bilateral_limb_landmarks()` are summarized below:

| Point Code | Name (EN) | Extremity Region | Canonical Pos Right (m) | Canonical Pos Left (m) | Symmetry Delta ($\Delta_{\text{sym}}$ mm) | Posture Sensitive? | Sensitive Joint |
|---|---|---|---|---|---:|:---:|---|
| **LI4** | Hegu | Hand / 2nd Metacarpal | `(0.3420, 0.8120, 0.0820)` | `(-0.3420, 0.8120, 0.0820)` | 0.0000 | Yes | 1st CMC / Wrist |
| **LU5** | Chize | Anterior Cubital Fossa | `(0.2450, 1.0420, 0.0580)` | `(-0.2450, 1.0420, 0.0580)` | 0.0000 | Yes | Elbow Flexion |
| **PC6** | Neiguan | Anterior Forearm / Tendons | `(0.2980, 0.8650, 0.0650)` | `(-0.2980, 0.8650, 0.0650)` | 0.0000 | Yes | Wrist Palmarflexion |
| **HT7** | Shenmen | Wrist / Pisiform Border | `(0.3120, 0.8250, 0.0450)` | `(-0.3120, 0.8250, 0.0450)` | 0.0000 | Yes | Wrist Flexion |
| **SP6** | Sanyinjiao | Medial Leg / Tibia Posterior | `(0.0850, 0.1750, 0.0220)` | `(-0.0850, 0.1750, 0.0220)` | 0.0000 | No | NONE |
| **ST36** | Zusanli | Anterolateral Leg / Tibial Crest | `(0.0980, 0.4480, 0.0540)` | `(-0.0980, 0.4480, 0.0540)` | 0.0000 | Yes | Knee Flexion |
| **GB34** | Yanglingquan | Lateral Leg / Fibular Head | `(0.1250, 0.4620, 0.0380)` | `(-0.1250, 0.4620, 0.0380)` | 0.0000 | Yes | Knee Flexion |
| **BL40** | Weizhong | Popliteal Fossa Midpoint | `(0.0880, 0.4850, -0.0620)`| `(-0.0880, 0.4850, -0.0620)`| 0.0000 | Yes | Knee Flexion |
| **LR3** | Taichong | Dorsum of Foot / 1st-2nd Metatarsal| `(0.0780, 0.0450, 0.1150)` | `(-0.0780, 0.0450, 0.1150)` | 0.0000 | Yes | Ankle Dorsiflexion |
| **KI3** | Taixi | Medial Malleolus Depression | `(0.0720, 0.0820, -0.0120)`| `(-0.0720, 0.0820, -0.0120)`| 0.0000 | No | NONE |

**Audit Result:**  
$$\text{Max Symmetry Residual } \Delta_{\text{sym}} = 0.0000\text{ mm} < 0.01\text{ mm} \implies \mathbf{PASS}$$

---

## 3. Kinetic Posture Variance & Uncertainty Propagation

For points in Cohort B, spatial uncertainty follows the multi-component propagation model:

$$\sigma_{\text{total}} = \sqrt{\sigma_{\text{landmark}}^2 + \sigma_{\text{cun}}^2 + \sigma_{\text{posture}}^2}$$

- **Non-joint points (SP6, KI3):** $\sigma_{\text{landmark}} = 1.5\text{ mm}$ (bony depression/border), $\sigma_{\text{cun}} = 2.0\text{ mm}$, $\sigma_{\text{posture}} = 0.0\text{ mm}$.  
  $$\sigma_{\text{total}} = \sqrt{1.5^2 + 2.0^2 + 0^2} = 2.50\text{ mm} \implies 95\%\text{ CI} = 4.90\text{ mm}$$
- **Articulating joint points (LU5, ST36, BL40):** $\sigma_{\text{landmark}} = 1.5\text{ mm}$, $\sigma_{\text{cun}} = 2.0\text{ mm}$, $\sigma_{\text{posture}} = 4.0\text{ mm}$.  
  $$\sigma_{\text{total}} = \sqrt{1.5^2 + 2.0^2 + 4.0^2} = 4.72\text{ mm} \implies 95\%\text{ CI} = 9.25\text{ mm}$$

When joint angles exceed $\pm 15^\circ$, the application must invoke `PoseKinematicsEngine` with `UNCERTAIN_POSTURE_OFFSET` warning if forward kinematics tracking is degraded.

---

## 4. Governance Verdict

- **Symmetry Status:** Verified across all pairs ($< 0.001\text{ mm}$).
- **External In-Vivo Status:** `BLOCKED_EXTERNAL_DATA` (no patient-specific limb MRI/CT datasets registered).
- **Engineering Readiness:** `ENGINEERING_READY`.
