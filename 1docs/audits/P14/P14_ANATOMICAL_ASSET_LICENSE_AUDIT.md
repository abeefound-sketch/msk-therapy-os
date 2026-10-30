# P14-A: ANATOMICAL ASSET LICENSE & PROVENANCE AUDIT
## Musculoskeletal Therapy OS (MSK-Therapy-OS) — Milestone P14
### Multi-Tier License Provenance · CC BY-SA Boundary · Component Attribution Manifest

- **Milestone:** P14 (Phase P14-A: License Governance)
- **Document ID:** `1docs/audits/P14/P14_ANATOMICAL_ASSET_LICENSE_AUDIT.md`
- **Audit Date:** 2026-10-30
- **Auditor:** Open-Source Software Compliance Reviewer & Research Governance Lead
- **Status:** COMPLIANT & LOCKED

---

## 1. COMPONENT-LEVEL PROVENANCE & LICENSE REGISTER

Every anatomical asset and rendering library integrated into MSK-Therapy-OS is mapped to its original upstream creator and governing legal license:

| Component | File Path in Project | Upstream Source & Copyright Holder | Governing License | Redistribution Conditions |
| :--- | :--- | :--- | :--- | :--- |
| **Volumetric Muscular Mesh** | `msk_therapy_os/static/education/models/anatomy.glb` | **BodyParts3D** (Database Center for Life Science - DBCLS, Japan) via **Z-Anatomy** | **CC BY-SA 2.1 Japan** | 1. Credit DBCLS & Z-Anatomy<br/>2. ShareAlike on model adaptations<br/>3. Retain license notices |
| **Shoulder Skeletal Mesh** | `msk_therapy_os/static/education/models/shoulder_skeleton.glb` | **BodyParts3D v4.0** (Database Center for Life Science - DBCLS, Japan) | **CC BY-SA 2.1 Japan / CC BY 4.0** | 1. Credit DBCLS BodyParts3D<br/>2. Disclose extraction pipeline<br/>3. ShareAlike on mesh derivatives |
| **3D Rendering Engine** | `msk_therapy_os/static/education/vendor/three/` | **Three.js** (Ricardo Cabello / Mr.doob & Contributors) | **MIT License** | Include copyright and permission notice |
| **Biomechanics Kinematics Adapter** | `msk_therapy_os/biomechanics_adapter.py` | **MSK-Therapy-OS Project** (OpenSim research derivative) | **MIT License** | Standard permissive software license |
| **Educational Curriculum & UI** | `msk_therapy_os/static/education/` (`index.html`, `shoulder_lab.js`) | **MSK-Therapy-OS Project** | **MIT License** | Standard permissive software license |

---

## 2. LEGAL BOUNDARY: CODE VS. ASSETS

Under copyright law and the terms of Creative Commons Attribution-ShareAlike 2.1 Japan Section 4:
1. **The ShareAlike condition attaches exclusively to the 3D anatomical meshes and their direct geometric adaptations.**
2. **Software scripts** (`server.py`, `anatomy_viewer.js`, `shoulder_lab.js`, `biomechanics_adapter.py`) that fetch, parse, and position these 3D meshes at runtime do **not** constitute a derivative adaptation of the polygon dataset. They are independent computer software programs distributed under permissive terms.
3. Embedding `anatomy.glb` or `shoulder_skeleton.glb` in an educational web view does not subject the broader MSK-Therapy-OS clinical platform to ShareAlike copyleft requirements.

---

## 3. MANDATORY ATTRIBUTION NOTICE

The following attribution notice is displayed in the Education Studio footer and system API:

```text
3D Anatomical Meshes derived from BodyParts3D (Database Center for Life Science - DBCLS, Japan)
and curated via Z-Anatomy, licensed under Creative Commons Attribution-ShareAlike 2.1 Japan
(CC BY-SA 2.1 JP). 3D WebGL rendering powered by Three.js r160 (MIT License).
```

---

## 4. AUDIT CONCLUSION

All asset rights, origins, and licenses are established. There are zero undocumented blobs or proprietary blackbox models in the repository.
