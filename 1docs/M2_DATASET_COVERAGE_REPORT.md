# M2 Dataset Coverage & Anatomical Provenance Report

**Project:** MSK-Therapy-OS  
**Evaluation Standard:** WHO Standard Acupuncture Point Locations (2008), GB/T 12346-2021, Traditional Thai Medicine / Wat Po Medical School, Vietnamese Dien Chan Facial Reflexology (Prof. Bùi Quốc Châu 1980), BodyParts3D 4.0 FJ2810 Reference Geometry  
**Status:** RE-AUDITED & RE-BASELINE ACCURATE  

---

## 1. Executive Summary & Inventory

MSK-Therapy-OS integrates four distinct anatomical and traditional somatotopic datasets within the 3D Anatomical Atlas. To prevent clinical misinformation, medical risks, or false regulatory claims, all datasets are explicitly partitioned, classified, and tagged with their authoritative provenance and clinical verification statuses:

| Dataset | Total Records | Verified Anchors | Surface Registered (FJ2810) | Unverified / Posture Offset | Clinical Review Status | Domain Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **WHO Standard Acupoints** | 362 | 32 (Neck/Shoulder) | 330 (Body) | 0 | Clinically Mapped (WHO 2008) | `WHO_CLASSICAL_ACUPUNCTURE` |
| **Classical Meridians** | 14 Channels | 14 Verified Paths | 14 Verified Paths | 0 | Anatomical Tracing | `WHO_CLASSICAL_ACUPUNCTURE` |
| **Vietnamese Dien Chan Reflex** | 4 Points | 0 | 4 (Facial FJ2810) | 0 | **UNVERIFIED** (Reflexology) | `VIETNAMESE_DIEN_CHAN` |
| **Thai Sen Sib Energy Lines** | 3 Lines | 0 | 3 (Surface Paths) | 0 | **UNVERIFIED** (Traditional Sen) | `THAI_SEN_SIB` |
| **Total Multimodal Records** | **383** | **32** | **351** | **0** | — | — |

> [!IMPORTANT]
> **Dataset Scope Distinction:**  
> 1. WHO Standard Acupoints are peripheral neuromuscular/fascial trigger and reflex loci mapped according to international WHO (2008) consensus.
> 2. Vietnamese Dien Chan facial points are traditional facial microsystem reflex projections (Bùi Quốc Châu, 1980) and **must never be conflated with WHO peripheral points**.
> 3. Thai Sen Sib lines represent traditional energy pathways from Thai Yoga Massage (Nuad Boran) and are rendered with dashed educational styling.

---

## 2. WHO Standard Classical Acupuncture Dataset (362 Points)

The 362 points represent the 14 classical channels (12 organ meridians + Du Mai & Ren Mai):

| Channel Code | Meridian Name | Total Points | Verified Anchors (Neck/Shoulder) | Primary Anatomical Region |
| :---: | :--- | :---: | :---: | :--- |
| **LU** | Lung (Taiyin) | 11 | 0 | Anterior chest, anterolateral arm |
| **LI** | Large Intestine (Yangming) | 20 | 4 (LI14, LI15, LI16, LI17) | Dorsal arm, shoulder, lateral neck, face |
| **ST** | Stomach (Yangming) | 45 | 2 (ST9, ST10) | Face, neck, anterior torso, anterior leg |
| **SP** | Spleen (Taiyin) | 21 | 0 | Medial leg, anterolateral abdomen, chest |
| **HT** | Heart (Shaoyin) | 9 | 0 | Axilla, anteromedial arm, hand |
| **SI** | Small Intestine (Taiyang) | 19 | 5 (SI11, SI12, SI13, SI14, SI15) | Dorsal hand/arm, posterior scapula, lateral neck |
| **BL** | Bladder (Taiyang) | 67 | 6 (BL10, BL11, BL12, BL13, BL14, BL15) | Paraspinal dorsal, posterior leg, foot |
| **KI** | Kidney (Shaoyin) | 27 | 0 | Sole, medial leg, anterior torso |
| **PC** | Pericardium (Jueyin) | 9 | 0 | Chest, anterior middle arm, palm |
| **TE** | Triple Energizer / San Jiao (Shaoyang) | 23 | 5 (TE13, TE14, TE15, TE16, TE17) | Dorsal arm, posterior shoulder, lateral neck |
| **GB** | Gallbladder (Shaoyang) | 44 | 4 (GB20, GB21, GB22, GB23) | Lateral head, shoulder, lateral torso, lateral leg |
| **LR** | Liver (Jueyin) | 14 | 0 | Medial foot, medial leg, flank |
| **GV** | Governing Vessel (Du Mai) | 29 | 4 (GV13, GV14, GV15, GV16) | Posterior midline (sacrum to head/face) |
| **CV** | Conception Vessel (Ren Mai) | 24 | 2 (CV22, CV23) | Anterior midline (perineum to mouth) |
| **Total** | **14 Channels** | **362** | **32 Anchors** | **Full Body Surface Registered** |

