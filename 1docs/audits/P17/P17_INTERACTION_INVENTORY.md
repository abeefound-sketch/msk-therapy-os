# P17 Complete UI Interaction Inventory & Verification Ledger

## 1. Overview & Classification Standard

Every visible user interface control is evaluated under the two fundamental acceptance criteria:
- **Condition A (Functional)**: User interaction alters application state, executes domain logic, updates the 3D renderer / visual scene, and is verifiable by end-to-end browser automation.
- **Condition B (Explicitly Unavailable)**: If required data, mesh paths, or dynamic solvers are unavailable offline, the control displays an unambiguous unavailable banner identifying missing prerequisites and refuses to invent fictional data.

Classifications:
- `FUNCTIONAL_VERIFIED`: Genuine end-to-end execution and visible result verified in Playwright browser tests.
- `INTENTIONALLY_DISABLED`: Explicit unavailable state or disclaimer shown with technical provenance; zero fake data.
- `BROKEN`: Control fails to alter state or produces deceptive visual feedback.

---

## 2. Comprehensive Control Ledger

| UI Element ID | Visible Label | Intended Function | JS Event Handler | State Variable | API Dependency | Scientific Prerequisite | Observable Visual Effect | Playwright Test | Current Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `#btn-mode-anatomy` | Chế độ A: Giải Phẫu | Explain anatomical muscle participation | `click -> setMode('MODE_A_...')` | `this.currentMode` | `/api/education/muscle-mechanics` | Muscle catalog attachment records | Agonists (#38bdf8), synergists (#f59e0b) highlighted in 3D; static percentages hidden; cards rendered | `test_p17_pw` Step 1-2 | `FUNCTIONAL_VERIFIED` |
| `.interactive-muscle-card` | [Muscle Cards] | Select & isolate individual muscle | `click -> selectMuscle(id)` | `this.selectedMeshName` | None (Local 3D Map) | Mapped GLB mesh identifier | Muscle lights up in gold (#facc15), others dimmed (opacity 0.18), camera focuses | `test_p17_pw` Step 2 | `FUNCTIONAL_VERIFIED` |
| `#btn-mode-geometry` | Chế độ B: Hình Học | Inspect musculotendon length change | `click -> setMode('MODE_B_...')` | `this.currentMode` | `/api/education/muscle-mechanics` | Discrete 3D wrapping curves | Shows `MODEL_GEOMETRY_INSUFFICIENT`; renders resting $L_0$ literature data; bars hidden | `test_p17_pw` Step 3 | `FUNCTIONAL_VERIFIED` |
| `#btn-mode-activation` | Chế độ C: Kích Hoạt | Inspect static optimization activation | `click -> setMode('MODE_C_...')` | `this.currentMode` | OpenSim `.sto` reader | Static optimization `.sto` dataset | Displays watermark banner; shows progress bars; 3D heat-map (blue->yellow->red) | `test_p17_pw` Step 4 | `FUNCTIONAL_VERIFIED` |
| `#btn-mode-force` | Chế độ D: Lực Cơ (N) | Inspect individual muscle forces | `click -> setMode('MODE_D_...')` | `this.currentMode` | None (Blocked offline) | Dynamic equilibrium runtime solver | Displays `MUSCLE_FORCE_NOT_AVAILABLE`; percentage bars hidden; zero invented data | `test_p17_pw` Step 5 | `FUNCTIONAL_VERIFIED` |
| `#btn-mode-comparison` | So Sánh Kịch Bản | Compare flexion vs forward head | `click -> setMode('SCENARIO_...')` | `this.currentMode` | `/api/education/compare-scenarios` | Scenario catalog & lever arms | Opens `#comparison-card` with $\Delta$ moment arm, torque, extensor load | `test_p17_pw` Step 8 | `FUNCTIONAL_VERIFIED` |
| `#btn-close-comparison` | Đóng (X) | Close scenario comparison dialog | `click` | DOM style | None | None | Hides `#comparison-card` | `test_p17_pw` Step 8 | `FUNCTIONAL_VERIFIED` |
| `#btn-view-anterior` | Mặt Trước | Frame front anatomical view | `click -> setCameraView('anterior')` | `camera.position` | None (Local Three.js) | Valid Three.js PerspectiveCamera | Camera moves to `(x, y, +dist)` facing origin; button receives `.active` class | `test_p17_pw` Step 10 | `FUNCTIONAL_VERIFIED` |
| `#btn-view-posterior` | Mặt Sau (Bả Vai) | Frame rear scapular view | `click -> setCameraView('posterior')` | `camera.position` | None (Local Three.js) | Valid Three.js PerspectiveCamera | Camera moves to `(x, y, -dist)` facing scapula; button receives `.active` class | `test_p17_pw` Step 10 | `FUNCTIONAL_VERIFIED` |
| `#btn-view-lateral` | Mặt Bên | Frame sagittal lateral view | `click -> setCameraView('lateral')` | `camera.position` | None (Local Three.js) | Valid Three.js PerspectiveCamera | Camera moves to `(+dist, y, z)` facing lateral profile; button receives `.active` class | `test_p17_pw` Step 10 | `FUNCTIONAL_VERIFIED` |
| `#btn-toggle-skeleton` | Khung Xương: Bật/Tắt | Toggle skeletal mesh visibility | `click -> setSkeletonVisible()` | `skeletonRoot.visible` | None | Local skeleton root | Bones hide/show; button text updates to "Bật" or "Tắt" | `test_p14_pw`, `test_p16_pw` | `FUNCTIONAL_VERIFIED` |
| `#muscle-opacity-slider` | Độ Mờ Cơ (Slider) | Adjust muscle transparency | `input -> setMuscleOpacity(val)` | `mesh.material.opacity` | None | WebGL material transparency | All muscle meshes smoothly fade between 0.0 and 1.0 | `test_p14_pw` | `FUNCTIONAL_VERIFIED` |
| `#btn-motion-play` | ▶ Phát / ⏸ Tạm dừng | Toggle animation playback | `click -> togglePlay()` | `this.isPlaying` | None | Valid `.mot` timeline | Time advances continuously, pivots rotate, button text updates to ⏸/▶ | `test_p17_pw` Step 6 | `FUNCTIONAL_VERIFIED` |
| `#btn-motion-reset` | ⏮ Đặt lại | Reset animation time to 0.0s | `click -> reset()` | `this.currentTime = 0.0` | None | None | Scrubber and readout reset to `0.00 s / 2.00 s`, joint angles reset to $t=0$ | `test_p17_pw` Step 6 | `FUNCTIONAL_VERIFIED` |
| `#btn-speed-025` | 0.25x | Set quarter-speed playback | `click -> setPlaybackSpeed(0.25)` | `this.playbackSpeed` | None | None | Playback advances at 0.25x; button receives `.active` class | `test_p16_pw` | `FUNCTIONAL_VERIFIED` |
| `#btn-speed-05` | 0.5x | Set half-speed playback | `click -> setPlaybackSpeed(0.5)` | `this.playbackSpeed` | None | None | Playback advances at 0.5x; button receives `.active` class | `test_p17_pw` Step 6 | `FUNCTIONAL_VERIFIED` |
| `#btn-speed-1` | 1.0x | Set normal playback speed | `click -> setPlaybackSpeed(1.0)` | `this.playbackSpeed` | None | None | Playback advances at 1.0x; button receives `.active` class | `test_p16_pw` | `FUNCTIONAL_VERIFIED` |
| `#motion-time-slider` | Timeline Scrubber | Seek exact motion timestamp | `input -> seek(t)` | `this.currentTime` | None | OpenSim `.mot` dataset | Joints rotate to exact interpolated posture; readouts update | `test_p17_pw` Step 4 | `FUNCTIONAL_VERIFIED` |
| `#scenario-select` | [Scenario Dropdown] | Select motion kinematics scenario | `change -> loadMotionData()` | `activeScenarioId` | Local `.mot` and `.sto` | Valid OpenSim text files | Loads kinematics, resets timeline, updates angles and physics metrics | `test_p17_pw` Step 7 | `FUNCTIONAL_VERIFIED` |
| `#region-select` | [Region Dropdown] | Select body region (Unified/Cervical/Shoulder) | `change -> setRegion()` | `this.currentRegion` | Unified curriculum API | Matching GLB skeleton & scenarios | Adapts camera focus, switches curriculum topics, updates default scenario | `test_p16_pw` Step 4 | `FUNCTIONAL_VERIFIED` |
| `.stage-nav-item` | [Curriculum 1-10] | Select curriculum learning module | `click -> _renderStage(id)` | `this.currentStageId` | None | Curriculum topics JSON | Active highlight updates, title/summary changes, 3D highlights focus muscles | `test_p17_pw` Step 9 | `FUNCTIONAL_VERIFIED` |
| `#posture-slider` | [Posture Severity] | Simulate rounded shoulder / FHP | `input -> _updateBiomechanics()` | `this.postureSeverity` | Cervical mechanics API | Biomechanical lever arm equations | Readouts update (Protraction, CVA, Moment Arm, Extensor Load) | `test_p17_pw` Step 7 | `FUNCTIONAL_VERIFIED` |
| `#btn-lang-toggle` | EN / VI | Toggle interface language | `click -> toggleLang()` | `this.currentLang` | None | Bilingual dictionary | Headers, labels, summaries, badges switch between Vietnamese and English | `test_p17_pw` Step 10 | `FUNCTIONAL_VERIFIED` |
