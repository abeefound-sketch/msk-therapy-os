# P17 Baseline Reproduction & User Failure Forensic Audit

## 1. Baseline Verification

- **Repository Path**: `D:\5Projects\msk-therapy-os`
- **Baseline Git Branch**: `feat/p16-scientific-biomechanics-integrity-studio`
- **Baseline Commit**: `896a3f5` (1-click standalone launcher and desktop shortcut for MSK Education Studio)
- **Repair Branch**: `feat/p17-real-functional-acceptance`
- **Target Hardware**: Intel Core i7-5600U, 8 GB RAM, Intel HD Graphics 5500
- **Release Classification**: `ENGINEERING_RESEARCH_ONLY`
- **Invariant Flags**:
  - `G14 = BLOCKED_EXTERNAL_DATA`
  - `clinical_depth_guidance_allowed = False`
  - `CLINICAL_VALIDATION = NOT_ESTABLISHED`
  - `ZERO_DECEPTIVE_CONTROLS = REQUIRED`

---

## 2. User-Reported Failure Reproduction

### Observed Symptoms Reported by User
1. Modes A, B, C, and D appear visually identical when clicked.
2. Multiple buttons appear to exist without performing meaningful actions.
3. The anatomical model occupies a small portion of the 3D viewport; camera framing is off-center.
4. Controls crowd the lower part of the 3D area, obscuring the anatomy.
5. Biomechanical indicators such as `8.0°` and `54/100` lack calculation provenance.

### Forensic Reproduction Findings
A headless browser session captured the baseline state to `1docs/audits/P17/screenshots/00_baseline_reproduction.png`:
- In `msk_therapy_os/static/education/index.html`, `#muscle-recruitment-list` was statically visible on page load with hardcoded percentages (`Deltoid: 45%`, `Supraspinatus: 62%`, `Levator: 22%`, `Suboccipitals: 18%`).
- In `shoulder_lab.js`, switching modes between A, B, C, and D never hid `#muscle-recruitment-list`. The user observed the exact same numbers regardless of clicked mode.
- In `anatomy_viewer.js`, `setVisualMode(mode)` only checked for `ANATOMICAL_FUNCTION` (which reset highlights) and `MODEL_ESTIMATED`. It did not recognize `MODE_A_ANATOMICAL_PARTICIPATION`, `MODE_B_GEOMETRIC_CHANGE`, or `MODE_D_ESTIMATED_FORCE`. Thus, Modes A, B, and D all cleared highlights to default terracotta bone color.
- In `index.html`, `skeletonUrl` was hardcoded to `shoulder_skeleton.glb` rather than `cervicothoracic_skeleton.glb`. When loading cervical or unified scenarios, cervical vertebrae and cranium were absent from the scene graph.
- The default camera position was fixed at `(-0.25, 1.48, 1.05)` looking at `(-0.10, 1.38, -0.02)` (focused on the right shoulder). For upper body and cervical viewing, the model was shifted and appeared small and distant.
- The floating player bar had excessive padding and large vertical height (~130px), crowding out the bottom 30% of the viewport.

---

## 3. Reproduction Verdict

**USER FAILURE REPRODUCED & CONFIRMED**: The visual identity between Modes A, B, C, and D was caused by decoupled UI state in `shoulder_lab.js`, unrecognized mode strings in `anatomy_viewer.js`, and a permanent static `#muscle-recruitment-list` DOM element that failed to toggle with mode changes.
