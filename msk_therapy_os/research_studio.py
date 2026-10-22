"""M2.10 synthetic-only 2D research point definitions and encounter findings.

No imaging inference, clinical prescription, copyrighted point coordinates or
3D atlas registration. Publication/version history is immutable by design.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

VIEWS = ("front", "left_profile", "right_profile", "other")
FRAMES = ("dien_chan_bqc", "tcm", "sen_sib", "custom")
STATES = ("observed_positive", "assessed_negative", "not_assessed")
GEOMETRIES = ("point", "polyline", "polygon")
STATIC_DIAGRAM_DIR = Path(__file__).resolve().parent / "static" / "research_demo"


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:20]}"


def _require_text(value: Any, *, field: str, length: int = 120) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > length:
        raise ValueError(f"{field} must be non-empty text up to {length} chars")
    return value.strip()


def _require_demo_case(db: sqlite3.Connection, case_id: str, visit_id: int) -> None:
    if not isinstance(case_id, str) or not case_id.startswith('DEMO-'):
        raise ValueError('Only DEMO-* cases are permitted in Research Studio')
    rec = db.execute('SELECT case_id FROM visits WHERE id=?', (visit_id,)).fetchone()
    if not rec or rec[0] != case_id:
        raise ValueError('Visit does not belong to the requested DEMO case')


def init_research_tables(db: sqlite3.Connection) -> None:
    db.executescript("""
    CREATE TABLE IF NOT EXISTS research_point_sets (
        set_id TEXT PRIMARY KEY, title TEXT NOT NULL, framework TEXT NOT NULL
          CHECK (framework IN ('dien_chan_bqc','tcm','sen_sib','custom')),
        owner_user_id TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS research_versions (
        version_id TEXT PRIMARY KEY, set_id TEXT NOT NULL REFERENCES research_point_sets(set_id),
        version_number INTEGER NOT NULL CHECK(version_number>0),
        parent_version_id TEXT REFERENCES research_versions(version_id),
        status TEXT NOT NULL CHECK(status IN ('draft','locked')) DEFAULT 'draft',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(set_id,version_number)
    );
    CREATE TABLE IF NOT EXISTS research_diagrams (
        diagram_id TEXT PRIMARY KEY, version_id TEXT NOT NULL REFERENCES research_versions(version_id),
        view TEXT NOT NULL CHECK(view IN ('front','left_profile','right_profile','other')),
        asset_path TEXT NOT NULL, asset_sha256 TEXT NOT NULL,
        width_px INTEGER NOT NULL CHECK(width_px>0), height_px INTEGER NOT NULL CHECK(height_px>0),
        license_status TEXT NOT NULL, source_description TEXT NOT NULL,
        UNIQUE(version_id,view)
    );
    CREATE TABLE IF NOT EXISTS research_definitions (
        definition_id TEXT PRIMARY KEY, version_id TEXT NOT NULL REFERENCES research_versions(version_id),
        diagram_id TEXT NOT NULL REFERENCES research_diagrams(diagram_id),
        local_code TEXT NOT NULL, label TEXT NOT NULL,
        geometry_type TEXT NOT NULL CHECK(geometry_type IN ('point','polyline','polygon')),
        geometry_json TEXT NOT NULL, theory_namespace TEXT NOT NULL,
        source_note TEXT NOT NULL, review_state TEXT NOT NULL DEFAULT 'draft'
          CHECK(review_state IN ('draft','reviewed','disputed','retired')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_research_local_code_version
       ON research_definitions(version_id,local_code COLLATE NOCASE);
    CREATE INDEX IF NOT EXISTS idx_research_def_diagram ON research_definitions(diagram_id);
    CREATE TABLE IF NOT EXISTS research_reactive_observations (
        observation_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL REFERENCES cases(case_id),
        visit_id INTEGER NOT NULL REFERENCES visits(id),
        diagram_id TEXT NOT NULL REFERENCES research_diagrams(diagram_id),
        definition_id TEXT REFERENCES research_definitions(definition_id),
        geometry_json TEXT NOT NULL,
        finding_state TEXT NOT NULL CHECK(finding_state IN ('observed_positive','assessed_negative','not_assessed')),
        tenderness INTEGER CHECK(tenderness BETWEEN 0 AND 10),
        method TEXT NOT NULL, operator TEXT NOT NULL,
        notes TEXT NOT NULL DEFAULT '',
        observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_research_observations_case ON research_reactive_observations(case_id,visit_id);
    """)


def validate_geometry(geometry: Any) -> dict[str, Any]:
    if not isinstance(geometry, dict) or geometry.get('space') != 'image_normalized_v1':
        raise ValueError('Geometry must specify image_normalized_v1')
    geometry_type = geometry.get('type')
    if geometry_type not in GEOMETRIES:
        raise ValueError('Invalid geometry type')
    points = geometry.get('coordinates')
    if geometry_type == 'point':
        points = [points]
    if not isinstance(points, list) or len(points) > 100 or len(points) < (1 if geometry_type == 'point' else 2 if geometry_type == 'polyline' else 3):
        raise ValueError('Missing or excessive 2D coordinates')
    for point in points:
        if not isinstance(point, list) or len(point) != 2 or any(type(c) not in (int,float) or not 0 <= c <= 1 for c in point):
            raise ValueError('Coordinates must be finite normalized [u,v] pairs in [0,1]')
    # copy only documented schema fields: no HTML/source injection piggybacking
    return {'space':'image_normalized_v1','type':geometry_type,'coordinates':geometry['coordinates']}


def create_research_set(db: sqlite3.Connection, *, title: str, framework: str, owner: str) -> dict[str, Any]:
    title = _require_text(title, field='title')
    if framework not in FRAMES:
        raise ValueError('Unknown framework')
    owner = _require_text(owner,field='owner',length=80)
    set_id, version_id = _new_id('RSET'), _new_id('RVER')
    with db:
        db.execute('INSERT INTO research_point_sets (set_id,title,framework,owner_user_id) VALUES (?,?,?,?)',
                   (set_id,title,framework,owner))
        db.execute('INSERT INTO research_versions (version_id,set_id,version_number) VALUES (?,?,1)',(version_id,set_id))
        for view, asset, width, height in (('front','face_front.svg',400,500),('left_profile','face_profile.svg',400,500)):
            path = STATIC_DIAGRAM_DIR / asset
            if not path.is_file():
                raise RuntimeError('Bundled synthetic diagram missing')
            # Whitelisted internal assets only. No arbitrary upload path or third-party image rights.
            db.execute('''INSERT INTO research_diagrams
                (diagram_id,version_id,view,asset_path,asset_sha256,width_px,height_px,license_status,source_description)
                VALUES (?,?,?,?,?,?,?,?,?)''',(_new_id('RDGM'),version_id,view,
                '/research_demo/'+asset,sha256(path.read_bytes()).hexdigest(),width,height,
                'generated_illustration','Simple original schematic. Not a licensed Bùi Quốc Châu chart.'))
    return get_research_set(db,set_id)


def _fetch(db: sqlite3.Connection, sql: str, args: tuple = ()) -> list[dict[str, Any]]:
    cursor = db.execute(sql,args)
    return [dict(zip((col[0] for col in cursor.description),row)) for row in cursor.fetchall()]


def get_research_set(db: sqlite3.Connection, set_id: str) -> dict[str, Any] | None:
    rows = _fetch(db,'SELECT * FROM research_point_sets WHERE set_id=?',(set_id,))
    if not rows:
        return None
    item = rows[0]
    item['versions'] = _fetch(db,'SELECT * FROM research_versions WHERE set_id=? ORDER BY version_number',(set_id,))
    item['diagrams'] = _fetch(db,'''SELECT d.* FROM research_diagrams d JOIN research_versions v ON d.version_id=v.version_id
       WHERE v.set_id=? ORDER BY v.version_number,d.view''',(set_id,))
    return item


def list_research_sets(db: sqlite3.Connection, user_id: str | None = None) -> list[dict[str, Any]]:
    return _fetch(db, """SELECT * FROM research_point_sets
        WHERE owner_user_id='PUBLIC-DEMO' OR owner_user_id=?
        ORDER BY created_at DESC,set_id""", (user_id or '',))


def diagram_visible_to(db: sqlite3.Connection, diagram_id: str, user_id: str | None = None) -> bool:
    return db.execute("""SELECT 1 FROM research_diagrams d
      JOIN research_versions v ON d.version_id=v.version_id
      JOIN research_point_sets s ON v.set_id=s.set_id
      WHERE d.diagram_id=? AND (s.owner_user_id='PUBLIC-DEMO' OR s.owner_user_id=?)""",
      (diagram_id,user_id or '')).fetchone() is not None


def set_visible_to(db: sqlite3.Connection, set_id: str, user_id: str | None = None) -> bool:
    return db.execute("""SELECT 1 FROM research_point_sets WHERE set_id=?
      AND (owner_user_id='PUBLIC-DEMO' OR owner_user_id=?)""",
      (set_id,user_id or '')).fetchone() is not None


def _assert_draft_and_owner(db: sqlite3.Connection, diagram_id: str, user_id: str) -> str:
    row = db.execute('''SELECT d.version_id,v.status,s.owner_user_id FROM research_diagrams d
        JOIN research_versions v ON d.version_id=v.version_id
        JOIN research_point_sets s ON v.set_id=s.set_id WHERE d.diagram_id=?''',(diagram_id,)).fetchone()
    if not row:
        raise ValueError('Unknown diagram')
    if row[2] == 'PUBLIC-DEMO':
        raise PermissionError('Shared tutorial is immutable')
    if row[1] != 'draft':
        raise PermissionError('Version is locked; fork it before adding definitions')
    if row[2] != user_id:
        raise PermissionError('Research set belongs to another user')
    return row[0]


def create_definition(db: sqlite3.Connection, data: dict[str, Any], user_id: str) -> dict[str, Any]:
    diagram_id = _require_text(data.get('diagram_id'),field='diagram_id')
    version_id = _assert_draft_and_owner(db,diagram_id,user_id)
    geometry = validate_geometry(data.get('geometry'))
    local_code = _require_text(data.get('local_code'),field='local_code',length=48)
    label = _require_text(data.get('label'),field='label',length=160)
    source_note = _require_text(data.get('source_note'),field='source_note',length=500)
    namespace = _require_text(data.get('theory_namespace','CUSTOM'),field='theory_namespace',length=64)
    definition_id = _new_id('RDEF')
    with db:
        db.execute('''INSERT INTO research_definitions
          (definition_id,version_id,diagram_id,local_code,label,geometry_type,geometry_json,theory_namespace,source_note)
          VALUES (?,?,?,?,?,?,?,?,?)''',(definition_id,version_id,diagram_id,local_code,label,geometry['type'],json.dumps(geometry),namespace,source_note))
    return list_definitions(db,diagram_id=diagram_id,definition_id=definition_id)[0]


def list_definitions(db: sqlite3.Connection, *, diagram_id: str, definition_id: str | None = None) -> list[dict[str, Any]]:
    sql = 'SELECT * FROM research_definitions WHERE diagram_id=?'
    args = (diagram_id,)
    if definition_id:
        sql += ' AND definition_id=?'
        args += (definition_id,)
    result = _fetch(db,sql+' ORDER BY local_code',args)
    for item in result:
        item['geometry'] = json.loads(item.pop('geometry_json'))
    return result


def create_reactive_observation(db: sqlite3.Connection, data: dict[str, Any], user_id: str) -> dict[str, Any]:
    if not user_id:
        raise PermissionError('Authentication required')
    case_id = _require_text(data.get('case_id'),field='case_id')
    try:
        visit_id = int(data.get('visit_id'))
    except (ValueError,TypeError) as error:
        raise ValueError('visit_id must be an integer') from error
    _require_demo_case(db,case_id,visit_id)
    diagram_id = _require_text(data.get('diagram_id'),field='diagram_id')
    if not diagram_visible_to(db,diagram_id,user_id):
        raise ValueError('Unknown diagram')
    owner = db.execute('''SELECT s.owner_user_id FROM research_diagrams d
       JOIN research_versions v ON d.version_id=v.version_id
       JOIN research_point_sets s ON v.set_id=s.set_id WHERE d.diagram_id=?''',(diagram_id,)).fetchone()
    if owner[0] != user_id:
        raise PermissionError('Cannot write to another owner’s research diagrams')
    definition_id = data.get('definition_id') or None
    if definition_id:
        found = db.execute('SELECT 1 FROM research_definitions WHERE definition_id=? AND diagram_id=?',(definition_id,diagram_id)).fetchone()
        if not found:
            raise ValueError('Definition not on this diagram')
    geometry = validate_geometry(data.get('geometry'))
    state = data.get('finding_state')
    if state not in STATES:
        raise ValueError('Invalid finding state')
    tenderness = data.get('tenderness')
    if tenderness is not None and (type(tenderness) is not int or not 0 <= tenderness <= 10):
        raise ValueError('Tenderness must be integer 0-10 or null')
    if state == 'not_assessed' and tenderness is not None:
        raise ValueError('A not-assessed finding cannot have a numeric score')
    method = _require_text(data.get('method'),field='method',length=160)
    notes = data.get('notes','')
    if not isinstance(notes,str) or len(notes)>1000:
        raise ValueError('Notes too long')
    obs_id = _new_id('ROBS')
    with db:
        db.execute('''INSERT INTO research_reactive_observations
          (observation_id,case_id,visit_id,diagram_id,definition_id,geometry_json,finding_state,tenderness,method,operator,notes)
          VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
          (obs_id,case_id,visit_id,diagram_id,definition_id,json.dumps(geometry),state,tenderness,method,user_id,notes))
    return {'observation_id':obs_id,'case_id':case_id,'visit_id':visit_id,'finding_state':state}


def case_research_timeline(db: sqlite3.Connection, case_id: str, user_id: str | None = None) -> list[dict[str, Any]]:
    if not case_id.startswith('DEMO-'):
        raise ValueError('Synthetic DEMO-* cases only')
    result = _fetch(db,'''SELECT o.*,v.visit_date,d.view FROM research_reactive_observations o
       JOIN visits v ON v.id=o.visit_id JOIN research_diagrams d ON d.diagram_id=o.diagram_id
       JOIN research_versions rv ON rv.version_id=d.version_id
       JOIN research_point_sets s ON s.set_id=rv.set_id
       WHERE o.case_id=? AND (s.owner_user_id='PUBLIC-DEMO' OR s.owner_user_id=?)
       ORDER BY v.visit_date,o.observed_at,o.rowid''',(case_id,user_id or '',))
    for item in result:
        item['geometry'] = json.loads(item.pop('geometry_json'))
    return result


def seed_demo_research_set(db: sqlite3.Connection) -> None:
    """Stable public READ-ONLY example, with invented NON-CLINICAL point positions."""
    set_id, version_id = 'RSET-DEMO-ILLUSTRATIVE','RVER-DEMO-1'
    with db:
        db.execute("""INSERT OR IGNORE INTO research_point_sets
          (set_id,title,framework,owner_user_id) VALUES (?,?,?,?)""",
          (set_id,'Fictional 2D annotation tutorial (not Bùi Quốc Châu coordinates)','custom','PUBLIC-DEMO'))
        db.execute("""INSERT OR IGNORE INTO research_versions
          (version_id,set_id,version_number,status) VALUES (?,?,1,'locked')""",(version_id,set_id))
        for view,asset in (('front','face_front.svg'),('left_profile','face_profile.svg')):
            path = STATIC_DIAGRAM_DIR / asset
            db.execute("""INSERT OR IGNORE INTO research_diagrams
                (diagram_id,version_id,view,asset_path,asset_sha256,width_px,height_px,license_status,source_description)
                VALUES (?,?,?,?,?,400,500,'generated_illustration','Generic generated schematic; no real acupuncture coordinates')""",
                ('RDGM-DEMO-'+view,version_id,view,'/research_demo/'+asset,sha256(path.read_bytes()).hexdigest()))
        db.execute("""INSERT OR IGNORE INTO research_definitions
          (definition_id,version_id,diagram_id,local_code,label,geometry_type,geometry_json,theory_namespace,source_note,review_state)
          VALUES (?,?,?,?,?,?,?,?,?,?)""",('RDEF-DEMO-FICTIVE',version_id,'RDGM-DEMO-front',
          'EXAMPLE-01','Fictional point, not a clinical location','point',
          json.dumps({'space':'image_normalized_v1','type':'point','coordinates':[0.5,0.5]}),
          'TUTORIAL_ONLY','Generated marker; no anatomical/traditional validity','draft'))
