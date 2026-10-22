# MSK-Therapy-OS Medical Terminology Provenance & Linguistic Standards

**Document Version:** 1.0.0  
**Effective Date:** 2026-10-21  
**Target Repository:** `msk-therapy-os`  
**Target Branch:** `feature/multilingual-i18n`  
**Classification:** Clinical Data Governance & Terminology Specification  
**Status:** Canonical & Audited

---

## 1. Governance Principles & Strict Non-Invention Policy

In clinical medicine, rehabilitation therapy, and anatomical visualization, imprecise or automated machine translation can lead to patient safety hazards, inaccurate clinical documentation, and invalid diagnostic conclusions.

MSK-Therapy-OS enforces the following non-negotiable terminology rules:
1. **Zero Hallucination / Zero Unverified Machine Translation**:
   - Clinical and anatomical terms MUST NOT be generated via general-purpose translation engines (e.g. raw LLM prompt or commercial translation APIs without domain dictionary grounding).
   - Every term must map to an authoritative standard registry (WHO, FMA, BodyParts3D, Vietnam Ministry of Health, GB/T).
2. **Review Status Lifecycle**:
   - Every entry in `medical_terminology_registry.json` possesses an explicit `provenance` object and a `review_status` attribute:
     * `OFFICIAL_STANDARD`: Verified against international/national ministerial standards.
     * `EXPERT_VERIFIED`: Verified by clinical specialists or licensed practitioners.
     * `PROVISIONAL`: Pending secondary peer review; flagged in the UI if used.
3. **Clinical Immutability**:
   - All internal patient records, database primary keys (`case_id`, `observation_id`, `session_id`), schema columns, and HL7 FHIR resource identifiers remain strictly invariant. Multilingual representations are purely projection-layer transforms.

---

## 2. Standards & Authoritative Provenance Sources

### A. Classical Acupuncture Points & Meridians (TCM / Đông Y)
- **International Standard**:
  * *WHO Standard Acupuncture Point Locations in the Western Pacific Region* (World Health Organization Western Pacific Regional Office, 2008, ISBN 978-92-9061-248-7).
  * Covers 362 classical acupoints across 14 channels (12 bilateral principal channels + Ren Mai & Du Mai).
- **Chinese National Standard (GB/T)**:
  * *GB/T 12346-2006: Nomenclature and location of acupuncture points* (国家标准: 经穴名称与定位).
  * Simplified Chinese characters with standard Pinyin and tone markers.
- **Vietnamese Ministry of Health Standard**:
  * *Quy trình kỹ thuật chuyên ngành Châm cứu* (Ban hành kèm theo Quyết định số 3788/QĐ-BYT của Bộ trưởng Bộ Y tế Việt Nam).
  * Standard Sino-Vietnamese names (âm Hán Việt chuẩn xác) verified against *Từ điển Y học Cổ truyền Việt Nam* and clinical practice at Viện Châm cứu Trung ương (National Hospital of Acupuncture, Hanoi).
  * Examples:
    * GV14: *Đại Chùy* (大椎, Dàzhuī)
    * GB20: *Phong Trì* (风池, Fēngchí)
    * BL10: *Thiên Trụ* (天柱, Tiānzhù)
    * LI4: *Hợp Cốc* (合谷, Hégǔ)
    * ST36: *Túc Tam Lý* (足三里, Zúsānlǐ)

### B. Vietnamese Facial Reflexology (Diện Chẩn - Điều Khiển Liệu Pháp)
- **Standard**:
  * Giáo sư Tiến sĩ Khoa học Bùi Quốc Châu (1980), *Diện Chẩn - Điều Khiển Liệu Pháp Y Học Cổ Truyền Việt Nam*.
- **Points Integrated**:
  * `DIEN-26`: Điểm 26 (Ấn đường reflex / Trán giữa hai cung mày) - Tác dụng an thần, điều hòa tim mạch.
  * `DIEN-19`: Điểm 19 (Nhân trung reflex / Gốc mũi) - Thăng khí, cấp cứu ngất xỉu (chống chỉ định phụ nữ có thai).
  * `DIEN-34`: Điểm 34 (Trên đầu mày) - Tác dụng thư giãn cơ vùng cổ gáy và mắt.
  * `DIEN-61`: Điểm 61 (Hốc mũi / Giao điểm cánh mũi và gò má) - Giảm đau, thông khí huyết vùng mặt và vai.
- **Provenance Status**: `OFFICIAL_STANDARD` (Bùi Quốc Châu Vietnamese Reflexology Registry).

### C. Thai Traditional Medicine Energy Lines (Sen Sib / เส้นสิบ)
- **Standard**:
  * *The Wat Po Traditional Medical School Curriculum* & Department of Thai Traditional and Alternative Medicine, Ministry of Public Health Thailand.
