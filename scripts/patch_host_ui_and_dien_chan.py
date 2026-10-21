from pathlib import Path

index_html_path = Path("msk_therapy_os/static/index.html")
html = index_html_path.read_text(encoding="utf-8")

# 1. Update Thai and Dien Chan button titles and badges
old_buttons = """            <button id="btnToggleThai" class="btn-secondary" onclick="toggleAtlasLayer('thai')" style="font-size:11px; padding:3px 8px;">🇹🇭 Thai Sen Sib</button>
            <button id="btnToggleDienChan" class="btn-secondary" onclick="toggleAtlasLayer('dien_chan')" style="font-size:11px; padding:3px 8px;">🇻🇳 Dien Chan Reflex</button>"""

new_buttons = """            <button id="btnToggleThai" class="btn-secondary" onclick="toggleAtlasLayer('thai')" style="font-size:11px; padding:3px 8px;" title="Thai Sen Sib: 3 lines loaded (Sen Ittha, Sen Pingkhla, Sen Sumana) — Incomplete educational dataset (3 of 10 lines)">🇹🇭 Thai Sen Sib <span style="font-size:9px; opacity:0.85; background:#78350f; color:#fde68a; padding:1px 4px; border-radius:3px; margin-left:2px;">3 lines</span></button>
            <button id="btnToggleDienChan" class="btn-secondary" onclick="toggleAtlasLayer('dien_chan')" style="font-size:11px; padding:3px 8px;" title="Vietnamese Dien Chan: 4 facial reflex points — Incomplete educational dataset (Reflexology/Non-WHO)">🇻🇳 Dien Chan Reflex <span style="font-size:9px; opacity:0.85; background:#831843; color:#fbcfe8; padding:1px 4px; border-radius:3px; margin-left:2px;">4 pts</span></button>"""

assert old_buttons in html, "old_buttons not found in index.html"
html = html.replace(old_buttons, new_buttons, 1)

# 2. Add #atlasDienChanCard HTML right after #atlasAcupointCard
old_after_acu = """            <div style="display:flex; gap:8px;">
              <button onclick="addAcupointToObservation()" style="font-size:11px; padding:4px 10px; background:#0f766e; color:#fff;">+ Add to Observations</button>
              <button onclick="addAcupointToSOAP()" style="font-size:11px; padding:4px 10px; background:#0284c7; color:#fff;">+ Add to SOAP Note</button>
              <button onclick="openStudioEditorModal(lastSelectedAcupoint)" style="font-size:11px; padding:4px 10px; background:#4338ca; color:#e0e7ff; border:1px solid #6366f1;">🛠️ Calibrate in Studio</button>
            </div>
          </div>

          <!-- Selected 3D Structure Interactive Banner -->"""

