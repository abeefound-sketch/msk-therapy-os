# P9.8 Meridian Route QA Studio Dynamic Metrics Audit

**Document ID:** `P98_QA_STUDIO_DYNAMIC_METRICS_AUDIT.md`  
**Milestone:** P9.8 Anatomical Ground Truth & Evidence Integrity Hardening  
**Status:** APPROVED | ZERO HARDCODED FALLBACK COUNTS  
**Date:** 2026-10-28  

---

## 1. Problem Statement: Hardcoded Frontend Display Literals

In prior milestones (P9.4 through P9.7), `msk_therapy_os/static/atlas/meridians.js` contained hardcoded numerical counts in both the initial DOM template and the catch block of `loadStudioCoverage()`:
- `lblCovClassA` initialized to `"18"`
- `lblCovClassB` initialized to `"122"` (or `"102"`, `"52"`)
- `lblCovClassD` initialized to `"222"` (or `"242"`, `"292"`)
- `lblCovVerifiedPct` initialized to `"38.7% (5.0% Audited)"`

If the backend API `/api/atlas/meridians/coverage` failed to load, was unreachable, or if points were updated dynamically, the UI continued to display outdated or fabricated numbers instead of truthfully reporting that live data was unavailable.

---

## 2. Remediation in P9.8

### Remediation A: Neutral Placeholder HTML Initialization
In `msk_therapy_os/static/atlas/meridians.js` (lines 2516–2528):
```html
<strong id="lblCovClassA" style="color:#10b981; font-size:11px;">--</strong>
<strong id="lblCovClassB" style="color:#38bdf8; font-size:11px;">--</strong>
<strong id="lblCovClassD" style="color:#f59e0b; font-size:11px;">--</strong>
<span>Verified: <strong id="lblCovVerifiedPct" style="color:#34d399;">--%</strong> (--% Audited)</span>
```
All initial values are set to neutral `--` placeholders.

### Remediation B: Live Dynamic API Binding
In `loadStudioCoverage()` (lines 3044–3070):
```javascript
async function loadStudioCoverage() {
  try {
    const res = await fetch('/api/atlas/meridians/coverage');
    const elA = document.getElementById('lblCovClassA');
    const elB = document.getElementById('lblCovClassB');
    const elD = document.getElementById('lblCovClassD');
    const elPct = document.getElementById('lblCovVerifiedPct');

    if (!res.ok) {
      if (elA) elA.textContent = '--';
      if (elB) elB.textContent = '--';
      if (elD) elD.textContent = '--';
      if (elPct) elPct.textContent = 'UNAVAILABLE';
      return;
    }
    const data = await res.json();
    const dist = data.class_distribution || {};
    if (elA) elA.textContent = (dist.CLASS_A !== undefined) ? dist.CLASS_A : '--';
    if (elB) elB.textContent = (dist.CLASS_B !== undefined) ? dist.CLASS_B : '--';
    if (elD) elD.textContent = (dist.CLASS_D !== undefined) ? dist.CLASS_D : '--';
    if (elPct) {
      if (data.verified_percentage !== undefined) {
        elPct.textContent = `${data.verified_percentage}% (${data.independently_verified_percentage ?? 0.0}% Audited)`;
      } else {
        elPct.textContent = 'UNAVAILABLE';
      }
    }
  } catch (err) {
    console.warn('Failed to load meridian studio coverage:', err);
    // Preserves neutral state without inventing counts
    if (elA) elA.textContent = '--';
    if (elB) elB.textContent = '--';
    if (elD) elD.textContent = '--';
    if (elPct) elPct.textContent = 'UNAVAILABLE';
  }
}
```

### Remediation C: Automatic Initialization & Exposed Debug Namespace
1. `loadStudioCoverage()` is invoked immediately when the Meridian module loads.
2. `window.__meridianStudio = { loadCoverage: loadStudioCoverage, loadTopology: loadStudioTopology }` is exposed on `window` for automated test orchestration.

---

## 3. Independent Verification

Automated test `tests/test_p9_8_integrity_hardening.py::TestP98QAStudioDynamicMetrics::test_meridians_js_no_hardcoded_fallback_counts` inspects `meridians.js` and asserts:
1. No occurrences of hardcoded fallback strings `"122"`, `"222"`, `"102"`, `"242"`, or `"38.7%"` in the coverage rendering logic.
2. The initial text content of `lblCovClassA`, `lblCovClassB`, `lblCovClassD` is `--`.
3. Error handler explicitly emits `UNAVAILABLE`.
