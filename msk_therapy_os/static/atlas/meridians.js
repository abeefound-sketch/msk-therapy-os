// MSK-Therapy-OS: 3D Acupuncture & Traditional Meridian Visualization Layer
// Calibrated to BodyParts3D 4.0 Anatomical Ground Truth (FMA Standards)
(() => {
  'use strict';

  let acuData = null;
  // Default to clean anatomical view with unnecessary overlays disabled (Requirement 7)
  let showPoints = false;
  let showMeridians = false;
  let showThai = false;
  let showDienChan = false;
  let verifiedOnly = true; // Default to verified anatomical anchors only (Requirement 5)
  let filterRegion = 'neck'; // Focus on Neck-Shoulder-Upper-Back scenario (Requirement 9)
  let selectedCode = null;

  const overlaySvg = document.getElementById('acupunctureOverlay');
  if (!overlaySvg) return;

  // Create SVG element containers
  overlaySvg.innerHTML = `
    <defs>
      <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="2" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
      </filter>
    </defs>
    <g id="groupMeridians"></g>
    <g id="groupThai"></g>
    <g id="groupPoints"></g>
    <g id="groupDienChan"></g>
  `;

  const groupMeridians = document.getElementById('groupMeridians');
  const groupThai = document.getElementById('groupThai');
  const groupPoints = document.getElementById('groupPoints');
  const groupDienChan = document.getElementById('groupDienChan');

  // Load consolidated 3D dataset
  async function loadData() {
    try {
      const res = await fetch('/api/acupuncture-3d');
      if (!res.ok) {
        console.warn('Could not load /api/acupuncture-3d, fallback to relative path');
        const res2 = await fetch('data/acupuncture_3d.json');
        acuData = await res2.json();
      } else {
        acuData = await res.json();
      }
      buildSidebarControls();
      render();
    } catch (err) {
      console.error('Failed to load acupuncture 3D dataset:', err);
    }
  }

  function getRenderer() {
    return window.__atlasDebug ? window.__atlasDebug.renderer : null;
  }

  function render() {
    const r = getRenderer();
    if (!r || !acuData) return;

    const stage = document.querySelector('.stage');
    if (!stage) return;
    const sw = stage.clientWidth;
    const sh = stage.clientHeight;

    // 1. Render Meridians
    if (!showMeridians) {
      groupMeridians.innerHTML = '';
    } else {
      let pathsHtml = '';
      for (const mCode in acuData.meridians) {
        // If verified only, only render Cervical/Shoulder/Upper-back pathways (GV, BL, GB)
        if (verifiedOnly && !['GV', 'BL', 'GB', 'SI', 'TE', 'LI'].includes(mCode)) continue;

        const m = acuData.meridians[mCode];
        for (const p of m.paths) {
          if (!p.points || p.points.length < 2) continue;

          // Bilateral rendering for lateral meridians
          const pointSets = [p.points];
          const isMidline = ['GV', 'CV'].includes(mCode);
          if (!isMidline && p.points.some(pt => Math.abs(pt[0]) > 0.005)) {
            // Also project left-side companion path
            const mirrored = p.points.map(pt => [-pt[0], pt[1], pt[2]]);
            pointSets.push(mirrored);
          }

          for (const pts of pointSets) {
            let d = '';
            for (let i = 0; i < pts.length; i++) {
              const pt = pts[i];
              // If verified only, restrict to neck-shoulder-upperback height (Y >= 1.30m)
              if (verifiedOnly && pt[1] < 1.30) continue;

              const s = r.project(pt);
              if (!s) continue;
              d += (d === '' ? 'M ' : ' L ') + s[0].toFixed(1) + ' ' + s[1].toFixed(1);
            }
            if (d && d.includes('L')) {
              pathsHtml += `<path d="${d}" stroke="${m.color}" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.85" filter="url(#glow)"/>`;
            }
          }
        }
      }
      groupMeridians.innerHTML = pathsHtml;
    }

    // 2. Render Thai Sen Sib Lines
    if (!showThai) {
      groupThai.innerHTML = '';
    } else {
      let thaiHtml = '';
      for (const line of acuData.thai_lines || []) {
        for (const p of line.paths) {
          if (!p.points || p.points.length < 2) continue;
          let d = '';
          for (let i = 0; i < p.points.length; i++) {
            const s = r.project(p.points[i]);
            if (!s) continue;
            d += (d === '' ? 'M ' : ' L ') + s[0].toFixed(1) + ' ' + s[1].toFixed(1);
          }
          if (d) {
            thaiHtml += `<path d="${d}" stroke="${line.color}" stroke-width="3" stroke-dasharray="6,4" fill="none" opacity="0.9" />`;
          }
        }
      }
      groupThai.innerHTML = thaiHtml;
    }

    // 3. Render Acupuncture Points
    if (!showPoints) {
      groupPoints.innerHTML = '';
    } else {
      let ptsHtml = '';
      for (const code in acuData.points) {
        const pt = acuData.points[code];
        const isVerified = pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR';

        // Filter: verified anchors only or posture offset
        if (verifiedOnly && !isVerified) continue;

        if (filterRegion !== 'all') {
          const ptRegion = pt.region || '';
          if (filterRegion === 'neck' && !isVerified && !ptRegion.includes('头面颈项') && !ptRegion.includes('腰背')) continue;
        }

        // Bilateral point instances
        const isMidline = Math.abs(pt.position[0]) < 0.005;
        const instances = [{ pos: pt.position, side: isMidline ? 'midline' : 'right' }];
        if (!isMidline && pt.position[0] > 0.005) {
          instances.push({ pos: [-pt.position[0], pt.position[1], pt.position[2]], side: 'left' });
        }

        for (const inst of instances) {
          const s = r.project(inst.pos);
          if (!s || s[0] < -20 || s[1] < -20 || s[0] > sw + 20 || s[1] > sh + 20) continue;

          const isSel = selectedCode === code;
          let rad = isSel ? 7 : (isVerified ? 5 : 4);
          let fill = isSel ? '#facc15' : (isVerified ? '#10b981' : '#f59e0b');
          let stroke = isSel ? '#ffffff' : (isVerified ? '#047857' : '#78350f');
          let swidth = isSel ? 2.5 : 1.5;
          let dash = isVerified ? '' : 'stroke-dasharray="2,2"';

          ptsHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${rad}" fill="${fill}" stroke="${stroke}" stroke-width="${swidth}" ${dash} class="acu-marker" data-code="${code}" data-side="${inst.side}" style="cursor:pointer;">
            <title>${pt.code} - ${pt.name_en} (${pt.name_zh}) [${isVerified ? 'VERIFIED ANCHOR' : 'UNCERTAIN POSTURE'}]</title>
          </circle>`;

          if (isSel) {
            ptsHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="13" fill="none" stroke="#facc15" stroke-width="2" stroke-dasharray="4,4" opacity="0.9">
              <animateTransform attributeName="transform" type="rotate" from="0 ${s[0]} ${s[1]}" to="360 ${s[0]} ${s[1]}" dur="5s" repeatCount="indefinite"/>
            </circle>`;
          }
        }
      }
      groupPoints.innerHTML = ptsHtml;
    }

    // 4. Render Dien Chan Reflex Points
    if (!showDienChan) {
      groupDienChan.innerHTML = '';
    } else {
      let dcHtml = '';
      for (const dc of acuData.dien_chan || []) {
        const s = r.project(dc.position);
        if (!s || s[0] < -10 || s[1] < -10 || s[0] > sw + 10 || s[1] > sh + 10) continue;
        dcHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="4.5" fill="#ec4899" stroke="#ffffff" stroke-width="1.5" class="acu-marker" data-code="${dc.code}">
          <title>${dc.name} [Dien Chan]</title>
        </circle>`;
      }
      groupDienChan.innerHTML = dcHtml;
    }
  }

  // Handle marker click
  overlaySvg.addEventListener('click', (ev) => {
    const target = ev.target.closest('.acu-marker');
    if (!target) return;
    const code = target.getAttribute('data-code');
    if (!code) return;
    selectPoint(code, true);
  });

  function selectPoint(code, notifyParent = true) {
    if (!acuData || !acuData.points[code]) return;
    selectedCode = code;
    const pt = acuData.points[code];
    const r = getRenderer();

    // Position pin
    if (r) {
      const s = r.project(pt.position);
      const pin = document.getElementById('pin');
      if (pin && s) {
        pin.hidden = false;
        pin.style.left = s[0] + 'px';
        pin.style.top = s[1] + 'px';
        const span = pin.querySelector('span');
        if (span) {
          const statusTag = pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR' ? ' [✓ Verified]' : ' [⚠️ Posture Offset]';
          span.textContent = `${pt.name_en} (${pt.code} / ${pt.name_zh})${statusTag}`;
        }
      }
    }

    render();

    if (notifyParent) {
      window.parent.postMessage({
        type: 'msk_acupoint_selected',
        point: pt,
      }, '*');
    }
  }

  // Build sidebar controls inside #panelMeridians
  function buildSidebarControls() {
    const panel = document.getElementById('panelMeridians');
    if (!panel || !acuData) return;

    let pointsListHtml = '';
    const sortedCodes = Object.keys(acuData.points).sort((a, b) => {
      const vA = acuData.points[a].registration_status === 'VERIFIED_ANATOMICAL_ANCHOR' ? 0 : 1;
      const vB = acuData.points[b].registration_status === 'VERIFIED_ANATOMICAL_ANCHOR' ? 0 : 1;
      return vA - vB;
    });

    for (const code of sortedCodes) {
      const p = acuData.points[code];
      const isVer = p.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR';
      const badge = isVer ? '<span style="background:#065f46; color:#a7f3d0; font-size:9px; padding:1px 4px; border-radius:3px; font-weight:600;">✓ ANCHOR</span>' : '<span style="background:#78350f; color:#fde68a; font-size:9px; padding:1px 4px; border-radius:3px;">⚠️ UNVERIFIED</span>';
      pointsListHtml += `
        <div class="acu-list-item" data-code="${code}" style="display:flex; justify-content:space-between; align-items:center; padding:5px 8px; font-size:11px; border-bottom:1px solid var(--line); cursor:pointer;">
          <div>
            <strong>${p.code}</strong> ${p.name_en} <small style="color:var(--muted)">(${p.name_zh})</small>
          </div>
          <div>${badge}</div>
        </div>
      `;
    }

    panel.innerHTML = `
      <div style="padding:10px; display:flex; flex-direction:column; gap:10px; font-size:12px;">
        <div style="font-weight:600; color:var(--bone); font-size:13px; display:flex; justify-content:space-between; align-items:center;">
          <span>Anatomical Overlays</span>
          <span style="font-size:10px; color:#38bdf8;">BodyParts3D Ground Truth</span>
        </div>

        <div style="display:flex; flex-direction:column; gap:6px; background:var(--panel-2); padding:8px; border-radius:var(--r-s);">
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
            <input type="checkbox" id="chkShowPoints" ${showPoints ? 'checked' : ''} />
            <span>📍 3D Acupoints</span>
          </label>
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer; margin-left:16px;">
            <input type="checkbox" id="chkVerifiedOnly" ${verifiedOnly ? 'checked' : ''} />
            <span style="color:#10b981; font-weight:600;">✓ Verified Anchors Only</span>
          </label>
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
            <input type="checkbox" id="chkShowMeridians" ${showMeridians ? 'checked' : ''} />
            <span>⚡ 14 Meridian Pathways</span>
          </label>
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
            <input type="checkbox" id="chkShowThai" ${showThai ? 'checked' : ''} />
            <span>🇹🇭 Thai Sen Sib Lines</span>
          </label>
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
            <input type="checkbox" id="chkShowDienChan" ${showDienChan ? 'checked' : ''} />
            <span>🇻🇳 Dien Chan Reflex Points</span>
          </label>
        </div>

        <div style="display:flex; flex-direction:column; gap:4px;">
          <label style="font-size:11px; color:var(--muted);">Region Focus:</label>
          <select id="selAcuRegion" style="background:var(--panel-2); color:var(--bone); border:1px solid var(--line); padding:4px 6px; border-radius:var(--r-s); font-size:11px;">
            <option value="neck" ${filterRegion === 'neck' ? 'selected' : ''}>Neck, Shoulder & Upper Back (Verified Scenario)</option>
            <option value="all" ${filterRegion === 'all' ? 'selected' : ''}>Full Body (All Regions)</option>
          </select>
        </div>

        <div style="font-weight:600; color:var(--bone); font-size:11px; margin-top:4px;">
          Key Clinical Points (Neck-Shoulder):
        </div>
        <div style="display:flex; gap:4px; flex-wrap:wrap;">
          <button class="btn-acu-quick" data-code="GB21" style="font-size:10px; padding:3px 6px; background:#065f46; color:#a7f3d0; border:1px solid #10b981; border-radius:3px; cursor:pointer;">GB21 肩井 (Trapezius)</button>
          <button class="btn-acu-quick" data-code="GV14" style="font-size:10px; padding:3px 6px; background:#065f46; color:#a7f3d0; border:1px solid #10b981; border-radius:3px; cursor:pointer;">GV14 大椎 (C7 Spine)</button>
          <button class="btn-acu-quick" data-code="GB20" style="font-size:10px; padding:3px 6px; background:#065f46; color:#a7f3d0; border:1px solid #10b981; border-radius:3px; cursor:pointer;">GB20 风池 (Suboccipital)</button>
          <button class="btn-acu-quick" data-code="BL10" style="font-size:10px; padding:3px 6px; background:#065f46; color:#a7f3d0; border:1px solid #10b981; border-radius:3px; cursor:pointer;">BL10 天柱 (Trapezius)</button>
          <button class="btn-acu-quick" data-code="SI15" style="font-size:10px; padding:3px 6px; background:#065f46; color:#a7f3d0; border:1px solid #10b981; border-radius:3px; cursor:pointer;">SI15 肩中俞 (C7 Paramedian)</button>
          <button class="btn-acu-quick" data-code="TE15" style="font-size:10px; padding:3px 6px; background:#065f46; color:#a7f3d0; border:1px solid #10b981; border-radius:3px; cursor:pointer;">TE15 天髎 (Supraspinous)</button>
        </div>

        <div style="font-weight:600; color:var(--bone); font-size:11px; margin-top:6px;">
          Points Directory:
        </div>
        <div id="acuPointsDirectory" style="overflow-y:auto; max-height:220px; background:var(--panel-2); border-radius:var(--r-s);">
          ${pointsListHtml}
        </div>
      </div>
    `;

    // Event listeners
    document.getElementById('chkShowPoints').addEventListener('change', (e) => {
      showPoints = e.target.checked;
      render();
    });
    document.getElementById('chkVerifiedOnly').addEventListener('change', (e) => {
      verifiedOnly = e.target.checked;
      render();
    });
    document.getElementById('chkShowMeridians').addEventListener('change', (e) => {
      showMeridians = e.target.checked;
      render();
    });
    document.getElementById('chkShowThai').addEventListener('change', (e) => {
      showThai = e.target.checked;
      render();
    });
    document.getElementById('chkShowDienChan').addEventListener('change', (e) => {
      showDienChan = e.target.checked;
      render();
    });
    document.getElementById('selAcuRegion').addEventListener('change', (e) => {
      filterRegion = e.target.value;
      render();
    });

    panel.querySelectorAll('.btn-acu-quick, .acu-list-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.getAttribute('data-code');
        if (code) {
          showPoints = true;
          const chk = document.getElementById('chkShowPoints');
          if (chk) chk.checked = true;
          selectPoint(code, true);
        }
      });
    });
  }

  // Hook into renderer's animation frame loop
  function hookFrame() {
    const r = getRenderer();
    if (!r) {
      setTimeout(hookFrame, 200);
      return;
    }
    const prevOnFrame = r.onFrame;
    r.onFrame = () => {
      if (typeof prevOnFrame === 'function') prevOnFrame();
      render();
    };
    render();
  }

  // Listen for commands from parent window
  window.addEventListener('message', (ev) => {
    if (!ev.data) return;
    if (ev.data.action === 'select_acupoint') {
      showPoints = true;
      const chk = document.getElementById('chkShowPoints');
      if (chk) chk.checked = true;
      selectPoint(ev.data.code, true);
    } else if (ev.data.action === 'toggle_layer' || ev.data.action === 'toggle_meridian_layer') {
      const layer = ev.data.layer;
      const val = ev.data.enabled;
      if (layer === 'points') {
        showPoints = (val !== undefined) ? val : !showPoints;
        const c = document.getElementById('chkShowPoints'); if (c) c.checked = showPoints;
      } else if (layer === 'meridians') {
        showMeridians = (val !== undefined) ? val : !showMeridians;
        const c = document.getElementById('chkShowMeridians'); if (c) c.checked = showMeridians;
      } else if (layer === 'verified_only') {
        verifiedOnly = (val !== undefined) ? val : !verifiedOnly;
        const c = document.getElementById('chkVerifiedOnly'); if (c) c.checked = verifiedOnly;
      } else if (layer === 'thai') {
        showThai = (val !== undefined) ? val : !showThai;
        const c = document.getElementById('chkShowThai'); if (c) c.checked = showThai;
      } else if (layer === 'dien_chan') {
        showDienChan = (val !== undefined) ? val : !showDienChan;
        const c = document.getElementById('chkShowDienChan'); if (c) c.checked = showDienChan;
      }
      render();
    } else if (ev.data.action === 'set_region') {
      filterRegion = ev.data.region || 'neck';
      const sel = document.getElementById('selAcuRegion');
      if (sel) sel.value = filterRegion;
      render();
    }
  });

  // Start initialization
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      loadData();
      hookFrame();
    });
  } else {
    loadData();
    hookFrame();
  }
})();