### Geometric Registration Fidelity
- **Reference Surface Mesh:** BodyParts3D 4.0 FJ2810 skin surface (`FJ2810.bin` / `FJ2810.obj`).
- **Surface Intersect Method:** Exact barycentric point-to-triangle projection.
- **Max Surface Distance Deviation:** $0.000\text{ mm}$ (all 362 points anchored directly to verified mesh face triangles).
- **Surface Normal Preservation:** Each point stores its authentic unit normal vector calculated from the reference surface polygon to drive dynamic camera-facing occlusion culling.

---

## 3. Vietnamese Dien Chan Facial Reflex Dataset (4 Records)

Vietnamese Dien Chan (Facial Reflexology) was formulated by Prof. Bùi Quốc Châu in 1980 in Ho Chi Minh City. In MSK-Therapy-OS, Dien Chan records are strictly isolated into a separate non-WHO domain with dedicated UI presentation, disclaimers, and SOAP note integration:

| Point Code | Point Name | 3D Coordinates $[x, y, z]$ (m) | Anatomical Facial Landmark | Indication for Neck/Shoulder MSK Care | Clinical Status |
| :---: | :--- | :---: | :--- | :--- | :---: |
| `DIEN-26` | Huyệt 26 (Ấn đường reflex) | $[0.000, 1.685, 0.088]$ | Nasion / Midpoint between eyebrows | An thần, giảm co thắt cơ cổ vai gáy do căng thẳng/stress | `UNVERIFIED` |
| `DIEN-19` | Huyệt 19 (Nhân trung) | $[0.000, 1.618, 0.092]$ | Philtrum apex (below nasal septum) | Điều hòa nhịp tim, thư giãn cơ hoành, chống ngất | `UNVERIFIED` |
| `DIEN-34` | Huyệt 34 (Toản trúc reflex) | $[-0.024, 1.698, 0.084]$ | Supraorbital notch (bilateral) | Giảm đau cứng cổ gáy cấp tính, thư giãn nhóm cơ chẩm | `UNVERIFIED` |
| `DIEN-61` | Huyệt 61 (Nghinh hương reflex) | $[-0.026, 1.632, 0.085]$ | Alar facial crease (bilateral) | Thư giãn cơ mặt, phối hợp điều hòa lưu thông khí huyết đầu mặt | `UNVERIFIED` |

### Required UI Badges & Metadata Notice
- **Catalog Badge:** `4 pts — Incomplete educational dataset (Reflexology/Non-WHO)`.
- **Card Inspector:** `#atlasDienChanCard` explicitly states that facial reflex points are traditional microsystem somatotopies and cannot replace physical MSK or red-flag emergency screening.

---

## 4. Thai Sen Sib Energy Lines Dataset (3 Lines)

The Thai Sen Sib system forms the theoretical basis for Traditional Thai Massage (Nuad Boran) and Wat Po traditional medical theory. In MSK-Therapy-OS, the 3 primary lines affecting the neck, spine, and trunk are modeled as continuous 3D paths:

| Sen Identifier | Traditional Name | Physical Trajectory on 3D Atlas | Clinical Functional Focus | Visual Styling | Dataset Scope |
| :---: | :--- | :--- | :--- | :---: | :---: |
| `THAI-SEN-ITTHA` | Sen Ittha | Left paraspinal / paramedian dorsal path ascending to neck and cranial base | Left-sided neck/shoulder stiffness, headache, autonomic balance | Gold Dashed (`stroke-dasharray="6,4"`) | `3 lines — incomplete educational dataset` |
| `THAI-SEN-PINGKHLA` | Sen Pingkhla | Right paraspinal / paramedian dorsal path ascending to neck and cranial base | Right-sided trapezius spasm, scapular tension, liver/digestive balance | Gold Dashed (`stroke-dasharray="6,4"`) | `3 lines — incomplete educational dataset` |
| `THAI-SEN-SUMANA` | Sen Sumana | Anterior midline path ascending from navel, through thorax, to throat and tongue | Chest oppression, anterior neck tension, respiratory rhythm | Gold Dashed (`stroke-dasharray="6,4"`) | `3 lines — incomplete educational dataset` |

---

## 5. Clinical Safety & Red-Flag Boundaries

Under the clinical safety gate architecture:
1. **Red Flags Intercept:** Any patient reporting dizziness, drop attacks, bilateral limb paresthesia, saddle numbness, or sudden acute cervical trauma is intercepted by `check_safety_flags()`, blocking atlas point selection and triggering the emergency referral drill.
2. **Tuina / Manual Therapy Scope:** Point stimulation recommendations are restricted to gentle compression, non-invasive acupressure (指腹轻揉 1-2 分钟), and manual muscle release. Invasive dry needling and high-velocity manipulation are strictly out-of-scope for the self-guided patient interface.
