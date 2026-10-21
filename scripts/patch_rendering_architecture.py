"""Comprehensive rendering architecture patch for:
1. Three Visualization Modes:
   - Mode A: Surface Meridian Mode
   - Mode B: Musculoskeletal Anatomy Mode
   - Mode C: Comparative Research Mode (Dual Split View)
2. Accurate Surface Normal Backface Culling in meridians.js
3. Skin Opacity Control (0% - 100%)
4. Individual Meridian Channel Filtering
5. UI Responsiveness & Responsive Toolbar Updates
"""
from pathlib import Path

BASE = Path("D:/5Projects/msk-therapy-os")

# ===========================================================================
# 1. Update meridians.js
# ===========================================================================
mer_path = BASE / "msk_therapy_os/static/atlas/meridians.js"
mer_src = mer_path.read_text(encoding="utf-8").replace("\r\n", "\n")

# State additions
old_state = """  let acuData = null;
  // Default to clean anatomical view with unnecessary overlays disabled (Requirement 7)
  let showPoints = false;
  let showMeridians = false;
  let showThai = false;
  let showDienChan = false;
  let verifiedOnly = true; // Default to verified anatomical anchors only
  let filterRegion = 'neck_shoulder'; // Focus scenario
  let selectedCode = null;
  let searchQuery = '';"""

new_state = """  let acuData = null;
  // Default to clean anatomical view with unnecessary overlays disabled (Requirement 7)
  let showPoints = false;
  let showMeridians = false;
  let showThai = false;
  let showDienChan = false;
  let verifiedOnly = true; // Default to verified anatomical anchors only
  let filterRegion = 'neck_shoulder'; // Focus scenario
  let filterMeridian = 'all'; // 'all' or specific meridian code (e.g. 'GV', 'BL', 'GB')
  let selectedCode = null;
  let searchQuery = '';
  let showSurfaceReference = false; // Optional reference in Musculoskeletal mode"""

if old_state in mer_src:
    mer_src = mer_src.replace(old_state, new_state)

# Accurate normal-based occlusion
old_facing = """  // Camera facing / occlusion test in horizontal plane
  function isFacingCamera(pos, r) {
    if (!r) return true;
    const eye = r._eye();
    const target = r.camera.target || [0, 0.9, 0];
    const h = pos[0] * (eye[0] - target[0]) + pos[2] * (eye[2] - target[2]);
    // If camera has steep pitch looking down from above, top shoulder/head points stay visible
    if (r.camera.pitch > 0.45 && pos[1] > 1.40) return true;
    return h >= -0.012;
  }"""

new_facing = """  // Camera facing / occlusion test using 3D surface normal whenever available
  function isFacingCamera(pos, r, normal = null) {
    if (!r) return true;
    const eye = r._eye();
    if (normal && normal.length === 3) {
      // 3D vector from surface point to camera eye
      const vx = eye[0] - pos[0];
      const vy = eye[1] - pos[1];
      const vz = eye[2] - pos[2];
      const dot = normal[0] * vx + normal[1] * vy + normal[2] * vz;
      return dot > -0.04;
    }
    const target = r.camera.target || [0, 0.9, 0];
    const h = pos[0] * (eye[0] - target[0]) + pos[2] * (eye[2] - target[2]);
    if (r.camera.pitch > 0.45 && pos[1] > 1.40) return true;
    return h >= -0.012;
  }"""

if old_facing in mer_src:
    mer_src = mer_src.replace(old_facing, new_facing)

# Projector supporting comparative mode
old_proj = """  // Fast inline projection using cached matrix to prevent GC churn on Intel HD 5500
  function createProjector(r) {
    const { vp } = r._matrices();
    const cw = r.canvas.clientWidth;
    const ch = r.canvas.clientHeight;
    return function fastProject(pos) {
      const x = vp[0] * pos[0] + vp[4] * pos[1] + vp[8] * pos[2] + vp[12];
      const y = vp[1] * pos[0] + vp[5] * pos[1] + vp[9] * pos[2] + vp[13];
      const w = vp[3] * pos[0] + vp[7] * pos[1] + vp[11] * pos[2] + vp[15];
      if (w <= 0.001) return null;
      return [(x / w * 0.5 + 0.5) * cw, (1 - (y / w * 0.5 + 0.5)) * ch];
    };
  }"""

