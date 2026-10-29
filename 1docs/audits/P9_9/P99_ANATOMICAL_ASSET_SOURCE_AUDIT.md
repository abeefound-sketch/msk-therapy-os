# P9.9 High-Resolution Anatomical Asset Source Audit

**Document ID:** `P99_ANATOMICAL_ASSET_SOURCE_AUDIT.md`  
**Milestone:** P9.9 High-Resolution Foot & Wrist Skeletal Registration  
**Status:** APPROVED | ASSET SUFFICIENCY & PROVENANCE VERIFIED  
**Date:** 2026-10-28  
**Author:** Principal Computational Anatomy Engineer & Medical 3D Registration Specialist  

---

## 1. Executive Summary & Objective

The objective of Phase A is to forensically audit whether the current **BodyParts3D 4.0** anatomical model provides sufficient geometrical resolution and discrete bone segmentations to support independent, non-circular landmark registration for the human foot, ankle, and wrist.

Prior to P9.9, an assumption was recorded in P9.8 that the canonical model `FJ2810` lacked discrete volume segmentations for individual tarsal, metatarsal, and carpal bones. This audit investigated the complete underlying BodyParts3D 4.0 dataset integrated within `3refs/upstream/tcm-3d/public/models/` and established that:

1. **Discrete Skeletal Meshes are Present:** The dataset contains **2,234 segmented anatomical parts**, including individual 3D polygonal meshes for every tarsal bone, metatarsal bone, phalangeal bone, carpal bone, and distal radius/ulna.
2. **Canonical Coordinate Alignment:** All discrete bone meshes share the exact same reference coordinate system and scale (SI meters, Y-Up ground plane) as the canonical skin boundary mesh `FJ2810`.
3. **Open Access & CC BY 4.0 Licensing:** All segmented assets derive directly from BodyParts3D 4.0 (The Database Center for Life Science, University of Tokyo / ROIS) under Creative Commons Attribution 4.0 International (CC BY 4.0), permitting open redistribution and derived engineering assets.

---

## 2. Anatomical Structure Inventory

### 2.1. Foot & Ankle Skeletal Structures Audited

The table below catalogs the authoritative BodyParts3D segmented meshes for the right and left foot:

| Anatomical Structure | FMA Identifier | BodyParts3D Part ID (Right) | BodyParts3D Part ID (Left) | Vertex Count (R / L) | Triangle Count (R / L) | 3D Bounding Box in Meters (Right Side, Reflected Frame) |
|---|---|---|---|---:|---:|---|
| **First Metatarsal Bone** | `FMA:24507` / `FMA:24508` | `FJ3351` | `FJ3241` | 492 / 493 | 908 / 910 | $X \in [0.0748, 0.1044], Y \in [0.0128, 0.0560], Z \in [0.0299, 0.0922]$ |
| **Navicular Bone of Foot** | `FMA:24500` / `FMA:24501` | `FJ3308` | `FJ3307` | 404 / 396 | 760 / 748 | $X \in [0.0582, 0.0968], Y \in [0.0473, 0.0720], Z \in [-0.0057, 0.0210]$ |
| **Medial Cuneiform Bone** | `FMA:24521` / `FMA:24522` | `FJ3377` | `FJ3271` | 553 / 513 | 1046 / 972 | $X \in [0.0660, 0.0941], Y \in [0.0328, 0.0639], Z \in [0.0120, 0.0405]$ |
| **Talus** | `FMA:24482` / `FMA:24483` | `FJ3385` | `FJ3280` | 709 / 666 | 1344 / 1264 | $X \in [0.0496, 0.0901], Y \in [0.0470, 0.0812], Z \in [-0.0512, 0.0056]$ |
| **Calcaneus** | `FMA:24497` / `FMA:24498` | `FJ3360` | `FJ3256` | 641 / 632 | 1204 / 1188 | $X \in [0.0449, 0.1008], Y \in [0.0096, 0.0590], Z \in [-0.0760, -0.0059]$ |
| **Tibia (Medial Malleolus)** | `FMA:24477` / `FMA:24478` | `FJ3387` | `FJ3282` | 334 / 331 | 632 / 628 | $X \in [0.0352, 0.1094], Y \in [0.0721, 0.4520], Z \in [-0.0479, 0.0148]$ |
| **Fibula (Lateral Malleolus)**| `FMA:24480` / `FMA:24481` | `FJ3366` | `FJ3260` | 162 / 149 | 304 / 280 | $X \in [0.0843, 0.1202], Y \in [0.0528, 0.4373], Z \in [-0.0515, -0.0218]$ |
| **Proximal Phalanx Hallux** | `FMA:43253` / `FMA:43254` | `FJ3310` | `FJ3329` | 272 / 310 | 508 / 580 | $X \in [0.0867, 0.1172], Y \in [0.0095, 0.0267], Z \in [0.0861, 0.1193]$ |
| **Distal Phalanx Hallux** | `FMA:32650` / `FMA:32651` | `FJ3192` | `FJ3182` | 271 / 249 | 506 / 468 | $X \in [0.1024, 0.1251], Y \in [0.0082, 0.0191], Z \in [0.1108, 0.1360]$ |

