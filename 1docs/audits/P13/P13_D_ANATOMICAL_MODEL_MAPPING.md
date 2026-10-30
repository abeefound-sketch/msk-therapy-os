# P13-D: ANATOMICAL MODEL MAPPING & NOMENCLATURE MATRIX
## Musculoskeletal Therapy OS (MSK-Therapy-OS) — Milestone P13
### Terminologia Anatomica · Bilingual Terminology (EN/VI) · Biomechanical Roles

- **Milestone:** P13 (Phase P13-D: Anatomical Standardization)
- **Document ID:** `1docs/audits/P13/P13_D_ANATOMICAL_MODEL_MAPPING.md`
- **Audit Date:** 2026-10-30
- **Auditor:** Medical Visualization Engineer & Anatomical Terminology Specialist
- **Status:** APPROVED & LOCKED

---

## 1. MAPPING ARCHITECTURE

The 3D model `anatomy.glb` (derived from BodyParts3D via Z-Anatomy) uses discrete mesh identifiers aligned with standard international anatomical definitions. The table below provides the full mapping across:
1. **GLTF Mesh ID:** Identifier used for WebGL raycasting, picking, and shader highlighting.
2. **Terminologia Anatomica (TA98):** Official Latin anatomical nomenclature.
3. **English Standard Name:** Standard medical term.
4. **Vietnamese Standard Name:** Vietnamese anatomical term.
5. **Functional Role in Rounded Shoulder Posture:** Biomechanical contribution to upper crossed syndrome and posture recurrence.

---

## 2. MUSCULOSKELETAL NOMENCLATURE MATRIX

| GLTF Mesh ID | Terminologia Anatomica | English Standard Name | Vietnamese Standard Name | Functional Role in Rounded Shoulders |
| :--- | :--- | :--- | :--- | :--- |
| `pectoralis_minor` | *Musculus pectoralis minor* | Pectoralis minor | Cơ ngực bé | **Primary Driver of Anterior Tilt:** Attaches to coracoid process (ribs 3-5); chronologically shortened; pulls scapula forward and down. |
| `pectoralis_major` | *Musculus pectoralis major* | Pectoralis major | Cơ ngực lớn | **Internal Rotator:** Sternal and clavicular fibers pull humerus into internal rotation and adduction. |
| `deltoid_anterior` | *Musculus deltoideus (pars clavicularis)* | Anterior deltoid | Cơ delta trước | **Anterior Pull:** Often tight and shortened in forward head and slumped postures. |
| `deltoid_lateral` | *Musculus deltoideus (pars acromialis)* | Lateral deltoid | Cơ delta giữa | **Arm Abductor:** Mediates glenohumeral elevation; requires stable scapular base. |
| `deltoid_posterior` | *Musculus deltoideus (pars spinalis)* | Posterior deltoid | Cơ delta sau | **External Rotator & Extensor:** Often lengthened and inhibited; needs activation. |
| `trapezius_upper` | *Musculus trapezius (pars descendens)* | Upper trapezius | Cơ thang trên | **Hyperactive Compensator:** Elevates clavicle/scapula; hypertonic due to stress and forward head posture. |
| `trapezius_middle` | *Musculus trapezius (pars transversa)* | Middle trapezius | Cơ thang giữa | **Scapular Retractor:** Weakened/lengthened; fails to counteract anterior pull. |
| `trapezius_lower` | *Musculus trapezius (pars ascendens)* | Lower trapezius | Cơ thang dưới | **Posterior Force Couple:** Crucial upward rotator and depressor; functionally inhibited in rounded shoulders. |
| `serratus_anterior` | *Musculus serratus anterior* | Serratus anterior | Cơ răng trước | **Scapular Stabilizer:** Prevents winging; upward rotator of inferior angle; inhibited in prolonged sitting. |
| `levator_scapulae` | *Musculus levator scapulae* | Levator scapulae | Cơ nâng vai | **Downward Rotator & Elevators:** Synergistic with upper trap; frequently develops trigger points. |
| `rhomboid_major` | *Musculus rhomboideus major* | Rhomboid major | Cơ trám lớn | **Retractor & Stabilizer:** Lengthened and inhibited; contributes to scapular protraction when underactive. |
| `rhomboid_minor` | *Musculus rhomboideus minor* | Rhomboid minor | Cơ trám bé | **Retractor & Elevators:** Acts in concert with rhomboid major. |
| `latissimus_dorsi` | *Musculus latissimus dorsi* | Latissimus dorsi | Cơ lưng rộng | **Internal Rotator & Depressor:** Tightness contributes to thoracic kyphosis and limited glenohumeral elevation. |

---

## 3. OSSEOUS LANDMARKS & ARTICULATIONS

| Osseous Structure | Anatomical Name | Landmark Features | Biomechanical Significance |
| :--- | :--- | :--- | :--- |
| `scapula` | Scapula (Shoulder blade) | Coracoid process, Acromion, Spine, Inferior angle | Mobile platform for humerus; participates in 2:1 scapulohumeral rhythm. |
| `clavicle` | Clavicle (Collarbone) | Sternal end, Acromial end | Only bony strut connecting upper limb to axial skeleton. |
| `humerus` | Humerus (Arm bone) | Humeral head, Greater/lesser tubercle, Bicipital groove | Glenohumeral joint articulation; internally rotated in rounded shoulders. |
| `sternum` | Sternum (Breastbone) | Manubrium, Body, Xiphoid process | Origin for sternocleidomastoid, pectoralis major, and sternoclavicular joint. |
| `ribs` | Costae (Rib cage) | Ribs 1 through 12 | Thoracic sliding surface for scapulothoracic articulation. |

---

## 4. CLINICAL INTEGRATION VERIFICATION

All mesh identifiers documented in this matrix are directly referenced in [`msk_therapy_os/biomechanics_adapter.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/biomechanics_adapter.py) and the frontend studio scripts, ensuring consistent picking, highlighting, and curriculum synchronization.