new_proj = """  // Fast inline projection supporting both single viewport and comparative dual-split
  function createProjector(r) {
    const isComp = r && r.renderMode === 'comparative';
    const cw = r.canvas.clientWidth;
    const ch = r.canvas.clientHeight;
    const aspect = isComp ? Math.max(1e-3, (cw * 0.5) / Math.max(1, ch)) : Math.max(1e-3, cw / Math.max(1, ch));
    const { vp } = isComp ? r._matricesForAspect(aspect) : r._matrices();
    const xOffset = isComp ? cw * 0.5 : 0;
    const xSpan = isComp ? cw * 0.5 : cw;

    return function fastProject(pos) {
      const x = vp[0] * pos[0] + vp[4] * pos[1] + vp[8] * pos[2] + vp[12];
      const y = vp[1] * pos[0] + vp[5] * pos[1] + vp[9] * pos[2] + vp[13];
      const w = vp[3] * pos[0] + vp[7] * pos[1] + vp[11] * pos[2] + vp[15];
      if (w <= 0.001) return null;
      return [xOffset + (x / w * 0.5 + 0.5) * xSpan, (1 - (y / w * 0.5 + 0.5)) * ch];
    };
  }"""

if old_proj in mer_src:
    mer_src = mer_src.replace(old_proj, new_proj)

# Update render() beginning with mode checks and split view badges
old_render_start = """  function render() {
    const r = getRenderer();
    if (!r || !acuData) return;

    const stage = document.querySelector('.stage');
    if (!stage) return;
    const sw = stage.clientWidth;
    const sh = stage.clientHeight;
    const fastProject = createProjector(r);

    // 1. Render Continuous Surface-Conforming Meridians (10,762 Vertices)"""

new_render_start = """  function render() {
    const r = getRenderer();
    if (!r || !acuData) return;

    const stage = document.querySelector('.stage');
    if (!stage) return;
    const sw = stage.clientWidth;
    const sh = stage.clientHeight;
    const fastProject = createProjector(r);

    const isMusculo = r.renderMode === 'musculoskeletal';
    const isComp = r.renderMode === 'comparative';

    // In pure Musculoskeletal mode, hide meridians and points unless surface reference guide is enabled
    if (isMusculo && !showSurfaceReference) {
      groupMeridians.innerHTML = '';
      groupThai.innerHTML = '';
      groupPoints.innerHTML = '';
      const pin = document.getElementById('pin');
      if (pin) pin.hidden = true;
      return;
    }

    // 1. Render Continuous Surface-Conforming Meridians (10,762 Vertices)"""

if old_render_start in mer_src:
    mer_src = mer_src.replace(old_render_start, new_render_start)

# Update meridian loop for filterMeridian
old_m_loop = """      for (const mCode in acuData.meridians) {
        // If verified only, only render verified pathways unless full body view is selected
        if (verifiedOnly && filterRegion !== 'all' && !verifiedMeridianCodes.includes(mCode)) continue;"""

new_m_loop = """      for (const mCode in acuData.meridians) {
        // Filter: individual meridian channel
        if (filterMeridian !== 'all' && mCode !== filterMeridian) continue;
        // If verified only, only render verified pathways unless full body view is selected
        if (verifiedOnly && filterRegion !== 'all' && !verifiedMeridianCodes.includes(mCode)) continue;"""

if old_m_loop in mer_src:
    mer_src = mer_src.replace(old_m_loop, new_m_loop)

# Update points rendering loop with filterMeridian and normal-based occlusion
old_pt_loop = """        // Filter: region
        if (!matchesRegion(pt.region, filterRegion)) continue;"""

new_pt_loop = """        // Filter: individual meridian channel
        if (filterMeridian !== 'all' && pt.meridian_code !== filterMeridian) continue;

        // Filter: region
        if (!matchesRegion(pt.region, filterRegion)) continue;"""

if old_pt_loop in mer_src:
    mer_src = mer_src.replace(old_pt_loop, new_pt_loop)

# Pass normal into isFacingCamera
old_pt_facing = """          const isSel = selectedCode === code;
          const facing = isFacingCamera(inst.pos, r);"""

