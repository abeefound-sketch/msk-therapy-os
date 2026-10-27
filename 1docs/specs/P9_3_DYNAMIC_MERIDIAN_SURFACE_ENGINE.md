# P9.3 TECHNICAL SPECIFICATION: DYNAMIC ANATOMICAL MERIDIAN SURFACE ENGINE

**Status:** APPROVED FOR IMPLEMENTATION  
**Version:** 1.0.0  
**Target Architecture:** MSK-Therapy-OS Spatial Geometry Resolution Pipeline  
**Mesh Ground Truth:** BodyParts3D FJ2810 (`05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`)  
**Zero-Dependency Constraint:** Standard Library Python 3.11 + WebGL 1.0/2.0 / SVG  

---

## 1. PURPOSE & ARCHITECTURAL OVERVIEW

The `MeridianSurfacePathEngine` is responsible for generating continuous, surface-conforming 3D geometric polylines for the 14 traditional channels (12 bilateral paired meridians + 2 midline channels).

Unlike static pre-baked vertex arrays, the dynamic engine:
1. Takes the **dynamically resolved control points** from `AnatomicalSpatialResolver` (`resolved_points`).
2. Generates smooth, continuous interpolating curves (Centripetal Catmull-Rom splines, $\alpha = 0.5$) connecting consecutive acupoint anchors.
3. Guards against subcutaneous mesh penetration and mid-air floating by projecting interpolated vertices onto the local anatomical surface envelope.
4. Associates each vertex with an outward-pointing unit normal vector $\vec{N}$ derived from the surface geometry and anchor normals.
5. Decomposes each channel into discrete, anatomically bounded segments (`segments`), enabling segment-level depth sorting, occlusion styling, and independent limb kinematic transformations.

```
       +-------------------------------------------------------+
       |   AnatomicalSpatialResolver.resolve_atlas_geometry()   |
       +-------------------------------------------------------+
                                   |
         Resolves Acupoint Anchors (WHO 2008 + FJ2810 FMA)
                                   v
       +-------------------------------------------------------+
       |              Resolved Control Points (P0..Pn)         |
       |  (Positions, Normals, Skeletal Hierarchy, Joint State)|
       +-------------------------------------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |              MeridianSurfacePathEngine                |
       |                                                       |
       |  1. Channel Sequence Topology & Landmark Anchors      |
       |  2. Centripetal Catmull-Rom Spline Interpolation      |
       |  3. Regional Skeletal Segment Binding                 |
       |  4. Guarded Surface Raycast / Envelope Projection     |
       |  5. Per-Vertex Outward Normal Generation              |
       |  6. Bilateral Symmetry with Parity Correction         |
       +-------------------------------------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |   Streaming Segment Geometry (JSON / GeoJSON-like)    |
       |  - Ordered Segments (e.g. hand, forearm, torso)       |
       |  - Vertices [x, y, z]                                 |
       |  - Normals [nx, ny, nz]                               |
       |  - Anchor Attachments & Residual Distances            |
       +-------------------------------------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |            Atlas WebGL / SVG Render Pipeline          |
       |  - Segment-Level Depth & Camera-Facing Classification |
       |  - Non-Disappearing Smooth Silhouette Fallback       |
       |  - Interactive Acupoint-to-Path Inspection            |
       +-------------------------------------------------------+
```

---

## 2. MATHEMATICAL FORMULATION

### 2.1. Centripetal Catmull-Rom Spline Interpolation
Standard cubic Bézier or uniform Catmull-Rom splines often suffer from cusp formation, self-intersection, and overshoot when the distance between control points varies significantly (e.g., small distance between `LI1` and `LI2` on the index finger vs. large distance between `LI10` and `LI11` on the forearm).

To eliminate loop formation and cusps, we use **Centripetal Catmull-Rom Splines** with parameter $\alpha = 0.5$.

