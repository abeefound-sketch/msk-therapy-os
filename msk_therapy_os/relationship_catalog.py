"""M2.9 evidence-typed graph for reference learning, never a clinical inference engine.

All nodes and relations carry explicitly scoped provenance. Unknown atlas mapping
stays unavailable rather than extrapolating point positions from labels.
"""
from __future__ import annotations

import json
import sqlite3
import unicodedata
from typing import Any

ENTITY_KINDS = ("organ", "muscle", "bone_joint", "nerve_vessel", "point", "channel", "region", "symptom", "research")
RELATION_CLASSES = ("physical_anatomy", "surface_proximity", "traditional_association", "clinical_research", "patient_observation", "hypothesis")
REVIEW_STATES = ("verified", "approximate", "awaiting_source_review", "unverified", "unavailable")


def init_relationship_tables(db: sqlite3.Connection) -> None:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS knowledge_sources (
            source_id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL, version TEXT NOT NULL DEFAULT '',
            license_status TEXT NOT NULL DEFAULT 'unknown',
            review_status TEXT NOT NULL DEFAULT 'unverified', notes TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS knowledge_entities (
            entity_id TEXT PRIMARY KEY, kind TEXT NOT NULL
                CHECK(kind IN ('organ','muscle','bone_joint','nerve_vessel','point','channel','region','symptom','research')),
            name TEXT NOT NULL, aliases_json TEXT NOT NULL DEFAULT '[]',
            namespace TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES knowledge_sources(source_id),
            review_status TEXT NOT NULL DEFAULT 'unverified'
                CHECK(review_status IN ('verified','approximate','awaiting_source_review','unverified','unavailable')),
            atlas_fma_id TEXT, atlas_mesh_id TEXT, atlas_version TEXT,
            notes TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_knowledge_entity_name ON knowledge_entities(name);
        CREATE INDEX IF NOT EXISTS idx_knowledge_entity_namespace ON knowledge_entities(namespace, kind);
        CREATE TABLE IF NOT EXISTS knowledge_relations (
            relation_id TEXT PRIMARY KEY,
            from_id TEXT NOT NULL REFERENCES knowledge_entities(entity_id),
            predicate TEXT NOT NULL, to_id TEXT NOT NULL REFERENCES knowledge_entities(entity_id),
            relation_class TEXT NOT NULL CHECK(relation_class IN
                ('physical_anatomy','surface_proximity','traditional_association','clinical_research','patient_observation','hypothesis')),
            status TEXT NOT NULL DEFAULT 'unverified'
                CHECK(status IN ('verified','approximate','awaiting_source_review','unverified','unavailable')),
            source_id TEXT NOT NULL REFERENCES knowledge_sources(source_id),
            reviewer_id TEXT, reviewed_at TEXT,
            assertion_note TEXT NOT NULL DEFAULT '',
            CHECK(from_id <> to_id)
        );
        CREATE INDEX IF NOT EXISTS idx_knowledge_rel_from ON knowledge_relations(from_id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_rel_to ON knowledge_relations(to_id);
    """)


def seed_relationship_examples(db: sqlite3.Connection) -> None:
    """Small *unverified* examples from the DESIGN SPEC, not clinical evidence."""
    db.execute("""INSERT OR IGNORE INTO knowledge_sources
        (source_id,title,source_type,license_status,review_status,notes)
        VALUES ('SPEC:RELATIONSHIP_V1','Relationship Explorer product specification',
        'design_example','user_provided_design','unverified',
        'Illustrative UX cases; not a primary anatomical or clinical verification source')""")
    examples = (
        ("ANAT:STOMACH", "organ", "Stomach (anatomical organ)", '["stomach","dạ dày"]', "ANATOMY", "Reference anatomy; Atlas FMA+mesh mapping not verified"),
        ("TCM:STOMACH_CHANNEL", "channel", "Stomach channel (TCM)", '["stomach","vị kinh","túc dương minh vị kinh"]', "TCM", "Traditional concept, not a physical connection to the stomach"),
        ("TCM:ST36", "point", "ST36 (Zusanli)", '["st36","túc tam lý"]', "TCM", "Illustrative point entry; positional mapping requires independent review"),
        ("TCM:GB21", "point", "GB21 (Jianjing)", '["gb21","kiên tỉnh"]', "TCM", "Illustrative point entry; no verified atlas surface position or safe depth"),
        ("ANAT:TRAPEZIUS", "muscle", "Trapezius (reference muscle)", '["trapezius","cơ thang"]', "ANATOMY", "Atlas mesh and laterality mapping not independently verified"),
    )
    db.executemany("""INSERT OR IGNORE INTO knowledge_entities
      (entity_id,kind,name,aliases_json,namespace,source_id,review_status,notes)
      VALUES (?,?,?,?,?,'SPEC:RELATIONSHIP_V1','awaiting_source_review',?)""", examples)
    db.execute("""INSERT OR IGNORE INTO knowledge_relations
      (relation_id,from_id,predicate,to_id,relation_class,status,source_id,assertion_note)
      VALUES ('SPEC:ST36-CHANNEL','TCM:ST36','BELONGS_TO_CHANNEL','TCM:STOMACH_CHANNEL',
      'traditional_association','awaiting_source_review','SPEC:RELATIONSHIP_V1',
      'Product-spec example only; not a biological mechanism or claim of efficacy')""")
    db.commit()


def _row_dict(cursor: sqlite3.Cursor, record: tuple[Any, ...]) -> dict[str, Any]:
    return {column[0]: value for column, value in zip(cursor.description, record)}


def _normalize(s: str) -> str:
    no_marks = ''.join(c for c in unicodedata.normalize('NFD', s.casefold()) if unicodedata.category(c) != 'Mn')
    return no_marks.replace('đ', 'd')


def _entity(row: dict[str, Any]) -> dict[str, Any]:
    aliases = json.loads(row.pop('aliases_json'))
    row['aliases'] = aliases
    row['atlas_focus_available'] = bool(row['atlas_fma_id'] and row['atlas_mesh_id'] and row['atlas_version'] and row['review_status'] == 'verified')
    return row


def find_entities(db: sqlite3.Connection, query: str, *, kind: str | None = None, limit: int = 30) -> list[dict[str, Any]]:
    if len(query) > 120 or limit < 1 or limit > 100:
        raise ValueError('Query too long or limit out of range')
    if kind and kind not in ENTITY_KINDS:
        raise ValueError('Unknown knowledge entity kind')
    sql = 'SELECT * FROM knowledge_entities' + (' WHERE kind = ?' if kind else '')
    cursor = db.execute(sql, (kind,) if kind else ())
    q = _normalize(query.strip())
    matches = []
    for record in cursor.fetchall():
        item = _entity(_row_dict(cursor, record))
        search_fields = [item['entity_id'], item['name'], *item['aliases']]
        if not q or any(q in _normalize(part) for part in search_fields):
            matches.append(item)
    matches.sort(key=lambda item: (0 if _normalize(item['entity_id']) == q else 1 if _normalize(item['name']).startswith(q) else 2, item['entity_id']))
    return matches[:limit]


def get_entity(db: sqlite3.Connection, entity_id: str) -> dict[str, Any] | None:
    cursor = db.execute('SELECT * FROM knowledge_entities WHERE entity_id=?', (entity_id,))
    record = cursor.fetchone()
    return _entity(_row_dict(cursor, record)) if record else None


def get_relations(db: sqlite3.Connection, entity_id: str, *, relation_class: str | None = None) -> list[dict[str, Any]]:
    if relation_class and relation_class not in RELATION_CLASSES:
        raise ValueError('Unknown relation class')
    if not get_entity(db, entity_id):
        raise ValueError('Unknown entity_id')
    query = """SELECT r.*, s.title AS source_title, s.review_status AS source_review_status
             FROM knowledge_relations r JOIN knowledge_sources s ON r.source_id=s.source_id
             WHERE (r.from_id=? OR r.to_id=?)"""
    args: list[str] = [entity_id, entity_id]
    if relation_class:
        query += ' AND r.relation_class=?'
        args.append(relation_class)
    query += ' ORDER BY r.relation_class,r.relation_id'
    cursor = db.execute(query, args)
    result = [_row_dict(cursor, row) for row in cursor.fetchall()]
    for row in result:
        row['other_entity_id'] = row['to_id'] if row['from_id'] == entity_id else row['from_id']
        row['other_entity'] = get_entity(db, row['other_entity_id'])
        row['clinical_efficacy_established'] = False  # Relation never implies intervention efficacy
    return result