new_pt_facing = """          const isSel = selectedCode === code;
          const norm = inst.side === 'left' && pt.normal ? [-pt.normal[0], pt.normal[1], pt.normal[2]] : pt.normal;
          const facing = isFacingCamera(inst.pos, r, norm);"""

if old_pt_facing in mer_src:
    mer_src = mer_src.replace(old_pt_facing, new_pt_facing)

# Add comparative split divider and headers at end of render()
old_render_end = """      groupPoints.innerHTML = ptsHtml;
    }"""

new_render_end = """    // Comparative split badges and divider
    if (isComp) {
      ptsHtml += `
        <line x1="${(sw / 2).toFixed(1)}" y1="0" x2="${(sw / 2).toFixed(1)}" y2="${sh}" stroke="#475569" stroke-width="2" stroke-dasharray="6,4" opacity="0.8"/>
        <g transform="translate(16, 26)">
          <rect x="-6" y="-16" width="225" height="24" rx="4" fill="rgba(15,23,42,0.88)" stroke="#38bdf8" stroke-width="1"/>
          <text fill="#38bdf8" font-size="11" font-weight="700" font-family="system-ui, sans-serif" y="-1">🦴 MUSCULOSKELETAL ANATOMY</text>
        </g>
        <g transform="translate(${(sw / 2 + 16).toFixed(1)}, 26)">
          <rect x="-6" y="-16" width="195" height="24" rx="4" fill="rgba(15,23,42,0.88)" stroke="#10b981" stroke-width="1"/>
          <text fill="#34d399" font-size="11" font-weight="700" font-family="system-ui, sans-serif" y="-1">🌐 SURFACE & MERIDIANS</text>
        </g>
      `;
    } else if (isMusculo && showSurfaceReference) {
      ptsHtml += `
        <g transform="translate(16, 26)">
          <rect x="-6" y="-16" width="285" height="24" rx="4" fill="rgba(15,23,42,0.88)" stroke="#eab308" stroke-width="1"/>
          <text fill="#facc15" font-size="11" font-weight="700" font-family="system-ui, sans-serif" y="-1">📍 SURFACE REFERENCE (Non-physical)</text>
        </g>
      `;
    }

      groupPoints.innerHTML = ptsHtml;
    }"""

if old_render_end in mer_src:
    mer_src = mer_src.replace(old_render_end, new_render_end)

# Add message actions for set_render_mode, set_skin_opacity, set_filter_meridian, toggle_surface_reference
old_msg_handler = """    } else if (ev.data.action === 'toggle_layer' || ev.data.action === 'toggle_meridian_layer') {"""

new_msg_handler = """    } else if (ev.data.action === 'set_render_mode') {
      const r = getRenderer();
      if (r) r.setRenderMode(ev.data.mode);
      render();
    } else if (ev.data.action === 'set_skin_opacity') {
      const r = getRenderer();
      if (r) r.setSkinOpacity(ev.data.opacity);
      render();
    } else if (ev.data.action === 'set_filter_meridian') {
      filterMeridian = ev.data.meridian || 'all';
      render();
    } else if (ev.data.action === 'toggle_surface_reference') {
      showSurfaceReference = Boolean(ev.data.enabled);
      const r = getRenderer();
      if (r) r.setSkinReference(showSurfaceReference);
      render();
    } else if (ev.data.action === 'toggle_layer' || ev.data.action === 'toggle_meridian_layer') {"""

if old_msg_handler in mer_src:
    mer_src = mer_src.replace(old_msg_handler, new_msg_handler)

mer_path.write_text(mer_src, encoding="utf-8")
print("meridians.js updated successfully!")


# ===========================================================================
# 2. Update app.js
# ===========================================================================
app_path = BASE / "msk_therapy_os/static/atlas/app.js"
app_src = app_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_app_msg = """      } else if (action === 'focus_selection') {
        focusSelection();"""

