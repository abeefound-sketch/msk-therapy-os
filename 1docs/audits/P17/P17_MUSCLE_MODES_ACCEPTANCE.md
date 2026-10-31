# P17 Muscle Mechanics Modes Acceptance & Verification Audit

## 1. Compliance Standard

Under Acceptance Principle P17-03:
- **Modes A, B, C, and D must be visibly and behaviorally distinct.**
- **No fabricated muscle activation or force data.**
- **Supported modes produce real, data-driven effects on both the DOM and WebGL canvas.**
- **Unsupported modes display unambiguous unavailable states identifying missing prerequisites.**

---

## 2. Mode A — Anatomical Participation

### Purpose
Explains which muscles are anatomically capable of contributing to a selected movement without inventing simulated percentage bars.

### Implementation Details
- **Endpoint**: `/api/education/muscle-mechanics?region={region}&scenario_id={scen}&mode=MODE_A_ANATOMICAL_PARTICIPATION&time={t}`
- **DOM State**: `#muscle-recruitment-list` is hidden (`display: none`). `#watermark-activation-banner` displays:
  `ANATOMICAL FUNCTION & PARTICIPATION — NOT INVENTED ACTIVATION`
- **Interactive Cards**: Renders `.interactive-muscle-card` elements in `#inspector-details-container`, categorizing muscles by anatomical role:
  - **Agonists (Chủ vận)**: Border sky blue (`#38bdf8`), badge `.badge-cyan`.
  - **Synergists (Đồng vận)**: Border amber (`#f59e0b`), badge `.badge-amber`.
  - **Stabilizers (Ổn định)**: Border purple (`#a855f7`), badge `.badge-neutral`.
- **3D Renderer Response**:
  - Agonist meshes colored sky blue (`#38bdf8`, opacity 0.95).
  - Synergist meshes colored amber (`#f59e0b`, opacity 0.90).
  - Stabilizer meshes colored purple (`#a855f7`, opacity 0.88).
  - Non-participating muscles dimmed (opacity 0.20).
- **Interactive Muscle Focus**: Clicking any muscle card isolates and illuminates that muscle in bright gold (`#facc15`, opacity 1.0) and adjusts OrbitControls target towards its bounding box center.
- **Verification Evidence**: `1docs/audits/P17/screenshots/02_mode_a_anatomical_response.png`. Verified in `tests/test_p17_functional_acceptance_playwright.py` Step 1-2.

---

## 3. Mode B — Geometric Muscle Change

### Purpose
Examines changes in muscle-tendon length or geometry during movement.

### Forensic Geometry Evaluation
- Articulated skeletal hierarchy: Present (9 joints).
- Muscle origin/insertion points: Defined in static catalog.
- Continuous 3D line-of-action wrapping curves: **MISSING / UNMESHED** in rigid osseous surface geometry.

### Implementation Details
- **Status Code**: `MODEL_GEOMETRY_INSUFFICIENT`
- **DOM State**: `#muscle-recruitment-list` is hidden (`display: none`).
- **Empty State Notice**:
  `THIẾU ĐƯỜNG DẪN HÌNH HỌC (MODEL_GEOMETRY_INSUFFICIENT): Mô hình bề mặt xương cứng hiện tại chưa phân đoạn đường bao bọc sợi cơ 3D liên tục (musculotendon wrapping curves).`
- **Literature Reference Data**: Instead of generic shrinking, displays empirical static resting fiber lengths ($L_0$) and reference moment arms ($r$) from literature (Vasavada et al. 1998; Seth et al. 2019):
  - Trapezius Upper: $L_0 = 19.8\text{ cm}$, $r = 3.5\text{ cm}$
  - Levator Scapulae: $L_0 = 13.5\text{ cm}$, $r = 3.2\text{ cm}$
  - Sternocleidomastoid: $L_0 = 16.2\text{ cm}$, $r = 4.1\text{ cm}$
  - Suboccipitals: $L_0 = 4.2\text{ cm}$, $r = 2.8\text{ cm}$
