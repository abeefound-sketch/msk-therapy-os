# ARCHITECTURE DECISION RECORD (ADR) P13-01
## Selection of 3D Musculoskeletal Visualization Foundation & Biomechanics Integration Architecture

- **Status:** APPROVED
- **Date:** 2026-10-30
- **Authors:** Principal Software Architect & Biomechanics Integration Engineer
- **Applies to:** Milestone P13 (Interactive MSK Education Studio)

---

## 1. CONTEXT & PROBLEM STATEMENT

MSK-Therapy-OS requires an interactive 3D anatomical and functional biomechanics education module that explains the musculoskeletal mechanics of rounded shoulder posture ("Why Do Rounded Shoulders Sometimes Return After Massage?").

Constraints:
1. Target hardware: Intel Core i7-5600U, 8 GB RAM, Intel HD Graphics 5500.
2. Zero external dependencies: 100% offline runtime on Windows x64 without CDN calls, package managers, or build steps.
3. Strict non-degradation of existing clinical workstation (`gl.js`, SOAP notes, ROM tracker, G14 gate).
4. Truth in advertising: Static meshes must not be deceptively represented as validated dynamic physical simulations.

---

## 2. DECISION

We adopt a **Dual-Engine Decoupled Architecture**:

1. **3D Visual & Educational Subsystem:**
   - **Engine:** Three.js r160 localized ES6 modules (`msk_therapy_os/static/education/vendor/three/`).
   - **Mesh Geometry:** BodyParts3D/Z-Anatomy optimized `.glb` asset (`anatomy.glb`, 8.86 MB) containing 54 segmented functional muscle groups and osseous landmarks.
   - **Host Route:** Isolated WebGL canvas served under `/education/` with automatic animation frame suspension when the tab is blurred or inactive.

2. **Quantitative Biomechanics Subsystem:**
   - **Module:** `msk_therapy_os/biomechanics_adapter.py`.
   - **Specification:** OpenSim `.mot` (motion) and `.sto` (storage) kinematic data parser supporting coordinate conversion, degree/radian validation, range limit checking, missing channel detection, and deterministic linear interpolation.
   - **Kinematic Boundary Declaration:** Because `anatomy.glb` lacks skinned joint weights, we explicitly report `SHOULDER_MOTION_DATA_UNAVAILABLE` regarding continuous multi-muscle physiological volumetric deformation, while providing validated discrete educational posture configurations and scapulohumeral rhythm ratios (2:1 glenohumeral to scapulothoracic elevation) with full literature attribution (Inman 1944, Ludewig 2009).

---

## 3. ALTERNATIVES CONSIDERED & REASONS FOR REJECTION

### Alternative A: Extend Existing WebGL Renderer (`gl.js`) with Custom GLTF/Skeletal Loader
- *Rationale for Rejection:* `gl.js` is an optimized 32 KB renderer tailored for single-draw-call skin hulls and 3D meridian curves. Adding full GLTF parsing, material PBR handling, and orbit controls to `gl.js` would bloat the core clinical atlas renderer, increase maintenance overhead, and risk regressions across the 770 existing tests.

### Alternative B: Direct OpenSim WASM C++ Solver in Browser
- *Rationale for Rejection:* Compiling the C++ OpenSim engine to WebAssembly generates a > 45 MB binary with high initialization times (> 15 seconds) that exceeds the RAM budget of the target Intel HD 5500 hardware and introduces build complexity.

### Alternative C: Full Z-Anatomy Blender Export
- *Rationale for Rejection:* Full Z-Anatomy meshes exceed 250 MB and 500,000 vertices, causing instantaneous browser tab crashes on integrated Intel GPUs due to DDR3L shared memory saturation.

---

## 4. CONSEQUENCES & SAFEGUARDS

### Positive Consequences:
- High visual fidelity: 54 distinct anatomical muscle groups allow precise color-highlighting of pectoralis minor, pectoralis major, anterior deltoid, upper/lower trapezius, and serratus anterior.
- High performance: Single optimized 8.86 MB asset loads in $< 1$ second and achieves stable 45–60 FPS on Intel HD 5500.
- Strict isolation: Educational interactions cannot contaminate clinical records or patient databases.

### Safeguards:
- Educational disclaimers permanently embedded in UI and API payloads.
- `G14: BLOCKED_EXTERNAL_DATA` gate remains untouched and fail-closed.
- Automated tests verify asset hash integrity, parser correctness, and API endpoints.