dien_chan_card_html = """            <div style="display:flex; gap:8px;">
              <button onclick="addAcupointToObservation()" style="font-size:11px; padding:4px 10px; background:#0f766e; color:#fff;">+ Add to Observations</button>
              <button onclick="addAcupointToSOAP()" style="font-size:11px; padding:4px 10px; background:#0284c7; color:#fff;">+ Add to SOAP Note</button>
              <button onclick="openStudioEditorModal(lastSelectedAcupoint)" style="font-size:11px; padding:4px 10px; background:#4338ca; color:#e0e7ff; border:1px solid #6366f1;">🛠️ Calibrate in Studio</button>
            </div>
          </div>

          <!-- Selected Dien Chan Reflex Point Interactive Banner (Requirement C) -->
          <div id="atlasDienChanCard" class="card" style="display:none; border-color:#ec4899; background:rgba(30,27,75,0.95); margin-bottom:14px;">
            <div class="card-title">
              <span style="color:#f472b6; font-weight:700;">Selected Vietnamese Dien Chan Reflex</span>
              <span class="badge" style="background:#831843; color:#fbcfe8; border:1px solid #db2777;">Non-WHO Traditional Reflex</span>
            </div>
            <div style="font-size:16px; font-weight:700; color:#fff; margin-bottom:2px;" id="dcPointTitle"></div>
            <div style="font-size:11px; color:#cbd5e1; margin-bottom:6px;">
              <span style="color:#f472b6; font-weight:600;">Domain:</span> Bùi Quốc Châu Facial Reflexology (1980) • <span style="color:#fbbf24; font-weight:600;">Dataset Scope:</span> 4 available records — incomplete educational dataset
            </div>
            <div style="background:rgba(217,119,6,0.15); border-left:3px solid #f59e0b; padding:6px 10px; border-radius:3px; margin-bottom:8px; font-size:11px; color:#fde68a; line-height:1.4;">
              <strong>⚠️ Educational & Traditional Scope Notice:</strong> Facial reflex points are traditional somatotopic projections. They are not peripheral acupuncture points and must not be classified under WHO standards. Coordinates are unverified approximations.
            </div>
            <div style="display:grid; grid-template-columns: 1fr; gap:6px; font-size:12px; line-height:1.4; margin-bottom:8px;">
              <div><strong style="color:var(--text);">Target MSK Region:</strong> <span id="dcTargetRegion" style="color:#38bdf8; font-weight:600;"></span></div>
              <div><strong style="color:var(--text);">Clinical Indication:</strong> <span id="dcIndication" style="color:var(--text-muted);"></span></div>
              <div><strong style="color:var(--text);">Geometry Status:</strong> <span class="badge" style="background:#0e7490; color:#cffafe; font-size:10px;">SURFACE_REGISTERED_FACIAL_FJ2810</span></div>
              <div><strong style="color:var(--text);">Clinical Review Status:</strong> <span class="badge" style="background:#7f1d1d; color:#fca5a5; font-size:10px;">UNVERIFIED (Traditional Reflex)</span></div>
            </div>
            <div style="display:flex; gap:8px;">
              <button onclick="addDienChanToObservation()" style="font-size:11px; padding:4px 10px; background:#0f766e; color:#fff;">+ Add to Observations</button>
              <button onclick="addDienChanToSOAP()" style="font-size:11px; padding:4px 10px; background:#0284c7; color:#fff;">+ Add to SOAP Note</button>
              <button onclick="clearAtlasInspector()" class="btn-secondary" style="font-size:11px; padding:4px 10px;">Close</button>
            </div>
          </div>

          <!-- Selected 3D Structure Interactive Banner -->"""

assert old_after_acu in html, "old_after_acu not found in index.html"
html = html.replace(old_after_acu, dien_chan_card_html, 1)

# 3. Update JavaScript event listeners and command handling
old_js_bridge = """    let lastSelectedStructure = null;
    let lastSelectedAcupoint = null;
    let layerStates = { points: false, meridians: false, verified_only: true, thai: false, dien_chan: false };

    // MSK 3D Atlas Communication Bridge
    window.addEventListener("message", (ev) => {
      if (!ev.data || typeof ev.data !== "object") return;
      if (ev.data.type === "msk_structure_selected") {
        const { name, fmaId, category } = ev.data;
        showAtlasSelection(name, fmaId, category);
      } else if (ev.data.type === "msk_acupoint_selected") {
        showAtlasAcupoint(ev.data.point);
      } else if (ev.data.type === "msk_selection_cleared") {
        clearAtlasInspector();
      } else if (ev.data.type === "msk_atlas_ready") {
        const overlay = document.getElementById("atlasLoadingOverlay");
        if (overlay) { overlay.style.opacity = "0"; setTimeout(() => overlay.style.display = "none", 400); }
      }
    });

    function clearAtlasInspector() {
      lastSelectedStructure = null;
      lastSelectedAcupoint = null;
      const bStruct = document.getElementById("atlasSelectionCard");
      if (bStruct) bStruct.style.display = "none";
      const bAcu = document.getElementById("atlasAcupointCard");
      if (bAcu) bAcu.style.display = "none";
      const hint = document.getElementById("atlasNoSelectionHint");
      if (hint) hint.style.display = "block";
    }"""