Given four consecutive points $P_0, P_1, P_2, P_3 \in \mathbb{R}^3$:

$$t_0 = 0$$
$$t_{i+1} = t_i + \| P_{i+1} - P_i \|_2^\alpha, \quad \text{where } \alpha = 0.5$$

For $t \in [t_1, t_2]$, the intermediate points are computed via recursive linear interpolation:

$$A_1 = \frac{t_1 - t}{t_1 - t_0} P_0 + \frac{t - t_0}{t_1 - t_0} P_1$$
$$A_2 = \frac{t_2 - t}{t_2 - t_1} P_1 + \frac{t - t_1}{t_2 - t_1} P_2$$
$$A_3 = \frac{t_3 - t}{t_3 - t_2} P_2 + \frac{t - t_2}{t_3 - t_2} P_3$$
$$B_1 = \frac{t_2 - t}{t_2 - t_0} A_1 + \frac{t - t_0}{t_2 - t_0} A_2$$
$$B_2 = \frac{t_3 - t}{t_3 - t_1} A_2 + \frac{t - t_1}{t_3 - t_1} A_3$$
$$C(t) = \frac{t_2 - t}{t_2 - t_1} B_1 + \frac{t - t_1}{t_2 - t_1} B_2$$

This guarantees:
1. $C(t_1) = P_1$ and $C(t_2) = P_2$ (the curve strictly passes through the resolved acupoints).
2. $C^1$ continuity at all internal knots.
3. No self-intersections or extreme overshoots across varying acupoint densities.

### 2.2. Guarded Surface Envelope Projection
Because limbs and torso surfaces are curved (ellipsoidal/convex cross-sections), a chord or spline between two surface points $P_1$ and $P_2$ dips beneath the skin mesh if left uncorrected:

$$d_{\text{chord}}(s) = P_{\text{interpolated}}(s) - P_{\text{surface}}$$

To prevent subcutaneous penetration:
1. Let $\vec{N}_1, \vec{N}_2$ be the unit surface normals at $P_1, P_2$.
2. The interpolated normal along the segment is:
   $$\vec{N}(s) = \text{normalize}\big((1-s)\vec{N}_1 + s\vec{N}_2\big)$$
3. Compute the sagittal/coronal radial envelope radius $R(y)$ at height $y$:
   $$\Delta_{\text{radial}} = \max\Big(0, R_{\text{mesh}}(y) - \| P_{\text{interpolated}}(s)_{xz} \|\Big)$$
4. The surface-projected vertex position is adjusted radially or along $\vec{N}(s)$:
   $$P^*(s) = P_{\text{interpolated}}(s) + \delta_{\text{skin}} \cdot \vec{N}(s)$$
   where $\delta_{\text{skin}} = 0.0015\text{ m}$ ($1.5\text{ mm}$) to guarantee clean WebGL depth-buffer rendering without Z-fighting against the mannequin skin mesh.

### 2.3. Anatomical Regional Decomposition & Skeletal Hierarchy
Channels are partitioned into discrete anatomical regions:

| Region Key | Included Skeletal Structures | Sensitive Joint Kinematics |
| :--- | :--- | :--- |
| `head_neck` | Cranium, Mandible, Cervical Spine (C1-C7) | Cervical flexion, extension, rotation |
| `torso_anterior` | Clavicle, Sternum, Ribcage, Abdominal wall | Thoracic posture, breathing expansion |
| `torso_posterior` | Scapula, Thoracic/Lumbar Spine, Sacrum | Thoracic flexion, extension |
| `shoulder_girdle` | Acromion, Clavicle lateral, Axillary fold | Shoulder abduction/adduction, flexion |
| `upper_arm` | Humerus, Biceps/Triceps brachii | Shoulder rotation, abduction |
| `forearm` | Radius, Ulna, Interosseous membrane | Elbow flexion, forearm pronation/supination |
| `hand` | Carpal, Metacarpal, Phalanges | Wrist flexion/radial deviation |
| `pelvis` | Iliac crest, Pubis, Greater trochanter | Pelvic tilt |
| `thigh` | Femur, Quadriceps, Hamstrings | Hip flexion, abduction |
| `shank` | Tibia, Fibula, Gastrocnemius, Popliteal | Knee flexion/extension |
| `foot` | Tarsal, Metatarsal, Calcaneus, Toes | Ankle dorsi/plantarflexion |

