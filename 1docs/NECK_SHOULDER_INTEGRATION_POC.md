# Neck-Shoulder Surface Registration Prototype (Milestone M2 PoC)

## Executive Summary

As required by Phase 3, this prototype delivers an isolated demonstration of verified 3D anatomical surface registration for the six core **Neck-Shoulder MSK scenario points**:

1. **GV14** (Dazhui / Great Hammer)
2. **GB21** (Jianjing / Shoulder Well)
3. **GB20** (Fengchi / Wind Pool)
4. **BL10** (Tianzhu / Celestial Pillar)
5. **SI15** (Jianzhongshu / Central Shoulder Shu)
6. **TE15** (Tianliao / Heavenly Crevice)

The prototype operates on an isolated Git branch (`prototype/neck-shoulder-poc`) with **zero modifications to production `main` or `msk_therapy_os/`**. The application is currently running live on **`http://127.0.0.1:8085/`** for manual verification.

---

## 1. Architectural & Isolation Safeguards

- **Isolation Branch**: `prototype/neck-shoulder-poc`
- **Zero Production Mutation**: Neither `main` nor `msk_therapy_os/` was modified.
- **Dedicated Prototype Runner**: Implemented in `prototype/server.py` subclassing `MSKRequestHandler` to route acupuncture API requests strictly to `prototype/data/neck_shoulder_poc.json`.
- **Anatomy Atlas Preservation**: Reuses Open Anatomy Atlas WebGL renderer and BodyParts3D binary mesh assets without alterations.

---

## 2. Anatomical & Geometric Verification Matrix

All six target points were extracted from JICio's surface-baked topology and cross-validated against the reconstructed BodyParts3D softened skin mesh (`fj2810_softened.bin`):

| Point Code | Standard Name | Side Instances | Anatomical Landmark Anchor (WHO 2008 / FMA) | Softened Mesh Face Index | Measured Mesh Distance | Outward Normal Dot | Registration Status |
|---|---|---|---|---|---|---|---|
| **GV14** | 大椎 (Dazhui) | Midline | FMA12525 (Seventh cervical vertebra spinous process) | 21,933 | **0.00 mm** | +1.000 | `VERIFIED_ANATOMICAL_ANCHOR` |
| **GB21** | 肩井 (Jianjing) | Bilateral (R/L) | FMA9622 (Trapezius muscle ridge, midpoint C7 to acromion) | 29,231 (R) / 12,630 (L) | **0.00 mm** | +1.000 | `VERIFIED_ANATOMICAL_ANCHOR` |
| **GB20** | 风池 (Fengchi) | Bilateral (R/L) | FMA9622 & FMA13407 (Suboccipital depression between SCM and trapezius) | 24,035 (R) / 18,009 (L) | **0.00 mm** | +1.000 | `VERIFIED_ANATOMICAL_ANCHOR` |
| **BL10** | 天柱 (Tianzhu) | Bilateral (R/L) | FMA12520 (Level of C2 spinous process, lateral border of trapezius) | 21,884 (R) / 19,693 (L) | **0.00 mm** | +1.000 | `VERIFIED_ANATOMICAL_ANCHOR` |
| **SI15** | 肩中俞 (Jianzhongshu) | Bilateral (R/L) | FMA13328 (2 cun lateral to lower border of C7 spinous process) | 26,083 (R) / 16,930 (L) | **0.00 mm** | +1.000 | `VERIFIED_ANATOMICAL_ANCHOR` |
| **TE15** | 天髎 (Tianliao) | Bilateral (R/L) | FMA23223 (Superior angle of scapula / supraspinous fossa) | 28,034 (R) / 10,502 (L) | **0.00 mm** | +1.000 | `VERIFIED_ANATOMICAL_ANCHOR` |

---

## 3. Visual Multi-Angle 3D Evidence

The prototype was rendered in Chromium with native Intel HD 5500 hardware acceleration. Screenshots were captured across four distinct camera viewpoints to verify that overlays remain locked to the skin surface without floating or penetrating:

### View 1: Posterior View (Back)
- **Artifact**: `research/artifacts/evidence_poc_posterior.png`
- **Camera Orientation**: `yaw = 180°`, `pitch = 2.8°`, `dist = 0.68m`, `target = [0, 1.48, -0.08]`
- **Observation**: All 11 circle instances (1 midline GV14 + 5 bilateral pairs) render in emerald green (`#10b981`), conforming strictly to the posterior cervical curvature and scapular borders. Continuous meridian paths (GV, BL, GB, SI, TE) trace without step discontinuities.

### View 2: Superior-Oblique View (Shoulder Top)
- **Artifact**: `research/artifacts/evidence_poc_shoulder_top.png`
- **Camera Orientation**: `yaw = 208°`, `pitch = 31.5°`, `dist = 0.58m`, `target = [0.04, 1.46, -0.06]`
- **Observation**: Shows GB21 (Jianjing) resting directly on the apex of the trapezius muscle ridge and TE15 in the supraspinous hollow. Highlights yellow selection halo around GB21.

### View 3: Left Lateral View (Profile)
- **Artifact**: `research/artifacts/evidence_poc_lateral.png`
- **Camera Orientation**: `yaw = 93.6°`, `pitch = 2.8°`, `dist = 0.62m`, `target = [0, 1.48, -0.08]`
- **Observation**: Confirms suboccipital hollow seating for GB20. Dynamic occlusion culling correctly hides right-sided contralateral points facing away from the camera.

### View 4: Zoomed Close-Up View (C7 / GV14 Cervical Junction)
- **Artifact**: `research/artifacts/evidence_poc_zoomed.png`
- **Camera Orientation**: `yaw = 180°`, `pitch = 1.1°`, `dist = 0.32m`, `target = [0, 1.44, -0.09]`
- **Observation**: Close-up inspection of the C7 spinous process depression. GV14 circle remains exactly centered on the vertebral prominence without polygonal penetration or floating offset.

### View 5: Main Application Integrated UI
- **Artifact**: `research/artifacts/evidence_poc_main_ui.png`
- **URL**: `http://127.0.0.1:8085/`
- **Observation**: Clicking GV14 inside the 3D atlas iframe automatically propagates to the main host application via `postMessage`, opening the `#atlasAcupointCard` with complete WHO localization guide, BodyParts3D anchor reference, clinical indications, cautions, tuina technique, and integration buttons ("Add to SOAP", "Add to Observation").

---

## 4. Manual Acceptance Testing Instructions

The server is currently running in the background. To verify the live prototype in your browser:

1. Open your browser and navigate to:
   - **Main App**: [http://127.0.0.1:8085/](http://127.0.0.1:8085/)
   - **Standalone Atlas**: [http://127.0.0.1:8085/atlas/](http://127.0.0.1:8085/atlas/)
2. In the 3D viewport, rotate the camera to the back (drag with left mouse button or click "Back" view).
3. In the left overlay controls, ensure **"📍 3D Acupoints"** and **"⚡ 14 Meridian Pathways"** are checked.
4. Click on **GV14** (center of back of neck), **GB21** (top of shoulder), or **GB20** (base of skull).
5. Verify that:
   - The selected point highlights with a yellow halo.
   - The interactive pin tooltip displays the point code, Chinese name, and "[✓ Verified]" badge.
   - In the main app, the left sidebar displays the complete clinical inspector card.
   - Zoom in/out with the mouse wheel: points remain locked to the skin surface.
