// MSK-Therapy-OS: 3D Acupuncture & Traditional Meridian Visualization Layer
// Integrates WHO 2008 / GB/T 12346-2021 acupoints and 14 meridian courses into Open Anatomy Atlas.
(() => {
  'use strict';

  let acuData = null;
  let showPoints = true;
  let showMeridians = true;
  let showThai = false;
  let showDienChan = false;
  let filterRegion = 'all';
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
        const m = acuData.meridians[mCode];
        for (const p of m.paths) {
          if (!p.points || p.points.length < 2) continue;
          let d = '';
          for (let i = 0; i < p.points.length; i++) {
            const pt = p.points[i];
            const s = r.project(pt);
            if (!s) continue;
            d += (d === '' ? 'M ' : ' L ') + s[0].toFixed(1) + ' ' + s[1].toFixed(1);
          }
          if (d) {
            pathsHtml += `<path d="${d}" stroke="${m.color}" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.85" filter="url(#glow)"/>`;
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
        if (filterRegion !== 'all' && pt.region !== filterRegion) continue;

        const s = r.project(pt.position);
        if (!s || s[0] < -20 || s[1] < -20 || s[0] > sw + 20 || s[1] > sh + 20) continue;

        const isSel = selectedCode === code;
        const rad = isSel ? 7 : 4;
        const fill = isSel ? '#facc15' : '#38bdf8';
        const stroke = isSel ? '#ffffff' : '#0f172a';
        const swidth = isSel ? 2.5 : 1.5;

        ptsHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${rad}" fill="${fill}" stroke="${stroke}" stroke-width="${swidth}" class="acu-marker" data-code="${code}">
          <title>${pt.code} - ${pt.name_en} (${pt.name_zh}) [${pt.meridian_name}]</title>
        </circle>`;

        if (isSel) {
          ptsHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="12" fill="none" stroke="#facc15" stroke-width="1.5" stroke-dasharray="3,3" opacity="0.8">
            <animateTransform attributeName="transform" type="rotate" from="0 ${s[0]} ${s[1]}" to="360 ${s[0]} ${s[1]}" dur="6s" repeatCount="indefinite"/>
          </circle>`;
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
        dcHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="4" fill="#ec4899" stroke="#ffffff" stroke-width="1.5" class="acu-marker" data-code="${dc.code}">
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
        if (span) span.textContent = `${pt.name_en} (${pt.code} / ${pt.name_zh})`;
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
    if (!panel) return;

    panel.innerHTML = `
      <div style="padding: 12px; display: flex; flex-direction: column; gap: 14px;">
        <div>
          <h3 style="margin: 0 0 6px 0; font-size: 13px; color: var(--film); font-weight: 600;">Traditional Meridian Layers</h3>
          <p style="margin: 0; font-size: 11px; color: var(--muted); line-height: 1.4;">
            WHO 2008 & GB/T 12346-2021 standard surface topography. Cultural constructs; not equivalent to physical nerves or fascia.
          </p>
        </div>

        <div style="display: flex; flex-direction: column; gap: 8px;">
          <label style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; cursor: pointer;">
            <span>Acupuncture Points (${acuData.metadata.count_points})</span>
            <input type="checkbox" id="chkShowPoints" ${showPoints ? 'checked' : ''}>
          </label>
          <label style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; cursor: pointer;">
            <span>14 Primary Meridians</span>
            <input type="checkbox" id="chkShowMeridians" ${showMeridians ? 'checked' : ''}>
          </label>
          <label style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; cursor: pointer;">
            <span>Thai Sen Sib Lines (DTAM)</span>
            <input type="checkbox" id="chkShowThai" ${showThai ? 'checked' : ''}>
          </label>
          <label style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; cursor: pointer;">
            <span>Dien Chan Facial Reflexes</span>
            <input type="checkbox" id="chkShowDienChan" ${showDienChan ? 'checked' : ''}>
          </label>
        </div>

        <div style="border-top: 1px solid var(--line); padding-top: 10px;">
          <label style="display: block; font-size: 11px; color: var(--muted); margin-bottom: 4px;">Region Focus</label>
          <select id="selAcuRegion" style="width: 100%; padding: 4px 8px; background: var(--stage); border: 1px solid var(--line); border-radius: var(--r-s); font-size: 12px;">
            <option value="all">All Anatomical Regions</option>
            <option value="头面颈项">Head & Neck (GB20, BL10, GV14)</option>
            <option value="肩背">Shoulder & Back (GB21, SI14, SI15)</option>
            <option value="上肢">Upper Extremity (LI4, LU5, PC6)</option>
            <option value="腰背">Lumbar Spine & Sacrum (BL23, GV4)</option>
            <option value="下肢">Lower Extremity (ST36, GB34, SP6)</option>
          </select>
        </div>

        <div style="border-top: 1px solid var(--line); padding-top: 10px;">
          <div style="font-size: 11px; font-weight: 600; color: var(--film); margin-bottom: 6px;">Key MSK Clinical Points</div>
          <div style="display: flex; flex-wrap: wrap; gap: 4px;">
            <button class="pill-btn" data-point="GB21" title="Trapezius Trigger Point #1">GB21 (Jianjing)</button>
            <button class="pill-btn" data-point="GB20" title="Suboccipital Release">GB20 (Fengchi)</button>
            <button class="pill-btn" data-point="GV14" title="C7-T1 Cervicothoracic">GV14 (Dazhui)</button>
            <button class="pill-btn" data-point="BL10" title="Paraspinal Neck">BL10 (Tianzhu)</button>
            <button class="pill-btn" data-point="LI4" title="Distal Analgesic Point">LI4 (Hegu)</button>
          </div>
        </div>
      </div>
    `;

    // Hook listeners
    document.getElementById('chkShowPoints').addEventListener('change', (e) => {
      showPoints = e.target.checked;
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

    panel.querySelectorAll('.pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.getAttribute('data-point');
        selectPoint(code, true);
      });
    });
  }

  // Hook into renderer's onFrame
  function hookFrame() {
    const r = getRenderer();
    if (r) {
      const prevOnFrame = r.onFrame;
      r.onFrame = () => {
        if (typeof prevOnFrame === 'function') prevOnFrame();
        render();
      };
      render();
    } else {
      setTimeout(hookFrame, 200);
    }
  }

  // Listen to parent postMessages
  window.addEventListener('message', (ev) => {
    if (!ev.data || typeof ev.data !== 'object') return;
    const { action, layer, enabled, code, region } = ev.data;

    if (action === 'toggle_meridian_layer') {
      if (layer === 'points') showPoints = enabled ?? !showPoints;
      if (layer === 'meridians') showMeridians = enabled ?? !showMeridians;
      if (layer === 'thai') showThai = enabled ?? !showThai;
      if (layer === 'dien_chan') showDienChan = enabled ?? !showDienChan;
      const chkP = document.getElementById('chkShowPoints');
      const chkM = document.getElementById('chkShowMeridians');
      const chkT = document.getElementById('chkShowThai');
      const chkD = document.getElementById('chkShowDienChan');
      if (chkP) chkP.checked = showPoints;
      if (chkM) chkM.checked = showMeridians;
      if (chkT) chkT.checked = showThai;
      if (chkD) chkD.checked = showDienChan;
      render();
    } else if (action === 'select_acupoint' && code) {
      selectPoint(code.toUpperCase(), true);
    } else if (action === 'filter_meridians' && region) {
      filterRegion = region;
      render();
    }
  });

  // Expose API
  window.__mskMeridians = {
    render,
    selectPoint,
    toggleLayer: (layer, enabled) => {
      if (layer === 'points') showPoints = enabled;
      if (layer === 'meridians') showMeridians = enabled;
      if (layer === 'thai') showThai = enabled;
      if (layer === 'dien_chan') showDienChan = enabled;
      render();
    },
    getData: () => acuData,
  };

  // Initialize
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
