# P9.4: FINAL ENGINEERING HANDOFF & TECHNICAL SYSTEM REFERENCE

**System:** MSK-Therapy-OS  
**Milestone:** P9.4 Definitive Meridian Atlas Data Correction & Anatomical Path Validation  
**Date:** October 2026  
**Engineering Leads:** Principal Computational Anatomy Engineer, Senior WebGL Architect, Python Backend Lead, Independent QA Lead  
**Status:** READY FOR PRODUCTION RELEASE  

---

## 1. MISSION CHARTER & ARCHITECTURAL OVERVIEW

Milestone P9.4 resolves the fundamental root-cause defect observed across previous iterations of the 3D Acupuncture Atlas:
> **The Fallacy of Zero-Residual Splines:** *Minimizing point-to-path residual ($\min \|P - \text{Path}\|_2 = 0.0000\text{ mm}$) does NOT guarantee anatomical fidelity if the underlying acupoint knots are anchored at erroneous coordinates.*

In legacy releases, 95% of acupoint positions in `acupuncture_3d.json` were unverified raycasts onto the BodyParts3D FJ2810 skin mesh, leading to anatomical displacements of up to 68 mm (such as inverted medial-lateral coordinates on the Kidney and Gallbladder channels).

P9.4 implements a mathematically grounded, reference-driven pipeline connecting:
$$\text{Authoritative Landmarks} \longrightarrow \text{Parametric WHO-Cun Rules} \longrightarrow \text{Topological Route Graph} \longrightarrow \text{Guarded Surface Spline} \longrightarrow \text{WebGL Rendering}$$

```
+-----------------------------------------------------------------------------------+
|                        CANONICAL OSTEOLOGICAL LANDMARKS                           |
|      (Trochanters, Epigastric Angle, Malleoli, Spinous Processes, Orbit, ASIS)     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|               ACUPOINT LOCALIZATION RULES ENGINE (WHO STANDARD)                   |
|           Class A (Audited Knots) | Class B (Parametric Rules) | Class D          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                   TOPOLOGICAL MERIDIAN ROUTE GRAPH (40 BRANCHES)                  |
|    Acupoint Anchors + Turning Waypoints + Corridor Waypoints + Explicit Gaps     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                CENTRIPETAL CATMULL-ROM SURFACE ENGINE (P9.3/P9.4)                 |
|       Tangential Continuity | Sagitta Lift (3.5 mm) | Skin Clearance (1.2 mm)     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     EDITABLE MERIDIAN QA STUDIO (WEBGL UI)                        |
|        Coverage Dashboard | Route Inspector | Revisions | Peer Reviews            |
+-----------------------------------------------------------------------------------+
```

---

## 2. CORE SYSTEM MODULES

### 2.1. Authoritative Acupoint Localization Rules (`msk_therapy_os/point_localization_rules.py`)
- Formalizes **68 authoritative parametric rules** based on the *WHO Standard Acupuncture Point Locations in the Western Pacific Region*.
- Key localization methodologies:
  1. `BONE_PROPORTIONAL`: Resolves points proportionally along standardized skeletal segments (e.g., ST36 at 3 cun below knee eye; SP6 at 3 cun above medial malleolus).
  2. `INTER_LANDMARK_RATIO`: Resolves points along anatomical segments connecting two audited bony landmarks (e.g., CV12 at 4/8 between umbilicus and sternocostal angle).
  3. `DIRECTIONAL_OFFSET`: Offsets from a primary landmark along surface normal or transverse axis (e.g., BL11 at 1.5 cun lateral to T1 spinous process; BL41 at 3.0 cun lateral).
  4. `TENDON_BORDER`: Locates points along palpated muscle or tendon boundaries (e.g., LU5 on biceps tendon border; PC6 between palmaris longus and flexor carpi radialis).
  5. `DEPRESSION_FOSSA`: Points anchored directly in osteological fossae (e.g., ST35 in lateral patellar depression; SI19 in tragus depression).

