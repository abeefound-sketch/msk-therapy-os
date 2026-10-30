# P14-A: ARCHITECTURE & TECHNICAL SOURCE AUDIT
## Musculoskeletal Therapy OS (MSK-Therapy-OS) — Milestone P14
### Deep Inspection of `anatomy.glb` · Osseous Asset Discovery · Kinematic Transform Strategy

- **Milestone:** P14 (Phase P14-A: Technical Source Audit)
- **Document ID:** `1docs/audits/P14/P14_ARCHITECTURE_AND_SOURCE_AUDIT.md`
- **Audit Date:** 2026-10-30
- **Auditor:** Principal Research Software Architect & 3D Visualization Engineer
- **Status:** COMPLETED & ACTIONABLE

---

## 1. FORENSIC AUDIT OF EXISTING 3D ASSET (`models/anatomy.glb`)

A binary inspection of [`msk_therapy_os/static/education/models/anatomy.glb`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/static/education/models/anatomy.glb) (9,291,204 bytes) yields:

```text
GLTF Version:    2.0
Nodes Count:     256
Meshes Count:    255
Skins Count:     0  <-- NO SKINNED SKELETON
Animations:      0  <-- NO EMBEDDED ANIMATION TRACKS
Unique Names:    54 named muscle groups
```

### 1.1 Structural Composition:
1. **Muscle-Only Geometry:** All 255 primitives represent volumetric muscular tissue. There are **zero osseous (bone) meshes** present in `anatomy.glb`.
2. **Stable Identifiers:** The 54 unique groups follow standard hyphenated shortcodes:
   - Anterior girdle: `pec-major`, `pec-minor`, `delt-a`
   - Lateral girdle: `delt-l`
   - Posterior girdle: `delt-p`, `trap-u`, `trap-m`, `trap-l`, `serratus`, `rhomboid`, `lat`
   - Rotator cuff: `subscap`, `supra`, `infra`, `teres-maj`, `teres-min`
3. **Coordinates & Scale:**
   - Raw positions are encoded in millimeters, Z-up orientation (`x: [-203, +203]`, `y: [-219, +5]`, `z: [1078, 1506]`).
   - The Three.js loader rotates the scene by $-\pi/2$ around X and applies a scaling factor ($s \approx 0.0010774$) to normalize the thorax to a Y-up height of $1.78\text{ m}$.

---

## 2. DISCOVERY OF REUSABLE BODYPARTS3D OSSEOUS GEOMETRY

To fulfill Phase P14-E (*"Observe actual motion of separate skeletal segments: Thorax, Clavicle, Scapula, Humerus"*), an inspection of the upstream dataset in [`3refs/upstream/tcm-3d/public/models/`](file:///D:/5Projects/msk-therapy-os/3refs/upstream/tcm-3d/public/models/) revealed the missing authentic BodyParts3D bones:

| Anatomical Segment | BodyParts3D ID | FMA Concept | Chunk File | Vertex Count | Triangle Count | Bounding Box in Meters (Y-up) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Manubrium** | `FJ3290` | FMA7486 | `body-12.bin` | 1,094 | 1,892 | $x: [-0.027, 0.027], y: [1.358, 1.403], z: [0.031, 0.079]$ |
| **Body of Sternum** | `FJ3178` | FMA7487 | `body-12.bin` | 2,511 | 2,810 | $x: [-0.023, 0.024], y: [1.258, 1.368], z: [0.065, 0.114]$ |
| **Right Ribs 1–5** | `FJ3334..FJ3342` | FMA7514.. | `body-13.bin` | 1,842 | 2,410 | Thoracic ribcage cage surface for scapular gliding |
| **Right Clavicle** | `FJ3362` | FMA13322 | `body-13.bin` | 420 | 820 | $x: [-0.145, -0.010], y: [1.387, 1.434], z: [-0.045, 0.047]$ |
| **Right Scapula** | `FJ3384` | FMA13395 | `body-13.bin` | 2,896 | 5,756 | $x: [-0.166, -0.057], y: [1.262, 1.428], z: [-0.105, 0.003]$ |
| **Right Humerus** | `FJ3368` | FMA23130 | `body-13.bin` | 794 | 1,070 | $x: [-0.241, -0.140], y: [1.108, 1.415], z: [-0.049, 0.000]$ |

> [!IMPORTANT]
> The osseous segments are already aligned with the BodyParts3D spatial coordinate space in meters and can be assembled into a lightweight, standard glTF 2.0 binary container ([`shoulder_skeleton.glb`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/static/education/models/shoulder_skeleton.glb), $< 450\text{ KB}$) with zero Draco dependencies.

---

## 3. KINEMATICS & SKELETAL TRANSFORM HIERARCHY

Skeletal motion does not require continuous polygon vertex skinning. Bony segments (Thorax, Clavicle, Scapula, Humerus) behave as rigid bodies articulating at synovial joints:

```mermaid
graph TD
    Thorax["Thorax (Sternum & Ribs)<br/>Fixed Reference Frame"] -->|Sternoclavicular Joint (SC Pivot)| Clavicle["Clavicle<br/>Elevation / Depression / Retraction"]
    Clavicle -->|Acromioclavicular Joint (AC Pivot)| Scapula["Scapula<br/>Upward Rotation / Tilt / Internal Rotation"]
    Scapula -->|Glenohumeral Joint (GH Center)| Humerus["Humerus<br/>Elevation / Plane / Internal-External Rotation"]
```

### Joint Pivot Locations:
1. **Sternoclavicular (SC) Joint Pivot:** $P_{\text{SC}} \approx (-0.020, 1.395, 0.040)\text{ m}$ (Medial clavicular facet meeting the manubrium).
2. **Acromioclavicular (AC) Joint Pivot:** $P_{\text{AC}} \approx (-0.142, 1.422, -0.025)\text{ m}$ (Lateral clavicle articulating with the acromion).
3. **Glenohumeral (GH) Joint Center:** $P_{\text{GH}} \approx (-0.160, 1.395, -0.022)\text{ m}$ (Center of humeral head sphere articulating in the glenoid cavity).

---

## 4. DEFECTS IN EXISTING P13 IMPLEMENTATION IDENTIFIED FOR REMEDIATION

1. **Static Posture Illusion:** P13 only shifted a slider and highlighted muscles. It did not transform any mesh in 3D space. P14 must apply genuine Euler/Quaternion matrix transforms to skeletal segments.
2. **Dogmatic 2:1 Rhythm Assertion:** P13 hardcoded an invariant 2:1 rhythm ratio, falsely labeling deviations as "dyskinesia".
3. **Unsupported Clinical Causal Claims:** P13 claimed that rounded shoulders *necessarily* indicate pec minor shortening or lower trapezius inhibition, and that massage resets mechanoreceptors.
4. **Missing Quiz and Verification:** P13 lacked an interactive comprehension checkpoint.

---

## 5. AUDIT VERDICT

The technical feasibility of extracting and rendering the genuine BodyParts3D shoulder skeletal segments is confirmed. The rigid-body kinematic hierarchy is mathematically sound and ready for implementation.
