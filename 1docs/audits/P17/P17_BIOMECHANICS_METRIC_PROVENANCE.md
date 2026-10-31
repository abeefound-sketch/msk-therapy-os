# P17 Biomechanical Metric Provenance & Scientific Transparency Audit

## 1. Compliance Standard

Under Acceptance Principle P17-06:
- Every displayed numerical metric must display its calculation derivation, biomechanical assumptions, and scientific citation.
- No synthetic or speculative numbers represented as empirical measurements.
- Clear separation between static lever physics, model optimization estimates, and clinical unknowns.

---

## 2. Metric Provenance Ledger

| Metric Key | UI Display ID | Current Value | Scientific Calculation / Model Source | Reference Literature | Provenance Badge |
|---|---|---|---|---|---|
| Arm Elevation | `#dyn-arm-elev` | Dynamic ($0^\circ - 120^\circ$) | OpenSim coordinate `arm_elev` | Seth et al. (2019) | `OPENSIM_KINEMATICS` |
| Scapular Upward Rot | `#dyn-scap-up` | Dynamic ($0^\circ - 40^\circ$) | OpenSim coordinate `scapula_upward_rot` | Inman et al. (1944); Seth (2019) | `OPENSIM_KINEMATICS` |
| Scapular Tilt | `#dyn-scap-tilt` | Dynamic ($10^\circ - 25^\circ$) | OpenSim coordinate `scapula_anterior_tilt` | Ludewig & Cook (2000) | `OPENSIM_KINEMATICS` |
| Scapulohumeral Ratio | `#val-rhythm-ratio` | Dynamic ($2.00 : 1$) | $\text{Arm Elevation} / \text{Scapular Upward Rot}$ | Inman et al. (1944) | `GEOMETRICALLY_DERIVED` |
| Craniovertebral Angle | `#dyn-cva-angle` | Dynamic ($33^\circ - 55^\circ$) | $\arctan(\Delta y / \Delta x)$ from C7 spinous process to tragus | Yip et al. (2008) | `GEOMETRICALLY_DERIVED` |
| Forward Head Trans | `#dyn-head-trans` | Dynamic ($0 - 50\text{ mm}$) | OpenSim coordinate `head_anterior_trans` | Vasavada et al. (1998) | `OPENSIM_KINEMATICS` |
| Head Weight ($W_{\text{head}}$) | `#dyn-head-weight` | $49.0\text{ N}$ ($5.0\text{ kg}$) | $m \cdot g = 5.0\text{ kg} \times 9.80665\text{ m/s}^2$ | Dempster (1955) anthropometry | `PHYSICAL_CONSTANT` |
| External Lever Arm ($d$) | `#dyn-moment-arm-m` | Dynamic ($0.025 - 0.075\text{ m}$) | Horizontal distance from C7 axis to head center of mass | Vasavada et al. (1998) | `STATICS_LEVER_ARM` |
| External Moment ($M_g$) | `#dyn-ext-moment` | Dynamic ($1.2 - 3.7\text{ N}\cdot\text{m}$) | $M_{\text{gravity}} = W_{\text{head}} \times d_{\text{horizontal}}$ | Static equilibrium ($\Sigma M = 0$) | `PHYSICS_EQUILIBRIUM` |
| Extensor Arm ($r_{\text{eff}}$) | `#dyn-internal-arm` | $3.5\text{ cm}$ | Effective extensor moment arm about C7-T1 | Vasavada et al. (1998) | `LITERATURE_ESTIMATE` |
| Extensor Load ($F_{\text{ext}}$) | `#dyn-extensor-load` | Dynamic ($35 - 105\text{ N}$) | $F_{\text{extensor}} = M_{\text{gravity}} / r_{\text{eff}}$ | Static moment counterbalance | `PHYSICS_EQUILIBRIUM` |
| Axial Compression | `#dyn-axial-comp` | Dynamic ($84 - 154\text{ N}$) | $R_{\text{comp}} = W_{\text{head}} + F_{\text{extensor}}$ | Joint reaction equilibrium | `PHYSICS_EQUILIBRIUM` |
| Disc Tissue Stress | `#dyn-tissue-stress` | `CHƯA HỖ TRỢ` | Requires 3D Finite Element Analysis (FEA) | Blocked offline | `UNAVAILABLE_PRESERVED` |

---

## 3. Scientific Disclaimers & Safety Invariants

- **Non-Diagnostic Invariant**: Mechanical extensor demands and moments reflect basic lever physics and do not prove tissue pathology, disc herniation, or structural deformity.
- **Watermark Invariants**:
  - `MATHEMATICAL MODEL ESTIMATE — NOT MEASURED EMG`
  - `MODEL_GEOMETRY_INSUFFICIENT`
  - `MUSCLE_FORCE_NOT_AVAILABLE`
  - `IDEALIZED EDUCATIONAL EXAMPLE — NOT A UNIVERSAL NORMAL RANGE`
