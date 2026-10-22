# Display Controls Acceptance: Host UI & Atlas Synchronization

**Document ID:** M2.6-UI-004  
**Author:** Staff Frontend QA Specialist, Human-Computer Interaction Engineer  
**Project:** MSK-Therapy-OS (`prototype/neck-shoulder-poc`)  
**Status:** Implemented & Verified  

---

## 1. Overview

Milestone M2.6 introduces a centralized **Display Settings Panel** accessible from the primary Atlas toolbar via the `🎨 Display` button. The interface allows clinicians and practitioners to seamlessly modulate visual point density, marker sizes, meridian line widths, and clustering algorithms according to their clinical inspection workflow.

---

## 2. Interactive Control Matrix

| Control ID | Label | Type | Default Value | Range / Options | Target Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `scalingModeSelect` | Scaling Mode | `<select>` | `auto` | `auto` (Adaptive), `manual` (Fixed) | Controls whether marker and line geometry adaptively scale with camera distance or obey manual sliders. |
| `markerSizeSlider` | Acupoint Size | `<input type="range">` | `3` | `1` to `6` (Step: 1) | Modulates marker base radius from $1.6\text{px}$ to $6.3\text{px}$ in manual mode; applies scalar multiplier in auto mode. |
| `lineWidthSlider` | Meridian Line | `<input type="range">` | `3` | `1` to `6` (Step: 1) | Modulates polyline stroke width from $1.0\text{px}$ to $4.2\text{px}$. |
| `labelDensitySelect` | Label Density | `<select>` | `auto` | `auto`, `all`, `selected`, `none` | Controls SVG text label visibility (auto displays labels only when camera zoom is sufficient or point is selected). |
| `smartDensityToggle` | Smart Density | `<input type="checkbox">` | `true` (Checked) | `true` (On), `false` (Off) | Enables or disables $O(N)$ spatial grid clustering in zoomed-out views. |
| `btnResetDisplaySettings` | Reset Defaults | `<button>` | — | Click action | Restores all settings to clinical defaults and clears invalid overrides. |

---

## 3. Live Density Metric Counters

The panel features a live, 4-tier status readout tracking the conservation of clinical acupoint codes across viewport states:

```
┌────────────────────────────────────────────────────────┐
│  Available: 368  │  Visible: 107  │  Clustered: 172  │  Filtered: 89  │
└────────────────────────────────────────────────────────┘
```

### Mathematical Conservation Formula:
$$\text{Available} = \text{Visible} + \text{Clustered} + \text{Filtered}$$

- **Available:** Count of unique clinical codes currently loaded in the database.
- **Visible:** Number of distinct codes currently rendered as individual clickable markers in the SVG viewport.
- **Clustered:** Number of distinct codes aggregated within cluster badges.
- **Filtered:** Number of codes suppressed by active regional filters (e.g. Neck/Shoulder focus), inactive meridian filters, or occlusion by 3D anatomy.

---

## 4. Cross-Frame Event Protocol (`postMessage`)

Because the 3D Atlas runs inside an isolated `<iframe>` (`#atlasFrame`) to isolate WebGL context and render threads from the clinical host UI, settings changes and counter broadcasts synchronize via HTML5 `postMessage`:

### 4.1 Host to Atlas (Settings Update)
```javascript
// Dispatched by host toolbar whenever slider or toggle changes
atlasFrame.contentWindow.postMessage({
  type: 'msk_update_display_settings',
  settings: {
    scalingMode: 'manual', // or 'auto'
    markerSize: 4,
    lineWidth: 3,
    labelDensity: 'auto',
    smartDensity: true
  }
}, '*');
```

### 4.2 Atlas to Host (Counter Broadcast)
```javascript
// Dispatched by meridians.js on each render cycle when counts change
window.parent.postMessage({
  type: 'msk_density_counters_updated',
  counters: {
    available: 368,
    visible: 107,
    clustered: 172,
    filtered: 89
  }
}, '*');
```

---

## 5. Persistence Specification

- Storage mechanism: `window.localStorage` under key `msk_display_settings_v1`.
- Resilience: If corrupted JSON is detected, defaults are silently restored without breaking the WebGL render loop or UI rendering.
- Cross-tab synchronization: Changes in one session persist across browser reloads.
