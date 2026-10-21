with open('msk_therapy_os/static/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update loadRegionAnatomy
old_load_region = '''          return `
            <div class="item-card">
              <div class="item-card-header">
                <strong>${s.name}</strong>'''

new_load_region = '''          const localizedName = resolveLocalizedStructureName(s.structure_id, s.name);
          return `
            <div class="item-card">
              <div class="item-card-header">
                <strong>${localizedName}</strong>'''

if old_load_region in text:
    text = text.replace(old_load_region, new_load_region, 1)
    print("Patched loadRegionAnatomy with localizedName")
else:
    print("Warning: old_load_region not found")

# 2. Update showAtlasAcupoint
old_acu = '''      document.getElementById("acuPointTitle").textContent = `${pt.name_en} (${pt.code} / ${pt.name_zh} - ${pt.pinyin})`;'''
new_acu = '''      window.lastSelectedAcupoint = pt;
      const lang = window.__msk_i18n ? window.__msk_i18n.getLang() : 'en';
      let title = `${pt.name_en} (${pt.code} / ${pt.name_zh} - ${pt.pinyin})`;
      if (lang === 'zh') {
        title = `${pt.name_zh} (${pt.code} / ${pt.pinyin || pt.name_en})`;
      } else if (lang === 'vi') {
        title = `${pt.name_vi || pt.name_en} (${pt.code} / ${pt.name_zh})`;
      }
      document.getElementById("acuPointTitle").textContent = title;'''

if old_acu in text:
    text = text.replace(old_acu, new_acu, 1)
    print("Patched showAtlasAcupoint with multilingual title")
else:
    print("Warning: old_acu not found")

# 3. Update showAtlasDienChan
old_dc = '''      document.getElementById("dcPointTitle").textContent = `${pt.name} (${pt.code})`;
      document.getElementById("dcTargetRegion").textContent = (pt.target_region || 'cervical').toUpperCase();
      document.getElementById("dcIndication").textContent = pt.indication || 'Traditional somatotopic facial reflex projection';'''

new_dc = '''      window.lastSelectedDienChan = pt;
      const lang = window.__msk_i18n ? window.__msk_i18n.getLang() : 'en';
      let dcName = pt.name;
      let dcInd = pt.indication || 'Traditional somatotopic facial reflex projection';
      if (window.__msk_i18n && window.__msk_i18n.getTerminology()) {
        const reg = window.__msk_i18n.getTerminology();
        if (reg.dien_chan) {
          const match = reg.dien_chan.find(d => d.code === pt.code);
          if (match) {
            if (lang === 'zh') {
              dcName = match.name_zh;
              dcInd = match.indications ? match.indications.zh : pt.indication;
            } else if (lang === 'vi') {
              dcName = match.name_vi;
              dcInd = match.indications ? match.indications.vi : pt.indication;
            }
          }
        }
      }
      document.getElementById("dcPointTitle").textContent = `${dcName} (${pt.code})`;
      document.getElementById("dcTargetRegion").textContent = (pt.target_region || 'cervical').toUpperCase();
      document.getElementById("dcIndication").textContent = dcInd;'''

if old_dc in text:
    text = text.replace(old_dc, new_dc, 1)
    print("Patched showAtlasDienChan with multilingual name and indications")
else:
    print("Warning: old_dc not found")

# 4. Update runSafetyCheck
old_safety = '''      if (hasRedFlag) {
        banner.style.display = "block";
        banner.className = "alert alert-danger";
        banner.innerHTML = `<strong>⚠️ STOP_AND_REFER:</strong> Red flag detected! High clinical risk. Manual therapy contraindicated. Immediate referral to emergency or specialist medical care recommended.`;
      } else {
        banner.style.display = "block";
        banner.className = "alert alert-success";
        banner.innerHTML = `<strong>✓ CLEARED:</strong> No immediate contraindication red flags reported. Proceed with careful graduated assessment.`;
      }'''

new_safety = '''      const t = window.__msk_i18n ? window.__msk_i18n.t : ((k, f) => f);
      if (hasRedFlag) {
        banner.style.display = "block";
        banner.className = "alert alert-danger";
        banner.innerHTML = `<strong>⚠️ STOP_AND_REFER:</strong> ${t('safety.status_stop', 'Red flag detected! High clinical risk. Manual therapy contraindicated. Immediate referral required.')}`;
      } else {
        banner.style.display = "block";
        banner.className = "alert alert-success";
        banner.innerHTML = `<strong>✓ CLEARED:</strong> ${t('safety.status_cleared', 'No immediate contraindication red flags reported. Proceed with careful graduated assessment.')}`;
      }'''

if old_safety in text:
    text = text.replace(old_safety, new_safety, 1)
    print("Patched runSafetyCheck with localized messages")
else:
    print("Warning: old_safety not found")

# 5. Store last loaded soaps in window.__lastSoaps in loadCaseData
old_soaps = '''renderSOAPRecords(data.soaps || []);'''
new_soaps = '''window.__lastSoaps = data.soaps || []; renderSOAPRecords(window.__lastSoaps);'''
if old_soaps in text:
    text = text.replace(old_soaps, new_soaps, 1)
    print("Patched loadCaseData with window.__lastSoaps")

with open('msk_therapy_os/static/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Dynamic functions in index.html patched successfully.")
