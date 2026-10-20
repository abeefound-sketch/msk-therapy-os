import re
from pathlib import Path

index_path = Path("D:/5Projects/msk-therapy-os/msk_therapy_os/static/index.html")
text = index_path.read_text(encoding="utf-8")

# 1. Add Studio button to toolbar
old_toggles = '<button id="btnToggleDienChan" class="btn-secondary" onclick="toggleAtlasLayer(\'dien_chan\')" style="font-size:11px; padding:3px 8px;">🇻🇳 Dien Chan Reflex</button>'
new_toggles = old_toggles + '\n            <button id="btnOpenStudioEditor" class="btn-secondary" onclick="openStudioEditorModal()" style="font-size:11px; padding:3px 8px; background:#4338ca; color:#e0e7ff; border-color:#6366f1;">🛠️ Meridian Studio</button>'
assert old_toggles in text, 'old_toggles not found'
text = text.replace(old_toggles, new_toggles, 1)

# 2. Add Arm, Leg, All region buttons
old_regions = '<button class="btn-secondary region-btn" data-region="face" style="font-size:11px; padding:3px 10px;">Face</button>'
new_regions = '''<button class="btn-secondary region-btn" data-region="arm" style="font-size:11px; padding:3px 10px;">Arm / Hand</button>
            <button class="btn-secondary region-btn" data-region="leg" style="font-size:11px; padding:3px 10px;">Leg / Foot</button>
            <button class="btn-secondary region-btn" data-region="face" style="font-size:11px; padding:3px 10px;">Face</button>
            <button class="btn-secondary region-btn" data-region="all" style="font-size:11px; padding:3px 10px;">Full Body</button>'''
assert old_regions in text, 'old_regions not found'
text = text.replace(old_regions, new_regions, 1)

# 3. Add Calibrate button to Acupoint Card
old_soap_btn = '<button onclick="addAcupointToSOAP()" style="font-size:11px; padding:4px 10px; background:#0284c7; color:#fff;">+ Add to SOAP Note</button>'
new_soap_btn = old_soap_btn + '\n              <button onclick="openStudioEditorModal(lastSelectedAcupoint)" style="font-size:11px; padding:4px 10px; background:#4338ca; color:#e0e7ff; border:1px solid #6366f1;">🛠️ Calibrate in Studio</button>'
assert old_soap_btn in text, 'old_soap_btn not found'
text = text.replace(old_soap_btn, new_soap_btn, 1)

# 4. Handle SURFACE_REGISTERED_FJ2810 in showAtlasAcupoint
old_banner = '''        if (isVer) {
          regBanner.innerHTML = `<span class="badge" style="background:#065f46; color:#a7f3d0; border:1px solid #10b981; font-weight:700;">✓ Verified Anatomical Anchor (BodyParts3D Ground Truth)</span>`;
        } else {
          regBanner.innerHTML = `<span class="badge" style="background:#78350f; color:#fde68a; border:1px solid #f59e0b; font-weight:700;">⚠️ Uncertain Posture Offset (External Reference)</span>`;
        }'''
new_banner = '''        const isSurf = pt.registration_status === "SURFACE_REGISTERED_FJ2810";
        if (isVer) {
          regBanner.innerHTML = `<span class="badge" style="background:#065f46; color:#a7f3d0; border:1px solid #10b981; font-weight:700;">✓ Verified Anatomical Anchor (BodyParts3D Ground Truth)</span>`;
        } else if (isSurf) {
          regBanner.innerHTML = `<span class="badge" style="background:#0e7490; color:#cffafe; border:1px solid #06b6d4; font-weight:700;">FJ2810 Surface Registered (JICio Skin Intersection)</span>`;
        } else {
          regBanner.innerHTML = `<span class="badge" style="background:#78350f; color:#fde68a; border:1px solid #f59e0b; font-weight:700;">⚠️ Uncertain Posture Offset (External Reference)</span>`;
        }'''
# Normalize newlines for matching
text_crlf = '\r\n' in text
old_banner_normalized = old_banner.replace('\n', '\r\n') if text_crlf else old_banner
new_banner_normalized = new_banner.replace('\n', '\r\n') if text_crlf else new_banner
assert old_banner_normalized in text, 'old_banner not found'
text = text.replace(old_banner_normalized, new_banner_normalized, 1)

# 5. Add atlasCommand('set_region') in region button click
old_reg_click = '''        loadRegionQuestionnaires(activeRegion);
      });'''
new_reg_click = '''        loadRegionQuestionnaires(activeRegion);
        atlasCommand('set_region', { region: activeRegion });
      });'''
old_reg_click_norm = old_reg_click.replace('\n', '\r\n') if text_crlf else old_reg_click
new_reg_click_norm = new_reg_click.replace('\n', '\r\n') if text_crlf else new_reg_click
assert old_reg_click_norm in text, 'old_reg_click not found'
text = text.replace(old_reg_click_norm, new_reg_click_norm, 1)

# 6. Add script tag before </body>
script_tag = '  <script src="/meridianEditor.js"></script>\n'
if text_crlf:
    script_tag = '  <script src="/meridianEditor.js"></script>\r\n'
idx_body = text.rfind('</body>')
assert idx_body != -1, '</body> not found'
text = text[:idx_body] + script_tag + text[idx_body:]

index_path.write_text(text, encoding="utf-8")
print("Successfully updated index.html with Meridian Studio & Region navigation!")
