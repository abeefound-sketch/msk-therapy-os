# MSK-Therapy-OS — Milestone P18 Forensic Audit
## External Reference Licenses, Intellectual Property & Attribution Register

**Document ID:** `MSK-P18-ERL-004`  
**Classification:** `ENGINEERING_RESEARCH_ONLY`  
**Baseline Commit:** `877450c`  
**Remediation Branch:** `fix/p18-meridian-anatomical-geometry`  

---

### 1. Intellectual Property & Academic Fair Use Overview

MSK-Therapy-OS integrates and references geometric, anatomical, and research data from upstream open-science projects. Under Milestone P18 governance, all external datasets, meshes, code libraries, and clinical standards must be fully documented with their exact licenses, upstream commit hashes, and attribution requirements.

The software is strictly classified as **`ENGINEERING_RESEARCH_ONLY`** and is not licensed or marketed as a medical device.

---

### 2. Comprehensive Upstream License Register

#### 2.1 BodyParts3D (DBCLS / RIKEN)
- **Asset Referenced:** BodyParts3D 4.0 polygonal surface meshes (`FJ2810` skin mesh, anatomical part chunks `body-0.bin` through `body-14.bin`).
- **Original Licensors:** Database Center for Life Science (DBCLS), University of Tokyo / Research Organization of Information and Systems (ROIS), RIKEN.
- **License:** Creative Commons Attribution-ShareAlike 2.1 Japan (CC BY-SA 2.1 JP) / Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Attribution Statement:**
  > *"BodyParts3D, © The Database Center for Life Science licensed under CC Attribution-Share Alike 2.1 Japan."*
- **Terms Compliance:**
  - Derivative mesh `fj2810_softened.bin` is distributed with source attribution.
  - No commercial trademarks are claimed.

#### 2.2 JICio / `tcm-3d`
- **Asset Referenced:** WebGL 3D Traditional Chinese Medicine & Meridian Visualizer codebase and pre-baked surface registrations.
- **Author:** JICio (`https://github.com/JICio/tcm-3d`)
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Terms Compliance:**
  - Preserved license notices in `3refs/upstream/tcm-3d/LICENSE` and `ATTRIBUTION.md`.
  - Disclosed modifications and algorithmic extensions in `meridian_surface_engine.py`.

#### 2.3 WaterCMY / `tcm-acupoints`
- **Asset Referenced:** Upstream TypeScript acupoint catalog and mannequin viewer (`tcm-acupoints`).
- **Author:** WaterCMY (`https://github.com/WaterCMY/tcm-acupoints`)
- **License:** MIT License.
- **Terms Compliance:**
  - Full license preserved in `3refs/upstream/tcm-acupoints/LICENSE`.
  - Upstream raw mode strictly documented; synthetic offsets eliminated.

#### 2.4 Z-Anatomy
- **Asset Referenced:** Open anatomical concept structures and atlas hierarchy referencing the Foundational Model of Anatomy (FMA).
- **Licensor:** Z-Anatomy Project
- **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
- **Terms Compliance:**
  - Standard FMA concept IDs used for non-invasive educational referencing.

#### 2.5 WHO Standard Acupuncture Point Locations (2008)
- **Reference Standard:** *WHO Standard Acupuncture Point Locations in the Western Pacific Region*, World Health Organization Western Pacific Regional Office, Manila, 2008.
- **Status:** International Public Health Standard / Academic Reference Document.
- **Usage:** Reference nomenclature (WHO alphanumeric codes), anatomical boundary landmarks, and B-cun proportional segment definitions.
- **Disclaimer:** Citations are non-commercial educational references; the World Health Organization does not endorse or certify this software application.

---

### 3. Verification & Offline-First Attestation

1. **Zero Dynamic External Dependencies:** The application does not fetch scripts, fonts, stylesheets, or binary assets from remote CDNs or external servers. All assets are served locally from `msk_therapy_os/static/`.
2. **Offline Network Isolation:** Verified under test suite assertion `G14 = BLOCKED_EXTERNAL_DATA`.
3. **No Clinical Warranty:** The software is provided "as is", without warranty of any kind, express or implied, including fitness for a surgical or invasive medical purpose.
