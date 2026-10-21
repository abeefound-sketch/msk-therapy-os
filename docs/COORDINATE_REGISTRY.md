# Coordinate Registry & Anatomical Landmark Specification

**Project:** MSK-Therapy-OS  
**Branch:** `research/anatomical-workbench`  
**Status:** CANONICAL SPECIFICATION  
**Author:** Staff/Principal Engineer & 3D Visualization Specialist  
**Date:** 2026-10-21  

---

## 1. Canonical Coordinate Standard

To eliminate floating points, displaced pathways, and incompatible transforms across disparate datasets, MSK-Therapy-OS defines the **Canonical Anatomical Coordinate Frame** based on the standardized BodyParts3D reference model:

* **Units:** Exact SI Meters ($1.0 = 1\text{m}$).
* **Axes & Handedness:** Right-handed Cartesian space:
  * $+X$: Right lateral direction (patient's anatomical right).
  * $+Y$: Superior direction (cranial / upwards).
  * $+Z$: Anterior direction (ventral / facing front).
* **Origin ($[0, 0, 0]$):**
  * $X = 0.0\text{m}$: Midsagittal symmetry plane.
  * $Y = 0.0\text{m}$: Ground contact plane directly beneath the plantar surface of the calcaneus (heels).
  * $Z = 0.0\text{m}$: Coronal mid-plane intersecting the external auditory meatus and center of gravity.
* **Vertical Reference Datums:**
  * Plantar Surface (Heel/Sole): $Y \approx 0.000\text{m}$
  * Center of Mass / DanTian / Pelvis: $Y \approx 0.860\text{m}$
  * Vertebra Prominens (C7 / Dazhui / GV14): $Y \approx 1.478\text{m}$
  * Acromioclavicular Joint / Shoulder: $Y \approx 1.440\text{m}$
  * Suboccipital Depression: $Y \approx 1.582\text{m}$
  * Vertex / Crown (Baihui / GV20): $Y \approx 1.718\text{m}$

```
       +Y (Superior / Cranium, Y ≈ 1.72m)
          ▲
          │       [GV20 / Baihui]
          │             ●
          │       [GB20 / Fengchi]
          │       [GV14 / Dazhui]
          │
          │   [GB21 / Jianjing]
          │        ●───────● [Acromion]
          │
          │   [DanTian / Pelvis, Y ≈ 0.86m]
          │
          │
          │
          │   [Sole / Ground, Y = 0.00m]
──────────┴──────────────────────────────► +X (Patient Right)
         /
        ▼ +Z (Anterior / Front)
```

---

## 2. Upstream Coordinate Mapping & Transformations

Each upstream project uses a divergent origin and scale convention. The table below details the exact affine transformations required to map raw upstream data into the Canonical Frame:

| Source Dataset | Upstream Origin | Upstream Scale | Affine Transformation Matrix to Canonical |
| :--- | :--- | :--- | :--- |
| **`JICio/tcm-3d`** | Floor ($Y=0$) | Meters ($1:1$) | $\mathbf{P}_{\text{canonical}} = \mathbf{P}_{\text{JICio}}$ (Identity) |
| **`WaterCMY/anatomy-3d`** | Floor ($Y=0$) | Meters ($1:1$) | $\mathbf{P}_{\text{canonical}} = \mathbf{P}_{\text{CMY}}$ (Identity) |
| **`spacejohnlf/tcm-acupoints`** | Pelvis ($Y=0$) | Meters ($1:1$, Sole=$-0.86$, Crown=$+0.86$) | $\begin{bmatrix} X_c \\ Y_c \\ Z_c \\ 1 \end{bmatrix} = \begin{bmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0.86 \\ 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} X_t \\ Y_t \\ Z_t \\ 1 \end{bmatrix}$ |
| **`Meridian Studio`** | Bounding Box Center | Normalized / Centered | $\mathbf{P}_{\text{canonical}} = \mathbf{S} \cdot \mathbf{P}_{\text{studio}} + \mathbf{T}_{\text{mesh\_center}}$ |

---

## 3. Ground Truth Anatomical Landmarks: Neck-Shoulder Scenario

The Neck–Shoulder–Upper-Back clinical scenario serves as the primary benchmark. Ground-truth coordinates are derived from palpable osteological and myological landmarks on the canonical BodyParts3D adult male reference geometry:

| Acupoint Code | Traditional Chinese Name | Canonical Coordinates $[X, Y, Z]$ (m) | Primary Skeletal / Myological Anchor | Anatomical Description & WHO Standard |
| :--- | :--- | :--- | :--- | :--- |
| **`GV14`** | 大椎 (Dazhui) | `[0.000, 1.478, -0.092]` | C7 Vertebra Prominens | Posterior midline, in the depression below the spinous process of the 7th cervical vertebra. |
| **`GB21`** | 肩井 (Jianjing) | `[0.142, 1.436, -0.012]` | Superior border of m. trapezius | Midpoint of the line connecting the spinous process of C7 (`GV14`) and the lateral acromion extremity. |
| **`GB20`** | 风池 (Fengchi) | `[0.068, 1.582, -0.076]` | Suboccipital depression | Depression between the upper portion of m. sternocleidomastoideus and m. trapezius, below occiput. |
| **`BL10`** | 天柱 (Tianzhu) | `[0.038, 1.572, -0.084]` | Lateral margin of m. trapezius | In the depression on the lateral border of m. trapezius, 1.3 cun lateral to the posterior midline at C2. |
| **`SI15`** | 肩中俞 (Jianzhongshu) | `[0.075, 1.455, -0.095]` | Medial border of scapula at C7 | On the back, 2 cun lateral to the lower border of the spinous process of C7. |
| **`TE15`** | 天髎 (Tianliao) | `[0.128, 1.442, -0.045]` | Supraspinous fossa, scapular angle | Midway between `GB21` and `SI13`, on the superior angle of the scapula. |

---

## 4. Distance Metric & Discrepancy Classification

To quantitatively evaluate agreement and boundary adherence, the workbench computes the 3D Euclidean distance $D_{\text{mm}}$ in millimeters:

$$D_{\text{mm}}(\mathbf{P}_1, \mathbf{P}_2) = 1000.0 \times \sqrt{(X_1 - X_2)^2 + (Y_1 - Y_2)^2 + (Z_1 - Z_2)^2}$$

Classification criteria:
* **`CONVERGENT` ($D \le 15.0\text{mm}$):** High confidence alignment across independent datasets. Suitable for automated display.
* **`DEVIATING` ($15.0\text{mm} < D \le 35.0\text{mm}$):** Moderate discrepancy caused by minor postural variation (e.g. cervical lordosis angle or scapular abduction). Requires visual confirmation.
* **`DISCREPANT` ($D > 35.0\text{mm}$):** Significant anatomical conflict or misregistered coordinate seed. Must be flagged as `UNVERIFIED` in user-facing UI until manually reviewed.
