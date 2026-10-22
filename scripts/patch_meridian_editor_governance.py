from pathlib import Path

EDITOR_FILE = Path("msk_therapy_os/static/meridianEditor.js")
content = EDITOR_FILE.read_text(encoding="utf-8")

# 1. Add ANATOMY_REVIEWED option to select
old_options = """                      <option value="VERIFIED_ANATOMICAL_ANCHOR">VERIFIED_ANATOMICAL_ANCHOR</option>
                      <option value="SURFACE_REGISTERED_FJ2810">SURFACE_REGISTERED_FJ2810</option>
                      <option value="GEOMETRY_VERIFIED">GEOMETRY_VERIFIED</option>
                      <option value="UNCERTAIN_POSTURE_OFFSET">UNCERTAIN_POSTURE_OFFSET</option>
                      <option value="UNVERIFIED">UNVERIFIED</option>"""

new_options = """                      <option value="VERIFIED_ANATOMICAL_ANCHOR">VERIFIED_ANATOMICAL_ANCHOR</option>
                      <option value="SURFACE_REGISTERED_FJ2810">SURFACE_REGISTERED_FJ2810</option>
                      <option value="GEOMETRY_VERIFIED">GEOMETRY_VERIFIED</option>
                      <option value="ANATOMY_REVIEWED">ANATOMY_REVIEWED (Human Review)</option>
                      <option value="UNCERTAIN_POSTURE_OFFSET">UNCERTAIN_POSTURE_OFFSET</option>
                      <option value="UNVERIFIED">UNVERIFIED</option>"""

assert old_options in content, "old_options not found"
content = content.replace(old_options, new_options, 1)

# 2. Add Reviewer & Evidence ID inputs in modal
old_notes_div = """                <div>
                  <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Verification / Clinical Notes:</label>
                  <textarea id="studioNotes" rows="2" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px; resize: vertical;"></textarea>
                </div>"""

new_notes_div = """                <div>
                  <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Verification / Clinical Notes:</label>
                  <textarea id="studioNotes" rows="2" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 11px; resize: vertical;"></textarea>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
                  <div>
                    <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Reviewer (Human):</label>
                    <input type="text" id="studioReviewer" placeholder="e.g. Dr. Jane Smith, MD / LAc" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 10px;" />
                  </div>
                  <div>
                    <label style="font-size: 10px; color: #9ca3af; display: block; margin-bottom: 1px;">Evidence Reference:</label>
                    <input type="text" id="studioEvidenceId" placeholder="e.g. EVID-A-002" style="width: 100%; background: #111827; color: #f3f4f6; border: 1px solid #4b5563; padding: 4px 6px; border-radius: 4px; font-size: 10px;" />
                  </div>
                </div>"""

assert old_notes_div in content, "old_notes_div not found"
content = content.replace(old_notes_div, new_notes_div, 1)

# 3. Add badge for ANATOMY_REVIEWED
old_badge = """    if (pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR') {
      badgeContainer.innerHTML += '<span style="background:#065f46; color:#a7f3d0; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">✓ ANCHOR</span>';
    } else if (pt.registration_status === 'GEOMETRY_VERIFIED') {"""

new_badge = """    if (pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR') {
      badgeContainer.innerHTML += '<span style="background:#065f46; color:#a7f3d0; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">✓ ANCHOR</span>';
    } else if (pt.registration_status === 'ANATOMY_REVIEWED') {
      badgeContainer.innerHTML += '<span style="background:#047857; color:#d1fae5; padding:2px 6px; border-radius:4px; font-weight:600; font-size:10px;">✓ ANATOMY REVIEWED</span>';
    } else if (pt.registration_status === 'GEOMETRY_VERIFIED') {"""

assert old_badge in content, "old_badge not found"
content = content.replace(old_badge, new_badge, 1)

# 4. Populate reviewer and evidence in loadPointIntoEditor
old_populate = """    document.getElementById('studioNotes').value = pt.verification_notes || pt.notes || '';"""
new_populate = """    document.getElementById('studioNotes').value = pt.verification_notes || pt.notes || '';
    const elRev = document.getElementById('studioReviewer');
    if (elRev) elRev.value = pt.reviewer || '';
    const elEvid = document.getElementById('studioEvidenceId');
    if (elEvid) elEvid.value = pt.evidence_id || '';"""

assert old_populate in content, "old_populate not found"
content = content.replace(old_populate, new_populate, 1)

# 5. Send reviewer and evidence in saveCurrentPoint
old_save_body = """            position: pt.position,
            normal: pt.normal,
            registration_status: pt.registration_status,
            review_status: pt.review_status,
            notes: pt.verification_notes,
            change_type: 'UPDATE_COORDS'"""

new_save_body = """            position: pt.position,
            normal: pt.normal,
            registration_status: pt.registration_status,
            review_status: pt.review_status,
            notes: pt.verification_notes,
            reviewer: (document.getElementById('studioReviewer') ? document.getElementById('studioReviewer').value.trim() : null),
            evidence_id: (document.getElementById('studioEvidenceId') ? document.getElementById('studioEvidenceId').value.trim() : null),
            change_type: 'UPDATE_COORDS'"""

assert old_save_body in content, "old_save_body not found"
content = content.replace(old_save_body, new_save_body, 1)

# 6. Override save body
old_ov_body = """            position: pt.position,
            normal: pt.normal,
            registration_status: pt.registration_status,
            review_status: pt.review_status,
            notes: pt.verification_notes"""

new_ov_body = """            position: pt.position,
            normal: pt.normal,
            registration_status: pt.registration_status,
            review_status: pt.review_status,
            notes: pt.verification_notes,
            reviewer: (document.getElementById('studioReviewer') ? document.getElementById('studioReviewer').value.trim() : null),
            evidence_id: (document.getElementById('studioEvidenceId') ? document.getElementById('studioEvidenceId').value.trim() : null)"""

assert old_ov_body in content, "old_ov_body not found"
content = content.replace(old_ov_body, new_ov_body, 1)

EDITOR_FILE.write_text(content, encoding="utf-8")
print("Successfully patched meridianEditor.js with governance UI!")
