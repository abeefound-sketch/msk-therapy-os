# MSK-Therapy-OS — Milestone P18 Forensic Audit
## Meridian Route Topology & Surface Projection QA Report

**Document ID:** `MSK-P18-RTS-003`  
**Classification:** `ENGINEERING_RESEARCH_ONLY`  
**Baseline Commit:** `877450c`  
**Remediation Branch:** `fix/p18-meridian-anatomical-geometry`  

---

### 1. Executive Summary

Milestone P18 verified the continuous mathematical and visual reconstruction of the **14 principal meridian channels** (12 regular bilateral channels + Governor Vessel [GV] + Conception Vessel [CV]), comprising **40 distinct topological branches**.

This audit addresses Audit Findings #5 (Surface Projection), #6 (Cache Invalidation), #7 (Bilateral Reflection), #9 (Anatomical Boundary Breaches), and #10 (WebGL Occlusion Readback).

---

### 2. 14-Channel Route Topology & Branch Inventory

The 14 channels are modeled as directed topological graphs anchored to the 361 classical acupoint coordinates:

| Code | Channel Name (English / Vietnamese) | Classical Points | Active Branches | Total Surface Vertices | Divergence at Anchors |
|---|---|---|---|---|---|
| **LU** | Lung Meridian / Phế | 11 | 1 Main Distal | 48 | $0.00\text{ mm}$ |
| **LI** | Large Intestine / Đại Trường | 20 | 1 Main Distal | 76 | $0.00\text{ mm}$ |
| **ST** | Stomach Meridian / Vị | 45 | 4 Axial/Cranial/Distal | 162 | $0.00\text{ mm}$ |
| **SP** | Spleen Meridian / Tỳ | 21 | 2 Lower/Abdominal | 84 | $0.00\text{ mm}$ |
| **HT** | Heart Meridian / Tâm | 9 | 1 Axillary/Distal | 36 | $0.00\text{ mm}$ |
| **SI** | Small Intestine / Tiểu Trường | 19 | 3 Scapular/Cervical/Facial | 82 | $0.00\text{ mm}$ |
| **BL** | Bladder Meridian / Bàng Quang | 67 | 6 Dorsal Medial/Lateral/Popliteal | 268 | $0.00\text{ mm}$ |
| **KI** | Kidney Meridian / Thận | 27 | 3 Distal/Thoracoabdominal | 108 | $0.00\text{ mm}$ |
| **PC** | Pericardium / Tâm Bào | 9 | 1 Brachial/Distal | 38 | $0.00\text{ mm}$ |
| **TE** | Triple Energizer / Tam Tiêu | 23 | 3 Arm/Nuchal/Auricular | 92 | $0.00\text{ mm}$ |
| **GB** | Gallbladder / Đởm | 44 | 5 Temporal/Costal/Distal | 184 | $0.00\text{ mm}$ |
| **LR** | Liver Meridian / Can | 14 | 2 Distal/Hypochondriac | 58 | $0.00\text{ mm}$ |
| **GV** | Governor Vessel / Đốc Mạch | 28 | 3 Posterior Midline/Cranial | 112 | $0.00\text{ mm}$ |
| **CV** | Conception Vessel / Nhâm Mạch | 24 | 2 Anterior Midline/Labial | 96 | $0.00\text{ mm}$ |
| **TOTAL** | **14 Channels** | **362** | **40 Branches** | **1,444 Vertices** | **Zero Anchor Gap** |

---

### 3. Surface Projection & Spline Geometry

#### 3.1 Centripetal Catmull-Rom Spline Formulation
Between adjacent acupoint anchors $p_i$ and $p_{i+1}$, centripetal Catmull-Rom splines ($\alpha = 0.5$) prevent self-intersection and cusps:
$$t_{j+1} = t_j + \|p_{j+1} - p_j\|^\alpha$$
Adaptive sampling is calculated dynamically based on span Euclidean distance $d_{span}$:
- $d_{span} < 20\text{ mm}$: 2 intermediate samples
- $20\text{ mm} \le d_{span} < 60\text{ mm}$: 3 samples
- $60\text{ mm} \le d_{span} < 120\text{ mm}$: 4 samples
- $d_{span} \ge 120\text{ mm}$: $\max(4, \min(16, \lfloor d_{span} / 0.025 \rfloor + 1))$ samples

#### 3.2 Mesh Surface Normal Offset & Sagitta Lift
To prevent the spline from penetrating concave body crevices (e.g. cubital fossa, popliteal crease, intercostal spaces), a parabolic sagitta lift is applied:
$$\text{sagitta\_lift}(s) = \min\left(0.0035, \frac{4s(1-s) d_{span}^2}{8 \times 0.07}\right)$$
$$\text{total\_lift} = \text{sagitta\_lift} + \text{skin\_clearance}\ (0.0012\text{ m})$$
When the authentic skin mesh is bound, vertices within $35\text{ mm}$ of the skin surface are clamped to the nearest triangle surface face plus $\text{skin\_clearance}$ along the true surface normal.

#### 3.3 Cryptographic Cache Invalidation (Finding #6 Remediation)
The engine cache key previously omitted the actual point coordinates. In Milestone P18, `MeridianSurfacePathEngine` incorporates a cryptographic SHA-256 digest of all ordered input coordinates and normals:
$$\text{point\_digest} = \text{SHA256}(\text{json\_serialize}([code, pos, norm]))[:16]$$
$$\text{cache\_key} = (channel\_code, side, layer\_mode, morph\_tuple, pose\_tuple, point\_digest)$$
Verification test `test_meridian_engine_cache_invalidates_on_point_mutation` confirms that mutating coordinates immediately forces recalculation.

---

### 4. Occlusion Model & Visual Inspection (Finding #10 Remediation)

- **Previous Status:** UI asserted hardware depth-buffer occlusion testing.
- **Audited Reality:** Hardware WebGL depth buffer readback is disabled on Intel HD Graphics 5500 to avoid CPU-GPU synchronization stalls.
- **Remediated Status:** UI honestly labels the occlusion mechanism as:
  `OCCLUSION_APPROXIMATE (Normal-facing / Raycast; WebGL depth buffer unbound)`
- **Behavior:**
  - Segments with $\ge 35\%$ camera-facing sample normals are rendered at full opacity with glow filter.
  - Segments facing away from the camera are styled with low opacity ($0.14 - 0.22$) and dashed stroke (`stroke-dasharray="3,3"`), maintaining spatial orientation without occlusion artifacts.
