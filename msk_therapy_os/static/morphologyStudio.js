/**
 * M2.12 Three-Photo Patient Morphology Studio Frontend.
 *
 * Provides parametric surface-only avatar adjustment, dual-model visualization,
 * and structured region-anchored anthropometric observations.
 */
(() => {
  let activeCaseId = "DEMO-NECK-001";
  let activeAvatar = null;
  let curParams = {
    height_cm: 172.0,
    weight_kg: 70.0,
    chest_circ_cm: 96.0,
    waist_circ_cm: 82.0,
    hip_circ_cm: 99.0,
    shoulder_width_cm: 44.0,
    abdomen_prominence: 0.2,
    pelvic_tilt_deg: 0.0,
  };

  async function api(path, options = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
  }

  function initMorphologyStudio() {
    const container = document.getElementById("tab-morphology");
    if (!container) return;

    const caseSelect = document.getElementById("morphCaseSelect");
    const reloadBtn = document.getElementById("morphReloadBtn");
    const createBtn = document.getElementById("morphCreateBtn");
    const saveParamsBtn = document.getElementById("morphSaveParamsBtn");
    const saveObsBtn = document.getElementById("morphSaveObsBtn");

    if (caseSelect) {
      caseSelect.addEventListener("change", (e) => {
        activeCaseId = e.target.value;
        loadCaseAvatars();
      });
    }

    if (reloadBtn) reloadBtn.addEventListener("click", loadCaseAvatars);
    if (createBtn) createBtn.addEventListener("click", createNewAvatarVersion);
    if (saveParamsBtn) saveParamsBtn.addEventListener("click", saveSurfaceParameters);
    if (saveObsBtn) saveObsBtn.addEventListener("click", saveRegionObservation);

    // Bind slider events
    [
      "height_cm", "weight_kg", "chest_circ_cm", "waist_circ_cm",
      "hip_circ_cm", "shoulder_width_cm", "abdomen_prominence", "pelvic_tilt_deg"
    ].forEach((param) => {
      const slider = document.getElementById(`morph_${param}`);
      const valDisp = document.getElementById(`val_${param}`);
      if (slider) {
        slider.addEventListener("input", (e) => {
          curParams[param] = parseFloat(e.target.value);
          if (valDisp) valDisp.textContent = e.target.value;
          renderAvatarSilhouettes();
        });
      }
    });

    loadCaseAvatars();
  }

  async function loadCaseAvatars() {
    const statusEl = document.getElementById("morphStatus");
    if (statusEl) statusEl.textContent = "Loading avatars...";
    try {
      const avatars = await api(`/api/morphology/avatars?case_id=${encodeURIComponent(activeCaseId)}`);
      const selectEl = document.getElementById("morphAvatarSelect");
      if (selectEl) {
        selectEl.innerHTML = "";
        if (avatars.length === 0) {
          const opt = document.createElement("option");
          opt.value = "";
          opt.textContent = "No avatars found. Create version 1.";
          selectEl.appendChild(opt);
          activeAvatar = null;
          renderEmptyCanvas();
        } else {
          avatars.forEach((a) => {
            const opt = document.createElement("option");
            opt.value = a.avatar_id;
            opt.textContent = `v${a.version_num}: ${a.title} (${a.status})`;
            selectEl.appendChild(opt);
          });
          selectEl.addEventListener("change", (e) => selectAvatar(e.target.value));
          selectAvatar(avatars[0].avatar_id);
        }
      }
      if (statusEl) statusEl.textContent = `Found ${avatars.length} avatar version(s).`;
    } catch (err) {
      if (statusEl) statusEl.textContent = `Error: ${err.message}`;
    }
  }

  async function selectAvatar(avatarId) {
    if (!avatarId) return;
    try {
      activeAvatar = await api(`/api/morphology/avatars/${encodeURIComponent(avatarId)}`);
      curParams = { ...curParams, ...(activeAvatar.params || {}) };
      updateSliderValues();
      renderAvatarSilhouettes();
      loadAvatarObservations(avatarId);
    } catch (err) {
      console.error("Failed to select avatar", err);
    }
  }

  function updateSliderValues() {
    Object.keys(curParams).forEach((param) => {
      const slider = document.getElementById(`morph_${param}`);
      const valDisp = document.getElementById(`val_${param}`);
      if (slider && curParams[param] !== undefined) {
        slider.value = curParams[param];
      }
      if (valDisp && curParams[param] !== undefined) {
        valDisp.textContent = curParams[param];
      }
    });
  }

  async function createNewAvatarVersion() {
    const statusEl = document.getElementById("morphStatus");
    if (statusEl) statusEl.textContent = "Creating new surface avatar version...";
    try {
      const res = await api("/api/morphology/avatars", {
        method: "POST",
        body: JSON.stringify({
          case_id: activeCaseId,
          title: `Morphology Evaluation (${new Date().toLocaleDateString()})`,
          height_cm: curParams.height_cm,
          weight_kg: curParams.weight_kg,
          chest_circ_cm: curParams.chest_circ_cm,
          waist_circ_cm: curParams.waist_circ_cm,
          hip_circ_cm: curParams.hip_circ_cm,
          extra_params: curParams,
        }),
      });
      loadCaseAvatars();
      if (statusEl) statusEl.textContent = `Avatar version ${res.avatar.version_num} created successfully.`;
    } catch (err) {
      if (statusEl) statusEl.textContent = `Creation failed: ${err.message}`;
    }
  }

  async function saveSurfaceParameters() {
    if (!activeAvatar) return;
    const statusEl = document.getElementById("morphStatus");
    if (statusEl) statusEl.textContent = "Saving surface parameters...";
    try {
      const res = await api(`/api/morphology/avatars/${encodeURIComponent(activeAvatar.avatar_id)}`, {
        method: "PUT",
        body: JSON.stringify({
          params: curParams,
          notes: document.getElementById("morphNotes")?.value || "",
        }),
      });
      activeAvatar = res.avatar;
      if (statusEl) statusEl.textContent = "Surface avatar parameters saved successfully.";
    } catch (err) {
      if (statusEl) statusEl.textContent = `Save failed: ${err.message}`;
    }
  }

  function renderAvatarSilhouettes() {
    const frontSvg = document.getElementById("morphFrontSvg");
    const sideSvg = document.getElementById("morphSideSvg");
    if (!frontSvg || !sideSvg) return;

    // Relative scales derived from parameters
    const heightScale = curParams.height_cm / 170.0;
    const waistScale = curParams.waist_circ_cm / 80.0;
    const chestScale = curParams.chest_circ_cm / 95.0;
    const hipScale = curParams.hip_circ_cm / 98.0;
    const shldScale = (curParams.shoulder_width_cm || 44.0) / 44.0;
    const abdProm = curParams.abdomen_prominence || 0.0;

    // Render Front View Silhouette
    frontSvg.innerHTML = `
      <defs>
        <linearGradient id="avatarGradFront" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#1e293b"/>
          <stop offset="50%" stop-color="#334155"/>
          <stop offset="100%" stop-color="#1e293b"/>
        </linearGradient>
      </defs>
      <!-- Head -->
      <ellipse cx="150" cy="${50 * heightScale}" rx="22" ry="28" fill="url(#avatarGradFront)" stroke="#38bdf8" stroke-width="1.5"/>
      <!-- Neck -->
      <rect x="142" y="${78 * heightScale}" width="16" height="${20 * heightScale}" fill="#334155"/>
      <!-- Torso -->
      <path d="
        M ${150 - 55 * shldScale} ${98 * heightScale}
        L ${150 + 55 * shldScale} ${98 * heightScale}
        L ${150 + 44 * chestScale} ${145 * heightScale}
        L ${150 + 36 * waistScale} ${195 * heightScale}
        L ${150 + 48 * hipScale} ${245 * heightScale}
        L ${150 - 48 * hipScale} ${245 * heightScale}
        L ${150 - 36 * waistScale} ${195 * heightScale}
        L ${150 - 44 * chestScale} ${145 * heightScale}
        Z"
        fill="url(#avatarGradFront)" stroke="#38bdf8" stroke-width="2"/>
      <!-- Arms -->
      <line x1="${150 - 55 * shldScale}" y1="${98 * heightScale}" x2="${150 - 75 * shldScale}" y2="${230 * heightScale}" stroke="#334155" stroke-width="16" stroke-linecap="round"/>
      <line x1="${150 + 55 * shldScale}" y1="${98 * heightScale}" x2="${150 + 75 * shldScale}" y2="${230 * heightScale}" stroke="#334155" stroke-width="16" stroke-linecap="round"/>
      <!-- Legs -->
      <line x1="${150 - 24 * hipScale}" y1="${245 * heightScale}" x2="${150 - 24 * hipScale}" y2="${430 * heightScale}" stroke="#334155" stroke-width="22" stroke-linecap="round"/>
      <line x1="${150 + 24 * hipScale}" y1="${245 * heightScale}" x2="${150 + 24 * hipScale}" y2="${430 * heightScale}" stroke="#334155" stroke-width="22" stroke-linecap="round"/>
      <text x="10" y="25" fill="#38bdf8" font-size="11" font-weight="bold">FRONT SILHOUETTE</text>
      <text x="10" y="42" fill="#94a3b8" font-size="9">Height: ${curParams.height_cm}cm | Waist: ${curParams.waist_circ_cm}cm</text>
    `;

    // Render Side View Silhouette
    sideSvg.innerHTML = `
      <defs>
        <linearGradient id="avatarGradSide" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#1e293b"/>
          <stop offset="50%" stop-color="#334155"/>
          <stop offset="100%" stop-color="#1e293b"/>
        </linearGradient>
      </defs>
      <!-- Head Side -->
      <ellipse cx="140" cy="${50 * heightScale}" rx="26" ry="28" fill="url(#avatarGradSide)" stroke="#38bdf8" stroke-width="1.5"/>
      <!-- Torso Profile with Abdomen Prominence -->
      <path d="
        M 125 ${98 * heightScale}
        C 155 ${98 * heightScale}, 160 ${140 * heightScale}, ${155 + abdProm * 20} ${195 * heightScale}
        C ${150 + abdProm * 20} ${230 * heightScale}, 145 ${245 * heightScale}, 145 ${245 * heightScale}
        L 115 ${245 * heightScale}
        C 110 ${200 * heightScale}, 115 ${140 * heightScale}, 125 ${98 * heightScale}
        Z"
        fill="url(#avatarGradSide)" stroke="#38bdf8" stroke-width="2"/>
      <!-- Leg Side -->
      <line x1="130" y1="${245 * heightScale}" x2="132" y2="${430 * heightScale}" stroke="#334155" stroke-width="26" stroke-linecap="round"/>
      <text x="10" y="25" fill="#38bdf8" font-size="11" font-weight="bold">SAGITTAL PROFILE</text>
      <text x="10" y="42" fill="#94a3b8" font-size="9">Abdomen Prominence: ${abdProm}</text>
    `;
  }

  async function saveRegionObservation() {
    if (!activeAvatar) return;
    const statusEl = document.getElementById("morphStatus");
    const region = document.getElementById("morphObsRegion").value;
    const type = document.getElementById("morphObsType").value;
    const sev = document.getElementById("morphObsSeverity").value;
    const desc = document.getElementById("morphObsDesc").value;

    if (!desc.trim()) {
      alert("Please enter a summary of the physical finding.");
      return;
    }

    try {
      await api("/api/morphology/observations", {
        method: "POST",
        body: JSON.stringify({
          avatar_id: activeAvatar.avatar_id,
          case_id: activeCaseId,
          body_region: region,
          observation_type: type,
          severity: sev ? parseInt(sev, 10) : null,
          findings_summary: desc.trim(),
          operator_notes: "Recorded during Morphology Studio review",
        }),
      });
      loadAvatarObservations(activeAvatar.avatar_id);
      if (statusEl) statusEl.textContent = "Observation anchored to avatar surface.";
    } catch (err) {
      if (statusEl) statusEl.textContent = `Observation save failed: ${err.message}`;
    }
  }

  async function loadAvatarObservations(avatarId) {
    const listEl = document.getElementById("morphObsList");
    if (!listEl) return;
    try {
      const obs = await api(`/api/morphology/observations?avatar_id=${encodeURIComponent(avatarId)}`);
      if (obs.length === 0) {
        listEl.innerHTML = "<small style='color:var(--text-muted);'>No region findings attached to this avatar.</small>";
      } else {
        listEl.innerHTML = obs
          .map(
            (o) => `
          <div style="background: rgba(30,41,59,0.6); padding:6px 10px; border-radius:4px; margin-bottom:6px; font-size:11px; border-left:3px solid #38bdf8;">
            <div style="display:flex; justify-content:space-between;">
              <strong>${o.body_region.replace("_", " ").toUpperCase()}</strong>
              <span class="badge" style="font-size:10px;">${o.observation_type}</span>
            </div>
            <div style="margin:2px 0;">${o.findings_summary}</div>
            <div style="color:var(--text-muted); font-size:10px;">Severity: ${o.severity !== null ? o.severity : "N/A"}/10</div>
          </div>
        `
          )
          .join("");
      }
    } catch (err) {
      console.error("Failed to load morphology observations", err);
    }
  }

  function renderEmptyCanvas() {
    const front = document.getElementById("morphFrontSvg");
    const side = document.getElementById("morphSideSvg");
    if (front) front.innerHTML = "<text x='50' y='150' fill='#94a3b8'>No avatar version loaded</text>";
    if (side) side.innerHTML = "";
  }

  window.addEventListener("DOMContentLoaded", initMorphologyStudio);
})();
