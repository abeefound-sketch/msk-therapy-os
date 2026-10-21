// MSK-Therapy-OS: 3D Acupuncture & Traditional Meridian Visualization Layer
// Calibrated to BodyParts3D 4.0 Anatomical Ground Truth (FMA Standards)
// Enhanced with JICio Surface Registration + Meridian Studio Authoring Pipeline
(() => {
  'use strict';

  let acuData = null;
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
  let showSurfaceReference = false; // Optional reference in Musculoskeletal mode

  const overlaySvg = document.getElementById('acupunctureOverlay');
  if (!overlaySvg) return;

  // Create SVG element containers with glow filter
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

  // Camera facing / occlusion test using 3D surface normal whenever available
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
  }

  // Fast inline projection supporting both single viewport and comparative dual-split
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
  }

  function matchesRegion(reg, target) {
    if (target === 'all') return true;
    if (target === 'neck_shoulder') return ['neck', 'shoulder', 'upper_back'].includes(reg);
    if (target === 'neck') return reg === 'neck';
    if (target === 'shoulder') return reg === 'shoulder';
    if (target === 'head') return reg === 'head';
    if (target === 'arm') return reg === 'arm';
    if (target === 'leg') return reg === 'leg';
    if (target === 'back') return ['upper_back', 'low_back'].includes(reg);
    if (target === 'torso') return reg === 'torso';
    return true;
  }

  function render() {
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

    // 1. Render Continuous Surface-Conforming Meridians (10,762 Vertices)
    if (!showMeridians) {
      groupMeridians.innerHTML = '';
    } else {
      let pathsHtml = '';
      const verifiedMeridianCodes = ['GV', 'BL', 'GB', 'SI', 'TE', 'LI'];

      for (const mCode in acuData.meridians) {
        // Filter: individual meridian channel
        if (filterMeridian !== 'all' && mCode !== filterMeridian) continue;
        // If verified only, only render verified pathways unless full body view is selected
        if (verifiedOnly && filterRegion !== 'all' && !verifiedMeridianCodes.includes(mCode)) continue;

        const m = acuData.meridians[mCode];
        for (const p of m.paths || []) {
          const pts = p.surface_vertices || p.points;
          if (!pts || pts.length < 2) continue;

          // Bilateral handling: if path has explicit side, render directly.
          // Otherwise, mirror if not midline.
          let pointSets;
          if (p.side) {
            pointSets = [pts];
          } else {
            pointSets = [pts];
            const isMidline = ['GV', 'CV'].includes(mCode);
            if (!isMidline && pts.some(pt => Math.abs(pt[0]) > 0.005)) {
              pointSets.push(pts.map(pt => [-pt[0], pt[1], pt[2]]));
            }
          }

          for (const poly of pointSets) {
            // Occlusion culling: sample points along curve
            let facingCount = 0;
            let sampleCount = 0;
            const step = Math.max(1, Math.floor(poly.length / 16));
            for (let i = 0; i < poly.length; i += step) {
              if (isFacingCamera(poly[i], r)) facingCount++;
              sampleCount++;
            }
            const pathFacing = sampleCount > 0 && (facingCount / sampleCount) >= 0.35;
            if (!r.xray && !pathFacing) continue;

            const pathOpacity = pathFacing ? "0.88" : "0.22";
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
            }

            if (d && d.includes('L')) {
              pathsHtml += `<path d="${d}" stroke="${m.color}" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="${pathOpacity}" ${pathFilter}/>`;
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
        for (const p of line.paths || []) {
          const pts = p.points || p.surface_vertices;
          if (!pts || pts.length < 2) continue;
          let d = '';
          for (let i = 0; i < pts.length; i++) {
            const s = fastProject(pts[i]);
            if (!s) continue;
            d += (d === '' ? 'M ' : ' L ') + s[0].toFixed(1) + ' ' + s[1].toFixed(1);
          }
          if (d && d.includes('L')) {
            thaiHtml += `<path d="${d}" stroke="${line.color || '#f59e0b'}" stroke-width="2.8" stroke-dasharray="6,4" fill="none" opacity="0.9" />`;
          }
        }
      }
      groupThai.innerHTML = thaiHtml;
    }

    // 3. Render Acupuncture Points (362 WHO Standard Points)
    if (!showPoints && !showSurfaceReference && !isComp) {
      groupPoints.innerHTML = '';
    } else {
      let ptsHtml = '';
      if (showPoints) {
        for (const code in acuData.points) {
        const pt = acuData.points[code];
        const isVerified = pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR';
        const isSurface = pt.registration_status === 'SURFACE_REGISTERED_FJ2810';

        // Filter: verified anchors only toggle (unless full body view is selected)
        if (verifiedOnly && filterRegion !== 'all' && !isVerified) continue;

        // Filter: individual meridian channel
        if (filterMeridian !== 'all' && pt.meridian_code !== filterMeridian) continue;

        // Filter: region
        if (!matchesRegion(pt.region, filterRegion)) continue;

        // Filter: search text
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          const matchCode = pt.code.toLowerCase().includes(q);
          const matchEn = (pt.name_en || '').toLowerCase().includes(q);
          const matchZh = (pt.name_zh || '').includes(q);
          if (!matchCode && !matchEn && !matchZh) continue;
        }

        // Bilateral point instances
        const isMidline = Math.abs(pt.position[0]) < 0.005;
        const instances = [{ pos: pt.position, side: isMidline ? 'midline' : 'right' }];
        if (!isMidline && pt.position[0] > 0.005) {
          instances.push({ pos: [-pt.position[0], pt.position[1], pt.position[2]], side: 'left' });
        }

        for (const inst of instances) {
          const s = fastProject(inst.pos);
          if (!s || s[0] < -20 || s[1] < -20 || s[0] > sw + 20 || s[1] > sh + 20) continue;

          const isSel = selectedCode === code;
          const norm = inst.side === 'left' && pt.normal ? [-pt.normal[0], pt.normal[1], pt.normal[2]] : pt.normal;
          const facing = isFacingCamera(inst.pos, r, norm);

          // Occlusion culling: hide points facing away unless X-ray is active or point is selected
          if (!r.xray && !facing && !isSel) {
            continue;
          }

          let rad = isSel ? 7 : (isVerified ? 5.5 : 4.5);
          let fill = isSel ? '#facc15' : (isVerified ? '#10b981' : (isSurface ? '#06b6d4' : '#f59e0b'));
          let stroke = isSel ? '#ffffff' : (isVerified ? '#047857' : (isSurface ? '#0891b2' : '#78350f'));
          let swidth = isSel ? 2.5 : (isVerified ? 2.0 : 1.5);
          let dash = isVerified || isSurface ? '' : 'stroke-dasharray="2,2"';
          let ptOpacity = '1.0';

          if (!facing) {
            // Occluded point depth cue
            ptOpacity = isSel ? '0.5' : '0.25';
            dash = 'stroke-dasharray="2,2"';
            stroke = '#94a3b8';
          }

          const statusLabel = isVerified ? 'VERIFIED ANCHOR' : (isSurface ? 'SURFACE REGISTERED (FJ2810)' : 'UNCERTAIN POSTURE OFFSET');

          ptsHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${rad}" fill="${fill}" stroke="${stroke}" stroke-width="${swidth}" ${dash} opacity="${ptOpacity}" class="acu-marker" data-code="${code}" data-side="${inst.side}" style="cursor:pointer;">
            <title>${pt.code} - ${pt.name_en} (${pt.name_zh}) [${statusLabel}] [${inst.side.toUpperCase()}]
Pos: [${inst.pos[0].toFixed(3)}, ${inst.pos[1].toFixed(3)}, ${inst.pos[2].toFixed(3)}]m
${!facing ? ' (Dorsal/Occluded)' : ''}</title>
          </circle>`;

          if (isSel) {
            ptsHtml += `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="14" fill="none" stroke="#facc15" stroke-width="2" stroke-dasharray="4,4" opacity="${facing ? '0.95' : '0.45'}">
              <animateTransform attributeName="transform" type="rotate" from="0 ${s[0]} ${s[1]}" to="360 ${s[0]} ${s[1]}" dur="5s" repeatCount="indefinite"/>
            </circle>`;
          }
        }
      }
      }
    // Comparative split badges and divider
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
    }

    // 4. Render Dien Chan Reflex Points
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
    window.__selectedAcupoint = pt; // Store globally for Focus Selected
    const r = getRenderer();

    // Position pin
    if (r) {
      const fastProject = createProjector(r);
      const s = fastProject(pt.position);
      const pin = document.getElementById('pin');
      if (pin && s) {
        pin.hidden = false;
        pin.style.left = s[0] + 'px';
        pin.style.top = s[1] + 'px';
        const span = pin.querySelector('span');
        if (span) {
          const statusTag = pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR' ? ' [✓ Verified]' : ' [Surface Registered]';
          span.textContent = `${pt.name_en} (${pt.code} / ${pt.name_zh})${statusTag}`;
        }
      }

      // Dynamic OrbitControls target update to the 3D acupoint!
      // This centers rotation and zooming directly on the acupoint (e.g. C7 / GV14)
      const targetPos = pt.position.slice();
      const isBackPoint = pt.position[2] < -0.035;
      const isFrontPoint = pt.position[2] > 0.035;
      const yawNorm = Math.abs(r.camera.yaw % (Math.PI * 2));
      const camFacingFront = yawNorm < 0.7 || yawNorm > 5.58;
      const camFacingBack = Math.abs(yawNorm - Math.PI) < 0.7;

      let targetYaw = r.camera.yaw;
      if (isBackPoint && camFacingFront) {
        targetYaw = Math.PI;
      } else if (isFrontPoint && camFacingBack) {
        targetYaw = 0;
      }

      // Ease distance closer for detailed acupoint inspection if currently too far
      const targetDist = Math.min(r.camera.dist, 0.48);

      r._animateTo({
        yaw: targetYaw,
        pitch: Math.max(-0.25, Math.min(0.35, r.camera.pitch)),
        dist: Math.max(0.15, targetDist),
        target: targetPos,
      });
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

    function renderPointsList() {
      const dir = document.getElementById('acuPointsDirectory');
      if (!dir) return;

      const codes = Object.keys(acuData.points).filter(code => {
        const p = acuData.points[code];
        const isVer = p.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR';
        if (verifiedOnly && filterRegion !== 'all' && !isVer) return false;
        if (!matchesRegion(p.region, filterRegion)) return false;
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          return p.code.toLowerCase().includes(q) || (p.name_en || '').toLowerCase().includes(q) || (p.name_zh || '').includes(q);
        }
        return true;
      }).sort((a, b) => {
        const vA = acuData.points[a].registration_status === 'VERIFIED_ANATOMICAL_ANCHOR' ? 0 : 1;
        const vB = acuData.points[b].registration_status === 'VERIFIED_ANATOMICAL_ANCHOR' ? 0 : 1;
        if (vA !== vB) return vA - vB;
        return a.localeCompare(b);
      });

      let listHtml = '';
      for (const code of codes) {
        const p = acuData.points[code];
        const isVer = p.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR';
        const isSurf = p.registration_status === 'SURFACE_REGISTERED_FJ2810';
        let badge = isVer 
          ? '<span style="background:#065f46; color:#a7f3d0; font-size:9px; padding:1px 4px; border-radius:3px; font-weight:600;">✓ ANCHOR</span>'
          : (isSurf ? '<span style="background:#0e7490; color:#cffafe; font-size:9px; padding:1px 4px; border-radius:3px;">FJ2810</span>' : '<span style="background:#78350f; color:#fde68a; font-size:9px; padding:1px 4px; border-radius:3px;">⚠️ UNVERIFIED</span>');

        listHtml += `
          <div class="acu-list-item" data-code="${code}" style="display:flex; justify-content:space-between; align-items:center; padding:5px 8px; font-size:11px; border-bottom:1px solid var(--line); cursor:pointer;">
            <div>
              <strong>${p.code}</strong> ${p.name_en} <small style="color:var(--muted)">(${p.name_zh})</small>
            </div>
            <div>${badge}</div>
          </div>
        `;
      }

      dir.innerHTML = listHtml || '<div style="padding:10px; color:var(--muted); font-size:11px;">No matching points.</div>';

      dir.querySelectorAll('.acu-list-item').forEach(item => {
        item.addEventListener('click', () => {
          const code = item.getAttribute('data-code');
          if (code) {
            showPoints = true;
            const chk = document.getElementById('chkShowPoints');
            if (chk) chk.checked = true;
            selectPoint(code, true);
          }
        });
      });
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
            <span>📍 3D Acupoints (362 WHO)</span>
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
            <option value="neck_shoulder" ${filterRegion === 'neck_shoulder' ? 'selected' : ''}>Neck, Shoulder & Upper Back</option>
            <option value="head" ${filterRegion === 'head' ? 'selected' : ''}>Head & Face (61 points)</option>
            <option value="arm" ${filterRegion === 'arm' ? 'selected' : ''}>Arm & Hand (57 points - LI4, LI11...)</option>
            <option value="leg" ${filterRegion === 'leg' ? 'selected' : ''}>Leg & Foot (75 points - ST36, SP6...)</option>
            <option value="back" ${filterRegion === 'back' ? 'selected' : ''}>Back (Upper & Lower - 62 points)</option>
            <option value="torso" ${filterRegion === 'torso' ? 'selected' : ''}>Torso / Chest & Abdomen (85 points)</option>
            <option value="all" ${filterRegion === 'all' ? 'selected' : ''}>Full Body (All 362 Points)</option>
          </select>
        </div>

        <div style="display:flex; flex-direction:column; gap:4px;">
          <label style="font-size:11px; color:var(--muted);">Meridian Channel:</label>
          <select id="selMeridianChannel" style="background:var(--panel-2); color:var(--bone); border:1px solid var(--line); padding:4px 6px; border-radius:var(--r-s); font-size:11px;">
            <option value="all">⚡ All 14 Meridians</option>
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
        </div>

        <div style="display:flex; flex-direction:column; gap:4px;">
          <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--muted);">
            <span>Skin Transparency:</span>
            <span id="lblAtlasSkinOpacity">78%</span>
          </div>
          <input type="range" id="rngAtlasSkinOpacity" min="0" max="100" value="78" style="cursor:pointer;" />
        </div>

        <div style="display:flex; flex-direction:column; gap:4px;">
          <input type="text" id="txtAcuSearch" placeholder="Search (e.g. LI4, ST36, Hegu, 合谷)..." style="background:var(--panel-2); color:var(--bone); border:1px solid var(--line); padding:4px 6px; border-radius:var(--r-s); font-size:11px;" />
        </div>

        <div style="font-weight:600; color:var(--bone); font-size:11px; margin-top:4px;">
          Quick Landmarks:
        </div>
        <div style="display:flex; gap:4px; flex-wrap:wrap;">
          <button class="btn-acu-quick" data-code="GB21" style="font-size:10px; padding:3px 6px; background:#065f46; color:#a7f3d0; border:1px solid #10b981; border-radius:3px; cursor:pointer;">GB21 肩井 (Trapezius)</button>
          <button class="btn-acu-quick" data-code="GV14" style="font-size:10px; padding:3px 6px; background:#065f46; color:#a7f3d0; border:1px solid #10b981; border-radius:3px; cursor:pointer;">GV14 大椎 (C7 Spine)</button>
          <button class="btn-acu-quick" data-code="GB20" style="font-size:10px; padding:3px 6px; background:#065f46; color:#a7f3d0; border:1px solid #10b981; border-radius:3px; cursor:pointer;">GB20 风池 (Suboccipital)</button>
          <button class="btn-acu-quick" data-code="LI4" style="font-size:10px; padding:3px 6px; background:#0e7490; color:#cffafe; border:1px solid #06b6d4; border-radius:3px; cursor:pointer;">LI4 合谷 (Hand/Arm)</button>
          <button class="btn-acu-quick" data-code="LI11" style="font-size:10px; padding:3px 6px; background:#0e7490; color:#cffafe; border:1px solid #06b6d4; border-radius:3px; cursor:pointer;">LI11 曲池 (Elbow)</button>
          <button class="btn-acu-quick" data-code="ST36" style="font-size:10px; padding:3px 6px; background:#0e7490; color:#cffafe; border:1px solid #06b6d4; border-radius:3px; cursor:pointer;">ST36 足三里 (Leg)</button>
          <button class="btn-acu-quick" data-code="SP6" style="font-size:10px; padding:3px 6px; background:#0e7490; color:#cffafe; border:1px solid #06b6d4; border-radius:3px; cursor:pointer;">SP6 三阴交 (Medial Leg)</button>
        </div>

        <div style="font-weight:600; color:var(--bone); font-size:11px; margin-top:6px; display:flex; justify-content:space-between;">
          <span>Points Directory:</span>
          <span id="acuPointCountBadge" style="color:#38bdf8; font-size:10px;"></span>
        </div>
        <div id="acuPointsDirectory" style="overflow-y:auto; max-height:220px; background:var(--panel-2); border-radius:var(--r-s);"></div>
      </div>
    `;

    renderPointsList();

    // Event listeners
    document.getElementById('chkShowPoints').addEventListener('change', (e) => {
      showPoints = e.target.checked;
      render();
    });
    document.getElementById('chkVerifiedOnly').addEventListener('change', (e) => {
      verifiedOnly = e.target.checked;
      renderPointsList();
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
      renderPointsList();
      render();
    });
    const selChan = document.getElementById('selMeridianChannel');
    if (selChan) selChan.addEventListener('change', (e) => {
      filterMeridian = e.target.value;
      renderPointsList();
      render();
    });
    const rngSkin = document.getElementById('rngAtlasSkinOpacity');
    if (rngSkin) rngSkin.addEventListener('input', (e) => {
      const alpha = parseInt(e.target.value, 10) / 100;
      const lbl = document.getElementById('lblAtlasSkinOpacity');
      if (lbl) lbl.textContent = e.target.value + '%';
      const r = getRenderer();
      if (r) r.setSkinOpacity(alpha);
      render();
    });

    document.getElementById('txtAcuSearch').addEventListener('input', (e) => {
      searchQuery = e.target.value.trim();
      renderPointsList();
      render();
    });

    panel.querySelectorAll('.btn-acu-quick').forEach(btn => {
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
    if (ev.data.action === 'clear_selection' || ev.data.action === 'reset_view') {
      selectedCode = null;
      const pin = document.getElementById('pin');
      if (pin) pin.hidden = true;
      render();
    } else if (ev.data.action === 'select_acupoint') {
      showPoints = true;
      const chk = document.getElementById('chkShowPoints');
      if (chk) chk.checked = true;
      selectPoint(ev.data.code, true);
    } else if (ev.data.action === 'set_render_mode') {
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
      filterRegion = ev.data.region || 'neck_shoulder';
      const sel = document.getElementById('selAcuRegion');
      if (sel) sel.value = filterRegion;

      const r = getRenderer();
      if (filterRegion === 'all' && r) {
        // Automatically zoom out to full body overview
        r.camera.target = [0, 0.85, 0];
        r.camera.dist = 2.45;
        r.camera.pitch = 0.02;
        r.camera.yaw = 0.0;
        showMeridians = true;
        const cMer = document.getElementById('chkShowMeridians');
        if (cMer) cMer.checked = true;
        if (typeof r._draw === 'function') r._draw();
      }
      buildSidebarControls();
      render();
    } else if (ev.data.action === 'update_point_coords') {
      // Live coordinate update from Meridian Studio Editor (Requirement 9)
      const { code, position, normal, registration_status, source_provenance, notes } = ev.data;
      if (acuData && acuData.points[code]) {
        const pt = acuData.points[code];
        if (position) pt.position = position;
        if (normal) pt.normal = normal;
        if (registration_status) pt.registration_status = registration_status;
        if (source_provenance) pt.source_provenance = source_provenance;
        if (notes) pt.verification_notes = notes;
        selectPoint(code, false);
        render();
        console.log(`[meridians.js] Live calibrated point ${code}:`, position);
      }
    } else if (ev.data.action === 'load_custom_points') {
      if (acuData && ev.data.points) {
        Object.assign(acuData.points, ev.data.points);
        buildSidebarControls();
        render();
        console.log(`[meridians.js] Loaded ${Object.keys(ev.data.points).length} custom points.`);
      }
    } else if (ev.data.action === 'reset_points_baseline') {
      loadData();
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

  window.__meridiansDebug = {
    get acuData() { return acuData; },
    selectPoint,
    render,
    setSurfaceReference: (on) => {
      showSurfaceReference = Boolean(on);
      const r = getRenderer();
      if (r) r.setSkinReference(showSurfaceReference);
      render();
    },
    setFilterMeridian: (code) => {
      filterMeridian = code || 'all';
      render();
    },
    setRenderMode: (mode) => {
      const r = getRenderer();
      if (r) r.setRenderMode(mode);
      render();
    }
  };
})();
