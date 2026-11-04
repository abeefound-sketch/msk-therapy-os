"""Core implementation of KnowledgeVault engine for Milestone P20."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from msk_therapy_os.knowledge_vault.db import init_database, get_connection
from msk_therapy_os.knowledge_vault.models import (
    Document,
    Claim,
    Citation,
    ClaimRelation,
    AuditEvent,
    Review,
    SearchFilter,
    SearchResult,
    ClaimStatus,
    DocumentNamespace,
    EvidenceTier,
    RelationType,
)


def _normalize_text(text: str) -> str:
    """Normalize Unicode to NFC form for reliable Vietnamese and multilingual handling."""
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)


def _compute_sha256(content: bytes | str) -> str:
    """Compute cryptographic SHA-256 digest."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _parse_yaml_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML-like frontmatter between triple dashes without external libraries."""
    text = _normalize_text(text)
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
    match = pattern.match(text)
    if not match:
        return {}, text

    raw_yaml, body = match.groups()
    meta = {}
    for line in raw_yaml.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip("\"'")
            if val.startswith("[") and val.endswith("]"):
                items = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
                meta[key] = items
            else:
                meta[key] = val
    return meta, body


class KnowledgeVault:
    """Offline Knowledge Vault for evidence, claims, citations and contradictory viewpoints."""

    def __init__(self, db_path: str | Path, vault_dir: Optional[str | Path] = None):
        self.db_path = Path(db_path).resolve()
        if vault_dir:
            self.vault_dir = Path(vault_dir).resolve()
        else:
            self.vault_dir = self.db_path.parent

        self.originals_dir = self.vault_dir / "originals"
        self.notes_dir = self.vault_dir / "notes"
        self.originals_dir.mkdir(parents=True, exist_ok=True)
        self.notes_dir.mkdir(parents=True, exist_ok=True)

        self._has_fts5 = True
        self._init_vault()

    def _init_vault(self) -> None:
        """Initialize database schema and verify FTS5 support."""
        conn = init_database(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT count(*) FROM documents_fts")
        except sqlite3.OperationalError:
            self._has_fts5 = False
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def _record_audit_event(
        self,
        conn: sqlite3.Connection,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        rationale: str = "",
    ) -> None:
        """Append an immutable audit event."""
        event_id = f"aud_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT INTO audit_events (
                event_id, entity_type, entity_id, action, actor,
                before_state, after_state, rationale, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                entity_type,
                entity_id,
                action,
                actor,
                json.dumps(before_state, ensure_ascii=False) if before_state else None,
                json.dumps(after_state, ensure_ascii=False) if after_state else None,
                rationale,
                now,
            ),
        )

    # -------------------------------------------------------------------------
    # DOCUMENT MANAGEMENT
    # -------------------------------------------------------------------------

    def import_text(
        self,
        text: str,
        title: str,
        namespace: str = DocumentNamespace.RESEARCH_NOTE.value,
        author: str = "UNKNOWN",
        publication_date: str = "UNKNOWN",
        document_type: str = "MARKDOWN",
        source_uri: str = "UNKNOWN",
        license_str: str = "UNKNOWN",
        tags: Optional[List[str]] = None,
        actor: str = "user",
    ) -> Document:
        """Import raw text or Markdown string into vault."""
        text = _normalize_text(text)
        content_hash = _compute_sha256(text)

        conn = self._get_conn()
        cur = conn.cursor()

        # Idempotent deduplication check
        cur.execute("SELECT doc_id, title FROM documents WHERE sha256_hash = ?", (content_hash,))
        existing = cur.fetchone()
        if existing:
            self._record_audit_event(
                conn, "DOCUMENT", existing[0], "IMPORT_IDEMPOTENT", actor,
                after_state={"doc_id": existing[0], "sha256_hash": content_hash},
                rationale="Identical content already imported. Reusing existing document ID.",
            )
            conn.commit()
            conn.close()
            return self.get_document(existing[0])

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        # Save to originals as immutable source artifact
        original_file = self.originals_dir / f"{content_hash[:16]}_{doc_id}.md"
        original_file.write_text(text, encoding="utf-8")

        with conn:
            conn.execute(
                """
                INSERT INTO documents (
                    doc_id, sha256_hash, title, author, publication_date,
                    document_type, namespace, language, source_uri, original_path,
                    license, imported_at, raw_content, review_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    content_hash,
                    title,
                    author or "UNKNOWN",
                    publication_date or "UNKNOWN",
                    document_type,
                    namespace,
                    "vi" if any(c in text for c in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ") else "en",
                    source_uri or "UNKNOWN",
                    str(original_file),
                    license_str or "UNKNOWN",
                    now,
                    text,
                    "UNREVIEWED",
                ),
            )

            # Insert tags
            if tags:
                for t in tags:
                    t_clean = t.strip()
                    if not t_clean:
                        continue
                    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (t_clean,))
                    cur.execute("SELECT tag_id FROM tags WHERE name = ?", (t_clean,))
                    t_id = cur.fetchone()[0]
                    conn.execute("INSERT OR IGNORE INTO document_tags (doc_id, tag_id) VALUES (?, ?)", (doc_id, t_id))

            # Update FTS5 index
            if self._has_fts5:
                try:
                    conn.execute(
                        "INSERT INTO documents_fts (doc_id, title, author, raw_content) VALUES (?, ?, ?, ?)",
                        (doc_id, title, author or "UNKNOWN", text),
                    )
                except sqlite3.OperationalError:
                    pass

            doc_dict = {
                "doc_id": doc_id,
                "title": title,
                "author": author or "UNKNOWN",
                "namespace": namespace,
                "sha256_hash": content_hash,
            }
            self._record_audit_event(
                conn, "DOCUMENT", doc_id, "IMPORT", actor,
                after_state=doc_dict,
                rationale="New document imported into Knowledge Vault",
            )

        conn.close()
        return self.get_document(doc_id)

    def import_file(
        self,
        file_path: str | Path,
        metadata: Optional[Dict[str, Any]] = None,
        actor: str = "user",
    ) -> Document:
        """Import a Markdown or text file, extracting frontmatter if present."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Document file not found: {path}")

        raw_text = path.read_text(encoding="utf-8")
        parsed_meta, body = _parse_yaml_frontmatter(raw_text)

        merged_meta = dict(parsed_meta)
        if metadata:
            merged_meta.update(metadata)

        title = merged_meta.get("title") or path.stem.replace("_", " ").title()
        author = merged_meta.get("author") or "UNKNOWN"
        publication_date = merged_meta.get("date") or merged_meta.get("publication_date") or "UNKNOWN"
        namespace = merged_meta.get("namespace") or DocumentNamespace.RESEARCH_NOTE.value
        source_uri = merged_meta.get("source_uri") or merged_meta.get("url") or "UNKNOWN"
        license_str = merged_meta.get("license") or "UNKNOWN"
        tags = merged_meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        return self.import_text(
            text=raw_text,
            title=title,
            namespace=namespace,
            author=author,
            publication_date=publication_date,
            document_type="MARKDOWN",
            source_uri=source_uri,
            license_str=license_str,
            tags=tags,
            actor=actor,
        )

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Fetch document by ID with tags."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT doc_id, sha256_hash, title, author, publication_date,
                   document_type, namespace, language, source_uri, original_path,
                   license, imported_at, raw_content, review_status
            FROM documents WHERE doc_id = ?
            """,
            (doc_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return None

        cur.execute(
            """
            SELECT t.name FROM tags t
            JOIN document_tags dt ON t.tag_id = dt.tag_id
            WHERE dt.doc_id = ?
            """,
            (doc_id,),
        )
        tags = [r[0] for r in cur.fetchall()]
        conn.close()

        return Document(
            doc_id=row[0],
            sha256_hash=row[1],
            title=row[2],
            author=row[3],
            publication_date=row[4],
            document_type=row[5],
            namespace=row[6],
            language=row[7],
            source_uri=row[8],
            original_path=row[9],
            license=row[10],
            imported_at=row[11],
            raw_content=row[12],
            review_status=row[13],
            tags=tags,
        )

    # -------------------------------------------------------------------------
    # CLAIMS & CITATIONS
    # -------------------------------------------------------------------------

    def add_claim(
        self,
        doc_id: str,
        claim_text: str,
        source_quote: str,
        claim_type: str = "ANATOMICAL_LOCATION",
        assertion_type: str = "ASSERTION",
        status: str = "UNREVIEWED",
        evidence_tier: str = "TIER_UNGRADED",
        actor: str = "user",
        uncertainty_notes: str = "",
    ) -> Claim:
        """Add an atomic claim linked to a source document. Prohibits fake clinical approvals."""
        # Non-negotiable invariant: Cannot self-claim clinical approval
        if status in ("CLINICAL_APPROVED", "ANATOMICAL_VERIFIED", "APPROVED"):
            raise ValueError(
                f"Unauthorized claim status '{status}'. Claims must remain UNREVIEWED, "
                "SUPPORTED, or CONTESTED under P19/P20 governance."
            )

        claim_text = _normalize_text(claim_text)
        source_quote = _normalize_text(source_quote)
        claim_id = f"clm_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO claims (
                    claim_id, doc_id, source_quote, claim_text, claim_type,
                    assertion_type, status, evidence_tier, created_by, created_at,
                    uncertainty_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    doc_id,
                    source_quote,
                    claim_text,
                    claim_type,
                    assertion_type,
                    status,
                    evidence_tier,
                    actor,
                    now,
                    uncertainty_notes,
                ),
            )

            # Auto create primary citation to document
            citation_id = f"cit_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO citations (citation_id, claim_id, doc_id, relationship, retrieval_date)
                VALUES (?, ?, ?, 'SUPPORTS', ?)
                """,
                (citation_id, claim_id, doc_id, now),
            )

            # Update claims FTS5 index
            if self._has_fts5:
                try:
                    conn.execute(
                        """
                        INSERT INTO claims_fts (claim_id, doc_id, claim_text, source_quote, uncertainty_notes)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (claim_id, doc_id, claim_text, source_quote, uncertainty_notes),
                    )
                except sqlite3.OperationalError:
                    pass

            claim_dict = {
                "claim_id": claim_id,
                "doc_id": doc_id,
                "claim_text": claim_text,
                "status": status,
            }
            self._record_audit_event(
                conn, "CLAIM", claim_id, "CREATE", actor,
                after_state=claim_dict,
                rationale="Claim created with citation anchor to source document",
            )

        conn.close()
        return self.get_claim(claim_id)

    def get_claim(self, claim_id: str) -> Optional[Claim]:
        """Fetch claim by ID."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT claim_id, doc_id, source_quote, claim_text, claim_type,
                   assertion_type, status, evidence_tier, created_by, created_at,
                   reviewed_by, reviewed_at, uncertainty_notes
            FROM claims WHERE claim_id = ?
            """,
            (claim_id,),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return Claim(
            claim_id=row[0],
            doc_id=row[1],
            source_quote=row[2],
            claim_text=row[3],
            claim_type=row[4],
            assertion_type=row[5],
            status=row[6],
            evidence_tier=row[7],
            created_by=row[8],
            created_at=row[9],
            reviewed_by=row[10],
            reviewed_at=row[11],
            uncertainty_notes=row[12],
        )

    # -------------------------------------------------------------------------
    # CONFLICT MANAGEMENT & RELATIONS
    # -------------------------------------------------------------------------

    def add_conflict(
        self,
        claim_id_1: str,
        claim_id_2: str,
        notes: str = "",
        actor: str = "user",
    ) -> ClaimRelation:
        """Record contradictory relationship between two claims. Keeps BOTH claims alive!"""
        if claim_id_1 == claim_id_2:
            raise ValueError("A claim cannot conflict with itself.")

        rel_id = f"rel_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        conn = self._get_conn()
        with conn:
            # Insert bidirectional contradiction relation
            conn.execute(
                """
                INSERT INTO claim_relations (relation_id, source_claim_id, target_claim_id, relationship_type, notes, created_at)
                VALUES (?, ?, ?, 'CONTRADICTS', ?, ?)
                """,
                (rel_id, claim_id_1, claim_id_2, notes, now),
            )

            # Mark both claims as CONTESTED if they are UNREVIEWED or SUPPORTED
            for cid in (claim_id_1, claim_id_2):
                cur = conn.cursor()
                cur.execute("SELECT status FROM claims WHERE claim_id = ?", (cid,))
                row = cur.fetchone()
                if row and row[0] in ("UNREVIEWED", "SUPPORTED"):
                    conn.execute("UPDATE claims SET status = 'CONTESTED' WHERE claim_id = ?", (cid,))

            rel_dict = {
                "relation_id": rel_id,
                "claim1": claim_id_1,
                "claim2": claim_id_2,
                "relationship": "CONTRADICTS",
            }
            self._record_audit_event(
                conn, "RELATION", rel_id, "CONFLICT_RECORDED", actor,
                after_state=rel_dict,
                rationale=f"Contradictory relationship established: {notes}",
            )

        conn.close()
        return ClaimRelation(
            relation_id=rel_id,
            source_claim_id=claim_id_1,
            target_claim_id=claim_id_2,
            relationship_type="CONTRADICTS",
            notes=notes,
            created_at=now,
        )

    def list_conflicts(self) -> List[Dict[str, Any]]:
        """List all contradictory claim pairings with their titles and quotes."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT cr.relation_id, cr.notes, cr.created_at,
                   c1.claim_id, c1.claim_text, c1.status, d1.title,
                   c2.claim_id, c2.claim_text, c2.status, d2.title
            FROM claim_relations cr
            JOIN claims c1 ON cr.source_claim_id = c1.claim_id
            JOIN documents d1 ON c1.doc_id = d1.doc_id
            JOIN claims c2 ON cr.target_claim_id = c2.claim_id
            JOIN documents d2 ON c2.doc_id = d2.doc_id
            WHERE cr.relationship_type = 'CONTRADICTS'
            ORDER BY cr.created_at DESC
            """
        )
        conflicts = []
        for r in cur.fetchall():
            conflicts.append({
                "relation_id": r[0],
                "notes": r[1],
                "created_at": r[2],
                "claim_1": {
                    "id": r[3],
                    "text": r[4],
                    "status": r[5],
                    "doc_title": r[6],
                },
                "claim_2": {
                    "id": r[7],
                    "text": r[8],
                    "status": r[9],
                    "doc_title": r[10],
                },
            })
        conn.close()
        return conflicts

    # -------------------------------------------------------------------------
    # SEARCH ENGINE (FTS5 + LIKE FALLBACK)
    # -------------------------------------------------------------------------

    def search(
        self,
        query: str,
        namespace: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[SearchResult]:
        """Full text search across documents and claims with Vietnamese diacritics support."""
        q_norm = _normalize_text(query.strip())
        results: List[SearchResult] = []
        if not q_norm:
            return results

        conn = self._get_conn()
        cur = conn.cursor()

        # Try FTS5 first
        used_fts = False
        if self._has_fts5:
            try:
                # Escape double quotes for FTS5 string query
                safe_fts_query = '"' + q_norm.replace('"', '""') + '"'
                
                # Search documents
                cur.execute(
                    """
                    SELECT d.doc_id, d.title, d.author, d.namespace, d.review_status,
                           snippet(documents_fts, 3, '<b>', '</b>', '...', 20) AS snip
                    FROM documents_fts f
                    JOIN documents d ON f.doc_id = d.doc_id
                    WHERE documents_fts MATCH ?
                    ORDER BY rank LIMIT ?
                    """,
                    (safe_fts_query, limit),
                )
                for r in cur.fetchall():
                    if namespace and r[3] != namespace:
                        continue
                    results.append(
                        SearchResult(
                            result_type="DOCUMENT",
                            id=r[0],
                            title_or_code=r[1],
                            snippet=r[5],
                            namespace=r[3],
                            status=r[4],
                            metadata={"author": r[2]},
                        )
                    )

                # Search claims
                cur.execute(
                    """
                    SELECT c.claim_id, c.doc_id, c.claim_text, c.claim_type, c.status,
                           snippet(claims_fts, 2, '<b>', '</b>', '...', 20) AS snip, d.namespace
                    FROM claims_fts f
                    JOIN claims c ON f.claim_id = c.claim_id
                    JOIN documents d ON c.doc_id = d.doc_id
                    WHERE claims_fts MATCH ?
                    ORDER BY rank LIMIT ?
                    """,
                    (safe_fts_query, limit),
                )
                for r in cur.fetchall():
                    if namespace and r[6] != namespace:
                        continue
                    if status and r[4] != status:
                        continue
                    results.append(
                        SearchResult(
                            result_type="CLAIM",
                            id=r[0],
                            title_or_code=r[3],
                            snippet=r[5],
                            namespace=r[6],
                            status=r[4],
                            metadata={"doc_id": r[1], "claim_text": r[2]},
                        )
                    )
                used_fts = True
            except (sqlite3.OperationalError, Exception):
                used_fts = False

        # Fallback to standard LIKE queries if FTS5 not used or returned zero due to syntax
        if not used_fts or len(results) == 0:
            like_param = f"%{q_norm}%"
            # Docs LIKE
            cur.execute(
                """
                SELECT doc_id, title, author, namespace, review_status, raw_content
                FROM documents
                WHERE title LIKE ? OR raw_content LIKE ? OR author LIKE ?
                LIMIT ?
                """,
                (like_param, like_param, like_param, limit),
            )
            for r in cur.fetchall():
                if namespace and r[3] != namespace:
                    continue
                # Generate simple snippet
                idx = r[5].lower().find(q_norm.lower())
                start = max(0, idx - 40)
                end = min(len(r[5]), idx + 60)
                snip = ("..." if start > 0 else "") + r[5][start:end] + ("..." if end < len(r[5]) else "")
                results.append(
                    SearchResult(
                        result_type="DOCUMENT",
                        id=r[0],
                        title_or_code=r[1],
                        snippet=snip,
                        namespace=r[3],
                        status=r[4],
                        metadata={"author": r[2]},
                    )
                )

            # Claims LIKE
            cur.execute(
                """
                SELECT c.claim_id, c.doc_id, c.claim_text, c.claim_type, c.status, c.source_quote, d.namespace
                FROM claims c
                JOIN documents d ON c.doc_id = d.doc_id
                WHERE c.claim_text LIKE ? OR c.source_quote LIKE ?
                LIMIT ?
                """,
                (like_param, like_param, limit),
            )
            for r in cur.fetchall():
                if namespace and r[6] != namespace:
                    continue
                if status and r[4] != status:
                    continue
                results.append(
                    SearchResult(
                        result_type="CLAIM",
                        id=r[0],
                        title_or_code=r[3],
                        snippet=r[2],
                        namespace=r[6],
                        status=r[4],
                        metadata={"doc_id": r[1], "source_quote": r[5]},
                    )
                )

        conn.close()
        return results

    # -------------------------------------------------------------------------
    # EXPORT & BACKUP
    # -------------------------------------------------------------------------

    def export_json(self, output_path: str | Path) -> str:
        """Export the complete vault as a single structured JSON file."""
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("SELECT * FROM documents")
        docs_cols = [c[0] for c in cur.description]
        docs = [dict(zip(docs_cols, r)) for r in cur.fetchall()]

        cur.execute("SELECT * FROM claims")
        claims_cols = [c[0] for c in cur.description]
        claims = [dict(zip(claims_cols, r)) for r in cur.fetchall()]

        cur.execute("SELECT * FROM citations")
        cit_cols = [c[0] for c in cur.description]
        citations = [dict(zip(cit_cols, r)) for r in cur.fetchall()]

        cur.execute("SELECT * FROM claim_relations")
        rel_cols = [c[0] for c in cur.description]
        relations = [dict(zip(rel_cols, r)) for r in cur.fetchall()]

        cur.execute("SELECT * FROM audit_events ORDER BY timestamp ASC")
        aud_cols = [c[0] for c in cur.description]
        audit = [dict(zip(aud_cols, r)) for r in cur.fetchall()]

        conn.close()

        dump = {
            "vault_version": "1.0.0",
            "exported_at": datetime.utcnow().isoformat(),
            "documents_count": len(docs),
            "claims_count": len(claims),
            "relations_count": len(relations),
            "documents": docs,
            "claims": claims,
            "citations": citations,
            "claim_relations": relations,
            "audit_events": audit,
        }

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(out)

    def backup_database(self, backup_path: str | Path) -> Tuple[str, str, int]:
        """Consistent online backup via sqlite3.backup API."""
        b_path = Path(backup_path).resolve()
        b_path.parent.mkdir(parents=True, exist_ok=True)

        src = self._get_conn()
        dst = sqlite3.connect(str(b_path))
        src.backup(dst)
        dst.close()
        src.close()

        b_bytes = b_path.read_bytes()
        sha = hashlib.sha256(b_bytes).hexdigest()
        size = len(b_bytes)
        return str(b_path), sha, size

    def restore_database(self, backup_path: str | Path) -> bool:
        """Restore database from backup file with integrity checks."""
        b_path = Path(backup_path).resolve()
        if not b_path.exists():
            raise FileNotFoundError(f"Backup file not found: {b_path}")

        # Check integrity of source backup
        test_conn = sqlite3.connect(str(b_path))
        cur = test_conn.cursor()
        cur.execute("PRAGMA integrity_check")
        status = cur.fetchone()[0]
        if status != "ok":
            test_conn.close()
            raise ValueError(f"Corrupt backup file: integrity_check returned '{status}'")
        test_conn.close()

        # Perform atomic copy/restore
        dst = sqlite3.connect(str(self.db_path))
        src = sqlite3.connect(str(b_path))
        src.backup(dst)
        src.close()
        dst.close()
        return True