### 2.2. Wrist & Hand Skeletal Structures Audited

The table below catalogs the authoritative BodyParts3D segmented meshes for the right and left wrist and hand:

| Anatomical Structure | FMA Identifier | BodyParts3D Part ID (Right) | BodyParts3D Part ID (Left) | Vertex Count (R / L) | Triangle Count (R / L) | 3D Bounding Box in Meters (Right Side, Reflected Frame) |
|---|---|---|---|---:|---:|---|
| **Radius (Radial Styloid)** | `FMA:23464` / `FMA:23465` | `FJ3349` | `FJ3277` | 249 / 250 | 466 / 468 | $X \in [0.2198, 0.2795], Y \in [0.8839, 1.1132], Z \in [-0.0389, 0.0269]$ |
| **Ulna (Ulnar Styloid)** | `FMA:23467` / `FMA:23468` | `FJ3391` | `FJ3286` | 305 / 283 | 578 / 534 | $X \in [0.1969, 0.2472], Y \in [0.8833, 1.1306], Z \in [-0.0552, 0.0235]$ |
| **Scaphoid Bone** | `FMA:24435` / `FMA:24436` | `FJ3383` | `FJ3278` | 185 / 172 | 342 / 320 | $X \in [0.2493, 0.2731], Y \in [0.8745, 0.8899], Z \in [0.0116, 0.0267]$ |
| **Pisiform Bone** | `FMA:24441` / `FMA:24442` | `FJ3382` | `FJ3276` | 110 / 116 | 204 / 216 | $X \in [0.2320, 0.2402], Y \in [0.8678, 0.8794], Z \in [0.0272, 0.0377]$ |
| **Triquetral Bone** | `FMA:24439` / `FMA:24440` | `FJ3390` | `FJ3285` | 158 / 152 | 292 / 280 | $X \in [0.2315, 0.2482], Y \in [0.8710, 0.8850], Z \in [0.0180, 0.0320]$ |
| **First Metacarpal Bone** | `FMA:24464` / `FMA:24465` | `FJ3350` | `FJ3240` | 287 / 287 | 536 / 536 | $X \in [0.2722, 0.3096], Y \in [0.8384, 0.8753], Z \in [0.0236, 0.0539]$ |
| **Second Metacarpal Bone** | `FMA:24466` / `FMA:24467` | `FJ3352` | `FJ3242` | 347 / 347 | 648 / 648 | $X \in [0.2618, 0.2927], Y \in [0.7970, 0.8650], Z \in [0.0171, 0.0428]$ |

---

## 3. Coordinate Frame, Scale, and Orientation Parity

