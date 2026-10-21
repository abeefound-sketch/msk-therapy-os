from bs4 import BeautifulSoup

with open('msk_therapy_os/static/index.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

button_i18n_map = {
    'exportFhirBtn': 'case.btn_export_fhir',
    'btnNewObs': 'case.btn_new_obs',
    'btnDocSession': 'case.btn_doc_session',
    'btnSubmitSoapDraft': 'soap.btn_submit_draft',
    'btnSupervisorApprove': 'soap.btn_approve',
    'btnSupervisorReject': 'soap.btn_reject',
    'btnDownloadReport': 'report.btn_download',
    'btnCopyReport': 'report.btn_copy',
    'btnRunSafetyCheck': 'safety.btn_evaluate',
    'btnResetSafetyDrill': 'safety.btn_reset',
    'btnToggleVerified': 'common.verified',
    'btnToggleAcupoints': 'layers.points',
    'btnToggleMeridians': 'layers.meridians',
    'btnToggleThai': 'layers.thai',
    'btnToggleDienChan': 'layers.dien_chan'
}

count = 0
for b_id, key in button_i18n_map.items():
    btn = soup.find('button', id=b_id)
    if btn:
        btn['data-i18n'] = key
        count += 1
        print(f"Patched #{b_id} -> {key}")
    else:
        print(f"Button #{b_id} not found")

with open('msk_therapy_os/static/index.html', 'w', encoding='utf-8') as f:
    f.write(str(soup))

print(f"Patched {count} buttons by ID.")
