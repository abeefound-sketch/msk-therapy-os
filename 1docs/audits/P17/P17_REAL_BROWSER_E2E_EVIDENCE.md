# P17 Real Browser Functional Acceptance (Playwright E2E Evidence)

## 1. Test Architecture & Execution Environment

- **Browser Harness**: Playwright 1.50+ on Headless Chromium.
- **Rendering Flags**: `--enable-webgl`, `--ignore-gpu-blocklist`, `--use-gl=angle`, `--use-angle=swiftshader`.
- **Target Resolution**: $1600 \times 960$ (with responsiveness tested at $1824 \times 800$).
- **Test File**: [`test_p17_functional_acceptance_playwright.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p17_functional_acceptance_playwright.py)
- **Execution Result**: `1 passed in 151.76s` (Exit Code 0).

---

## 2. Step-by-Step Functional Acceptance Log

| Step | Tested Interaction | Assertion & Observable Renderer Change | Status | Captured Screenshot |
|---|---|---|---|---|
| **01** | Initial Page Load (`/education/?v=p17`) | Canvas attached; Mode A active; `#muscle-recruitment-list` hidden (`display: none`); 4+ muscle cards rendered | PASS | `01_default_anatomical_viewer.png` |
| **02** | Mode A Muscle Selection | First card clicked; receives `.active` gold border; `window.anatomyViewer.selectedMeshName` set to muscle ID; 3D mesh illuminates in gold (#facc15) | PASS | `02_mode_a_anatomical_response.png` |
| **03** | Mode B Geometric Change | `#btn-mode-geometry` clicked; `#inspector-empty-state` contains `MODEL_GEOMETRY_INSUFFICIENT`; list remains hidden; literature $L_0$ metrics shown | PASS | `03_mode_b_geometric_change.png` |
| **04** | Mode C Estimated Activation | `#btn-mode-activation` clicked; watermark banner displayed; `#muscle-recruitment-list` visible; timeline scrubbed to 1.0s; bars update dynamically | PASS | `04_mode_c_model_activation.png` |
| **05** | Mode D Estimated Force | `#btn-mode-force` clicked; `#inspector-empty-state` contains `MUSCLE_FORCE_NOT_AVAILABLE`; percentage bars hidden (no invented force numbers) | PASS | `05_mode_d_estimated_force_unavailable.png` |
| **06** | Kinematic Playback Controls | Speed set to 0.5x (`.active`); Play starts timeline progression; Pause freezes time; Reset rewinds time label to `0.00 s / 2.00 s` | PASS | `06_playback_timeline_scrubbing.png` |
| **07** | Posture Simulator & ROM | Slider adjusted to 85%; label reads `85%`; scenario switched to `cervical_axial_rotation`; kinematic readouts and transforms update | PASS | `07_rom_cervical_movement.png` |
| **08** | Scenario Comparison Tool | `#btn-mode-comparison` clicked; dialog displays $\Delta$ moment arm (+cm), $\Delta$ moment (+N·m), $\Delta$ extensor load (+N); Close hides card | PASS | `08_scenario_comparison.png` |
| **09** | Curriculum Navigation | Stage 3 clicked; `#stage-title` and `#stage-summary` update to Forward-Head Posture; 3D scene reorients to cervical sagittal profile | PASS | `09_curriculum_module_switching.png` |
| **10** | Camera Views & Language Toggle | Lateral view ($X > 0.3$), Posterior view ($Z < -0.3$), Anterior view ($Z > 0.3$) verified; Language toggles between Vietnamese and English | PASS | `10_final_desktop_layout.png` |

---

## 3. Playwright Screenshot Manifest

All 10 authoritative screenshots plus baseline reproduction are persisted in `1docs/audits/P17/screenshots/`:
1. `00_baseline_reproduction.png` (174.5 KB)
2. `01_default_anatomical_viewer.png` (203.6 KB)
3. `02_mode_a_anatomical_response.png` (215.7 KB)
4. `03_mode_b_geometric_change.png` (220.3 KB)
5. `04_mode_c_model_activation.png` (219.1 KB)
6. `05_mode_d_estimated_force_unavailable.png` (228.3 KB)
7. `06_playback_timeline_scrubbing.png` (229.2 KB)
8. `07_rom_cervical_movement.png` (228.8 KB)
9. `08_scenario_comparison.png` (227.1 KB)
10. `09_curriculum_module_switching.png` (202.3 KB)
11. `10_final_desktop_layout.png` (202.3 KB)
