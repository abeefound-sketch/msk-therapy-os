# P16 Audit: OpenSim Biomechanical Data Provenance & Runtime Governance

**Milestone:** P16 — Scientific Biomechanics Integrity, Muscle Mechanics & Interactive Self-Education Studio  
**Date:** 2026-10-31  
**Status:** AUDITED AND CERTIFIED  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Classification:** `ENGINEERING_RESEARCH_ONLY`  
**Gate G14 Status:** `BLOCKED_EXTERNAL_DATA`

---

## 1. Provenance Manifest and Cryptographic Integrity

Milestone P16 enforces complete transparency regarding the origin, mathematical generation method, and cryptographic hash of every biomechanical motion (`.mot`) and muscle activation (`.sto`) dataset in MSK-Therapy-OS.

All datasets are stored in `msk_therapy_os/data/biomechanics/` and mirrored identically to `msk_therapy_os/static/education/data/`.

### Verified Dataset Inventory

| Scenario ID | Dataset Title | Motion File (`.mot`) | SHA-256 Hash | Muscle File (`.sto`) | SHA-256 Hash | Origin & License |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SCEN_SETH_2019_ARM_ELEVATION` | Unloaded Arm Elevation (0°–120°) | `seth_shoulder_elevation.mot` | `b52e93c4c4e186957fc6a7e089d4a767821872465b07bedcb04a7ca7595149a8` | `seth_shoulder_elevation.sto` | `7fb3ee1d1be3b1da27c5bf95a5fbcdd3eb3b9d038dc3b5736db2e95144aa7508` | Seth Scapulothoracic Model (Seth et al. 2016, 2019). Apache 2.0 / SimTK. |
| `SCEN_ILLUSTRATIVE_ROUNDED_ELEVATION` | Altered Scapular Dyskinesis Elevation | `illustrative_rounded_elevation.mot` | `d720d297594dfc1e55ec50e6fc8eef6ae16371bfab10246a36db5f764a8ebceb` | `illustrative_rounded_elevation.sto` | `295c52c5031b269550b73c2a690bf03dc0eb81ec74d8dd8fdfd42c300f28e21a` | Illustrative Simulation. Synthetic research profile. |
| `SCEN_VASAVADA_CERVICAL_FLEX_EXT` | Vasavada Cervical Flexion/Extension | `vasavada_cervical_flexion_extension.mot` | `105a3064e43fdbf381c828ca41cc9a6e127976e5d8095fefab75421ae0393cb1` | `vasavada_cervical_flexion_extension.sto` | `2ff853907e59b207d5718df2cfbb8dc5a0b7bf0e38676d1e4e0ae5c48b71d9d4` | Vasavada Neck Model (Vasavada et al. 1998, 2010). Apache 2.0 / SimTK. |
| `SCEN_ILLUSTRATIVE_FORWARD_HEAD` | Forward Head Posture & UCS Kinematics | `illustrative_forward_head_posture.mot` | `c4daec0ce3ce30da90d96d74492bf1ceef21f200c406859eec2161bf90df4be8` | `illustrative_forward_head_posture.sto` | `b68a73fe91a5cb741ec85d564fa7e8ef6e6df669781ff7ea9ec217c093a201ba` | Illustrative Postural Simulation. Synthetic research profile. |
| `SCEN_CERVICAL_AXIAL_ROTATION` | Cervical Left-Right Axial Rotation | `cervical_axial_rotation.mot` | `7bb48dbcb8c2a72a14ce0d5af3093a89bb4afc77e21858276f12603bc7723e2f` | `cervical_axial_rotation.sto` | `a3c21d4896d56ebdc6333030be75bcd212b42c1caf9f4fd92cb630685d3b3b17` | Standardized Kinematic Trajectory (White & Panjabi 1990). P16 Generated. |
| `SCEN_CERVICAL_LATERAL_BENDING` | Cervical Left-Right Lateral Bending | `cervical_lateral_bending.mot` | `3bec69762393edc6c4c751440c9d47faee54c8f8738a4303f38845988069359d` | `cervical_lateral_bending.sto` | `94a9b05e34b912b1e62b54085baaa3c047ba47bbcdab46682dd22b8788f9d69c` | Standardized Kinematic Trajectory (White & Panjabi 1990). P16 Generated. |
| `SCEN_CONCURRENT_FORWARD_HEAD_ROUNDED_SHOULDER` | Concurrent FHP & Rounded Shoulder | `concurrent_fwd_head_rounded_shoulder.mot` | `7f7aa4aa7a8c3d97f3efc2919d8544a04d2653ea91535eb0fc6793cf837580b0` | `concurrent_fwd_head_rounded_shoulder.sto` | `8e6c7ea84d9f7535b9148d281ef5f22f7b88939c1935e40e6955bca0a3a2c5a2` | Multi-segment Concurrent Biomechanics Model. P16 Generated. |

---

## 2. OpenSim Runtime Governance & Offline Enforcement

### Live Solver Status
The system environment was formally audited for OpenSim C++ libraries (`libOpenSimCommon.so` / `OpenSimCommon.dll`) and Python bindings (`import opensim`). Neither is installed on this standalone target machine.

In strict compliance with Milestone P16 specifications, live execution status is locked:
```json
{
  "live_opensim_runtime_status": "OPENSIM_LIVE_SIMULATION_BLOCKED",
  "offline_environment_enforced": true,
  "live_opensim_runtime_notice": "OpenSim C++ binaries and Python bindings are not installed on this workstation; live simulation is blocked offline."
}
```

### Prevention of Fabricated Dynamics
In previous releases, applications without live solvers were susceptible to estimating muscle forces by multiplying static optimization activations by scalar multipliers (e.g. $F = a \times 500\text{ N}$). Milestone P16 establishes that:
1. Muscle force calculation in Newtons requires dynamic inverse/forward equilibrium solving and physiological cross-sectional area (PCSA) parameterization.
2. In the absence of a live OpenSim runtime, Mode D returns empty state `MUSCLE_FORCE_NOT_AVAILABLE`.
3. Arbitrary scalar multiplication is strictly rejected as scientifically fraudulent.

---

## 3. Coordinate System Conventions

All motion files adhere strictly to standard OpenSim coordinate frame definitions:
- **X-axis:** Anterior (+X forward).
- **Y-axis:** Superior (+Y upward).
- **Z-axis:** Lateral right (+Z to subject's right).

Joint rotations adhere to right-hand Euler conventions matching standard musculoskeletal modeling literature (Wu et al. 2005 ISB recommendation).