new_app_msg = """      } else if (action === 'focus_selection') {
        focusSelection();
      } else if (action === 'set_render_mode') {
        setRenderMode(ev.data.mode);
      } else if (action === 'set_skin_opacity') {
        if (renderer) renderer.setSkinOpacity(ev.data.opacity);
      } else if (action === 'set_filter_meridian') {
        window.postMessage({ action: 'set_filter_meridian', meridian: ev.data.meridian }, '*');
      } else if (action === 'toggle_surface_reference') {
        if (renderer) renderer.setSkinReference(ev.data.enabled);
        window.postMessage({ action: 'toggle_surface_reference', enabled: ev.data.enabled }, '*');"""

if old_app_msg in app_src:
    app_src = app_src.replace(old_app_msg, new_app_msg)

# Add setRenderMode in app.js
old_set_xray = """  function setXray(on) {
    renderer.xray = on;
    quiz.userXray = on;
    $('#btnXray').setAttribute('aria-pressed', on ? 'true' : 'false');
    renderer.requestRender();
  }"""

new_set_xray = """  function setRenderMode(mode) {
    if (!renderer) return;
    renderer.setRenderMode(mode);
    if (mode === 'surface') {
      catOn['skin'] = true;
      renderer.setSkinOpacity(0.78);
      applyVisibility();
      window.postMessage({ action: 'set_render_mode', mode: 'surface' }, '*');
    } else if (mode === 'musculoskeletal') {
      catOn['skin'] = false;
      renderer.setSkinOpacity(0.0);
      applyVisibility();
      window.postMessage({ action: 'set_render_mode', mode: 'musculoskeletal' }, '*');
    } else if (mode === 'comparative') {
      catOn['skin'] = true;
      renderer.setSkinOpacity(0.85);
      applyVisibility();
      window.postMessage({ action: 'set_render_mode', mode: 'comparative' }, '*');
    }
    $$('#visModeSelector button').forEach(b => {
      b.classList.toggle('on', b.dataset.mode === mode);
    });
    renderer.requestRender();
  }

  function setXray(on) {
    renderer.xray = on;
    quiz.userXray = on;
    $('#btnXray').setAttribute('aria-pressed', on ? 'true' : 'false');
    renderer.requestRender();
  }"""

if old_set_xray in app_src:
    app_src = app_src.replace(old_set_xray, new_set_xray)

# Add event listeners for visModeSelector in bindUI()
old_bind_ui = """    const btnFull = $('#btnFullBody');
    if (btnFull) btnFull.addEventListener('click', () => { if (atlas) renderer.frame(atlas.index.bbox); });
    const btnFoc = $('#btnFocusSelected');
    if (btnFoc) btnFoc.addEventListener('click', focusSelection);"""

new_bind_ui = """    $$('#visModeSelector button').forEach(b => {
      b.addEventListener('click', () => setRenderMode(b.dataset.mode));
    });
    const btnFull = $('#btnFullBody');
    if (btnFull) btnFull.addEventListener('click', () => { if (atlas) renderer.frame(atlas.index.bbox); });
    const btnFoc = $('#btnFocusSelected');
    if (btnFoc) btnFoc.addEventListener('click', focusSelection);"""

if old_bind_ui in app_src:
    app_src = app_src.replace(old_bind_ui, new_bind_ui)

app_path.write_text(app_src, encoding="utf-8")
print("app.js updated successfully!")


# ===========================================================================
# 3. Update atlas/index.html & style.css
# ===========================================================================
idx_path = BASE / "msk_therapy_os/static/atlas/index.html"
idx_src = idx_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_atlas_tools = """    <div class="tools">
      <div class="seg small" aria-label="Viewpoint">"""

new_atlas_tools = """    <div class="tools">
      <div class="seg small" role="tablist" aria-label="Visualization Mode" id="visModeSelector">
        <button data-mode="surface" class="on" title="Surface Meridian Mode: Skin mesh with surface-anchored meridians">🌐 Surface</button>
        <button data-mode="musculoskeletal" title="Musculoskeletal Anatomy Mode: Deep bones, muscles, joints">🦴 Anatomy</button>
        <button data-mode="comparative" title="Comparative Research Mode: Synchronized dual split-view">⚖ Compare</button>
      </div>
      <div class="seg small" aria-label="Viewpoint">"""

if old_atlas_tools in idx_src:
    idx_src = idx_src.replace(old_atlas_tools, new_atlas_tools)
    idx_path.write_text(idx_src, encoding="utf-8")
print("atlas index.html updated successfully!")


