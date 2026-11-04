"""SQLite schema definition, connection management and migrations for Knowledge Vault."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA_V1 = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    sha256_hash TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'UNKNOWN',
    publication_date TEXT NOT NULL DEFAULT 'UNKNOWN',
    document_type TEXT NOT NULL DEFAULT 'MARKDOWN',
    namespace TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'vi',
    source_uri TEXT NOT NULL DEFAULT 'UNKNOWN',
    original_path TEXT NOT NULL DEFAULT 'UNKNOWN',
    license TEXT NOT NULL DEFAULT 'UNKNOWN',
    imported_at TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'UNREVIEWED'
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    source_quote TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    claim_type TEXT NOT NULL DEFAULT 'ANATOMICAL_LOCATION',
    assertion_type TEXT NOT NULL DEFAULT 'ASSERTION',
    status TEXT NOT NULL DEFAULT 'UNREVIEWED',
    evidence_tier TEXT NOT NULL DEFAULT 'TIER_UNGRADED',
    created_by TEXT NOT NULL DEFAULT 'system',
    created_at TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT,
    uncertainty_notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS citations (
    citation_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    locator TEXT DEFAULT '',
    relationship TEXT NOT NULL DEFAULT 'SUPPORTS',
    retrieval_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_relations (
    relation_id TEXT PRIMARY KEY,
    source_claim_id TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    target_claim_id TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    CONSTRAINT chk_diff_claims CHECK (source_claim_id != target_claim_id)
);

CREATE TABLE IF NOT EXISTS tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS document_tags (
    doc_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (doc_id, tag_id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    before_state TEXT,
    after_state TEXT,
    rationale TEXT DEFAULT '',
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_docs_sha256 ON documents(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_docs_namespace ON documents(namespace);
CREATE INDEX IF NOT EXISTS idx_claims_doc_id ON claims(doc_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_claim_relations_src ON claim_relations(source_claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_relations_tgt ON claim_relations(target_claim_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id);
"""


def init_database(db_path: str | Path) -> sqlite3.Connection:
    """Connect to SQLite database and apply V1 schema and FTS5 tables."""
    db_path = str(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")

    with conn:
        conn.executescript(SCHEMA_V1)
        # Check and record migration V1
        cur = conn.cursor()
        cur.execute("SELECT version FROM schema_migrations WHERE version = 1")
        if not cur.fetchone():
            cur.execute("INSERT INTO schema_migrations (version, applied_at) VALUES (1, datetime('now'))")

        # Create FTS5 virtual tables if supported
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    doc_id UNINDEXED,
                    title,
                    author,
                    raw_content,
                    tokenize='unicode61'
                );
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts USING fts5(
                    claim_id UNINDEXED,
                    doc_id UNINDEXED,
                    claim_text,
                    source_quote,
                    uncertainty_notes,
                    tokenize='unicode61'
                );
            """)
        except sqlite3.OperationalError:
            # Fallback for minimal SQLite without FTS5 compiled
            pass

    return conn


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Get connection with foreign keys enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
