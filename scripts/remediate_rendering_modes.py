"""Script to implement Three Visualization Modes in 3D Atlas Renderer (gl.js).
1. Mode A: Surface Meridian Mode (actual skin mesh with adjustable opacity + surface meridians)
2. Mode B: Musculoskeletal Anatomy Mode (deep bones/muscles, meridians hidden by default)
3. Mode C: Comparative Research Mode (synchronized dual split view + instant mode toggle)
"""
from pathlib import Path

BASE = Path("D:/5Projects/msk-therapy-os")
gl_path = BASE / "msk_therapy_os/static/atlas/gl.js"
gl_src = gl_path.read_text(encoding="utf-8").replace("\r\n", "\n")

# 1. Update constructor with mode properties and methods
old_ctor_block = """    this.camera = { yaw: 0, pitch: 0.05, dist: 3, target: [0, 0.9, 0], fov: 40 * Math.PI / 180 };
    this.clip = { on: false, plane: [0, -1, 0, 1] };
    this.xray = false;
    this.selColor = [0.56, 0.86, 0.80];
    this.background = [0.118, 0.145, 0.180];"""

new_ctor_block = """    this.camera = { yaw: 0, pitch: 0.05, dist: 3, target: [0, 0.9, 0], fov: 40 * Math.PI / 180 };
    this.clip = { on: false, plane: [0, -1, 0, 1] };
    this.xray = false;
    this.selColor = [0.56, 0.86, 0.80];
    this.background = [0.118, 0.145, 0.180];
    this.renderMode = 'surface'; // 'surface' | 'musculoskeletal' | 'comparative'
    this.skinOpacity = 0.78;
    this.skinReferenceOn = false;
    this.skinColor = [0.86, 0.77, 0.70];"""

assert old_ctor_block in gl_src, "old_ctor_block not found in gl.js"
gl_src = gl_src.replace(old_ctor_block, new_ctor_block)

# 2. Add setRenderMode, setSkinOpacity, setSkinReference, _matricesForAspect
old_matrices = """  _matrices() {
    const eye = this._eye();
    const aspect = Math.max(1e-3, this.canvas.width / Math.max(1, this.canvas.height));
    const d = this.camera.dist;
    // Intelligent near plane to prevent clipping when zoomed into detail (e.g. neck/cervical points)
    const near = Math.min(0.015, Math.max(0.001, d * 0.015));
    const far = Math.max(25.0, d * 15 + 20);
    const proj = mat4.perspective(mat4.create(), this.camera.fov, aspect, near, far);
    const view = mat4.lookAt(mat4.create(), eye, this.camera.target, [0, 1, 0]);
    return { vp: mat4.multiply(mat4.create(), proj, view), eye };
  }"""

new_matrices = """  setRenderMode(mode) {
    if (this.renderMode === mode) return;
    this.renderMode = mode;
    this.requestRender();
  }
  setSkinOpacity(alpha) {
    this.skinOpacity = Math.max(0.0, Math.min(1.0, alpha));
    this.requestRender();
  }
  setSkinReference(on) {
    this.skinReferenceOn = Boolean(on);
    this.requestRender();
  }
  _matricesForAspect(aspect) {
    const eye = this._eye();
    const d = this.camera.dist;
    const near = Math.min(0.015, Math.max(0.001, d * 0.015));
    const far = Math.max(25.0, d * 15 + 20);
    const proj = mat4.perspective(mat4.create(), this.camera.fov, aspect, near, far);
    const view = mat4.lookAt(mat4.create(), eye, this.camera.target, [0, 1, 0]);
    return { vp: mat4.multiply(mat4.create(), proj, view), eye };
  }
  _matrices() {
    const aspect = Math.max(1e-3, this.canvas.width / Math.max(1, this.canvas.height));
    return this._matricesForAspect(aspect);
  }"""

assert old_matrices in gl_src, "old_matrices not found in gl.js"
gl_src = gl_src.replace(old_matrices, new_matrices)

