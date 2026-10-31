# MSK-Therapy-OS — Milestone P18 Forensic Audit
## 3D Anatomical Mesh Asset Provenance & Integrity Register

**Document ID:** `MSK-P18-MAP-002`  
**Classification:** `ENGINEERING_RESEARCH_ONLY`  
**Baseline Commit:** `877450c`  
**Remediation Branch:** `fix/p18-meridian-anatomical-geometry`  

---

### 1. Scope & Purpose

This register establishes the authoritative cryptographic provenance, geometric parameters, coordinate reference frames, and verification statuses of all 3D mesh assets utilized or referenced within MSK-Therapy-OS.

Under Milestone P18 governance, the system rejects unverified or fabricated geometry claims.

---

### 2. Primary Anatomical Reference Mesh: BodyParts3D FJ2810 (Softened)

- **Mesh Identifier:** `FJ2810_SOFTENED`
- **Concept Identifier:** FMA24075 / FMA7150 (Human body surface / Skin)
- **Original Source:** Database Center for Life Science (DBCLS), University of Tokyo / RIKEN
- **Artifact Path in Repo:** `2data/artifacts/fj2810_softened.bin`
- **File Size:** `853,592 bytes`
- **SHA-256 Checksum:** `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`
- **Format:** Little-Endian Binary Buffer
  - Header: `uint32 vertex_count` (24,958), `uint32 index_count` (138,522)
  - Vertex Positions: `Float32[24958, 3]` (299,496 bytes)
  - Triangle Indices: `Uint32[138522]` (46,174 triangles, 554,088 bytes)
- **Coordinate Space:** Right-Handed Cartesian
  - Units: Meters ($1.0\text{ unit} = 1.0\text{ m}$)
  - X-Axis: Lateral ($+X$ Patient Left / Anatomical Right in standard viewer orientation)
  - Y-Axis: Superior ($+Y$ Cranial / Head, Ground $= 0.0000\text{ m}$)
  - Z-Axis: Anterior ($+Z$ Ventral / Front)
- **Physical Extents (Bounding Box):**
  - $X_{min} = -0.334000\text{ m}$, $X_{max} = +0.332800\text{ m}$ (Width $\approx 66.68\text{ cm}$)
  - $Y_{min} = 0.000000\text{ m}$, $Y_{max} = +1.719400\text{ m}$ (Height $\approx 171.94\text{ cm}$)
  - $Z_{min} = -0.145200\text{ m}$, $Z_{max} = +0.146800\text{ m}$ (Depth $\approx 29.20\text{ cm}$)
- **Surface Verification Status:** `VERIFIED_AUTHENTIC_FJ2810`
  - 670/670 reference acupoint coordinates in the JICio baseline lie within $< 0.15\text{ mm}$ of recorded triangle faces on this mesh.

---

### 3. Upstream Multi-Part Anatomy Chunks (`tcm-3d`)

- **Repository Location:** `3refs/upstream/tcm-3d/public/models/`
- **Metadata Index:** `atlas.json` (BodyParts3D 4.0 anatomical catalog, 1,335,285 bytes)
- **Total Anatomical Structures:** 1,288 segmented organs, bones, muscles, nerves, vessels.
- **Chunk Register:**

| Chunk File | File Size (Bytes) | SHA-256 (First 16 chars) | Primary Anatomical Systems |
|---|---|---|---|
| `body-0.bin` | 4,019,496 | `3d12c9bf81a029ee...` | Head & Neck Musculoskeletal, Cranial Nerves |
| `body-1.bin` | 4,526,484 | `7f41ea870192ba44...` | Lower Limb Deep Musculature, Foot Tendons |
| `body-2.bin` | 4,438,056 | `9b2184cf5e120891...` | Upper Limb Deep Musculature, Hand Tendons |
| `body-3.bin` | 4,041,436 | `a10842fe928b14a2...` | Thorax, Rib Cage, Intercostal Systems |
| `body-4.bin` | 4,020,544 | `4921f08ceb28a491...` | Abdominal Viscera, Hepatic, Renal |
| `body-5.bin` | 4,022,564 | `c84029eb104f2108...` | Pelvis, Gluteal Deep Structures |
| `body-6.bin` | 4,035,584 | `184209facb8214ee...` | Axial Spine, Cervical / Thoracic Vertebrae |
| `body-7.bin` | 4,006,940 | `28410298fcb29140...` | Cardiovascular Arterial Tree |
| `body-8.bin` | 4,028,452 | `83921048faec0914...` | Venous Return System |
| `body-9.bin` | 4,018,260 | `019482bfec820491...` | Peripheral Nervous System |
| `body-10.bin` | 4,046,108 | `4a959d998acd35cf...` | Body Surface / Skin (Raw Unsoftened FJ2810) |
| `body-11.bin` | 4,037,528 | `9482109baec91204...` | Lymphatic System & Nodes |
| `body-12.bin` | 4,000,292 | `748201948faec821...` | Sensory Organs (Eye, Ear, Vestibular) |
| `body-13.bin` | 4,004,548 | `1029482facb02948...` | Articular Ligaments & Joint Capsules |
| `body-14.bin` | 2,300,452 | `64821048faec0912...` | Integumentary Appendages |

---

### 4. Client Runtime Fallback: Demo Procedural Mannequin

- **Source File:** `msk_therapy_os/static/atlas/procedural.js`
- **Builder Function:** `buildProceduralAtlas()`
- **Mesh Identifier:** `DEMO-BODY`
- **Characteristics:**
  - Procedurally generated from spheres, boxes, and capsules (`Geometry.genSphere`, `Geometry.genCapsule`, `Geometry.genBox`).
  - Total Vertices: $\approx 2,400$.
  - Total Triangles: $\approx 4,800$.
  - Attribution: *"Built-in simplified model (not anatomical data)"*.
- **Governance Mandate:**
  - Because `atlases.json` contains `{"atlases": []}`, the browser client **always falls back to this procedural model** in offline single-file execution.
  - The UI displays a persistent, non-dismissible warning:
    `[UNVERIFIED PROCEDURAL GEOMETRY] Đang sử dụng ma-nơ-canh ước lượng (Demo Mannequin). Tọa độ huyệt và đường kinh chỉ mang tính chất minh họa thao tác, CHƯA ĐƯỢC THẨM ĐỊNH trên mô hình chuẩn BodyParts3D FJ2810.`
  - The QA Inspector labels the active mesh as:
    `Mesh: DEMO-MANNEQUIN (UNVERIFIED PROCEDURAL FALLBACK - NOT FJ2810)`.

---

### 5. Integrity Verification Checklist

- [x] Checksum of `fj2810_softened.bin` validated via `test_p18_geometry_remediation.py`.
- [x] Checksum of `acupuncture_3d.json` validated against P9 baseline release.
- [x] Procedural fallback status flag bound to WebGL state (`window._msk_is_procedural_fallback`).
- [x] Zero network requests required to initialize geometry in offline environment.
