"""M2.8.1 Security Audit, Governance Tier, and Dynamic Reconciliation Test Suite."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

import pytest

from msk_therapy_os.db import init_db, open_db, seed_db
from msk_therapy_os.points import (
    ALLOWED_CLINICAL_CREDENTIALS,
    backup_database,
    create_point,
    delete_reference_override,
    get_point,
    get_safe_backup_path,
    init_points_tables,
    list_custom_points,
    rollback_database,
    run_database_integrity_check,
    sanitize_backup_filename,
    set_reference_override,
    soft_delete_point,
    validate_governance_tier,
)
from msk_therapy_os.server import MAX_JSON_PAYLOAD_SIZE, create_server


class TestSecurityAndGovernanceUnit(unittest.TestCase):
    """Unit tests for backup path safety, governance rules, and checksum integrity."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_sec.sqlite3"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA foreign_keys=ON")
        init_points_tables(self.conn)

    def tearDown(self):
        self.conn.close()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_sanitize_backup_filename_traversal_rejection(self):
        """Verify path traversal sequences are rejected."""
        traversal_attempts = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "../backup.sqlite3",
            "..\\backup.sqlite3",
            "sub/dir/backup.sqlite3",
            "backup\0nullbyte.sqlite3",
            "bad;name.sqlite3",
            "bad name with spaces.sqlite3",
        ]
        for attempt in traversal_attempts:
            with self.assertRaises(ValueError, msg=f"Should reject: {attempt}"):
                sanitize_backup_filename(attempt)

    def test_sanitize_backup_filename_valid_names(self):
        """Verify clean alphanumeric backup filenames are accepted."""
        valid_names = [
            "backup_2026_10_22.sqlite3",
            "clinical-snapshot-01.sqlite3",
            "snapshot_v1.sqlite3",
        ]
        for name in valid_names:
            sanitized = sanitize_backup_filename(name)
            self.assertEqual(sanitized, name)

        # Automatically append .sqlite3 if omitted
        self.assertEqual(sanitize_backup_filename("my_backup"), "my_backup.sqlite3")

    def test_get_safe_backup_path_directory_containment(self):
        """Verify get_safe_backup_path strictly resolves within approved base directory."""
        base_dir = Path(self.temp_dir.name) / "backups"
        safe_path = get_safe_backup_path("daily_snap.sqlite3", base_dir=base_dir)
        self.assertTrue(str(safe_path).startswith(str(base_dir.resolve())))
        self.assertEqual(safe_path.name, "daily_snap.sqlite3")

    def test_governance_tier_credential_enforcement(self):
        """Verify ANATOMY_REVIEWED requires recognized clinical credentials."""
        # Uncredentialed reviewer must fail
        with self.assertRaises(ValueError) as ctx:
            validate_governance_tier(
                "ANATOMY_REVIEWED",
                reviewer="John Doe",
                evidence_id="EVID-A-001",
                uncertainty_radius_mm=3.5,
                db=self.conn
            )
        self.assertIn("lacks verifiable clinical credentials", str(ctx.exception))

        # Credentialed reviewers must succeed
        valid_reviewers = [
            "Dr. Sarah Chen, MD",
            "Li Wei, LAc",
            "Robert Vance, PT, DPT",
            "David Miller, DC",
            "Prof. Elena Rostova, PhD",
            "Dr. Marcus Brown, DO",
            "Dr. Priya Patel, MBBS, FACP",
            "Hanna Kim, ND",
        ]
        for rev in valid_reviewers:
            validate_governance_tier(
                "ANATOMY_REVIEWED",
                reviewer=rev,
                evidence_id="EVID-A-001",
                uncertainty_radius_mm=2.5,
                db=self.conn
            )

    def test_governance_tier_uncertainty_radius_bounds(self):
        """Verify localization uncertainty radius is strictly bounded to (0.0, 25.0] mm."""
        # Negative -> non-negative error
        with self.assertRaises(ValueError) as ctx:
            validate_governance_tier(
                "ANATOMY_REVIEWED",
                reviewer="Dr. Sarah Chen, MD",
                evidence_id="EVID-A-001",
                uncertainty_radius_mm=-1.0,
                db=self.conn
            )
        self.assertIn("non-negative", str(ctx.exception))

        # Zero -> bounded error
        with self.assertRaises(ValueError) as ctx:
            validate_governance_tier(
                "ANATOMY_REVIEWED",
                reviewer="Dr. Sarah Chen, MD",
                evidence_id="EVID-A-001",
                uncertainty_radius_mm=0.0,
                db=self.conn
            )
        self.assertIn("physically bounded", str(ctx.exception))

        # Exceeds 25.0mm -> bounded error
        with self.assertRaises(ValueError) as ctx:
            validate_governance_tier(
                "ANATOMY_REVIEWED",
                reviewer="Dr. Sarah Chen, MD",
                evidence_id="EVID-A-001",
                uncertainty_radius_mm=30.0,
                db=self.conn
            )
        self.assertIn("physically bounded", str(ctx.exception))

        # Valid radius passes
        validate_governance_tier(
            "ANATOMY_REVIEWED",
            reviewer="Dr. Sarah Chen, MD",
            evidence_id="EVID-A-001",
            uncertainty_radius_mm=5.0,
            db=self.conn
        )

    def test_governance_tier_evidence_catalog_validation(self):
        """Verify uncataloged evidence IDs are rejected."""
        with self.assertRaises(ValueError) as ctx:
            validate_governance_tier(
                "ANATOMY_REVIEWED",
                reviewer="Dr. Sarah Chen, MD",
                evidence_id="NON_EXISTENT_CITATION_999",
                uncertainty_radius_mm=3.0,
                db=self.conn
            )
        self.assertIn("is not registered in evidence_catalog", str(ctx.exception))

        # Recognized standard passes
        validate_governance_tier(
            "ANATOMY_REVIEWED",
            reviewer="Dr. Sarah Chen, MD",
            evidence_id="WHO-2008",
            uncertainty_radius_mm=3.0,
            db=self.conn
        )

    def test_custom_point_cannot_claim_official_standard(self):
        """Verify user custom points are rejected if claiming OFFICIAL_STANDARD review status."""
        pt_data = {
            "code": "CUST-OFFICIAL-FAIL",
            "name_en": "Illegal Claim Point",
            "position": [0.01, 1.5, -0.05],
            "registration_status": "GEOMETRY_VERIFIED",
            "review_status": "OFFICIAL_STANDARD",
        }
        with self.assertRaises(ValueError) as ctx:
            create_point(self.conn, pt_data)
        self.assertIn("cannot claim 'OFFICIAL_STANDARD'", str(ctx.exception))

    def test_backup_creates_sha256_checksum_and_verifies_on_restore(self):
        """Verify backup generates SHA-256 and restore verifies integrity."""
        backup_file = Path(self.temp_dir.name) / "clean_backup.sqlite3"
        b_res = backup_database(self.conn, str(backup_file))
        self.assertEqual(b_res["status"], "SUCCESS")
        self.assertIn("sha256_checksum", b_res)

        sha_file = backup_file.with_suffix(backup_file.suffix + ".sha256")
        self.assertTrue(sha_file.exists())
        self.assertIn(b_res["sha256_checksum"], sha_file.read_text(encoding="utf-8"))

        # Tamper with backup file
        target_db = Path(self.temp_dir.name) / "restored.sqlite3"
        backup_file.write_bytes(backup_file.read_bytes() + b"\x00CORRUPT")

        # Rollback should fail due to checksum mismatch or SQLite integrity check
        with self.assertRaises(ValueError) as ctx:
            rollback_database(str(target_db), str(backup_file))
        self.assertTrue("checksum mismatch" in str(ctx.exception) or "integrity check failed" in str(ctx.exception))


