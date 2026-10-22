"""
Complete precision patch script for M2.6 Adaptive Visualization & Smart Density
Updates:
1. msk_therapy_os/static/atlas/meridians.js
2. msk_therapy_os/static/index.html
"""
import re
from pathlib import Path

BASE_DIR = Path("D:/5Projects/msk-therapy-os")

ENGINE_CODE = '''
  // =========================================================================
  // M2.6: Visual Configuration, Scale Engine & Density Management
  // =========================================================================

  const STORAGE_KEY_DISPLAY = 'msk_atlas_display_settings';

  const DEFAULT_DISPLAY_SETTINGS = {
    scalingMode: 'auto',              // 'auto' | 'manual'
    markerSizeMultiplier: 1.0,        // 0.5 - 2.5 (in auto mode)
    markerSize: 3.0,                  // 1.0 - 8.0 px (in manual mode)
    meridianThicknessMultiplier: 1.0, // 0.5 - 2.5 (in auto mode)
    meridianThickness: 1.5,           // 0.5 - 4.5 px (in manual mode)
    labelDensity: 'auto',             // 'auto' | 'selected' | 'all' | 'none'
    smartDensity: true,               // true = cluster overlapping markers in screen-space
    channelEmphasis: 'all'            // 'all' or specific meridian code (e.g. 'GV', 'BL')
  };

  function loadDisplaySettings() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY_DISPLAY);
      if (raw) {
        const parsed = JSON.parse(raw);
        return Object.assign({}, DEFAULT_DISPLAY_SETTINGS, parsed);
      }
    } catch (e) {
      console.warn('[meridians.js] Failed to load display settings:', e);
    }
    return Object.assign({}, DEFAULT_DISPLAY_SETTINGS);
  }

  let displaySettings = loadDisplaySettings();

  function saveDisplaySettings() {
    try {
      localStorage.setItem(STORAGE_KEY_DISPLAY, JSON.stringify(displaySettings));
    } catch (e) {
      console.warn('[meridians.js] Failed to save display settings:', e);
    }
  }

  // Visual Scale Engine: Computes apparent scale factor from 3D projection
  const VisualScaleEngine = {
    calculateApparentScale(r, viewport) {
      if (!r || !r.camera || !viewport) {
        return { scale: 1.0, pixelsPerMeter: 800, viewingCondition: 'regional' };
      }

      const vp = viewport.viewProjectionMatrix;
      const t = r.camera.target || [0, 1.0, 0];
      const p0 = projectPoint(t, vp, viewport);
      const p1 = projectPoint([t[0], t[1] + 0.1, t[2]], vp, viewport);

      let pixelsPerMeter = 800;
      if (p0 && p1) {
        const dx = p1[0] - p0[0];
        const dy = p1[1] - p0[1];
        const dist10cm = Math.sqrt(dx * dx + dy * dy);
        if (dist10cm > 0.5) {
          pixelsPerMeter = dist10cm * 10.0;
        }
      }

      if (pixelsPerMeter === 800 || !isFinite(pixelsPerMeter)) {
        const fov = r.camera.fov || 0.7;
        const dist = Math.max(0.1, r.camera.dist || 2.0);
        pixelsPerMeter = viewport.height / (2.0 * dist * Math.tan(fov / 2.0));
      }

      // Viewing conditions:
      // Full-body overview: pixelsPerMeter < 450 (typically camera.dist > 2.0m)
      // Regional inspection: 450 <= pixelsPerMeter <= 1200 (camera.dist ~ 0.8m - 2.0m)
      // Close-up examination: pixelsPerMeter > 1200 (camera.dist < 0.8m)
      let viewingCondition = 'regional';
      if (pixelsPerMeter < 450) viewingCondition = 'full_body';
      else if (pixelsPerMeter > 1200) viewingCondition = 'close_up';

      // Normalized scale relative to regional baseline (800 px/m)
      const rawScale = pixelsPerMeter / 800.0;
      const clampedScale = Math.max(0.18, Math.min(3.5, rawScale));

      return {
        scale: clampedScale,
        pixelsPerMeter,
        viewingCondition
      };
    },

    getMarkerVisuals(settings, scaleInfo, isSel, isVerified, isSurface, isDienChan) {
      let baseRad;
      if (settings.scalingMode === 'manual') {
        baseRad = Math.max(1.0, Math.min(8.0, settings.markerSize));
      } else {
        // Auto-scaling responsive to apparent anatomical scale
        // Target visual scale:
        // Full-body overview: 1.5 - 2.5 px
        // Regional inspection: 2.5 - 4.0 px
        // Close-up examination: 3.5 - 5.5 px
        const s = scaleInfo.scale;
        baseRad = Math.max(1.5, Math.min(5.2, 1.5 + (s - 0.2) * 1.5));
        baseRad *= (settings.markerSizeMultiplier || 1.0);
      }

      let rad = baseRad;
      if (isVerified) rad *= 1.15;
      else if (isSurface) rad *= 1.05;
      if (isDienChan) rad *= 1.1;

      if (isSel) {
        rad = Math.max(rad * 1.35, 4.5);
      }

      const haloRad = Math.max(rad * 2.2, 10.0);
      const hitRad = Math.max(rad, 10.0); // Fitts's law generous hit target
      const swidth = isSel ? 2.0 : (isVerified ? 1.4 : 1.0);

      return { rad, haloRad, hitRad, swidth };
    },

    getMeridianVisuals(settings, scaleInfo, mCode, isSelectedMeridian) {
      let baseStroke;
      if (settings.scalingMode === 'manual') {
        baseStroke = Math.max(0.4, Math.min(4.5, settings.meridianThickness));
      } else {
        // Suggested targets:
        // Full-body: 0.8 - 1.2 px
        // Regional: 1.1 - 1.7 px
        // Close-up: 1.5 - 2.2 px
        const s = scaleInfo.scale;
        baseStroke = Math.max(0.8, Math.min(2.2, 0.85 + (s - 0.2) * 0.65));
        baseStroke *= (settings.meridianThicknessMultiplier || 1.0);
      }

      let opacity = '0.88';
      let strokeWidth = baseStroke;

      if (settings.channelEmphasis && settings.channelEmphasis !== 'all') {
        if (mCode === settings.channelEmphasis || isSelectedMeridian) {
          opacity = '1.0';
          strokeWidth = baseStroke * 1.35;
        } else {
          opacity = '0.18';
          strokeWidth = baseStroke * 0.75;
        }
      }

      return { strokeWidth, opacity };
    }
  };

  // Marker Density Manager: Screen-space density & stable clustering
  const MarkerDensityManager = {
    processCandidates(candidates, scaleInfo, settings, selectedCode, activelyEditedCode) {
      if (!settings.smartDensity || scaleInfo.viewingCondition === 'close_up') {
        return {
          unclustered: candidates,
          clusters: [],
          counters: {
            visible: candidates.length,
            clustered: 0
          }
        };
      }

      // Cluster threshold in screen pixels
      const thresholdPx = scaleInfo.viewingCondition === 'full_body' ? 14 : 8;
      const cellSize = Math.max(thresholdPx, 16);

      const unclustered = [];
      const pool = [];

      for (const item of candidates) {
        // Selected point or actively edited point is NEVER clustered!
        if (item.code === selectedCode || item.code === activelyEditedCode) {
          unclustered.push(item);
        } else {
          pool.push(item);
        }
      }

      // Spatial binning by system + side + grid coordinate
      const grid = new Map();
      for (const item of pool) {
        const gx = Math.floor(item.screen[0] / cellSize);
        const gy = Math.floor(item.screen[1] / cellSize);
        const key = `${item.system}:${item.inst.side}:${gx},${gy}`;
        if (!grid.has(key)) grid.set(key, []);
        grid.get(key).push(item);
      }

      const clusters = [];
      let totalClusteredPoints = 0;

      for (const [key, items] of grid.entries()) {
        if (items.length === 1) {
          unclustered.push(items[0]);
        } else {
          // Sort deterministically: Verified anchors first, then alphabetical code
          items.sort((a, b) => {
            const aVer = a.pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR' ? 0 : 1;
            const bVer = b.pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR' ? 0 : 1;
            if (aVer !== bVer) return aVer - bVer;
            return a.code.localeCompare(b.code);
          });

          const rep = items[0];
          let cx = 0, cy = 0, cz = 0;
          items.forEach(it => {
            cx += it.inst.pos[0];
            cy += it.inst.pos[1];
            cz += it.inst.pos[2];
          });
          const n = items.length;
          const centroid3D = [cx / n, cy / n, cz / n];

          clusters.push({
            rep,
            members: items,
            count: items.length,
            screen: rep.screen,
            centroid3D,
            system: rep.system,
            side: rep.inst.side
          });
          totalClusteredPoints += items.length;
        }
      }

      return {
        unclustered,
        clusters,
        counters: {
          visible: unclustered.length + clusters.length,
          clustered: totalClusteredPoints
        }
      };
    }
  };

  // Overlay Style Controller: Manages settings mutations, persistence and UI sync
  const OverlayStyleController = {
    getSettings() {
      return Object.assign({}, displaySettings);
    },
    updateSettings(newSettings) {
      Object.assign(displaySettings, newSettings);
      saveDisplaySettings();
      syncDisplaySettingsUI();
      render(true);
      notifyParentDisplayChanged();
    },
    resetDefaults() {
      displaySettings = Object.assign({}, DEFAULT_DISPLAY_SETTINGS);
      saveDisplaySettings();
      syncDisplaySettingsUI();
      render(true);
      notifyParentDisplayChanged();
    }
  };

  let lastRenderKey = null;
  let currentDensityCounters = { available: 0, visible: 0, clustered: 0, filtered: 0 };

  function notifyParentDisplayChanged() {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({
        action: 'msk_display_settings_changed',
        settings: displaySettings,
        counters: currentDensityCounters
      }, '*');
    }
  }

  function syncDisplaySettingsUI() {
    const selMode = document.getElementById('selScalingMode');
    if (selMode) selMode.value = displaySettings.scalingMode;

    const chkSmart = document.getElementById('chkSmartDensity');
    if (chkSmart) chkSmart.checked = Boolean(displaySettings.smartDensity);

    const lblSmart = document.getElementById('lblSmartDensityState');
    if (lblSmart) {
      lblSmart.textContent = displaySettings.smartDensity ? 'ON (Cluster)' : 'OFF (All)';
      lblSmart.style.color = displaySettings.smartDensity ? '#10b981' : '#f59e0b';
    }

    const rngMarker = document.getElementById('rngMarkerSize');
    const lblMarker = document.getElementById('lblMarkerSizeVal');
    if (rngMarker && lblMarker) {
      if (displaySettings.scalingMode === 'manual') {
        rngMarker.min = '10';
        rngMarker.max = '80';
        rngMarker.value = String(Math.round(displaySettings.markerSize * 10));
        lblMarker.textContent = `${displaySettings.markerSize.toFixed(1)} px`;
      } else {
        rngMarker.min = '50';
        rngMarker.max = '250';
        rngMarker.value = String(Math.round(displaySettings.markerSizeMultiplier * 100));
        lblMarker.textContent = `${displaySettings.markerSizeMultiplier.toFixed(1)}x`;
      }
    }

    const rngStroke = document.getElementById('rngMeridianThickness');
    const lblStroke = document.getElementById('lblStrokeWidthVal');
    if (rngStroke && lblStroke) {
      if (displaySettings.scalingMode === 'manual') {
        rngStroke.min = '5';
        rngStroke.max = '45';
        rngStroke.value = String(Math.round(displaySettings.meridianThickness * 10));
        lblStroke.textContent = `${displaySettings.meridianThickness.toFixed(1)} px`;
      } else {
        rngStroke.min = '50';
        rngStroke.max = '250';
        rngStroke.value = String(Math.round(displaySettings.meridianThicknessMultiplier * 100));
        lblStroke.textContent = `${displaySettings.meridianThicknessMultiplier.toFixed(1)}x`;
      }
    }

    const selLabel = document.getElementById('selLabelDensity');
    if (selLabel) selLabel.value = displaySettings.labelDensity;
  }

  function updateDensityCountersUI(cnt) {
    const cAvail = document.getElementById('cntAvailable');
    const cVis = document.getElementById('cntVisible');
    const cClust = document.getElementById('cntClustered');
    const cFilt = document.getElementById('cntFiltered');
    if (cAvail) cAvail.textContent = String(cnt.available);
    if (cVis) cVis.textContent = String(cnt.visible);
    if (cClust) cClust.textContent = String(cnt.clustered);
    if (cFilt) cFilt.textContent = String(cnt.filtered);

    if (window.parent && window.parent !== window) {
      window.parent.postMessage({
        action: 'msk_density_counters_updated',
        counters: cnt
      }, '*');
    }
  }
'''

