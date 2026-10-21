from pathlib import Path

# ==============================================================================
# 3. Patch msk_therapy_os/static/atlas/meridians.js
# ==============================================================================
merid_js_path = Path("msk_therapy_os/static/atlas/meridians.js")
merid_js = merid_js_path.read_text(encoding="utf-8")

# A. verifiedMeridianCodes and channel selection logic
old_merid_loop = """      const verifiedMeridianCodes = ['GV', 'BL', 'GB', 'SI', 'TE', 'LI'];

      for (const mCode in acuData.meridians) {
        // Filter: individual meridian channel
        if (filterMeridian !== 'all' && mCode !== filterMeridian) continue;
        // If verified only, only render verified pathways unless full body view is selected
        if (verifiedOnly && filterRegion !== 'all' && !verifiedMeridianCodes.includes(mCode)) continue;"""

new_merid_loop = """      const verifiedMeridianCodes = ['GV', 'CV', 'BL', 'GB', 'SI', 'TE', 'LI', 'LU', 'ST', 'SP', 'HT', 'KI', 'PC', 'LR'];

      for (const mCode in acuData.meridians) {
        // Filter: individual meridian channel
        if (filterMeridian !== 'all') {
          if (mCode !== filterMeridian) continue;
          // When a specific channel is selected (e.g. CV Ren Mai), do not suppress it with verifiedOnly or region filter
        } else {
          // If verified only in multi-meridian view, only render verified pathways unless full body view is selected
          if (verifiedOnly && filterRegion !== 'all' && !verifiedMeridianCodes.includes(mCode)) continue;
        }"""

assert old_merid_loop in merid_js, "old_merid_loop not found in meridians.js"
merid_js = merid_js.replace(old_merid_loop, new_merid_loop, 1)

# B. Pathway subpath handling to prevent joining disconnected segments
old_path_loop = """            const pathOpacity = pathFacing ? "0.88" : "0.22";
            const pathFilter = pathFacing ? 'filter="url(#glow)"' : '';
            let d = '';

            for (let i = 0; i < poly.length; i++) {
              const pt = poly[i];
              // Optional region filter for meridian paths
              if (filterRegion === 'neck_shoulder' && (pt[1] < 1.15 || pt[1] > 1.68)) continue;
              if (filterRegion === 'neck' && (pt[1] < 1.32 || pt[1] > 1.58)) continue;
              if (filterRegion === 'shoulder' && (pt[1] < 1.25 || pt[1] > 1.60 || Math.abs(pt[0]) < 0.08)) continue;
              if (filterRegion === 'head' && pt[1] < 1.50) continue;
              if (filterRegion === 'arm' && (Math.abs(pt[0]) < 0.16 || pt[1] > 1.45)) continue;
              if (filterRegion === 'leg' && pt[1] > 0.95) continue;
              if (filterRegion === 'upper_back' && (pt[1] < 1.15 || pt[1] > 1.55 || pt[2] > 0.0)) continue;
              if (filterRegion === 'low_back' && (pt[1] < 0.82 || pt[1] > 1.18 || pt[2] > 0.0)) continue;
              if (filterRegion === 'torso' && (pt[1] < 0.85 || pt[1] > 1.45 || Math.abs(pt[0]) > 0.22)) continue;

              const s = fastProject(pt);
              if (!s) continue;
              d += (d === '' ? 'M ' : ' L ') + s[0].toFixed(1) + ' ' + s[1].toFixed(1);
            }"""

