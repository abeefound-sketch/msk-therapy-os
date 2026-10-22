"""Test suite for M2.8.2 Native SQLite Online Backup & Safe Restore API."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

from msk_therapy_os.db import init_db, open_db, seed_db
from msk_therapy_os.points import (
    IS_MAINTENANCE_ACTIVE,
    MAINTENANCE_LOCK,
    backup_database,
    create_point,
    init_points_tables,
    list_custom_points,
    restore_database_safely,
    rollback_database,
    run_database_integrity_check,
)
from msk_therapy_os.server import create_server


class TestSafeSQLiteRestoreUnit(unittest.TestCase):
    """Unit tests for native backup API restore, checksum validation, and atomic rollback."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "live.sqlite3"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA foreign_keys=ON")
        init_db(self.conn)
        seed_db(self.conn)

    def tearDown(self):
        self.conn.close()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_native_backup_and_safe_restore_lifecycle(self):
        """Verify clean backup snapshot generation and native backup API restoration."""
        # 1. Create a custom point in live DB
        pt = create_point(self.conn, {
            "code": "PRE-BACKUP-01",
            "name_en": "Pre Backup Point",
            "position": [0.01, 1.50, -0.05]
        })
        self.assertIsNotNone(pt["point_id"])

        # 2. Take backup
        backup_file = Path(self.temp_dir.name) / "snapshot_01.sqlite3"
        b_res = backup_database(self.conn, str(backup_file))
        self.assertEqual(b_res["status"], "SUCCESS")
        self.assertEqual(b_res["backup_path"], str(backup_file.resolve()))
        self.assertTrue(backup_file.exists())
        self.assertTrue(backup_file.with_suffix(".sqlite3.sha256").exists())

        # 3. Mutate live DB (create another point, delete original)
        pt2 = create_point(self.conn, {
            "code": "POST-BACKUP-MUTATION",
            "name_en": "Post Backup Mutation",
            "position": [0.02, 1.51, -0.06]
        })
        self.conn.execute("DELETE FROM custom_points WHERE code = 'PRE-BACKUP-01'")
        self.conn.commit()

        # Verify mutation took effect
        live_codes = [p["code"] for p in list_custom_points(self.conn, include_deleted=True)]
        self.assertNotIn("PRE-BACKUP-01", live_codes)
        self.assertIn("POST-BACKUP-MUTATION", live_codes)

        # 4. Perform safe restore using native SQLite backup API
        self.conn.close()  # close our connection so target file is free
        r_res = restore_database_safely(str(self.db_path), str(backup_file))
        self.assertEqual(r_res["status"], "SUCCESS")
        self.assertEqual(r_res["method"], "sqlite3_online_backup_api")

        # 5. Reopen live DB and verify restored state
        self.conn = sqlite3.connect(str(self.db_path))
        restored_codes = [p["code"] for p in list_custom_points(self.conn, include_deleted=True)]
        self.assertIn("PRE-BACKUP-01", restored_codes)
        self.assertNotIn("POST-BACKUP-MUTATION", restored_codes)

        # Verify integrity & foreign keys
        audit = run_database_integrity_check(self.conn)
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["integrity_check"], "ok")
        self.assertEqual(audit["foreign_key_violations_count"], 0)

    def test_restore_rejects_checksum_mismatch(self):
        """Verify restore aborts immediately if SHA-256 digest fails."""
        backup_file = Path(self.temp_dir.name) / "snapshot_tamper.sqlite3"
        backup_database(self.conn, str(backup_file))

        # Tamper with companion .sha256 file
        sha_file = backup_file.with_suffix(".sqlite3.sha256")
        sha_file.write_text("0000000000000000000000000000000000000000000000000000000000000000  snapshot_tamper.sqlite3\n")

        with self.assertRaises(ValueError) as ctx:
            restore_database_safely(str(self.db_path), str(backup_file))
        self.assertIn("checksum mismatch", str(ctx.exception).lower())

    def test_restore_rejects_corrupted_sqlite_file(self):
        """Verify restore aborts if backup fails PRAGMA integrity_check."""
        corrupt_file = Path(self.temp_dir.name) / "corrupt.sqlite3"
        # Write corrupted header / non-sqlite data
        corrupt_file.write_bytes(b"SQLite format 3\x00CORRUPTED_DATABASE_PAGE_DATA_JUNK")

        with self.assertRaises(ValueError) as ctx:
            restore_database_safely(str(self.db_path), str(corrupt_file))
        self.assertTrue("integrity check failed" in str(ctx.exception).lower() or "invalid or corrupted" in str(ctx.exception).lower())

    def test_restore_rejects_incompatible_schema(self):
        """Verify restore aborts if backup lacks required clinical/point tables."""
        incompat_file = Path(self.temp_dir.name) / "incompat.sqlite3"
        inc_conn = sqlite3.connect(str(incompat_file))
        inc_conn.execute("CREATE TABLE irrelevant_data (id INT, note TEXT)")
        inc_conn.execute("INSERT INTO irrelevant_data VALUES (1, 'hello')")
        inc_conn.commit()
        inc_conn.close()

        with self.assertRaises(ValueError) as ctx:
            restore_database_safely(str(self.db_path), str(incompat_file))
        self.assertIn("missing required tables", str(ctx.exception))


