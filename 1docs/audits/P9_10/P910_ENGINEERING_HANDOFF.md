# P9.10 Engineering Handoff & Technical Transition Document

**Milestone:** P9.10 Independent Anatomical Ground Truth Validation & Performance Acceptance Hardening  
**Target Milestone:** P9.11 Scaled Extremity & Paraspinal Anatomical Calibration  
**Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Date:** 2026-10-28  
**Author:** Principal Computational Anatomy Engineer, Senior Systems Architect, & Independent Evidence Auditor  
**Status:** COMPLETE, AUDITED, AND READY FOR HANDOFF

---

## 1. Milestone Overview & Objectives Achieved

In Milestone P9.10, we conducted an independent, forensic audit of the distal limb anatomical improvements introduced in P9.9. Rather than adding more Class B points prematurely, P9.10 hardened the evidence base, audited mathematical algorithms, investigated performance anomalies, and established unassailable clinical governance.

### Core Deliverables Completed:
1. **P9.9 Baseline Reconciliation:** Verified bitwise exact matches on canonical datasets (`acupuncture_3d.json` and `fj2810_softened.bin`), and verified the catalog distribution of 18 Class A (5.0%), 126 Class B (34.8%), 0 Class C (0.0%), and 218 Class D (60.2%).
2. **13-Point Forensic Validation:** Independently audited SP2–SP5, KI1–KI6, LU9, HT7, PC7 without self-reference. Evaluated tendon versus crease boundaries and classified all 13 points as `QUALIFIED` for non-invasive reference.
3. **Plantar Surface Normal Refinement:** Corrected KI1 normal from P9.9's coarse approximation to the exact BodyParts3D FJ2810 plantar mesh face #29466 normal: Right `[-0.02941, -0.99237, -0.11970]`, Left `[0.02941, -0.99237, -0.11970]`, confirming downward plantar orientation.
4. **Umeyama SVD Mathematical Audit:** Audited pure-Python Jacobi SVD. Added intentional sagittal reflection handling (`allow_reflection=True`), reducing reflection residual from $2.28\text{ mm}$ to $0.015\text{ mm}$. Added condition number $\kappa = \sigma_1 / \sigma_3$ to detect degenerate collinear anchors.
5. **Holdout Independence Clarification:** Forensically established that P9.9's reported $<0.1\text{ mm}$ holdout error represented an **intra-frame spatial consistency check**, NOT an out-of-sample physical cross-modality registration. Formally classified this status as `HOLDOUT_SAME_FRAME_CONSISTENCY`.
6. **Physical GPU Benchmark Restoration ($\ge 30.0\text{ FPS}$):**
   - Uncovered why P9.9 relaxed the test assertion from $\ge 30.0$ to $\ge 25.0\text{ FPS}$: 2,234 draw calls per frame caused thermal power throttling on the 15W TDP Intel Core i7-5600U package.
   - Implemented surface-mode occlusion culling in `msk_therapy_os/static/atlas/app.js` (culling deep occluded non-surface vessels: artery, vein, nervous, organ).
   - Reduced active draw calls from 2,234 to 749 per frame (-66.5%).
   - Reduced GPU draw time from $28.54\text{ ms}$ to $9.04\text{ ms}$ (3.16x speedup).
   - Restored standardized physical acceptance floor to $\ge 30.0\text{ FPS}$. Physical silicon currently achieves **41.0 FPS** (24.41 ms frame time, p95 32.60 ms, raycast 0.001 ms).
7. **Four-Tier Claim Governance Enforced:**
   - Enforced strict separation between Computational Correctness, Geometric Registration, Anatomical Validity, and Clinical Verification.
   - Mandated that the 39.8% metric is strictly labeled **"39.8% Calibrated Coverage"**, NEVER "39.8% Clinically Verified".
   - Formal clinical trial verification is explicitly established as 0 (0.0%).
8. **Class D Prioritization for P9.11:** Delivered `P910_CLASS_D_NEXT_PHASE_PRIORITY.csv` with all 218 Class D points categorized across 4 priority tiers.
9. **Full Regression Execution:** **352 / 352 tests PASS (100.0%)** across 33 unit/integration suites and 3 physical WebGL Playwright benchmark suites.

---

## 2. Directory Structure of Deliverables

All documentation, data, and evidence assets are version-controlled in the repository:

```
1docs/audits/P9_10/
├── P910_BASELINE_FORENSIC_AUDIT.md
├── P910_13_POINT_INDEPENDENT_VALIDATION.csv
├── P910_REGISTRATION_ENGINE_FORENSIC_AUDIT.md
├── P910_GROUND_TRUTH_PROVENANCE_AUDIT.md
├── P910_ANATOMICAL_DEPENDENCY_GRAPH.json
├── P910_CLASSIFICATION_REVALIDATION.csv
├── P910_QUALITY_CLAIM_GOVERNANCE.md
├── P910_PHYSICAL_GPU_COMPARATIVE_BENCHMARK.md
├── P910_PERFORMANCE_REMEDIATION_REPORT.md
├── P910_CLASS_D_NEXT_PHASE_PRIORITY.csv
├── P910_FULL_REGRESSION_REPORT.md
├── P910_EVIDENCE_MANIFEST.json
├── P910_FINAL_ACCEPTANCE_MATRIX.md
└── P910_ENGINEERING_HANDOFF.md

2data/evidence/p9_10_validation/
├── 01_p910_qa_studio_calibrated_governance.png
├── 02_p910_foot_dequarantine_forensic_audit.png
├── 03_p910_ki1_plantar_face_normal_mesh_alignment.png
├── 04_p910_wrist_crease_tendon_dual_layer.png
├── 05_p910_standardized_30fps_intel_hd5500_benchmark.png
└── webgl_p9_10_standardized_benchmark.json

tests/
├── test_p9_10_forensic_validation.py (27 unit & forensic tests)
└── test_p9_10_playwright_benchmark.py (Standardized physical GPU benchmark)
```

---

## 3. Recommended Roadmap for P9.11

The incoming P9.11 engineering team should follow the risk-ranked prioritization established in `P910_CLASS_D_NEXT_PHASE_PRIORITY.csv`:

### Priority 1: High-Feasibility Extremity Elevation (45 Points)
- **Target Channels:** Large Intestine (LI1–LI10), Triple Energizer (TE1–TE10), Small Intestine (SI1–SI10), Stomach crural line (ST31–ST40), Gallbladder crural line (GB34–GB40).
- **Anatomical Substrates:** Radial shaft, ulnar shaft, metacarpal heads/bases, tibial crest, fibular head/shaft.
- **Expected Calibrated Coverage Gain:** Elevation of 45 Class D points to Class B will increase calibrated coverage from **39.8% to 52.2%** (189 / 362 points).

### Priority 2: Axial Midline Spinous Process Calibration (27 Points)
- **Target Channels:** Governing Vessel (GV) and Conception Vessel (CV).
- **Anatomical Substrates:** Spinous processes of C7, T1–T12, L1–L5, sacral hiatus, sternal notches, pubic symphysis.
- **Expected Calibrated Coverage Gain:** Elevation of 27 midline points will increase calibrated coverage from **52.2% to 59.7%** (216 / 362 points).

### Invariants for P9.11:
1. Maintain zero production pip dependencies and zero npm dependencies.
2. Maintain the restored physical GPU acceptance floor ($\ge 30.0\text{ FPS}$) on Intel HD Graphics 5500.
3. Preserve the four-tier semantic governance: never claim rule-derived Class B points as clinically verified.
4. Execute `AnatomicalProvenanceDependencyValidator` on every new landmark to prevent circular loops.