new_js_bridge = """    let lastSelectedStructure = null;
    let lastSelectedAcupoint = null;
    let lastSelectedDienChan = null;
    let layerStates = { points: false, meridians: false, verified_only: true, thai: false, dien_chan: false };
    let isAtlasReady = false;
    let queuedAtlasCommands = [];

    // MSK 3D Atlas Communication Bridge & State Handshake
    window.addEventListener("message", (ev) => {
      if (!ev.data || typeof ev.data !== "object") return;
      if (ev.data.type === "msk_structure_selected") {
        const { name, fmaId, category } = ev.data;
        showAtlasSelection(name, fmaId, category);
      } else if (ev.data.type === "msk_acupoint_selected") {
        showAtlasAcupoint(ev.data.point);
      } else if (ev.data.type === "msk_dien_chan_selected") {
        showAtlasDienChan(ev.data.point);
      } else if (ev.data.type === "msk_selection_cleared") {
        clearAtlasInspector();
      } else if (ev.data.type === "msk_atlas_ready") {
        isAtlasReady = true;
        const overlay = document.getElementById("atlasLoadingOverlay");
        if (overlay) { overlay.style.opacity = "0"; setTimeout(() => overlay.style.display = "none", 400); }
        // Flush queued commands
        while (queuedAtlasCommands.length > 0) {
          const cmd = queuedAtlasCommands.shift();
          const f = document.getElementById("atlasFrame");
          if (f && f.contentWindow) f.contentWindow.postMessage(cmd, "*");
        }
      } else if (ev.data.type === "msk_ack") {
        // State synchronization confirmation from atlas engine
        if (ev.data.action === "set_skin_opacity") {
          const lbl = document.getElementById("hostSkinOpacityVal");
          if (lbl) lbl.textContent = Math.round(ev.data.opacity * 100) + "%";
        } else if (ev.data.action === "set_filter_meridian") {
          if (ev.data.showMeridians) {
            layerStates.meridians = true;
            const b = document.getElementById("btnToggleMeridians");
            if (b) { b.classList.add("active"); b.style.borderColor = "var(--primary)"; }
          }
        }
      }
    });

    function clearAtlasInspector() {
      lastSelectedStructure = null;
      lastSelectedAcupoint = null;
      lastSelectedDienChan = null;
      const bStruct = document.getElementById("atlasSelectionCard");
      if (bStruct) bStruct.style.display = "none";
      const bAcu = document.getElementById("atlasAcupointCard");
      if (bAcu) bAcu.style.display = "none";
      const bDc = document.getElementById("atlasDienChanCard");
      if (bDc) bDc.style.display = "none";
      const hint = document.getElementById("atlasNoSelectionHint");
      if (hint) hint.style.display = "block";
    }

    function showAtlasDienChan(pt) {
      lastSelectedDienChan = pt;
      lastSelectedAcupoint = null;
      lastSelectedStructure = null;

      const card = document.getElementById("atlasDienChanCard");
      if (!card) return;
      card.style.display = "block";
      const bStruct = document.getElementById("atlasSelectionCard");
      if (bStruct) bStruct.style.display = "none";
      const bAcu = document.getElementById("atlasAcupointCard");
      if (bAcu) bAcu.style.display = "none";
      const hint = document.getElementById("atlasNoSelectionHint");
      if (hint) hint.style.display = "none";

      document.getElementById("dcPointTitle").textContent = `${pt.name} (${pt.code})`;
      document.getElementById("dcTargetRegion").textContent = (pt.target_region || 'cervical').toUpperCase();
      document.getElementById("dcIndication").textContent = pt.indication || 'Traditional somatotopic facial reflex projection';
    }

    function addDienChanToSOAP() {
      if (!lastSelectedDienChan) return;
      const pt = lastSelectedDienChan;
      const txt = `[Vietnamese Dien Chan Reflexology] Examined ${pt.name} (${pt.code}) - Somatotopic facial reflex for ${pt.target_region}. Indication: ${pt.indication}. Note: Traditional non-anatomical reflex projection (Unverified clinical evidence).\n`;
      const oArea = document.getElementById("soapO");
      if (oArea) {
        oArea.value = (oArea.value ? oArea.value + "\\n" : "") + txt;
        showToast(`Dien Chan reflex point ${pt.code} added to SOAP Objective.`, "success");
      }
    }

    function addDienChanToObservation() {
      if (!lastSelectedDienChan) return;
      const pt = lastSelectedDienChan;
      const structInput = document.getElementById("obsStructureId");
      const findInput = document.getElementById("obsFinding");
      const interpInput = document.getElementById("obsInterpretation");
      if (structInput) structInput.value = pt.code;
      if (findInput) findInput.value = `Facial sensitivity / hyper-reactive zone at ${pt.name} (${pt.code}).`;
      if (interpInput) interpInput.value = `Traditional reflex projection correlated with ${pt.target_region} tension.`;
      const tabCase = document.querySelector('button.tab-btn[data-tab="tab-case"]');
      if (tabCase) tabCase.click();
      const obsBox = document.getElementById("newObservationFormBox");
      if (obsBox) obsBox.style.display = "block";
      showToast(`Dien Chan ${pt.code} pre-populated into Observation form.`, "info");
    }"""

