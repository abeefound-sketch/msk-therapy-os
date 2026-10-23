/**
 * M5 Reference Anatomy Layering & Discrete Slicing
 * Manages discrete tissue layer visibility, opacities, and planar slicing.
 */

const TissueLayersModule = (() => {
  let layerCatalog = null;
  let userConfig = [];

  async function init() {
    try {
      const catRes = await fetch('/api/anatomy/layers');
      if (catRes.ok) {
        layerCatalog = await catRes.json();
      }
      const cfgRes = await fetch('/api/anatomy/layers/config');
      if (cfgRes.ok) {
        userConfig = await cfgRes.json();
      }
      renderUI();
    } catch (err) {
      console.warn('[TissueLayers] Failed to initialize layers:', err);
    }
  }

  function renderUI() {
    const container = document.getElementById('tissueLayersContent');
    if (!container || !layerCatalog) return;

    let html = `
      <div style="font-size:11px; color:#cbd5e1; margin-bottom:8px; line-height:1.4; background:rgba(239,68,68,0.1); border-left:3px solid #ef4444; padding:6px 8px; border-radius:3px;">
        <strong>Legal & Clinical Notice:</strong> ${layerCatalog.disclaimer}
      </div>
      <div style="display:flex; flex-direction:column; gap:8px;">
    `;

    for (const [key, meta] of Object.entries(layerCatalog.layers)) {
      const cfg = userConfig.find(c => c.layer_name === key) || {
        opacity: meta.default_opacity,
        is_visible: meta.default_opacity > 0 ? 1 : 0,
        slice_plane: 'none',
        slice_offset: 0.0
      };

      html += `
        <div style="background:#1e293b; padding:8px; border-radius:4px; border:1px solid #334155;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <label style="cursor:pointer; display:flex; align-items:center; gap:6px; font-weight:600; color:#38bdf8;">
              <input type="checkbox" id="tl_chk_${key}" ${cfg.is_visible ? 'checked' : ''} onchange="TissueLayersModule.updateLayer('${key}')" />
              <span>${meta.display_name}</span>
            </label>
            <span style="font-size:10px; color:#94a3b8;">${(meta.fma_ids || []).join(', ')}</span>
          </div>
          <div style="font-size:10px; color:#94a3b8; margin-bottom:6px;">${meta.description}</div>
          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; align-items:center;">
            <div style="display:flex; align-items:center; gap:6px;">
              <span style="font-size:10px; color:#94a3b8;">Opacity:</span>
              <input type="range" id="tl_rng_${key}" min="0" max="100" value="${Math.round(cfg.opacity * 100)}" oninput="TissueLayersModule.onOpacityInput('${key}', this.value)" onchange="TissueLayersModule.updateLayer('${key}')" style="flex:1; cursor:pointer;" />
              <span id="tl_lbl_${key}" style="font-size:10px; width:30px; text-align:right;">${Math.round(cfg.opacity * 100)}%</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
              <span style="font-size:10px; color:#94a3b8;">Slice:</span>
              <select id="tl_sel_plane_${key}" onchange="TissueLayersModule.updateLayer('${key}')" style="background:#0f172a; color:#e2e8f0; font-size:10px; border:1px solid #475569; border-radius:3px; padding:2px;">
                <option value="none" ${cfg.slice_plane === 'none' ? 'selected' : ''}>None</option>
                <option value="axial" ${cfg.slice_plane === 'axial' ? 'selected' : ''}>Axial (Z)</option>
                <option value="sagittal" ${cfg.slice_plane === 'sagittal' ? 'selected' : ''}>Sagittal (X)</option>
                <option value="coronal" ${cfg.slice_plane === 'coronal' ? 'selected' : ''}>Coronal (Y)</option>
              </select>
              <input type="range" id="tl_rng_slice_${key}" min="-100" max="100" value="${Math.round(cfg.slice_offset * 100)}" onchange="TissueLayersModule.updateLayer('${key}')" style="flex:1; cursor:pointer;" title="Slice plane offset" />
            </div>
          </div>
        </div>
      `;
    }

    html += `</div>`;
    container.innerHTML = html;
  }

  function onOpacityInput(key, val) {
    const lbl = document.getElementById(`tl_lbl_${key}`);
    if (lbl) lbl.textContent = `${val}%`;
  }

  async function updateLayer(key) {
    const chk = document.getElementById(`tl_chk_${key}`);
    const rng = document.getElementById(`tl_rng_${key}`);
    const plane = document.getElementById(`tl_sel_plane_${key}`);
    const slice = document.getElementById(`tl_rng_slice_${key}`);

    const is_visible = chk ? chk.checked : true;
    const opacity = rng ? parseFloat(rng.value) / 100.0 : 1.0;
    const slice_plane = plane ? plane.value : 'none';
    const slice_offset = slice ? parseFloat(slice.value) / 100.0 : 0.0;

    const payload = {
      layer_name: key,
      opacity: opacity,
      is_visible: is_visible,
      slice_plane: slice_plane,
      slice_offset: slice_offset
    };

    try {
      const res = await fetch('/api/anatomy/layers/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        // Forward command to Atlas iframe if available
        if (typeof window.atlasCommand === 'function') {
          window.atlasCommand('set_layer_opacity', { layer: key, opacity: opacity, visible: is_visible });
          if (slice_plane !== 'none') {
            window.atlasCommand('set_slice_plane', { plane: slice_plane, offset: slice_offset });
          }
        }
      }
    } catch (err) {
      console.error('[TissueLayers] Failed to persist layer config:', err);
    }
  }

  return {
    init,
    updateLayer,
    onOpacityInput
  };
})();

window.TissueLayersModule = TissueLayersModule;
window.toggleTissueLayersModal = function() {
  const modal = document.getElementById('tissueLayersModal');
  if (!modal) return;
  const isHidden = modal.style.display === 'none' || !modal.style.display;
  modal.style.display = isHidden ? 'block' : 'none';
};
document.addEventListener('DOMContentLoaded', () => {
  TissueLayersModule.init();
});