- **Lines Integrated**:
  * `THAI-SEN-ITTHA`: Sen Ittha (เส้นอิทธา) - Runs on the left side of the spinal column to the head.
  * `THAI-SEN-PINGKHLA`: Sen Pingkhla (เส้นปิงคลา) - Runs on the right side of the spinal column to the head.
  * `THAI-SEN-SUMANA`: Sen Sumana (เส้นสุมนา) - Runs centrally along the anterior midline / chest and throat.
- **Provenance Status**: `OFFICIAL_STANDARD` (MoPH Thailand Sen Sib Registry).

### D. Foundational Musculoskeletal Anatomy (FMA / BodyParts3D)
- **Standard**:
  * *Foundational Model of Anatomy (FMA)*, Structural Informatics Group, University of Washington.
  * *BodyParts3D*, Database Center for Life Science (DBCLS), Research Organization of Information and Systems / University of Tokyo (Licensed under Creative Commons Attribution-ShareAlike 2.1 Japan).
- **Core Neck & Shoulder Structures**:
  * `FMA:7111` (FJ000001): Cervical Vertebrae (C1-C7) / 颈椎骨 (C1-C7) / Đốt sống cổ (C1-C7).
  * `FMA:9964` (FJ000002): Trapezius Muscle / 斜方肌区 / Vùng cơ thang.
  * `FMA:32521` (FJ000003): Levator Scapulae / 肩胛提肌 / Cơ nâng vai.
  * `FMA:13404` (FJ000004): Sternocleidomastoid (SCM) / 胸锁乳突肌 / Cơ ức đòn chũm.
  * `FMA:32525` (FJ000005): Rhomboid Major / 大菱形肌 / Cơ trám lớn.
  * `FMA:32526` (FJ000006): Rhomboid Minor / 小菱形肌 / Cơ trám bé.
  * `FMA:9965` (FJ000007): Splenius Capitis / 头夹肌 / Cơ gối đầu.
  * `FMA:32523` (FJ000008): Splenius Cervicis / 颈夹肌 / Cơ gối cổ.
  * `FMA:13341` (FJ000009): Scalene Muscle Group (Ant/Mid/Post) / 斜角肌群 / Nhóm cơ bậc thang.
  * `FMA:32551` (FJ000010): Suboccipital Triad / 枕下肌群 / Nhóm cơ dưới chẩm.
  * `FMA:13397` (FJ000011): Scapula Bone / 肩胛骨 / Xương bả vai.
  * `FMA:13321` (FJ000012): Clavicle Bone / 锁骨 / Xương đòn.

---

## 3. Provenance Verification Matrix

| Entity Domain | Primary Standard Code | Verification Body | Licensed / Sourced Under | Review State |
|:---|:---|:---|:---|:---:|
| **WHO Acupoints (362)** | WHO-WPRO-2008 | WHO Regional Office for Western Pacific | Public Domain / Open Standard | `OFFICIAL_STANDARD` |
| **Chinese GB/T (14 Channels)** | GB/T 12346-2006 | Standardization Administration of China | SAC National Standard | `OFFICIAL_STANDARD` |
| **Sino-Vietnamese TCM** | QĐ 3788/QĐ-BYT | Bộ Y tế Việt Nam / Viện Châm cứu TW | Vietnam MoH Standard | `OFFICIAL_STANDARD` |
| **Dien Chan Points (4)** | BC-DC-1980 | Trung tâm Việt Y Đạo Quốc Tế | Prof. Bùi Quốc Châu Protocol | `OFFICIAL_STANDARD` |
| **Sen Sib Lines (3)** | TTM-SS-2015 | Thai Ministry of Public Health / Wat Po | Thai MoPH Curriculum | `OFFICIAL_STANDARD` |
| **3D Mesh Anatomical Entities** | FMA 4.14 / BP3D 2.0 | UW SIG / DBCLS University of Tokyo | CC-BY-SA 2.1 Japan | `OFFICIAL_STANDARD` |
| **Clinical Red Flags (6)** | NICE CG88 / IFOMPT | IFOMPT Cervical Framework / AAOMPT | Evidence-Based Guidelines | `OFFICIAL_STANDARD` |

---

## 4. Maintenance & Contribution Protocol

1. Any future term addition must be entered into `msk_therapy_os/data/medical_terminology_registry.json`.
2. Contributions must include:
   - Canonical `code` (e.g. `WHO:GV14` or `FMA:7111`).
   - `name_en`, `name_zh`, `name_vi`.
   - `provenance` dictionary with `standard_body`, `citation`, and `review_status`.
3. An automated script (`scripts/build_medical_terminology_registry.py`) mirrors changes between backend and frontend runtime directories.
4. CI execution (`prototype/test_multilingual_i18n.py`) automatically asserts that no Unicode replacement characters (`U+FFFD`) or unmapped identifier fallbacks appear in production rendering.