new_path_loop = """            const pathOpacity = pathFacing ? "0.88" : "0.22";
            const pathFilter = pathFacing ? 'filter="url(#glow)"' : '';
            let d = '';
            let inSubpath = false;

            for (let i = 0; i < poly.length; i++) {
              const pt = poly[i];
              // Optional region filter for meridian paths when in 'all' multi-channel overview
              if (filterMeridian === 'all') {
                if (filterRegion === 'neck_shoulder' && (pt[1] < 1.15 || pt[1] > 1.68)) { inSubpath = false; continue; }
                if (filterRegion === 'neck' && (pt[1] < 1.32 || pt[1] > 1.58)) { inSubpath = false; continue; }
                if (filterRegion === 'shoulder' && (pt[1] < 1.25 || pt[1] > 1.60 || Math.abs(pt[0]) < 0.08)) { inSubpath = false; continue; }
                if (filterRegion === 'head' && pt[1] < 1.50) { inSubpath = false; continue; }
                if (filterRegion === 'arm' && (Math.abs(pt[0]) < 0.16 || pt[1] > 1.45)) { inSubpath = false; continue; }
                if (filterRegion === 'leg' && pt[1] > 0.95) { inSubpath = false; continue; }
                if (filterRegion === 'upper_back' && (pt[1] < 1.15 || pt[1] > 1.55 || pt[2] > 0.0)) { inSubpath = false; continue; }
                if (filterRegion === 'low_back' && (pt[1] < 0.82 || pt[1] > 1.18 || pt[2] > 0.0)) { inSubpath = false; continue; }
                if (filterRegion === 'torso' && (pt[1] < 0.85 || pt[1] > 1.45 || Math.abs(pt[0]) > 0.22)) { inSubpath = false; continue; }
              }

              const s = fastProject(pt);
              if (!s) { inSubpath = false; continue; }
              if (!inSubpath) {
                d += (d ? ' ' : '') + `M ${s[0].toFixed(1)} ${s[1].toFixed(1)}`;
                inSubpath = true;
              } else {
                d += ` L ${s[0].toFixed(1)} ${s[1].toFixed(1)}`;
              }
            }"""

assert old_path_loop in merid_js, "old_path_loop not found in meridians.js"
merid_js = merid_js.replace(old_path_loop, new_path_loop, 1)

# C. Dien Chan marker rendering with selection animation
old_dc_render = """    // 4. Render Dien Chan Reflex Points
    if (!showDienChan) {
      groupDienChan.innerHTML = '';
    } else {
      let dcHtml = '';
      for (const dc of acuData.dien_chan || []) {
        const s = fastProject(dc.position);
        if (!s || s[0] < -10 || s[1] < -10 || s[0] > sw + 10 || s[1] > sh + 10) continue;
        dcHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="4.5" fill="#ec4899" stroke="#ffffff" stroke-width="1.5" class="acu-marker" data-code="${dc.code}">
          <title>${dc.name} [Dien Chan]</title>
        </circle>`;
      }
      groupDienChan.innerHTML = dcHtml;
    }"""

new_dc_render = """    // 4. Render Dien Chan Reflex Points (4 Records: DIEN-26, DIEN-19, DIEN-34, DIEN-61)
    if (!showDienChan) {
      groupDienChan.innerHTML = '';
    } else {
      let dcHtml = '';
      for (const dc of acuData.dien_chan || []) {
        const s = fastProject(dc.position);
        if (!s || s[0] < -10 || s[1] < -10 || s[0] > sw + 10 || s[1] > sh + 10) continue;
        const isSel = selectedCode === dc.code;
        const fill = isSel ? '#facc15' : '#ec4899';
        const rad = isSel ? 6.5 : 5.0;
        const stroke = isSel ? '#ffffff' : '#be185d';
        dcHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${rad}" fill="${fill}" stroke="${stroke}" stroke-width="2.0" class="acu-marker" data-code="${dc.code}" style="cursor:pointer;">
          <title>${dc.code} - ${dc.name} [Vietnamese Dien Chan Reflex - 4 records incomplete educational dataset]</title>
        </circle>`;
        if (isSel) {
          dcHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="14" fill="none" stroke="#facc15" stroke-width="2" stroke-dasharray="4,4">
            <animateTransform attributeName="transform" type="rotate" from="0 ${s[0]} ${s[1]}" to="360 ${s[0]} ${s[1]}" dur="4s" repeatCount="indefinite"/>
          </circle>`;
        }
      }
      groupDienChan.innerHTML = dcHtml;
    }"""

assert old_dc_render in merid_js, "old_dc_render not found in meridians.js"
merid_js = merid_js.replace(old_dc_render, new_dc_render, 1)

# D. Click event routing: distinguish Dien Chan from WHO acupuncture points
old_click = """  // Handle marker click
  overlaySvg.addEventListener('click', (ev) => {
    const target = ev.target.closest('.acu-marker');
    if (!target) return;
    const code = target.getAttribute('data-code');
    if (!code) return;
    selectPoint(code, true);
  });"""

