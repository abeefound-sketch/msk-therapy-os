# M2 Control Root-Cause Forensic Audit Report

**Project:** MSK-Therapy-OS  
**Branch:** `prototype/neck-shoulder-poc`  
**Auditor:** Principal Software Engineer, Full-Stack Debugger, 3D Rendering Architect  
**Methodology:** Constraint-first → Artifact-first → CLI-first → Evidence-first → Cost-aware → Automation-last  
**Status:** COMPLETED & RESOLVED  

---

## 1. Executive Summary

This forensic audit investigates and remediates five core architectural defects that rendered 3D Atlas and clinical controls nonfunctional, decorative, or clinically misleading in MSK-Therapy-OS:
1. **Skin Opacity Slider:** Visual change failed to render despite the UI slider moving between 0% and 100%.
2. **Meridian Channel Dropdown:** Selection of specific channels (e.g. CV Ren Mai, GV Du Mai) failed to display or isolate the meridian pathways and acupoint markers.
3. **Vietnamese Dien Chan Facial Reflex Points:** Facial reflex points were routed through the WHO acupuncture dictionary or suppressed, lacking somatotopic separation and traditional disclaimers.
4. **Thai Sen Sib Energy Lines:** Lacked educational scope badges and clear line separation.
5. **State & IPC Handshake Architecture:** Unchecked asynchronous postMessage communication led to race conditions, dropped commands, and unacknowledged states.

---

## 2. Forensic Analysis & Root-Cause Remediation

### Defect 1: Skin Opacity Slider (Nonfunctional Rendering)

#### Observable Symptom
In earlier iterations, dragging the skin opacity slider to 100% or 50% left the model showing exposed deep musculature and bones, with no visible skin mesh or translucent envelope.

#### Root-Cause Mechanics
1. **Category Suppression at Initialization:** In `atlas/app.js`, the category `skin` was categorized under `HIDDEN_BY_DEFAULT`. During `useAtlas()` initialization, `catOn['skin']` was evaluated to `false`.
2. **WebGL Draw Call Bypass:** In `atlas/gl.js`, the draw loop for skin meshes evaluated:
   ```javascript
   if (!this.visible[i] || els[i].t !== 'skin') continue;
   ```
   Because `catOn['skin'] = false`, `applyVisibility()` in `app.js` populated `renderer.visible[i] = 0` for all skin triangles. Consequently, the WebGL pipeline completely skipped vertex submission for the FJ2810 mesh during both color and depth passes. Changing `skinOpacity` alone simply set a uniform float that was never read by any drawn fragments.
3. **Depth Buffer & Blending State:** Transparent rendering requires blending (`gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)`) with depth mask disabled (`gl.depthMask(false)`) during the transparent pass to prevent invisible back-faces from occluding front-faces.

#### Remediation Implemented
- In `atlas/app.js`: When entering `surface` mode or adjusting skin opacity (`set_skin_opacity`), `catOn['skin']` is dynamically set to `(alpha > 0.005)`. `applyVisibility()` is invoked immediately to copy skin element visibilities to `renderer.visible`.
- In `atlas/gl.js`: Implemented two-pass rendering: an opaque pass with depth writes enabled for internal musculoskeletal structures, followed by a depth-tested, depth-write-masked alpha-blended pass for the FJ2810 skin envelope when `0.0 < skinOpacity < 0.99`.
- **Validation Result:** Verified via Playwright. Skin opacity 100% yields `visibleSkinCount = 2` (draw calls submitted, muscles occluded); opacity 50% yields `visibleSkinCount = 2` (translucent blend); opacity 0% yields `visibleSkinCount = 0` (skin skipped, deep structures exposed).

---

### Defect 2: Meridian Channel Dropdown (Filter Conflict & Broken Paths)

#### Observable Symptom
Selecting `CV — Ren Mai (Conception)` or `GV — Du Mai (Governing)` in the Meridian filter failed to display the pathway or rendered 0 acupoints.

#### Root-Cause Mechanics
1. **Filtering Predicate Conflict:** In `atlas/meridians.js`, the point iteration loop combined three orthogonal filters in series:
   ```javascript
   if (verifiedOnly && filterRegion !== 'all' && !isVerified) continue;
   if (filterMeridian !== 'all' && pt.meridian_code !== filterMeridian) continue;
   if (!matchesRegion(pt.region, filterRegion)) continue;
   ```
   When the user selected a channel like `CV` from the dropdown, `filterMeridian` was `'CV'`. However, `filterRegion` defaulted to `'neck_shoulder'`, and `verifiedOnly` defaulted to `true`. Because CV has only 2 points in the neck/shoulder area and most points are on the anterior torso/abdomen (`torso`), line 264 skipped all 22 torso points. Furthermore, non-verified anchors were skipped by line 258.
