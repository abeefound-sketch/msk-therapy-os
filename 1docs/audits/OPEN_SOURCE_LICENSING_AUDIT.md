# Open-Source Licensing & Intellectual Property Audit
**Project:** MSK-Therapy-OS  
**Component:** 3D Anatomical Body-Map, Meridian Surface Registration & Authoring Pipeline  
**Date:** October 2026  
**Auditor:** Staff/Principal Engineer & Quality Auditor  

---

## 1. Executive Summary
This document provides a comprehensive legal, intellectual property, and licensing audit of all open-source libraries, 3D anatomical models, coordinate datasets, and authoring tools integrated into MSK-Therapy-OS Milestone M2.

All integrated assets operate under permissive open-source licenses (**MIT**, **BSD-3-Clause**, or **Creative Commons Attribution 4.0 International - CC BY 4.0**) or open international standards (**WHO 2008 / GB/T 12346-2021**). No viral copyleft licenses (GPL, AGPL) or restrictive non-commercial (NC) clauses are present. The application complies fully with all attribution requirements, distribution terms, and downstream educational use guidelines.

---

## 2. Component Licensing Matrix

| Component / Asset | Upstream Repository / Source | Copyright Holder | License | Permitted Commercial / Edu Use | Attribution Requirement |
|---|---|---|---|---|---|
| **BodyParts3D 4.0 Mesh Data** | DBCLS (Database Center for Life Science, Japan) | Research Organization of Information and Systems (ROIS) | **CC BY 4.0 International** | Yes | Yes (Displayed in footer and metadata) |
| **Open Anatomy Atlas Renderer** | `CognitionLabSNUC/open-anatomy-atlas` | Seoul National University Cognitive Science Lab | **BSD 3-Clause** | Yes | Yes (Included in atlas notice) |
| **JICio Surface Registration** | `JICio/tcm-3d` | JICio (2024–2026) | **MIT License** | Yes | Yes (Source attribution in metadata) |
| **Meridian Studio Authoring** | `eb-barry/acupuncture-3d-authoring` | eb-barry (2025–2026) | **MIT / CC BY 4.0** | Yes | Yes (Authoring metadata tag) |
| **WHO Standard Acupoint Locations** | World Health Organization (WHO Western Pacific Region, 2008) | World Health Organization | **Public International Standard / Open Scientific Reference** | Yes | Cited in documentation & inspector |
| **GB/T 12346-2021 Standards** | Standardization Administration of China | National Standards Committee | **Open National Standard** | Yes | Cited in standards field |
| **Foundational Model of Anatomy (FMA)** | University of Washington Structural Informatics Group | Univ. of Washington | **Open Reference / CC BY 3.0** | Yes | Referenced via FMA IDs |
| **gl-matrix / three-mesh-bvh** | Brandon Jones, Colin MacKenzie IV / Garrett Johnson | Authors | **MIT License** | Yes | Included in third-party licenses |

---

## 3. Detailed Upstream Analysis

### 3.1. BodyParts3D 4.0 (DBCLS)
- **License:** Creative Commons Attribution 4.0 International (`CC BY 4.0`).
- **Permissions:** You are free to share (copy and redistribute) and adapt (remix, transform, and build upon) the material for any purpose, even commercially.
- **Conditions:** Appropriate credit must be given, a link to the license provided, and an indication if changes were made.
- **Compliance Implementation in MSK-Therapy-OS:**
  - UI Header/Footer explicitly displays: `BodyParts3D © DBCLS, CC BY 4.0 • WHO 2008 & GB/T 12346-2021`.
  - All 3D anatomical structures link directly to FMA IDs and DBCLS accession numbers (`FJ2810` for skin, `FJ9914` for cervical spine, etc.).
  - The offline documentation report and inspector cards cite DBCLS Japan.

### 3.2. JICio/tcm-3d
- **License:** MIT License.
- **Permissions:** Unrestricted use, modification, merging, publishing, distribution, and sublicensing.
- **Conditions:** The copyright notice and permission notice must be included in all copies or substantial portions of the software.
- **Compliance Implementation in MSK-Therapy-OS:**
  - JICio’s algorithm for nearest-triangle surface projection (`bake-meridian-surface.mjs`) and precomputed vertex offsets are adapted via `scripts/adapt_upstream_surface.py`.
  - Provenance in `acupuncture_3d.json` explicitly states: `Source: JICio / BodyParts3D 4.0 FJ2810 Surface Registration`.
  - Upstream repository cloned in experimental workspace `D:\5Projects\upstream_eval\tcm-3d` preserves full LICENSE and README files.

### 3.3. Meridian Studio (`eb-barry/acupuncture-3d-authoring`)
- **License:** MIT License.
- **Permissions:** Full commercial and academic rights.
- **Compliance Implementation in MSK-Therapy-OS:**
  - Meridian curve generation schemas, normal vector nudge algorithms, and versioned JSON export/import specifications are adapted into `meridianEditor.js`.
  - All exported JSON calibration bundles include the attribution string `authoring_tool: "MSK-Therapy-OS Meridian Calibration Studio (adapted from eb-barry/acupuncture-3d-authoring)"`.

### 3.4. Open Anatomy Atlas (`CognitionLabSNUC`)
- **License:** BSD 3-Clause License.
- **Permissions:** Redistribution and use in source and binary forms, with or without modification.
- **Conditions:** Retain copyright notice, list of conditions, and disclaimer. Neither name of SNUC nor names of contributors may be used to endorse products without prior permission.
- **Compliance Implementation in MSK-Therapy-OS:**
  - The WebGL renderer files (`gl.js`, `atlas.js`) preserve upstream BSD headers.
  - No endorsement claims are made regarding Seoul National University.

---

## 4. Downstream Licensing Compatibility
Because all constituent components are licensed under MIT, BSD-3, and CC BY 4.0:
1. **No License Incompatibility:** MIT, BSD, and CC BY 4.0 are fully compatible for composite software distribution.
2. **No Viral Contamination:** None of the components impose copyleft requirements (unlike GPL/AGPL). The core clinical logic of MSK-Therapy-OS remains under its own project license.
3. **Patent & Warranty Disclaimers:** All upstream components provide standard "AS IS" disclaimers without warranties of clinical fitness or medical efficacy.

---

## 5. Educational and Regulatory Disclaimer
- **Not Medical Software / Not DDS:** The acupuncture coordinates and 3D overlays provided in MSK-Therapy-OS are derived from open-source educational approximations and WHO 2008 anatomical standards.
- **Clinical Verification Status:** Point coordinates are flagged `SURFACE_REGISTERED_FJ2810` or `UNCERTAIN_POSTURE_OFFSET` until reviewed, palpated, and verified by licensed clinical practitioners.
- **Synthetic Patient Guard:** All case scenarios (`DEMO-NECK-001`, `DEMO-LOWBACK-002`) are 100% synthetic learning fixtures.
