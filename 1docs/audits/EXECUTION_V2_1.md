# Execution evidence — Roadmap V2.1 (2026-10-23)

**Source of truth:** user-supplied `msk-therapy-os-m3-roadmap-source.zip` (122 entries). All changes performed on an isolated extracted copy. The live Windows repository at `D:\5Projects\msk-therapy-os` could **not** be accessed: Local Coding Agent / Tunnel workspace call failed with HTTP 429. This bundle therefore **must be reviewed and merged**, not treated as a live commit. The ZIP contains no `.git` history, hence no valid SHA or deployment commit.

## Work completed in the local snapshot

1. `HANDOFF_ROADMAP_V2_1_CODING_AGENT.md` and `docs/ROADMAP_V2_1.md` with milestone names, dependencies, safety gates and HF token stop-rule.
2. **M2.9 vertical slice:** `msk_therapy_os/relationship_catalog.py` adds SQLite source-typed entities and edges, explicitly distinct anatomy organ and TCM channel, casefold/diacritic-tolerant search, relation reads, unknown Atlas mapping block. Additive tables wired via `db.py`, HTTP `/api/explore/search`, `/api/explore/entities/:id`, `/api/explore/relations`, read-only tab and safe-text JS.
3. **M2.10 partial vertical slice:** `research_studio.py` introduces research set/version/diagram/definition/finding tables; normalized 2D point/line/polygon coordinates; synthetic-only case/visit validation; source note; positive/assessed_negative/not_assessed; private ownership; generated fictional front/profile diagrams, public locked tutorial seed, read/write API (auth+CSRF required), point editor UI and timeline reads. **Not complete:** user image import, version fork/edit operations, CSV/JSON export/import, formal browser acceptance, source-review workflow and complete risk audit.
4. **HF Docker candidate:** `Dockerfile`, `.dockerignore`, `deploy/start-space.sh`, HF YAML header in README, `docs/HUGGINGFACE_DEPLOYMENT.md`. Read-only public mode rejects mutations (except stateless safety screening), non-local writable bind rejected. No Hugging Face token used; no Space created or pushed.
5. New test modules for M2.9/M2.10; no intentional edits of original Atlas/meridian/points assets. Original source spec documents are preserved under `docs/roadmap_sources/`.

## Actual verification

| Gate | Evidence / result | Verdict |
|---|---|---|
| M2.9 unit + HTTP | `python -m unittest discover -s tests -p test_relationship_explorer.py -v` = **6 / 6 pass** | PASS local |
| M2.10 unit + HTTP/security | `python -m unittest discover -s tests -p test_research_studio.py -q` = **7 / 7 pass** | PASS local |
| Local HTTP CRUD | Test login+CSRF, create private set with two bundled diagrams, save a point, anonymous user cannot see private set | PASS local |
| Public read-only API | GET query returns example; anonymous research POST returns **HTTP 403** with read-only enabled | PASS local |
| Full `unittest discover` | **92 tests** run in **54.0 seconds**, 1 FAIL + 2 ERROR, details below | NOT GREEN |
| Baseline comparison | Unmodified snapshot `tests/test_server.py` has the **same 1 FAIL + 1 ERROR** for absent BodyParts3D data. `tests/test_anatomical_workbench.py` requires missing `research.*` package and external dependencies | Known source gap |
| Syntax | Python `compileall`, Node `--check` for two new JS modules, HTMLParser on index passed | PASS static |
| Chromium E2E | Headless attempt timed out without a screenshot; no claimed UI-browser pass | BLOCKED |
| Docker build | Docker executable not installed here | BLOCKED |
| Physical Intel HD5500 FPS | Target laptop not connected | BLOCKED |
| Hugging Face upload | No authenticated upload attempted | NOT STARTED; no token requested |

### Unmodified baseline gaps (must not fabricate a 'regression')

- `tests/test_anatomical_workbench.py` imports `research.workbench` from unbundled project directory (and uses numpy/pytest, outside the stated zero-pip app). It cannot import from the provided source ZIP.
- `tests/test_server.py::test_get_atlas_status` expects the full BodyParts3D Atlas build to be ready, but the archived source lacks that installed data directory. `test_get_atlas_data_index` consequently returns 404 for `index.json`. Running `tests/test_server.py` on the pristine extracted ZIP reproduced both errors (13 tests in 2.42 seconds).
- Therefore legacy M2.8.2 acceptance reports alone do not prove full regression success on this independently provided ZIP.

## Remaining roadmap and acceptance blockers

- Merge this candidate onto actual Windows Git branch without clobbering local changes. Inspect full checkout and source licenses. Fix missing dataset/test framework prerequisites in **separate changes**.
- Complete M2.9 browser interactions, source review, richer documented node taxonomy and verified FMA↔mesh mappings.
- Complete M2.10 import/versioned editing/export, attachment security, comprehensive e2e, use proper licensed charts.
- M3 patient management/PROMs/CTCAE/FHIR/RBAC, M2.11 Pose, M2.12 surface avatar, M4 dynamic ROM, M5 tissue layers, M6 cohort analytics are **PLANNED** and **not yet implemented here**.
- Confirm Docker build and browser functionality and licensed Atlas assets before any public Space upload.

## Running locally (current candidate)

```bash
python -m msk_therapy_os init --db demo.sqlite3
python -m msk_therapy_os seed-demo --db demo.sqlite3
python -m msk_therapy_os serve --db demo.sqlite3 --port 8085
# http://127.0.0.1:8085/ -> tabs M2.9 and M2.10
python -m unittest discover -s tests -p 'test_relationship_explorer.py' -v
python -m unittest discover -s tests -p 'test_research_studio.py' -v
```

**Token gate:** token is not currently needed to develop or test locally. Ask only when authorized HF creation/push is the next actual step and all safety/license acceptance gates have passed. Never commit tokens into the repo.
