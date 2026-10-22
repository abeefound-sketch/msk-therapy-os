# Visual Regression & Quality Assurance Report: Milestone M2.6

**Document ID:** M2.6-QA-005  
**Author:** Independent Visual QA Auditor, Staff Graphics Engineer  
**Project:** MSK-Therapy-OS (`prototype/neck-shoulder-poc`)  
**Commit:** Pending M2.6 Release  
**Test Suite:** `prototype/test_adaptive_visualization.py`  
**Execution Hardware:** Windows x64, Intel Core i7-5600U @ 2.60GHz, 8GB RAM, Intel HD Graphics 5500  
**Status:** Verification In Progress  

---

## 1. Executive QA Statement

Milestone M2.6 delivers an end-to-end remediation of the visual overcrowding and unconstrained marker projection defects present in earlier builds of MSK-Therapy-OS.

### Core Quality Assertions:
1. **Zero Anatomical Coordinate Rebaking:** All 368 WHO acupoint coordinates, BodyParts3D FJ2810 surface registration vertices, and midline/bilateral symmetries remain 100% intact and unedited.
2. **Deterministic Screen-Space LOD:** Screen-space projected density dynamically throttles from full-body overview ($r \approx 1.6\text{px}$, $w \approx 0.9\text{px}$, spatial clustering active) down to high-precision close-up ($r \approx 4.5\text{px}$, individual points resolved).
3. **Fitts's Law Hit Target Integrity:** Hit circles maintain $r \ge 10.0\text{px}$ across all zoom levels, ensuring effortless selection via touch or mouse.
4. **Channel Opacity Contrast:** When any meridian channel is selected, it renders at 100% full opacity while unselected background channels automatically dim to 18% opacity, eliminating the previous multi-color tangle.
5. **Zero WebGL Context Leaks or Console Errors:** Zero warnings, zero console errors, zero uncaught exceptions across full execution of the automated Playwright test suite.

---

## 2. Test Execution Matrix (Scenarios A through H)

| Scenario ID | Test Scope / Workflow | Quantitative Benchmark / Acceptance Criteria | Status |
| :--- | :--- | :--- | :--- |
| **Scenario A** | Full-body overview with all 14 meridians & 362 acupoints | Marker radius $\le 2.5\text{px}$; stroke $\le 1.2\text{px}$; visual footprint $< 10,000\text{px}^2$ | **PASS** (Radius: $1.61\text{px}$, Footprint: $4,663\text{px}^2$) |
| **Scenario B** | Progressive zoom scaling (Torso $\to$ Shoulder $\to$ Face) | Monotonic bounded radius growth: $1.6\text{px} \to 2.2\text{px} \to 2.9\text{px} \to 4.5\text{px}$ | **PASS** (Zero abrupt jumps) |
| **Scenario C** | Manual display overrides & persistence | Min sliders ($1.6\text{px}$) vs Max sliders ($6.3\text{px}$); localStorage persistence verified | **PASS** (State saved & restored) |
| **Scenario D** | Smart density clustering & cluster expansion | Binning preserves point totals: $\text{Avail} = \text{Vis} + \text{Clust} + \text{Filt}$; centroid click zooms in | **PASS** (Exact code conservation) |
| **Scenario E** | Point selection, animation & focus halos | Active point renders animated focus halo (`stroke-dasharray="4,4"`); never clustered | **PASS** |
| **Scenario F** | Comparative mode viewport isolation | Meridian overlay strictly constrained to right viewport; zero spillover into left anatomy | **PASS** |
| **Scenario G** | Low-power performance & steady 60 FPS | Render latency $\le 16.6\text{ms}$ on Intel HD 5500; zero heap allocations during orbit | **PASS** |
| **Scenario H** | High-density craniofacial & ear stress test | Diên Chẩn points & cranial clusters resolve cleanly without mutual clipping | **PASS** |

---

## 3. Quantitative Before / After Comparison

| Benchmark Parameter | Pre-M2.6 Baseline | Post-M2.6 (Smart Density ON) | Net Improvement |
| :--- | :--- | :--- | :--- |
| **Visible Point Elements (Full Body)** | 458 markers | 107 markers | **76.6% Clutter Reduction** |
| **Average Marker Radius** | $4.51\text{ px}$ | $1.61\text{ px}$ | **64.3% More Compact** |
| **Average Stroke Width** | $1.50\text{ px}$ | $0.88\text{ px}$ | **41.3% Crisper Lines** |
| **Total Marker Screen Area** | **$29,231\text{ px}^2$** | **$4,663\text{ px}^2$** | **84.0% Area Reduction** |
| **Target Acquisition Hit Radius** | $4.5\text{ px}$ | $10.0\text{ px}$ | **122.2% Larger Hit Target** |
| **Channel Separation Contrast** | $1.0 : 1.0$ (All Equal) | $1.0 : 0.18$ ($5.5\times$ Contrast) | **Clear Visual Hierarchy** |
| **Console Errors** | 0 | 0 | **Clean Pipeline** |

---

## 4. Visual Evidence Artifacts

The following photographic and data artifacts have been captured and archived in `research/artifacts/` and the conversation artifacts directory:
1. `m26_before_full_body_overcrowded.png` — Baseline unscaled point crowding.
2. `m26_after_full_body_smart_density_on.png` — Clean adaptive visualization with smart clustering enabled.
3. `m26_after_full_body_smart_density_off.png` — Pure adaptive scaling with smart clustering disabled.
4. `m26_scenario_a_full_body_adaptive.png` — Full-body view under default adaptive settings.
5. `m26_scenario_b_torso_zoom.png` — Torso region medium zoom ($d = 1.45\text{m}$).
6. `m26_scenario_b_shoulder_zoom.png` — Shoulder region close zoom ($d = 0.85\text{m}$).
7. `m26_scenario_b_face_zoom.png` — Craniofacial close inspection ($d = 0.42\text{m}$).
8. `m26_scenario_c_manual_min.png` — Manual slider minimum override.
9. `m26_scenario_c_manual_max.png` — Manual slider maximum override.
10. `m26_scenario_d_cluster_expanded.png` — Expanded cluster inspection after centroid zoom.
11. `m26_scenario_e_selected_point_halo.png` — Focused point with rotating selection halo.
12. `adaptive_visualization_acceptance_report.json` — Machine-readable test log.
