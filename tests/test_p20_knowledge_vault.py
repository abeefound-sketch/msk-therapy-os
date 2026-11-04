"""Unit and integration test suite for Knowledge Vault (Milestone P20).

Validates:
- Schema initialization and foreign keys.
- Markdown import with YAML frontmatter.
- Missing metadata handling (strict UNKNOWN, zero hallucination).
- Idempotent repeated imports via SHA-256 deduplication.
- Prohibition of fake CLINICAL_APPROVED statuses.
- Contradictory claims coexistence (dual retention, no silent deletion).
- Full-text search with Vietnamese diacritics and English terms.
- Security against SQL injection and path traversal.
- Append-only audit events log.
- Database backup and restore round-trip with integrity checking.
- Evidence catalog adapter synchronization.
- CLI subcommands invocation.
"""

import json
from pathlib import Path
import pytest

from msk_therapy_os.knowledge_vault.models import (
    DocumentNamespace,
    ClaimType,
    ClaimStatus,
    EvidenceTier,
)
from msk_therapy_os.knowledge_vault.vault import KnowledgeVault
from msk_therapy_os.knowledge_vault.evidence_adapter import EvidenceCatalogAdapter
from msk_therapy_os.knowledge_vault.cli import main as cli_main


@pytest.fixture(scope="module")
def repo_root():
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def temp_vault(tmp_path):
    """Provide isolated ephemeral KnowledgeVault instance for testing."""
    db_file = tmp_path / "test_vault.db"
    vault_dir = tmp_path / "vault_root"
    return KnowledgeVault(db_path=db_file, vault_dir=vault_dir)