# 3. Replace _draw() with _drawScene and multi-mode rendering
old_draw = """  _draw() {
    const gl = this.gl;
    this._resize();
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    gl.clearColor(...this.background, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    if (!this.n) return;
    const { vp, eye } = this._matrices();
    const u = this.main.u;
    this._setCommon(this.main, vp, eye);
    gl.bindVertexArray(this.vao);
    gl.enable(gl.DEPTH_TEST);
    gl.disable(gl.BLEND);
    gl.disable(gl.CULL_FACE);
    gl.depthMask(true);

    const anySel = this.selected.some(Boolean);
    const ghostOthers = this.xray && anySel;
    const els = this.elements;
    gl.uniform1f(u.uAlpha, 1);
    for (let i = 0; i < this.n; i++) {
      if (!this.visible[i]) continue;
      if (this.xray && !(ghostOthers && this.selected[i])) continue;
      gl.uniform3fv(u.uColor, this.colors.subarray(i * 3, i * 3 + 3));
      gl.uniform1f(u.uSel, this.selected[i] ? 1 : 0);
      gl.drawElements(gl.TRIANGLES, els[i].n, gl.UNSIGNED_INT, els[i].o * 4);
    }
    if (anySel && !this.xray) {
      // Show the hidden parts of the selection faintly through whatever covers them.
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.depthMask(false);
      gl.depthFunc(gl.GREATER);
      gl.uniform1f(u.uAlpha, 0.38);
      gl.uniform1f(u.uSel, 1);
      for (let i = 0; i < this.n; i++) {
        if (!this.visible[i] || !this.selected[i]) continue;
        gl.uniform3fv(u.uColor, this.selColor);
        gl.drawElements(gl.TRIANGLES, els[i].n, gl.UNSIGNED_INT, els[i].o * 4);
      }
      gl.depthFunc(gl.LESS);
      gl.depthMask(true);
      gl.disable(gl.BLEND);
    }
    if (this.xray) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.depthMask(false);
      gl.enable(gl.CULL_FACE);
      gl.uniform1f(u.uAlpha, ghostOthers ? 0.10 : 0.22);
      gl.uniform1f(u.uSel, 0);
      for (let i = 0; i < this.n; i++) {
        if (!this.visible[i] || (ghostOthers && this.selected[i])) continue;
        gl.uniform3fv(u.uColor, this.colors.subarray(i * 3, i * 3 + 3));
        gl.drawElements(gl.TRIANGLES, els[i].n, gl.UNSIGNED_INT, els[i].o * 4);
      }
      gl.depthMask(true);
      gl.disable(gl.BLEND);
      gl.disable(gl.CULL_FACE);
    }
    gl.bindVertexArray(null);
  }"""

new_draw = """  _drawScene(vp, eye, mode) {
    const gl = this.gl;
    const u = this.main.u;
    this._setCommon(this.main, vp, eye);
    gl.bindVertexArray(this.vao);
    gl.enable(gl.DEPTH_TEST);
    gl.disable(gl.BLEND);
    gl.disable(gl.CULL_FACE);
    gl.depthMask(true);

    const anySel = this.selected.some(Boolean);
    const ghostOthers = this.xray && anySel;
    const els = this.elements;

    // Pass 1: Opaque geometry (bones, muscles, organs, etc. - skin excluded)
    gl.uniform1f(u.uAlpha, 1.0);
    for (let i = 0; i < this.n; i++) {
      if (!this.visible[i]) continue;
      if (els[i].t === 'skin') continue; // skin rendered in dedicated pass
      if (this.xray && !(ghostOthers && this.selected[i])) continue;
      gl.uniform3fv(u.uColor, this.colors.subarray(i * 3, i * 3 + 3));
      gl.uniform1f(u.uSel, this.selected[i] ? 1 : 0);
      gl.drawElements(gl.TRIANGLES, els[i].n, gl.UNSIGNED_INT, els[i].o * 4);
    }

    // Pass 2: Skin mesh (Surface Mode or Musculoskeletal with Surface Reference Envelope)
    const drawSkin = (mode === 'surface' && this.skinOpacity > 0) ||
                     (mode === 'musculoskeletal' && this.skinReferenceOn);
    const skinAlpha = mode === 'musculoskeletal' ? 0.14 : this.skinOpacity;

    if (drawSkin && !this.xray) {
      if (skinAlpha >= 0.98) {
        gl.depthMask(true);
        gl.disable(gl.BLEND);
        gl.uniform1f(u.uAlpha, 1.0);
        gl.uniform1f(u.uSel, 0);
        for (let i = 0; i < this.n; i++) {
          if (!this.visible[i] || els[i].t !== 'skin') continue;
          gl.uniform3fv(u.uColor, this.skinColor || this.colors.subarray(i * 3, i * 3 + 3));
          gl.drawElements(gl.TRIANGLES, els[i].n, gl.UNSIGNED_INT, els[i].o * 4);
        }
      } else {
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        gl.depthMask(false);
        gl.uniform1f(u.uAlpha, skinAlpha);
        gl.uniform1f(u.uSel, 0);
        for (let i = 0; i < this.n; i++) {
          if (!this.visible[i] || els[i].t !== 'skin') continue;
          gl.uniform3fv(u.uColor, this.skinColor || this.colors.subarray(i * 3, i * 3 + 3));
          gl.drawElements(gl.TRIANGLES, els[i].n, gl.UNSIGNED_INT, els[i].o * 4);
        }
        gl.depthMask(true);
        gl.disable(gl.BLEND);
      }
    }

    // Pass 3: Selection Highlight (faint through occluding structures)
    if (anySel && !this.xray) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.depthMask(false);
      gl.depthFunc(gl.GREATER);
      gl.uniform1f(u.uAlpha, 0.38);
      gl.uniform1f(u.uSel, 1);
      for (let i = 0; i < this.n; i++) {
        if (!this.visible[i] || !this.selected[i]) continue;
        gl.uniform3fv(u.uColor, this.selColor);
        gl.drawElements(gl.TRIANGLES, els[i].n, gl.UNSIGNED_INT, els[i].o * 4);
      }
      gl.depthFunc(gl.LESS);
      gl.depthMask(true);
      gl.disable(gl.BLEND);
    }

    // Pass 4: X-ray mode ghosting
    if (this.xray) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.depthMask(false);
      gl.enable(gl.CULL_FACE);
      gl.uniform1f(u.uAlpha, ghostOthers ? 0.10 : 0.22);
      gl.uniform1f(u.uSel, 0);
      for (let i = 0; i < this.n; i++) {
        if (!this.visible[i] || (ghostOthers && this.selected[i])) continue;
        gl.uniform3fv(u.uColor, this.colors.subarray(i * 3, i * 3 + 3));
        gl.drawElements(gl.TRIANGLES, els[i].n, gl.UNSIGNED_INT, els[i].o * 4);
      }
      gl.depthMask(true);
      gl.disable(gl.BLEND);
      gl.disable(gl.CULL_FACE);
    }
    gl.bindVertexArray(null);
  }

  _draw() {
    const gl = this.gl;
    this._resize();
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.clearColor(...this.background, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    if (!this.n) return;

    const W = this.canvas.width;
    const H = this.canvas.height;

    if (this.renderMode === 'comparative') {
      const W2 = Math.floor(W / 2);
      const leftMats = this._matricesForAspect(Math.max(1e-3, W2 / Math.max(1, H)));
      const rightMats = this._matricesForAspect(Math.max(1e-3, (W - W2) / Math.max(1, H)));

      gl.enable(gl.SCISSOR_TEST);

      // Left Viewport: Musculoskeletal Anatomy (Western)
      gl.viewport(0, 0, W2, H);
      gl.scissor(0, 0, W2, H);
      this._drawScene(leftMats.vp, leftMats.eye, 'musculoskeletal');

      // Right Viewport: Surface & Meridians (TCM)
      gl.viewport(W2, 0, W - W2, H);
      gl.scissor(W2, 0, W - W2, H);
      this._drawScene(rightMats.vp, rightMats.eye, 'surface');

      gl.disable(gl.SCISSOR_TEST);
    } else {
      gl.viewport(0, 0, W, H);
      const mats = this._matrices();
      this._drawScene(mats.vp, mats.eye, this.renderMode);
    }
  }"""