def patch():
    print("Applying precision patch to meridians.js...")
    m_path = BASE_DIR / "msk_therapy_os/static/atlas/meridians.js"
    content = m_path.read_text(encoding="utf-8")

    # Insert ENGINE_CODE before loadData if not present
    if "const STORAGE_KEY_DISPLAY" not in content:
        content = content.replace(
            "  async function loadData() {",
            ENGINE_CODE + "\n\n  async function loadData() {",
            1
        )

    # Replace render function
    render_start = content.find("  function render(")
    if render_start == -1:
        render_start = content.find("function render(")
    assert render_start != -1, "Could not find function render("

    update_pin_idx = content.find("  function updatePin() {", render_start)
    assert update_pin_idx != -1, "Could not find function updatePin() after render()"

    pre_render = content[:render_start]
    post_render = content[update_pin_idx:]

    new_render = '''  function render(force = false) {
    const r = getRenderer();
    if (!r || !acuData) return;

    const stage = document.querySelector('.stage');
    if (!stage) return;
    const sw = stage.clientWidth;
    const sh = stage.clientHeight;

    // Get authoritative Viewport Descriptor from Renderer
    const viewport = r.getViewportDescriptor('overlay');
    const vp = viewport.viewProjectionMatrix;

    // Update SVG clipPath rect
    const clipRect = document.getElementById('overlayClipRect');
    if (clipRect) {
      clipRect.setAttribute('x', String(viewport.clippingBounds[0]));
      clipRect.setAttribute('y', String(viewport.clippingBounds[1]));
      clipRect.setAttribute('width', String(viewport.clippingBounds[2] - viewport.clippingBounds[0]));
      clipRect.setAttribute('height', String(viewport.clippingBounds[3] - viewport.clippingBounds[1]));
    }

    const isMusculo = r.renderMode === 'musculoskeletal';
    const isComp = r.renderMode === 'comparative';

    // In pure Musculoskeletal mode, hide meridians and points unless surface reference guide is enabled
    if (isMusculo && !showSurfaceReference) {
      groupMeridians.innerHTML = '';
      groupThai.innerHTML = '';
      groupPoints.innerHTML = '';
      groupDienChan.innerHTML = '';
      if (groupComparativeOverlay) groupComparativeOverlay.innerHTML = '';
      const pin = document.getElementById('pin');
      if (pin) pin.hidden = true;
      const totalAvail = (acuData && acuData.points ? Object.keys(acuData.points).length : 0) + (acuData && acuData.dien_chan ? acuData.dien_chan.length : 0);
      updateDensityCountersUI({ available: totalAvail, visible: 0, clustered: 0, filtered: totalAvail });
      return;
    }

    // Calculate dynamic apparent scale from 3D projection
    const scaleInfo = VisualScaleEngine.calculateApparentScale(r, viewport);

    // Render state cache check
    const stateKey = [
      (r.camera.dist || 0).toFixed(3),
      (r.camera.yaw || 0).toFixed(3),
      (r.camera.pitch || 0).toFixed(3),
      (r.camera.target || [0,0,0]).map(v => v.toFixed(3)).join(','),
      viewport.width,
      viewport.height,
      showPoints,
      showMeridians,
      showThai,
      showDienChan,
      showSurfaceReference,
      filterRegion,
      filterMeridian,
      verifiedOnly,
      selectedCode,
      displaySettings.scalingMode,
      displaySettings.markerSizeMultiplier,
      displaySettings.markerSize,
      displaySettings.meridianThicknessMultiplier,
      displaySettings.meridianThickness,
      displaySettings.labelDensity,
      displaySettings.smartDensity,
      displaySettings.channelEmphasis,
      window._msk_picking_mode,
      window._msk_moving_code
    ].join('|');

    if (!force && stateKey === lastRenderKey) {
      return;
    }
    lastRenderKey = stateKey;

    // 1. Render Continuous Surface-Conforming Meridians (Adaptive Stroke & Viewport-Clipped)
    if (!showMeridians) {
      groupMeridians.innerHTML = '';
    } else {
      let pathsHtml = '';
      const verifiedMeridianCodes = ['GV', 'CV', 'BL', 'GB', 'SI', 'TE', 'LI', 'LU', 'ST', 'SP', 'HT', 'KI', 'PC', 'LR'];

      for (const mCode in acuData.meridians) {
        if (filterMeridian !== 'all') {
          if (mCode !== filterMeridian) continue;
        } else {
          if (verifiedOnly && filterRegion !== 'all' && !verifiedMeridianCodes.includes(mCode)) continue;
        }

        const m = acuData.meridians[mCode];
        const isSelectedChannel = (filterMeridian === mCode || displaySettings.channelEmphasis === mCode);
        const meridianVis = VisualScaleEngine.getMeridianVisuals(displaySettings, scaleInfo, mCode, isSelectedChannel);

        for (const p of m.paths || []) {
          const pts = p.surface_vertices || p.points;
          if (!pts || pts.length < 2) continue;

          let pointSets = [pts];

          for (const poly of pointSets) {
            let facingCount = 0;
            let sampleCount = 0;
            const step = Math.max(1, Math.floor(poly.length / 16));
            for (let i = 0; i < poly.length; i += step) {
              if (isFacingCamera(poly[i], r)) facingCount++;
              sampleCount++;
            }
            const pathFacing = sampleCount > 0 && (facingCount / sampleCount) >= 0.35;
            if (!r.xray && !pathFacing) continue;

            const pathOpacity = pathFacing ? meridianVis.opacity : "0.18";
            // In full body overview, avoid heavy glow filter unless channel is selected
            const pathFilter = (pathFacing && (scaleInfo.viewingCondition !== 'full_body' || isSelectedChannel)) ? 'filter="url(#glow)"' : '';

            const filterFn = (filterMeridian === 'all') ? (pt) => matchesRegionPath(pt, filterRegion) : null;
            const d = projectAndClipPolyline(poly, vp, viewport, filterFn);
            if (d && d.includes('L')) {
              pathsHtml += `<path d="${d}" stroke="${m.color}" stroke-width="${meridianVis.strokeWidth.toFixed(2)}" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="${pathOpacity}" ${pathFilter}/>`;
            }
          }
        }
      }
      groupMeridians.innerHTML = pathsHtml;
    }

    // 2. Render Thai Sen Sib Lines (3 Educational Lines, Dashed Gold)
    if (!showThai) {
      groupThai.innerHTML = '';
    } else {
      let thaiHtml = '';
      const thaiVis = VisualScaleEngine.getMeridianVisuals(displaySettings, scaleInfo, 'THAI', false);
      const thaiStroke = (thaiVis.strokeWidth * 1.15).toFixed(2);
      const dashArr = scaleInfo.viewingCondition === 'full_body' ? '4,3' : '6,4';

      for (const line of acuData.thai_lines || []) {
        for (const p of line.paths || []) {
          const pts = p.points || p.surface_vertices;
          if (!pts || pts.length < 2) continue;
          const d = projectAndClipPolyline(pts, vp, viewport, null);
          if (d && d.includes('L')) {
            thaiHtml += `<path d="${d}" stroke="${line.color || '#f59e0b'}" stroke-width="${thaiStroke}" stroke-dasharray="${dashArr}" fill="none" opacity="0.9" />`;
          }
        }
      }
      groupThai.innerHTML = thaiHtml;
    }

    // 3. Collect Visible Candidate Acupoints & Dien Chan Points
    const candidates = [];
    const allCodes = new Set();
    if (acuData.points) {
      for (const c in acuData.points) allCodes.add(c);
    }
    if (acuData.dien_chan) {
      for (const dc of acuData.dien_chan) allCodes.add(dc.code);
    }

    const activelyEditedCode = (window._msk_picking_mode === 'move') ? window._msk_moving_code : null;

    if (showPoints) {
      for (const code in acuData.points) {
        const pt = acuData.points[code];
        const isVerified = pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR';

        const isSel = (selectedCode === code);

        if (!isSel) {
          if (filterMeridian !== 'all') {
            if (pt.meridian_code !== filterMeridian) continue;
          } else {
            if (verifiedOnly && filterRegion !== 'all' && !isVerified) continue;
            if (!matchesRegion(pt.region, filterRegion)) continue;
          }

          if (searchQuery) {
            const q = searchQuery.toLowerCase();
            const matchCode = pt.code.toLowerCase().includes(q);
            const matchEn = (pt.name_en || '').toLowerCase().includes(q);
            const matchZh = (pt.name_zh || '').includes(q);
            if (!matchCode && !matchEn && !matchZh) continue;
          }
        }

        const isMidline = Math.abs(pt.position[0]) < 0.005;
        const instances = [{ pos: pt.position, side: isMidline ? 'midline' : 'right' }];
        if (!isMidline && pt.position[0] > 0.005) {
          instances.push({ pos: [-pt.position[0], pt.position[1], pt.position[2]], side: 'left' });
        }

        for (const inst of instances) {
          const s = projectPoint(inst.pos, vp, viewport);
          if (!s) continue;

          const isSel = (selectedCode === code);
          const norm = inst.side === 'left' && pt.normal ? [-pt.normal[0], pt.normal[1], pt.normal[2]] : pt.normal;
          const facing = isFacingCamera(inst.pos, r, norm);

          if (!r.xray && !facing && !isSel) continue;

          const isEditing = (code === activelyEditedCode);

          candidates.push({
            code,
            pt,
            inst,
            screen: s,
            facing,
            isSel,
            isEditing,
            system: pt.library_id || 'lib_who_classical'
          });
        }
      }
    }

    // Also collect Dien Chan reflex points if enabled
    if (showDienChan && acuData.dien_chan) {
      for (const dc of acuData.dien_chan) {
        const s = projectPoint(dc.position, vp, viewport);
        if (!s) continue;

        const isSel = (selectedCode === dc.code);
        const facing = isFacingCamera(dc.position, r, dc.normal || null);
        if (!r.xray && !facing && !isSel) continue;

        candidates.push({
          code: dc.code,
          pt: dc,
          inst: { pos: dc.position, side: 'midline' },
          screen: s,
          facing,
          isSel,
          isEditing: false,
          system: 'lib_dien_chan'
        });
      }
    }

    // Process Density & Clustering
    const densityResult = MarkerDensityManager.processCandidates(
      candidates,
      scaleInfo,
      displaySettings,
      selectedCode,
      activelyEditedCode
    );

    // 4. Render Markers & Clusters into groupPoints
    if (!showPoints && !showSurfaceReference && !isComp && !showDienChan) {
      groupPoints.innerHTML = '';
      groupDienChan.innerHTML = '';
    } else {
      let ptsHtml = '';

      // A. Render Clusters
      for (const c of densityResult.clusters) {
        const s = c.screen;
        const scaleVis = VisualScaleEngine.getMarkerVisuals(displaySettings, scaleInfo, false, false, false, false);
        const hitRad = Math.max(12, scaleVis.rad * 2.2);
        const clusterRad = Math.max(4.0, Math.min(8.0, scaleVis.rad * 1.55));
        const codesStr = c.members.map(m => m.code).join(',');
        const titleText = `[Cluster: ${c.count} points (${c.system.toUpperCase()})]\\n${c.members.map(m => `${m.code} - ${m.pt.name_en || m.pt.name || ''}`).join('\\n')}\\nClick to zoom in and expand`;

        ptsHtml += `
          <g class="acu-cluster-marker" data-cluster-codes="${codesStr}" data-centroid-x="${c.centroid3D[0]}" data-centroid-y="${c.centroid3D[1]}" data-centroid-z="${c.centroid3D[2]}" style="cursor:pointer;">
            <circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${hitRad}" fill="transparent" stroke="none" pointer-events="all"/>
            <circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${clusterRad.toFixed(1)}" fill="#0f766e" stroke="#38bdf8" stroke-width="1.5" opacity="0.95" pointer-events="none"/>
            <text x="${s[0].toFixed(1)}" y="${(s[1] + 3.0).toFixed(1)}" text-anchor="middle" font-size="9" font-weight="700" fill="#ffffff" pointer-events="none" font-family="-apple-system, BlinkMacSystemFont, sans-serif">+${c.count}</text>
            <title>${titleText}</title>
          </g>
        `;
      }

      // B. Render Unclustered Markers
      for (const item of densityResult.unclustered) {
        const s = item.screen;
        const code = item.code;
        const pt = item.pt;
        const inst = item.inst;
        const isSel = item.isSel;
        const isVerified = (pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR');
        const isSurface = (pt.registration_status === 'SURFACE_REGISTERED_FJ2810');
        const isDienChan = Boolean(item.system && item.system.startsWith('lib_dien_chan'));

        const vis = VisualScaleEngine.getMarkerVisuals(displaySettings, scaleInfo, isSel, isVerified, isSurface, isDienChan);

        let fill = isSel ? '#facc15' : (isVerified ? '#10b981' : (isSurface ? '#06b6d4' : (isDienChan ? '#ec4899' : '#f59e0b')));
        let stroke = isSel ? '#ffffff' : (isVerified ? '#047857' : (isSurface ? '#0891b2' : (isDienChan ? '#be185d' : '#78350f')));
        let dash = (isVerified || isSurface) ? '' : 'stroke-dasharray="2,2"';
        let ptOpacity = item.facing ? '1.0' : '0.35';

        const statusLabel = isVerified ? 'VERIFIED ANCHOR' : (isSurface ? 'SURFACE REGISTERED (FJ2810)' : (isDienChan ? 'VIETNAMESE DIEN CHAN' : 'UNCERTAIN POSTURE OFFSET'));

        ptsHtml += `
          <g class="acu-marker-group" data-code="${code}" data-side="${inst.side}" style="cursor:pointer;">
            <circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${vis.hitRad}" fill="transparent" stroke="none" class="acu-marker ${isDienChan ? 'dien-chan-marker' : ''}" data-code="${code}" data-side="${inst.side}" pointer-events="all"/>
            <circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${vis.rad.toFixed(1)}" fill="${fill}" stroke="${stroke}" stroke-width="${vis.swidth}" ${dash} opacity="${ptOpacity}" pointer-events="none"/>
            <title>${pt.code} - ${pt.name_en || pt.name || ''} (${pt.name_zh || ''}) [${statusLabel}] [${inst.side.toUpperCase()}]
Pos: [${inst.pos[0].toFixed(3)}, ${inst.pos[1].toFixed(3)}, ${inst.pos[2].toFixed(3)}]m
${!item.facing ? ' (Dorsal/Occluded)' : ''}</title>
        `;

        // Selection rotating halo
        if (isSel) {
          ptsHtml += `
            <circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${vis.haloRad.toFixed(1)}" fill="none" stroke="#facc15" stroke-width="1.8" stroke-dasharray="4,4" opacity="${item.facing ? '0.95' : '0.45'}" pointer-events="none">
              <animateTransform attributeName="transform" type="rotate" from="0 ${s[0]} ${s[1]}" to="360 ${s[0]} ${s[1]}" dur="5s" repeatCount="indefinite"/>
            </circle>
          `;
        }

        // Text label rendering
        let shouldRenderLabel = false;
        if (displaySettings.labelDensity === 'all') {
          shouldRenderLabel = true;
        } else if (displaySettings.labelDensity === 'selected') {
          shouldRenderLabel = isSel;
        } else if (displaySettings.labelDensity === 'auto') {
          shouldRenderLabel = isSel || (scaleInfo.viewingCondition === 'close_up') || (scaleInfo.viewingCondition === 'regional' && isVerified && scaleInfo.scale > 0.85);
        }

        if (shouldRenderLabel) {
          const lblX = (s[0] + vis.rad + 3.0).toFixed(1);
          const lblY = (s[1] + 3.0).toFixed(1);
          const fontSize = Math.max(9, Math.min(12, Math.round(vis.rad * 2.2)));
          ptsHtml += `<text x="${lblX}" y="${lblY}" font-size="${fontSize}" font-weight="600" fill="#f8fafc" font-family="-apple-system, BlinkMacSystemFont, sans-serif" style="text-shadow:0 1px 2px rgba(0,0,0,0.8); pointer-events:none;">${code}</text>`;
        }

        ptsHtml += `</g>`;
      }

      groupPoints.innerHTML = ptsHtml;
      groupDienChan.innerHTML = '';
    }

    // 5. Update Dynamic Density Counters (Tracked by Unique Clinical Point Codes)
    const visibleCodes = new Set();
    for (const item of densityResult.unclustered) {
      visibleCodes.add(item.code);
    }
    const clusteredCodes = new Set();
    for (const cl of densityResult.clusters) {
      for (const m of cl.members) {
        if (!visibleCodes.has(m.code)) {
          clusteredCodes.add(m.code);
        }
      }
    }

    const totalAvailablePoints = allCodes.size;
    const totalVis = visibleCodes.size;
    const totalClust = clusteredCodes.size;
    const totalFilt = Math.max(0, totalAvailablePoints - totalVis - totalClust);

    currentDensityCounters = {
      available: totalAvailablePoints,
      visible: totalVis,
      clustered: totalClust,
      filtered: totalFilt
    };
    updateDensityCountersUI(currentDensityCounters);

    // 6. Comparative Mode Split Badges
    if (groupComparativeOverlay) {
      if (isComp) {
        const halfW = viewport.clippingBounds[0];
        groupComparativeOverlay.innerHTML = `
          <line x1="${halfW}" y1="0" x2="${halfW}" y2="${sh}" stroke="#475569" stroke-width="2" stroke-dasharray="6,4" opacity="0.8"/>
          <g transform="translate(16, 26)">
            <rect x="-6" y="-16" width="225" height="24" rx="4" fill="rgba(15,23,42,0.88)" stroke="#38bdf8" stroke-width="1"/>
            <text fill="#38bdf8" font-size="11" font-weight="700" font-family="system-ui, sans-serif" y="-1">🦴 MUSCULOSKELETAL ANATOMY</text>
          </g>
          <g transform="translate(${halfW + 16}, 26)">
            <rect x="-6" y="-16" width="195" height="24" rx="4" fill="rgba(15,23,42,0.88)" stroke="#10b981" stroke-width="1"/>
            <text fill="#34d399" font-size="11" font-weight="700" font-family="system-ui, sans-serif" y="-1">🌐 SURFACE & MERIDIANS</text>
          </g>
        `;
      } else if (isMusculo && showSurfaceReference) {
        groupComparativeOverlay.innerHTML = `
          <g transform="translate(16, 26)">
            <rect x="-6" y="-16" width="285" height="24" rx="4" fill="rgba(15,23,42,0.88)" stroke="#eab308" stroke-width="1"/>
            <text fill="#facc15" font-size="11" font-weight="700" font-family="system-ui, sans-serif" y="-1">📍 SURFACE REFERENCE (Non-physical)</text>
          </g>
        `;
      } else {
        groupComparativeOverlay.innerHTML = '';
      }
    }

    // Update active selection pin
    updatePin();
  }
\n'''

    content = pre_render + new_render + post_render
    m_path.write_text(content, encoding="utf-8")
    print("✓ Successfully patched meridians.js with unique clinical point code counters")

if __name__ == "__main__":
    patch()
