# P9.9 High-Resolution Skeletal Registration Technical Specification

## 1. Executive Summary & Purpose
This document establishes the authoritative technical specification for the high-resolution skeletal registration engine implemented in MSK-Therapy-OS milestone P9.9. The primary objective is to ground distal extremity acupoints (specifically the foot and wrist) on independent 3D skeletal geometry from BodyParts3D 4.0, eliminating circular dependencies, quantifying residual fitting and holdout errors, maintaining bilateral sagittal parity invariants, and upholding strict clinical safety boundaries.

---

## 2. Anatomical Coordinate Frames & Units

### 2.1 Canonical Target Coordinate System (BodyParts3D FJ2810)
- **Origin $(0,0,0)$:** Midpoint of the line connecting bilateral anterior superior iliac spines (ASIS), projected to the sacral promontory coronal plane.
- **Orientation:**
  - $+X$: Patient Anatomic Right (lateral)
  - $-X$: Patient Anatomic Left (lateral)
  - $+Y$: Superior (cranial / vertex)
  - $-Y$: Inferior (caudal / plantar)
  - $+Z$: Anterior (ventral)
  - $-Z$: Posterior (dorsal)
- **Units:** Meters ($m$), with internal computation in millimeters ($mm$) where specified for sub-millimeter precision.

### 2.2 Upstream Source Coordinate System (BodyParts3D 4.0 Discrete Mesh Partitions)
- **Orientation:**
  - $+X$: Patient Anatomic Left
  - $-X$: Patient Anatomic Right
  - $+Y$: Superior
  - $+Z$: Anterior
- **Parity Relation:** Sagittal parity reflection across the $Y\text{-}Z$ midline plane:
  $$\begin{pmatrix} X_{\text{canonical}} \\ Y_{\text{canonical}} \\ Z_{\text{canonical}} \end{pmatrix} = \begin{pmatrix} -1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{pmatrix} \begin{pmatrix} X_{\text{source}} \\ Y_{\text{source}} \\ Z_{\text{source}} \end{pmatrix}$$
- **Scale Invariant:** Uniform scaling $s = 1.000000$ (identity scale preservation between BodyParts3D derived releases).

---

## 3. Mathematical Registration Formalism

### 3.1 Umeyama SVD Closed-Form Orthogonal Procrustes
Given $n$ source skeletal landmark points $\{x_i\}_{i=1}^n$ and corresponding target landmarks $\{y_i\}_{i=1}^n$ where $n \ge 3$:

1. **Centroid Computation:**
   $$\mu_x = \frac{1}{n}\sum_{i=1}^n x_i, \quad \mu_y = \frac{1}{n}\sum_{i=1}^n y_i$$

2. **Demeaned Point Matrices:**
   $$X_c = [x_1 - \mu_x, \dots, x_n - \mu_x]^T, \quad Y_c = [y_1 - \mu_y, \dots, y_n - \mu_y]^T$$

3. **Cross-Covariance Matrix (3x3):**
   $$H = \frac{1}{n} X_c^T Y_c$$

4. **Singular Value Decomposition (Pure-Python Jacobi SVD):**
   $$H = U \Sigma V^T$$

5. **Rotation Matrix with Reflection Control:**
   $$S = \begin{pmatrix} 1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & d \end{pmatrix}, \quad d = \det(V U^T)$$
   $$R = V S U^T$$
   For proper rigid registration without inversion, $d = +1$; for sagittal reflection mapping, $d = -1$ is explicitly handled.

6. **Scale Factor ($s$):**
   $$s = \frac{1}{\sigma_x^2} \operatorname{tr}(\Sigma S) = 1.000000 \quad (\text{rigid enforcement})$$

7. **Translation Vector ($t$):**
   $$t = \mu_y - s R \mu_x$$

### 3.2 Degeneracy & Collinearity Safeguards
The registration engine implements a collinearity test prior to SVD execution:
$$\|\vec{v}_1 \times \vec{v}_2\| > \epsilon = 10^{-4}$$
If the anchor landmarks are collinear or $n < 3$, the engine strictly aborts with status `DEGENERATE_COLLINEAR_LANDMARKS` or `UNREGISTERED`, failing closed without guessing an unconstrained rotation axis.

---

## 4. Independent Holdout Verification Architecture
To eliminate self-fitting circularity, every registered subsystem (foot and wrist) partitions landmarks into two disjoint sets:

1. **Fitting Anchors:** Used to solve the SVD transformation matrix.
2. **Holdout Validation Anchors:** Unseen during fitting, used exclusively to evaluate out-of-sample generalization error:
   $$\text{RMS}_{\text{holdout}} = \sqrt{\frac{1}{m}\sum_{j=1}^m \| (s R x_j^{\text{holdout}} + t) - y_j^{\text{target}} \|^2}$$

### Threshold Gates:
- `PASS`: $\text{RMS}_{\text{fitting}} \le 1.0\text{ mm}$ and $\text{RMS}_{\text{holdout}} \le 5.0\text{ mm}$
- `REJECTED`: Exceeds tolerance or exhibits out-of-bounds bounding box violation.

---

## 5. Subsystem Architecture

### 5.1 Distal Foot Subsystem
- **Bones:** First Metatarsal (`FJ3351`/`FJ3241`), Navicular (`FJ3308`/`FJ3307`), Medial Cuneiform (`FJ3377`/`FJ3271`), Calcaneus (`FJ3360`/`FJ3256`), Distal Tibia (`FJ3387`/`FJ3282`).
- **Fitting Landmarks:** `LM_MTP1_DISTAL_R`, `LM_MTP1_PROXIMAL_R`, `LM_METATARSAL1_BASE_R`, `LM_NAVICULAR_TUBEROSITY_R`.
- **Holdout Landmarks:** `LM_MED_MALLEOLUS_R`, `LM_CALCANEUS_POST_R`, `LM_CALCANEUS_MEDIAL_TUBEROSITY_R`.
- **Fitting RMS:** $0.015\text{ mm}$
- **Holdout RMS:** $0.057\text{ mm}$

### 5.2 Distal Wrist Subsystem
- **Bones:** Distal Radius (`FJ3349`/`FJ3277`), Distal Ulna (`FJ3391`/`FJ3286`), Scaphoid (`FJ3383`/`FJ3278`), Pisiform (`FJ3382`/`FJ3276`).
- **Fitting Landmarks:** `LM_RADIAL_STYLOID_PROCESS_R`, `LM_ULNAR_STYLOID_PROCESS_R`, `LM_SCAPHOID_TUBERCLE_R`, `LM_PISIFORM_PROMINENCE_R`.
- **Holdout Landmarks:** `LM_WRIST_PALMAR_CREASE_RADIAL_R`, `LM_WRIST_PALMAR_CREASE_ULNAR_R`, `LM_WRIST_PALMAR_CREASE_MIDPOINT_R`.
- **Fitting RMS:** $0.089\text{ mm}$
- **Holdout RMS:** $0.070\text{ mm}$

---

## 6. Implementation Reference
- Module: `msk_therapy_os/anatomical_registration.py`
- Classes: `HighResolutionSkeletalRegistrar`, `SkeletalRegistrationReport`, `AnatomicalRegistrationEngine`
- Manifest: `2data/evidence/p9_9_registration/p9_9_skeletal_registration_manifest.json`
