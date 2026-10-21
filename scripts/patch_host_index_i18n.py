import re

with open('msk_therapy_os/static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add script tag in head
if '<script src="/i18n.js"></script>' not in html:
    html = html.replace('</head>', '  <script src="/i18n.js"></script>\n</head>')

# 2. Add CSS for language switcher
lang_css = '''
    /* Language Switcher Styling */
    .lang-switcher {
      display: inline-flex;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 2px;
      gap: 2px;
    }
    .lang-btn {
      background: transparent;
      color: var(--text-muted);
      border: none;
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .lang-btn:hover {
      color: var(--text);
      background: var(--surface-hover);
    }
    .lang-btn.active {
      background: var(--primary);
      color: #0f172a;
      font-weight: 700;
    }
'''
if '.lang-switcher {' not in html:
    html = html.replace('</style>', f'{lang_css}\n</style>')

# 3. Add Language Switcher into header-controls
header_controls_target = '<div class="header-controls">'
lang_switcher_html = '''<div class="header-controls">
      <!-- Multilingual Language Selector (EN / 中文 / Tiếng Việt) -->
      <div class="lang-switcher" role="group" aria-label="Language Selector">
        <button type="button" class="lang-btn active" data-lang="en">EN</button>
        <button type="button" class="lang-btn" data-lang="zh">中文（简体）</button>
        <button type="button" class="lang-btn" data-lang="vi">Tiếng Việt</button>
      </div>'''

if 'class="lang-switcher"' not in html:
    html = html.replace(header_controls_target, lang_switcher_html, 1)

# 4. Add data-i18n to Header & Nav Tabs
replacements = [
    ('<label for="caseSelect" style="color:var(--text-muted); font-size:12px;">Active Demo Case:</label>', '<label for="caseSelect" style="color:var(--text-muted); font-size:12px;" data-i18n="app.active_case">Active Demo Case:</label>'),
    ('<label for="roleSelect" style="color:var(--text-muted); font-size:12px;">Operator Role:</label>', '<label for="roleSelect" style="color:var(--text-muted); font-size:12px;" data-i18n="app.operator_role">Operator Role:</label>'),
    ('<option value="student">Student (Drafting)</option>', '<option value="student" data-i18n="app.role_student">Student (Drafting)</option>'),
    ('<option value="reviewer">Clinical Supervisor (Reviewer)</option>', '<option value="reviewer" data-i18n="app.role_supervisor">Clinical Supervisor (Reviewer)</option>'),
    ('<button id="refreshBtn" class="btn-secondary">↻ Refresh</button>', '<button id="refreshBtn" class="btn-secondary" data-i18n="app.btn_refresh">↻ Refresh</button>'),
    # Nav tabs
    ('<button class="tab-btn active" data-tab="tab-bodymap">Interactive Body-Map & Anatomy</button>', '<button class="tab-btn active" data-tab="tab-bodymap" data-i18n="nav.bodymap">Interactive Body-Map & Anatomy</button>'),
    ('<button class="tab-btn" data-tab="tab-safety">Safety & Red Flags Gating Drill</button>', '<button class="tab-btn" data-tab="tab-safety" data-i18n="nav.safety">Safety & Red Flags Gating Drill</button>'),
    ('<button class="tab-btn" data-tab="tab-case">Longitudinal Tracking & Timeline</button>', '<button class="tab-btn" data-tab="tab-case" data-i18n="nav.case">Longitudinal Tracking & Timeline</button>'),
    ('<button class="tab-btn" data-tab="tab-soap">Structured SOAP & Supervision</button>', '<button class="tab-btn" data-tab="tab-soap" data-i18n="nav.soap">Structured SOAP & Supervision</button>'),
    ('<button class="tab-btn" data-tab="tab-evidence">Curated Evidence Catalog</button>', '<button class="tab-btn" data-tab="tab-evidence" data-i18n="nav.evidence">Curated Evidence Catalog</button>'),
    ('<button class="tab-btn" data-tab="tab-report">Offline Markdown Report</button>', '<button class="tab-btn" data-tab="tab-report" data-i18n="nav.report">Offline Markdown Report</button>'),
    # Modes
    ('<button id="hostBtnModeSurface" class="btn-mode active" onclick="setHostRenderMode(\'surface\')" style="font-size:11px; padding:3px 8px; background:#0f766e; color:#fff; border:none; border-radius:3px; cursor:pointer;" title="Surface Meridian Mode: Skin mesh with surface-anchored points">🌐 Surface</button>', '<button id="hostBtnModeSurface" class="btn-mode active" onclick="setHostRenderMode(\'surface\')" style="font-size:11px; padding:3px 8px; background:#0f766e; color:#fff; border:none; border-radius:3px; cursor:pointer;" title="Surface Meridian Mode: Skin mesh with surface-anchored points" data-i18n="modes.surface" data-i18n-title="modes.surface_title">🌐 Surface</button>'),
    ('<button id="hostBtnModeMusculo" class="btn-mode" onclick="setHostRenderMode(\'musculoskeletal\')" style="font-size:11px; padding:3px 8px; background:transparent; color:#94a3b8; border:none; border-radius:3px; cursor:pointer;" title="Musculoskeletal Anatomy Mode: Deep bones, muscles, joints">🦴 Anatomy</button>', '<button id="hostBtnModeMusculo" class="btn-mode" onclick="setHostRenderMode(\'musculoskeletal\')" style="font-size:11px; padding:3px 8px; background:transparent; color:#94a3b8; border:none; border-radius:3px; cursor:pointer;" title="Musculoskeletal Anatomy Mode: Deep bones, muscles, joints" data-i18n="modes.musculoskeletal" data-i18n-title="modes.musculoskeletal_title">🦴 Anatomy</button>'),
    ('<button id="hostBtnModeComparative" class="btn-mode" onclick="setHostRenderMode(\'comparative\')" style="font-size:11px; padding:3px 8px; background:transparent; color:#94a3b8; border:none; border-radius:3px; cursor:pointer;" title="Comparative Research Mode: Synchronized dual split-view">⚖ Compare</button>', '<button id="hostBtnModeComparative" class="btn-mode" onclick="setHostRenderMode(\'comparative\')" style="font-size:11px; padding:3px 8px; background:transparent; color:#94a3b8; border:none; border-radius:3px; cursor:pointer;" title="Comparative Research Mode: Synchronized dual split-view" data-i18n="modes.comparative" data-i18n-title="modes.comparative_title">⚖ Compare</button>'),
    # Camera Presets
    ('<button class="btn-secondary" onclick="atlasCommand(\'set_view\', {preset:\'front\'})" style="font-size:11px; padding:3px 7px;">Front</button>', '<button class="btn-secondary" onclick="atlasCommand(\'set_view\', {preset:\'front\'})" style="font-size:11px; padding:3px 7px;" data-i18n="camera.front" data-i18n-title="camera.front_title">Front</button>'),
    ('<button class="btn-secondary" onclick="atlasCommand(\'set_view\', {preset:\'back\'})" style="font-size:11px; padding:3px 7px;">Back</button>', '<button class="btn-secondary" onclick="atlasCommand(\'set_view\', {preset:\'back\'})" style="font-size:11px; padding:3px 7px;" data-i18n="camera.back" data-i18n-title="camera.back_title">Back</button>'),
    ('<button class="btn-secondary" onclick="atlasCommand(\'set_view\', {preset:\'left\'})" style="font-size:11px; padding:3px 7px;">Left</button>', '<button class="btn-secondary" onclick="atlasCommand(\'set_view\', {preset:\'left\'})" style="font-size:11px; padding:3px 7px;" data-i18n="camera.left" data-i18n-title="camera.left_title">Left</button>'),
    ('<button class="btn-secondary" onclick="atlasCommand(\'set_view\', {preset:\'right\'})" style="font-size:11px; padding:3px 7px;">Right</button>', '<button class="btn-secondary" onclick="atlasCommand(\'set_view\', {preset:\'right\'})" style="font-size:11px; padding:3px 7px;" data-i18n="camera.right" data-i18n-title="camera.right_title">Right</button>'),
    ('<button class="btn-secondary" onclick="atlasCommand(\'full_body_view\')" style="font-size:11px; padding:3px 7px;" title="Full body view (Home)">Full Body</button>', '<button class="btn-secondary" onclick="atlasCommand(\'full_body_view\')" style="font-size:11px; padding:3px 7px;" title="Full body view (Home)" data-i18n="camera.full_body" data-i18n-title="camera.full_body_title">Full Body</button>'),
    ('<button class="btn-secondary" onclick="atlasCommand(\'focus_selection\')" style="font-size:11px; padding:3px 7px;" title="Focus camera on selected structure or acupoint (F)">Focus</button>', '<button class="btn-secondary" onclick="atlasCommand(\'focus_selection\')" style="font-size:11px; padding:3px 7px;" title="Focus camera on selected structure or acupoint (F)" data-i18n="camera.focus" data-i18n-title="camera.focus_title">Focus</button>'),
    ('<button class="btn-secondary" onclick="atlasCommand(\'reset_view\')" style="font-size:11px; padding:3px 7px;">Reset</button>', '<button class="btn-secondary" onclick="atlasCommand(\'reset_view\')" style="font-size:11px; padding:3px 7px;" data-i18n="camera.reset" data-i18n-title="camera.reset_title">Reset</button>'),
    ('<button class="btn-secondary" onclick="atlasCommand(\'set_xray\')" style="font-size:11px; padding:3px 7px;">X-Ray</button>', '<button class="btn-secondary" onclick="atlasCommand(\'set_xray\')" style="font-size:11px; padding:3px 7px;" data-i18n="camera.xray" data-i18n-title="camera.xray_title">X-Ray</button>'),
    # Regions
    ('<button class="btn-secondary region-btn active" data-region="neck" style="font-size:11px; padding:3px 10px;">Neck</button>', '<button class="btn-secondary region-btn active" data-region="neck" style="font-size:11px; padding:3px 10px;" data-i18n="regions.neck">Neck</button>'),
    ('<button class="btn-secondary region-btn" data-region="shoulder" style="font-size:11px; padding:3px 10px;">Shoulder</button>', '<button class="btn-secondary region-btn" data-region="shoulder" style="font-size:11px; padding:3px 10px;" data-i18n="regions.shoulder">Shoulder</button>'),
    ('<button class="btn-secondary region-btn" data-region="thoracic" style="font-size:11px; padding:3px 10px;">Thoracic</button>', '<button class="btn-secondary region-btn" data-region="thoracic" style="font-size:11px; padding:3px 10px;" data-i18n="regions.thoracic">Thoracic</button>'),
    ('<button class="btn-secondary region-btn" data-region="low_back" style="font-size:11px; padding:3px 10px;">Low Back</button>', '<button class="btn-secondary region-btn" data-region="low_back" style="font-size:11px; padding:3px 10px;" data-i18n="regions.low_back">Low Back</button>'),
    ('<button class="btn-secondary region-btn" data-region="hip" style="font-size:11px; padding:3px 10px;">Hip / Pelvis</button>', '<button class="btn-secondary region-btn" data-region="hip" style="font-size:11px; padding:3px 10px;" data-i18n="regions.hip">Hip / Pelvis</button>'),
    ('<button class="btn-secondary region-btn" data-region="arm" style="font-size:11px; padding:3px 10px;">Arm / Hand</button>', '<button class="btn-secondary region-btn" data-region="arm" style="font-size:11px; padding:3px 10px;" data-i18n="regions.arm">Arm / Hand</button>'),
    ('<button class="btn-secondary region-btn" data-region="leg" style="font-size:11px; padding:3px 10px;">Leg / Foot</button>', '<button class="btn-secondary region-btn" data-region="leg" style="font-size:11px; padding:3px 10px;" data-i18n="regions.leg">Leg / Foot</button>'),
    ('<button class="btn-secondary region-btn" data-region="face" style="font-size:11px; padding:3px 10px;">Face</button>', '<button class="btn-secondary region-btn" data-region="face" style="font-size:11px; padding:3px 10px;" data-i18n="regions.face">Face</button>'),
    ('<button class="btn-secondary region-btn" data-region="all" style="font-size:11px; padding:3px 10px;">Full Body</button>', '<button class="btn-secondary region-btn" data-region="all" style="font-size:11px; padding:3px 10px;" data-i18n="regions.all">Full Body</button>'),
    # Case tab buttons
    ('<button id="exportFhirBtn" class="btn-secondary" style="font-size:11px; padding:4px 10px;">📤 Export HL7 FHIR R4</button>', '<button id="exportFhirBtn" class="btn-secondary" style="font-size:11px; padding:4px 10px;" data-i18n="case.btn_export_fhir">📤 Export HL7 FHIR R4</button>'),
    ('<button id="btnNewObs" onclick="toggleObservationForm()" style="font-size:11px; padding:4px 10px; background:#0f766e; color:#fff;">+ Record New Observation</button>', '<button id="btnNewObs" onclick="toggleObservationForm()" style="font-size:11px; padding:4px 10px; background:#0f766e; color:#fff;" data-i18n="case.btn_new_obs">+ Record New Observation</button>'),
    ('<button id="btnDocSession" onclick="toggleSessionForm()" style="font-size:11px; padding:4px 10px; background:#0284c7; color:#fff;">+ Document Session</button>', '<button id="btnDocSession" onclick="toggleSessionForm()" style="font-size:11px; padding:4px 10px; background:#0284c7; color:#fff;" data-i18n="case.btn_doc_session">+ Document Session</button>'),
    # SOAP tab buttons
    ('<button id="btnSubmitSoapDraft" onclick="submitSoapDraft()" style="background:#0284c7; color:#fff; padding:6px 14px; font-weight:600;">Submit SOAP Draft for Supervision</button>', '<button id="btnSubmitSoapDraft" onclick="submitSoapDraft()" style="background:#0284c7; color:#fff; padding:6px 14px; font-weight:600;" data-i18n="soap.btn_submit_draft">Submit SOAP Draft for Supervision</button>'),
    ('<button id="btnSupervisorApprove" onclick="approveSoap()" style="background:#065f46; color:#a7f3d0; border:1px solid #10b981; padding:6px 14px; font-weight:700;">✓ Approve SOAP Note</button>', '<button id="btnSupervisorApprove" onclick="approveSoap()" style="background:#065f46; color:#a7f3d0; border:1px solid #10b981; padding:6px 14px; font-weight:700;" data-i18n="soap.btn_approve">✓ Approve SOAP Note</button>'),
    ('<button id="btnSupervisorReject" onclick="rejectSoap()" style="background:#7f1d1d; color:#fecaca; border:1px solid #ef4444; padding:6px 14px; font-weight:700;">✕ Request Revisions</button>', '<button id="btnSupervisorReject" onclick="rejectSoap()" style="background:#7f1d1d; color:#fecaca; border:1px solid #ef4444; padding:6px 14px; font-weight:700;" data-i18n="soap.btn_reject">✕ Request Revisions</button>'),
    # Report tab buttons
    ('<button id="btnDownloadReport" onclick="downloadReport()" style="background:#0284c7; color:#fff; padding:6px 14px;">📥 Download Markdown</button>', '<button id="btnDownloadReport" onclick="downloadReport()" style="background:#0284c7; color:#fff; padding:6px 14px;" data-i18n="report.btn_download">📥 Download Markdown</button>'),
    ('<button id="btnCopyReport" onclick="copyReport()" class="btn-secondary" style="padding:6px 14px;">📋 Copy Markdown</button>', '<button id="btnCopyReport" onclick="copyReport()" class="btn-secondary" style="padding:6px 14px;" data-i18n="report.btn_copy">📋 Copy Markdown</button>'),
    # Safety drill buttons
    ('<button id="btnRunSafetyCheck" onclick="runSafetyCheck()" style="background:#dc2626; color:#fff; padding:8px 16px; font-weight:700;">Evaluate Safety Gate</button>', '<button id="btnRunSafetyCheck" onclick="runSafetyCheck()" style="background:#dc2626; color:#fff; padding:8px 16px; font-weight:700;" data-i18n="safety.btn_evaluate">Evaluate Safety Gate</button>'),
    ('<button id="btnResetSafetyDrill" onclick="resetSafetyDrill()" class="btn-secondary" style="padding:8px 16px;">Reset Safety Drill</button>', '<button id="btnResetSafetyDrill" onclick="resetSafetyDrill()" class="btn-secondary" style="padding:8px 16px;" data-i18n="safety.btn_reset">Reset Safety Drill</button>')
]

for old, new in replacements:
    if old in html:
        html = html.replace(old, new)
    else:
        print(f"Warning: pattern not matched in index.html: {old[:50]}")

with open('msk_therapy_os/static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("index.html patched with language switcher, CSS and data-i18n attributes.")
