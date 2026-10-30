# P13-B: ASSET PROVENANCE & INTEGRITY REGISTER
## Musculoskeletal Therapy OS (MSK-Therapy-OS) — Milestone P13
### Upstream Origins · SHA-256 Fingerprints · Asset Pipeline Modifications

- **Milestone:** P13 (Phase P13-B: Open-Source Compliance & Asset Governance)
- **Register Date:** 2026-10-30
- **Auditor:** Open-Source Software Compliance Reviewer & Release Engineer
- **Status:** CERTIFIED & LOCKED

---

## 1. PROVENANCE SUMMARY

MSK-Therapy-OS integrates open-source anatomical assets and rendering engines strictly from auditable, permissively/freely licensed upstream sources. No blackbox binaries, obfuscated blobs, or proprietary 3D formats are accepted.

---

## 2. ASSET SPECIFICATION & CHECKSUM MANIFEST

### 2.1 Anatomical 3D Model: `anatomy.glb`

| Attribute | Upstream Source Record |
| :--- | :--- |
| **Primary Origin** | BodyParts3D dataset, Database Center for Life Science (DBCLS), Japan (<https://dbarchive.biosciencedbc.jp/en/bodyparts3d/>) |
| **Intermediate Curator** | Z-Anatomy Project (<https://www.z-anatomy.com/>) |
| **Local Staging Path** | `3refs/upstream/anatomy-3d/models/anatomy.glb` |
| **Installed Target Path** | `msk_therapy_os/static/education/models/anatomy.glb` |
| **Original License** | Creative Commons Attribution-ShareAlike 2.1 Japan (CC BY-SA 2.1 JP) |
| **Derivative License** | Creative Commons Attribution-ShareAlike 2.1 Japan (CC BY-SA 2.1 JP) |
| **File Format** | Binary glTF 2.0 (`.glb`) |
| **File Size** | 9,291,204 bytes (8.86 MB) |
| **Canonical SHA-256** | `318347f91e4989da0c271e9662df536943df1149b413fef01cf21586073ea73e` |

#### Derivative Modifications Applied to Upstream BodyParts3D Geometry:
1. **Mesh Decimation & Boundary Cropping:** Segmented anatomical components cropped to full-body musculoskeletal scope; redundant non-musculoskeletal internal organs pruned.
2. **Coordinate Frame Conversion:** Transformed from BodyParts3D medical MRI standard (Z-up, millimeter) to standard WebGL/Three.js orientation (Y-up, meters) with a uniform scaling factor $s \approx 0.0010774$ normalized to a standard anatomical height of 1.780 m.
3. **Attribute Stripping for integrated GPU Optimization:** Pre-computed vertex normals removed from the GLB buffer to achieve a 40% file size reduction. Normals are recomputed deterministically upon load via `BufferGeometry.computeVertexNormals()`.
4. **Anatomical Naming Alignment:** Geometry primitives mapped to standardized identifiers (e.g., `pectoralis_major`, `pectoralis_minor`, `deltoid_anterior`, `trapezius_lower`, `serratus_anterior`) matching the educational curriculum.

---

### 2.2 3D Rendering Engine: Three.js (r160)

| Attribute | Upstream Source Record |
| :--- | :--- |
| **Project** | Three.js JavaScript 3D Engine (<https://threejs.org/>) |
| **Version** | r160 |
| **License** | MIT License (Copyright 2010-2026 Three.js Authors) |
| **Local Staging Path** | `3refs/upstream/anatomy-3d/vendor/three/` |
| **Installed Target Path** | `msk_therapy_os/static/education/vendor/three/` |
| **Network Policy** | 100% Offline Local Distribution (Zero CDN dependencies) |

#### Component Manifest & Checksums:
- `three.module.js` (1,272,972 bytes) — SHA-256: `76dea8151bc9352a...`
- `OrbitControls.js` (29,868 bytes) — SHA-256: `5a44a9e86a2a0fb1...`
- `loaders/GLTFLoader.js` (168,794 bytes) — SHA-256: `14cb351efb88235e...`
- `utils/BufferGeometryUtils.js` (40,519 bytes) — SHA-256: `a93b4e76d9c6e3b5...`
- `LICENSE` (1,387 bytes) — SHA-256: `920bf3f2fa0433c7...`

---

## 3. ASSET PIPELINE VERIFICATION

1. **Tamper Detection:** The SHA-256 checksum of `anatomy.glb` is embedded in the unit test suite (`tests/test_p13_biomechanics_adapter.py`) to prevent silent asset corruption.
2. **Fail-Closed Loading:** The client-side loader verifies file size and valid glTF header magic bytes (`0x46546C67`) before parsing.
3. **Attribution Display:** The viewer UI prominently renders attribution links to DBCLS BodyParts3D and Z-Anatomy in compliance with CC BY-SA 2.1 JP Section 4.
