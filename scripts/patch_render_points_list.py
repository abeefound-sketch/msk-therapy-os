with open('msk_therapy_os/static/atlas/meridians.js', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add refreshPointsList variable
target1 = "  // Build sidebar controls inside #panelMeridians\n  function buildSidebarControls() {"
replacement1 = "  let refreshPointsList = null;\n\n  // Build sidebar controls inside #panelMeridians\n  function buildSidebarControls() {"

if target1 in text:
    text = text.replace(target1, replacement1, 1)
    print("Replaced target1 (LF)")
else:
    target1_crlf = target1.replace('\n', '\r\n')
    replacement1_crlf = replacement1.replace('\n', '\r\n')
    if target1_crlf in text:
        text = text.replace(target1_crlf, replacement1_crlf, 1)
        print("Replaced target1 (CRLF)")

# 2. Assign refreshPointsList = renderPointsList inside buildSidebarControls
target2 = "    function renderPointsList() {"
replacement2 = "    function renderPointsList() {\n      refreshPointsList = renderPointsList;"

if target2 in text:
    text = text.replace(target2, replacement2, 1)
    print("Replaced target2 (LF)")
else:
    target2_crlf = target2.replace('\n', '\r\n')
    replacement2_crlf = replacement2.replace('\n', '\r\n')
    if target2_crlf in text:
        text = text.replace(target2_crlf, replacement2_crlf, 1)
        print("Replaced target2 (CRLF)")

# 3. Replace renderPointsList() call on line 790
target3 = "      renderPointsList();\n      render();"
replacement3 = "      if (refreshPointsList) refreshPointsList();\n      render();"

if target3 in text:
    text = text.replace(target3, replacement3, 1)
    print("Replaced target3 (LF)")
else:
    target3_crlf = target3.replace('\n', '\r\n')
    replacement3_crlf = replacement3.replace('\n', '\r\n')
    if target3_crlf in text:
        text = text.replace(target3_crlf, replacement3_crlf, 1)
        print("Replaced target3 (CRLF)")

with open('msk_therapy_os/static/atlas/meridians.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved updated meridians.js")
