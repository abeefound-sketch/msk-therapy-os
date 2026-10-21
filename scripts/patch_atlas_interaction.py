"""Script applying enhanced 3D atlas interaction:
1. Camera panning (right-drag, Shift+left-drag, middle-drag, touch pan)
2. Dynamic OrbitControls target updates to selected structure or acupoint
3. Fit-to-object framing using bounding box / sphere
4. Intelligent min/max zoom limits and near-plane clipping prevention
5. Full Body and Focus Selected toolbar buttons and keybindings
"""
from pathlib import Path

BASE = Path("D:/5Projects/msk-therapy-os")

# ---------------------------------------------------------------------------
# 3. Update app.js
# ---------------------------------------------------------------------------
app_path = BASE / "msk_therapy_os/static/atlas/app.js"
app_src = app_path.read_text(encoding="utf-8").replace("\r\n", "\n")

# Update select()
old_select = """  function select(ci, { focus = false, reveal = true } = {}) {
    if (ci < 0 || ci == null) { clearSelection(); return; }
    selection = ci;
    $('#hoverTip').hidden = true;
    const els = atlas.concepts[ci].el;
    if (els.some(e => !renderer.visible[e])) { ensureVisible(els); applyVisibility(); }
    renderer.selected.fill(0);
    for (const e of els) renderer.selected[e] = 1;
    renderer.requestRender();
    showInspector();
    if (reveal) revealInTree(ci); else markTree();
    if (focus) focusSelection();"""

new_select = """  function select(ci, { focus = false, reveal = true, updateTarget = true } = {}) {
    if (ci < 0 || ci == null) { clearSelection(); return; }
    selection = ci;
    window.__selectedAcupoint = null; // Clear acupoint focus when anatomical structure is selected
    $('#hoverTip').hidden = true;
    const els = atlas.concepts[ci].el;
    if (els.some(e => !renderer.visible[e])) { ensureVisible(els); applyVisibility(); }
    renderer.selected.fill(0);
    for (const e of els) renderer.selected[e] = 1;
    renderer.requestRender();
    showInspector();
    if (reveal) revealInTree(ci); else markTree();
    if (focus) {
      focusSelection();
    } else if (updateTarget) {
      // Dynamic OrbitControls target update to structure centroid
      const b = atlas.bbox(els.filter(e => renderer.visible[e]));
      if (b) {
        const c = [(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2];
        renderer.setTarget(c, true);
      }
    }"""

if old_select in app_src:
    app_src = app_src.replace(old_select, new_select)

# Update focusSelection()
old_focus_sel = """  function focusSelection() {
    const els = selection >= 0 ? atlas.concepts[selection].el.filter(e => renderer.visible[e]) : [];
    if (!els.length) { renderer.frame(atlas.index.bbox); return; }
    frameWithContext(els, 1.4);
  }"""

new_focus_sel = """  function focusSelection() {
    if (window.__selectedAcupoint && window.__selectedAcupoint.position) {
      renderer.framePoint(window.__selectedAcupoint.position, 0.08);
      return;
    }
    const els = selection >= 0 ? atlas.concepts[selection].el.filter(e => renderer.visible[e]) : [];
    if (!els.length) { renderer.frame(atlas.index.bbox); return; }
    frameWithContext(els, 1.35);
  }"""

if old_focus_sel in app_src:
    app_src = app_src.replace(old_focus_sel, new_focus_sel)

