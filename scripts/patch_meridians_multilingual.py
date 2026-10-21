with open('msk_therapy_os/static/atlas/meridians.js', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''    let pos = null;
    let label = '';
    if (selectedCode && selectedCode.startsWith('DIEN-') && window.__selectedDienChan) {
      pos = window.__selectedDienChan.position;
      label = `${window.__selectedDienChan.name} [🇻🇳 Dien Chan Reflex]`;
    } else if (selectedCode && window.__selectedAcupoint) {
      pos = window.__selectedAcupoint.position;
      const pt = window.__selectedAcupoint;
      const statusTag = pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR' ? ' [✓ Verified]' : ' [Surface Registered]';
      label = `${pt.name_en} (${pt.code} / ${pt.name_zh})${statusTag}`;
    }'''

replacement = '''    let pos = null;
    let label = '';
    const lang = window.__atlas_i18n ? window.__atlas_i18n.getLang() : 'en';

    if (selectedCode && selectedCode.startsWith('DIEN-') && window.__selectedDienChan) {
      pos = window.__selectedDienChan.position;
      const dc = window.__selectedDienChan;
      const dcName = lang === 'vi' ? (dc.name_vi || dc.name) : (lang === 'zh' ? (dc.name_zh || dc.name) : dc.name);
      const tag = lang === 'vi' ? ' [🇻🇳 Phản xạ Diện Chẩn]' : (lang === 'zh' ? ' [🇻🇳 越南面针反射]' : ' [🇻🇳 Dien Chan Reflex]');
      label = `${dcName}${tag}`;
    } else if (selectedCode && window.__selectedAcupoint) {
      pos = window.__selectedAcupoint.position;
      const pt = window.__selectedAcupoint;
      let statusTag = ' [Surface Registered]';
      if (pt.registration_status === 'VERIFIED_ANATOMICAL_ANCHOR') {
        statusTag = lang === 'vi' ? ' [✓ Đã kiểm chứng]' : (lang === 'zh' ? ' [✓ 已验证基准]' : ' [✓ Verified]');
      } else {
        statusTag = lang === 'vi' ? ' [Mốc thể biểu]' : (lang === 'zh' ? ' [体表对齐]' : ' [Surface Registered]');
      }
      if (lang === 'zh') {
        label = `${pt.name_zh} (${pt.code} / ${pt.pinyin || pt.name_en})${statusTag}`;
      } else if (lang === 'vi') {
        label = `${pt.name_vi || pt.name_en} (${pt.code} / ${pt.name_zh})${statusTag}`;
      } else {
        label = `${pt.name_en} (${pt.code} / ${pt.name_zh})${statusTag}`;
      }
    }'''

text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

assert target_norm in text_norm, "Target not found in meridians.js"
text_norm = text_norm.replace(target_norm, replacement_norm, 1)

with open('msk_therapy_os/static/atlas/meridians.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text_norm)

print("meridians.js updated with multilingual pin labels.")
