with open('msk_therapy_os/static/meridianEditor.js', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update initStudio
target1 = "if (allPoints['LI4']) {\n          loadPointIntoEditor('LI4');\n        }"
replacement1 = "if (allPoints['LI4']) {\n          loadPointIntoEditor('LI4', false);\n        }"
if target1 in text:
    text = text.replace(target1, replacement1, 1)
    print("Replaced target1 (LF)")
else:
    target1_crlf = target1.replace('\n', '\r\n')
    replacement1_crlf = replacement1.replace('\n', '\r\n')
    if target1_crlf in text:
        text = text.replace(target1_crlf, replacement1_crlf, 1)
        print("Replaced target1 (CRLF)")
    else:
        print("target1 NOT FOUND")

# 2. Update function signature
target2 = """  function loadPointIntoEditor(code) {
    if (!allPoints[code]) return;
    currentPointCode = code;
    const pt = allPoints[code];"""

replacement2 = """  function loadPointIntoEditor(code, notifyAtlas = true) {
    if (!allPoints[code]) return;
    currentPointCode = code;
    const pt = allPoints[code];"""

if target2 in text:
    text = text.replace(target2, replacement2, 1)
    print("Replaced target2 (LF)")
else:
    target2_crlf = target2.replace('\n', '\r\n')
    replacement2_crlf = replacement2.replace('\n', '\r\n')
    if target2_crlf in text:
        text = text.replace(target2_crlf, replacement2_crlf, 1)
        print("Replaced target2 (CRLF)")
    else:
        print("target2 NOT FOUND")

# 3. Update atlasCommand
target3 = """    // Select in 3D Atlas
    if (window.atlasCommand) {
      window.atlasCommand('select_acupoint', { code });
    }"""

replacement3 = """    // Select in 3D Atlas only if requested and modal is active
    const modalEl = document.getElementById('meridianStudioModal');
    const isModalActive = modalEl && modalEl.style.display === 'flex';
    if (notifyAtlas && isModalActive && window.atlasCommand) {
      window.atlasCommand('select_acupoint', { code });
    }"""

if target3 in text:
    text = text.replace(target3, replacement3, 1)
    print("Replaced target3 (LF)")
else:
    target3_crlf = target3.replace('\n', '\r\n')
    replacement3_crlf = replacement3.replace('\n', '\r\n')
    if target3_crlf in text:
        text = text.replace(target3_crlf, replacement3_crlf, 1)
        print("Replaced target3 (CRLF)")
    else:
        print("target3 NOT FOUND")

with open('msk_therapy_os/static/meridianEditor.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved updated meridianEditor.js")