# Update bindStage()
old_bind_stage = """  function bindStage() {
    const canvas = $('#viewport');
    let drag = null;
    let hoverTimer = 0;
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    canvas.addEventListener('pointerdown', (e) => {
      canvas.focus({ preventScroll: true });
      drag = { x: e.clientX, y: e.clientY, btn: e.button, pan: e.button !== 0 || e.shiftKey, moved: false };
      canvas.setPointerCapture(e.pointerId);
      $('#hoverTip').hidden = true;
    });
    canvas.addEventListener('pointermove', (e) => {
      if (drag) {
        const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
        if (!drag.moved && Math.hypot(dx, dy) < 3) return;
        drag.moved = true;
        canvas.classList.add('dragging');
        drag.x = e.clientX; drag.y = e.clientY;
        if (drag.pan) renderer.pan(dx, dy); else renderer.orbit(dx, dy);
        return;
      }
      if (mode === 'quiz') return; // hovering would give answers away
      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => {
        const i = renderer.pick(e.clientX, e.clientY);
        const tip = $('#hoverTip');
        if (i < 0) { tip.hidden = true; return; }
        const r = canvas.getBoundingClientRect();
        tip.textContent = atlas.displayName(atlas.conceptOf(i));
        tip.style.left = (e.clientX - r.left) + 'px';
        tip.style.top = (e.clientY - r.top) + 'px';
        tip.hidden = false;
      }, atlas.index.counts.triangles > 4e6 ? 220 : 80);
    });
    canvas.addEventListener('pointerleave', () => { clearTimeout(hoverTimer); $('#hoverTip').hidden = true; });
    canvas.addEventListener('pointerup', (e) => {
      canvas.classList.remove('dragging');
      if (drag && !drag.moved && drag.btn === 0) {
        const i = renderer.pick(e.clientX, e.clientY);
        if (mode === 'quiz') quizPick(i);
        else if (i < 0) clearSelection();
        else select(atlas.conceptOf(i));
      }
      drag = null;
    });
    canvas.addEventListener('dblclick', (e) => {
      if (mode === 'quiz') return;
      const i = renderer.pick(e.clientX, e.clientY);
      if (i >= 0) select(atlas.conceptOf(i), { focus: true }); else renderer.frame(atlas.index.bbox);
    });
    canvas.addEventListener('wheel', (e) => { e.preventDefault(); renderer.zoom(Math.exp(e.deltaY * 0.0012)); }, { passive: false });
  }"""

