from pathlib import Path

BASE = Path("D:/5Projects/msk-therapy-os")
mer_path = BASE / "msk_therapy_os/static/atlas/meridians.js"
text = mer_path.read_text(encoding="utf-8").replace("\r\n", "\n")

target = """        <div style="display:flex; flex-direction:column; gap:4px;">
          <input type="text" id="txtAcuSearch" """

addition = """        <div style="display:flex; flex-direction:column; gap:4px;">
          <label style="font-size:11px; color:var(--muted);">Meridian Channel:</label>
          <select id="selMeridianChannel" style="background:var(--panel-2); color:var(--bone); border:1px solid var(--line); padding:4px 6px; border-radius:var(--r-s); font-size:11px;">
            <option value="all">⚡ All 14 Meridians</option>
            <option value="GV">GV — Du Mai (Governing)</option>
            <option value="CV">CV — Ren Mai (Conception)</option>
            <option value="BL">BL — Bladder (Taiyang)</option>
            <option value="GB">GB — Gallbladder (Shaoyang)</option>
            <option value="SI">SI — Small Intestine</option>
            <option value="TE">TE — Triple Energizer (Sanjiao)</option>
            <option value="LI">LI — Large Intestine</option>
            <option value="LU">LU — Lung (Taiyin)</option>
            <option value="ST">ST — Stomach (Yangming)</option>
            <option value="SP">SP — Spleen (Taiyin)</option>
            <option value="HT">HT — Heart (Shaoyin)</option>
            <option value="KI">KI — Kidney (Shaoyin)</option>
            <option value="PC">PC — Pericardium (Jueyin)</option>
            <option value="LR">LR — Liver (Jueyin)</option>
          </select>
        </div>

        <div style="display:flex; flex-direction:column; gap:4px;">
          <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--muted);">
            <span>Skin Transparency:</span>
            <span id="lblAtlasSkinOpacity">78%</span>
          </div>
          <input type="range" id="rngAtlasSkinOpacity" min="0" max="100" value="78" style="cursor:pointer;" />
        </div>

        <div style="display:flex; flex-direction:column; gap:4px;">
          <input type="text" id="txtAcuSearch" """

if target in text:
    text = text.replace(target, addition, 1)

target2 = """    document.getElementById('txtAcuSearch').addEventListener('input', (e) => {"""
addition2 = """    const selChan = document.getElementById('selMeridianChannel');
    if (selChan) selChan.addEventListener('change', (e) => {
      filterMeridian = e.target.value;
      renderPointsList();
      render();
    });
    const rngSkin = document.getElementById('rngAtlasSkinOpacity');
    if (rngSkin) rngSkin.addEventListener('input', (e) => {
      const alpha = parseInt(e.target.value, 10) / 100;
      const lbl = document.getElementById('lblAtlasSkinOpacity');
      if (lbl) lbl.textContent = e.target.value + '%';
      const r = getRenderer();
      if (r) r.setSkinOpacity(alpha);
      render();
    });

    document.getElementById('txtAcuSearch').addEventListener('input', (e) => {"""

if target2 in text:
    text = text.replace(target2, addition2, 1)

mer_path.write_text(text, encoding="utf-8")
print("Successfully added channel filter & skin opacity slider to meridians.js!")
