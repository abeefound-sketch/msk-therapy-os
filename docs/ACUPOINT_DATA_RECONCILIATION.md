# Canonical Acupoint Data Reconciliation & Standard Provenance

**Document ID:** M2.7-RECON-002  
**Author:** Medical Terminology Architect, Senior Data Governance Specialist  
**Project:** MSK-Therapy-OS (`integration/m2.7-m2.8`)  
**Status:** Approved & Formally Reconciled  

---

## 1. Executive Summary

Previous development iterations reported confusing discrepancies between point counts cited across documentation, UI status badges, and source files—variously quoted as **361**, **362**, or **368**.

This audit provides definitive, mathematical, and historical reconciliation of all point counts across international standards, national standards, traditional reflexology schemes, and local practitioner customization.

> [!IMPORTANT]
> **Zero Point Remapping or Deletion:** No points were fabricated, renamed, deleted, or silently altered. Each number represents a distinct, clinically grounded knowledge boundary with explicit provenance.

---

## 2. Mathematical Reconciliation Formulation

$$\text{Runtime Atlas Total (368)} = \underbrace{\text{WHO Regular (361)} + \text{GB/T Yintang (1)}}_{\text{Canonical Standard Dataset: 362}} + \underbrace{\text{Dien Chan (4)}}_{\text{Reflexology: 4}} + \underbrace{\text{Active Custom Points (2)}}_{\text{SQLite User Authorship: 2}}$$

| Knowledge System | Standard Reference | Namespace | Point Count | Clinical & Topographical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **WHO Standard Meridians** | WHO Standard Acupuncture Point Locations (2008) | `WHO_CLASSICAL` | **361** | The international baseline comprising 14 regular channels: 12 organ meridians (309 pts) + Governor Vessel (28 pts: GV1–GV28) + Conception Vessel (24 pts: CV1–CV24). In WHO 2008, Yintang is classified as an Extra point (`EX-HN3`). |
| **Chinese National Standard** | GB/T 12346-2006 / GB/T 12346-2021 | `WHO_CLASSICAL` | **362** | Standardized by the Standardization Administration of China. Yintang (印堂) was officially incorporated into the Governing Vessel (Du Mai) as regular point `GV24+` (also known as GV29). Base file `acupuncture_3d.json` stores this 362-point dataset. |
| **Vietnamese Diên Chẩn** | Prof. Bùi Quốc Châu (1980) | `DIEN_CHAN` | **4** | Facial reflexology diagnostic & therapeutic landmarks (`DC_0`, `DC_1`, `DC_26`, `DC_126`). Included for integrated East Asian somatotopic study. Isolated from WHO classical points. |
| **Active Custom Points** | Milestone M2.5 / Local SQLite | `USER_CUSTOM` | **2** | Practitioner-authored clinical reflex points stored in `demo.sqlite3` (`GV14-MIRROR`, `TEST-MIRROR-01`). |
| **Total Runtime Atlas Points** | Combined Atlas Registry | **All** | **368** | Total unique logical codes loaded into memory and available for clinical selection and filtering. |

---

## 3. Meridian-by-Meridian Point Count Breakdown

The 362 canonical points in `msk_therapy_os/static/atlas/data/acupuncture_3d.json` partition exactly into the following channels:

```
┌────────────────────────────────────────────────────────┬────────┐
│ Meridian / Channel Name                                │ Count  │
├────────────────────────────────────────────────────────┼────────┤
│ Lung Meridian (LU)                                     │   11   │
│ Large Intestine Meridian (LI)                          │   20   │
│ Stomach Meridian (ST)                                  │   45   │
│ Spleen Meridian (SP)                                   │   21   │
│ Heart Meridian (HT)                                    │    9   │
│ Small Intestine Meridian (SI)                          │   19   │
│ Bladder Meridian (BL)                                  │   67   │
│ Kidney Meridian (KI)                                   │   27   │
│ Pericardium Meridian (PC)                              │    9   │
│ Triple Energizer / Sanjiao (TE)                        │   23   │
│ Gallbladder Meridian (GB)                              │   44   │
│ Liver Meridian (LR)                                    │   14   │
│ Conception Vessel / Ren Mai (CV)                       │   24   │
│ Governing Vessel / Du Mai (GV) (WHO 28 + GV24+ Yintang)│   29   │
├────────────────────────────────────────────────────────┼────────┤
│ Total Canonical Regular Points                         │  362   │
└────────────────────────────────────────────────────────┴────────┘
```

---

## 4. The Yintang (`GV24+` / `EX-HN3`) Clarification

1. **WHO Standard Nomenclature (1991 / 2008):**
   - Nomenclature: `EX-HN3` (Extra Head/Neck Point #3).
   - Location: On the anterior midline of the head, midway between the medial ends of the two eyebrows.
   - Channel: Not formally assigned to the 14 channels; counted among Extra Points. Total regular channel points: **361**.
2. **National Standard of P.R. China (GB/T 12346-2006, reaffirmation 2021):**
   - Nomenclature: Formally integrated into the Governing Vessel as regular point `GV24+` (or GV29 in some clinical texts) due to its anatomical location on the sagitally symmetric course of Du Mai.
   - Total regular channel points: **362**.
3. **MSK-Therapy-OS Policy:**
   - Coded internally as `GV24+` to preserve bidirectional cross-referencing with both WHO Extra Points and GB/T National Standards.
   - Metadata explicitly documents both citations in `standards: ["WHO 2008", "GB/T 12346-2021"]`.

---

## 5. Non-WHO Knowledge Systems Isolation

To eliminate clinical confusion:
1. **Vietnamese Diên Chẩn (4 points):**
   - Isolated under namespace `lib_dien_chan`.
   - Distinct pink marker styling (`#ec4899`).
   - Counter and selection displays explicitly flag non-WHO status: `(Reflexology/Non-WHO)`.
2. **Thai Sen Sib Lines (3 lines):**
   - Isolated under namespace `lib_thai_sen`.
   - Trajectories: Sen Ittha, Sen Pingkhla, Sen Sumana.
   - Explicit toolbar badge: `Thai Sen Sib [3 lines] (Incomplete educational dataset - 3 of 10 lines)`.
3. **Musculoskeletal Palpation Landmarks:**
   - Isolated under namespace `lib_msk_landmarks`.
   - Anchored to BodyParts3D FMA concepts (e.g. `FMA32557 Descending part of trapezius`).

---

## 6. Live Reconciled Telemetry API

The application exposes `/api/governance/reconciliation` for automated verification:
```json
{
  "who_standard_count": 361,
  "who_standard_notes": "14 classical channels (12 organ meridians + 28 GV + 24 CV). Yintang classified as Extra Point EX-HN3.",
  "national_standard_count": 362,
  "national_standard_citation": "GB/T 12346-2006 / GB/T 12346-2021",
  "national_standard_notes": "Yintang officially incorporated into Du Mai (Governing Vessel) as GV24+ / GV29.",
  "dien_chan_count": 4,
  "dien_chan_notes": "Vietnamese facial reflex points (DC_0, DC_1, DC_26, DC_126) isolated in lib_dien_chan namespace.",
  "active_custom_count": 2,
  "runtime_total_points": 368,
  "conservation_formula": "Available = Visible + Clustered + Filtered",
  "status": "RECONCILED"
}
```