### 2.2. Authoritative Route Graph Engine (`msk_therapy_os/meridian_route_graph.py`)
- Partitions the 14 classical channels into **40 anatomical branches** (left, right, midline) with strict laterality parity.
- Decouples **acupoint knots** from **route waypoints**:
  - `ACUPOINT_ANCHOR`: Primary therapeutic points with zero residual ($0.0000\text{ mm}$).
  - `TURNING_WAYPOINT`: Guides splines around complex bone contours (e.g., 5 turning waypoints navigating the Gallbladder cranial loop around the ear).
  - `CORRIDOR_WAYPOINT`: Enforces smooth curvature along muscular corridors (e.g., deltopectoral groove, gastrocnemius belly).
  - `BRANCH_JUNCTION`: Explicit topological convergence knots (e.g., Bladder inner and outer columns meeting at BL40 in popliteal fossa).
  - `EXPLICIT_GAP`: Marks visceral or deep collaterals where cutaneous splines MUST NOT draw connecting chords (e.g., ST8 to ST9 across neck; KI10 to KI11 across pelvis; LR8 to LR13 across groin).

### 2.3. Surface Engine Integration (`msk_therapy_os/meridian_surface_engine.py`)
- Executes Centripetal Catmull-Rom interpolation ($\alpha = 0.5$) with:
  - Adaptive sampling ($4\text{--}16$ samples per segment, ensuring intra-segment vertex distance $< 35\text{ mm}$).
  - Parabolic sagitta lift ($h(s) = 4s(1-s)\Delta s^2 / (8R)$ capped at $3.5\text{ mm}$).
  - Uniform normal outward clearance ($1.2\text{ mm}$) to guarantee zero mesh penetration.
  - Multi-branch assembly preventing false inter-branch chords.

### 2.4. Spatial Resolver (`msk_therapy_os/spatial_resolver.py`)
- Emits hierarchical 4-tier data quality classes:
  - **CLASS_A:** Audited canonical point with measured residual and known anatomical landmark (18 points).
  - **CLASS_B:** Standard-derived point calculated via authoritative WHO parametric rule (52 points).
  - **CLASS_C:** Secondary literature or atlas consensus point.
  - **CLASS_D:** Geometric surface approximation from legacy dataset (292 points; strictly tagged with educational disclaimer and tolerance radius).

---

## 3. SQLITE DATABASE SCHEMA & MIGRATIONS

All meridian atlas tables are automatically provisioned during database initialization via `migrate_p9_4_meridian_atlas_tables(db)` in `msk_therapy_os/points.py`:

```sql
-- 1. Acupoint Localization Rules
CREATE TABLE IF NOT EXISTS acupoint_localization_rules (
    rule_id TEXT PRIMARY KEY,
    point_code TEXT NOT NULL UNIQUE,
    channel_code TEXT NOT NULL,
    method TEXT NOT NULL,
    reference_landmark_a TEXT NOT NULL,
    reference_landmark_b TEXT,
    bone_segment_id TEXT,
    ratio_from_a REAL,
    cun_offset_lateral REAL DEFAULT 0.0,
    cun_offset_longitudinal REAL DEFAULT 0.0,
    region TEXT NOT NULL,
    who_chapter_clause TEXT,
    tolerance_radius_mm REAL DEFAULT 3.0,
    anatomical_description TEXT,
    created_at TEXT NOT NULL
);

-- 2. Anatomical Point References (Master 362 catalog)
CREATE TABLE IF NOT EXISTS anatomical_point_references (
    point_code TEXT PRIMARY KEY,
    channel_code TEXT NOT NULL,
    name_zh TEXT NOT NULL,
    name_pinyin TEXT NOT NULL,
    name_en TEXT NOT NULL,
    quality_class TEXT NOT NULL,
    primary_landmark_id TEXT,
    fma_id TEXT,
    who_reference TEXT,
    tolerance_radius_mm REAL,
    is_audited INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 3. Meridian Route Graphs
CREATE TABLE IF NOT EXISTS meridian_route_graphs (
    channel_code TEXT PRIMARY KEY,
    channel_name_zh TEXT NOT NULL,
    channel_name_en TEXT NOT NULL,
    element TEXT NOT NULL,
    polarity TEXT NOT NULL,
    branch_count INTEGER NOT NULL,
    has_explicit_gaps INTEGER DEFAULT 0,
    notes TEXT
);

-- 4. Meridian Route Waypoints
CREATE TABLE IF NOT EXISTS meridian_route_waypoints (
    waypoint_id TEXT PRIMARY KEY,
    channel_code TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    sequence_order INTEGER NOT NULL,
    waypoint_type TEXT NOT NULL,
    waypoint_code TEXT NOT NULL,
    pos_x REAL NOT NULL,
    pos_y REAL NOT NULL,
    pos_z REAL NOT NULL,
    norm_x REAL NOT NULL,
    norm_y REAL NOT NULL,
    norm_z REAL NOT NULL,
    region TEXT NOT NULL,
    anatomical_structure TEXT,
    point_code TEXT,
    source_annotation TEXT,
    is_active INTEGER DEFAULT 1
);

-- 5. Meridian Route Revisions (Audit Trail)
CREATE TABLE IF NOT EXISTS meridian_route_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_code TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    waypoint_code TEXT NOT NULL,
    revision_type TEXT NOT NULL,
    old_pos_x REAL, old_pos_y REAL, old_pos_z REAL,
    new_pos_x REAL, new_pos_y REAL, new_pos_z REAL,
    clinical_justification TEXT NOT NULL,
    proposed_by TEXT NOT NULL,
    proposed_at TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING'
);

-- 6. Meridian Route Reviews (Peer Reviews)
CREATE TABLE IF NOT EXISTS meridian_route_reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    revision_id INTEGER NOT NULL REFERENCES meridian_route_revisions(revision_id),
    reviewer_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    comments TEXT,
    reviewed_at TEXT NOT NULL
);

-- 7. Meridian Geometry Validation
CREATE TABLE IF NOT EXISTS meridian_geometry_validation (
    validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_code TEXT NOT NULL,
    side TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    point_residual_max_mm REAL NOT NULL,
    point_residual_mean_mm REAL NOT NULL,
    mesh_clearance_min_mm REAL NOT NULL,
    discontinuous_jump_detected INTEGER DEFAULT 0,
    validation_passed INTEGER DEFAULT 1,
    details TEXT
);
```

---

## 4. REST API ENDPOINTS

All endpoints are hosted by `msk_therapy_os/server.py` and communicate via JSON:

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/api/atlas/meridians/coverage` | Returns live 361-point quality metrics, Class A/B/D counts, and per-channel breakdown | `200` |
| `GET` | `/api/atlas/meridians/route-graph` | Returns topological branches, waypoints, corridors, and explicit gap definitions | `200` |
| `POST` | `/api/atlas/meridians/revisions` | Submits a proposed waypoint move, addition, or gap toggle | `201`, `400` |
| `POST` | `/api/atlas/meridians/revisions/{id}/review` | Approves or rejects a revision with peer review comments | `200`, `400`, `404` |
| `POST` | `/api/atlas/meridians/revisions/{id}/rollback` | Rolls back an approved revision, restoring original coordinates | `200`, `400`, `404` |

### Sample Revision Payload (`POST /api/atlas/meridians/revisions`)
```json
{
  "channel_code": "GB",
  "branch_id": "GB_R_B1_CRANIAL",
  "waypoint_code": "WP_GB_R_T2_SUPRA_AUR",
  "revision_type": "MOVE_WAYPOINT",
  "new_position": [0.0685, 1.6250, -0.0195],
  "clinical_justification": "Adjust supra-auricular curve 1.5 mm lateral to clear auricle helix rim",
  "proposed_by": "SeniorAnatomySpecialist"
}
```

---

## 5. FRONTEND: EDITABLE MERIDIAN QA STUDIO

Located in `msk_therapy_os/static/atlas/meridians.js`, the QA Studio panel `#p94MeridianStudioPanel` provides:
1. **Live Coverage Dashboard Widget:** Displays total points (361), Class A audited count, Class B WHO standard count, Class D approximation count, verified percentage, and real-time maximum residual ($0.000\text{ mm}$).
2. **Channel Route Topology Inspector:** Allows interactive browsing through all 14 classical channels, listing all constituent branches, corridors, and waypoints with coordinate displays.
3. **Interactive Waypoint Revision Form:** Enables anatomical clinicians to submit coordinates adjustments with mandatory clinical justification.
4. **Debug JavaScript APIs:** Exposed via `window.__meridiansDebug`:
   - `getCoverageDashboard()`: Fetches live coverage data.
   - `getRouteGraph(channel)`: Fetches route topology for any channel.
   - `submitRevision(revision)`: Submits new revision.
   - `reviewRevision(revId, decision, comments)`: Approves/rejects revision.
   - `rollbackRevision(revId)`: Rolls back revision.

