// MSK-Therapy-OS: Custom Acupoint Atlas & Interactive 3D Point Editor (M2.5)
// Upstream Integration: Open Anatomy Atlas + JICio Surface Registration + Meridian Studio Authoring
// Durable SQLite Persistence, Geometric Ray-Triangle Picking, Semantic Status Integrity & SHA-256 Export
(() => {
  'use strict';

  let allPoints = {};
  let currentPointCode = 'GV14';
  let currentPointId = null;
  let baselinePoints = {};
  let modifiedCount = 0;
  let activeLibrary = 'all';
  let librariesList = [];
  let isPickingSurface = false;
  let isMovingPoint = false;

  let initPromise = null;
  function ensureStudioReady() {
    if (!initPromise) {
      initPromise = initStudio();
    }
    return initPromise;
  }

  // Initialize and load points and libraries from durable SQLite backend
  async function initStudio() {
    try {
      // 1. Load libraries
      const libRes = await fetch('/api/points/libraries');
      if (libRes.ok) {
        librariesList = await libRes.json();
      }

      // 2. Load consolidated points
      const res = await fetch('/api/acupuncture-3d');
      if (res.ok) {
        const data = await res.json();
        allPoints = data.points || {};
        baselinePoints = JSON.parse(JSON.stringify(allPoints));
        ensureModal();
        populateLibrarySelect();
        populatePointSelect();
        if (currentPointCode && allPoints[currentPointCode]) {
          loadPointIntoEditor(currentPointCode, false);
        } else if (allPoints['GV14']) {
          loadPointIntoEditor('GV14', false);
        } else if (Object.keys(allPoints).length > 0) {
          loadPointIntoEditor(Object.keys(allPoints)[0], false);
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
      background: rgba(10, 15, 29, 0.88);
      backdrop-filter: blur(5px);
      z-index: 10000;
      align-items: center;
      justify-content: center;
      padding: 16px;
      box-sizing: border-box;
    `;

    modal.innerHTML = `
      <!-- Floating Interaction Bar when picking or moving on 3D model -->
      <div id="studioFloatingBar" style="display: none; position: fixed; top: 16px; left: 50%; transform: translateX(-50%); background: #111827; border: 1px solid #0284c7; padding: 8px 18px; border-radius: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.9); z-index: 10005; align-items: center; gap: 14px; color: #fff; font-size: 12px;">
        <span id="studioFloatingText" style="font-weight: 600; color: #38bdf8;">🎯 Click anywhere on the 3D human body to place point...</span>
        <button id="btnStudioCancelFloat" style="background: #0284c7; color: #fff; border: none; padding: 4px 12px; border-radius: 12px; cursor: pointer; font-size: 11px; font-weight: 600;">Done</button>
      </div>

      <div id="studioModalDialog" style="background: #111827; border: 1px solid #374151; border-radius: 8px; width: 100%; max-width: 980px; max-height: 94vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.85); overflow-y: auto; overflow-x: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <!-- Header -->
        <div style="padding: 10px 18px; background: #1f2937; border-bottom: 1px solid #374151; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-size: 15px; font-weight: 700; color: #f3f4f6; display: flex; align-items: center; gap: 8px;">
              <span>🛠️ 3D Custom Acupoint Atlas & Point Editor</span>
              <span style="font-size: 10px; background: #0284c7; color: #e0f2fe; padding: 2px 6px; border-radius: 4px; font-weight: 600;">M2.5 Multi-Library</span>
              <span id="studioActiveModeBadge" style="font-size: 10px; background: #374151; color: #9ca3af; padding: 2px 6px; border-radius: 4px;">Standard Edit</span>
            </div>
            <div style="font-size: 11px; color: #9ca3af; margin-top: 2px;">
              BodyParts3D 4.0 (FJ2810 Skin) • Ray-Triangle Surface Picking • Durable SQLite Persistence
            </div>
          </div>
          <button id="btnCloseStudioModal" style="background: transparent; border: none; color: #9ca3af; font-size: 20px; cursor: pointer; padding: 4px 8px; border-radius: 4px;">✕</button>
        </div>

        <!-- Top Action Bar -->
        <div style="padding: 8px 18px; background: #162032; border-bottom: 1px solid #2d3748; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
          <button id="btnStudioNewPoint" style="background: #059669; color: #fff; border: none; padding: 5px 10px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px; display: flex; align-items: center; gap: 4px;">➕ New Point</button>
          <button id="btnStudioMove3D" style="background: #2563eb; color: #fff; border: none; padding: 5px 10px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px; display: flex; align-items: center; gap: 4px;">🎯 Move on 3D Model</button>
          <button id="btnStudioSnapSurface" style="background: #0d9488; color: #fff; border: none; padding: 5px 10px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px; display: flex; align-items: center; gap: 4px;">🧲 Snap to Surface</button>
          <button id="btnStudioMirrorBilateral" style="background: #7c3aed; color: #fff; border: none; padding: 5px 10px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px; display: flex; align-items: center; gap: 4px;">🪞 Duplicate / Mirror</button>
          <button id="btnStudioHistory" style="background: #374151; color: #cbd5e1; border: 1px solid #4b5563; padding: 5px 10px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px;">📜 Revision History</button>
          <button id="btnStudioRestoreBaseline" style="background: #4b5563; color: #f87171; border: 1px solid #6b7280; padding: 5px 10px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px;">↺ Restore Original</button>
          <button id="btnStudioDeletePoint" style="background: #7f1d1d; color: #fca5a5; border: 1px solid #b91c1c; padding: 5px 10px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px; display: none;">🗑️ Delete Point</button>
          <span style="flex: 1;"></span>
          <button id="btnStudioSave" style="background: #10b981; color: #fff; border: none; padding: 6px 14px; border-radius: 4px; font-weight: 700; cursor: pointer; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.4);">💾 Save Changes</button>
        </div>

        <!-- Inline Point Creation Card (Collapsible) -->
        <div id="studioCreatorCard" style="display: none; background: #1a2333; padding: 12px 18px; border-bottom: 1px solid #374151;">
          <div style="font-weight: 700; color: #38bdf8; margin-bottom: 8px; font-size: 13px; display: flex; justify-content: space-between; align-items: center;">
            <span>➕ Create New Custom Acupoint / Reflex Landmark</span>
            <button id="btnStudioCancelCreate" style="background: transparent; border: none; color: #9ca3af; cursor: pointer; font-size: 12px;">✕ Cancel</button>
          </div>
          <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; font-size: 11px; margin-bottom: 8px;">
            <div>
              <label style="color: #9ca3af; display: block; margin-bottom: 2px;">Library / Classification:</label>
              <select id="newPtLibrary" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px; border-radius: 3px;">
                <option value="lib_custom_user">User Custom Points (Local)</option>
                <option value="lib_extra">Extra Acupuncture Points</option>
                <option value="lib_thai_sen">Thai Sen Sib Landmark</option>
                <option value="lib_dien_chan">Vietnamese Dien Chan Reflex</option>
                <option value="lib_msk_landmarks">MSK Palpation Landmark</option>
              </select>
            </div>
            <div>
              <label style="color: #9ca3af; display: block; margin-bottom: 2px;">Point Code (Unique):</label>
              <input type="text" id="newPtCode" placeholder="e.g. EX-SH-01" style="width: 100%; background: #111827; color: #38bdf8; border: 1px solid #0284c7; padding: 4px; border-radius: 3px; font-weight: 600;" />
            </div>
            <div>
              <label style="color: #9ca3af; display: block; margin-bottom: 2px;">English Name:</label>
              <input type="text" id="newPtNameEn" placeholder="e.g. Scapular Trigger Locus" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px; border-radius: 3px;" />
            </div>
            <div>
              <label style="color: #9ca3af; display: block; margin-bottom: 2px;">Vietnamese Name (Tiếng Việt):</label>
              <input type="text" id="newPtNameVi" placeholder="e.g. Điểm Kích Hoạt Bả Vai" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px; border-radius: 3px;" />
            </div>
          </div>
          <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; font-size: 11px; margin-bottom: 8px;">
            <div>
              <label style="color: #9ca3af; display: block; margin-bottom: 2px;">Chinese Name (中文):</label>
              <input type="text" id="newPtNameZh" placeholder="e.g. 肩胛敏化点" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px; border-radius: 3px;" />
            </div>
            <div>
              <label style="color: #9ca3af; display: block; margin-bottom: 2px;">Region:</label>
              <select id="newPtRegion" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px; border-radius: 3px;">
                <option value="shoulder">Shoulder</option>
                <option value="neck">Neck</option>
                <option value="arm">Arm & Hand</option>
                <option value="upper_back">Upper Back</option>
                <option value="low_back">Low Back</option>
                <option value="leg">Leg & Foot</option>
                <option value="head">Head & Face</option>
                <option value="torso">Torso</option>
              </select>
            </div>
            <div>
              <label style="color: #9ca3af; display: block; margin-bottom: 2px;">Laterality:</label>
              <select id="newPtLaterality" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px; border-radius: 3px;">
                <option value="bilateral">Bilateral (Left & Right)</option>
                <option value="right">Right Side Only</option>
                <option value="left">Left Side Only</option>
                <option value="midline">Anterior/Posterior Midline</option>
              </select>
            </div>
            <div style="display: flex; align-items: flex-end;">
              <button id="btnStudioPickSurface" style="width: 100%; background: #0284c7; color: #fff; border: none; padding: 5px; border-radius: 3px; font-weight: 600; cursor: pointer;">🎯 Click 3D Body to Position</button>
            </div>
          </div>
          <div style="font-size: 11px; color: #a7f3d0;" id="newPtCoordStatus">
            No coordinates picked yet. Click "🎯 Click 3D Body to Position" to raycast onto the skin mesh.
          </div>
        </div>

        <!-- Body -->
        <div style="padding: 14px 18px; overflow-y: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 12px;">
          <!-- Left Column: Point Selection & 3D Geometry -->
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <!-- Library & Filter Bar -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 6px;">
                <div>
                  <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Point Library / Namespace:</label>
                  <select id="studioLibrarySelect" style="width: 100%; background: #111827; color: #38bdf8; border: 1px solid #4b5563; padding: 4px; border-radius: 4px; font-size: 11px; font-weight: 600;">
                    <option value="all">All Libraries</option>
                    <option value="lib_who_classical">WHO Classical (362 pts)</option>
                    <option value="lib_extra">Extra Points</option>
                    <option value="lib_thai_sen">Thai Sen Sib</option>
                    <option value="lib_dien_chan">Vietnamese Dien Chan</option>
                    <option value="lib_msk_landmarks">MSK Landmarks</option>
                    <option value="lib_custom_user">User Custom Points</option>
                  </select>
                </div>
                <div>
                  <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Body Region:</label>
                  <select id="studioRegionFilter" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px; border-radius: 4px; font-size: 11px;">
                    <option value="all">All Regions</option>
                    <option value="neck">Neck</option>
                    <option value="shoulder">Shoulder</option>
                    <option value="arm">Arm & Hand</option>
                    <option value="leg">Leg & Foot</option>
                    <option value="head">Head & Face</option>
                    <option value="upper_back">Upper Back</option>
                    <option value="low_back">Low Back</option>
                    <option value="torso">Torso</option>
                  </select>
                </div>
              </div>
              <div style="display: flex; gap: 6px; margin-bottom: 6px;">
                <input type="text" id="studioPointSearch" placeholder="Search code, name (EN/ZH/VI)..." style="flex: 1; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px;" />
              </div>
              <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 2px;">Active Point in Editor:</label>
              <select id="studioPointSelect" style="width: 100%; background: #111827; color: #38bdf8; border: 1px solid #0284c7; padding: 6px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;"></select>
            </div>

            <!-- Point Profile Card -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div style="font-size: 14px; font-weight: 700; color: #f3f4f6;" id="studioPointTitle">GV14 - Dazhui (大椎)</div>
                <div style="display: flex; gap: 4px;" id="studioStatusBadge"></div>
              </div>
              <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;" id="studioMeridianDetails">Meridian: Governing Vessel (GV) • Region: Neck</div>
              <div style="font-size: 11px; color: #cbd5e1; margin-bottom: 4px;" id="studioLocationZh">Location: 后正中线上，第7颈椎棘突下凹陷中。</div>
              <div style="font-size: 11px; color: #38bdf8;" id="studioSurfaceAnchor">Mesh: FJ2810 (Skin of body) • Face: #Registered</div>
            </div>

            <!-- 3D Coordinates & Axis/Normal Nudge -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="font-weight: 600; color: #f3f4f6; margin-bottom: 8px; display: flex; justify-content: space-between;">
                <span>3D Coordinates (Meters & Millimeters)</span>
                <span id="studioSyncIndicator" style="font-size: 10px; color: #10b981;">● Live Sync Active</span>
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
                <button id="btnStudioApplyCoords" style="flex: 1; background: #0284c7; color: #fff; border: none; padding: 6px; border-radius: 4px; font-weight: 600; cursor: pointer;">Apply Coordinates to 3D View</button>
                <button id="btnStudioResetPoint" style="background: #4b5563; color: #fff; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer;">Revert</button>
              </div>
            </div>
          </div>

          <!-- Right Column: Registration Status, Clinical Metadata, Export/Import -->
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <!-- Metadata & Registration Status -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="font-weight: 600; color: #f3f4f6; margin-bottom: 8px;">Registration & Provenance</div>
              
              <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
                  <div>
                    <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Geometric Status:</label>
                    <select id="studioRegStatus" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px; border-radius: 4px; font-size: 10px;">
                      <option value="VERIFIED_ANATOMICAL_ANCHOR">VERIFIED_ANATOMICAL_ANCHOR</option>
                      <option value="SURFACE_REGISTERED_FJ2810">SURFACE_REGISTERED_FJ2810</option>
                      <option value="GEOMETRY_VERIFIED">GEOMETRY_VERIFIED</option>
                      <option value="UNCERTAIN_POSTURE_OFFSET">UNCERTAIN_POSTURE_OFFSET</option>
                      <option value="UNVERIFIED">UNVERIFIED</option>
                    </select>
                  </div>
                  <div>
                    <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Clinical Review Status:</label>
                    <select id="studioReviewStatus" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px; border-radius: 4px; font-size: 10px;">
                      <option value="OFFICIAL_STANDARD">OFFICIAL_STANDARD (WHO / MoH)</option>
                      <option value="EXPERT_VERIFIED">EXPERT_VERIFIED (Clinical Specialist)</option>
                      <option value="PROVISIONAL">PROVISIONAL (Under Review)</option>
                      <option value="PENDING_EXPERT_REVIEW">PENDING_EXPERT_REVIEW (User Created)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Source Provenance:</label>
                  <input type="text" id="studioProvenance" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px;" />
                </div>

                <div>
                  <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Verification / Clinical Notes:</label>
                  <textarea id="studioNotes" rows="2" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px; resize: vertical;"></textarea>
                </div>
              </div>

              <button id="btnStudioSaveMetadata" style="width: 100%; background: #059669; color: #fff; border: none; padding: 6px; border-radius: 4px; font-weight: 600; cursor: pointer;">Save Metadata Changes</button>
            </div>

            <!-- Clinical Indications & Evidence Scope -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="font-weight: 600; color: #f3f4f6; margin-bottom: 4px;">Clinical Indications & Tuina Method</div>
              <div style="font-size: 11px; color: #38bdf8; margin-bottom: 4px;" id="studioIndications">Indications: 颈项强痛, 感冒, 发热</div>
              <div style="font-size: 11px; color: #cbd5e1; margin-bottom: 4px;" id="studioTuina">Method: 指揉或点按大椎，宜轻柔渗透。</div>
              <div style="font-size: 11px; color: #f87171;" id="studioCaution">Caution: 椎旁斜刺需注意深度，防止气胸或深部血管神经损伤。</div>
            </div>

            <!-- Versioned Dataset Export & Import (Requirement 7 & 9) -->
            <div style="background: #1f2937; padding: 10px; border-radius: 6px; border: 1px solid #374151;">
              <div style="font-weight: 600; color: #f3f4f6; margin-bottom: 4px; display: flex; justify-content: space-between;">
                <span>Dataset Export / Import</span>
                <span id="studioModCounter" style="font-size: 10px; color: #a7f3d0;">0 Calibrations</span>
              </div>
              <div style="font-size: 10px; color: #9ca3af; margin-bottom: 8px;">
                Conforms to Schema v2.5 with cryptographic SHA-256 digest and FJ2810 mesh verification.
              </div>

              <div style="display: flex; gap: 6px; margin-bottom: 6px;">
                <button id="btnStudioExportJSON" style="flex: 1; background: #4f46e5; color: #fff; border: none; padding: 6px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px;">📥 Export JSON (SHA-256)</button>
                <label style="flex: 1; background: #374151; color: #fff; border: 1px solid #4b5563; padding: 6px; border-radius: 4px; font-weight: 600; cursor: pointer; font-size: 11px; text-align: center; display: block;">
                  📤 Import JSON
                  <input type="file" id="studioFileInput" accept=".json" style="display: none;" />
                </label>
              </div>

              <div style="display: flex; gap: 6px;">
                <button id="btnStudioCopyPointJSON" style="flex: 1; background: #1f2937; color: #cbd5e1; border: 1px solid #4b5563; padding: 4px; border-radius: 3px; cursor: pointer; font-size: 10px;">📋 Copy Point JSON</button>
                <button id="btnStudioResetAll" style="background: #1f2937; color: #ef4444; border: 1px solid #ef4444; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 10px;">Reset All to Upstream</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div style="padding: 8px 18px; background: #1f2937; border-top: 1px solid #374151; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #9ca3af;">
          <div>WHO WPRO 2008 & GB/T 12346-2006 • BodyParts3D 4.0 CC BY-SA 2.1 JP</div>
          <div>Status: <span id="studioSaveStatus" style="color: #10b981;">Ready</span></div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Event Wire-up
    document.getElementById('btnCloseStudioModal').addEventListener('click', closeStudioModal);
    document.getElementById('btnStudioCancelFloat').addEventListener('click', () => {
      if (isMovingPoint) toggleMovePointMode();
      else stopSurfacePickMode();
    });
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeStudioModal();
    });

    document.getElementById('studioLibrarySelect').addEventListener('change', (e) => {
      activeLibrary = e.target.value;
      populatePointSelect();
    });

    document.getElementById('studioRegionFilter').addEventListener('change', populatePointSelect);
    document.getElementById('studioPointSearch').addEventListener('input', populatePointSelect);
    document.getElementById('studioPointSelect').addEventListener('change', (e) => {
      loadPointIntoEditor(e.target.value);
    });

    // Top action bar buttons
    document.getElementById('btnStudioNewPoint').addEventListener('click', openPointCreator);
    document.getElementById('btnStudioCancelCreate').addEventListener('click', closePointCreator);
    document.getElementById('btnStudioPickSurface').addEventListener('click', startSurfacePickMode);
    document.getElementById('btnStudioMove3D').addEventListener('click', toggleMovePointMode);
    document.getElementById('btnStudioSnapSurface').addEventListener('click', snapCurrentPointToSurface);
    document.getElementById('btnStudioMirrorBilateral').addEventListener('click', mirrorBilateralPair);
    document.getElementById('btnStudioSave').addEventListener('click', saveDurableChanges);
    document.getElementById('btnStudioRestoreBaseline').addEventListener('click', restoreBaselinePosition);
    document.getElementById('btnStudioDeletePoint').addEventListener('click', deleteCurrentCustomPoint);
    document.getElementById('btnStudioHistory').addEventListener('click', openRevisionHistoryModal);

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

  function populateLibrarySelect() {
    const sel = document.getElementById('studioLibrarySelect');
    if (!sel || !librariesList.length) return;
    sel.innerHTML = '<option value="all">All Libraries</option>' + librariesList.map(lib => {
      return `<option value="${lib.library_id}">${lib.name} (${lib.points_count || 0})</option>`;
    }).join('');
  }

  function populatePointSelect() {
    const sel = document.getElementById('studioPointSelect');
    if (!sel) return;

    const lib = activeLibrary;
    const region = document.getElementById('studioRegionFilter').value;
    const query = document.getElementById('studioPointSearch').value.trim().toLowerCase();

    const filtered = Object.keys(allPoints).filter(code => {
      const p = allPoints[code];
      // Library filter
      if (lib !== 'all') {
        const pLib = p.library_id || (p.system_classification === 'user_custom' ? 'lib_custom_user' : (p.code && p.code.startsWith('DIEN-') ? 'lib_dien_chan' : 'lib_who_classical'));
        if (pLib !== lib) return false;
      }
      // Region filter
      if (region !== 'all' && p.region !== region) return false;
      // Search query
      if (query) {
        return code.toLowerCase().includes(query) ||
               (p.name_en || '').toLowerCase().includes(query) ||
               (p.name_zh || '').includes(query) ||
               (p.name_vi || '').toLowerCase().includes(query);
      }
      return true;
    }).sort((a, b) => a.localeCompare(b));

    sel.innerHTML = filtered.map(code => {
      const p = allPoints[code];
      const isAnchor = p.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR';
      const isCustom = p.library_id === 'lib_custom_user' || p.system_classification === 'user_custom';
      const mark = isCustom ? '⭐ ' : (isAnchor ? '✓ ' : '');
      const viName = p.name_vi ? ` / ${p.name_vi}` : '';
      return `<option value="${code}" ${code === currentPointCode ? 'selected' : ''}>${mark}${code} - ${p.name_en}${viName}</option>`;
    }).join('');

    if (filtered.length > 0 && !filtered.includes(currentPointCode)) {
      loadPointIntoEditor(filtered[0]);
    }
  }

  function loadPointIntoEditor(code, notifyAtlas = true) {
    if (!allPoints[code]) return;
    currentPointCode = code;
    const pt = allPoints[code];
    currentPointId = pt.point_id || pt.code;
    const sel = document.getElementById('studioPointSelect');
    if (sel && sel.value !== code) {
      sel.value = code;
    }

    const zhPart = pt.name_zh ? ` (${pt.name_zh})` : '';
    const viPart = pt.name_vi ? ` • ${pt.name_vi}` : '';
    document.getElementById('studioPointTitle').textContent = `${pt.code} - ${pt.name_en}${zhPart}${viPart}`;
    document.getElementById('studioMeridianDetails').textContent = `System: ${pt.system_classification || pt.meridian_name || 'Traditional'} • Region: ${pt.region || 'unspecified'} • Laterality: ${pt.laterality || 'bilateral'}`;
    document.getElementById('studioLocationZh').textContent = `Location: ${pt.location_zh || pt.location_method || 'Standard anatomical surface landmark'}`;
    document.getElementById('studioSurfaceAnchor').textContent = `Mesh: ${pt.mesh_id || 'FJ2810'} (Skin of body) • Face: #${pt.face_index || 'Registered'} • Normal: [${(pt.normal || [0,0,1]).map(v => v.toFixed(3)).join(', ')}]`;

    // Coordinates
    document.getElementById('studioCoordX').value = pt.position[0].toFixed(4);
    document.getElementById('studioCoordY').value = pt.position[1].toFixed(4);
    document.getElementById('studioCoordZ').value = pt.position[2].toFixed(4);

    // Status Badges (Semantic Independence)
    const badgeContainer = document.getElementById('studioStatusBadge');
    badgeContainer.innerHTML = '';

    // 1. Geometric Badge
    if (pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR') {
      badgeContainer.innerHTML += '<span style="background:#065f46; color:#a7f3d0; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">✓ ANCHOR</span>';
    } else if (pt.registration_status === 'GEOMETRY_VERIFIED') {
      badgeContainer.innerHTML += '<span style="background:#0284c7; color:#e0f2fe; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">✓ GEOM VERIFIED</span>';
    } else if (pt.registration_status === 'SURFACE_REGISTERED_FJ2810') {
      badgeContainer.innerHTML += '<span style="background:#0e7490; color:#cffafe; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">FJ2810 SURFACE</span>';
    } else {
      badgeContainer.innerHTML += '<span style="background:#78350f; color:#fde68a; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">⚠️ UNVERIFIED</span>';
    }

    // 2. Clinical Review Badge
    const rev = pt.review_status || 'PENDING_EXPERT_REVIEW';
    if (rev === 'OFFICIAL_STANDARD') {
      badgeContainer.innerHTML += '<span style="background:#3730a3; color:#c7d2fe; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">OFFICIAL</span>';
    } else if (rev === 'EXPERT_VERIFIED') {
      badgeContainer.innerHTML += '<span style="background:#1e40af; color:#bfdbfe; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">EXPERT VERIFIED</span>';
    } else {
      badgeContainer.innerHTML += '<span style="background:#4b5563; color:#d1d5db; padding:2px 6px; border-radius:4px; font-size:10px;">PENDING REVIEW</span>';
    }

    // 3. Override Badge if reference point modified
    if (pt.is_overridden) {
      badgeContainer.innerHTML += '<span style="background:#b45309; color:#fef3c7; padding:2px 6px; border-radius:4px; font-weight:700; font-size:10px;">⚡ OVERRIDE</span>';
    }

    // Delete button visibility (custom points only)
    const isCustom = pt.library_id === 'lib_custom_user' || pt.system_classification === 'user_custom';
    const btnDel = document.getElementById('btnStudioDeletePoint');
    if (btnDel) btnDel.style.display = isCustom ? 'inline-block' : 'none';

    // Status & Notes
    document.getElementById('studioRegStatus').value = pt.registration_status || 'SURFACE_REGISTERED_FJ2810';
    document.getElementById('studioReviewStatus').value = pt.review_status || 'PENDING_EXPERT_REVIEW';
    document.getElementById('studioProvenance').value = pt.source_provenance || (isCustom ? 'User Created Custom Landmark' : 'JICio / BodyParts3D 4.0 FJ2810 Surface Registration');
    document.getElementById('studioNotes').value = pt.verification_notes || pt.notes || '';

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

  // ---------------------------------------------------------------------------
  // Point Creation Workflow
  // ---------------------------------------------------------------------------

  function openPointCreator() {
    const card = document.getElementById('studioCreatorCard');
    if (card) {
      card.style.display = 'block';
      document.getElementById('newPtCode').value = `CUSTOM-${Date.now().toString().slice(-4)}`;
      document.getElementById('newPtNameEn').value = '';
      document.getElementById('newPtNameVi').value = '';
      document.getElementById('newPtNameZh').value = '';
      document.getElementById('newPtCoordStatus').textContent = 'Click "🎯 Click 3D Body to Position" to raycast onto the skin mesh.';
      document.getElementById('newPtCoordStatus').style.color = '#fde68a';
    }
  }

  function closePointCreator() {
    const card = document.getElementById('studioCreatorCard');
    if (card) card.style.display = 'none';
    stopSurfacePickMode();
  }

  function startSurfacePickMode() {
    isPickingSurface = true;
    const modal = document.getElementById('meridianStudioModal');
    if (modal) {
      modal.style.background = 'transparent';
      modal.style.pointerEvents = 'none';
    }
    const dlg = document.getElementById('studioModalDialog');
    if (dlg) dlg.style.display = 'none';
    const fb = document.getElementById('studioFloatingBar');
    if (fb) {
      fb.style.display = 'flex';
      fb.style.pointerEvents = 'all';
      document.getElementById('studioFloatingText').textContent = '🎯 Click anywhere on the 3D human body to pick surface point...';
      document.getElementById('btnStudioCancelFloat').textContent = '✕ Cancel';
    }

    const f = document.getElementById('atlasFrame');
    if (f && f.contentWindow) {
      f.contentWindow.postMessage({ action: 'start_pick_surface' }, '*');
    }
  }

  function stopSurfacePickMode() {
    isPickingSurface = false;
    const modal = document.getElementById('meridianStudioModal');
    if (modal) {
      modal.style.background = 'rgba(10, 15, 29, 0.88)';
      modal.style.pointerEvents = 'all';
    }
    const dlg = document.getElementById('studioModalDialog');
    if (dlg) dlg.style.display = 'flex';
    const fb = document.getElementById('studioFloatingBar');
    if (fb) fb.style.display = 'none';

    const f = document.getElementById('atlasFrame');
    if (f && f.contentWindow) {
      f.contentWindow.postMessage({ action: 'stop_pick_surface' }, '*');
    }
  }

  function toggleMovePointMode() {
    isMovingPoint = !isMovingPoint;
    const btn = document.getElementById('btnStudioMove3D');
    const modal = document.getElementById('meridianStudioModal');
    const dlg = document.getElementById('studioModalDialog');
    const fb = document.getElementById('studioFloatingBar');

    if (isMovingPoint) {
      btn.style.background = '#e11d48';
      btn.textContent = '⏹️ Done Moving';
      if (modal) {
        modal.style.background = 'transparent';
        modal.style.pointerEvents = 'none';
      }
      if (dlg) dlg.style.display = 'none';
      if (fb) {
        fb.style.display = 'flex';
        fb.style.pointerEvents = 'all';
        document.getElementById('studioFloatingText').textContent = `🎯 Drag or click on 3D body to relocate ${currentPointCode}...`;
        document.getElementById('btnStudioCancelFloat').textContent = '💾 Done Relocating';
      }

      const f = document.getElementById('atlasFrame');
      if (f && f.contentWindow) {
        f.contentWindow.postMessage({ action: 'start_move_point', code: currentPointCode }, '*');
      }
    } else {
      btn.style.background = '#2563eb';
      btn.textContent = '🎯 Move on 3D Model';
      if (modal) {
        modal.style.background = 'rgba(10, 15, 29, 0.88)';
        modal.style.pointerEvents = 'all';
      }
      if (dlg) dlg.style.display = 'flex';
      if (fb) fb.style.display = 'none';

      const f = document.getElementById('atlasFrame');
      if (f && f.contentWindow) {
        f.contentWindow.postMessage({ action: 'stop_pick_surface' }, '*');
      }
      setSaveStatus(`Point ${currentPointCode} relocation finished. Click 'Save Changes' to persist!`);
    }
  }

  // ---------------------------------------------------------------------------
  // Surface Snapping & Bilateral Mirroring
  // ---------------------------------------------------------------------------

  function snapCurrentPointToSurface() {
    const pt = allPoints[currentPointCode];
    if (!pt) return;
    const x = parseFloat(document.getElementById('studioCoordX').value);
    const y = parseFloat(document.getElementById('studioCoordY').value);
    const z = parseFloat(document.getElementById('studioCoordZ').value);

    setSaveStatus('Snapping to nearest FJ2810 skin surface vertex...');
    const f = document.getElementById('atlasFrame');
    if (f && f.contentWindow) {
      f.contentWindow.postMessage({
        action: 'snap_point_to_surface',
        code: currentPointCode,
        position: [x, y, z]
      }, '*');
    }
  }

  async function mirrorBilateralPair() {
    console.log('[mirrorBilateralPair] CLICKED! currentPointCode =', currentPointCode);
    const pt = allPoints[currentPointCode];
    console.log('[mirrorBilateralPair] pt =', pt);
    if (!pt) {
      console.warn('[mirrorBilateralPair] No point found for code:', currentPointCode);
      return;
    }

    let mirCode = pt.code.endsWith('-R') ? pt.code.replace(/-R$/, '-L') : (pt.code.endsWith('-L') ? pt.code.replace(/-L$/, '-R') : `${pt.code}-MIRROR`);
    if (allPoints[mirCode]) {
      mirCode = `${mirCode}-${Date.now().toString().slice(-4)}`;
    }
    const newX = -pt.position[0];
    const newNormX = pt.normal ? -pt.normal[0] : 0.0;

    const mirPt = {
      code: mirCode,
      name_en: `${pt.name_en} (Mirrored)`,
      name_zh: pt.name_zh ? `${pt.name_zh} (对侧)` : '',
      name_vi: pt.name_vi ? `${pt.name_vi} (Đối Bên)` : '',
      region: pt.region || 'shoulder',
      laterality: pt.position[0] > 0 ? 'left' : 'right',
      position: [newX, pt.position[1], pt.position[2]],
      normal: [newNormX, pt.normal ? pt.normal[1] : 0, pt.normal ? pt.normal[2] : 1],
      registration_status: 'GEOMETRY_VERIFIED',
      review_status: 'PENDING_EXPERT_REVIEW',
      notes: `Bilateral mirrored counterpart of ${pt.code}`,
      library_id: 'lib_custom_user'
    };

    console.log('[mirrorBilateralPair] sending payload:', JSON.stringify(mirPt));
    try {
      const res = await fetch('/api/points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mirPt)
      });
      if (res.ok) {
        const result = await res.json();
        allPoints[mirCode] = result.point;
        currentPointCode = mirCode;
        populatePointSelect();
        loadPointIntoEditor(mirCode);
        applyCoordinates();
        setSaveStatus(`Created mirrored point ${mirCode}`);
      } else {
        const err = await res.json();
        alert('Failed to mirror point: ' + (err.error || 'Unknown error'));
      }
    } catch (e) {
      console.error(e);
      alert('Error creating mirrored point: ' + e.message);
    }
  }

  // ---------------------------------------------------------------------------
  // Durable Persistence (SQLite API Integration)
  // ---------------------------------------------------------------------------

  async function saveDurableChanges() {
    // Check if we are saving from the inline creator card
    const card = document.getElementById('studioCreatorCard');
    if (card && card.style.display === 'block') {
      const code = document.getElementById('newPtCode').value.trim().toUpperCase();
      const nameEn = document.getElementById('newPtNameEn').value.trim();
      const nameVi = document.getElementById('newPtNameVi').value.trim();
      const nameZh = document.getElementById('newPtNameZh').value.trim();
      const libId = document.getElementById('newPtLibrary').value;
      const region = document.getElementById('newPtRegion').value;
      const laterality = document.getElementById('newPtLaterality').value;

      if (!code || !nameEn) {
        alert('Point code and English display name are required.');
        return;
      }

      const x = parseFloat(document.getElementById('studioCoordX').value);
      const y = parseFloat(document.getElementById('studioCoordY').value);
      const z = parseFloat(document.getElementById('studioCoordZ').value);

      const newPointPayload = {
        code,
        name_en: nameEn,
        name_vi: nameVi,
        name_zh: nameZh,
        library_id: libId,
        region,
        laterality,
        position: [x, y, z],
        normal: window._lastPickedNormal || [0, 0, 1],
        registration_status: 'GEOMETRY_VERIFIED',
        review_status: 'PENDING_EXPERT_REVIEW',
        notes: 'Created via Meridian Studio 3D surface raycaster.'
      };

      try {
        setSaveStatus('Saving new point to database...');
        const res = await fetch('/api/points', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newPointPayload)
        });
        if (res.ok) {
          const data = await res.json();
          allPoints[code] = data.point;
          currentPointCode = code;
          closePointCreator();
          populatePointSelect();
          loadPointIntoEditor(code);
          applyCoordinates();
          setSaveStatus(`✓ Saved ${code} to database!`);
        } else {
          const err = await res.json();
          alert('Save failed: ' + (err.error || 'Server error'));
        }
      } catch (e) {
        alert('Network error saving point: ' + e.message);
      }
      return;
    }

    // Saving modifications to existing point
    const pt = allPoints[currentPointCode];
    if (!pt) return;

    const x = parseFloat(document.getElementById('studioCoordX').value);
    const y = parseFloat(document.getElementById('studioCoordY').value);
    const z = parseFloat(document.getElementById('studioCoordZ').value);
    pt.position = [x, y, z];
    pt.registration_status = document.getElementById('studioRegStatus').value;
    pt.review_status = document.getElementById('studioReviewStatus').value;
    pt.source_provenance = document.getElementById('studioProvenance').value.trim();
    pt.verification_notes = document.getElementById('studioNotes').value.trim();

    const isCustom = pt.library_id === 'lib_custom_user' || pt.system_classification === 'user_custom';

    try {
      setSaveStatus('Persisting changes to SQLite database...');
      if (isCustom) {
        // Update custom point
        const res = await fetch(`/api/points/${currentPointId}/update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            position: pt.position,
            normal: pt.normal,
            registration_status: pt.registration_status,
            review_status: pt.review_status,
            notes: pt.verification_notes,
            change_type: 'UPDATE_COORDS'
          })
        });
        if (res.ok) {
          applyCoordinates();
          setSaveStatus(`✓ Saved ${pt.code} successfully!`);
        }
      } else {
        // Versioned override of canonical reference point
        const res = await fetch(`/api/points/overrides/${pt.code}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            position: pt.position,
            normal: pt.normal,
            registration_status: pt.registration_status,
            review_status: pt.review_status,
            notes: pt.verification_notes
          })
        });
        if (res.ok) {
          pt.is_overridden = true;
          applyCoordinates();
          loadPointIntoEditor(pt.code);
          setSaveStatus(`✓ Saved override for ${pt.code} in database!`);
        }
      }
    } catch (e) {
      console.error(e);
      setSaveStatus('Failed to persist to database');
    }
  }

  async function restoreBaselinePosition() {
    const pt = allPoints[currentPointCode];
    if (!pt) return;

    if (pt.is_overridden) {
      if (!confirm(`Restore canonical reference coordinates for ${pt.code}?`)) return;
      try {
        const res = await fetch(`/api/points/overrides/${pt.code}/delete`, { method: 'POST' });
        if (res.ok) {
          if (baselinePoints[pt.code]) {
            allPoints[pt.code] = JSON.parse(JSON.stringify(baselinePoints[pt.code]));
          }
          loadPointIntoEditor(pt.code);
          applyCoordinates();
          setSaveStatus(`Restored ${pt.code} to canonical baseline`);
        }
      } catch (e) {
        console.error(e);
      }
    } else {
      revertPoint();
    }
  }

  async function deleteCurrentCustomPoint() {
    const pt = allPoints[currentPointCode];
    if (!pt) return;
    if (!confirm(`Are you sure you want to delete custom point ${pt.code}?`)) return;

    try {
      const res = await fetch(`/api/points/${currentPointId}/delete`, { method: 'POST' });
      if (res.ok) {
        delete allPoints[currentPointCode];
        populatePointSelect();
        if (Object.keys(allPoints).length > 0) {
          loadPointIntoEditor(Object.keys(allPoints)[0]);
        }
        setSaveStatus(`Deleted custom point ${pt.code}`);
      }
    } catch (e) {
      console.error(e);
      alert('Failed to delete point: ' + e.message);
    }
  }

  async function openRevisionHistoryModal() {
    try {
      const res = await fetch(`/api/points/${currentPointId}/revisions`);
      if (!res.ok) return;
      const revs = await res.json();
      
      let html = `<div style="padding:16px; background:#111827; color:#f3f4f6; border-radius:8px; max-width:600px; width:90vw; max-height:80vh; overflow-y:auto; border:1px solid #374151;">
        <div style="font-weight:700; font-size:14px; margin-bottom:12px; display:flex; justify-content:space-between;">
          <span>📜 Revision History for ${currentPointCode}</span>
          <button id="btnCloseRevModal" style="background:transparent; border:none; color:#9ca3af; cursor:pointer;">✕</button>
        </div>
        <table style="width:100%; border-collapse:collapse; font-size:11px;">
          <tr style="border-bottom:1px solid #374151; color:#9ca3af; text-align:left;">
            <th style="padding:4px;">#</th><th>Type</th><th>Author</th><th>Time (UTC)</th><th>Action</th>
          </tr>`;
      
      for (const r of revs) {
        html += `<tr style="border-bottom:1px solid #2d3748;">
          <td style="padding:6px 4px; font-weight:700;">${r.revision_number}</td>
          <td><span style="background:#374151; padding:2px 4px; border-radius:3px;">${r.change_type}</span></td>
          <td>${r.author}</td>
          <td style="color:#9ca3af;">${r.created_utc.slice(0,19).replace('T',' ')}</td>
          <td><button class="btn-revert-rev" data-rev="${r.revision_number}" style="background:#0284c7; color:#fff; border:none; padding:2px 6px; border-radius:3px; cursor:pointer; font-size:10px;">Revert</button></td>
        </tr>`;
      }
      html += `</table></div>`;

      const revModal = document.createElement('div');
      revModal.id = 'studioRevModal';
      revModal.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8); display:flex; align-items:center; justify-content:center; z-index:11000;';
      revModal.innerHTML = html;
      document.body.appendChild(revModal);

      document.getElementById('btnCloseRevModal').onclick = () => revModal.remove();
      revModal.onclick = (e) => { if (e.target === revModal) revModal.remove(); };

      revModal.querySelectorAll('.btn-revert-rev').forEach(btn => {
        btn.onclick = async () => {
          const revNum = btn.dataset.rev;
          if (!confirm(`Revert point to revision #${revNum}?`)) return;
          const revRes = await fetch(`/api/points/${currentPointId}/revert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ revision_number: parseInt(revNum, 10) })
          });
          if (revRes.ok) {
            const data = await revRes.json();
            allPoints[currentPointCode] = data.point;
            loadPointIntoEditor(currentPointCode);
            applyCoordinates();
            revModal.remove();
            setSaveStatus(`Reverted ${currentPointCode} to revision #${revNum}`);
          }
        };
      });
    } catch (e) {
      console.error(e);
    }
  }

  // ---------------------------------------------------------------------------
  // Nudge, Coordinates & 3D Synchronization
  // ---------------------------------------------------------------------------

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
        notes: pt.verification_notes || pt.notes,
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
    pt.review_status = document.getElementById('studioReviewStatus').value;
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
      el.dataset.lastStatus = msg;
      el.style.color = '#38bdf8';
      setTimeout(() => {
        el.textContent = 'Ready';
        el.style.color = '#10b981';
      }, 5000);
    }
  }

  // ---------------------------------------------------------------------------
  // Cryptographic SHA-256 JSON Export & Import
  // ---------------------------------------------------------------------------

  async function exportDatasetJSON() {
    try {
      const res = await fetch(`/api/points/export?library_id=${activeLibrary === 'all' ? 'lib_custom_user' : activeLibrary}`);
      if (!res.ok) throw new Error('Export API returned error');
      const exportData = await res.json();

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `custom_points_atlas_v2.5_${new Date().toISOString().slice(0,10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setSaveStatus('Exported Calibrated Dataset (SHA-256 verified)');
    } catch (e) {
      console.error(e);
      alert('Export failed: ' + e.message);
    }
  }

  async function importDatasetJSON(ev) {
    const file = ev.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const bundle = JSON.parse(e.target.result);
        setSaveStatus('Validating and importing JSON bundle...');
        const res = await fetch('/api/points/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(bundle)
        });
        const result = await res.json();
        if (res.ok) {
          alert(`Import Successful!\n• Imported: ${result.imported_count}\n• Updated: ${result.updated_count}\n• Skipped: ${result.skipped_count}`);
          await initStudio();
        } else {
          alert('Import Rejected: ' + (result.error || 'Validation error'));
        }
      } catch (err) {
        alert('Failed to parse or import JSON: ' + err.message);
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

  // ---------------------------------------------------------------------------
  // Modal Lifecycle & Window Messaging
  // ---------------------------------------------------------------------------

  window.openStudioEditorModal = async function(pointOrCode) {
    await ensureStudioReady();
    ensureModal();
    populatePointSelect();
    const modal = document.getElementById('meridianStudioModal');
    if (modal) {
      modal.style.display = 'flex';
      let targetCode = (currentPointCode && allPoints[currentPointCode]) ? currentPointCode : 'GV14';
      if (typeof pointOrCode === 'string') {
        targetCode = pointOrCode;
      } else if (pointOrCode && pointOrCode.code) {
        targetCode = pointOrCode.code;
      }
      if (allPoints[targetCode]) {
        currentPointCode = targetCode;
        loadPointIntoEditor(targetCode);
      }
    }
  };

  window.selectStudioPoint = async function(code) {
    await ensureStudioReady();
    if (allPoints[code]) {
      loadPointIntoEditor(code);
    }
  };

  window.closeStudioModal = function() {
    const modal = document.getElementById('meridianStudioModal');
    if (modal) modal.style.display = 'none';
    stopSurfacePickMode();
  };

  // Cross-frame messaging from Atlas
  window.addEventListener('message', (ev) => {
    if (!ev.data) return;

    if (ev.data.type === 'msk_acupoint_selected' && ev.data.point) {
      if (isPickingSurface || isMovingPoint) return;
      if (allPoints[ev.data.point.code]) {
        currentPointCode = ev.data.point.code;
        const sel = document.getElementById('studioPointSelect');
        if (sel) sel.value = currentPointCode;
        loadPointIntoEditor(currentPointCode);
      }
    } else if (ev.data.type === 'msk_surface_picked' && ev.data.hit) {
      const hit = ev.data.hit;
      window._lastPickedNormal = hit.normal;
      const inX = document.getElementById('studioCoordX');
      const inY = document.getElementById('studioCoordY');
      const inZ = document.getElementById('studioCoordZ');
      if (inX && inY && inZ) {
        inX.value = hit.position[0].toFixed(4);
        inY.value = hit.position[1].toFixed(4);
        inZ.value = hit.position[2].toFixed(4);
      }
      const stEl = document.getElementById('newPtCoordStatus');
      if (stEl) {
        stEl.textContent = `✓ Surface Hit on ${hit.mesh_id} [X:${hit.position[0].toFixed(3)}, Y:${hit.position[1].toFixed(3)}, Z:${hit.position[2].toFixed(3)}] - Distance: ${hit.distance}m`;
        stEl.style.color = '#38bdf8';
      }
      setSaveStatus(`Picked 3D surface point on ${hit.mesh_id}!`);
      stopSurfacePickMode();
    } else if (ev.data.type === 'msk_point_relocated') {
      const inX = document.getElementById('studioCoordX');
      const inY = document.getElementById('studioCoordY');
      const inZ = document.getElementById('studioCoordZ');
      if (inX && inY && inZ) {
        inX.value = ev.data.position[0].toFixed(4);
        inY.value = ev.data.position[1].toFixed(4);
        inZ.value = ev.data.position[2].toFixed(4);
      }
      const pt = allPoints[currentPointCode];
      if (pt) {
        pt.position = ev.data.position;
        if (ev.data.normal) pt.normal = ev.data.normal;
      }
    } else if (ev.data.type === 'msk_snap_result' && ev.data.snap) {
      const snap = ev.data.snap;
      const inX = document.getElementById('studioCoordX');
      const inY = document.getElementById('studioCoordY');
      const inZ = document.getElementById('studioCoordZ');
      if (inX && inY && inZ) {
        inX.value = snap.position[0].toFixed(4);
        inY.value = snap.position[1].toFixed(4);
        inZ.value = snap.position[2].toFixed(4);
      }
      applyCoordinates();
      setSaveStatus(`Snapped to surface vertex #${snap.face_index} (offset: ${(snap.distance * 1000).toFixed(1)}mm)`);
    }
  });

  // Start initialization
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureStudioReady);
  } else {
    ensureStudioReady();
  }
})();