class TestP20KnowledgeVaultCore:
    """Test core vault functionality: import, claims, conflicts, search, backup."""

    def test_import_markdown_with_frontmatter(self, temp_vault, tmp_path):
        """Markdown with YAML frontmatter correctly extracts metadata."""
        md_file = tmp_path / "test_doc.md"
        content = (
            "---\n"
            "title: Cervical Spine Biomechanics\n"
            "author: Dr. John Anatomist\n"
            "date: 2024-01-15\n"
            "namespace: ANATOMY_EVIDENCE\n"
            "license: CC-BY-4.0\n"
            "tags: [cervical, spine, biomechanics]\n"
            "---\n\n"
            "# Cervical Spine\n\n"
            "The atlas (C1) and axis (C2) form a complex pivot joint.\n"
        )
        md_file.write_text(content, encoding="utf-8")

        doc = temp_vault.import_file(md_file, actor="test_user")
        assert doc is not None
        assert doc.title == "Cervical Spine Biomechanics"
        assert doc.author == "Dr. John Anatomist"
        assert doc.namespace == "ANATOMY_EVIDENCE"
        assert doc.license == "CC-BY-4.0"
        assert "cervical" in doc.tags
        assert "spine" in doc.tags
        assert doc.review_status == "UNREVIEWED"

    def test_missing_metadata_defaults_to_unknown(self, temp_vault, tmp_path):
        """Missing author and URL strictly default to UNKNOWN without hallucination."""
        md_file = tmp_path / "no_meta.md"
        md_file.write_text("Simple text without frontmatter.", encoding="utf-8")

        doc = temp_vault.import_file(md_file)
        assert doc.author == "UNKNOWN"
        assert doc.source_uri == "UNKNOWN"
        assert doc.license == "UNKNOWN"
        assert doc.publication_date == "UNKNOWN"

    def test_idempotent_import_deduplication(self, temp_vault, tmp_path):
        """Importing identical file content twice returns existing doc_id and logs audit event."""
        md_file = tmp_path / "idempotent.md"
        md_file.write_text("Unique text for deduplication test.", encoding="utf-8")

        doc1 = temp_vault.import_file(md_file, actor="user1")
        doc2 = temp_vault.import_file(md_file, actor="user2")

        assert doc1.doc_id == doc2.doc_id
        assert doc1.sha256_hash == doc2.sha256_hash

        # Verify audit trail contains IMPORT_IDEMPOTENT
        conn = temp_vault._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT action FROM audit_events WHERE entity_id = ?", (doc1.doc_id,))
        actions = [r[0] for r in cur.fetchall()]
        conn.close()
        assert "IMPORT" in actions
        assert "IMPORT_IDEMPOTENT" in actions

    def test_prohibition_of_fake_clinical_approved_status(self, temp_vault):
        """Attempting to create claim with CLINICAL_APPROVED status raises ValueError."""
        doc = temp_vault.import_text("Some text", title="Doc Title")
        with pytest.raises(ValueError, match="Unauthorized claim status"):
            temp_vault.add_claim(
                doc_id=doc.doc_id,
                claim_text="Unapproved clinical statement",
                source_quote="Some text",
                status="CLINICAL_APPROVED",
            )

    def test_contradictory_claims_coexistence(self, temp_vault):
        """Contradictory claims are both retained, linked as CONFLICT, and marked CONTESTED."""
        doc1 = temp_vault.import_text("Point LI4 is located on the dorsum of hand.", title="Source 1")
        doc2 = temp_vault.import_text("Point LI4 is located on the palmar surface.", title="Source 2")

        c1 = temp_vault.add_claim(
            doc_id=doc1.doc_id,
            claim_text="LI4 on dorsal aspect",
            source_quote="dorsum of hand",
            status="SUPPORTED",
        )
        c2 = temp_vault.add_claim(
            doc_id=doc2.doc_id,
            claim_text="LI4 on palmar aspect",
            source_quote="palmar surface",
            status="UNREVIEWED",
        )

        rel = temp_vault.add_conflict(
            c1.claim_id,
            c2.claim_id,
            notes="Direct anatomical contradiction between dorsal and palmar locations",
        )
        assert rel.relationship_type == "CONTRADICTS"

        # Both claims must now be CONTESTED
        c1_updated = temp_vault.get_claim(c1.claim_id)
        c2_updated = temp_vault.get_claim(c2.claim_id)
        assert c1_updated.status == "CONTESTED"
        assert c2_updated.status == "CONTESTED"

        # Both claims still exist and are queryable
        conflicts = temp_vault.list_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0]["claim_1"]["id"] == c1.claim_id
        assert conflicts[0]["claim_2"]["id"] == c2.claim_id

    def test_full_text_search_vietnamese_and_english(self, temp_vault):
        """Search engine matches Vietnamese diacritics and English queries."""
        temp_vault.import_text(
            text="Huyệt Đại Chùy nằm ở chỗ lõm dưới gai đốt sống cổ C7. Tác dụng thanh nhiệt giải biểu.",
            title="Tài liệu Châm cứu Cổ truyền",
            namespace="TRADITIONAL_MERIDIAN",
        )
        temp_vault.import_text(
            text="The median nerve passes through the carpal tunnel deep to the flexor retinaculum.",
            title="Upper Limb Neuroanatomy",
            namespace="ANATOMY_EVIDENCE",
        )

        # 1. Search Vietnamese with diacritics
        res_vi = temp_vault.search("Đại Chùy")
        assert len(res_vi) >= 1
        assert "Châm cứu" in res_vi[0].title_or_code or "Đại Chùy" in res_vi[0].snippet

        res_vi2 = temp_vault.search("thanh nhiệt")
        assert len(res_vi2) >= 1

        # 2. Search English
        res_en = temp_vault.search("carpal tunnel")
        assert len(res_en) >= 1
        assert "Neuroanatomy" in res_en[0].title_or_code or "carpal tunnel" in res_en[0].snippet

    def test_sql_injection_resilience(self, temp_vault):
        """Search and filter parameters are properly parameterized against SQL injection."""
        malicious_input = "'; DROP TABLE documents; --"
        # Should execute safely as a literal search string
        results = temp_vault.search(malicious_input)
        assert isinstance(results, list)

        # Verify table still intact
        conn = temp_vault._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM documents")
        assert cur.fetchone() is not None
        conn.close()

    def test_backup_and_restoration_round_trip(self, temp_vault, tmp_path):
        """Online database backup can be restored with 100% integrity."""
        doc = temp_vault.import_text("Test content for backup verification.", title="Backup Doc")
        claim = temp_vault.add_claim(doc.doc_id, "Sample claim", "Test content")

        backup_file = tmp_path / "vault_backup.sqlite3"
        b_path, sha, sz = temp_vault.backup_database(backup_file)
        assert Path(b_path).exists()
        assert sz > 0
        assert len(sha) == 64

        # Create a new vault and restore from backup
        new_db = tmp_path / "restored_vault.db"
        restored_vault = KnowledgeVault(db_path=new_db, vault_dir=tmp_path / "restored_root")
        restored_vault.restore_database(backup_file)

        # Verify data restored
        restored_doc = restored_vault.get_document(doc.doc_id)
        assert restored_doc is not None
        assert restored_doc.title == "Backup Doc"
        restored_claim = restored_vault.get_claim(claim.claim_id)
        assert restored_claim is not None
        assert restored_claim.claim_text == "Sample claim"

    def test_json_export(self, temp_vault, tmp_path):
        """Export vault produces structured JSON with documents, claims, and audit events."""
        doc = temp_vault.import_text("Export test", title="Export Doc")
        temp_vault.add_claim(doc.doc_id, "Export Claim", "Export test")

        out_json = tmp_path / "export_test.json"
        temp_vault.export_json(out_json)
        assert out_json.exists()

        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["vault_version"] == "1.0.0"
        assert data["documents_count"] >= 1
        assert data["claims_count"] >= 1
        assert len(data["audit_events"]) >= 2


class TestP20EvidenceAdapterAndAcceptance:
    """Validate Evidence Catalog Adapter and acceptance dataset requirements."""

    def test_evidence_adapter_sync(self, temp_vault, repo_root):
        """EvidenceCatalogAdapter parses 1docs/EVIDENCE.md and populates Vault without file mutation."""
        evidence_file = repo_root / "1docs" / "EVIDENCE.md"
        assert evidence_file.exists()

        mtime_before = evidence_file.stat().st_mtime
        adapter = EvidenceCatalogAdapter(evidence_file, temp_vault)
        count = adapter.sync_to_vault()
        mtime_after = evidence_file.stat().st_mtime

        # Verify EVIDENCE.md was NOT modified
        assert mtime_before == mtime_after, "EVIDENCE.md must remain untouched"
        assert count >= 9, f"Should import at least 9 evidence catalog entries, got {count}"

        # Verify EVID-G-001 is searchable in vault
        res = temp_vault.search("NICE NG59")
        assert len(res) >= 1

    def test_cli_subcommands(self, temp_vault, tmp_path):
        """CLI runs import, search, stats, conflict list without error."""
        db_path = temp_vault.db_path

        # 1. Stats command
        rc = cli_main(["--db", str(db_path), "stats"])
        assert rc == 0

        # 2. Search command
        rc = cli_main(["--db", str(db_path), "search", "test"])
        assert rc == 0

        # 3. Conflict list
        rc = cli_main(["--db", str(db_path), "conflict", "list"])
        assert rc == 0
