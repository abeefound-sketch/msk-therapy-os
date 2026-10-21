from pathlib import Path

BASE = Path("D:/5Projects/msk-therapy-os")
index_path = BASE / "msk_therapy_os/static/index.html"
src = index_path.read_text(encoding="utf-8").replace("\r\n", "\n")

# 1. Add showToast() function and toast container style
old_script_start = """  <script>
    // State"""

new_script_start = """  <script>
    // Modern non-blocking clinical toast notification
    function showToast(msg, type = 'info') {
      let toast = document.getElementById('mskToast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'mskToast';
        toast.style.cssText = 'position:fixed; bottom:24px; right:24px; padding:10px 18px; border-radius:6px; box-shadow:0 10px 25px -5px rgba(0,0,0,0.6); z-index:99999; font-size:13px; font-weight:600; transition:opacity 0.3s ease; opacity:0; pointer-events:none;';
        document.body.appendChild(toast);
      }
      toast.textContent = msg;
      toast.style.background = type === 'error' ? '#7f1d1d' : (type === 'success' ? '#064e3b' : '#0f172a');
      toast.style.color = type === 'error' ? '#fecaca' : (type === 'success' ? '#a7f3d0' : '#f8fafc');
      toast.style.border = '1px solid ' + (type === 'error' ? '#ef4444' : (type === 'success' ? '#10b981' : '#38bdf8'));
      toast.style.opacity = '1';
      clearTimeout(toast._timeout);
      toast._timeout = setTimeout(() => { toast.style.opacity = '0'; }, 3200);
    }

    // State"""

if old_script_start in src:
    src = src.replace(old_script_start, new_script_start)
    print("Added showToast() helper.")

# 2. Add Reset Drill button to tab-safety
old_safety_btn = """            <button id="runSafetyCheckBtn" style="width:100%; margin-top:10px;">Evaluate Safety Gate</button>"""
new_safety_btn = """            <div style="display:flex; gap:8px; margin-top:10px;">
              <button id="runSafetyCheckBtn" style="flex:1;">Evaluate Safety Gate</button>
              <button id="resetSafetyCheckBtn" class="btn-secondary" style="padding:6px 14px;">Reset Drill</button>
            </div>"""

if old_safety_btn in src:
    src = src.replace(old_safety_btn, new_safety_btn)
    print("Added Reset Drill button to tab-safety.")

# 3. Add Tier filter & search input to tab-evidence
old_evidence_card = """    <!-- TAB 5: EVIDENCE CATALOG -->
    <section id="tab-evidence" class="tab-content" style="display:none;">
      <div class="card">
        <div class="card-title">
          <span>Vetted Clinical & Anatomical Evidence Catalog (Tiers 1–4)</span>
        </div>
        <div id="evidenceTableArea">Loading evidence...</div>
      </div>
    </section>"""

new_evidence_card = """    <!-- TAB 5: EVIDENCE CATALOG -->
    <section id="tab-evidence" class="tab-content" style="display:none;">
      <div class="card">
        <div class="card-title" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
          <span>Vetted Clinical & Anatomical Evidence Catalog (Tiers 1–4)</span>
          <div style="display:flex; gap:8px; align-items:center;">
            <select id="evidenceTierFilter" style="font-size:11px; padding:3px 6px; background:#1e293b; color:#e2e8f0; border:1px solid #475569; border-radius:4px;">
              <option value="all">All Tiers (1–4)</option>
              <option value="1">Tier 1: Clinical Guidelines</option>
              <option value="2">Tier 2: Peer-Reviewed Anatomy</option>
              <option value="3">Tier 3: Manufacturer Manuals</option>
              <option value="4">Tier 4: Traditional Schemas</option>
            </select>
            <input type="text" id="evidenceSearchInput" placeholder="Filter evidence by keyword..." style="font-size:11px; padding:3px 6px; background:#1e293b; color:#e2e8f0; border:1px solid #475569; border-radius:4px; width:180px;">
          </div>
        </div>
        <div id="evidenceTableArea">Loading evidence...</div>
      </div>
    </section>"""

if old_evidence_card in src:
    src = src.replace(old_evidence_card, new_evidence_card)
    print("Added Tier filter and Search box to tab-evidence.")

