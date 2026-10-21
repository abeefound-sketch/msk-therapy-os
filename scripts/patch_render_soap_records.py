with open('msk_therapy_os/static/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''function renderSOAPRecords(soaps) {
      const container = document.getElementById("soapListArea");
      if (!soaps || soaps.length === 0) {
        container.innerHTML = "<p style='color:var(--text-muted)'>No structured SOAP notes recorded for this case yet.</p>";
        return;
      }
      container.innerHTML = soaps.map(s => {
        let statusBadge = `<span class="tag tag-safe">[APPROVED]</span>`;
        if (s.review_status === "DRAFT") statusBadge = `<span class="tag tag-trad">[DRAFT]</span>`;
        if (s.review_status === "REJECTED") statusBadge = `<span class="tag tag-stop">[REJECTED]</span>`;
        if (s.review_status === "SUPERVISED") statusBadge = `<span class="tag tag-evidence">[SUPERVISED]</span>`;

        let supervisorActions = "";
        if (activeRole === "reviewer" && s.review_status !== "APPROVED") {
          supervisorActions = `
            <div style="margin-top:10px; padding-top:10px; border-top:1px dashed var(--border); display:flex; gap:8px;">
              <input type="text" id="feedback-${s.id}" placeholder="Supervisor review comments..." style="flex:1;">
              <button onclick="approveSOAP(${s.id}, 'APPROVED')" style="background:var(--success); color:#000;">Approve</button>
              <button onclick="approveSOAP(${s.id}, 'REJECTED')" style="background:var(--danger); color:#fff;">Reject</button>
            </div>
          `;
        }'''

replacement = '''function renderSOAPRecords(soaps) {
      const container = document.getElementById("soapListArea");
      const t = window.__msk_i18n ? window.__msk_i18n.t : ((k, fb) => fb);
      if (!soaps || soaps.length === 0) {
        container.innerHTML = `<p style='color:var(--text-muted)'>${t('soap.no_records', 'No structured SOAP notes recorded for this case yet.')}</p>`;
        return;
      }
      container.innerHTML = soaps.map(s => {
        let statusBadge = `<span class="tag tag-safe">[${t('soap.status_approved', 'APPROVED')}]</span>`;
        if (s.review_status === "DRAFT") statusBadge = `<span class="tag tag-trad">[${t('soap.status_draft', 'DRAFT')}]</span>`;
        if (s.review_status === "REJECTED") statusBadge = `<span class="tag tag-stop">[${t('soap.status_revision', 'REJECTED')}]</span>`;
        if (s.review_status === "SUPERVISED") statusBadge = `<span class="tag tag-evidence">[${t('soap.status_supervised', 'SUPERVISED')}]</span>`;

        let supervisorActions = "";
        if (activeRole === "reviewer" && s.review_status !== "APPROVED") {
          supervisorActions = `
            <div style="margin-top:10px; padding-top:10px; border-top:1px dashed var(--border); display:flex; gap:8px;">
              <input type="text" id="feedback-${s.id}" placeholder="${t('soap.feedback_placeholder', 'Supervisor review comments...')}" style="flex:1;">
              <button onclick="approveSOAP(${s.id}, 'APPROVED')" style="background:var(--success); color:#000;">${t('soap.btn_approve', 'Approve')}</button>
              <button onclick="approveSOAP(${s.id}, 'REJECTED')" style="background:var(--danger); color:#fff;">${t('soap.btn_reject', 'Reject')}</button>
            </div>
          `;
        }'''

text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

assert target_norm in text_norm, "Target not found in index.html"
text_norm = text_norm.replace(target_norm, replacement_norm, 1)

with open('msk_therapy_os/static/index.html', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text_norm)

print("renderSOAPRecords patched successfully.")