class TestSafeSQLiteRestoreIntegration(unittest.TestCase):
    """Integration test proving HTTP 503 maintenance mode during backup/restore and admin RBAC."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = str(Path(cls.temp_dir.name) / "test_restore_server.sqlite3")

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

    def _login_admin(self):
        payload = json.dumps({"username": "admin", "password": "admin123"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/auth/login",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["session_token"], data["csrf_token"]

    def test_http_503_maintenance_mode_during_restore(self):
        """Verify concurrent requests receive HTTP 503 Service Unavailable when maintenance lock is active."""
        from msk_therapy_os import points

        # Artificially activate maintenance lock to test server response
        points.IS_MAINTENANCE_ACTIVE = True
        try:
            req = urllib.request.Request(f"{self.base_url}/api/cases")
            try:
                with urllib.request.urlopen(req) as resp:
                    self.fail("Server should return 503 during maintenance mode")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 503)
                self.assertEqual(e.headers.get("Retry-After"), "5")
                err_data = json.loads(e.read().decode("utf-8"))
                self.assertIn("maintenance", err_data["error"].lower())
        finally:
            points.IS_MAINTENANCE_ACTIVE = False

        # Once maintenance is released, server resumes normal 200 responses
        req_resumed = urllib.request.Request(f"{self.base_url}/api/cases")
        with urllib.request.urlopen(req_resumed) as resp:
            self.assertEqual(resp.status, 200)

    def test_api_restore_flow_with_admin_auth(self):
        """Verify complete backup -> modify -> restore workflow through the HTTP API."""
        a_tok, a_csrf = self._login_admin()

        # 1. Trigger backup via API
        snap_name = "e2e_api_snapshot.sqlite3"
        b_req = urllib.request.Request(
            f"{self.base_url}/api/governance/backup",
            data=json.dumps({"name": snap_name, "csrf_token": a_csrf}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {a_tok}",
                "X-CSRF-Token": a_csrf
            }
        )
        with urllib.request.urlopen(b_req) as resp:
            self.assertEqual(resp.status, 200)
            b_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(b_data["status"], "SUCCESS")

        # 2. Add custom point
        pt_req = urllib.request.Request(
            f"{self.base_url}/api/points",
            data=json.dumps({
                "code": "API-POST-BACKUP-PT",
                "name_en": "Point to be reverted",
                "position": [0.05, 1.45, -0.02],
                "csrf_token": a_csrf
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {a_tok}",
                "X-CSRF-Token": a_csrf
            }
        )
        with urllib.request.urlopen(pt_req) as resp:
            self.assertEqual(resp.status, 201)

        # 3. Restore snapshot via API
        r_req = urllib.request.Request(
            f"{self.base_url}/api/governance/restore",
            data=json.dumps({"name": snap_name, "csrf_token": a_csrf}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {a_tok}",
                "X-CSRF-Token": a_csrf
            }
        )
        with urllib.request.urlopen(r_req) as resp:
            self.assertEqual(resp.status, 200)
            r_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(r_data["status"], "SUCCESS")
            self.assertEqual(r_data["method"], "sqlite3_online_backup_api")

        # 4. Check points to confirm restored state
        pts_req = urllib.request.Request(f"{self.base_url}/api/points")
        with urllib.request.urlopen(pts_req) as resp:
            pts = json.loads(resp.read().decode("utf-8"))
            codes = [p["code"] for p in pts]
            self.assertNotIn("API-POST-BACKUP-PT", codes, "Restored state must not contain post-backup mutations")