### 3.1. Upstream vs Canonical Transformation
In the raw BodyParts3D upstream model (donor standard Japanese male, 172 cm):
- **Measurement Units:** SI Meters ($\text{m}$).
- **Vertical Axis:** $+Y$ Superior (Ground plane at $Y = 0.00\text{ m}$, crown vertex at $Y \approx 1.72\text{ m}$).
- **Coronal Axis:** $+Z$ Anterior / Frontal, $-Z$ Posterior / Dorsal.
- **Sagittal Parity:** In raw BodyParts3D files (`atlas.json`), the patient's anatomical **Right is negative $X$** (e.g., $X \in [-0.104, -0.075]$ for right 1st metatarsal), and anatomical **Left is positive $X$**.

In the MSK-Therapy-OS canonical coordinate frame (`landmark_registry.py`, `CANONICAL_LANDMARKS`):
- Anatomical **Right is $+X$** (e.g., `LM_MED_MALLEOLUS_R` at $+0.076\text{ m}$).
- Anatomical **Left is $-X$** (e.g., `LM_MASTOID_L` at $-0.062\text{ m}$).

### 3.2. Authoritative Transformation Mapping
The exact affine transformation from BodyParts3D source coordinates $(x_s, y_s, z_s)$ to MSK-Therapy-OS canonical frame $(x_c, y_c, z_c)$ is an exact reflection across the sagittal midline plane:

$$\begin{bmatrix} x_c \\ y_c \\ z_c \end{bmatrix} = \begin{bmatrix} -1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} x_s \\ y_s \\ z_s \end{bmatrix}$$

No scale factor is applied ($s = 1.000000$), preserving exact physical millimeter dimensions.

---

## 4. Separation of Bone Geometry from Soft-Tissue / Tendon References

Clinical acupuncture point definitions (WHO Standard Acupuncture Point Locations, 2008) distinguish between:
1. **Pure Bony Prominences:** Anchored directly to rigid osseous features (e.g., tip of medial malleolus, tuberosity of navicular, radial styloid process).
2. **Joint Depressions & Soft-Tissue Creases:** Located at surface skin creases or soft-tissue palpation depressions adjacent to bones and tendons (e.g., LU9 in depression between radial styloid and scaphoid; HT7 on wrist crease radial to flexor carpi ulnaris tendon; KI1 on plantar aponeurosis).

### Methodological Rule:
A bone landmark establishes the **deep skeletal coordinate constraint**. The clinical acupuncture point coordinates on the external skin surface are derived by projecting from the skeletal anchor outward along the anatomical surface normal to intersect the canonical skin boundary (`FJ2810`), preserving the physical soft-tissue thickness ($2-8\text{ mm}$ on distal extremities).

Under no circumstances is an uncalibrated legacy raycast substituted for skeletal ground truth.

---

## 5. Provenance, Versioning and Licensing Verification

- **Data Source:** BodyParts3D 4.0 Release, Database Center for Life Science (DBCLS), Research Organization of Information and Systems (ROIS), Japan.
- **Upstream Integration:** `3refs/upstream/tcm-3d/public/models/atlas.json` and associated binary chunk files (`body-*.bin`).
- **Cryptographic Invariants:**
  - `atlas.json` SHA256: `c359f4bcd2cba90b7411d66d5e9fc04dc81294d46cd5c1e8b212c824f2e5bbee`
  - `body-10.bin` (Skin + major skeleton) SHA256: `4a959d998acd35cf88518a0f2f8ab99b42d9f69c7ce0d6a814df315eeac807ac`
  - Canonical softened skin mesh (`fj2810_softened.bin`) SHA256: `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`
- **License Terms:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Redistribution Rights:** Commercial and non-commercial redistribution and adaptation are permitted with attribution.
- **Audit Conclusion:** The assets are legally cleared, cryptographically immutable, and anatomically sufficient for distal extremity calibration.