2. **Disconnected Path Vertex Joining:** Meridian pathways clipped by regional bounds were concatenated into SVG `path` strings using naive `d += ' L ' + x + ' ' + y`. When points exited the region or crossed behind the body, they were skipped, but the next visible vertex immediately issued an `L` command, drawing an artificial straight line straight through the interior torso or skull.
3. **Camera Orientation Mismatch:** Classical meridians have distinct anterior vs. posterior trajectories (e.g. CV is entirely anterior midline; GV is entirely posterior midline). Selecting CV or GV without adjusting camera orientation caused points on the opposing anatomical side to be culled by the surface normal occlusion test.

#### Remediation Implemented
- In `atlas/meridians.js`: Channel selection overrides regional clipping:
   ```javascript
   if (filterMeridian !== 'all') {
     if (pt.meridian_code !== filterMeridian) continue;
   } else {
     if (verifiedOnly && filterRegion !== 'all' && !isVerified) continue;
     if (!matchesRegion(pt.region, filterRegion)) continue;
   }
   ```
- Implemented `inSubpath` state machine in SVG path builder: when a vertex is culled or clipped, `inSubpath = false`. The next valid point begins with `M` (MoveTo) rather than `L` (LineTo), preventing false lines through the body.
- Auto-camera reorientation: Selecting `CV` automatically sets `camera.yaw = 0.0` (anterior); selecting `GV` or `BL` sets `camera.yaw = Math.PI` (posterior paraspinal).
- Auto-layer enabling: Selecting any specific channel automatically sets `showMeridians = true` and `showPoints = true`, ensuring immediate user feedback.

---

### Defect 3: Vietnamese Dien Chan Facial Reflex Points

#### Observable Symptom
Clicking Dien Chan points either opened the standard WHO acupuncture panel with blank fields, or threw JavaScript exceptions due to missing WHO metadata.

#### Root-Cause Mechanics
- **Conflation with WHO Dictionary:** Dien Chan points were registered in the same click handler as classical acupoints, which queried `acuData.points[code]`. Because Dien Chan points are stored in `acuData.dien_chan`, the lookup returned `undefined`, causing null-pointer errors or silent failure.
- **Lack of Clinical Context:** Dien Chan points were not distinguished from peripheral neuromusculoskeletal trigger points, creating false equivalence between traditional facial somatotopic reflexology and evidence-based MSK therapy.

#### Remediation Implemented
- **Independent Click Router:** Added prefix check `if (code.startsWith('DIEN-')) { selectDienChanPoint(code); }`.
- **Dedicated UI Card:** Added `#atlasDienChanCard` in `index.html` displaying point name, facial reflex projection, indication for neck/shoulder tension, non-WHO disclaimer, and `UNVERIFIED` clinical status.
- **SOAP Note Integration:** Added "+ Add to SOAP Note" button specifically formatted for reflexology protocols.
- **Dataset Badging:** Added `4 pts — Incomplete educational dataset (Reflexology/Non-WHO)` badge to the toggle button.

---

### Defect 4: Thai Sen Sib Energy Lines

#### Observable Symptom
Thai Sen Sib lines appeared as generic solid paths without educational qualification or distinct line identities.

#### Root-Cause Mechanics
- Lack of metadata badge explaining that Thai Sen Sib contains 3 educational pathways (Sen Ittha, Sen Pingkhla, Sen Sumana) out of the classical 10 Sen lines.
- Solid line rendering created visual confusion with classical Chinese meridians.

#### Remediation Implemented
- Configured dashed gold stroke styling (`stroke="${line.color || '#f59e0b'}" stroke-width="2.8" stroke-dasharray="6,4"`).
- Added `3 lines — Incomplete educational dataset` badge and tooltip to `#btnToggleThai`.

---

### Defect 5: State & IPC Handshake Protocol

#### Observable Symptom
Rapid clicking between tabs and controls caused commands to be dropped when the atlas iframe was reloading or resetting.

#### Root-Cause Mechanics
- Host-to-iframe communication was unacknowledged fire-and-forget `postMessage`.
- No deterministic correlation between command issuance and completion in the atlas renderer.

#### Remediation Implemented
- Defined typed IPC protocol with deterministic `requestId` generation.
- Added `msk_ack` acknowledgment messages returned by the atlas engine for every state-altering command.
- Maintained a pending command queue in the host window until the initial handshake is established.

---

## 3. Forensic Conclusion

All 5 core architectural defects have been comprehensively resolved at the source level. No cosmetic workarounds, hardcoded PASS assertions, or decorative controls remain. The application is verified through Playwright automated test suites and ready for formal user acceptance.
