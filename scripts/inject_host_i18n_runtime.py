import re

with open('msk_therapy_os/static/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Helper code to inject at the beginning of the <script> block
script_injection = '''
    // --- Multilingual Terminology Resolution Helper ---
    function resolveLocalizedStructureName(structId, defaultName) {
      if (!window.__msk_i18n) return defaultName;
      const lang = window.__msk_i18n.getLang();
      const reg = window.__msk_i18n.getTerminology();
      if (!reg) return defaultName;

      // 1. Check anatomy_structures
      if (reg.anatomy_structures) {
        const match = reg.anatomy_structures.find(s => s.id === structId);
        if (match && match['name_' + lang]) return match['name_' + lang];
      }

      // 2. Check acupuncture points
      if (structId && structId.startsWith('ACU-')) {
        const code = structId.replace('ACU-', '');
        if (reg.points && reg.points[code]) {
          const pt = reg.points[code];
          if (lang === 'zh') return `${pt.name_zh} (${pt.code} / ${pt.pinyin || pt.name_en})`;
          if (lang === 'vi') return `${pt.name_vi || pt.name_en} (${pt.code} / ${pt.name_zh})`;
          return `${pt.name_en} (${pt.code} / ${pt.name_zh})`;
        }
      }

      // 3. Check Thai Sen Sib
      if (structId && structId.includes('THAI') && reg.thai_sen_sib) {
        const match = reg.thai_sen_sib.find(t => t.id === structId || structId.endsWith(t.code.split('-').pop()));
        if (match && match['name_' + lang]) return match['name_' + lang];
      }

      // 4. Check Dien Chan
      if (structId && structId.includes('DIEN') && reg.dien_chan) {
        const match = reg.dien_chan.find(d => d.id === structId || structId.endsWith(d.code.split('-').pop()));
        if (match && match['name_' + lang]) return match['name_' + lang];
      }

      return defaultName;
    }

    // Global listener for language change
    window.addEventListener('msk:lang-changed', (ev) => {
      const { lang, t } = ev.detail;
      // Re-render active region structures
      const activeRegionBtn = document.querySelector('.region-btn.active');
      const activeRegion = activeRegionBtn ? activeRegionBtn.getAttribute('data-region') : 'neck';
      if (typeof loadRegionAnatomy === 'function') {
        loadRegionAnatomy(activeRegion);
      }
      // Re-render acupoint details if active
      if (typeof showAtlasAcupoint === 'function' && window.lastSelectedAcupoint) {
        showAtlasAcupoint(window.lastSelectedAcupoint);
      }
      // Re-render Dien Chan details if active
      if (typeof showAtlasDienChan === 'function' && window.lastSelectedDienChan) {
        showAtlasDienChan(window.lastSelectedDienChan);
      }
      // Re-render SOAP records if active
      if (typeof renderSOAPRecords === 'function' && window.__lastSoaps) {
        renderSOAPRecords(window.__lastSoaps);
      }
    });

    // Language switcher click delegation
    document.addEventListener('click', (ev) => {
      const btn = ev.target.closest('.lang-btn');
      if (btn) {
        const lang = btn.getAttribute('data-lang');
        if (window.__msk_i18n && lang) {
          window.__msk_i18n.setLanguage(lang);
        }
      }
    });
'''

# Check if script_injection is already present
if 'resolveLocalizedStructureName' not in text:
    # Inject right after `<script>` tag
    script_pos = text.find('<script>')
    if script_pos != -1:
        text = text[:script_pos + 8] + script_injection + text[script_pos + 8:]
        print("Injected multilingual resolution helper into <script>")
    else:
        print("Warning: <script> tag not found")

with open('msk_therapy_os/static/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated index.html successfully.")
