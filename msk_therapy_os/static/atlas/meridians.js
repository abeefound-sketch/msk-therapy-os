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
  let activeDienChanProtocol = null;
  let dienChanProtocolOnly = false;

  let verifiedOnly = true; // Default to verified anatomical anchors only

  let filterRegion = 'neck_shoulder'; // Focus scenario

  let filterMeridian = 'all'; // 'all' or specific meridian code (e.g. 'GV', 'BL', 'GB')

  let selectedCode = null;

  let searchQuery = '';

  let showSurfaceReference = false;
  let currentP9LayerMode = 'canonical'; // 'canonical' | 'legacy_raycast' | 'upstream_raw' | 'pose_adjusted'

  // Authoritative Unified Spatial State
  const AtlasSpatialState = {
    meshId: 'FJ2810',
    layerMode: 'canonical',
    morphology: {
      height_cm: 172.0,
      shoulder_width_cm: 42.0,
      arm_circ_cm: 28.0,
      waist_circ_cm: 75.0,
      thigh_circ_cm: 54.0,
      calf_circ_cm: 36.0,
    },
    pose: {
      joint_angles: {
        cervical_flexion: 0.0,
        cervical_extension: 0.0,
        shoulder_abduction_r: 0.0,
        shoulder_abduction_l: 0.0,
        elbow_flexion_r: 0.0,
        elbow_flexion_l: 0.0,
        knee_flexion_r: 0.0,
        knee_flexion_l: 0.0,
      }
    },
    geometryVersion: 0,
    isResolving: false,
    resolvedData: null,
  };



  const overlaySvg = document.getElementById('acupunctureOverlay');

  if (!overlaySvg) return;



  // Create SVG element containers with glow filter and dynamic viewport clipping

  overlaySvg.innerHTML = `

    <defs>

      <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">

        <feGaussianBlur stdDeviation="2" result="blur" />

        <feComposite in="SourceGraphic" in2="blur" operator="over" />

      </filter>

      <clipPath id="overlayViewportClip">

        <rect id="overlayClipRect" x="0" y="0" width="100%" height="100%"/>

      </clipPath>

    </defs>

    <g id="overlayContent" clip-path="url(#overlayViewportClip)">

      <g id="groupMeridians"></g>

      <g id="groupThai"></g>

      <g id="groupPoints"></g>

      <g id="groupDienChan"></g>

    </g>

    <g id="groupComparativeOverlay"></g>

  `;



  const overlayClipRect = document.getElementById('overlayClipRect');

  const groupMeridians = document.getElementById('groupMeridians');

  const groupThai = document.getElementById('groupThai');

  const groupPoints = document.getElementById('groupPoints');

  const groupDienChan = document.getElementById('groupDienChan');

  const groupComparativeOverlay = document.getElementById('groupComparativeOverlay');



  // Load consolidated 3D dataset


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


  async function resolveSpatialGeometry(force = false) {
    if (!acuData) return;
    const currentGeneration = ++AtlasSpatialState.geometryVersion;
    AtlasSpatialState.isResolving = true;

    try {
      const resp = await fetch('/api/atlas/geometry/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          layer_mode: AtlasSpatialState.layerMode,
          morphology: AtlasSpatialState.morphology,
          pose: AtlasSpatialState.pose,
          mesh_id: AtlasSpatialState.meshId,
          client_generation: currentGeneration,
        }),
      });

      if (!resp.ok) {
        console.warn('[meridians.js] POST /api/atlas/geometry/resolve returned status', resp.status);
        AtlasSpatialState.isResolving = false;
        return;
      }

      const resData = await resp.json();

      // Guard against race conditions: Ignore if a newer request was dispatched
      if (resData.client_generation !== AtlasSpatialState.geometryVersion) {
        return;
      }

      AtlasSpatialState.resolvedData = resData;
      AtlasSpatialState.isResolving = false;

      // Update points in acuData
      if (resData.points && acuData.points) {
        for (const code in resData.points) {
          const rPt = resData.points[code];
          if (acuData.points[code]) {
            Object.assign(acuData.points[code], rPt);
          } else {
            acuData.points[code] = rPt;
          }
        }
      }

      // Update meridians in acuData
      if (resData.meridians && acuData.meridians) {
        for (const mCode in resData.meridians) {
          if (acuData.meridians[mCode] && resData.meridians[mCode].paths) {
            acuData.meridians[mCode].paths = resData.meridians[mCode].paths;
          }
        }
      }

      // Update QA Inspector if a point is selected
      if (selectedCode && acuData.points[selectedCode]) {
        updateP9QAInspector(acuData.points[selectedCode]);
      }

      render(true);
    } catch (e) {
      console.error('[meridians.js] Resolution error:', e);
      AtlasSpatialState.isResolving = false;
    }
  }

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

      // Load authoritative Dien Chan points from /api/dien-chan/points
      try {
        const dcRes = await fetch('/api/dien-chan/points');
        if (dcRes.ok) {
          const dcJson = await dcRes.json();
          if (dcJson && dcJson.points) {
            acuData.dien_chan = dcJson.points.map(pt => ({
              code: pt.point_code,
              point_code: pt.point_code,
              name: pt.name_vi,
              name_vi: pt.name_vi,
              name_en: pt.name_en,
              name_zh: pt.name_zh,
              position: pt.position,
              resolved_world_position: pt.position,
              normal: pt.surface_normal,
              surface_normal: pt.surface_normal,
              grid_coordinate: pt.grid_coordinate,
              review_status: pt.review_status,
              uncertainty_mm: pt.uncertainty_mm,
              projection_residual_mm: pt.projection_residual_mm,
              fma_anchor: pt.fma_anchor,
              system: 'lib_dien_chan',
              domain: 'VIETNAMESE_DIEN_CHAN',
              laterality: pt.laterality,
              anatomical_region: pt.anatomical_region,
              anatomical_location_vi: pt.anatomical_location_vi,
              source_image_id: pt.source_id,
            }));
          }
        }
      } catch (errDc) {
        console.warn('Could not load /api/dien-chan/points, fallback to baked:', errDc);
      }

      buildSidebarControls();
      await resolveSpatialGeometry(true);
      render(true);

    } catch (err) {
      console.error('Failed to load acupuncture 3D dataset:', err);
    }
  }



  function getRenderer() {

    return window.__atlasDebug ? window.__atlasDebug.renderer : null;

  }

  function setDienChanCameraView(view) {
    const r = getRenderer();
    if (!r) return;
    if (view === 'front') {
      r._animateTo({
        yaw: 0.0,
        pitch: 0.02,
        dist: 0.42,
        target: [0.0, 1.62, 0.06],
      });
    } else if (view === 'left_profile') {
      r._animateTo({
        yaw: -1.57,
        pitch: 0.02,
        dist: 0.42,
        target: [0.0, 1.62, 0.06],
      });
    } else if (view === 'right_profile') {
      r._animateTo({
        yaw: 1.57,
        pitch: 0.02,
        dist: 0.42,
        target: [0.0, 1.62, 0.06],
      });
    }
    render(true);
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



  // ---------------------------------------------------------------------------

  // Topologically-Preserving Viewport Projection & Frustum Clipping Engine

  // ---------------------------------------------------------------------------



  // 4D Homogeneous Near-Plane Segment Clipping (w >= wNear)

  function clipSegmentNearPlane(c0, c1, wNear = 0.005) {

    const w0 = c0[3];

    const w1 = c1[3];

    if (w0 < wNear && w1 < wNear) return null;

    let cc0 = c0;

    let cc1 = c1;

    if (w0 < wNear && w1 >= wNear) {

      const t = (wNear - w0) / (w1 - w0);

      cc0 = [

        c0[0] + t * (c1[0] - c0[0]),

        c0[1] + t * (c1[1] - c0[1]),

        c0[2] + t * (c1[2] - c0[2]),

        wNear

      ];

    } else if (w0 >= wNear && w1 < wNear) {

      const t = (wNear - w0) / (w1 - w0);

      cc1 = [

        c0[0] + t * (c1[0] - c0[0]),

        c0[1] + t * (c1[1] - c0[1]),

        c0[2] + t * (c1[2] - c0[2]),

        wNear

      ];

    }

    return [cc0, cc1];

  }



  // 2D Liang-Barsky Segment Clipping against strict screen bounds [xmin, ymin, xmax, ymax]

  function clipSegment2D(x0, y0, x1, y1, bounds) {

    const [xmin, ymin, xmax, ymax] = bounds;

    const dx = x1 - x0;

    const dy = y1 - y0;

    const p = [-dx, dx, -dy, dy];

    const q = [x0 - xmin, xmax - x0, y0 - ymin, ymax - y0];

    let u1 = 0.0;

    let u2 = 1.0;



    for (let i = 0; i < 4; i++) {

      if (p[i] === 0) {

        if (q[i] < 0) return null; // Parallel and outside

      } else {

        const t = q[i] / p[i];

        if (p[i] < 0) {

          if (t > u2) return null;

          if (t > u1) u1 = t;

        } else {

          if (t < u1) return null;

          if (t < u2) u2 = t;

        }

      }

    }



    const cx0 = Math.max(xmin, Math.min(xmax, x0 + u1 * dx));

    const cy0 = Math.max(ymin, Math.min(ymax, y0 + u1 * dy));

    const cx1 = Math.max(xmin, Math.min(xmax, x0 + u2 * dx));

    const cy1 = Math.max(ymin, Math.min(ymax, y0 + u2 * dy));

    return [[cx0, cy0], [cx1, cy1]];

  }



  // Project single 3D point to 2D viewport coordinates with near-plane and bounds validation

  function projectPoint(pos, vp, viewport) {

    const x = vp[0] * pos[0] + vp[4] * pos[1] + vp[8] * pos[2] + vp[12];

    const y = vp[1] * pos[0] + vp[5] * pos[1] + vp[9] * pos[2] + vp[13];

    const w = vp[3] * pos[0] + vp[7] * pos[1] + vp[11] * pos[2] + vp[15];

    if (w <= 0.005) return null;



    const ndcX = x / w;

    const ndcY = y / w;

    if (!isFinite(ndcX) || !isFinite(ndcY)) return null;



    const sx = viewport.x + (ndcX * 0.5 + 0.5) * viewport.width;

    const sy = viewport.y + (1.0 - (ndcY * 0.5 + 0.5)) * viewport.height;



    const [xmin, ymin, xmax, ymax] = viewport.clippingBounds;

    if (sx < xmin || sx > xmax || sy < ymin || sy > ymax) return null;

    return [sx, sy];

  }



  // Topology-preserving 3D-to-2D polyline segment projection and clipping

  function projectAndClipPolyline(pts, vp, viewport, filterFn = null) {

    if (!pts || pts.length < 2) return '';

    let d = '';

    let lastPoint = null;



    for (let i = 0; i < pts.length - 1; i++) {

      const p0 = pts[i];

      const p1 = pts[i + 1];



      if (filterFn && (!filterFn(p0) || !filterFn(p1))) {

        lastPoint = null;

        continue;

      }



      // 1. Transform to 4D clip space

      const c0 = [

        vp[0] * p0[0] + vp[4] * p0[1] + vp[8] * p0[2] + vp[12],

        vp[1] * p0[0] + vp[5] * p0[1] + vp[9] * p0[2] + vp[13],

        vp[2] * p0[0] + vp[6] * p0[1] + vp[10] * p0[2] + vp[14],

        vp[3] * p0[0] + vp[7] * p0[1] + vp[11] * p0[2] + vp[15]

      ];

      const c1 = [

        vp[0] * p1[0] + vp[4] * p1[1] + vp[8] * p1[2] + vp[12],

        vp[1] * p1[0] + vp[5] * p1[1] + vp[9] * p1[2] + vp[13],

        vp[2] * p1[0] + vp[6] * p1[1] + vp[10] * p1[2] + vp[14],

        vp[3] * p1[0] + vp[7] * p1[1] + vp[11] * p1[2] + vp[15]

      ];



      // 2. Homogeneous near-plane clip

      const clippedClip = clipSegmentNearPlane(c0, c1, 0.005);

      if (!clippedClip) {

        lastPoint = null;

        continue;

      }



      const [cc0, cc1] = clippedClip;



      // 3. Perspective division & viewport mapping

      const ndc0X = cc0[0] / cc0[3];

      const ndc0Y = cc0[1] / cc0[3];

      const ndc1X = cc1[0] / cc1[3];

      const ndc1Y = cc1[1] / cc1[3];

      if (!isFinite(ndc0X) || !isFinite(ndc0Y) || !isFinite(ndc1X) || !isFinite(ndc1Y)) {

        lastPoint = null;

        continue;

      }



      const s0x = viewport.x + (ndc0X * 0.5 + 0.5) * viewport.width;

      const s0y = viewport.y + (1.0 - (ndc0Y * 0.5 + 0.5)) * viewport.height;

      const s1x = viewport.x + (ndc1X * 0.5 + 0.5) * viewport.width;

      const s1y = viewport.y + (1.0 - (ndc1Y * 0.5 + 0.5)) * viewport.height;



      // 4. 2D Viewport bounds clip (Liang-Barsky)

      const clipped2D = clipSegment2D(s0x, s0y, s1x, s1y, viewport.clippingBounds);

      if (!clipped2D) {

        lastPoint = null;

        continue;

      }



      const [[q0x, q0y], [q1x, q1y]] = clipped2D;



      // 5. Topology-preserving SVG path construction

      if (lastPoint && Math.hypot(q0x - lastPoint[0], q0y - lastPoint[1]) < 0.6) {

        d += ` L ${q1x.toFixed(1)} ${q1y.toFixed(1)}`;

      } else {

        d += (d ? ' ' : '') + `M ${q0x.toFixed(1)} ${q0y.toFixed(1)} L ${q1x.toFixed(1)} ${q1y.toFixed(1)}`;

      }

      lastPoint = [q1x, q1y];

    }



    return d;

  }



  function matchesRegionPath(pt, filterRegion) {

    if (filterRegion === 'all') return true;

    if (filterRegion === 'neck_shoulder' && (pt[1] < 1.15 || pt[1] > 1.68)) return false;

    if (filterRegion === 'neck' && (pt[1] < 1.32 || pt[1] > 1.58)) return false;

    if (filterRegion === 'shoulder' && (pt[1] < 1.25 || pt[1] > 1.60 || Math.abs(pt[0]) < 0.08)) return false;

    if (filterRegion === 'head' && pt[1] < 1.50) return false;

    if (filterRegion === 'arm' && (Math.abs(pt[0]) < 0.16 || pt[1] > 1.45)) return false;

    if (filterRegion === 'leg' && pt[1] > 0.95) return false;

    if (filterRegion === 'upper_back' && (pt[1] < 1.15 || pt[1] > 1.55 || pt[2] > 0.0)) return false;

    if (filterRegion === 'low_back' && (pt[1] < 0.82 || pt[1] > 1.18 || pt[2] > 0.0)) return false;

    if (filterRegion === 'torso' && (pt[1] < 0.85 || pt[1] > 1.45 || Math.abs(pt[0]) > 0.22)) return false;

    return true;

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



  function render(force = false) {
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
      AtlasSpatialState.layerMode,
      AtlasSpatialState.geometryVersion,
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

        let instances = [];
        if (pt.instances && pt.instances.length > 0) {
          instances = pt.instances.map(inst => ({
            pos: inst.position,
            side: inst.side,
            normal: inst.normal
          }));
        } else {
          const pos = pt.resolved_world_position || pt.position;
          const isMidline = Math.abs(pos[0]) < 0.005;
          instances = [{ pos: pos, side: isMidline ? 'midline' : 'right', normal: pt.normal }];
          if (!isMidline && pos[0] > 0.005) {
            instances.push({ pos: [-pos[0], pos[1], pos[2]], side: 'left', normal: pt.normal ? [-pt.normal[0], pt.normal[1], pt.normal[2]] : null });
          }
        }

        for (const inst of instances) {
          const s = projectPoint(inst.pos, vp, viewport);
          if (!s) continue;

          const isSel = (selectedCode === code);
          const norm = inst.normal || (inst.side === 'left' && pt.normal ? [-pt.normal[0], pt.normal[1], pt.normal[2]] : pt.normal);
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
        const isProtoPt = Boolean(activeDienChanProtocol && activeDienChanProtocol.point_codes && activeDienChanProtocol.point_codes.includes(dc.code));
        if (dienChanProtocolOnly && !isProtoPt) {
          continue;
        }

        const s = projectPoint(dc.position, vp, viewport);
        if (!s) continue;

        const isSel = (selectedCode === dc.code);
        const facing = isFacingCamera(dc.position, r, dc.normal || null);
        if (!r.xray && !facing && !isSel) continue;

        candidates.push({
          code: dc.code,
          pt: dc,
          inst: { pos: dc.position, side: dc.laterality || 'midline' },
          screen: s,
          facing,
          isSel,
          isProtoPt,
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
        const titleText = `[Cluster: ${c.count} points (${c.system.toUpperCase()})]\n${c.members.map(m => `${m.code} - ${m.pt.name_en || m.pt.name || ''}`).join('\n')}\nClick to zoom in and expand`;

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
        const isSurface = (pt.registration_status === 'SURFACE_REGISTERED_FJ2810' || pt.registration_status === 'GEOMETRIC_SURFACE_APPROXIMATION');
        const isUncertain = (pt.registration_status === 'UNCERTAIN_POSTURE_OFFSET');
        const isUpstream = (pt.registration_status === 'UPSTREAM_TRANSFORMED');
        const isLegacy = (pt.registration_status === 'LEGACY_SURFACE_RAYCAST');
        const isDienChan = Boolean(item.system && item.system.startsWith('lib_dien_chan'));
        const isProtoPt = Boolean(item.isProtoPt);

        const vis = VisualScaleEngine.getMarkerVisuals(displaySettings, scaleInfo, isSel, isVerified, isSurface, isDienChan);

        let fill = isSel ? '#facc15' : (isProtoPt ? '#f43f5e' : (isUncertain ? '#f59e0b' : (isVerified ? '#10b981' : (isDienChan ? '#ec4899' : (isSurface ? '#06b6d4' : (isUpstream ? '#6366f1' : '#64748b'))))));
        let stroke = isSel ? '#ffffff' : (isProtoPt ? '#fbbf24' : (isUncertain ? '#b45309' : (isVerified ? '#047857' : (isDienChan ? '#be185d' : (isSurface ? '#0891b2' : (isUpstream ? '#4338ca' : '#334155'))))));
        let dash = isUncertain ? 'stroke-dasharray="3,3"' : ((isVerified || isSurface || isProtoPt) ? '' : 'stroke-dasharray="2,2"');
        let ptOpacity = item.facing ? '1.0' : '0.35';

        const statusLabel = isUncertain ? '⚠️ UNCERTAIN POSTURE OFFSET' : (isVerified ? 'VERIFIED ANCHOR' : (isSurface ? 'SURFACE REGISTERED (FJ2810)' : (isUpstream ? 'UPSTREAM RAW' : (isLegacy ? 'LEGACY RAYCAST' : (isDienChan ? 'VIETNAMESE DIEN CHAN' : 'UNKNOWN')))));

        let warningRing = '';
        if (isUncertain) {
          warningRing = `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${(vis.rad + 2.5).toFixed(1)}" fill="none" stroke="#f59e0b" stroke-width="1.2" stroke-dasharray="2,2" opacity="${item.facing ? '0.9' : '0.4'}" pointer-events="none" />`;
        } else if (isProtoPt) {
          warningRing = `<circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${(vis.rad + 3.0).toFixed(1)}" fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3,2" opacity="${item.facing ? '0.95' : '0.45'}" pointer-events="none" />`;
        }

        ptsHtml += `
          <g class="acu-marker-group" data-code="${code}" data-side="${inst.side}" style="cursor:pointer;">
            <circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${vis.hitRad}" fill="transparent" stroke="none" class="acu-marker ${isDienChan ? 'dien-chan-marker' : ''}" data-code="${code}" data-side="${inst.side}" pointer-events="all"/>
            <circle cx="${s[0].toFixed(1)}" cy="${s[1].toFixed(1)}" r="${(isProtoPt ? vis.rad + 1.2 : vis.rad).toFixed(1)}" fill="${fill}" stroke="${stroke}" stroke-width="${vis.swidth}" ${dash} opacity="${ptOpacity}" pointer-events="none"/>
            ${warningRing}
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
        if (isProtoPt || (isDienChan && showDienChan)) {
          shouldRenderLabel = true;
        } else if (displaySettings.labelDensity === 'all') {
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
          const lblColor = isProtoPt ? '#fbbf24' : (isDienChan ? '#fbcfe8' : '#f8fafc');
          const cleanCode = isDienChan ? code.replace('DC_', '') : code;
          ptsHtml += `<text x="${lblX}" y="${lblY}" font-size="${fontSize}" font-weight="${isProtoPt ? '700' : '600'}" fill="${lblColor}" font-family="-apple-system, BlinkMacSystemFont, sans-serif" style="text-shadow:0 1px 2px rgba(0,0,0,0.8); pointer-events:none;">${cleanCode}</text>`;
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

  function updatePin() {

    const pin = document.getElementById('pin');

    if (!pin) return;

    const r = getRenderer();

    if (!r) { pin.hidden = true; return; }

    const viewport = r.getViewportDescriptor('overlay');

    const vp = viewport.viewProjectionMatrix;



    let pos = null;

    let label = '';

    const lang = window.__atlas_i18n ? window.__atlas_i18n.getLang() : 'en';



    if (selectedCode && selectedCode.startsWith('DIEN-') && window.__selectedDienChan) {

      pos = window.__selectedDienChan.position;

      const dc = window.__selectedDienChan;

      const dcName = lang === 'vi' ? (dc.name_vi || dc.name) : (lang === 'zh' ? (dc.name_zh || dc.name) : dc.name);

      const tag = lang === 'vi' ? ' [🇻🇳 Phản xạ Diện Chẩn]' : (lang === 'zh' ? ' [🇻🇳 越南面针反射]' : ' [🇻🇳 Dien Chan Reflex]');

      label = `${dcName}${tag}`;

    } else if (selectedCode && window.__selectedAcupoint) {

      pos = window.__selectedAcupoint.resolved_world_position || window.__selectedAcupoint.position;

      const pt = window.__selectedAcupoint;

      let statusTag = ' [Surface Registered]';

      if (pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR') {

        statusTag = lang === 'vi' ? ' [✓ Đã kiểm chứng]' : (lang === 'zh' ? ' [✓ 已验证基准]' : ' [✓ Verified Anchor]');

      } else if (pt.registration_status === 'UNCERTAIN_POSTURE_OFFSET') {

        statusTag = ' [⚠️ Uncertain Posture]';

      } else if (pt.registration_status === 'LEGACY_SURFACE_RAYCAST') {

        statusTag = ' [Legacy Raycast]';

      } else if (pt.registration_status === 'UPSTREAM_TRANSFORMED') {

        statusTag = ' [Upstream Raw]';

      } else {

        statusTag = lang === 'vi' ? ' [Mốc thể biểu]' : (lang === 'zh' ? ' [体表对齐]' : ' [Surface Registered]');

      }

      if (lang === 'zh') {

        label = `${pt.name_zh} (${pt.code} / ${pt.pinyin || pt.name_en})${statusTag}`;

      } else if (lang === 'vi') {

        label = `${pt.name_vi || pt.name_en} (${pt.code} / ${pt.name_zh})${statusTag}`;

      } else {

        label = `${pt.name_en} (${pt.code} / ${pt.name_zh})${statusTag}`;

      }

    }



    if (!pos) {

      pin.hidden = true;

      return;

    }



    const s = projectPoint(pos, vp, viewport);

    if (!s) {

      pin.hidden = true;

    } else {

      pin.hidden = false;

      pin.style.left = s[0] + 'px';

      pin.style.top = s[1] + 'px';

      const span = pin.querySelector('span');

      if (span && label) span.textContent = label;

    }

  }



  let isDraggingPoint = false;



  overlaySvg.addEventListener('pointerdown', (ev) => {

    if (window._msk_picking_mode === 'create') {

      ev.preventDefault();

      ev.stopPropagation();

      const r = getRenderer();

      if (!r || !r.pickSkinSurface) return;

      const hit = r.pickSkinSurface(ev.clientX, ev.clientY);

      if (hit) {

        positionPin(hit.position, '📍 [New Point]');

        const pin = document.getElementById('pin');

        if (pin) pin.hidden = false;

        if (window.parent && window.parent !== window) {

          window.parent.postMessage({

            type: 'msk_surface_picked',

            hit: hit

          }, '*');

        }

      }

    } else if (window._msk_picking_mode === 'move') {

      isDraggingPoint = true;

      ev.preventDefault();

      ev.stopPropagation();

      const r = getRenderer();

      if (r && r.canvas) r.canvas.style.cursor = 'grabbing';

      handleMovePoint(ev);

    }

  });



  overlaySvg.addEventListener('pointermove', (ev) => {

    if (window._msk_picking_mode === 'move' && isDraggingPoint) {

      ev.preventDefault();

      ev.stopPropagation();

      handleMovePoint(ev);

    }

  });



  overlaySvg.addEventListener('pointerup', (ev) => {

    if (window._msk_picking_mode === 'move' && isDraggingPoint) {

      isDraggingPoint = false;

      const r = getRenderer();

      if (r && r.canvas) r.canvas.style.cursor = 'grab';

    }

  });



  function handleMovePoint(ev) {

    const r = getRenderer();

    if (!r || !r.pickSkinSurface) return;

    const hit = r.pickSkinSurface(ev.clientX, ev.clientY);

    if (hit) {

      const code = window._msk_moving_code;

      if (code && acuData && acuData.points[code]) {

        acuData.points[code].position = hit.position;

        acuData.points[code].normal = hit.normal;

        positionPin(hit.position, `${code} (Relocated)`);

        render();

      }

      if (window.parent && window.parent !== window) {

        window.parent.postMessage({

          type: 'msk_point_relocated',

          code: code,

          position: hit.position,

          normal: hit.normal,

          face_index: hit.face_index

        }, '*');

      }

    }

  }



  // Handle marker click (Routes WHO acupoints vs Vietnamese Dien Chan independently)

  overlaySvg.addEventListener('click', (ev) => {
    if (window._msk_picking_mode) {
      ev.stopPropagation();
      return;
    }

    // Handle Cluster Click: Smoothly zoom into cluster centroid and expand into individual markers
    const clusterTarget = ev.target.closest('.acu-cluster-marker');
    if (clusterTarget) {
      const codesStr = clusterTarget.getAttribute('data-cluster-codes');
      const cx = parseFloat(clusterTarget.getAttribute('data-centroid-x'));
      const cy = parseFloat(clusterTarget.getAttribute('data-centroid-y'));
      const cz = parseFloat(clusterTarget.getAttribute('data-centroid-z'));

      const r = getRenderer();
      if (r) {
        r.camera.target = [cx, cy, cz];
        r.camera.dist = Math.max(0.75, r.camera.dist * 0.55);
        if (typeof r._draw === 'function') r._draw();
      }

      if (codesStr) {
        const codes = codesStr.split(',');
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({
            type: 'msk_cluster_selected',
            count: codes.length,
            codes: codes,
            centroid: [cx, cy, cz]
          }, '*');
        }
      }
      render(true);
      return;
    }

    const target = ev.target.closest('.acu-marker');

    if (!target) return;

    const code = target.getAttribute('data-code');

    if (!code) return;

    if (code.startsWith('DIEN-') || code.startsWith('DC_') || code.startsWith('DC-')) {
      selectDienChanPoint(code, true);
    } else {
      selectPoint(code, true);
    }
  });

  // Dedicated Dien Chan selection handler (Requirement C - never route via WHO lookup)
  function selectDienChanPoint(code, notifyParent = true) {
    if (!acuData || !acuData.dien_chan) return;
    const dc = acuData.dien_chan.find(d => d.code === code || d.point_code === code);
    if (!dc) return;

    selectedCode = code;
    window.__selectedDienChan = dc;
    window.__selectedAcupoint = null;

    const r = getRenderer();
    if (r) {
      updatePin();
      // Smooth camera focus to face
      r._animateTo({
        yaw: 0.0,
        pitch: 0.03,
        dist: 0.38,
        target: [0, 1.62, 0.06],
      });
    }

    updateP9QAInspector(dc);
    render(true);



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

  }



  function selectPoint(code, notifyParent = true) {

    if (!acuData || !acuData.points[code]) return;

    selectedCode = code;

    const pt = acuData.points[code];

    window.__selectedAcupoint = pt; // Store globally for Focus Selected

    const r = getRenderer();



    // Position pin

    if (r) {

      updatePin();

      // Dynamic OrbitControls target update to the 3D acupoint!

      // This centers rotation and zooming directly on the acupoint (e.g. C7 / GV14)

      const pActive = pt.resolved_world_position || pt.position;
      const targetPos = pActive.slice();

      const isBackPoint = pActive[2] < -0.035;

      const isFrontPoint = pActive[2] > 0.035;

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



    updateP9QAInspector(pt);
    if (notifyParent) {



      window.parent.postMessage({

        type: 'msk_acupoint_selected',

        point: pt,

      }, '*');

    }

  }



  let refreshPointsList = null;



  // Build sidebar controls inside #panelMeridians

  function updateP9QAInspector(pt) {
    const badge = document.getElementById('p9QAStatusBadge');
    const content = document.getElementById('p9QAInspectorContent');
    if (!badge || !content || !pt) return;

    const isDienChan = Boolean(pt.system === 'lib_dien_chan' || (pt.code && (pt.code.startsWith('DC') || pt.code.startsWith('DIEN-'))));

    if (isDienChan) {
      const isAnchor = pt.review_status === 'VERIFIED_ANATOMICAL_ANCHOR';
      const badgeBg = isAnchor ? '#065f46' : '#831843';
      const badgeColor = isAnchor ? '#a7f3d0' : '#fbcfe8';
      const badgeText = isAnchor ? 'VERIFIED ANCHOR' : (pt.review_status || 'CANDIDATE ANNOTATION');

      badge.style.background = badgeBg;
      badge.style.color = badgeColor;
      badge.textContent = badgeText;

      const gridCoord = pt.grid_coordinate || 'Tuyến O/A/B';
      const curPos = pt.resolved_world_position || pt.position || [0, 0, 0];
      const posStr = `[${curPos[0].toFixed(4)}, ${curPos[1].toFixed(4)}, ${curPos[2].toFixed(4)}] m`;
      const fmaText = pt.fma_anchor || 'Facial Reflex Zone';
      const errorMm = (pt.projection_residual_mm !== undefined && pt.projection_residual_mm !== null)
        ? `${pt.projection_residual_mm.toFixed(2)} mm`
        : 'None / Not Measured';
      const uncertMm = (pt.uncertainty_mm !== undefined && pt.uncertainty_mm !== null)
        ? `±${pt.uncertainty_mm.toFixed(1)} mm`
        : 'Unknown / Unverified';
      const codeClean = pt.point_code || pt.code;

      content.innerHTML = `
        <div style="font-weight:700; color:#f8fafc; font-size:12px; margin-bottom:4px;">
          ${codeClean} — ${pt.name_vi || pt.name || ''}
        </div>
        <div style="font-size:10px; color:#f472b6; margin-bottom:4px; font-family:monospace;">
          Tọa độ đồ hình: <strong>${gridCoord}</strong> • Pos: ${posStr}
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; margin-bottom:6px; background:#1e293b; padding:6px; border-radius:4px; font-size:9.5px;">
          <div><span style="color:#94a3b8;">Vùng giải phẫu:</span> <strong style="color:#38bdf8;">${pt.anatomical_region || 'Khuôn mặt'}</strong></div>
          <div><span style="color:#94a3b8;">Mốc đối chiếu:</span> <strong style="color:#a7f3d0;">${fmaText}</strong></div>
          <div><span style="color:#94a3b8;">Sai số tái chiếu:</span> <strong style="color:#10b981;">${errorMm}</strong></div>
          <div><span style="color:#94a3b8;">Độ bất định:</span> <strong style="color:#f59e0b;">${uncertMm}</strong></div>
          <div style="grid-column:1/3;"><span style="color:#94a3b8;">Vị trí mô tả:</span> <span style="color:#cbd5e1;">${pt.anatomical_location_vi || pt.indication || ''}</span></div>
          <div style="grid-column:1/3;"><span style="color:#94a3b8;">Xuất xứ nguồn:</span> <span style="color:#cbd5e1;">${pt.source_image_id ? 'Đồ hình Diện Chẩn Image B / BQC 1980' : 'Bùi Quốc Châu Facial Reflexology (1980)'}</span></div>
        </div>
        <div style="font-size:9px; color:#f43f5e; background:#881337; padding:4px 6px; border-radius:3px; line-height:1.3;">
          ⚠️ <strong>Lưu ý y tế:</strong> Dữ liệu Diện Chẩn là phương pháp phản xạ học truyền thống/bổ trợ cho mục đích nghiên cứu & học tập, không phải chỉ định y khoa độc lập.
        </div>
      `;
      return;
    }

    const status = pt.registration_status || 'UNKNOWN';
    const isAnchor = status === 'VERIFIED_ANATOMICAL_ANCHOR';
    const isPostUncert = status === 'UNCERTAIN_POSTURE_OFFSET';
    const isApprox = status === 'GEOMETRIC_SURFACE_APPROXIMATION';
    const isLegacy = status === 'LEGACY_SURFACE_RAYCAST';
    const isUpstream = status === 'UPSTREAM_TRANSFORMED';

    let badgeBg = '#475569';
    let badgeColor = '#e2e8f0';
    let badgeText = 'UNKNOWN / UNVERIFIED';

    if (isAnchor) {
      badgeBg = '#065f46';
      badgeColor = '#a7f3d0';
      badgeText = 'VERIFIED ANCHOR';
    } else if (isPostUncert) {
      badgeBg = '#78350f';
      badgeColor = '#fde68a';
      badgeText = '⚠️ UNCERTAIN POSTURE';
    } else if (isApprox) {
      badgeBg = '#0e7490';
      badgeColor = '#cffafe';
      badgeText = 'APPROX SURFACE';
    } else if (isLegacy) {
      badgeBg = '#334155';
      badgeColor = '#cbd5e1';
      badgeText = 'LEGACY RAYCAST';
    } else if (isUpstream) {
      badgeBg = '#3730a3';
      badgeColor = '#c7d2fe';
      badgeText = 'UPSTREAM RAW';
    }

    badge.style.background = badgeBg;
    badge.style.color = badgeColor;
    badge.textContent = badgeText;

    const anchorName = pt.skeletal_anchor || pt.anchor_structure || 'None / Surface only';
    const fmaText = pt.fma_id ? `[${pt.fma_id}]` : 'None / Unmapped';
    const errorMm = (pt.residual_error_mm !== undefined && pt.residual_error_mm !== null)
      ? `${pt.residual_error_mm.toFixed(1)} mm`
      : 'None / Not Measured';
    const uncertMm = (pt.uncertainty_mm !== undefined && pt.uncertainty_mm !== null)
      ? `±${pt.uncertainty_mm.toFixed(1)} mm`
      : 'Unknown / Unverified';
    const bCunRule = pt.applied_cun_rule || 'None / Unspecified';

    const curPos = pt.resolved_world_position || pt.position || [0,0,0];
    const posStr = `[${curPos[0].toFixed(4)}, ${curPos[1].toFixed(4)}, ${curPos[2].toFixed(4)}] m`;

    let deltaText = 'N/A';
    if (pt.legacy_position && pt.resolved_world_position) {
      const dx = (pt.resolved_world_position[0] - pt.legacy_position[0]) * 1000.0;
      const dy = (pt.resolved_world_position[1] - pt.legacy_position[1]) * 1000.0;
      const dz = (pt.resolved_world_position[2] - pt.legacy_position[2]) * 1000.0;
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
      deltaText = `${dist.toFixed(1)} mm (ΔX:${dx >= 0 ? '+' : ''}${dx.toFixed(1)}, ΔY:${dy >= 0 ? '+' : ''}${dy.toFixed(1)}, ΔZ:${dz >= 0 ? '+' : ''}${dz.toFixed(1)})`;
    }

    let postureNote = '✓ Rest calibration posture';
    if (isPostUncert) {
      postureNote = pt.rejection_reason || '⚠️ High joint deviation: static surface coordinates invalidated.';
    } else if (pt.pose_validity && pt.pose_validity.joint && pt.pose_validity.current_angle_deg > 0) {
      postureNote = `✓ Articulated (${pt.pose_validity.current_angle_deg}° on ${pt.pose_validity.joint})`;
    }

    const meshInfo = `${pt.mesh_id || 'FJ2810'} (Hash: ${(pt.mesh_hash || '05b49233').substring(0, 8)}...)`;
    const provenance = pt.source_provenance || 'BodyParts3D FJ2810 Surface Mesh';

    content.innerHTML = `
      <div style="font-weight:700; color:#f8fafc; font-size:12px; margin-bottom:4px;">
        ${pt.code} — ${pt.name_en || ''} <span style="color:#94a3b8; font-weight:400;">(${pt.name_zh || ''} / ${pt.name_vi || ''})</span>
      </div>
      <div style="font-size:10px; color:#38bdf8; margin-bottom:4px; font-family:monospace;">
        Pos: ${posStr} <span style="color:#94a3b8;">(${AtlasSpatialState.layerMode.toUpperCase()})</span>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; margin-bottom:6px; background:#1e293b; padding:6px; border-radius:4px; font-size:9.5px;">
        <div><span style="color:#94a3b8;">Anchor:</span> <strong style="color:#38bdf8;">${fmaText}</strong></div>
        <div><span style="color:#94a3b8;">Residual:</span> <strong style="color:#10b981;">${errorMm}</strong></div>
        <div><span style="color:#94a3b8;">Uncertainty:</span> <strong style="color:#f59e0b;">${uncertMm}</strong></div>
        <div><span style="color:#94a3b8;">Displacement:</span> <span style="color:#cbd5e1;">${deltaText}</span></div>
        <div style="grid-column:1/3;"><span style="color:#94a3b8;">B-Cun Rule:</span> <strong style="color:#fbbf24;">${bCunRule}</strong></div>
        <div style="grid-column:1/3;"><span style="color:#94a3b8;">Skeletal:</span> <span style="color:#cbd5e1;">${anchorName}</span></div>
        <div style="grid-column:1/3;"><span style="color:#94a3b8;">Provenance:</span> <span style="color:#94a3b8;">${provenance}</span></div>
        <div style="grid-column:1/3;"><span style="color:#94a3b8;">Mesh:</span> <span style="color:#64748b;">${meshInfo}</span></div>
      </div>
      <div style="font-size:9.5px; color:#94a3b8; margin-bottom:4px;">
        <strong>Posture State:</strong> <span style="color:${isPostUncert ? '#f59e0b' : '#34d399'};">${postureNote}</span>
      </div>
      <div style="font-size:9px; color:#64748b; font-style:italic; border-top:1px solid #1e293b; padding-top:4px;">
        Ref: WHO 2008 Standard. Non-invasive educational visualization only. Not validated for surgical depth.
      </div>
    `;
  }

  function ensureDienChanModal() {
    let modal = document.getElementById('dienChanRefModal');
    if (modal) return modal;

    modal = document.createElement('div');
    modal.id = 'dienChanRefModal';
    modal.style.cssText = 'position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); width:min(720px, 92vw); max-height:85vh; background:#0f172a; border:1px solid #475569; border-radius:8px; box-shadow:0 20px 25px -5px rgba(0,0,0,0.5), 0 8px 10px -6px rgba(0,0,0,0.5); z-index:9999; display:none; flex-direction:column; overflow:hidden; font-family:inherit;';

    modal.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 14px; background:#1e293b; border-bottom:1px solid #334155;">
        <div style="display:flex; align-items:center; gap:8px;">
          <strong style="color:#f472b6; font-size:12px;">🇻🇳 Đồ Hình Gốc Diện Chẩn (Reference Chart)</strong>
          <span style="font-size:10px; color:#94a3b8; background:#0f172a; padding:2px 6px; border-radius:3px;">Local Source</span>
        </div>
        <button id="btnCloseDienChanModal" style="background:transparent; border:none; color:#cbd5e1; font-size:16px; cursor:pointer; padding:2px 6px;">✕</button>
      </div>
      <div style="padding:8px 14px; background:#1e1b4b; display:flex; gap:8px; align-items:center; border-bottom:1px solid #312e81;">
        <span style="font-size:11px; color:#a5b4fc; font-weight:600;">Chọn đồ hình:</span>
        <button id="btnRefImgHeadache" style="font-size:11px; padding:3px 8px; background:#4338ca; color:#ffffff; border:1px solid #6366f1; border-radius:3px; cursor:pointer;">Image B: Đau Đầu – Viêm Xoang</button>
        <button id="btnRefImgAtlas" style="font-size:11px; padding:3px 8px; background:#1e293b; color:#cbd5e1; border:1px solid #475569; border-radius:3px; cursor:pointer;">Image A: Toàn Diện (Front/Side)</button>
      </div>
      <div style="flex:1; overflow:auto; padding:12px; display:flex; justify-content:center; align-items:center; background:#020617; min-height:300px;">
        <img id="imgDienChanRefChart" src="/api/dien-chan/images/headache-sinus" alt="Dien Chan Reference Chart" style="max-width:100%; max-height:60vh; object-fit:contain; border-radius:4px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.3);" />
      </div>
      <div style="padding:8px 14px; background:#0f172a; border-top:1px solid #1e293b; font-size:10px; color:#94a3b8; display:flex; justify-content:space-between; align-items:center;">
        <span>Tài liệu tham khảo lịch sử (GS.TSKH Bùi Quốc Châu, 1980 / 1984). Dữ liệu phục vụ nghiên cứu & học tập.</span>
        <span style="color:#f43f5e; font-weight:600;">Không thay thế chẩn đoán y khoa</span>
      </div>
    `;

    document.body.appendChild(modal);

    const btnClose = modal.querySelector('#btnCloseDienChanModal');
    if (btnClose) {
      btnClose.addEventListener('click', () => {
        modal.style.display = 'none';
      });
    }

    const btnHeadache = modal.querySelector('#btnRefImgHeadache');
    const btnAtlas = modal.querySelector('#btnRefImgAtlas');
    const imgChart = modal.querySelector('#imgDienChanRefChart');

    if (btnHeadache && btnAtlas && imgChart) {
      btnHeadache.addEventListener('click', () => {
        imgChart.src = '/api/dien-chan/images/headache-sinus';
        btnHeadache.style.background = '#4338ca';
        btnHeadache.style.color = '#ffffff';
        btnAtlas.style.background = '#1e293b';
        btnAtlas.style.color = '#cbd5e1';
      });

      btnAtlas.addEventListener('click', () => {
        imgChart.src = '/api/dien-chan/images/atlas-front-side';
        btnAtlas.style.background = '#4338ca';
        btnAtlas.style.color = '#ffffff';
        btnHeadache.style.background = '#1e293b';
        btnHeadache.style.color = '#cbd5e1';
      });
    }

    return modal;
  }

  function buildSidebarControls() {

    const panel = document.getElementById('panelMeridians');

    if (!panel || !acuData) return;



    function renderPointsList() {

      refreshPointsList = renderPointsList;

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



                <!-- P9: Anatomical Landmark Registration & QA Workbench -->
        <div style="background:var(--panel-2); padding:8px; border-radius:var(--r-s); border:1px solid #0284c7; display:flex; flex-direction:column; gap:6px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#38bdf8; font-size:11px;">📐 P9 Registration Layer:</strong>
            <span id="p9LayerBadge" style="background:#0369a1; color:#e0f2fe; font-size:9px; padding:1px 4px; border-radius:3px; font-weight:600;">CANONICAL</span>
          </div>
          <select id="selP9LayerMode" style="background:#0f172a; color:#f8fafc; border:1px solid #0284c7; padding:3px 6px; border-radius:3px; font-size:10px;">
            <option value="canonical">Canonical (Landmarks & Proportional Cun)</option>
            <option value="legacy_raycast">Legacy Surface Raycast (Pre-baked)</option>
            <option value="upstream_raw">Upstream Raw (WaterCMY / TCMAcupoints)</option>
            <option value="pose_adjusted">Pose Kinematics & Posture Adjusted</option>
          </select>
        </div>

        <!-- P9: QA Anatomical Inspector Panel -->
        <div id="p9QAInspectorPanel" style="background:#0f172a; border:1px solid #334155; border-radius:var(--r-s); padding:8px; display:flex; flex-direction:column; gap:6px; font-size:11px;">
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; padding-bottom:4px;">
            <strong style="color:#10b981; font-size:11px;">🔬 QA Anatomical Inspector</strong>
            <span id="p9QAStatusBadge" style="background:#065f46; color:#a7f3d0; font-size:9px; padding:1px 4px; border-radius:3px;">STANDBY</span>
          </div>
          <div id="p9QAInspectorContent" style="color:#cbd5e1; font-size:10px; line-height:1.4;">
            Select any acupoint to inspect skeletal anchors, WHO B-cun rules, transform matrices, and residual tolerances.
          </div>
        </div>

        <!-- Vietnamese Dien Chan Facial Reflexology Studio Card -->
        <div style="background:var(--panel-2); padding:10px; border-radius:var(--r-s); border:1px solid #ec4899; display:flex; flex-direction:column; gap:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#f472b6; font-size:12px;">🇻🇳 Diện Chẩn Reflexology Studio</strong>
            <span style="background:#831843; color:#fbcfe8; font-size:9px; padding:1px 5px; border-radius:3px; font-weight:600;">3D ATLAS</span>
          </div>
          
          <!-- Camera Presets -->
          <div style="display:flex; flex-direction:column; gap:4px;">
            <span style="font-size:10px; color:var(--muted);">Góc nhìn khuôn mặt (Camera):</span>
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:4px;">
              <button type="button" id="btnDienChanFrontView" style="font-size:10px; padding:4px 2px; background:#1e293b; color:#f8fafc; border:1px solid #475569; border-radius:3px; cursor:pointer;" title="Chính diện">👤 Thẳng</button>
              <button type="button" id="btnDienChanLeftProfile" style="font-size:10px; padding:4px 2px; background:#1e293b; color:#f8fafc; border:1px solid #475569; border-radius:3px; cursor:pointer;" title="Nghiêng trái">👈 Trái</button>
              <button type="button" id="btnDienChanRightProfile" style="font-size:10px; padding:4px 2px; background:#1e293b; color:#f8fafc; border:1px solid #475569; border-radius:3px; cursor:pointer;" title="Nghiêng phải">👉 Phải</button>
            </div>
          </div>

          <!-- Filter & Display Toggles -->
          <div style="display:flex; flex-direction:column; gap:4px; font-size:10.5px;">
            <label style="display:flex; align-items:center; gap:6px; cursor:pointer;">
              <input type="checkbox" id="chkShowDienChanStudio" ${showDienChan ? 'checked' : ''} />
              <span style="color:#f472b6; font-weight:600;">Hiện huyệt Diện Chẩn</span>
            </label>
            <label style="display:flex; align-items:center; gap:6px; cursor:pointer;">
              <input type="checkbox" id="chkDienChanProtocolOnly" ${dienChanProtocolOnly ? 'checked' : ''} />
              <span style="color:#fb7185;">Chỉ hiện huyệt phác đồ đang chọn</span>
            </label>
          </div>

          <!-- Symptom / Condition Search -->
          <div style="display:flex; flex-direction:column; gap:4px;">
            <span style="font-size:10px; color:var(--muted);">Tra cứu bệnh lý / triệu chứng:</span>
            <div style="display:flex; gap:4px;">
              <input type="text" id="txtDienChanSearch" placeholder="Ví dụ: Đau đầu, viêm xoang, mất ngủ..." style="flex:1; background:#0f172a; color:#f8fafc; border:1px solid #475569; padding:4px 6px; border-radius:3px; font-size:11px;" />
              <button type="button" id="btnDienChanSearch" style="background:#db2777; color:#ffffff; border:none; border-radius:3px; padding:4px 8px; font-size:11px; cursor:pointer; font-weight:600;">Tìm</button>
            </div>
          </div>

          <!-- Active Protocol & Search Results Container -->
          <div id="dienChanSearchResults" style="display:flex; flex-direction:column; gap:6px;"></div>

          <!-- Active Protocol Card -->
          <div id="dienChanActiveProtocolCard" style="display:none; flex-direction:column; gap:4px; background:#1e1b4b; border:1px solid #818cf8; padding:6px; border-radius:4px; font-size:10px;"></div>

          <!-- 2D Reference Image Modal Trigger -->
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:2px;">
            <button type="button" id="btnToggleDienChanReferenceImg" style="width:100%; font-size:10px; padding:4px 6px; background:#334155; color:#e2e8f0; border:1px solid #64748b; border-radius:3px; cursor:pointer;">🖼️ Xem đồ hình 2D gốc đối chiếu</button>
          </div>
        </div>

        <!-- M2.6: Adaptive Display Settings -->
        <div style="background:var(--panel-2); padding:8px; border-radius:var(--r-s); border:1px solid var(--line); display:flex; flex-direction:column; gap:6px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:var(--bone); font-size:11px;">⚙ Display Settings</strong>
            <button id="btnResetDisplaySettings" style="background:transparent; border:none; color:#38bdf8; font-size:10px; cursor:pointer;" title="Restore visual defaults">↺ Reset</button>
          </div>
          
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px;">
            <span style="color:var(--muted)">Scaling Mode:</span>
            <select id="selScalingMode" style="background:#0f172a; color:#e2e8f0; border:1px solid var(--line); border-radius:3px; padding:2px 4px; font-size:10px;">
              <option value="auto">Auto (Responsive)</option>
              <option value="manual">Manual</option>
            </select>
          </div>
          
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px;">
            <span style="color:var(--muted)">Smart Density:</span>
            <label style="cursor:pointer; display:flex; align-items:center; gap:4px;">
              <input type="checkbox" id="chkSmartDensity" ${displaySettings.smartDensity ? 'checked' : ''} />
              <span id="lblSmartDensityState" style="color:${displaySettings.smartDensity ? '#10b981' : '#f59e0b'}; font-weight:600; font-size:10px;">${displaySettings.smartDensity ? 'ON (Cluster)' : 'OFF (All)'}</span>
            </label>
          </div>
          
          <div style="display:flex; flex-direction:column; gap:2px;">
            <div style="display:flex; justify-content:space-between; font-size:10px; color:var(--muted);">
              <span>Acupoint Size:</span>
              <span id="lblMarkerSizeVal">${displaySettings.scalingMode === 'manual' ? displaySettings.markerSize.toFixed(1) + ' px' : displaySettings.markerSizeMultiplier.toFixed(1) + 'x'}</span>
            </div>
            <input type="range" id="rngMarkerSize" min="${displaySettings.scalingMode === 'manual' ? '10' : '50'}" max="${displaySettings.scalingMode === 'manual' ? '80' : '250'}" value="${displaySettings.scalingMode === 'manual' ? Math.round(displaySettings.markerSize * 10) : Math.round(displaySettings.markerSizeMultiplier * 100)}" style="cursor:pointer;" />
          </div>
          
          <div style="display:flex; flex-direction:column; gap:2px;">
            <div style="display:flex; justify-content:space-between; font-size:10px; color:var(--muted);">
              <span>Meridian Line:</span>
              <span id="lblStrokeWidthVal">${displaySettings.scalingMode === 'manual' ? displaySettings.meridianThickness.toFixed(1) + ' px' : displaySettings.meridianThicknessMultiplier.toFixed(1) + 'x'}</span>
            </div>
            <input type="range" id="rngMeridianThickness" min="${displaySettings.scalingMode === 'manual' ? '5' : '50'}" max="${displaySettings.scalingMode === 'manual' ? '45' : '250'}" value="${displaySettings.scalingMode === 'manual' ? Math.round(displaySettings.meridianThickness * 10) : Math.round(displaySettings.meridianThicknessMultiplier * 100)}" style="cursor:pointer;" />
          </div>
          
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px;">
            <span style="color:var(--muted)">Labels:</span>
            <select id="selLabelDensity" style="background:#0f172a; color:#e2e8f0; border:1px solid var(--line); border-radius:3px; padding:2px 4px; font-size:10px;">
              <option value="auto" ${displaySettings.labelDensity === 'auto' ? 'selected' : ''}>Auto (Zoom-based)</option>
              <option value="selected" ${displaySettings.labelDensity === 'selected' ? 'selected' : ''}>Selected Only</option>
              <option value="all" ${displaySettings.labelDensity === 'all' ? 'selected' : ''}>All Visible</option>
              <option value="none" ${displaySettings.labelDensity === 'none' ? 'selected' : ''}>None</option>
            </select>
          </div>
        </div>

        <!-- Density Counters Badge -->
        <div id="densityCountersBadge" style="display:flex; justify-content:space-between; font-size:9px; color:#94a3b8; background:rgba(15,23,42,0.6); padding:4px 6px; border-radius:3px; border:1px solid var(--line);">
          <span>Avail: <strong id="cntAvailable" style="color:#38bdf8;">0</strong></span>
          <span>Vis: <strong id="cntVisible" style="color:#10b981;">0</strong></span>
          <span>Clust: <strong id="cntClustered" style="color:#facc15;">0</strong></span>
          <span>Filt: <strong id="cntFiltered" style="color:#94a3b8;">0</strong></span>
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


    // M2.6 Display Settings Listeners
    const selP9LayerMode = document.getElementById('selP9LayerMode');
    if (selP9LayerMode) {
      selP9LayerMode.value = AtlasSpatialState.layerMode;
      selP9LayerMode.addEventListener('change', (e) => {
        currentP9LayerMode = e.target.value;
        AtlasSpatialState.layerMode = e.target.value;
        const b = document.getElementById('p9LayerBadge');
        if (b) b.textContent = currentP9LayerMode.toUpperCase();
        resolveSpatialGeometry(true);
      });
    }

    const selScalingMode = document.getElementById('selScalingMode');
    if (selScalingMode) {
      selScalingMode.addEventListener('change', (e) => {
        displaySettings.scalingMode = e.target.value;
        saveDisplaySettings();
        syncDisplaySettingsUI();
        render(true);
        notifyParentDisplayChanged();
      });
    }

    const chkSmartDensity = document.getElementById('chkSmartDensity');
    if (chkSmartDensity) {
      chkSmartDensity.addEventListener('change', (e) => {
        displaySettings.smartDensity = e.target.checked;
        saveDisplaySettings();
        syncDisplaySettingsUI();
        render(true);
        notifyParentDisplayChanged();
      });
    }

    const rngMarkerSize = document.getElementById('rngMarkerSize');
    if (rngMarkerSize) {
      rngMarkerSize.addEventListener('input', (e) => {
        const val = parseInt(e.target.value, 10);
        if (displaySettings.scalingMode === 'manual') {
          displaySettings.markerSize = val / 10.0;
          const lbl = document.getElementById('lblMarkerSizeVal');
          if (lbl) lbl.textContent = `${displaySettings.markerSize.toFixed(1)} px`;
        } else {
          displaySettings.markerSizeMultiplier = val / 100.0;
          const lbl = document.getElementById('lblMarkerSizeVal');
          if (lbl) lbl.textContent = `${displaySettings.markerSizeMultiplier.toFixed(1)}x`;
        }
        saveDisplaySettings();
        render(true);
        notifyParentDisplayChanged();
      });
    }

    const rngMeridianThickness = document.getElementById('rngMeridianThickness');
    if (rngMeridianThickness) {
      rngMeridianThickness.addEventListener('input', (e) => {
        const val = parseInt(e.target.value, 10);
        if (displaySettings.scalingMode === 'manual') {
          displaySettings.meridianThickness = val / 10.0;
          const lbl = document.getElementById('lblStrokeWidthVal');
          if (lbl) lbl.textContent = `${displaySettings.meridianThickness.toFixed(1)} px`;
        } else {
          displaySettings.meridianThicknessMultiplier = val / 100.0;
          const lbl = document.getElementById('lblStrokeWidthVal');
          if (lbl) lbl.textContent = `${displaySettings.meridianThicknessMultiplier.toFixed(1)}x`;
        }
        saveDisplaySettings();
        render(true);
        notifyParentDisplayChanged();
      });
    }

    const selLabelDensity = document.getElementById('selLabelDensity');
    if (selLabelDensity) {
      selLabelDensity.addEventListener('change', (e) => {
        displaySettings.labelDensity = e.target.value;
        saveDisplaySettings();
        render(true);
        notifyParentDisplayChanged();
      });
    }

    const btnResetDisplaySettings = document.getElementById('btnResetDisplaySettings');
    if (btnResetDisplaySettings) {
      btnResetDisplaySettings.addEventListener('click', () => {
        OverlayStyleController.resetDefaults();
      });
    }

    document.getElementById('chkShowPoints').addEventListener('change', (e) => {

      showPoints = e.target.checked;

      render();

    });

    document.getElementById('chkVerifiedOnly').addEventListener('change', (e) => {

      verifiedOnly = e.target.checked;

      if (refreshPointsList) refreshPointsList();

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

    // Dien Chan Search & Protocol Activation Logic
    async function performDienChanSearch(q) {
      const resultsContainer = document.getElementById('dienChanSearchResults');
      if (!resultsContainer) return;
      if (!q || !q.trim()) {
        resultsContainer.innerHTML = '';
        return;
      }
      resultsContainer.innerHTML = '<div style="font-size:10px; color:#94a3b8; padding:4px;">Đang tìm kiếm...</div>';
      try {
        const res = await fetch(`/api/dien-chan/conditions/search?q=${encodeURIComponent(q.trim())}`);
        if (!res.ok) {
          resultsContainer.innerHTML = '<div style="font-size:10px; color:#f43f5e; padding:4px;">Lỗi kết nối máy chủ.</div>';
          return;
        }
        const data = await res.json();
        const results = data.results || [];
        if (results.length === 0) {
          resultsContainer.innerHTML = `
            <div style="font-size:10px; color:#f59e0b; background:#451a03; padding:5px 8px; border-radius:3px; border:1px solid #78350f;">
              Chưa có dữ liệu đã đối chiếu. Hệ thống không tạo phác đồ giả.
            </div>
          `;
          return;
        }

        let html = '';
        for (const item of results) {
          const cond = item.condition || item;
          const protocols = item.protocols || [];
          const matchLabel = item.match_reason || item.match_type || 'Phù hợp';
          html += `
            <div style="background:#0f172a; border:1px solid #334155; border-radius:4px; padding:6px; display:flex; flex-direction:column; gap:4px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#f472b6; font-size:11px;">${cond.name_vi}</strong>
                <span style="font-size:9px; color:#94a3b8;">${cond.category || ''}</span>
              </div>
              <div style="font-size:9.5px; color:#94a3b8;">
                Khớp: <span style="color:#38bdf8;">${matchLabel}</span>
              </div>
          `;

          if (protocols.length === 0) {
            html += `<div style="font-size:9.5px; color:#94a3b8; font-style:italic;">Chưa có phác đồ đối chiếu</div>`;
          } else {
            for (const proto of protocols) {
              const ptCodes = proto.point_codes || [];
              const protoTitle = proto.title_vi || proto.name_vi || proto.title_en || 'Phác đồ';
              const srcCite = (proto.source && proto.source.title) ? `${proto.source.title} (${proto.source.author})` : (proto.source_citation || 'Đồ hình gốc');
              html += `
                <div style="background:#1e1b4b; border:1px solid #4338ca; border-radius:3px; padding:4px 6px; margin-top:2px;">
                  <div style="font-size:10px; font-weight:600; color:#c7d2fe;">${protoTitle}</div>
                  <div style="font-size:9px; color:#cbd5e1; margin:2px 0;">
                    Huyệt (${ptCodes.length}): <strong style="color:#f43f5e;">${ptCodes.join(', ')}</strong>
                  </div>
                  <div style="font-size:8.5px; color:#818cf8; margin-bottom:4px;">
                    Nguồn: ${srcCite}
                  </div>
                  <button type="button" class="btn-apply-dien-chan-protocol" data-proto-id="${proto.protocol_id}" style="width:100%; font-size:9.5px; padding:3px 6px; background:#db2777; color:#ffffff; border:none; border-radius:2px; cursor:pointer; font-weight:600;">
                    ✓ Áp dụng &amp; Highlight
                  </button>
                </div>
              `;
            }
          }
          html += `</div>`;
        }
        resultsContainer.innerHTML = html;

        resultsContainer.querySelectorAll('.btn-apply-dien-chan-protocol').forEach(btn => {
          btn.addEventListener('click', () => {
            const protoId = btn.getAttribute('data-proto-id');
            const foundProto = results.flatMap(r => r.protocols).find(p => p.protocol_id === protoId);
            if (foundProto) {
              activateDienChanProtocol(foundProto);
            }
          });
        });
      } catch (err) {
        resultsContainer.innerHTML = `<div style="font-size:10px; color:#f43f5e; padding:4px;">Lỗi: ${err.message}</div>`;
      }
    }

    function activateDienChanProtocol(proto) {
      activeDienChanProtocol = proto;
      showDienChan = true;
      const chkMain = document.getElementById('chkShowDienChan');
      const chkStudio = document.getElementById('chkShowDienChanStudio');
      if (chkMain) chkMain.checked = true;
      if (chkStudio) chkStudio.checked = true;

      setDienChanCameraView('front');
      renderActiveProtocolCard();
      render(true);
    }

    function renderActiveProtocolCard() {
      const card = document.getElementById('dienChanActiveProtocolCard');
      if (!card) return;
      if (!activeDienChanProtocol) {
        card.style.display = 'none';
        card.innerHTML = '';
        return;
      }
      const ptCodes = activeDienChanProtocol.point_codes || [];
      card.style.display = 'flex';
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong style="color:#c7d2fe; font-size:10.5px;">Phác đồ: ${activeDienChanProtocol.name_vi}</strong>
          <button type="button" id="btnClearActiveProtocol" style="background:transparent; border:none; color:#f43f5e; cursor:pointer; font-weight:700; font-size:11px;">✕ Bỏ chọn</button>
        </div>
        <div style="color:#94a3b8; font-size:9.5px;">Tình trạng: <span style="color:#38bdf8;">${activeDienChanProtocol.condition_name_vi || activeDienChanProtocol.condition_id || ''}</span></div>
        <div style="color:#fbcfe8; font-size:9.5px;">Huyệt (${ptCodes.length}): <strong style="color:#f43f5e;">${ptCodes.join(', ')}</strong></div>
        <div style="color:#64748b; font-size:8.5px;">Nguồn: ${activeDienChanProtocol.source_citation || 'Đồ hình gốc Image B'}</div>
      `;

      const btnClear = card.querySelector('#btnClearActiveProtocol');
      if (btnClear) {
        btnClear.addEventListener('click', () => {
          activeDienChanProtocol = null;
          renderActiveProtocolCard();
          render(true);
        });
      }
    }

    // Dien Chan Buttons & Listeners
    const btnDcFront = document.getElementById('btnDienChanFrontView');
    if (btnDcFront) btnDcFront.addEventListener('click', () => setDienChanCameraView('front'));

    const btnDcLeft = document.getElementById('btnDienChanLeftProfile');
    if (btnDcLeft) btnDcLeft.addEventListener('click', () => setDienChanCameraView('left_profile'));

    const btnDcRight = document.getElementById('btnDienChanRightProfile');
    if (btnDcRight) btnDcRight.addEventListener('click', () => setDienChanCameraView('right_profile'));

    const chkDcStudio = document.getElementById('chkShowDienChanStudio');
    if (chkDcStudio) {
      chkDcStudio.addEventListener('change', (e) => {
        showDienChan = e.target.checked;
        const chkMain = document.getElementById('chkShowDienChan');
        if (chkMain) chkMain.checked = showDienChan;
        render(true);
      });
    }

    const chkDcProtoOnly = document.getElementById('chkDienChanProtocolOnly');
    if (chkDcProtoOnly) {
      chkDcProtoOnly.addEventListener('change', (e) => {
        dienChanProtocolOnly = e.target.checked;
        render(true);
      });
    }

    const btnDcSearch = document.getElementById('btnDienChanSearch');
    const txtDcSearch = document.getElementById('txtDienChanSearch');
    if (btnDcSearch && txtDcSearch) {
      btnDcSearch.addEventListener('click', () => performDienChanSearch(txtDcSearch.value));
      txtDcSearch.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          performDienChanSearch(txtDcSearch.value);
        }
      });
    }

    const btnToggleRef = document.getElementById('btnToggleDienChanReferenceImg');
    if (btnToggleRef) {
      btnToggleRef.addEventListener('click', () => {
        const m = ensureDienChanModal();
        m.style.display = 'flex';
      });
    }

    renderActiveProtocolCard();

    // Expose search & protocol activation on internal window handlers
    window.__dienChanInternal = {
      performDienChanSearch,
      activateDienChanProtocol,
      clearActiveProtocol: () => {
        activeDienChanProtocol = null;
        renderActiveProtocolCard();
        render(true);
      }
    };

    document.getElementById('chkShowDienChan').addEventListener('change', (e) => {
      showDienChan = e.target.checked;
      const chkStudio = document.getElementById('chkShowDienChanStudio');
      if (chkStudio) chkStudio.checked = showDienChan;
      render(true);
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

    } else if (ev.data.action === 'set_p9_layer_mode') {

      const mode = ev.data.mode || 'canonical';
      currentP9LayerMode = mode;
      AtlasSpatialState.layerMode = mode;
      const sel = document.getElementById('selP9LayerMode');
      if (sel) sel.value = mode;
      const b = document.getElementById('p9LayerBadge');
      if (b) b.textContent = mode.toUpperCase();
      resolveSpatialGeometry(true);

    } else if (ev.data.action === 'set_pose') {

      if (ev.data.pose) {
        if (ev.data.pose.joint_angles) {
          Object.assign(AtlasSpatialState.pose.joint_angles, ev.data.pose.joint_angles);
        } else {
          Object.assign(AtlasSpatialState.pose.joint_angles, ev.data.pose);
        }
        resolveSpatialGeometry(true);
      }

    } else if (ev.data.action === 'set_morphology') {

      if (ev.data.morphology) {
        Object.assign(AtlasSpatialState.morphology, ev.data.morphology);
        resolveSpatialGeometry(true);
      }

    } else if (ev.data.action === 'resolve_geometry') {

      resolveSpatialGeometry(true);

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

      if (filterMeridian !== 'all') {

        showMeridians = true;

        showPoints = true;

        const cMer = document.getElementById('chkShowMeridians');

        if (cMer) cMer.checked = true;

        const cPts = document.getElementById('chkShowPoints');

        if (cPts) cPts.checked = true;



        const r = getRenderer();

        if (r) {

          r.camera.target = [0, 1.22, 0];

          r.camera.dist = Math.max(r.camera.dist, 1.35);

          if (filterMeridian === 'CV') {

            r.camera.yaw = 0.0;

            r.camera.pitch = 0.02;

            if (typeof r._draw === 'function') r._draw();

          } else if (filterMeridian === 'GV' || filterMeridian === 'BL') {

            r.camera.yaw = Math.PI;

            r.camera.pitch = 0.02;

            if (typeof r._draw === 'function') r._draw();

          } else {

            if (typeof r._draw === 'function') r._draw();

          }

        }

      }

      if (refreshPointsList) refreshPointsList();

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

      }

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

    } else if (ev.data.action === 'start_pick_surface') {

      window._msk_picking_mode = 'create';

      overlaySvg.style.pointerEvents = 'all';

      const r = getRenderer();

      if (r && r.canvas) r.canvas.style.cursor = 'crosshair';

    } else if (ev.data.action === 'start_move_point') {

      window._msk_picking_mode = 'move';

      window._msk_moving_code = ev.data.code;

      overlaySvg.style.pointerEvents = 'all';

      const r = getRenderer();

      if (r && r.canvas) r.canvas.style.cursor = 'grab';

    } else if (ev.data.action === 'stop_pick_surface') {

      window._msk_picking_mode = null;

      window._msk_moving_code = null;

      isDraggingPoint = false;

      overlaySvg.style.pointerEvents = 'none';

      const r = getRenderer();

      if (r && r.canvas) r.canvas.style.cursor = '';

    } else if (ev.data.action === 'snap_point_to_surface') {

      const r = getRenderer();

      if (r && r.snapToSkinSurface && ev.data.position) {

        const snap = r.snapToSkinSurface(ev.data.position, ev.data.maxDistance || 0.08);

        if (window.parent && window.parent !== window) {

          window.parent.postMessage({

            type: 'msk_snap_result',

            code: ev.data.code,

            snap: snap

          }, '*');

        }

      }

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
    get activeDienChanProtocol() { return activeDienChanProtocol; },
    searchDienChan: (q) => window.__dienChanInternal ? window.__dienChanInternal.performDienChanSearch(q) : null,
    selectProtocol: (proto) => window.__dienChanInternal ? window.__dienChanInternal.activateDienChanProtocol(proto) : null,
    clearActiveProtocol: () => window.__dienChanInternal ? window.__dienChanInternal.clearActiveProtocol() : null,
    getActiveProtocol: () => activeDienChanProtocol,
    setDienChanCameraView,
    getDienChanPoints: () => (acuData && acuData.dien_chan ? acuData.dien_chan : []),

    get displaySettings() { return displaySettings; },
    get currentCounters() { return currentDensityCounters; },
    AtlasSpatialState,
    resolveSpatialGeometry,
    VisualScaleEngine,
    MarkerDensityManager,
    OverlayStyleController,
    updateDisplaySettings: (s) => OverlayStyleController.updateSettings(s),
    resetDisplaySettings: () => OverlayStyleController.resetDefaults(),
    selectPoint,

    selectDienChanPoint,

    render,

    setLayerMode: async (mode) => {
      currentP9LayerMode = mode;
      AtlasSpatialState.layerMode = mode;
      const sel = document.getElementById('selP9LayerMode');
      if (sel) sel.value = mode;
      const b = document.getElementById('p9LayerBadge');
      if (b) b.textContent = mode.toUpperCase();
      return await resolveSpatialGeometry(true);
    },

    setPose: async (jointAngles) => {
      if (jointAngles) {
        Object.assign(AtlasSpatialState.pose.joint_angles, jointAngles);
        return await resolveSpatialGeometry(true);
      }
    },

    setMorphology: async (params) => {
      if (params) {
        Object.assign(AtlasSpatialState.morphology, params);
        return await resolveSpatialGeometry(true);
      }
    },

    getPointData: (code) => {
      return acuData && acuData.points ? acuData.points[code] : null;
    },

    getResolvedData: () => AtlasSpatialState.resolvedData,

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

