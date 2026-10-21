import re
from pathlib import Path

BASE = Path("D:/5Projects/msk-therapy-os")

# 1. Update app.js
app_path = BASE / "msk_therapy_os/static/atlas/app.js"
app_src = app_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_app_msg = """      } else if (action === 'set_render_mode') {
        setRenderMode(ev.data.mode);
      } else if (action === 'set_skin_opacity') {
        if (renderer) renderer.setSkinOpacity(ev.data.opacity);
      } else if (action === 'set_filter_meridian') {
        window.postMessage({ action: 'set_filter_meridian', meridian: ev.data.meridian }, '*');
      } else if (action === 'toggle_surface_reference') {
        if (renderer) renderer.setSkinReference(ev.data.enabled);
        window.postMessage({ action: 'toggle_surface_reference', enabled: ev.data.enabled }, '*');"""

new_app_msg = """      } else if (action === 'set_render_mode') {
        setRenderMode(ev.data.mode);
      } else if (action === 'set_skin_opacity') {
        if (renderer) renderer.setSkinOpacity(ev.data.opacity);
        if (window.__meridiansDebug && window.__meridiansDebug.render) window.__meridiansDebug.render();
      } else if (action === 'set_filter_meridian') {
        if (window.__meridiansDebug && window.__meridiansDebug.setFilterMeridian) {
          window.__meridiansDebug.setFilterMeridian(ev.data.meridian);
        }
      } else if (action === 'toggle_surface_reference') {
        if (renderer) renderer.setSkinReference(ev.data.enabled);
        if (window.__meridiansDebug && window.__meridiansDebug.setSurfaceReference) {
          window.__meridiansDebug.setSurfaceReference(ev.data.enabled);
        }"""

if old_app_msg in app_src:
    app_src = app_src.replace(old_app_msg, new_app_msg)
    print("Patched app.js message listener.")
else:
    print("old_app_msg already updated or not found.")

old_set_mode = """  function setRenderMode(mode) {
    if (!renderer) return;
    renderer.setRenderMode(mode);
    if (mode === 'surface') {
      catOn['skin'] = true;
      renderer.setSkinOpacity(0.78);
      applyVisibility();
      window.postMessage({ action: 'set_render_mode', mode: 'surface' }, '*');
    } else if (mode === 'musculoskeletal') {
      catOn['skin'] = false;
      renderer.setSkinOpacity(0.0);
      applyVisibility();
      window.postMessage({ action: 'set_render_mode', mode: 'musculoskeletal' }, '*');
    } else if (mode === 'comparative') {
      catOn['skin'] = true;
      renderer.setSkinOpacity(0.85);
      applyVisibility();
      window.postMessage({ action: 'set_render_mode', mode: 'comparative' }, '*');
    }
    $$('#visModeSelector button').forEach(b => {
      b.classList.toggle('on', b.dataset.mode === mode);
    });
    renderer.requestRender();
  }"""

new_set_mode = """  function setRenderMode(mode) {
    if (!renderer) return;
    renderer.setRenderMode(mode);
    if (mode === 'surface') {
      catOn['skin'] = true;
      renderer.setSkinOpacity(0.78);
      applyVisibility();
    } else if (mode === 'musculoskeletal') {
      catOn['skin'] = false;
      renderer.setSkinOpacity(0.0);
      applyVisibility();
    } else if (mode === 'comparative') {
      catOn['skin'] = true;
      renderer.setSkinOpacity(0.85);
      applyVisibility();
    }
    $$('#visModeSelector button').forEach(b => {
      b.classList.toggle('on', b.dataset.mode === mode);
    });
    if (window.__meridiansDebug && window.__meridiansDebug.setRenderMode) {
      window.__meridiansDebug.setRenderMode(mode);
    } else if (window.__meridiansDebug && window.__meridiansDebug.render) {
      window.__meridiansDebug.render();
    }
    renderer.requestRender();
  }"""

if old_set_mode in app_src:
    app_src = app_src.replace(old_set_mode, new_set_mode)
    print("Patched app.js setRenderMode.")
else:
    print("old_set_mode already updated or not found.")

app_path.write_text(app_src, encoding="utf-8")
print("app.js updated successfully.")

# 2. Update meridians.js
mer_path = BASE / "msk_therapy_os/static/atlas/meridians.js"
mer_src = mer_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_pts_block = """    // 3. Render Acupuncture Points (362 WHO Standard Points)
    if (!showPoints && !showSurfaceReference) {
      groupPoints.innerHTML = '';
    } else {
      let ptsHtml = '';
      for (const code in acuData.points) {"""

new_pts_block = """    // 3. Render Acupuncture Points (362 WHO Standard Points)
    if (!showPoints && !showSurfaceReference && !isComp) {
      groupPoints.innerHTML = '';
    } else {
      let ptsHtml = '';
      if (showPoints) {
        for (const code in acuData.points) {"""

if old_pts_block in mer_src:
    mer_src = mer_src.replace(old_pts_block, new_pts_block)
    # Add closing brace for if (showPoints)
    target_closing = """        }
      }
    // Comparative split badges and divider"""
    replacement_closing = """        }
      }
      }
    // Comparative split badges and divider"""
    mer_src = mer_src.replace(target_closing, replacement_closing)
    print("Patched points rendering conditional in meridians.js")

# Remove duplicated message listener blocks
old_dup_handlers = """    } else if (ev.data.action === 'toggle_surface_reference') {
      showSurfaceReference = Boolean(ev.data.enabled);
      const r = getRenderer();
      if (r) r.setSkinReference(showSurfaceReference);
      render();
    } else if (ev.data.action === 'set_render_mode') {
      const r = getRenderer();
      if (r) r.setRenderMode(ev.data.mode);
      render();
    } else if (ev.data.action === 'set_skin_opacity') {
      const r = getRenderer();
      if (r) r.setSkinOpacity(ev.data.opacity);
      render();
    } else if (ev.data.action === 'set_filter_meridian') {
      filterMeridian = ev.data.meridian || 'all';
      render();
    } else if (ev.data.action === 'toggle_surface_reference') {
      showSurfaceReference = Boolean(ev.data.enabled);
      const r = getRenderer();
      if (r) r.setSkinReference(showSurfaceReference);
      render();"""

new_dup_handlers = """    } else if (ev.data.action === 'toggle_surface_reference') {
      showSurfaceReference = Boolean(ev.data.enabled);
      const r = getRenderer();
      if (r) r.setSkinReference(showSurfaceReference);
      render();"""

if old_dup_handlers in mer_src:
    mer_src = mer_src.replace(old_dup_handlers, new_dup_handlers)
    print("Removed duplicate message listeners in meridians.js")

# Update window.__meridiansDebug export
old_debug = """  window.__meridiansDebug = {
    get acuData() { return acuData; },
    selectPoint,
  };"""

new_debug = """  window.__meridiansDebug = {
    get acuData() { return acuData; },
    selectPoint,
    render,
    setSurfaceReference: (on) => {
      showSurfaceReference = Boolean(on);
      const r = getRenderer();
      if (r) r.setSkinReference(showSurfaceReference);
      render();
    },
    setFilterMeridian: (code) => {
      filterMeridian = code || 'all';
      render();
    },
    setRenderMode: (mode) => {
      const r = getRenderer();
      if (r) r.setRenderMode(mode);
      render();
    }
  };"""

if old_debug in mer_src:
    mer_src = mer_src.replace(old_debug, new_debug)
    print("Updated window.__meridiansDebug in meridians.js")

mer_path.write_text(mer_src, encoding="utf-8")
print("meridians.js updated successfully.")
