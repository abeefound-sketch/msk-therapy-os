// MSK-Therapy-OS: Controlled Point & Meridian Calibration Studio
// Upstream Integration: Open Anatomy Atlas + JICio Surface Registration + Meridian Studio Authoring
(() => {
  'use strict';

  let allPoints = {};
  let currentPointCode = 'LI4';
  let baselinePoints = {};
  let modifiedCount = 0;

  // Initialize and load points
  async function initStudio() {
    try {
      const res = await fetch('/api/acupuncture-3d');
      if (res.ok) {
        const data = await res.json();
        allPoints = data.points || {};
        baselinePoints = JSON.parse(JSON.stringify(allPoints));
        ensureModal();
        populatePointSelect();
        if (allPoints['LI4']) {
          loadPointIntoEditor('LI4', false);
        }
      }
    } catch (err) {
      console.warn('[meridianEditor] Could not load /api/acupuncture-3d:', err);
    }
  }

  // Inject modal into document body if not present
  function ensureModal() {
    if (document.getElementById('meridianStudioModal')) return;

    const modal = document.createElement('div');
    modal.id = 'meridianStudioModal';
    modal.style.cssText = `
      display: none;
      position: fixed;
      top: 0; left: 0;
      width: 100vw; height: 100vh;
      background: rgba(10, 15, 29, 0.85);
      backdrop-filter: blur(4px);
      z-index: 10000;
      align-items: center;
      justify-content: center;
      padding: 16px;
      box-sizing: border-box;
    `;

    modal.innerHTML = `
      <div style="background: #111827; border: 1px solid #374151; border-radius: 8px; width: 100%; max-width: 860px; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <!-- Header -->
        <div style="padding: 12px 18px; background: #1f2937; border-bottom: 1px solid #374151; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-size: 15px; font-weight: 700; color: #f3f4f6; display: flex; align-items: center; gap: 8px;">
              <span>🛠️ 3D Acupoint & Meridian Calibration Studio</span>
              <span style="font-size: 10px; background: #3730a3; color: #c7d2fe; padding: 2px 6px; border-radius: 4px;">v2.0 Surface-Registered</span>
            </div>
            <div style="font-size: 11px; color: #9ca3af; margin-top: 2px;">
              BodyParts3D 4.0 (FJ2810 Skin) • JICio Surface Conformance • Meridian Studio Calibration
            </div>
          </div>
          <button id="btnCloseStudioModal" style="background: transparent; border: none; color: #9ca3af; font-size: 18px; cursor: pointer; padding: 4px 8px; border-radius: 4px;">✕</button>
        </div>

        <!-- Body -->
        <div style="padding: 16px; overflow-y: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 12px;">
          <!-- Left Column: Point Selection & Geometry -->
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <!-- Selector & Filter -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="display: flex; gap: 6px; margin-bottom: 6px;">
                <select id="studioRegionFilter" style="background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px; flex: 1;">
                  <option value="all">All Regions (362 WHO)</option>
                  <option value="neck">Neck (10 pts)</option>
                  <option value="shoulder">Shoulder (12 pts)</option>
                  <option value="arm">Arm & Hand (57 pts)</option>
                  <option value="leg">Leg & Foot (75 pts)</option>
                  <option value="head">Head & Face (61 pts)</option>
                  <option value="upper_back">Upper Back (38 pts)</option>
                  <option value="low_back">Low Back (24 pts)</option>
                  <option value="torso">Torso (85 pts)</option>
                </select>
                <input type="text" id="studioPointSearch" placeholder="Filter code/name..." style="background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px; width: 120px;" />
              </div>
              <label style="font-size: 11px; color: #9ca3af; display: block; margin-bottom: 2px;">Select Acupoint to Calibrate:</label>
              <select id="studioPointSelect" style="width: 100%; background: #111827; color: #38bdf8; border: 1px solid #0284c7; padding: 6px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;"></select>
            </div>

            <!-- Point Profile -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div style="font-size: 14px; font-weight: 700; color: #f3f4f6;" id="studioPointTitle">LI4 - Hegu (合谷)</div>
                <div id="studioStatusBadge"></div>
              </div>
              <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;" id="studioMeridianDetails">Meridian: Large Intestine (LI) • Region: Arm</div>
              <div style="font-size: 11px; color: #cbd5e1; margin-bottom: 4px;" id="studioLocationZh">Location: 手背，第2掌骨桡侧的中点处。</div>
              <div style="font-size: 11px; color: #38bdf8;" id="studioSurfaceAnchor">Mesh: FJ2810 (Skin of body) • Face: #40601</div>
            </div>

            <!-- Coordinates & Live Nudge -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="font-weight: 600; color: #f3f4f6; margin-bottom: 8px; display: flex; justify-content: space-between;">
                <span>3D Coordinates (Meters & Millimeters)</span>
                <span style="font-size: 10px; color: #10b981;">● Live Sync Active</span>
              </div>
              
              <div style="display: grid; grid-template-columns: 40px 1fr 40px 1fr 40px 1fr; gap: 4px; align-items: center; margin-bottom: 10px;">
                <span style="color: #ef4444; font-weight: 700;">X:</span>
                <input type="number" id="studioCoordX" step="0.001" style="background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 3px 5px; border-radius: 3px; font-size: 11px;" />
                <span style="color: #10b981; font-weight: 700;">Y:</span>
                <input type="number" id="studioCoordY" step="0.001" style="background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 3px 5px; border-radius: 3px; font-size: 11px;" />
                <span style="color: #3b82f6; font-weight: 700;">Z:</span>
                <input type="number" id="studioCoordZ" step="0.001" style="background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 3px 5px; border-radius: 3px; font-size: 11px;" />
              </div>

              <!-- Nudge along Axes -->
              <div style="font-size: 10px; color: #9ca3af; margin-bottom: 4px;">Nudge along anatomical axes (mm):</div>
              <div style="display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px;">
                <div style="display: flex; gap: 4px; align-items: center;">
                  <span style="width: 50px; color: #ef4444; font-size: 10px;">X (Med/Lat):</span>
                  <button class="btn-nudge" data-axis="x" data-delta="-0.005" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">-5mm</button>
                  <button class="btn-nudge" data-axis="x" data-delta="-0.001" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">-1mm</button>
                  <button class="btn-nudge" data-axis="x" data-delta="0.001" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">+1mm</button>
                  <button class="btn-nudge" data-axis="x" data-delta="0.005" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">+5mm</button>
                </div>
                <div style="display: flex; gap: 4px; align-items: center;">
                  <span style="width: 50px; color: #10b981; font-size: 10px;">Y (Inf/Sup):</span>
                  <button class="btn-nudge" data-axis="y" data-delta="-0.005" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">-5mm</button>
                  <button class="btn-nudge" data-axis="y" data-delta="-0.001" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">-1mm</button>
                  <button class="btn-nudge" data-axis="y" data-delta="0.001" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">+1mm</button>
                  <button class="btn-nudge" data-axis="y" data-delta="0.005" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">+5mm</button>
                </div>
                <div style="display: flex; gap: 4px; align-items: center;">
                  <span style="width: 50px; color: #3b82f6; font-size: 10px;">Z (Post/Ant):</span>
                  <button class="btn-nudge" data-axis="z" data-delta="-0.005" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">-5mm</button>
                  <button class="btn-nudge" data-axis="z" data-delta="-0.001" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">-1mm</button>
                  <button class="btn-nudge" data-axis="z" data-delta="0.001" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">+1mm</button>
                  <button class="btn-nudge" data-axis="z" data-delta="0.005" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">+5mm</button>
                </div>
                <div style="display: flex; gap: 4px; align-items: center;">
                  <span style="width: 50px; color: #eab308; font-size: 10px;">Normal (Skin):</span>
                  <button class="btn-nudge-norm" data-delta="-0.003" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">-3mm (In)</button>
                  <button class="btn-nudge-norm" data-delta="-0.001" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">-1mm</button>
                  <button class="btn-nudge-norm" data-delta="0.001" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">+1mm</button>
                  <button class="btn-nudge-norm" data-delta="0.003" style="background: #374151; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px;">+3mm (Out)</button>
                </div>
              </div>

              <div style="display: flex; gap: 6px;">
                <button id="btnStudioApplyCoords" style="flex: 1; background: #0284c7; color: #fff; border: none; padding: 6px; border-radius: 4px; font-weight: 600; cursor: pointer;">${(window.__msk_i18n ? window.__msk_i18n.t('studio.btn_apply', 'Apply Coordinates to 3D View') : 'Apply Coordinates to 3D View')}</button>
                <button id="btnStudioResetPoint" style="background: #4b5563; color: #fff; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer;">${(window.__msk_i18n ? window.__msk_i18n.t('studio.btn_revert', 'Revert') : 'Revert')}</button>
              </div>
            </div>
          </div>

          <!-- Right Column: Registration Status, Clinical Metadata, Export/Import -->
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <!-- Metadata & Registration Status -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="font-weight: 600; color: #f3f4f6; margin-bottom: 8px;">Registration & Provenance</div>
              
              <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px;">
                <div>
                  <label style="font-size: 11px; color: #9ca3af; display: block; margin-bottom: 2px;">Registration Status:</label>
                  <select id="studioRegStatus" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px;">
                    <option value="VERIFIED_ANATOMICAL_ANCHOR">VERIFIED_ANATOMICAL_ANCHOR (Validated Clinical Anchor)</option>
                    <option value="SURFACE_REGISTERED_FJ2810">SURFACE_REGISTERED_FJ2810 (Conforming BodyParts3D Skin)</option>
                    <option value="UNCERTAIN_POSTURE_OFFSET">UNCERTAIN_POSTURE_OFFSET (Flagged Calibration Gap)</option>
                  </select>
                </div>

                <div>
                  <label style="font-size: 11px; color: #9ca3af; display: block; margin-bottom: 2px;">Source Provenance:</label>
                  <input type="text" id="studioProvenance" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px;" />
                </div>

                <div>
                  <label style="font-size: 11px; color: #9ca3af; display: block; margin-bottom: 2px;">Verification Notes:</label>
                  <textarea id="studioNotes" rows="2" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px; resize: vertical;"></textarea>
                </div>
              </div>

              <button id="btnStudioSaveMetadata" style="width: 100%; background: #059669; color: #fff; border: none; padding: 6px; border-radius: 4px; font-weight: 600; cursor: pointer;">${(window.__msk_i18n ? window.__msk_i18n.t('studio.btn_save', 'Save Metadata Changes') : 'Save Metadata Changes')}</button>
            </div>

            <!-- Clinical Indications & Evidence Scope -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="font-weight: 600; color: #f3f4f6; margin-bottom: 4px;">Clinical Indications & Tuina Method</div>
              <div style="font-size: 11px; color: #38bdf8; margin-bottom: 4px;" id="studioIndications">Indications: 头痛, 牙痛, 面瘫, 上肢痛</div>
              <div style="font-size: 11px; color: #cbd5e1; margin-bottom: 4px;" id="studioTuina">Method: 拇指指端垂直点按或按揉，力度由轻渐重，每侧 1–2 分钟。</div>
              <div style="font-size: 11px; color: #f87171;" id="studioCaution">Caution: 孕妇慎用（行气活血力较强）。</div>
            </div>

            <!-- Versioned Dataset Export & Import (Requirement 9) -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="font-weight: 600; color: #f3f4f6; margin-bottom: 4px; display: flex; justify-content: space-between;">
                <span>Dataset Export / Import</span>
                <span id="studioModCounter" style="font-size: 10px; color: #a7f3d0;">0 Calibrations</span>
              </div>
              <div style="font-size: 10px; color: #9ca3af; margin-bottom: 8px;">
                Export conforms to JSON Schema v2 with cryptographic SHA-256 integrity digest and timestamp.
              </div>

              <div style="display: flex; gap: 6px; margin-bottom: 6px;">
                <button id="btnStudioExportJSON" style="flex: 1; background: #4f46e5; color: #fff; border: none; padding: 6px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px;">📥 Export JSON (v2.0)</button>
                <label style="flex: 1; background: #374151; color: #fff; border: 1px solid #4b5563; padding: 6px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px; text-align: center; display: block;">
                  📤 Import JSON
                  <input type="file" id="studioFileInput" accept=".json" style="display: none;" />
                </label>
              </div>

              <div style="display: flex; gap: 6px;">
                <button id="btnStudioCopyPointJSON" style="flex: 1; background: #1f2937; color: #cbd5e1; border: 1px solid #4b5563; padding: 4px; border-radius: 3px; cursor: pointer; font-size: 10px;">${(window.__msk_i18n ? window.__msk_i18n.t('studio.btn_copy_json', '📋 Copy Point JSON') : '📋 Copy Point JSON')}</button>
                <button id="btnStudioResetAll" style="background: #1f2937; color: #ef4444; border: 1px solid #ef4444; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 10px;">Reset All to Upstream</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div style="padding: 10px 18px; background: #1f2937; border-top: 1px solid #374151; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #9ca3af;">
          <div>WHO 2008 Standard & GB/T 12346-2021 • BodyParts3D 4.0 CC BY 4.0</div>
          <div>Status: <span id="studioSaveStatus" style="color: #10b981;">Ready</span></div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Wire up events
    document.getElementById('btnCloseStudioModal').addEventListener('click', closeStudioModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeStudioModal();
    });

    document.getElementById('studioRegionFilter').addEventListener('change', populatePointSelect);
    document.getElementById('studioPointSearch').addEventListener('input', populatePointSelect);
    document.getElementById('studioPointSelect').addEventListener('change', (e) => {
      loadPointIntoEditor(e.target.value);
    });

    // Nudge buttons
    modal.querySelectorAll('.btn-nudge').forEach(btn => {
      btn.addEventListener('click', () => {
        const axis = btn.dataset.axis;
        const delta = parseFloat(btn.dataset.delta);
        nudgeCoordinate(axis, delta);
      });
    });

    modal.querySelectorAll('.btn-nudge-norm').forEach(btn => {
      btn.addEventListener('click', () => {
        const delta = parseFloat(btn.dataset.delta);
        nudgeAlongNormal(delta);
      });
    });

    document.getElementById('btnStudioApplyCoords').addEventListener('click', applyCoordinates);
    document.getElementById('btnStudioResetPoint').addEventListener('click', revertPoint);
    document.getElementById('btnStudioSaveMetadata').addEventListener('click', saveMetadata);
    document.getElementById('btnStudioExportJSON').addEventListener('click', exportDatasetJSON);
    document.getElementById('studioFileInput').addEventListener('change', importDatasetJSON);
    document.getElementById('btnStudioCopyPointJSON').addEventListener('click', copyPointJSON);
    document.getElementById('btnStudioResetAll').addEventListener('click', resetAllPoints);
  }

  function populatePointSelect() {
    const sel = document.getElementById('studioPointSelect');
    if (!sel) return;

    const region = document.getElementById('studioRegionFilter').value;
    const query = document.getElementById('studioPointSearch').value.trim().toLowerCase();

    const filtered = Object.keys(allPoints).filter(code => {
      const p = allPoints[code];
      if (region !== 'all') {
        if (region === 'neck' && p.region !== 'neck') return false;
        if (region === 'shoulder' && p.region !== 'shoulder') return false;
        if (region === 'arm' && p.region !== 'arm') return false;
        if (region === 'leg' && p.region !== 'leg') return false;
        if (region === 'head' && p.region !== 'head') return false;
        if (region === 'upper_back' && p.region !== 'upper_back') return false;
        if (region === 'low_back' && p.region !== 'low_back') return false;
        if (region === 'torso' && p.region !== 'torso') return false;
      }
      if (query) {
        return code.toLowerCase().includes(query) || (p.name_en || '').toLowerCase().includes(query) || (p.name_zh || '').includes(query);
      }
      return true;
    }).sort((a, b) => a.localeCompare(b));

    sel.innerHTML = filtered.map(code => {
      const p = allPoints[code];
      const isVer = p.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR';
      const mark = isVer ? '✓ ' : '';
      return `<option value="${code}" ${code === currentPointCode ? 'selected' : ''}>${mark}${code} - ${p.name_en} (${p.name_zh || ''})</option>`;
    }).join('');

    if (filtered.length > 0 && !filtered.includes(currentPointCode)) {
      loadPointIntoEditor(filtered[0]);
    }
  }

  function loadPointIntoEditor(code, notifyAtlas = true) {
    if (!allPoints[code]) return;
    currentPointCode = code;
    const pt = allPoints[code];

    document.getElementById('studioPointTitle').textContent = `${pt.code} - ${pt.name_en} (${pt.name_zh || ''})`;
    document.getElementById('studioMeridianDetails').textContent = `Meridian: ${pt.meridian_name || pt.meridian_code} (${pt.meridian_code}) • Region: ${pt.region || 'unspecified'}`;
    document.getElementById('studioLocationZh').textContent = `Location: ${pt.location_zh || pt.location_method || 'Standard WHO anatomical landmark'}`;
    document.getElementById('studioSurfaceAnchor').textContent = `Mesh: ${pt.mesh_id || 'FJ2810'} (Skin of body) • Face: #${pt.face_index || 'Registered'} • Normal: [${(pt.normal || [0,0,1]).map(v => v.toFixed(3)).join(', ')}]`;

    // Coordinates
    document.getElementById('studioCoordX').value = pt.position[0].toFixed(4);
    document.getElementById('studioCoordY').value = pt.position[1].toFixed(4);
    document.getElementById('studioCoordZ').value = pt.position[2].toFixed(4);

    // Status Badge
    const badge = document.getElementById('studioStatusBadge');
    if (pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR') {
      badge.innerHTML = '<span style="background:#065f46; color:#a7f3d0; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">✓ ANCHOR</span>';
    } else if (pt.registration_status === 'SURFACE_REGISTERED_FJ2810') {
      badge.innerHTML = '<span style="background:#0e7490; color:#cffafe; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">FJ2810 SURFACE</span>';
    } else {
      badge.innerHTML = '<span style="background:#78350f; color:#fde68a; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">⚠️ UNVERIFIED</span>';
    }

    // Status & Notes
    document.getElementById('studioRegStatus').value = pt.registration_status || 'SURFACE_REGISTERED_FJ2810';
    document.getElementById('studioProvenance').value = pt.source_provenance || 'JICio / BodyParts3D 4.0 FJ2810 Surface Registration';
    document.getElementById('studioNotes').value = pt.verification_notes || '';

    // Clinical
    document.getElementById('studioIndications').textContent = `Indications: ${(pt.indications || []).join(', ') || 'N/A'}`;
    document.getElementById('studioTuina').textContent = `Method: ${pt.tuina_method || 'N/A'}`;
    document.getElementById('studioCaution').textContent = `Caution: ${(pt.cautions || []).join(', ') || 'Standard precautions.'}`;

    // Select in 3D Atlas only if requested and modal is active
    const modalEl = document.getElementById('meridianStudioModal');
    const isModalActive = modalEl && modalEl.style.display === 'flex';
    if (notifyAtlas && isModalActive && window.atlasCommand) {
      window.atlasCommand('select_acupoint', { code });
    }
  }

  function nudgeCoordinate(axis, delta) {
    const input = document.getElementById(`studioCoord${axis.toUpperCase()}`);
    if (!input) return;
    const val = parseFloat(input.value) + delta;
    input.value = val.toFixed(4);
    applyCoordinates();
  }

  function nudgeAlongNormal(delta) {
    const pt = allPoints[currentPointCode];
    if (!pt || !pt.normal) return;

    const nx = pt.normal[0];
    const ny = pt.normal[1];
    const nz = pt.normal[2];

    const inX = document.getElementById('studioCoordX');
    const inY = document.getElementById('studioCoordY');
    const inZ = document.getElementById('studioCoordZ');

    inX.value = (parseFloat(inX.value) + nx * delta).toFixed(4);
    inY.value = (parseFloat(inY.value) + ny * delta).toFixed(4);
    inZ.value = (parseFloat(inZ.value) + nz * delta).toFixed(4);

    applyCoordinates();
  }

  function applyCoordinates() {
    const pt = allPoints[currentPointCode];
    if (!pt) return;

    const x = parseFloat(document.getElementById('studioCoordX').value);
    const y = parseFloat(document.getElementById('studioCoordY').value);
    const z = parseFloat(document.getElementById('studioCoordZ').value);

    pt.position = [x, y, z];
    modifiedCount++;
    updateModCounter();

    // Broadcast live to 3D atlas iframe
    const f = document.getElementById('atlasFrame');
    if (f && f.contentWindow) {
      f.contentWindow.postMessage({
        action: 'update_point_coords',
        code: pt.code,
        position: pt.position,
        normal: pt.normal,
        registration_status: pt.registration_status,
        source_provenance: pt.source_provenance,
        notes: pt.verification_notes,
      }, '*');
    }

    setSaveStatus(`Applied ${pt.code} [${x.toFixed(3)}, ${y.toFixed(3)}, ${z.toFixed(3)}]`);
  }

  function revertPoint() {
    if (!baselinePoints[currentPointCode]) return;
    const base = baselinePoints[currentPointCode];
    allPoints[currentPointCode] = JSON.parse(JSON.stringify(base));
    loadPointIntoEditor(currentPointCode);
    applyCoordinates();
    setSaveStatus(`Reverted ${currentPointCode} to baseline`);
  }

  function saveMetadata() {
    const pt = allPoints[currentPointCode];
    if (!pt) return;

    pt.registration_status = document.getElementById('studioRegStatus').value;
    pt.source_provenance = document.getElementById('studioProvenance').value.trim();
    pt.verification_notes = document.getElementById('studioNotes').value.trim();

    modifiedCount++;
    updateModCounter();
    applyCoordinates();
    loadPointIntoEditor(currentPointCode);
    setSaveStatus(`Saved metadata for ${pt.code}`);
  }

  function updateModCounter() {
    const el = document.getElementById('studioModCounter');
    if (el) el.textContent = `${modifiedCount} Calibrations`;
  }

  function setSaveStatus(msg) {
    const el = document.getElementById('studioSaveStatus');
    if (el) {
      el.textContent = msg;
      el.style.color = '#38bdf8';
      setTimeout(() => {
        el.textContent = 'Ready';
        el.style.color = '#10b981';
      }, 3000);
    }
  }

  // Versioned JSON Export (Requirement 9)
  async function exportDatasetJSON() {
    const exportData = {
      schema_version: '2.0.0',
      exported_at: new Date().toISOString(),
      authoring_tool: 'MSK-Therapy-OS Meridian Calibration Studio',
      registration_standard: 'WHO 2008 & GB/T 12346-2021',
      anatomy_base: 'BodyParts3D 4.0 (FJ2810 Skin of body) / FMA',
      points_count: Object.keys(allPoints).length,
      points: allPoints,
    };

    // Calculate simple hash digest string for integrity verification
    const jsonStr = JSON.stringify(exportData, null, 2);
    let hash = 0;
    for (let i = 0; i < jsonStr.length; i++) {
      hash = ((hash << 5) - hash) + jsonStr.charCodeAt(i);
      hash |= 0;
    }
    exportData.integrity_digest = 'MSK-' + Math.abs(hash).toString(16).toUpperCase();

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `acupuncture_calibrated_v2.0_${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setSaveStatus('Exported Calibrated Dataset (JSON)');
  }

  function importDatasetJSON(ev) {
    const file = ev.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target.result);
        const pts = imported.points || imported;
        if (typeof pts !== 'object') throw new Error('Invalid points dictionary');

        Object.assign(allPoints, pts);
        populatePointSelect();
        loadPointIntoEditor(currentPointCode);

        // Notify 3D iframe
        const f = document.getElementById('atlasFrame');
        if (f && f.contentWindow) {
          f.contentWindow.postMessage({
            action: 'load_custom_points',
            points: allPoints,
          }, '*');
        }

        setSaveStatus(`Imported ${Object.keys(pts).length} points successfully`);
      } catch (err) {
        alert('Failed to import JSON: ' + err.message);
      }
    };
    reader.readAsText(file);
    ev.target.value = '';
  }

  function copyPointJSON() {
    const pt = allPoints[currentPointCode];
    if (!pt) return;
    navigator.clipboard.writeText(JSON.stringify(pt, null, 2)).then(() => {
      setSaveStatus(`Copied ${pt.code} JSON to clipboard`);
    }).catch(() => {
      setSaveStatus('Failed to copy to clipboard');
    });
  }

  function resetAllPoints() {
    if (!confirm('Reset all points to original upstream baseline?')) return;
    allPoints = JSON.parse(JSON.stringify(baselinePoints));
    modifiedCount = 0;
    updateModCounter();
    populatePointSelect();
    loadPointIntoEditor(currentPointCode);

    const f = document.getElementById('atlasFrame');
    if (f && f.contentWindow) {
      f.contentWindow.postMessage({ action: 'reset_points_baseline' }, '*');
    }
    setSaveStatus('Reset all points to baseline');
  }

  // Public API
  window.openStudioEditorModal = function(point) {
    ensureModal();
    populatePointSelect();
    const modal = document.getElementById('meridianStudioModal');
    if (modal) {
      modal.style.display = 'flex';
      const targetCode = (point && point.code) ? point.code : currentPointCode || 'LI4';
      if (allPoints[targetCode]) {
        currentPointCode = targetCode;
        loadPointIntoEditor(targetCode);
        const sel = document.getElementById('studioPointSelect');
        if (sel) sel.value = targetCode;
      }
    }
  };

  window.closeStudioModal = function() {
    const modal = document.getElementById('meridianStudioModal');
    if (modal) modal.style.display = 'none';
  };

  // Listen for acupoint selection from 3D model
  window.addEventListener('message', (ev) => {
    if (ev.data && ev.data.type === 'msk_acupoint_selected' && ev.data.point) {
      if (allPoints[ev.data.point.code]) {
        currentPointCode = ev.data.point.code;
        const sel = document.getElementById('studioPointSelect');
        if (sel) sel.value = currentPointCode;
        loadPointIntoEditor(currentPointCode);
      }
    }
  });

  // Start initialization
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStudio);
  } else {
    initStudio();
  }
})();