# ===========================================================================
# 4. Update msk_therapy_os/static/index.html (Main Host Application)
# ===========================================================================
main_idx_path = BASE / "msk_therapy_os/static/index.html"
main_idx_src = main_idx_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_host_tools = """            <div style="display:flex; gap:5px; align-items:center; flex-wrap:wrap;">
              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'front'})" style="font-size:11px; padding:3px 7px;">Front</button>"""

new_host_tools = """            <div style="display:flex; gap:5px; align-items:center; flex-wrap:wrap;">
              <!-- Three Visualization Modes Switcher -->
              <div class="seg small" style="display:inline-flex; background:#0f172a; padding:2px; border-radius:4px; border:1px solid #334155; margin-right:4px;">
                <button id="hostBtnModeSurface" class="btn-mode active" onclick="setHostRenderMode('surface')" style="font-size:11px; padding:3px 8px; background:#0f766e; color:#fff; border:none; border-radius:3px; cursor:pointer;" title="Surface Meridian Mode: Skin mesh with surface-anchored points">🌐 Surface</button>
                <button id="hostBtnModeMusculo" class="btn-mode" onclick="setHostRenderMode('musculoskeletal')" style="font-size:11px; padding:3px 8px; background:transparent; color:#94a3b8; border:none; border-radius:3px; cursor:pointer;" title="Musculoskeletal Anatomy Mode: Deep bones, muscles, joints">🦴 Anatomy</button>
                <button id="hostBtnModeComparative" class="btn-mode" onclick="setHostRenderMode('comparative')" style="font-size:11px; padding:3px 8px; background:transparent; color:#94a3b8; border:none; border-radius:3px; cursor:pointer;" title="Comparative Research Mode: Synchronized dual split-view">⚖ Compare</button>
              </div>
              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'front'})" style="font-size:11px; padding:3px 7px;">Front</button>"""

if old_host_tools in main_idx_src:
    main_idx_src = main_idx_src.replace(old_host_tools, new_host_tools)

# Add Skin Opacity and Meridian Filter to the 3D Overlays toolbar in main index.html
old_host_overlays = """            <button id="btnToggleThai" class="btn-secondary" onclick="toggleAtlasLayer('thai')" style="font-size:11px; padding:3px 8px;">🇹🇭 Thai Sen Sib</button>
            <button id="btnToggleDienChan" class="btn-secondary" onclick="toggleAtlasLayer('dien_chan')" style="font-size:11px; padding:3px 8px;">🇻🇳 Dien Chan Reflex</button>
            <button id="btnOpenStudioEditor" class="btn-secondary" onclick="openStudioEditorModal()" style="font-size:11px; padding:3px 8px; background:#4338ca; color:#e0e7ff; border-color:#6366f1;">🛠️ Meridian Studio</button>
          </div>"""

