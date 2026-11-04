# MSK-Therapy-OS: Remaining Blockers & Prioritized Engineering Roadmap

**Audit Date:** November 5, 2026  
**Auditor Classification:** Principal Software Architect & Verification Lead  

---

## 1. Blocker Priority Matrix

| Priority | Issue ID | Title | Technical Impact | Prerequisite for Release? | Recommended Action |
|:---:|:---:|:---|:---|:---:|:---|
| **P0** | — | **Zero Remaining P0 Blockers** | All P0 audit integrity findings (secret leakage, unverifiable tests, node discrepancies) are resolved. | **RESOLVED** | Maintain deny-by-default export filters. |
| **P1** | **BLK-001** | Full-Body WebGL LOD Progressive Streaming | The 19.4 MB uncompressed GLB asset creates a 3.5s main-thread blocking time during initial WebGL buffer upload on Intel HD 5500 GPUs. | Highly Recommended for Web Deployment | Implement Draco/Meshopt compression and 3-level progressive LOD (LOD0: 15k, LOD1: 45k, LOD2: 120k triangles). |
| **P1** | **BLK-002** | Dual Quaternion Skinning (DQS) Shader | Linear Blend Skinning (LBS) exhibits volume pinching ("candy-wrapper" artifact) at acute joint angles (>100° elbow/knee flexion). | Recommended for Biomechanical Accuracy | Implement DQS vertex shader with GPU bone transform dual quaternions to preserve muscle volume during deep flexion. |
| **P2** | **BLK-003** | Offline Standard-Library PDF Report Generator | System currently exports Markdown and HTML reports; lacks native offline PDF generation for clinical referral letters without external wkhtmltopdf/weasyprint dependencies. | Nice-to-Have (Clinical Workflow) | Implement lightweight pure-Python PDF generator or browser-native `window.print()` CSS print media styles. |
| **P2** | **BLK-004** | Multi-Center In-Vivo Hospital Clinical Trials | Software simulation models (BodyParts3D/WHO 2008) lack empirical validation against live human patient ultrasound/CT/MRI scans. | Required ONLY for Autonomous Clinical Diagnosis | Establish hospital IRB partnership to collect de-identified in-vivo needle placement imaging data. |

---

## 2. Explicit Regulatory & Clinical Boundary

MSK-Therapy-OS is strictly an **educational and computational biomechanics documentation platform**. It is NOT certified as a medical device (SaMD) under US FDA 510(k) or EU MDR regulations. Autonomous diagnostic, surgical, or invasive therapeutic needle guidance is strictly locked and prohibited by software safety invariants.