class TestSecurityAndGovernanceIntegration(unittest.TestCase):
    """Integration tests for HTTP endpoints: payload limits, origin checks, and reconciliation."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = str(Path(cls.temp_dir.name) / "test_api_sec.sqlite3")

        with open_db(cls.db_path) as db:
            init_db(db)
            seed_db(db)

        cls.server = create_server(cls.db_path, host="127.0.0.1", port=0)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1.0)
        time.sleep(0.1)
        try:
            cls.temp_dir.cleanup()
        except Exception:
            pass

    def test_backup_path_traversal_via_api(self):
        """Verify API prevents directory traversal in backup name parameter."""
        payload = json.dumps({"name": "../../traversal_attack.sqlite3"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/governance/backup",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("error", data)
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            err_data = json.loads(e.read().decode("utf-8"))
            self.assertIn("Path traversal", err_data["error"])

    def test_payload_size_limit_rejection(self):
        """Verify API rejects request bodies exceeding 5MB payload limit."""
        # Simulate oversized payload header
        large_len = MAX_JSON_PAYLOAD_SIZE + 1024
        req = urllib.request.Request(
            f"{self.base_url}/api/points",
            data=b"{}",
            headers={"Content-Type": "application/json", "Content-Length": str(large_len)}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                self.fail("Should not accept payload > 5MB")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            err_data = json.loads(e.read().decode("utf-8"))
            self.assertIn("Payload too large", err_data["error"])

    def test_malformed_json_rejection(self):
        """Verify API rejects malformed JSON cleanly with HTTP 400."""
        req = urllib.request.Request(
            f"{self.base_url}/api/points",
            data=b"{not valid json: true,",
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                self.fail("Should not accept malformed JSON")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            err_data = json.loads(e.read().decode("utf-8"))
            self.assertIn("Malformed JSON", err_data["error"])

    def test_cors_origin_protection_on_write(self):
        """Verify POST requests from foreign external web origins are rejected with 403 Forbidden."""
        payload = json.dumps({
            "code": "EX-ATTACK-01",
            "name_en": "Malicious Point",
            "position": [0.0, 1.5, 0.0]
        }).encode("utf-8")

        # External untrusted origin
        req_foreign = urllib.request.Request(
            f"{self.base_url}/api/points",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Origin": "https://malicious-tracker.com"
            }
        )
        try:
            with urllib.request.urlopen(req_foreign) as resp:
                self.fail("Should reject external web origin")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)
            err = json.loads(e.read().decode("utf-8"))
            self.assertIn("Forbidden", err["error"])

        # Local trusted origin
        req_local = urllib.request.Request(
            f"{self.base_url}/api/points",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Origin": f"http://127.0.0.1:{self.port}"
            }
        )
        with urllib.request.urlopen(req_local) as resp:
            self.assertEqual(resp.status, 201)
            res_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res_data["status"], "created")

    def test_dynamic_reconciliation_math_lifecycle(self):
        """Verify dynamic point total updates dynamically upon point creation, deletion, and restoration."""
        # 1. Fetch initial reconciliation state
        req_init = urllib.request.Request(f"{self.base_url}/api/governance/reconciliation")
        with urllib.request.urlopen(req_init) as resp:
            init_data = json.loads(resp.read().decode("utf-8"))
            init_custom = init_data["active_custom_count"]
            init_total = init_data["runtime_total_points"]
            # 362 canonical points + 4 Dien Chan + existing custom points
            self.assertEqual(init_total, 362 + 4 + init_custom)

        # 2. Create custom point
        new_pt_payload = json.dumps({
            "code": f"DYN-TEST-{int(time.time())}",
            "name_en": "Dynamic Reconciliation Point",
            "position": [0.02, 1.55, -0.06]
        }).encode("utf-8")
        req_create = urllib.request.Request(
            f"{self.base_url}/api/points",
            data=new_pt_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_create) as resp:
            created_data = json.loads(resp.read().decode("utf-8"))["point"]
            created_id = created_data["point_id"]

        # Verify count incremented
        with urllib.request.urlopen(req_init) as resp:
            post_create_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(post_create_data["active_custom_count"], init_custom + 1)
            self.assertEqual(post_create_data["runtime_total_points"], init_total + 1)

        # 3. Soft-delete custom point
        req_del = urllib.request.Request(
            f"{self.base_url}/api/points/{created_id}/delete",
            data=b"{}",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_del) as resp:
            self.assertEqual(resp.status, 200)

        # Verify count decremented
        with urllib.request.urlopen(req_init) as resp:
            post_del_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(post_del_data["active_custom_count"], init_custom)
            self.assertEqual(post_del_data["runtime_total_points"], init_total)

        # 4. Restore custom point
        req_restore = urllib.request.Request(
            f"{self.base_url}/api/points/{created_id}/restore",
            data=b"{}",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_restore) as resp:
            self.assertEqual(resp.status, 200)

        # Verify count restored
        with urllib.request.urlopen(req_init) as resp:
            post_restore_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(post_restore_data["active_custom_count"], init_custom + 1)
            self.assertEqual(post_restore_data["runtime_total_points"], init_total + 1)

    def test_transactional_rollback_on_server_error(self):
        """Verify server failure cleanly rolls back SQLite transaction without orphaned records."""
        with open_db(self.db_path) as db:
            before_count = db.execute("SELECT COUNT(*) FROM custom_points").fetchone()[0]

        # Send invalid point coordinates (outside anatomical envelope)
        invalid_payload = json.dumps({
            "code": "INVALID-COORD-POINT",
            "name_en": "Out of Envelope Point",
            "position": [999.0, 999.0, 999.0]
        }).encode("utf-8")
        req_fail = urllib.request.Request(
            f"{self.base_url}/api/points",
            data=invalid_payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req_fail) as resp:
                self.fail("Should reject out-of-envelope point")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)

        with open_db(self.db_path) as db:
            after_count = db.execute("SELECT COUNT(*) FROM custom_points").fetchone()[0]
            self.assertEqual(before_count, after_count, "Database must cleanly rollback failed transaction")
