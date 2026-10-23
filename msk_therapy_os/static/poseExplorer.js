/**
 * M2.11 Pose-to-Anatomy Explorer Frontend.
 *
 * Provides interactive 2D pose skeleton inspection, manual landmark adjustment,
 * candidate muscle role visualization, and encounter-linked symptom recording.
 * Strictly adheres to non-diagnostic educational disclosures.
 */
(() => {
  let activeStudy = null;
  let activeCaseId = "DEMO-NECK-001";
  let curLandmarks = [];
  let selectedLandmarkIdx = null;

  // MediaPipe skeleton connectivity pairs
  const POSE_CONNECTIONS = [
    [11, 12], // shoulders
    [11, 13], [13, 15], // left arm
    [12, 14], [14, 16], // right arm
    [11, 23], [12, 24], // trunk
    [23, 24], // hips
    [23, 25], [25, 27], // left leg
    [24, 26], [26, 28], // right leg
  ];

  async function api(path, options = {}) {
    const fetchFn = (typeof window.apiFetch === 'function') ? window.apiFetch : fetch;
    const res = await fetchFn(path, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
  }

  function initPoseExplorer() {
    const container = document.getElementById("tab-pose");
    if (!container) return;

    const caseSelect = document.getElementById("poseCaseSelect");
    const loadBtn = document.getElementById("poseLoadBtn");
    const createDemoBtn = document.getElementById("poseCreateDemoBtn");
    const saveLmBtn = document.getElementById("poseSaveLmBtn");
    const saveObsBtn = document.getElementById("poseSaveObsBtn");
    const focusAtlasBtn = document.getElementById("poseFocusAtlasBtn");

    if (caseSelect) {
      caseSelect.addEventListener("change", (e) => {
        activeCaseId = e.target.value;
        loadCaseStudies();
      });
    }

    if (loadBtn) loadBtn.addEventListener("click", loadCaseStudies);
    if (createDemoBtn) createDemoBtn.addEventListener("click", createSyntheticDemoStudy);
    if (saveLmBtn) saveLmBtn.addEventListener("click", saveLandmarkOverrides);
    if (saveObsBtn) saveObsBtn.addEventListener("click", savePoseObservation);
    if (focusAtlasBtn) focusAtlasBtn.addEventListener("click", focusCandidateMusclesInAtlas);

    loadCaseStudies();
  }

  async function loadCaseStudies() {
    const statusEl = document.getElementById("poseStatus");
    if (statusEl) statusEl.textContent = "Loading pose studies...";
    try {
      const studies = await api(`/api/pose/studies?case_id=${encodeURIComponent(activeCaseId)}`);
      const listEl = document.getElementById("poseStudySelect");
      if (listEl) {
        listEl.innerHTML = "";
        if (studies.length === 0) {
          const opt = document.createElement("option");
          opt.value = "";
          opt.textContent = "No studies (Click 'Load Sample Pose')";
          listEl.appendChild(opt);
          activeStudy = null;
          renderEmptyCanvas();
        } else {
          studies.forEach((s) => {
            const opt = document.createElement("option");
            opt.value = s.study_id;
            opt.textContent = `${s.title} (${s.camera_view})`;
            listEl.appendChild(opt);
          });
          listEl.addEventListener("change", (e) => selectStudy(e.target.value));
          selectStudy(studies[0].study_id);
        }
      }
      if (statusEl) statusEl.textContent = `Found ${studies.length} pose study(ies).`;
    } catch (err) {
      if (statusEl) statusEl.textContent = `Error: ${err.message}`;
    }
  }

  async function selectStudy(studyId) {
    if (!studyId) return;
    try {
      activeStudy = await api(`/api/pose/studies/${encodeURIComponent(studyId)}`);
      curLandmarks = (activeStudy.landmarks || []).map((lm) => ({ ...lm }));
      renderPoseSkeleton();
      renderActionInsights();
      loadStudyObservations(studyId);
    } catch (err) {
      console.error("Failed to select study", err);
    }
  }

  async function createSyntheticDemoStudy() {
    const statusEl = document.getElementById("poseStatus");
    if (statusEl) statusEl.textContent = "Generating synthetic demonstration pose...";
    const syntheticLandmarks = [
      { index: 0, u: 0.50, v: 0.12, confidence: 0.95 },  // nose
      { index: 11, u: 0.44, v: 0.26, confidence: 0.90 }, // left shoulder
      { index: 12, u: 0.56, v: 0.26, confidence: 0.90 }, // right shoulder
      { index: 13, u: 0.28, v: 0.28, confidence: 0.88 }, // left elbow (abducted ~90 deg)
      { index: 14, u: 0.62, v: 0.38, confidence: 0.85 }, // right elbow
      { index: 15, u: 0.18, v: 0.24, confidence: 0.82 }, // left wrist
      { index: 16, u: 0.64, v: 0.50, confidence: 0.85 }, // right wrist
      { index: 23, u: 0.46, v: 0.58, confidence: 0.92 }, // left hip
      { index: 24, u: 0.54, v: 0.58, confidence: 0.92 }, // right hip
      { index: 25, u: 0.45, v: 0.76, confidence: 0.88 }, // left knee
      { index: 26, u: 0.55, v: 0.76, confidence: 0.88 }, // right knee
      { index: 27, u: 0.45, v: 0.92, confidence: 0.85 }, // left ankle
      { index: 28, u: 0.55, v: 0.92, confidence: 0.85 }, // right ankle
    ];

    try {
      const res = await api("/api/pose/studies", {
        method: "POST",
        body: JSON.stringify({
          case_id: activeCaseId,
          title: `Synthetic Shoulder Abduction Drill (${new Date().toLocaleTimeString()})`,
          camera_view: "front",
          image_asset: "/static/research_demo/face_front.svg",
          image_sha256: "synthetic_demo_hash",
          landmarks: syntheticLandmarks,
        }),
      });
      loadCaseStudies();
      if (statusEl) statusEl.textContent = "Synthetic demonstration pose loaded successfully.";
    } catch (err) {
      if (statusEl) statusEl.textContent = `Creation failed: ${err.message}`;
    }
  }

  function renderPoseSkeleton() {
    const svg = document.getElementById("poseSvg");
    if (!svg) return;
    svg.innerHTML = "";

    const w = 400;
    const h = 500;

    // Draw background grid
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    defs.innerHTML = `
      <pattern id="poseGrid" width="20" height="20" patternUnits="userSpaceOnUse">
        <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
      </pattern>
    `;
    svg.appendChild(defs);

    const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bg.setAttribute("width", "100%");
    bg.setAttribute("height", "100%");
    bg.setAttribute("fill", "url(#poseGrid)");
    svg.appendChild(bg);

    const lmMap = {};
    curLandmarks.forEach((lm) => {
      lmMap[lm.index] = lm;
    });

    // 1. Draw connecting bones
    POSE_CONNECTIONS.forEach(([i1, i2]) => {
      const p1 = lmMap[i1];
      const p2 = lmMap[i2];
      if (p1 && p2 && p1.confidence >= 0.5 && p2.confidence >= 0.5) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", p1.u * w);
        line.setAttribute("y1", p1.v * h);
        line.setAttribute("x2", p2.u * w);
        line.setAttribute("y2", p2.v * h);
        line.setAttribute("stroke", "#38bdf8");
        line.setAttribute("stroke-width", "3");
        line.setAttribute("stroke-linecap", "round");
        svg.appendChild(line);
      }
    });

    // 2. Draw landmark points
    curLandmarks.forEach((lm) => {
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const cx = lm.u * w;
      const cy = lm.v * h;

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", cx);
      circle.setAttribute("cy", cy);
      circle.setAttribute("r", selectedLandmarkIdx === lm.index ? "7" : "5");
      circle.setAttribute("fill", lm.is_manual_override ? "#f59e0b" : lm.confidence < 0.5 ? "#ef4444" : "#10b981");
      circle.setAttribute("stroke", "#ffffff");
      circle.setAttribute("stroke-width", "1.5");
      circle.style.cursor = "pointer";

      circle.addEventListener("click", () => {
        selectedLandmarkIdx = lm.index;
        updateLandmarkEditor(lm);
        renderPoseSkeleton();
      });

      g.appendChild(circle);

      // Label on hover or selected
      if (selectedLandmarkIdx === lm.index) {
        const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
        txt.setAttribute("x", cx + 10);
        txt.setAttribute("y", cy - 5);
        txt.setAttribute("fill", "#f8fafc");
        txt.setAttribute("font-size", "11px");
        txt.setAttribute("font-weight", "bold");
        txt.textContent = `${lm.name} (#${lm.index})`;
        g.appendChild(txt);
      }

      svg.appendChild(g);
    });

    // SVG click to relocate selected landmark
    svg.onmousedown = (e) => {
      if (selectedLandmarkIdx === null) return;
      const rect = svg.getBoundingClientRect();
      const clickX = (e.clientX - rect.left) / rect.width;
      const clickY = (e.clientY - rect.top) / rect.height;
      if (clickX >= 0 && clickX <= 1 && clickY >= 0 && clickY <= 1) {
        const lm = curLandmarks.find((l) => l.index === selectedLandmarkIdx);
        if (lm) {
          lm.u = Math.round(clickX * 1000) / 1000;
          lm.v = Math.round(clickY * 1000) / 1000;
          lm.is_manual_override = true;
          updateLandmarkEditor(lm);
          renderPoseSkeleton();
        }
      }
    };
  }

  function updateLandmarkEditor(lm) {
    const editContainer = document.getElementById("poseLandmarkEditor");
    if (!editContainer) return;
    editContainer.innerHTML = `
      <div style="background: rgba(30, 41, 59, 0.8); padding: 8px; border-radius: 6px; border: 1px solid var(--border); margin-top: 8px;">
        <div style="font-weight: 600; color: var(--primary); font-size: 12px;">Active Landmark: ${lm.name} (#${lm.index})</div>
        <div style="display: flex; gap: 8px; align-items: center; margin-top: 4px; font-size: 11px;">
          <span>U: <strong>${lm.u}</strong></span>
          <span>V: <strong>${lm.v}</strong></span>
          <span>Conf: <strong>${(lm.confidence * 100).toFixed(0)}%</strong></span>
          ${lm.is_manual_override ? '<span style="color:#f59e0b;">(Manual Override)</span>' : ""}
        </div>
        <small style="color: var(--text-muted); display: block; margin-top: 4px;">Click anywhere on the pose canvas to reposition this landmark.</small>
      </div>
    `;
  }

  function renderActionInsights() {
    const insightsEl = document.getElementById("poseActionInsights");
    if (!insightsEl || !activeStudy) return;

    const estimates = activeStudy.action_estimates || [];
    if (estimates.length === 0) {
      insightsEl.innerHTML = "<p style='color:var(--text-muted);'>No motion estimates available.</p>";
      return;
    }

    let html = "";
    estimates.forEach((est) => {
      const isAbstain = est.status === "ABSTAIN";
      html += `
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid ${isAbstain ? "#ef4444" : "#38bdf8"}; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color: var(--text);">${est.action.replace("_", " ").toUpperCase()} (${est.side})</strong>
            <span class="badge" style="background:${isAbstain ? "rgba(239,68,68,0.2)" : "rgba(56,189,248,0.2)"}; color:${isAbstain ? "#ef4444" : "#38bdf8"};">
              ${est.status}
            </span>
          </div>
          ${
            est.estimated_angle_deg !== null && est.estimated_angle_deg !== undefined
              ? `<div style="font-size:18px; font-weight:700; color:#38bdf8; margin:4px 0;">${est.estimated_angle_deg}°</div>`
              : ""
          }
          <div style="font-size: 11px; color: var(--text-muted);">${est.disclaimer || est.reason || ""}</div>
          ${
            est.candidate_muscles && est.candidate_muscles.length > 0
              ? `
            <div style="margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 6px;">
              <small style="font-weight: 600; color: #f59e0b;">Candidate Muscles (Curated Biomechanical Roles):</small>
              <ul style="margin: 4px 0 0 16px; font-size: 11px; color: var(--text);">
                ${est.candidate_muscles
                  .map(
                    (m) =>
                      `<li><strong>${m.name}</strong> — <em>${m.role}</em> <span style="color:var(--text-muted);">(${m.evidence_source})</span></li>`
                  )
                  .join("")}
              </ul>
            </div>`
              : ""
          }
        </div>
      `;
    });

    insightsEl.innerHTML = html;
  }

  async function saveLandmarkOverrides() {
    if (!activeStudy) return;
    const statusEl = document.getElementById("poseStatus");
    if (statusEl) statusEl.textContent = "Saving manual landmark corrections...";
    try {
      const overrides = curLandmarks.filter((l) => l.is_manual_override);
      const res = await api(`/api/pose/studies/${encodeURIComponent(activeStudy.study_id)}/landmarks`, {
        method: "PUT",
        body: JSON.stringify({ landmarks: overrides }),
      });
      activeStudy = res.study;
      curLandmarks = (activeStudy.landmarks || []).map((lm) => ({ ...lm }));
      renderPoseSkeleton();
      renderActionInsights();
      if (statusEl) statusEl.textContent = "Manual landmark corrections saved successfully.";
    } catch (err) {
      if (statusEl) statusEl.textContent = `Save failed: ${err.message}`;
    }
  }

  async function savePoseObservation() {
    if (!activeStudy) return;
    const statusEl = document.getElementById("poseStatus");
    const zone = document.getElementById("poseSymptomZone").value;
    const pain = document.getElementById("posePainScore").value;
    const phase = document.getElementById("posePhaseSelect").value;
    const desc = document.getElementById("poseSymptomDesc").value;

    if (!zone.trim()) {
      alert("Please specify a reported symptom zone");
      return;
    }

    try {
      await api("/api/pose/observations", {
        method: "POST",
        body: JSON.stringify({
          study_id: activeStudy.study_id,
          case_id: activeCaseId,
          symptom_zone: zone.trim(),
          pain_score: pain ? parseInt(pain, 10) : null,
          movement_phase: phase,
          reported_symptoms: desc.trim(),
          functional_limitation: "Pose drill observation",
        }),
      });
      loadStudyObservations(activeStudy.study_id);
      if (statusEl) statusEl.textContent = "Symptom observation recorded.";
    } catch (err) {
      if (statusEl) statusEl.textContent = `Observation save failed: ${err.message}`;
    }
  }

  async function loadStudyObservations(studyId) {
    const listEl = document.getElementById("poseObservationList");
    if (!listEl) return;
    try {
      const obs = await api(`/api/pose/observations?study_id=${encodeURIComponent(studyId)}`);
      if (obs.length === 0) {
        listEl.innerHTML = "<small style='color:var(--text-muted);'>No symptom findings recorded for this pose.</small>";
      } else {
        listEl.innerHTML = obs
          .map(
            (o) => `
          <div style="background: rgba(30,41,59,0.5); padding:6px 10px; border-radius:4px; margin-bottom:4px; font-size:11px;">
            <div style="display:flex; justify-content:space-between;">
              <strong>${o.symptom_zone} (Pain: ${o.pain_score !== null ? o.pain_score : "N/A"}/10)</strong>
              <span style="color:var(--text-muted);">${o.movement_phase}</span>
            </div>
            <div>${o.reported_symptoms}</div>
          </div>
        `
          )
          .join("");
      }
    } catch (err) {
      console.error("Failed to load observations", err);
    }
  }

  function focusCandidateMusclesInAtlas() {
    // Switch to bodymap tab and trigger 3D Atlas focus
    const bodymapBtn = document.querySelector('.tab-btn[data-tab="tab-bodymap"]');
    if (bodymapBtn) bodymapBtn.click();
    // Post message to Atlas iframe if available
    const iframe = document.getElementById("atlasFrame");
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.postMessage({ type: "FOCUS_ANATOMY_REGION", region: "shoulder" }, "*");
    }
  }

  function renderEmptyCanvas() {
    const svg = document.getElementById("poseSvg");
    if (svg) svg.innerHTML = "<text x='120' y='250' fill='#94a3b8'>No pose loaded</text>";
  }

  window.addEventListener("DOMContentLoaded", initPoseExplorer);
})();
