/**
 * M6 De-identified Synthetic Cohort Research Dashboard
 * Renders aggregate longitudinal analytics, PROM distributions,
 * CTCAE adverse event trends, missingness accounting, and research exports.
 */

const CohortDashboardModule = (() => {
  async function loadSummary() {
    const container = document.getElementById('cohortDashboardContent');
    if (!container) return;

    try {
      const res = await fetch('/api/cohort/summary');
      if (!res.ok) {
        container.innerHTML = `<div style="color:#ef4444; padding:16px;">Failed to load cohort analytics: HTTP ${res.status}</div>`;
        return;
      }
      const data = await res.json();
      renderDashboard(data, container);
    } catch (err) {
      console.error('[CohortDashboard] Load error:', err);
      container.innerHTML = `<div style="color:#ef4444; padding:16px;">Error loading cohort summary: ${err.message}</div>`;
    }
  }

  function renderDashboard(data, container) {
    const pain = data.pain_analytics || {};
    const rom = data.rom_analytics || {};
    const proms = data.prom_analytics || {};
    const ae = data.adverse_events_summary || {};
    const miss = data.missingness_report || {};

    let html = `
      <div style="background:rgba(239,68,68,0.1); border-left:4px solid #ef4444; padding:10px 14px; border-radius:4px; margin-bottom:16px; font-size:12px; line-height:1.4; color:#fca5a5;">
        <strong>⚠️ Clinical Governance & Non-Causal Analytics Disclaimer:</strong> ${data.disclaimer}
      </div>

      <!-- Top Metric Cards -->
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin-bottom:16px;">
        <div style="background:#1e293b; padding:12px; border-radius:6px; border:1px solid #334155;">
          <div style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Cohort Sample Size</div>
          <div style="font-size:24px; font-weight:700; color:#38bdf8; margin:4px 0;">${data.total_cases} <small style="font-size:12px; color:#94a3b8;">Cases</small></div>
          <div style="font-size:11px; color:#cbd5e1;">${data.total_visits} recorded visits</div>
        </div>

        <div style="background:#1e293b; padding:12px; border-radius:6px; border:1px solid #334155;">
          <div style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Mean Pain Reduction</div>
          <div style="font-size:24px; font-weight:700; color:#10b981; margin:4px 0;">
            ${pain.mean_delta !== null && pain.mean_delta !== undefined ? '+' + pain.mean_delta + ' pts' : 'N/A'}
          </div>
          <div style="font-size:11px; color:#cbd5e1;">
            ${pain.mean_percentage_reduction !== null ? pain.mean_percentage_reduction + '% reduction' : 'Baseline: ' + (pain.baseline_mean || 'N/A')}
          </div>
        </div>

        <div style="background:#1e293b; padding:12px; border-radius:6px; border:1px solid #334155;">
          <div style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Mean ROM Gain</div>
          <div style="font-size:24px; font-weight:700; color:#a855f7; margin:4px 0;">
            ${rom.mean_delta !== null && rom.mean_delta !== undefined ? '+' + rom.mean_delta + '°' : 'N/A'}
          </div>
          <div style="font-size:11px; color:#cbd5e1;">Evaluated in ${rom.cases_evaluated || 0} paired cases</div>
        </div>

        <div style="background:#1e293b; padding:12px; border-radius:6px; border:1px solid #334155;">
          <div style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Adverse Event Rate</div>
          <div style="font-size:24px; font-weight:700; color:#f59e0b; margin:4px 0;">
            ${ae.incident_rate_per_visit_pct !== undefined ? ae.incident_rate_per_visit_pct + '%' : '0%'}
          </div>
          <div style="font-size:11px; color:#cbd5e1;">${ae.total_events || 0} event(s) recorded</div>
        </div>

        <div style="background:#1e293b; padding:12px; border-radius:6px; border:1px solid #334155;">
          <div style="font-size:11px; color:#94a3b8; text-transform:uppercase;">Case Retention Rate</div>
          <div style="font-size:24px; font-weight:700; color:#ec4899; margin:4px 0;">
            ${miss.case_retention_rate_pct !== undefined ? miss.case_retention_rate_pct + '%' : 'N/A'}
          </div>
          <div style="font-size:11px; color:#cbd5e1;">${miss.cases_missing_followup || 0} case(s) missing follow-up</div>
        </div>
      </div>

      <!-- Detail Panels Grid -->
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-bottom:16px;">
        <!-- PROM Outcomes -->
        <div style="background:#1e293b; padding:14px; border-radius:6px; border:1px solid #334155;">
          <h4 style="color:#38bdf8; margin:0 0 10px 0; font-size:13px;">📋 Patient-Reported Outcome Measures (PROMs)</h4>
          <table style="width:100%; font-size:11px; border-collapse:collapse;">
            <thead>
              <tr style="border-bottom:1px solid #475569; color:#94a3b8; text-align:left;">
                <th style="padding:6px;">Instrument</th>
                <th style="padding:6px;">Administered</th>
                <th style="padding:6px;">Paired Followup</th>
                <th style="padding:6px;">Baseline Avg</th>
                <th style="padding:6px;">Followup Avg</th>
                <th style="padding:6px;">Avg Reduction</th>
              </tr>
            </thead>
            <tbody>
    `;

    for (const [name, meta] of Object.entries(proms)) {
      html += `
        <tr style="border-bottom:1px solid #334155;">
          <td style="padding:6px; font-weight:600; color:#e2e8f0;">${name}</td>
          <td style="padding:6px;">${meta.cases_administered}</td>
          <td style="padding:6px;">${meta.cases_paired_followup} (${meta.followup_completion_rate}%)</td>
          <td style="padding:6px;">${meta.baseline_mean_pct !== null ? meta.baseline_mean_pct + '%' : '-'}</td>
          <td style="padding:6px;">${meta.followup_mean_pct !== null ? meta.followup_mean_pct + '%' : '-'}</td>
          <td style="padding:6px; color:#10b981; font-weight:600;">${meta.mean_disability_reduction_pct !== null ? '-' + meta.mean_disability_reduction_pct + '%' : '-'}</td>
        </tr>
      `;
    }

    html += `
            </tbody>
          </table>
        </div>

        <!-- Adverse Events & Safety Drill Summary -->
        <div style="background:#1e293b; padding:14px; border-radius:6px; border:1px solid #334155;">
          <h4 style="color:#f59e0b; margin:0 0 10px 0; font-size:13px;">🛡️ CTCAE Adverse Events & Safety Quality Breakdown</h4>
          <div style="display:flex; gap:16px; margin-bottom:12px;">
            <div style="flex:1; background:#0f172a; padding:10px; border-radius:4px; border:1px solid #334155;">
              <strong style="font-size:11px; color:#94a3b8;">Grade Distribution:</strong>
              <div style="margin-top:6px; font-size:11px; line-height:1.6;">
                <div>Grade 1 (Mild): <strong style="color:#10b981;">${ae.grade_distribution ? ae.grade_distribution[1] : 0}</strong></div>
                <div>Grade 2 (Moderate): <strong style="color:#facc15;">${ae.grade_distribution ? ae.grade_distribution[2] : 0}</strong></div>
                <div>Grade 3 (Severe): <strong style="color:#f97316;">${ae.grade_distribution ? ae.grade_distribution[3] : 0}</strong></div>
                <div>Grade 4/5 (Critical): <strong style="color:#ef4444;">${(ae.grade_distribution ? ae.grade_distribution[4] + ae.grade_distribution[5] : 0)}</strong></div>
              </div>
            </div>
            <div style="flex:1; background:#0f172a; padding:10px; border-radius:4px; border:1px solid #334155;">
              <strong style="font-size:11px; color:#94a3b8;">Resolution Status:</strong>
              <div style="margin-top:6px; font-size:11px; line-height:1.6;">
                <div>Resolved: <strong style="color:#10b981;">${ae.resolution_distribution ? ae.resolution_distribution.resolved : 0}</strong></div>
                <div>Ongoing: <strong style="color:#f59e0b;">${ae.resolution_distribution ? ae.resolution_distribution.ongoing : 0}</strong></div>
                <div>Sequelae: <strong style="color:#ef4444;">${ae.resolution_distribution ? ae.resolution_distribution.sequelae : 0}</strong></div>
              </div>
            </div>
          </div>
          <div style="font-size:11px; color:#94a3b8;">
            ROM Documentation Rate: <strong style="color:#38bdf8;">${miss.rom_documentation_rate_pct || 0}%</strong> (${miss.visits_missing_rom || 0} visits missing ROM)
          </div>
        </div>
      </div>

      <!-- Export & Research Governance -->
      <div style="background:#1e293b; padding:14px; border-radius:6px; border:1px solid #334155; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <strong style="color:#e2e8f0; font-size:12px;">📥 De-identified Research Cohort Export (HIPAA / GDPR Safe)</strong>
          <div style="font-size:11px; color:#94a3b8; margin-top:2px;">
            Export pseudonymized records with hashed IDs (<span style="color:#38bdf8;">SYNTH-xxxxxxxxxx</span>), relative visit indices, and zero direct identifiers.
          </div>
        </div>
        <div style="display:flex; gap:8px;">
          <a href="/api/cohort/export?format=json" target="_blank" download="deidentified_cohort.json" class="btn-secondary" style="font-size:11px; padding:6px 12px; background:#0284c7; color:#fff; text-decoration:none; border-radius:4px; display:inline-flex; align-items:center; gap:4px;">
            ⬇ Export JSON
          </a>
          <a href="/api/cohort/export?format=csv" target="_blank" download="deidentified_cohort.csv" class="btn-secondary" style="font-size:11px; padding:6px 12px; background:#059669; color:#fff; text-decoration:none; border-radius:4px; display:inline-flex; align-items:center; gap:4px;">
            ⬇ Export CSV
          </a>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  return {
    loadSummary
  };
})();

window.CohortDashboardModule = CohortDashboardModule;