- **3D Renderer Response**: Dimmed muscle meshes (opacity 0.22) with fully opaque bones (`#e2e8f0`) to emphasize articulated joint rotation angles without deceptive fiber deformation.
- **Verification Evidence**: `1docs/audits/P17/screenshots/03_mode_b_geometric_change.png`. Verified in `tests/test_p17_functional_acceptance_playwright.py` Step 3.

---

## 4. Mode C — Model-Estimated Muscle Activation

### Purpose
Visualizes time-dependent muscle activations derived from OpenSim Static Optimization (`.sto`) simulation outputs.

### Implementation Details
- **Watermark Banner**: `MATHEMATICAL MODEL ESTIMATE — NOT MEASURED EMG`
- **DOM State**: `#muscle-recruitment-list` is visible (`display: block`). Each bar shows percentage fill corresponding to normalized activation ($a \in [0.0, 1.0]$).
- **Data Provenance**: Explicit notice that values solve inverse dynamic moment equilibrium and do not constitute measured surface electromyography (EMG) or maximum voluntary contraction (MVC).
- **3D Renderer Response**:
  - Color ramp: Blue ($a = 0.0$) $\to$ Yellow ($a = 0.5$) $\to$ Red ($a = 1.0$).
  - Interpolated in real time at `currentTime` from `.sto` timestamps during playback and timeline scrubbing.
- **Graceful Fallback**: If a scenario lacks `.sto` data (e.g. `illustrative_rounded_elevation`), the list is hidden and `#inspector-empty-state` displays `MUSCLE_ACTIVATION_NOT_AVAILABLE`.
- **Verification Evidence**: `1docs/audits/P17/screenshots/04_mode_c_model_activation.png`. Verified in `tests/test_p17_functional_acceptance_playwright.py` Step 4.

---

## 5. Mode D — Estimated Muscle Force

### Purpose
Investigates individual muscle forces in Newtons ($N$).

### Scientific Assessment
Calculating individual muscle forces in Newtons requires dynamic equilibrium solving with physiological cross-sectional area (PCSA), active/passive force-length-velocity curves, and pennation angles. Dynamic equilibrium solving is blocked offline.
**Strict prohibition**: Multiplying normalized activation by an arbitrary scalar constant is scientifically deceptive and prohibited.

### Implementation Details
- **Status Code**: `MUSCLE_FORCE_NOT_AVAILABLE`
- **DOM State**: `#muscle-recruitment-list` is hidden (`display: none`).
- **Empty State Notice**:
  `CHƯA CÓ LỰC CƠ (MUSCLE_FORCE_NOT_AVAILABLE): Tính toán lực cơ theo đơn vị Newton đòi hỏi giải cân bằng động học OpenSim runtime (bị khóa ngoại tuyến). Tuyệt đối không nhân kích hoạt với hằng số tùy ý.`
- **3D Renderer Response**: Meshes reset to neutral terracotta tone (opacity 0.45); zero active highlights.
- **Verification Evidence**: `1docs/audits/P17/screenshots/05_mode_d_estimated_force_unavailable.png`. Verified in `tests/test_p17_functional_acceptance_playwright.py` Step 5.

---

## 6. Mode Comparison Summary Matrix

| Mode | Visual Theme | `#muscle-recruitment-list` | Watermark Banner | 3D Renderer State | Tested Behavior |
|---|---|---|---|---|---|
| **Mode A: Anatomy** | Sky Blue / Amber / Purple | `display: none` | `ANATOMICAL FUNCTION & PARTICIPATION` | Agonists / Synergists / Stabilizers highlighted; click isolates in gold | Click card isolates mesh |
| **Mode B: Geometry** | Amber Warning | `display: none` | `MODEL GEOMETRY INSUFFICIENT` | Dimmed muscles (0.22); highlighted bone joints | Shows $L_0$ reference metrics |
| **Mode C: Activation** | Heat-map Ramp | `display: block` | `MATHEMATICAL MODEL ESTIMATE — NOT MEASURED EMG` | Blue $\to$ Yellow $\to$ Red heat-map on meshes | Animates with scrubber |
| **Mode D: Force** | Amber Warning | `display: none` | `MUSCLE FORCE NOT AVAILABLE` | Neutral terracotta tone (0.45); no highlights | Refuses fake forces |