---

## 6. VERIFICATION & REPRODUCIBILITY MATRIX

### 6.1. Test Suites
| Test Suite | File | Test Count | Result |
|---|---|---|---|
| **P9.4 Definitive Atlas** | `tests/test_p9_4_definitive_atlas.py` | 14 tests | **14 PASSED (100%)** |
| **P9.3 Geometry Correction** | `tests/test_p9_3_meridian_geometry.py` | 9 tests | **9 PASSED (100%)** |
| **P9.2 Spatial Resolver** | `tests/test_p9_2_dynamic_geometry_resolver.py` | 10 tests | **10 PASSED (100%)** |
| **Playwright Visual E2E** | `tests/test_p9_4_playwright_studio.py` | 1 test (5 assets) | **1 PASSED (100%)** |

### 6.2. Reproduction Commands
```powershell
# 1. Run all P9.4 core and API tests
python -m pytest tests/test_p9_4_definitive_atlas.py -v

# 2. Run P9.3 and P9.2 regression test suites
python -m pytest tests/test_p9_3_meridian_geometry.py tests/test_p9_2_dynamic_geometry_resolver.py -v

# 3. Run Playwright E2E visual screenshot generation
python -m pytest tests/test_p9_4_playwright_studio.py -v
```

---

## 7. SAFETY, ETHICAL & CLINICAL DEMARCATION

1. **Zero Curative Claims:** The 3D Atlas is strictly an educational and visual spatial reference tool. It does not provide medical diagnoses, treatment prescriptions, or therapeutic efficacy claims.
2. **Non-Invasive Visual Demarcation:** All trajectories are rendered with explicit visual disclaimers. Points with Class D approximations display prominent visual warnings and tolerance halos.
3. **Immutable Reference Checksums:** `acupuncture_3d.json` SHA-256 checksum is locked in `CANONICAL_REFERENCE_CHECKSUMS`. All calibrations are additive and transparently stored in SQLite.

---

## 8. DEPLOYMENT & MAINTENANCE RUNBOOK

1. **Database Bootstrap:**
   When spinning up a new instance, ensure `open_db()` is called with a writable SQLite path. `init_points_tables(db)` will automatically invoke `migrate_p9_4_meridian_atlas_tables(db)` and seed all 68 rules, 362 reference points, and 100+ waypoints.
2. **Adding New Parametric Rules:**
   To add a rule for a remaining Class D point, append an `AcupointLocalizationRule` entry in `msk_therapy_os/point_localization_rules.py` referencing standard `WHO_BONE_SEGMENTS` and `CANONICAL_LANDMARKS`. The system will automatically promote the point to Class B on the next query.
3. **Updating Waypoints in Field:**
   Use the QA Studio UI or POST `/api/atlas/meridians/revisions` $\to$ POST `/review`. The active waypoints in SQLite are updated immediately, and the `MeridianSurfacePathEngine` will dynamically re-route splines upon the next render pass.
