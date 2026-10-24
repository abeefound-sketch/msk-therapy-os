# ANATOMICAL LANDMARK REGISTRATION, PARAMETRIC CUN & POSE-AWARE 3D ACUPOINT ENGINE
## TECHNICAL ARCHITECTURAL SPECIFICATION (P9 SPEC)

**Document Version:** 1.0.0  
**Effective Date:** 2026-10-24  
**Status:** IMPLEMENTED & VALIDATED  
**Author:** Principal 3D Geometry, Computational Anatomy & Biomedical Software Architect  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Target Mesh Reference:** BodyParts3D 4.0 FJ2810 Skin Mesh (`FMA:7163`)  

---

## 1. SCOPE & CLINICAL SAFETY BOUNDARIES

This specification defines the computational geometry, coordinate transformations, parametric proportionality, and clinical abstention semantics of the **MSK-Therapy-OS P9 Anatomical Landmark Registration Engine**.

> [!CAUTION]
> **Clinical Abstention Notice:**
> MSK-Therapy-OS is an educational, biomechanical reference and non-invasive procedural visualization system.
> Under no circumstances does this engine compute, claim, or validate internal surgical trajectory, needle insertion depth, or invasive procedure safety. When anatomical landmarks are unresolvable or posture exceeds calibration limits, the engine refuses calculation and flags results as `UNREGISTERED` or `UNCERTAIN_POSTURE_OFFSET`.

---

## 2. CANONICAL COORDINATE FRAME SPECIFICATION

All spatial calculations, 3D mesh vertices, and landmark anchors are standardized according to the canonical reference frame:

1. **Reference 3D Model:** BodyParts3D Release 4.0 (FJ2810 canonical adult male skin mesh, 634,000 triangles).
2. **Measurement Units:** SI Meters ($\text{m}$) internally; rendered and reported in millimeters ($\text{mm}$) for user clarity.
3. **Cartesian Coordinate System:** Standard Right-Handed Cartesian:
   - $+X$ Axis: Lateral Right (patient's anatomical right).
   - $+Y$ Axis: Superior (Up, toward cranium).
   - $+Z$ Axis: Anterior (Front, toward ventral surface).
4. **Origin Alignment:**
   - Ground Plane ($Y = 0.00\text{ m}$): Floor contact plane directly below center of gravity.
   - Soles of Feet: $Y \approx 0.00\text{ m}$.
   - Pelvic Center / DanTian: $Y \approx 0.86\text{ m}$.
   - C7 Spinous Process (Dazhui GV14): $Y \approx 1.478\text{ m}$.
   - Vertex of Cranium (Baihui GV20): $Y \approx 1.718\text{ m}$.
5. **Physiological Adult Human Envelope:**
   $$X \in [-0.38\text{ m}, +0.38\text{ m}], \quad Y \in [-0.05\text{ m}, +1.76\text{ m}], \quad Z \in [-0.28\text{ m}, +0.28\text{ m}]$$

---

## 3. ANATOMICAL LANDMARK ONTOLOGY

The landmark ontology categorizes physical structures into six discrete ontological classes:

```
+---------------------------------------------------------------------------------------------------+
|                                 P9 ANATOMICAL LANDMARK ONTOLOGY                                   |
+--------------------------+--------------------------+---------------------------------------------+
| Class                    | Primary Examples         | Morphological Invariance                   |
+--------------------------+--------------------------+---------------------------------------------+
| BONY_LANDMARK            | C7 spine, Inion,         | Rigid skeletal attachment; tracks bone     |
|                          | Acromion, ASIS, Malleoli | movement rigidly with 0 posture error.      |
| JOINT_LANDMARK           | Glenohumeral center,     | Kinematic rotation axis pivot; constant     |
|                          | Elbow, Knee joint center | inter-segment distance.                     |
| TENDON_LANDMARK          | Achilles, Biceps tendon, | Palpable linear tensile structure; shifts   |
|                          | Palmaris longus          | with muscle tension and joint angle.        |
| MUSCLE_BORDER            | Lateral trapezius border,| Topographic border; expands with muscle     |
|                          | Anterior SCM margin      | contraction / hypertrophy.                  |
| SKIN_CREASE              | Palmar wrist crease,     | Flexion crease; strictly valid only in      |
|                          | Cubital, Popliteal crease| calibrated rest posture.                    |
| SURFACE_TOPOGRAPHIC      | Jugular notch,           | Palpable fossa or subcutaneous depression.  |
|                          | Anatomical snuffbox      |                                             |
+--------------------------+--------------------------+---------------------------------------------+
```

Each registered landmark implements:
- `landmark_id`: Unique identifier (e.g. `LM_C7_SPINE`).
- `canonical_position`: $[X, Y, Z]$ in meters on FJ2810.
- `fma_id`: Curated link to the Foundational Model of Anatomy (e.g. `FMA:13337`).
- `skeletal_anchor`: Descriptive physical palpation guideline.
- `tolerance_radius_mm`: Maximum allowable registration threshold.
- `clinical_uncertainty_mm`: Expected physiological variation across general population.

---

## 4. MATHEMATICAL FORMULATION OF UMEYAMA SVD REGISTRATION

Given a set of $n$ source landmarks $X = \{x_1, \dots, x_n\} \subset \mathbb{R}^3$ and target canonical landmarks $Y = \{y_1, \dots, y_n\} \subset \mathbb{R}^3$:

### 4.1. Centroids and Demeaning
$$\mu_x = \frac{1}{n} \sum_{i=1}^n x_i, \quad \mu_y = \frac{1}{n} \sum_{i=1}^n y_i$$
$$X_c = x_i - \mu_x, \quad Y_c = y_i - \mu_y$$

### 4.2. Cross-Covariance Matrix $H$
$$H = \frac{1}{n} X_c^T Y_c \in \mathbb{R}^{3 \times 3}$$

### 4.3. Singular Value Decomposition
$$H = U \Sigma V^T$$
Where $U, V \in O(3)$ are calculated via cyclic Jacobi rotations on the symmetric $3 \times 3$ matrix $H^T H$.
To guarantee a proper rotation matrix ($\det(R) = +1$) and prevent reflection artifacts:
$$S = \begin{pmatrix} 1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & d \end{pmatrix}, \quad d = \text{sign}(\det(V U^T))$$
$$R = V S U^T$$

### 4.4. Translation Vector
$$t = \mu_y - s R \mu_x$$

### 4.5. Degeneracy & Rejection Conditions
1. **Count Constraint:** If $n < 3$, return `UNREGISTERED` (system underconstrained).
2. **Collinearity Test:** If the cross products of all normalized vectors $\frac{x_i - x_0}{\|x_i - x_0\|}$ are zero, return `DEGENERATE_COLLINEAR_LANDMARKS`.
3. **Residual Error Threshold:** If $\text{RMS} = \sqrt{\frac{1}{n} \sum \|y_i - (sRx_i + t)\|^2} > \text{threshold}$, return `HIGH_DISCREPANCY_UNVERIFIED`.

---

## 5. WHO 2008 PARAMETRIC CUN-SCALING ENGINE

The engine implements proportional bone-segment division (B-cun) across 11 discrete anatomical segments per WHO 2008 Section 2:

### 5.1. Regional Segment Division Formula
For any segment with start anchor $P_{start}$, end anchor $P_{end}$, standard units $N_{cun}$, and point coordinate $(u, v)$ where $u \in [0, 1]$ is longitudinal fraction and $v$ is lateral cun:
$$P(u, v) = P_{start} + u \cdot (P_{end} - P_{start}) + v \cdot \left(\frac{\|P_{end} - P_{start}\|}{N_{cun}}\right) \cdot \hat{n}_{lateral}$$

### 5.2. Morphology Studio Dynamic Adaptation
When patient anthropometric parameters are provided:
- Stature factor: $\alpha = \frac{\text{Height}_{patient}}{\text{Height}_{baseline}}$
- Shoulder factor: $\beta = \frac{\text{ShoulderWidth}_{patient}}{\text{ShoulderWidth}_{baseline}}$
- Longitudinal segments scale by $\alpha$; transverse thoracic segments scale by $\beta$.
- Finger cun ($F\text{-cun}$) is derived as:
  $$\text{Middle Finger } 1\text{ cun} = \frac{\text{Height}_{patient}}{75}$$
  $$\text{Hand Breadth } 3\text{ cun} = 3 \times (\text{Middle Finger } 1\text{ cun})$$

---

## 6. POSE-AWARE RIGGING & GUARDED SURFACE PROJECTION

### 6.1. Forward Kinematics (Rodrigues Formula)
Points rotating around joint pivots $(P_{pivot}, \hat{a})$ by angle $\theta$:
$$P' = P_{pivot} + (P - P_{pivot})\cos\theta + (\hat{a} \times (P - P_{pivot}))\sin\theta + \hat{a}(\hat{a} \cdot (P - P_{pivot}))(1 - \cos\theta)$$

### 6.2. Posture Calibration Limits & Invalidation
For skin-crease and mobile-tendon points (LU5, BL40, PC6, HT3, ST35, etc.):
$$\text{If } |\Delta\theta_{joint}| > \theta_{threshold} \implies \text{Status} \leftarrow \text{"UNCERTAIN\_POSTURE\_OFFSET"}$$

### 6.3. Guarded Surface Raycasting
A surface projection hit $P_{hit}$ with normal $\hat{n}_{surface}$ and intended outward direction $\hat{d}_{outward}$ is accepted if and only if:
1. **Normal Inclination:** $\hat{n}_{surface} \cdot \hat{d}_{outward} \ge \cos(60^\circ) = 0.50$
2. **Containment:** $P_{hit} \in \text{RegionBoundingBox}(\text{BodyRegion})$
Violations emit `NORMAL_INCLINATION_REJECTED` or `PROJECTION_OUTSIDE_CONTAINMENT`.