Each segment inherits kinematic rotation matrices from its proximal and distal joints, ensuring that when an elbow or knee flexes, the path segments deform synchronously with the bones and skin.

---

## 3. DATA MODEL & SCHEMA

### 3.1. Segment Geometry Object
```json
{
  "segment_id": "LU_seg_02_forearm",
  "start_point": "LU5",
  "end_point": "LU9",
  "region": "forearm",
  "side": "right",
  "vertices": [
    [0.285, 1.054, 0.021],
    [0.291, 1.012, 0.023],
    ...
  ],
  "normals": [
    [0.58, 0.35, 0.735],
    [0.59, 0.33, 0.741],
    ...
  ],
  "arc_length_mm": 218.4,
  "point_anchor_count": 5
}
```

### 3.2. Channel Resolution Output
```json
{
  "code": "LU",
  "name_zh": "手太阴肺经",
  "name_en": "Lung Meridian",
  "color": "#38bdf8",
  "element": "Metal",
  "yin_yang": "Hand Taiyin",
  "points": ["LU1", "LU2", "LU3", "LU4", "LU5", "LU6", "LU7", "LU8", "LU9", "LU10", "LU11"],
  "paths": [
    {
      "side": "right",
      "point_count": 142,
      "surface_vertices": [[...], [...]],
      "surface_normals": [[...], [...]],
      "segments": [ ... ],
      "point_residual_max_mm": 0.0,
      "point_residual_mean_mm": 0.0,
      "disclaimer": "Educational visualization approximation dynamically constrained to skin surface"
    },
    {
      "side": "left",
      "point_count": 142,
      "surface_vertices": [[...], [...]],
      "surface_normals": [[...], [...]],
      "segments": [ ... ],
      "point_residual_max_mm": 0.0,
      "point_residual_mean_mm": 0.0,
      "disclaimer": "Educational visualization approximation dynamically constrained to skin surface"
    }
  ]
}
```

---

## 4. OCCLUSION & RENDERING SPECIFICATION

### 4.1. Camera-Facing Dot Product
For each polyline vertex $V_i$ with outward normal $N_i$ and camera eye $E$:

$$\vec{U}_{\text{view}} = \text{normalize}(E - V_i)$$
$$\text{facing}_i = (N_i \cdot \vec{U}_{\text{view}}) \ge -0.05$$

### 4.2. Segment-Based Rendering
Instead of dropping the entire meridian when some vertices face away:
- Vertices where $\text{facing}_i = \text{true}$ are grouped into front-facing sub-paths: rendered with full channel color, standard stroke-width, and subtle glow.
- Vertices where $\text{facing}_i = \text{false}$ are grouped into back-facing sub-paths:
  - If X-Ray mode is enabled: rendered with dashed pattern or 20% opacity.
  - If standard anatomical mode: rendered with subtle attenuated opacity ($0.12$) or culled cleanly without breaking neighboring front-facing segments.
- Polyline connections across the silhouette limb boundary are split cleanly at tangent transitions, preventing long false lines cutting through 3D meshes.

---

## 5. PERFORMANCE BUDGET
- Re-generation of all 14 channels (26 bilateral/midline paths): **$\le 15\text{ ms}$** on Python 3.11 backend.
- Client-side WebGL/SVG projection and render cycle: **$\le 8\text{ ms}$** ($> 60\text{ fps}$ interactive orbit).
- Zero memory leakage during continuous camera orbit.

---

*End of Technical Specification.*
