with open('msk_therapy_os/static/meridianEditor.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Add translation calls in createStudioModal
replacements = [
    ('Apply Coordinates to 3D View', "${(window.__msk_i18n ? window.__msk_i18n.t('studio.btn_apply', 'Apply Coordinates to 3D View') : 'Apply Coordinates to 3D View')}"),
    ('>Revert</button>', ">${(window.__msk_i18n ? window.__msk_i18n.t('studio.btn_revert', 'Revert') : 'Revert')}</button>"),
    ('Save Metadata Changes', "${(window.__msk_i18n ? window.__msk_i18n.t('studio.btn_save', 'Save Metadata Changes') : 'Save Metadata Changes')}"),
    ('📋 Copy Point JSON', "${(window.__msk_i18n ? window.__msk_i18n.t('studio.btn_copy_json', '📋 Copy Point JSON') : '📋 Copy Point JSON')}")
]

for old, new in replacements:
    if old in text:
        text = text.replace(old, new, 1)
        print(f"Patched '{old}' in meridianEditor.js")
    else:
        print(f"Warning: '{old}' not found in meridianEditor.js")

with open('msk_therapy_os/static/meridianEditor.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("meridianEditor.js updated successfully.")