assert old_js_bridge in html, "old_js_bridge not found in index.html"
html = html.replace(old_js_bridge, new_js_bridge, 1)

# 4. Update onHostMeridianFilterChange and atlasCommand
old_filter_cmd = """    function onHostMeridianFilterChange(meridian) {
      atlasCommand('set_filter_meridian', { meridian });
    }

    function onHostSurfaceRefChange(enabled) {
      atlasCommand('toggle_surface_reference', { enabled });
    }

    function atlasCommand(action, params = {}) {
      const f = document.getElementById("atlasFrame");
      if (f && f.contentWindow) {
        f.contentWindow.postMessage({ action, ...params }, "*");
      }
      if (action === "reset_view" || action === "clear_selection") {
        clearAtlasInspector();
      }
    }"""

new_filter_cmd = """    function onHostMeridianFilterChange(meridian) {
      if (meridian !== 'all') {
        // Auto-enable meridian and points layers in host UI state
        layerStates.meridians = true;
        layerStates.points = true;
        const bM = document.getElementById('btnToggleMeridians');
        if (bM) { bM.classList.add('active'); bM.style.borderColor = 'var(--primary)'; }
        const bP = document.getElementById('btnToggleAcupoints');
        if (bP) { bP.classList.add('active'); bP.style.borderColor = 'var(--primary)'; }
      }
      atlasCommand('set_filter_meridian', { meridian });
    }

    function onHostSurfaceRefChange(enabled) {
      atlasCommand('toggle_surface_reference', { enabled });
    }

    function atlasCommand(action, params = {}) {
      const requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
      const msg = { action, ...params, requestId };
      const f = document.getElementById("atlasFrame");
      if (!isAtlasReady || !f || !f.contentWindow) {
        queuedAtlasCommands.push(msg);
      } else {
        f.contentWindow.postMessage(msg, "*");
      }
      if (action === "reset_view" || action === "clear_selection") {
        clearAtlasInspector();
      }
      return requestId;
    }"""

assert old_filter_cmd in html, "old_filter_cmd not found in index.html"
html = html.replace(old_filter_cmd, new_filter_cmd, 1)

index_html_path.write_text(html, encoding="utf-8")
print("✓ index.html patched successfully with Dien Chan card, badges, and state handshake")
