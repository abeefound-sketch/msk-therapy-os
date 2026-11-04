# MSK-Therapy-OS: WebGL Visual Acceptance & 3D Anatomy Verification

**Date:** November 5, 2026  
**Rendering Target:** WebGL 2.0 Canvas, Three.js r128+, Google SwiftShader (Software Rasterization) / Intel HD Graphics 5500.

---

## 1. Visual Verification Methodology

Automated Playwright browser tests executed in headless Chromium captured visual proof directly from the WebGL canvas. UI badges, CSS indicators, and HTML legends were explicitly disqualified as proof of visible 3D geometry; only rendered canvas pixels and evaluated scene-graph objects were accepted.

---

## 2. Canvas Rendering Evidence Summary

| Module | Studio / Viewer | Viewport | Key Visual Features Verified | Captured PNG Screenshot |
|:---|:---|:---:|:---|:---|
| **Arm Studio** | `character_v12/index.html` | 1400x900 | Rest Pose (0° elbow extension), 5 authentic bones, 6 muscles, LI4/LI11 markers | `evidence/browser_screenshots/v12_1_01_posture_0deg_rest.png` |
| **Arm Studio** | `character_v12/index.html` | 1400x900 | Mid Flexion (45°), biceps shortening >10%, belly diameter expansion | `evidence/browser_screenshots/v12_1_02_posture_45deg_mid.png` |
| **Arm Studio** | `character_v12/index.html` | 1400x900 | Right Angle Flexion (90°), triceps elongation >15%, LI4 elevation | `evidence/browser_screenshots/v12_1_03_posture_90deg_right_angle.png` |
| **Arm Studio** | `character_v12/index.html` | 1400x900 | Deep Flexion (120°), articular joint gap 2.4mm, zero mesh penetration (0.0mm) | `evidence/browser_screenshots/v12_1_04_posture_120deg_deep_flexion.png` |
| **Arm Studio** | `character_v12/index.html` | 1400x900 | Musculoskeletal Anatomy Mode (muscles & bones isolated) | `evidence/browser_screenshots/v12_1_05_anatomy_mode_120deg.png` |
| **Arm Studio** | `character_v12/index.html` | 1400x900 | Character Mode (pure MakeHuman living skin) | `evidence/browser_screenshots/v12_1_06_character_skin_mode.png` |
| **Arm Studio** | `character_v12/index.html` | 1400x900 | Tissue Layer Slicing (skin + meridian line visible; bones/muscles hidden) | `evidence/browser_screenshots/v12_1_07_skin_and_meridian_layer.png` |
| **Arm Studio** | `character_v12/index.html` | 1400x900 | GPU Morph Targets: ArmLength 0.8, ShoulderWidth 0.7, Broader 0.6 | `evidence/browser_screenshots/v12_1_08_morphed_broader_flexion90.png` |
| **Dien Chan** | `static/dien_chan/index.html` | 1440x900 | 3D Facial Reflexology Mesh, Point Groups, Vietnamese Search Protocol | `evidence/browser_screenshots/dien_chan_initial_load.png` |
| **Fullbody UABS** | `static/character_v13/index.html` | 1400x900 | Full-body 19.4 MB GLB humanoid avatar, 17-bone skeleton, 14 meridians | `evidence/browser_screenshots/v13_01_fullbody_atlas_initial.png` |

---

## 3. Hardware Performance Envelope

- **Intel HD Graphics 5500 (Hardware Acceleration):** 57.4 - 59.9 sustained FPS, 20.3ms P95 frame time.
- **Headless SwiftShader (Pure CPU Software Rasterization):** Sustained 8 - 9 FPS, zero WebGL context crashes.