new_click = """  // Handle marker click (Routes WHO acupoints vs Vietnamese Dien Chan independently)
  overlaySvg.addEventListener('click', (ev) => {
    const target = ev.target.closest('.acu-marker');
    if (!target) return;
    const code = target.getAttribute('data-code');
    if (!code) return;
    if (code.startsWith('DIEN-')) {
      selectDienChanPoint(code, true);
    } else {
      selectPoint(code, true);
    }
  });

  // Dedicated Dien Chan selection handler (Requirement C - never route via WHO lookup)
  function selectDienChanPoint(code, notifyParent = true) {
    if (!acuData || !acuData.dien_chan) return;
    const dc = acuData.dien_chan.find(d => d.code === code);
    if (!dc) return;
    selectedCode = code;
    window.__selectedDienChan = dc;
    window.__selectedAcupoint = null;

    const r = getRenderer();
    if (r) {
      const fastProject = createProjector(r);
      const s = fastProject(dc.position);
      const pin = document.getElementById('pin');
      if (pin && s) {
        pin.hidden = false;
        pin.style.left = s[0] + 'px';
        pin.style.top = s[1] + 'px';
        const span = pin.querySelector('span');
        if (span) {
          span.textContent = `${dc.name} [🇻🇳 Dien Chan Reflex]`;
        }
      }

      // Smooth camera focus to face
      r._animateTo({
        yaw: 0.0,
        pitch: 0.03,
        dist: 0.38,
        target: [0, 1.65, 0.05],
      });
    }

    render();

    if (notifyParent && window.parent && window.parent !== window) {
      window.parent.postMessage({
        type: 'msk_dien_chan_selected',
        point: {
          code: dc.code,
          name: dc.name,
          position: dc.position,
          indication: dc.indication,
          target_region: dc.target_region,
          source: 'Bùi Quốc Châu Facial Reflexology (1980)',
          domain: 'VIETNAMESE_DIEN_CHAN',
          dataset_notice: '4 available records — incomplete educational dataset (Reflexology/Non-WHO)',
          registration_status: 'SURFACE_REGISTERED_FACIAL_FJ2810',
          clinical_review_status: 'UNVERIFIED',
          limitations: 'Facial reflex projections are traditional somatotopic representations and must not be conflated with WHO peripheral acupuncture points.'
        }
      }, '*');
    }
  }"""

assert old_click in merid_js, "old_click not found in meridians.js"
merid_js = merid_js.replace(old_click, new_click, 1)

# E. set_filter_meridian message handler with auto-enabling and smart camera orienting
old_set_filter = """    } else if (ev.data.action === 'set_filter_meridian') {
      filterMeridian = ev.data.meridian || 'all';
      render();"""

new_set_filter = """    } else if (ev.data.action === 'set_filter_meridian') {
      filterMeridian = ev.data.meridian || 'all';
      if (filterMeridian !== 'all') {
        showMeridians = true;
        showPoints = true;
        const cMer = document.getElementById('chkShowMeridians');
        if (cMer) cMer.checked = true;
        const cPts = document.getElementById('chkShowPoints');
        if (cPts) cPts.checked = true;

        const r = getRenderer();
        if (r) {
          if (filterMeridian === 'CV') {
            r.camera.yaw = 0.0;
            r.camera.pitch = 0.02;
            if (typeof r._draw === 'function') r._draw();
          } else if (filterMeridian === 'GV' || filterMeridian === 'BL') {
            r.camera.yaw = Math.PI;
            r.camera.pitch = 0.02;
            if (typeof r._draw === 'function') r._draw();
          }
        }
      }
      renderPointsList();
      render();
      if (window.parent && window.parent !== window && ev.data.requestId) {
        window.parent.postMessage({
          type: 'msk_ack',
          requestId: ev.data.requestId,
          action: 'set_filter_meridian',
          meridian: filterMeridian,
          showMeridians: showMeridians,
          showPoints: showPoints
        }, '*');
      }"""

assert old_set_filter in merid_js, "old_set_filter not found in meridians.js"
merid_js = merid_js.replace(old_set_filter, new_set_filter, 1)

# F. Export selectDienChanPoint in debug API
old_debug = """  window.__meridiansDebug = {
    get acuData() { return acuData; },
    selectPoint,
    render,"""

new_debug = """  window.__meridiansDebug = {
    get acuData() { return acuData; },
    selectPoint,
    selectDienChanPoint,
    render,"""

assert old_debug in merid_js, "old_debug not found in meridians.js"
merid_js = merid_js.replace(old_debug, new_debug, 1)

merid_js_path.write_text(merid_js, encoding="utf-8")
print("✓ meridians.js patched successfully")