# 4. Add Download Markdown button to tab-report
old_report_card = """    <!-- TAB 6: OFFLINE REPORT -->
    <section id="tab-report" class="tab-content" style="display:none;">
      <div class="card">
        <div class="card-title">
          <span>Offline Clinical Learning Report</span>
          <button id="copyReportBtn" class="btn-secondary">Copy Markdown</button>
        </div>
        <pre id="reportPreArea">Generating report...</pre>
      </div>
    </section>"""

new_report_card = """    <!-- TAB 6: OFFLINE REPORT -->
    <section id="tab-report" class="tab-content" style="display:none;">
      <div class="card">
        <div class="card-title" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
          <span>Offline Clinical Learning Report</span>
          <div style="display:flex; gap:8px;">
            <button id="downloadReportBtn" class="btn-secondary" style="background:#0284c7; color:#fff; font-size:11px; padding:3px 10px;">📥 Download Markdown</button>
            <button id="copyReportBtn" class="btn-secondary" style="font-size:11px; padding:3px 10px;">📋 Copy Markdown</button>
          </div>
        </div>
        <pre id="reportPreArea">Generating report...</pre>
      </div>
    </section>"""

if old_report_card in src:
    src = src.replace(old_report_card, new_report_card)
    print("Added Download Markdown button to tab-report.")

# 5. Wire up the Reset Drill button and Download Report button in script
old_safety_listener = """    document.getElementById("runSafetyCheckBtn").addEventListener("click", async () => {"""

new_safety_listener = """    document.getElementById("resetSafetyCheckBtn").addEventListener("click", () => {
      document.getElementById("safetyFlag").value = "none";
      document.getElementById("safetyModality").value = "none";
      document.querySelectorAll("#contraindicationsList input:checked").forEach(cb => cb.checked = false);
      document.getElementById("safetyResultArea").innerHTML = `
        <div class="alert-box alert-info">
          Select safety parameters and click <strong>Evaluate Safety Gate</strong>.
        </div>`;
      showToast("Safety gate drill reset to clean baseline.", "info");
    });

    document.getElementById("runSafetyCheckBtn").addEventListener("click", async () => {"""

if old_safety_listener in src:
    src = src.replace(old_safety_listener, new_safety_listener)
    print("Wired resetSafetyCheckBtn click listener.")

old_copy_listener = """    document.getElementById("copyReportBtn").addEventListener("click", () => {
      const text = document.getElementById("reportPreArea").textContent;
      navigator.clipboard.writeText(text);
      alert("Report copied to clipboard!");
    });"""

new_copy_listener = """    document.getElementById("downloadReportBtn").addEventListener("click", () => {
      const text = document.getElementById("reportPreArea").textContent;
      const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `MSK_Report_${activeCaseId}.md`;
      a.click();
      showToast("Report downloaded successfully!", "success");
    });

    document.getElementById("copyReportBtn").addEventListener("click", () => {
      const text = document.getElementById("reportPreArea").textContent;
      navigator.clipboard.writeText(text);
      showToast("Report copied to clipboard!", "success");
    });"""

if old_copy_listener in src:
    src = src.replace(old_copy_listener, new_copy_listener)
    print("Wired downloadReportBtn and updated copyReportBtn.")

# 6. Replace alert() with showToast() across clinical forms
src = src.replace('alert(`Added "${lastSelectedStructure.name}" to SOAP Objective note.`);', 'showToast(`Added "${lastSelectedStructure.name}" to SOAP Objective note.`, "success");')
src = src.replace('alert(`Added acupoint "${lastSelectedAcupoint.code}" to SOAP Objective note.`);', 'showToast(`Added acupoint "${lastSelectedAcupoint.code}" to SOAP Objective note.`, "success");')
src = src.replace('alert("Observation recorded successfully!");', 'showToast("Observation recorded successfully!", "success");')
src = src.replace('alert("Session documented successfully!");', 'showToast("Session documented successfully!", "success");')
src = src.replace('alert("SOAP Note submitted for clinical supervision!");', 'showToast("SOAP Note submitted for clinical supervision!", "success");')
src = src.replace('alert(`Visit recorded! Disposition: ${out.disposition}`);', 'showToast(`Visit recorded! Disposition: ${out.disposition}`, out.disposition === "STOP_AND_REFER" ? "error" : "success");')
src = src.replace('if (out.error) alert(`Error: ${out.error}`);', 'if (out.error) showToast(`Error: ${out.error}`, "error");')

