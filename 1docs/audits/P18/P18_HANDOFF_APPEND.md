# MSK-Therapy-OS — Milestone P18 Append-Only Engineering Handoff

**Handoff Timestamp:** 2026-10-31T23:59:00+07:00  
**Active Branch:** `fix/p18-meridian-anatomical-geometry`  
**Baseline Commit:** `877450c`  
**Classification:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Summary of Completed Remediation Work

1. **Reconciliation of Spatial Divergence (Audit Findings #2 & #3):**
   - Executed exhaustive pairwise Euclidean comparison of all 362 points between baked static JSON and the canonical spatial resolver via `tools/forensics/compare_spatial_sources.py`.
   - Documented exact discrepancy counts: 28 points $\ge 100\text{ mm}$, 130 points $\ge 50\text{ mm}$, with maximum discrepancy on KI3 ($175.45\text{ mm}$).
   - Discovered root cause: Baked JSON coordinates represent authentic face raycasts on `fj2810_softened.bin` ($<0.15\text{ mm}$ error), whereas canonical coordinates were uncalibrated proportional B-cun approximations (LI4 floated 9.2 mm outside the body bounding box; ST36 floated 4.5 cm anterior to the leg surface).
   - Generated authoritative audit artifacts: `1docs/audits/P18/P18_ACUPOINT_RECONCILIATION.csv` and `.json`.
   - Harmonized runtime API in `msk_therapy_os/server.py` (`GET /api/acupuncture-3d`) to enrich base points with canonical resolver attributes and active SQLite overrides while preserving on-disk file checksums.

2. **Removal of Synthetic Upstream Offsets (Audit Finding #4):**
   - Removed hardcoded constants ($dx=-0.008, dy=0.012, dz=-0.010$) from `msk_therapy_os/spatial_resolver.py:530–544`.
   - Implemented fail-closed response returning unshifted legacy coordinates with status `UPSTREAM_TRANSFORM_UNAVAILABLE` and explicit rejection reason.
   - Updated `tests/test_p9_2_dynamic_geometry_resolver.py` to assert the updated governance contract.

3. **Meridian Engine Cache Invalidation (Audit Finding #6):**
   - Fixed cache key in `msk_therapy_os/meridian_surface_engine.py` by incorporating a 16-hex SHA-256 digest of ordered point codes, coordinates, and normal vectors.
   - Verified that mutating point coordinates immediately forces path recalculation.

4. **Quality Tier Governance & Taxonomy (Audit Finding #8):**
   - Created `msk_therapy_os/geometry_contracts.py` establishing `AcupointQualityTier` (`CLASS_A`, `CLASS_B`, `CLASS_D`, `CLASS_E`, `UNAVAILABLE`) and `MeshIdentity`.
   - Replaced hardcoded `"CLASS_B"` promotion in `spatial_resolver.py:475` with `rule_res.get("quality_class", "CLASS_B")`.

5. **Procedural Fallback Transparency (Audit Finding #1 & #10):**
   - In `msk_therapy_os/static/atlas/app.js`, bound `atlas.isProceduralFallback` and added a prominent persistent banner warning users when the procedural demo mannequin is active.
   - In `msk_therapy_os/static/atlas/meridians.js`, updated the QA inspector to display `OCCLUSION_APPROXIMATE (Normal-facing / Raycast; WebGL depth buffer unbound)`.

6. **Documentation & Verification:**
   - Authored all 6 mandatory audit documents in `1docs/audits/P18/`.
   - Created comprehensive verification test suite `tests/test_p18_geometry_remediation.py` validating Gates G0 through G7.

---

### 2. File Modification & Creation Manifest

- **Created Files:**
  - `msk_therapy_os/geometry_contracts.py`
  - `tools/forensics/compare_spatial_sources.py`
  - `tests/test_p18_geometry_remediation.py`
  - `1docs/audits/P18/P18_ACUPOINT_RECONCILIATION.csv`
  - `1docs/audits/P18/P18_ACUPOINT_RECONCILIATION.json`
  - `1docs/audits/P18/P18_ANATOMICAL_ROOT_CAUSE.md`
  - `1docs/audits/P18/P18_MESH_ASSET_PROVENANCE.md`
  - `1docs/audits/P18/P18_ROUTE_TOPOLOGY_AND_SURFACE_QA.md`
  - `1docs/audits/P18/P18_EXTERNAL_REFERENCE_LICENSES.md`
  - `1docs/audits/P18/P18_TEST_AND_RELEASE_MATRIX.md`
  - `1docs/audits/P18/P18_HANDOFF_APPEND.md`
- **Modified Files:**
  - `msk_therapy_os/meridian_surface_engine.py` (cache digest)
  - `msk_therapy_os/spatial_resolver.py` (upstream governance, quality tier)
  - `msk_therapy_os/server.py` (reconciled `/api/acupuncture-3d`)
  - `msk_therapy_os/static/atlas/app.js` (fallback banner)
  - `msk_therapy_os/static/atlas/meridians.js` (inspector occlusion & mesh label)
  - `tests/test_p9_2_dynamic_geometry_resolver.py` (governance assertion)

---

### 3. Verification Instructions for Successor Agent

Run the following commands to verify:
```bash
# 1. P18 Remediation Verification
pytest tests/test_p18_geometry_remediation.py -v

# 2. P9 Resolver Regression
pytest tests/test_p9_2_dynamic_geometry_resolver.py -v

# 3. Full Non-Playwright Regression Suite
pytest -m "not playwright"
```
