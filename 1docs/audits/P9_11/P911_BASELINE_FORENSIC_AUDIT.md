# P9.11 Baseline Forensic Audit & Preflight Verification

**Milestone:** P9.11 Anatomical Ground-Truth Validation & Class D Remediation  
**Predecessor Milestone:** P9.10 Independent Anatomical Ground Truth Validation & Performance Acceptance Hardening  
**Lead Auditor:** Principal Computational Anatomy Engineer & Independent Scientific Auditor  
**Date:** 2026-10-28  
**Repository Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Host Environment:** Windows 10 Pro 64-bit | Python 3.11.9 | Intel(R) Core(TM) i7-5600U @ 2.60GHz | Intel(R) HD Graphics 5500 (D3D11 via ANGLE)  
**Status:** FULLY RECONCILED & REPRODUCED

---

## 1. Executive Summary

Prior to initiating any algorithmic modifications or coordinate calibrations for Milestone P9.11, a comprehensive forensic preflight audit was conducted to verify all claims made by predecessor Milestone P9.10. 

All reported baseline metrics were independently reproduced from runtime SQLite database queries, spatial geometry evaluations, cryptographic hashes, and physical GPU automated Playwright executions.

---

## 2. Canonical Dataset & Mesh Hash Invariants

The canonical BodyParts3D 4.0 polygonal surface mesh and WHO standard acupuncture dataset were verified using SHA256 cryptographic checksums:

| Asset Description | Repository File Path | Expected SHA256 Hash | Runtime Verified SHA256 | Integrity Status |
|---|---|---|---|:---:|
| **Canonical Acupuncture JSON** | `msk_therapy_os/static/atlas/data/acupuncture_3d.json` | `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df` | `47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df` | **BITWISE EXACT** |
| **Canonical Softened Mesh** | `2data/artifacts/fj2810_softened.bin` | `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808` | `05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808` | **BITWISE EXACT** |

Both authoritative assets remain unmodified and intact.

---

## 3. Catalog Distribution Baseline Reconciliation

Authoritative distribution across all 362 acupoints in the canonical atlas:

| Quality Class | Semantic Definition | P9.10 Reported | P9.11 Reconciled | Discrepancy |
|---|---|---:|---:|:---:|
| **Class A** | Independently Audited Canonical Ground Truth Anchors | 18 | 18 | 0 |
| **Class B** | WHO 2008 Standard Parametric Rule-Derived Points | 126 | 126 | 0 |
| **Class C** | Deprecated / Ambiguous Geometric Points | 0 | 0 | 0 |
| **Class D** | Uncalibrated Legacy Surface Raycasts (Target for Remediation)| 218 | 218 | 0 |
| **Class A+B** | **Combined Calibrated Coverage** | **144 (39.8%)** | **144 (39.8%)** | **0.0%** |
| **Tier 4** | **Formal Clinical Trial / Practitioner Verification** | **0 (0.0%)** | **0 (0.0%)** | **0.0%** |
| **TOTAL** | Authoritative Meridian Acupoint Catalog | **362** | **362** | **0** |

---

## 4. Hardware & Regression Baseline Reproduction

1. **Unit & Integration Regression Suite:**
   - 349 non-playwright tests executed: **349 / 349 PASS (100.0%)** in 118.47s.
   - Milestone verification suites P9.5 through P9.10: all passed cleanly.
2. **Physical GPU Hardware Benchmark on Intel HD Graphics 5500:**
   - Standardized physical execution via Playwright Chromium D3D11 / ANGLE:
     - Average FPS: **41.0 FPS** (Target floor: $\ge 30.0\text{ FPS}$)
     - P95 Frame Time: **32.60 ms** (Target ceiling: $\le 33.33\text{ ms}$)
     - Raycasting Latency: **0.001 ms** (Target ceiling: $\le 5.0\text{ ms}$)
     - WebGL Context Loss Events: **0**
     - Console / Page Exceptions: **0**
3. **Dependency Graph & Circularity Audit:**
   - Evaluated using `AnatomicalProvenanceDependencyValidator`.
   - 74 registered canonical landmarks; 0 undisclosed circular references; 0 quarantined circular references.

---

## 5. Preflight Conclusion & Authorization

The P9.10 baseline has been independently verified and proven stable. Phase A (Independent Ground-Truth Audit) is formally authorized to proceed.