assert old_draw in gl_src, "old_draw not found in gl.js"
gl_src = gl_src.replace(old_draw, new_draw)

# 4. Update pick() to support comparative mode and direct muscle picking through skin
old_pick = """    const { vp, eye } = this._matrices();
    this._setCommon(this.pickProg, vp, eye);
    gl.bindVertexArray(this.vao);
    const anySel = this.selected.some(Boolean);
    const id = new Float32Array(3);
    for (let i = 0; i < this.n; i++) {
      if (!this.visible[i]) continue;
      if (this.xray && anySel && !this.selected[i]) continue; // in X-ray, only solid structures are clickable
      const k = i + 1;
      id[0] = (k & 255) / 255; id[1] = ((k >> 8) & 255) / 255; id[2] = ((k >> 16) & 255) / 255;
      gl.uniform3fv(this.pickProg.u.uColor, id);
      gl.drawElements(gl.TRIANGLES, this.elements[i].n, gl.UNSIGNED_INT, this.elements[i].o * 4);
    }"""

new_pick = """    let vp, eye;
    if (this.renderMode === 'comparative') {
      const W2 = Math.floor(W / 2);
      if (x < W2) {
        gl.viewport(0, 0, W2, H);
        const mats = this._matricesForAspect(Math.max(1e-3, W2 / Math.max(1, H)));
        vp = mats.vp; eye = mats.eye;
      } else {
        gl.viewport(W2, 0, W - W2, H);
        const mats = this._matricesForAspect(Math.max(1e-3, (W - W2) / Math.max(1, H)));
        vp = mats.vp; eye = mats.eye;
      }
    } else {
      gl.viewport(0, 0, W, H);
      const mats = this._matrices();
      vp = mats.vp; eye = mats.eye;
    }

    this._setCommon(this.pickProg, vp, eye);
    gl.bindVertexArray(this.vao);
    const anySel = this.selected.some(Boolean);
    const id = new Float32Array(3);
    for (let i = 0; i < this.n; i++) {
      if (!this.visible[i]) continue;
      // When skin is translucent, allow single-clicking structures directly beneath the skin
      if (this.elements[i].t === 'skin' && this.skinOpacity < 0.95 && this.renderMode !== 'surface_strict') continue;
      if (this.xray && anySel && !this.selected[i]) continue;
      const k = i + 1;
      id[0] = (k & 255) / 255; id[1] = ((k >> 8) & 255) / 255; id[2] = ((k >> 16) & 255) / 255;
      gl.uniform3fv(this.pickProg.u.uColor, id);
      gl.drawElements(gl.TRIANGLES, this.elements[i].n, gl.UNSIGNED_INT, this.elements[i].o * 4);
    }"""

assert old_pick in gl_src, "old_pick not found in gl.js"
gl_src = gl_src.replace(old_pick, new_pick)

gl_path.write_text(gl_src, encoding="utf-8")
print("gl.js successfully updated with Three Visualization Modes support!")