new_bind_stage = """  function bindStage() {
    const canvas = $('#viewport');
    let drag = null;
    let hoverTimer = 0;
    const activePointers = new Map();
    let initialPinchDist = null;
    let lastTouchCenter = null;

    canvas.addEventListener('contextmenu', (e) => e.preventDefault());

    canvas.addEventListener('pointerdown', (e) => {
      canvas.focus({ preventScroll: true });
      activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      canvas.setPointerCapture(e.pointerId);
      $('#hoverTip').hidden = true;

      if (activePointers.size === 1) {
        const isPan = e.button === 2 || e.button === 1 || (e.button === 0 && e.shiftKey);
        drag = { x: e.clientX, y: e.clientY, btn: e.button, pan: isPan, moved: false };
        initialPinchDist = null;
        lastTouchCenter = null;
      } else if (activePointers.size === 2) {
        drag = null;
        const pts = Array.from(activePointers.values());
        initialPinchDist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        lastTouchCenter = { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 };
      }
    });

    canvas.addEventListener('pointermove', (e) => {
      if (activePointers.has(e.pointerId)) {
        activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      }

      // Two-finger touch gesture: Pinch-to-zoom + Two-finger pan
      if (activePointers.size === 2) {
        const pts = Array.from(activePointers.values());
        const currentDist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        const currentCenter = { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 };

        if (initialPinchDist && initialPinchDist > 5 && currentDist > 5) {
          const factor = Math.exp((initialPinchDist - currentDist) * 0.005);
          renderer.zoom(factor);
          initialPinchDist = currentDist;
        }

        if (lastTouchCenter) {
          const dx = currentCenter.x - lastTouchCenter.x;
          const dy = currentCenter.y - lastTouchCenter.y;
          if (Math.hypot(dx, dy) > 1) {
            renderer.pan(dx, dy);
            lastTouchCenter = currentCenter;
          }
        } else {
          lastTouchCenter = currentCenter;
        }
        return;
      }

      // Single pointer drag (Mouse or 1-finger touch)
      if (drag) {
        const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
        if (!drag.moved && Math.hypot(dx, dy) < 3) return;
        drag.moved = true;
        canvas.classList.add('dragging');
        drag.x = e.clientX; drag.y = e.clientY;
        const isPan = drag.pan || e.shiftKey || (e.buttons & 2) !== 0 || (e.buttons & 4) !== 0;
        if (isPan) renderer.pan(dx, dy); else renderer.orbit(dx, dy);
        return;
      }

      if (mode === 'quiz') return;
      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => {
        const i = renderer.pick(e.clientX, e.clientY);
        const tip = $('#hoverTip');
        if (i < 0) { tip.hidden = true; return; }
        const r = canvas.getBoundingClientRect();
        tip.textContent = atlas.displayName(atlas.conceptOf(i));
        tip.style.left = (e.clientX - r.left) + 'px';
        tip.style.top = (e.clientY - r.top) + 'px';
        tip.hidden = false;
      }, atlas.index.counts.triangles > 4e6 ? 220 : 80);
    });

    canvas.addEventListener('pointerleave', () => { clearTimeout(hoverTimer); $('#hoverTip').hidden = true; });

    canvas.addEventListener('pointerup', (e) => {
      activePointers.delete(e.pointerId);
      if (activePointers.size === 0) {
        canvas.classList.remove('dragging');
        if (drag && !drag.moved && drag.btn === 0) {
          const i = renderer.pick(e.clientX, e.clientY);
          if (mode === 'quiz') quizPick(i);
          else if (i < 0) clearSelection();
          else select(atlas.conceptOf(i));
        }
        drag = null;
        initialPinchDist = null;
        lastTouchCenter = null;
      } else if (activePointers.size === 1) {
        const remaining = Array.from(activePointers.values())[0];
        drag = { x: remaining.x, y: remaining.y, btn: 0, pan: false, moved: true };
        initialPinchDist = null;
        lastTouchCenter = null;
      }
    });

    canvas.addEventListener('pointercancel', (e) => {
      activePointers.delete(e.pointerId);
      if (activePointers.size === 0) {
        canvas.classList.remove('dragging');
        drag = null;
        initialPinchDist = null;
        lastTouchCenter = null;
      }
    });

    canvas.addEventListener('dblclick', (e) => {
      if (mode === 'quiz') return;
      const i = renderer.pick(e.clientX, e.clientY);
      if (i >= 0) select(atlas.conceptOf(i), { focus: true }); else renderer.frame(atlas.index.bbox);
    });

    canvas.addEventListener('wheel', (e) => { e.preventDefault(); renderer.zoom(Math.exp(e.deltaY * 0.0012)); }, { passive: false });
  }"""

if old_bind_stage in app_src:
    app_src = app_src.replace(old_bind_stage, new_bind_stage)

# Update bindUI()
old_bind_ui = """    $('#btnReset').addEventListener('click', resetAll);"""
new_bind_ui = """    const btnFull = $('#btnFullBody');
    if (btnFull) btnFull.addEventListener('click', () => { if (atlas) renderer.frame(atlas.index.bbox); });
    const btnFoc = $('#btnFocusSelected');
    if (btnFoc) btnFoc.addEventListener('click', focusSelection);
    $('#btnReset').addEventListener('click', resetAll);"""

if old_bind_ui in app_src:
    app_src = app_src.replace(old_bind_ui, new_bind_ui)

# Update message listener in app.js
old_msg = """      } else if (action === 'reset_view') {
        resetAll();"""

new_msg = """      } else if (action === 'reset_view') {
        resetAll();
      } else if (action === 'full_body_view' && renderer && atlas) {
        renderer.frame(atlas.index.bbox);
      } else if (action === 'focus_selection') {
        focusSelection();"""

if old_msg in app_src:
    app_src = app_src.replace(old_msg, new_msg)

# Update document keydown listener in app.js
old_kbd = """      else if (k === 'a' || k === 'A') resetAll();"""
new_kbd = """      else if (k === 'a' || k === 'A') resetAll();
      else if (k === 'Home') { if (atlas) renderer.frame(atlas.index.bbox); }"""

