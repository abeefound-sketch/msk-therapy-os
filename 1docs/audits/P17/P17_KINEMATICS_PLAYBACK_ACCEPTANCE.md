# P17 Kinematics, Playback & Motion Controls Acceptance Audit

## 1. Compliance Standard

Under Acceptance Principle P17-04:
- All playback controls must produce observable changes in application state and WebGL scene transforms.
- Play advances time; Pause stops time; Reset rewinds to $0.00\text{ s}$; Speed multipliers alter playback rate.
- Timeline scrubber allows random-access seeking with real-time skeletal articulation.

---

## 2. Playback Controls Verification

### Play / Pause (`#btn-motion-play`)
- **Initial State**: Paused, label `▶ Phát` (or `▶ Play`).
- **Action**: Click `#btn-motion-play`.
- **Observable Result**: State switches to `isPlaying = true`; button updates to `⏸ Tạm dừng` with `.active` class. Time progresses continuously via `requestAnimationFrame` delta accumulator.
- **Pause Action**: Click again; state switches to `isPlaying = false`; time progression freezes at current timestamp.

### Reset (`#btn-motion-reset`)
- **Action**: Click `#btn-motion-reset`.
- **Observable Result**: `currentTime` resets to `0.0`; scrubber slider value resets to `0`; readout label displays `0.00 s / 2.00 s`; all 9 joint pivots return to reference zero angles.

### Speed Multipliers (`#btn-speed-025`, `#btn-speed-05`, `#btn-speed-1`)
- **Functionality**: `setPlaybackSpeed(speed)` updates `this.playbackSpeed`.
- **Visual Feedback**: The clicked speed button gains `.active` class while others lose it.
- **Playback Rate**: Validated at $0.25\times$, $0.50\times$, and $1.00\times$ progression speeds.

---

## 3. Timeline Scrubbing & Kinematic Transform Mapping

The OpenSim `.mot` parser reads column vectors and linearly interpolates channel values at timestamp $t$:

```text
Timestamp t
     │
     ├── arm_elevation ────────► pivots.gh.rotation.z
     ├── scapula_upward_rot ───► pivots.ac.rotation.z
     ├── scapula_tilt ─────────► pivots.ac.rotation.x
     ├── clavicle_elev ────────► pivots.sc.rotation.z
     ├── lower_cervical_flex ──► pivots.c7t1.rotation.x
     ├── upper_cervical_flex ──► pivots.aa.rotation.x & pivots.ao.rotation.x
     ├── head_anterior_trans ──► pivots.c7t1.position.z
     ├── cervical_rotation ────► pivots.c7t1.rotation.y & pivots.aa.rotation.y
     └── cervical_lateral_bend ► pivots.c7t1.rotation.z & pivots.ao.rotation.z
```

All 6 motion scenarios (`seth_shoulder_elevation`, `illustrative_rounded_elevation`, `vasavada_cervical_flexion_extension`, `illustrative_forward_head_posture`, `cervical_axial_rotation`, `cervical_lateral_bending`) smoothly articulate their corresponding joints during playback.

---

## 4. Posture Simulator Slider (`#posture-slider`)

- **Range**: 0% (ideal alignment) to 100% (extreme forward head / rounded shoulder).
- **Domain Equations**:
  - Protraction angle: $15.0^\circ + (\text{severity} \times 28.0^\circ)$
  - Scapular anterior tilt: $8.0^\circ + (\text{severity} \times 25.0^\circ)$
  - Craniovertebral Angle (CVA): $55.0^\circ - (\text{severity} \times 25.0^\circ)$
  - Horizontal lever arm $d$: $2.5\text{ cm} + \left(\frac{55^\circ - \text{CVA}}{25^\circ}\right) \times 5.0\text{ cm}$
- **Evidence Screenshot**: `1docs/audits/P17/screenshots/06_playback_timeline_scrubbing.png` and `07_rom_cervical_movement.png`.
