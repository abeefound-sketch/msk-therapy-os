"""Command Line Interface for MSK-Therapy-OS Knowledge Vault."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from msk_therapy_os.knowledge_vault.vault import KnowledgeVault

DEFAULT_VAULT_DB = Path("knowledge_vault") / "vault.db"


def get_vault(db_path: Path | None = None) -> KnowledgeVault:
    target = db_path or DEFAULT_VAULT_DB
    return KnowledgeVault(db_path=target)


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m msk_therapy_os.knowledge_vault",
        description="Offline Knowledge Vault Management CLI",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_VAULT_DB, help="Path to SQLite vault.db")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: import
    import_parser = subparsers.add_parser("import", help="Import a Markdown or text file")
    import_parser.add_argument("file", type=Path, help="File to import")
    import_parser.add_argument("--namespace", default=None, help="Document namespace override")
    import_parser.add_argument("--author", default=None, help="Author name")
    import_parser.add_argument("--actor", default="cli_user", help="Actor logging the event")

    # Subcommand: search
    search_parser = subparsers.add_parser("search", help="Search vault via full text or keyword")
    search_parser.add_argument("query", help="Search query string")
    search_parser.add_argument("--namespace", default=None, help="Filter by namespace")
    search_parser.add_argument("--status", default=None, help="Filter by status")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")

    # Subcommand: claim
    claim_parser = subparsers.add_parser("claim", help="Claim management")
    claim_sub = claim_parser.add_subparsers(dest="claim_action", required=True)
    claim_add = claim_sub.add_parser("add", help="Add a claim")
    claim_add.add_argument("--doc", required=True, help="Document ID")
    claim_add.add_argument("--text", required=True, help="Claim statement text")
    claim_add.add_argument("--quote", required=True, help="Exact source quote")
    claim_add.add_argument("--type", default="ANATOMICAL_LOCATION", help="Claim type")
    claim_add.add_argument("--status", default="UNREVIEWED", help="Claim status")

    # Subcommand: conflict
    conflict_parser = subparsers.add_parser("conflict", help="Contradictory claims management")
    conflict_sub = conflict_parser.add_subparsers(dest="conflict_action", required=True)
    conflict_add = conflict_sub.add_parser("add", help="Record a contradiction between two claims")
    conflict_add.add_argument("--claim1", required=True, help="First Claim ID")
    conflict_add.add_argument("--claim2", required=True, help="Second Claim ID")
    conflict_add.add_argument("--notes", default="", help="Conflict notes or rationale")
    conflict_sub.add_parser("list", help="List all contradictory claim pairings")

    # Subcommand: export
    export_parser = subparsers.add_parser("export", help="Export vault data")
    export_parser.add_argument("--out", type=Path, required=True, help="Output JSON path")

    # Subcommand: backup
    backup_parser = subparsers.add_parser("backup", help="Create consistent SQLite backup")
    backup_parser.add_argument("--out", type=Path, required=True, help="Backup destination path")

    # Subcommand: restore
    restore_parser = subparsers.add_parser("restore", help="Restore database from backup")
    restore_parser.add_argument("--in", dest="input_path", type=Path, required=True, help="Backup source path")

    # Subcommand: stats
    subparsers.add_parser("stats", help="Display vault statistics")

    parsed = parser.parse_args(args)
    vault = get_vault(parsed.db)

    if parsed.command == "import":
        meta = {}
        if parsed.namespace:
            meta["namespace"] = parsed.namespace
        if parsed.author:
            meta["author"] = parsed.author
        doc = vault.import_file(parsed.file, metadata=meta, actor=parsed.actor)
        print(f"[v] Imported: doc_id={doc.doc_id}, title='{doc.title}', sha256={doc.sha256_hash[:16]}...")
        return 0

    elif parsed.command == "search":
        results = vault.search(parsed.query, namespace=parsed.namespace, status=parsed.status, limit=parsed.limit)
        print(f"[i] Search '{parsed.query}': {len(results)} matches found")
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r.result_type}] ID={r.id} | {r.title_or_code} | {r.namespace} | Status={r.status}")
            print(f"     Snippet: {r.snippet}")
        return 0

    elif parsed.command == "claim":
        if parsed.claim_action == "add":
            c = vault.add_claim(
                doc_id=parsed.doc,
                claim_text=parsed.text,
                source_quote=parsed.quote,
                claim_type=parsed.type,
                status=parsed.status,
            )
            print(f"[v] Added Claim: ID={c.claim_id}, status={c.status}")
            return 0

    elif parsed.command == "conflict":
        if parsed.conflict_action == "add":
            rel = vault.add_conflict(parsed.claim1, parsed.claim2, notes=parsed.notes)
            print(f"[v] Conflict recorded: ID={rel.relation_id} between {parsed.claim1} and {parsed.claim2}")
            return 0
        elif parsed.conflict_action == "list":
            confs = vault.list_conflicts()
            print(f"[i] Total Contradictory Claim Pairings: {len(confs)}")
            for c in confs:
                print(f"  * Conflict ID: {c['relation_id']}")
                print(f"    - Claim 1 ({c['claim_1']['id']} / {c['claim_1']['status']}): \"{c['claim_1']['text']}\" [Source: {c['claim_1']['doc_title']}]")
                print(f"    - Claim 2 ({c['claim_2']['id']} / {c['claim_2']['status']}): \"{c['claim_2']['text']}\" [Source: {c['claim_2']['doc_title']}]")
                print(f"    - Notes: {c['notes']}")
            return 0

    elif parsed.command == "export":
        out = vault.export_json(parsed.out)
        print(f"[v] Vault exported to {out}")
        return 0

    elif parsed.command == "backup":
        p, sha, sz = vault.backup_database(parsed.out)
        print(f"[v] Backup created at {p}: size={sz} bytes, sha256={sha}")
        return 0

    elif parsed.command == "restore":
        vault.restore_database(parsed.input_path)
        print(f"[v] Restored database from {parsed.input_path}")
        return 0

    elif parsed.command == "stats":
        conn = vault._get_conn()
        cur = conn.cursor()
        d_cnt = cur.execute("SELECT count(*) FROM documents").fetchone()[0]
        c_cnt = cur.execute("SELECT count(*) FROM claims").fetchone()[0]
        r_cnt = cur.execute("SELECT count(*) FROM claim_relations WHERE relationship_type = 'CONTRADICTS'").fetchone()[0]
        a_cnt = cur.execute("SELECT count(*) FROM audit_events").fetchone()[0]
        conn.close()
        print(f"=== Knowledge Vault Statistics ===")
        print(f"  * Documents:    {d_cnt}")
        print(f"  * Claims:       {c_cnt}")
        print(f"  * Conflicts:    {r_cnt}")
        print(f"  * Audit Events: {a_cnt}")
        print(f"  * FTS5 Search:  {'ENABLED' if vault._has_fts5 else 'FALLBACK_LIKE'}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
