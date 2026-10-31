# P15 Anatomical Asset License & Cervicothoracic Geometry Audit

**Milestone:** P15 — Cervicothoracic Biomechanics, Forward Head Posture & Upper Crossed Syndrome Studio  
**Date:** October 31, 2026  
**Auditor / Architect:** Open-Source Software Compliance Reviewer & 3D Visualization Engineer  
**Document ID:** `1docs/audits/P15/P15_CERVICOTHORACIC_ASSET_AUDIT.md`  
**Status:** VALIDATED & COMPLIANT  

---

## 1. Segment-Level Provenance & BodyParts3D IDs

Every osseous and muscular structure assembled into [`cervicothoracic_skeleton.glb`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/static/education/models/cervicothoracic_skeleton.glb) (1,539,324 bytes, SHA-256: `d9edeb9165cca790aca6cfabf2ee3bfa170d40ccbd9a662335b3ef68b244d678`) originates from authentic BodyParts3D v4.0 CT/MRI segmentation:

| Node Name | Segment Composition | BodyParts3D ID | FMA Concept | Bounding Box in Meters (Y-up) |
| :--- | :--- | :--- | :--- | :--- |
| **Thorax** | Manubrium, Sternum Body, Ribs 1–5, T1–T4 | `FJ3290`, `FJ3178`, `FJ3158`, `FJ3160`, `FJ3163`, `FJ3166` | FMA7486, FMA7487, FMA7514.. | $x: [-0.037, 0.036], y: [1.258, 1.455], z: [-0.083, 0.114]$ |
| **Cervical_Lower** | C3, C4, C5, C6, C7 | `FJ3161`, `FJ3164`, `FJ3167`, `FJ3170`, `FJ3172` | FMA12525, FMA12524.. | $x: [-0.033, 0.032], y: [1.442, 1.524], z: [-0.079, -0.010]$ |
| **Cervical_Upper** | C1 (Atlas), C2 (Axis) | `FJ3176`, `FJ3177` | FMA12519, FMA12520 | $x: [-0.041, 0.040], y: [1.511, 1.559], z: [-0.063, -0.012]$ |
| **Skull_Cranium** | Occipital, Frontal, Parietal, Temporal, Sphenoid | `FJ3309`, `FJ3200`, `FJ3274`, `FJ3380`, `FJ3281`, `FJ3386`, `FJ3394` | FMA52737, FMA52738.. | $x: [-0.062, 0.061], y: [1.555, 1.663], z: [-0.118, 0.001]$ |
| **Clavicle_R** | Right Clavicle | `FJ3362` | FMA13322 | $x: [-0.145, -0.010], y: [1.387, 1.434], z: [-0.045, 0.047]$ |
| **Scapula_R** | Right Scapula | `FJ3384` | FMA13395 | $x: [-0.166, -0.057], y: [1.262, 1.428], z: [-0.105, 0.003]$ |
| **Humerus_R** | Right Humerus | `FJ3368` | FMA23130 | $x: [-0.241, -0.140], y: [1.108, 1.415], z: [-0.049, 0.000]$ |
| **Levator_Scapulae** | Right & Left Levator Scapulae | `FJ1532`, `FJ1532M` | FMA9623 | Resolves the P14 unmodeled cervical-scapular connection |
| **Suboccipital_Muscles**| Rectus capitis post. maj/min, Obliquus capitis sup/inf | `FJ1563`, `FJ1564`, `FJ1567`, `FJ1568`, `FJ1584`, `FJ1585`, `FJ1589`, `FJ1590` | FMA9622.. | Connects C1–C2 to Occiput |

---

## 2. Licensing Compliance & Legal Separation

1. **Geometry Assets:** Sourced from BodyParts3D (Database Center for Life Science - DBCLS, Japan) via Z-Anatomy, licensed under **Creative Commons Attribution-ShareAlike 2.1 Japan (CC BY-SA 2.1 JP) / CC BY 4.0**.
2. **Software Code:** Three.js scene graphs, kinematic math engines, REST APIs, and educational UI controllers are original works distributed under the permissive **MIT License**.
3. **Attribution & Trademark:** Full attribution is retained in application footers, API payloads, and scenario manifests.