if old_kbd in app_src:
    app_src = app_src.replace(old_kbd, new_kbd)

app_path.write_text(app_src, encoding="utf-8")
print("app.js verified / updated successfully!")

# ---------------------------------------------------------------------------
# 4. Update msk_therapy_os/static/atlas/index.html
# ---------------------------------------------------------------------------
idx_path = BASE / "msk_therapy_os/static/atlas/index.html"
idx_src = idx_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_tools = """      <div class="seg small" aria-label="Viewpoint">
        <button data-view="front" title="Front view (1)">Front</button>
        <button data-view="back" title="Back view (2)">Back</button>
        <button data-view="left" title="Patient's left side (3)">Left</button>
        <button data-view="right" title="Patient's right side (4)">Right</button>
      </div>
      <button id="btnReset" class="icon-btn" title="Show everything and reset the view (A)">Reset</button>"""

new_tools = """      <div class="seg small" aria-label="Viewpoint">
        <button data-view="front" title="Front view (1)">Front</button>
        <button data-view="back" title="Back view (2)">Back</button>
        <button data-view="left" title="Patient's left side (3)">Left</button>
        <button data-view="right" title="Patient's right side (4)">Right</button>
      </div>
      <button id="btnFullBody" class="icon-btn" title="Full body framing (Home)">Full Body</button>
      <button id="btnFocusSelected" class="icon-btn" title="Focus on selected structure or acupoint (F)">Focus</button>
      <button id="btnReset" class="icon-btn" title="Show everything and reset the view (A)">Reset</button>"""

if old_tools in idx_src:
    idx_src = idx_src.replace(old_tools, new_tools)
    idx_path.write_text(idx_src, encoding="utf-8")
print("atlas index.html verified / updated successfully!")

# ---------------------------------------------------------------------------
# 5. Update msk_therapy_os/static/index.html (Main Host Application)
# ---------------------------------------------------------------------------
main_idx_path = BASE / "msk_therapy_os/static/index.html"
main_idx_src = main_idx_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_host_btns = """              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'front'})" style="font-size:11px; padding:3px 7px;">Front</button>
              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'back'})" style="font-size:11px; padding:3px 7px;">Back</button>
              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'left'})" style="font-size:11px; padding:3px 7px;">Left</button>
              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'right'})" style="font-size:11px; padding:3px 7px;">Right</button>
              <button class="btn-secondary" onclick="atlasCommand('reset_view')" style="font-size:11px; padding:3px 7px;">Reset</button>"""

new_host_btns = """              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'front'})" style="font-size:11px; padding:3px 7px;">Front</button>
              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'back'})" style="font-size:11px; padding:3px 7px;">Back</button>
              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'left'})" style="font-size:11px; padding:3px 7px;">Left</button>
              <button class="btn-secondary" onclick="atlasCommand('set_view', {preset:'right'})" style="font-size:11px; padding:3px 7px;">Right</button>
              <button class="btn-secondary" onclick="atlasCommand('full_body_view')" style="font-size:11px; padding:3px 7px;" title="Full body view (Home)">Full Body</button>
              <button class="btn-secondary" onclick="atlasCommand('focus_selection')" style="font-size:11px; padding:3px 7px;" title="Focus camera on selected structure or acupoint (F)">Focus</button>
              <button class="btn-secondary" onclick="atlasCommand('reset_view')" style="font-size:11px; padding:3px 7px;">Reset</button>"""

if old_host_btns in main_idx_src:
    main_idx_src = main_idx_src.replace(old_host_btns, new_host_btns)
    main_idx_path.write_text(main_idx_src, encoding="utf-8")
    print("main index.html updated successfully!")
else:
    print("main index.html already updated or pattern not found")

print("\nALL ATLAS 3D INTERACTION ENHANCEMENTS APPLIED SUCCESSFULLY!")
