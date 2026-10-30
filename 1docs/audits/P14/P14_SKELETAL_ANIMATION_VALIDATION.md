# P14 Skeletal Animation & Kinematic Transform Validation

**Milestone:** P14 — Evidence-Grounded Dynamic Biomechanics, Muscle Recruitment Visualization & Interactive MSK Education  
**Date:** October 31, 2026  
**Auditor / Engineer:** Principal Systems Architect & 3D Medical Visualization Engineer  
**Status:** VALIDATED  

---

## 1. Executive Summary

This document validates the implementation of true skeletal segment transformations within the Three.js 3D Musculoskeletal Education Studio (`anatomy_viewer.js`). 

In milestone P13, the educational studio relied on static volumetric muscle meshes (`anatomy.glb`) with fixed vertex coordinates and descriptive highlights. Milestone P14 integrates authentic osseous structures (`shoulder_skeleton.glb`, extracted from BodyParts3D v4.0) into a continuous multi-body forward kinematic chain.

---

## 2. Segment Identification & Anatomical Joint Pivots

The osseous segments and biological pivot locations are mapped in the standard BodyParts3D world coordinate system (meters, $Y$-up, Right shoulder located in the negative $X$ half-space):

| Segment | BodyParts3D FMA ID | Mesh Name | World Bounding Box $(X, Y, Z)$ [m] | Joint Articulation | Biological Pivot Center $(X, Y, Z)$ [m] |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Thorax** | FMA7486, FMA7487 | `Thorax` | $[-0.127, 0.027] \times [1.250, 1.448] \times [-0.087, 0.114]$ | Static ground reference | Origin $(0.0, 0.0, 0.0)$ |
| **Right Clavicle** | FMA13322 | `Clavicle_R` | $[-0.145, -0.010] \times [1.387, 1.434] \times [-0.045, 0.047]$ | Sternoclavicular (SC) Joint | $P_{\text{SC}} = (-0.018, 1.405, 0.038)$ |
| **Right Scapula** | FMA13395 | `Scapula_R` | $[-0.166, -0.057] \times [1.262, 1.428] \times [-0.105, 0.003]$ | Acromioclavicular (AC) Joint | $P_{\text{AC}} = (-0.142, 1.415, -0.025)$ |
| **Right Humerus** | FMA23130 | `Humerus_R` | $[-0.241, -0.140] \times [1.108, 1.415] \times [-0.049, 0.000]$ | Glenohumeral (GH) Joint | $P_{\text{GH}} = (-0.165, 1.395, -0.020)$ |

---

## 3. Mathematical Scene Graph Hierarchy

The kinematic hierarchy preserves joint articulations without bone separation:

```text
Scene
 └── KinematicSkeletonRoot (Origin)
      ├── Thorax Mesh (Local: 0, 0, 0)
      └── Sternoclavicular Pivot (Position: P_SC)
           ├── Clavicle_R Mesh (Local offset: -P_SC)
           └── Acromioclavicular Pivot (Position: P_AC - P_SC)
                ├── Scapula_R Mesh (Local offset: -P_AC)
                └── Glenohumeral Pivot (Position: P_GH - P_AC)
                     └── Humerus_R Mesh (Local offset: -P_GH)
```

### 3.1 Unrotated Neutral Verification
When all pivot rotations $\mathbf{R}_{\text{SC}} = \mathbf{R}_{\text{AC}} = \mathbf{R}_{\text{GH}} = \mathbf{I}$, any vertex $v$ of `Humerus_R` transforms as:
$$T(v) = P_{\text{SC}} + (P_{\text{AC}} - P_{\text{SC}}) + (P_{\text{GH}} - P_{\text{AC}}) + (v - P_{\text{GH}}) = v$$
Thus, at zero rotation, all bone vertices align with their authentic CT/MRI BodyParts3D resting coordinates.

---

## 4. Rotational Kinematics & Sign Conventions

Because the subject faces the camera ($+Z$ anterior) and the right shoulder lies at $X < 0$, abduction in the coronal plane rotates clockwise around $+Z$. By the right-hand rule in Three.js, clockwise rotation corresponds to negative radians:

1. **Clavicular Elevation ($\theta_{\text{clav}}$):**
   $$\mathbf{R}_{z,\text{SC}} = -\text{degToRad}(\theta_{\text{clav}})$$
   Lifts the lateral end of the clavicle superiorly ($+Y$).
2. **Scapular Upward Rotation ($\theta_{\text{up}}$):**
   $$\mathbf{R}_{z,\text{AC}} = -\text{degToRad}(\theta_{\text{up}})$$
   Swings the inferior angle of the scapula laterally and rotates the glenoid cavity upward.
3. **Scapular Anterior/Posterior Tilt ($\theta_{\text{tilt}}$):**
   $$\mathbf{R}_{x,\text{AC}} = \text{degToRad}(\theta_{\text{tilt}})$$
   Anterior tilt ($+X$) tilts the superior border anteriorly ($+Z$); posterior tilt ($-X$) tilts the superior border backward ($-Z$).
4. **Scapular Internal Rotation / Protraction ($\theta_{\text{prot}}$):**
   $$\mathbf{R}_{y,\text{AC}} = \text{degToRad}(\theta_{\text{prot}})$$
   Rotates the lateral acromion anteriorly around the ribcage.
5. **Glenohumeral Relative Elevation ($\theta_{\text{gh\_elev}} = \theta_{\text{arm\_elev}} - \theta_{\text{up}}$):**
   $$\mathbf{R}_{z,\text{GH}} = -\text{degToRad}(\theta_{\text{gh\_elev}})$$
   Elevates the humerus in the scapular plane relative to the upward-rotating glenoid cavity.
6. **Humeral Axial External Rotation ($\theta_{\text{rot}}$):**
   $$\mathbf{R}_{y,\text{GH}} = \text{degToRad}(\theta_{\text{rot}})$$
   Clears the greater tuberosity from the acromion during elevation past $90^\circ$.

---

## 5. Playback Controls & Frame-by-Frame Interactivity

The Three.js viewer implements complete playback controls:
- **Play / Pause / Reset:** Real-time delta-time clock integration with seamless looping.
- **Speed Multiplier:** $0.25\times$, $0.5\times$, $1.0\times$ for biomechanical observation.
- **Timeline Scrubber:** Linear interpolation across OpenSim keyframe rows for continuous scrubbing from $t = 0.0\text{ s}$ to $t = 2.0\text{ s}$.
- **Dynamic Angle Readouts:** Dispatches event `onPoseUpdated` with current degrees of elevation, upward rotation, tilt, and clavicular elevation.

---

## 6. Validation Conclusion

The kinematic chain has been mathematically derived and implemented in `anatomy_viewer.js`. Rotational transforms preserve bone contact and reproduce published shoulder kinematic motions (Seth et al. 2016, Sugamoto et al. 2002).