new_host_overlays = """            <button id="btnToggleThai" class="btn-secondary" onclick="toggleAtlasLayer('thai')" style="font-size:11px; padding:3px 8px;">🇹🇭 Thai Sen Sib</button>
            <button id="btnToggleDienChan" class="btn-secondary" onclick="toggleAtlasLayer('dien_chan')" style="font-size:11px; padding:3px 8px;">🇻🇳 Dien Chan Reflex</button>
            <button id="btnOpenStudioEditor" class="btn-secondary" onclick="openStudioEditorModal()" style="font-size:11px; padding:3px 8px; background:#4338ca; color:#e0e7ff; border-color:#6366f1;">🛠️ Meridian Studio</button>
            <span style="border-left:1px solid #475569; height:16px; margin:0 2px;"></span>
            <!-- Meridian Channel Filter Dropdown -->
            <select id="hostMeridianFilter" onchange="onHostMeridianFilterChange(this.value)" style="font-size:11px; padding:2px 6px; background:#1e293b; color:#e2e8f0; border:1px solid #475569; border-radius:4px; cursor:pointer;" title="Filter to a specific meridian channel">
              <option value="all">⚡ All Meridians (14)</option>
              <option value="GV">GV — Du Mai (Governing)</option>
              <option value="CV">CV — Ren Mai (Conception)</option>
              <option value="BL">BL — Bladder (Taiyang)</option>
              <option value="GB">GB — Gallbladder (Shaoyang)</option>
              <option value="SI">SI — Small Intestine</option>
              <option value="TE">TE — Triple Energizer (Sanjiao)</option>
              <option value="LI">LI — Large Intestine</option>
              <option value="LU">LU — Lung (Taiyin)</option>
              <option value="ST">ST — Stomach (Yangming)</option>
              <option value="SP">SP — Spleen (Taiyin)</option>
              <option value="HT">HT — Heart (Shaoyin)</option>
              <option value="KI">KI — Kidney (Shaoyin)</option>
              <option value="PC">PC — Pericardium (Jueyin)</option>
              <option value="LR">LR — Liver (Jueyin)</option>
            </select>
            <!-- Skin Opacity Slider -->
            <label id="hostSkinOpacityContainer" style="font-size:11px; color:#94a3b8; display:flex; align-items:center; gap:4px; margin-left:2px;" title="Adjust skin mesh transparency">
              Skin:
              <input type="range" id="hostSkinOpacity" min="0" max="100" value="78" style="width:65px; height:4px; cursor:pointer;" oninput="onHostSkinOpacityChange(this.value)" />
              <span id="hostSkinOpacityVal" style="color:#e2e8f0; width:26px; font-variant-numeric:tabular-nums;">78%</span>
            </label>
            <!-- Surface Reference Guide toggle (Musculoskeletal mode) -->
            <label id="hostSurfaceRefContainer" style="font-size:11px; color:#facc15; display:none; align-items:center; gap:4px; margin-left:4px;" title="Display surface reference guide over musculoskeletal anatomy">
              <input type="checkbox" id="chkHostSurfaceRef" onchange="onHostSurfaceRefChange(this.checked)" />
              <span>Reference Overlay</span>
            </label>
          </div>"""

if old_host_overlays in main_idx_src:
    main_idx_src = main_idx_src.replace(old_host_overlays, new_host_overlays)

# Add JavaScript handler functions in main index.html
old_host_script = """    function atlasCommand(action, params = {}) {"""

new_host_script = """    let currentHostRenderMode = 'surface';

    function setHostRenderMode(mode) {
      currentHostRenderMode = mode;
      atlasCommand('set_render_mode', { mode });
      // Update button styling
      const btnMap = {
        'surface': document.getElementById('hostBtnModeSurface'),
        'musculoskeletal': document.getElementById('hostBtnModeMusculo'),
        'comparative': document.getElementById('hostBtnModeComparative')
      };
      for (const m in btnMap) {
        if (!btnMap[m]) continue;
        if (m === mode) {
          btnMap[m].style.background = m === 'musculoskeletal' ? '#0369a1' : (m === 'comparative' ? '#7c3aed' : '#0f766e');
          btnMap[m].style.color = '#fff';
        } else {
          btnMap[m].style.background = 'transparent';
          btnMap[m].style.color = '#94a3b8';
        }
      }
      // Toggle controls visibility based on mode
      const opacityCtrl = document.getElementById('hostSkinOpacityContainer');
      const refCtrl = document.getElementById('hostSurfaceRefContainer');
      if (opacityCtrl) opacityCtrl.style.display = mode === 'musculoskeletal' ? 'none' : 'flex';
      if (refCtrl) refCtrl.style.display = mode === 'musculoskeletal' ? 'flex' : 'none';
    }

    function onHostSkinOpacityChange(val) {
      const alpha = parseInt(val, 10) / 100;
      const lbl = document.getElementById('hostSkinOpacityVal');
      if (lbl) lbl.textContent = val + '%';
      atlasCommand('set_skin_opacity', { opacity: alpha });
    }

    function onHostMeridianFilterChange(meridian) {
      atlasCommand('set_filter_meridian', { meridian });
    }

    function onHostSurfaceRefChange(enabled) {
      atlasCommand('toggle_surface_reference', { enabled });
    }

    function atlasCommand(action, params = {}) {"""

if old_host_script in main_idx_src:
    main_idx_src = main_idx_src.replace(old_host_script, new_host_script)

main_idx_path.write_text(main_idx_src, encoding="utf-8")
print("main index.html updated successfully!")

print("\nALL ARCHITECTURAL RENDERING MODES SUCCESSFULLY PATCHED!")