# 7. Update loadEvidence() to support tier and keyword filtering
old_load_ev = """    // Evidence
    async function loadEvidence() {
      const area = document.getElementById("evidenceTableArea");
      area.innerHTML = "Loading evidence catalog...";
      try {
        const res = await fetch("/api/evidence");
        const list = await res.json();
        area.innerHTML = `
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Tier</th>
                <th>Title & Organization</th>
                <th>Scope</th>
                <th>Reviewer</th>
              </tr>
            </thead>
            <tbody>
              ${list.map(e => `
                <tr>
                  <td><strong>${e.evidence_id}</strong></td>
                  <td><span class="tag tag-evidence">Tier ${e.tier}</span></td>
                  <td>
                    <div><strong>${e.title}</strong></div>
                    <small style="color:var(--text-muted)">${e.organization} (${e.year}) | License: ${e.license}</small>
                  </td>
                  <td><small>${e.claim_scope}</small></td>
                  <td><small>${e.reviewer} (${e.reviewed_on})</small></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        `;
      } catch (err) {
        area.innerHTML = `<div class="alert-box alert-danger">Error: ${err}</div>`;
      }
    }"""

new_load_ev = """    // Evidence catalog with reactive filtering
    let cachedEvidenceList = [];
    async function loadEvidence() {
      const area = document.getElementById("evidenceTableArea");
      area.innerHTML = "Loading evidence catalog...";
      try {
        const res = await fetch("/api/evidence");
        cachedEvidenceList = await res.json();
        renderEvidenceTable();
      } catch (err) {
        area.innerHTML = `<div class="alert-box alert-danger">Error: ${err}</div>`;
      }
    }

    function renderEvidenceTable() {
      const area = document.getElementById("evidenceTableArea");
      const tierFilter = document.getElementById("evidenceTierFilter") ? document.getElementById("evidenceTierFilter").value : "all";
      const searchQuery = document.getElementById("evidenceSearchInput") ? document.getElementById("evidenceSearchInput").value.trim().toLowerCase() : "";

      const filtered = cachedEvidenceList.filter(e => {
        if (tierFilter !== "all" && String(e.tier) !== tierFilter) return false;
        if (searchQuery) {
          const matchTitle = (e.title || "").toLowerCase().includes(searchQuery);
          const matchOrg = (e.organization || "").toLowerCase().includes(searchQuery);
          const matchScope = (e.claim_scope || "").toLowerCase().includes(searchQuery);
          const matchId = (e.evidence_id || "").toLowerCase().includes(searchQuery);
          if (!matchTitle && !matchOrg && !matchScope && !matchId) return false;
        }
        return true;
      });

      if (filtered.length === 0) {
        area.innerHTML = '<p style="color:var(--text-muted); padding:12px;">No evidence citations match the current filter.</p>';
        return;
      }

      area.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Tier</th>
              <th>Title & Organization</th>
              <th>Scope</th>
              <th>Reviewer</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.map(e => `
              <tr class="evidence-card">
                <td><strong>${e.evidence_id}</strong></td>
                <td><span class="tag tag-evidence">Tier ${e.tier}</span></td>
                <td>
                  <div><strong>${e.title}</strong></div>
                  <small style="color:var(--text-muted)">${e.organization} (${e.year}) | License: ${e.license}</small>
                </td>
                <td><small>${e.claim_scope}</small></td>
                <td><small>${e.reviewer} (${e.reviewed_on})</small></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    document.getElementById("evidenceTierFilter").addEventListener("change", renderEvidenceTable);
    document.getElementById("evidenceSearchInput").addEventListener("input", renderEvidenceTable);"""

if old_load_ev in src:
    src = src.replace(old_load_ev, new_load_ev)
    print("Updated loadEvidence() with reactive filtering.")

index_path.write_text(src, encoding="utf-8")
print("Successfully patched msk_therapy_os/static/index.html!")
