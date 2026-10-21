with open('msk_therapy_os/static/atlas/meridians.js', 'r', encoding='utf-8') as f:
    text = f.read()

target = """        const r = getRenderer();
        if (r) {
          if (filterMeridian === 'CV') {
            r.camera.yaw = 0.0;
            r.camera.pitch = 0.02;
            if (typeof r._draw === 'function') r._draw();
          } else if (filterMeridian === 'GV' || filterMeridian === 'BL') {
            r.camera.yaw = Math.PI;
            r.camera.pitch = 0.02;
            if (typeof r._draw === 'function') r._draw();
          }
        }"""

replacement = """        const r = getRenderer();
        if (r) {
          r.camera.target = [0, 1.22, 0];
          r.camera.dist = Math.max(r.camera.dist, 1.35);
          if (filterMeridian === 'CV') {
            r.camera.yaw = 0.0;
            r.camera.pitch = 0.02;
            if (typeof r._draw === 'function') r._draw();
          } else if (filterMeridian === 'GV' || filterMeridian === 'BL') {
            r.camera.yaw = Math.PI;
            r.camera.pitch = 0.02;
            if (typeof r._draw === 'function') r._draw();
          } else {
            if (typeof r._draw === 'function') r._draw();
          }
        }"""

if target in text:
    text = text.replace(target, replacement, 1)
    print("Replaced in meridians.js (LF)")
else:
    target_crlf = target.replace('\n', '\r\n')
    replacement_crlf = replacement.replace('\n', '\r\n')
    if target_crlf in text:
        text = text.replace(target_crlf, replacement_crlf, 1)
        print("Replaced in meridians.js (CRLF)")
    else:
        print("Target NOT FOUND in meridians.js")

with open('msk_therapy_os/static/atlas/meridians.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved updated meridians.js")
