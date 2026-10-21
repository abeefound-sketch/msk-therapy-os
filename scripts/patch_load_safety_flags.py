with open('msk_therapy_os/static/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''      flags.forEach(f => {
        const opt1 = document.createElement("option");
        opt1.value = f;
        opt1.textContent = f;
        sel.appendChild(opt1);

        const opt2 = document.createElement("option");
        opt2.value = f;
        opt2.textContent = f;
        visSel.appendChild(opt2);
      });'''

replacement = '''      const t = window.__msk_i18n ? window.__msk_i18n.t : ((k, fb) => fb);
      flags.forEach(f => {
        const label = t('safety_flags.' + f, f);
        const opt1 = document.createElement("option");
        opt1.value = f;
        opt1.textContent = label;
        sel.appendChild(opt1);

        const opt2 = document.createElement("option");
        opt2.value = f;
        opt2.textContent = label;
        visSel.appendChild(opt2);
      });'''

text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

assert target_norm in text_norm, "Target not found in index.html"
text_norm = text_norm.replace(target_norm, replacement_norm, 1)

# Also ensure loadSafetyFlags() is called on msk:lang-changed
listener_target = "loadRegionAnatomy(activeRegion);\n      }"
listener_repl = "loadRegionAnatomy(activeRegion);\n      }\n      if (typeof loadSafetyFlags === 'function') loadSafetyFlags();"

if listener_target in text_norm:
    text_norm = text_norm.replace(listener_target, listener_repl, 1)
    print("Added loadSafetyFlags to lang-changed listener")

with open('msk_therapy_os/static/index.html', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text_norm)

print("loadSafetyFlags patched with multilingual labels successfully.")
