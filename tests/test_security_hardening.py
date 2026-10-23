"""Comprehensive Security Regression & Anti-Tamper Hardening Test Suite.

Covers:
1. Strict separation of DEMO MODE vs SECURE MODE.
2. Prevention of unauthenticated demo role elevation in SECURE MODE.
3. Server-side RBAC and CSRF token enforcement.
4. Supervisor credential verification requirement for SOAP approval.
5. Strict synthetic patient boundary enforcement.
6. Cryptographic HMAC-SHA256 backup anti-tamper authentication vs SHA-256 bit-rot.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

from msk_therapy_os.auth import (
    authenticate_user,
    create_session,
    init_auth_tables,
    seed_default_users,
)
from msk_therapy_os.db import init_db, open_db, seed_db
from msk_therapy_os.points import (
    backup_database,
    get_backup_signing_key,
    restore_database_safely,
)
from msk_therapy_os.server import create_server
from msk_therapy_os.soap import create_soap_note


class TestSecurityHardening(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_sec.sqlite3"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA foreign_keys=ON")
        init_db(self.conn)
        seed_db(self.conn)
        self.conn.close()

        # Save env
        self.orig_mode = os.environ.get("MSK_MODE")
        self.orig_sec = os.environ.get("MSK_SECURE_MODE")
        self.orig_ro = os.environ.get("MSK_PUBLIC_DEMO_READONLY")

    def tearDown(self):
        # Restore env
        if self.orig_mode is not None:
            os.environ["MSK_MODE"] = self.orig_mode
        else:
            os.environ.pop("MSK_MODE", None)

        if self.orig_sec is not None:
            os.environ["MSK_SECURE_MODE"] = self.orig_sec
        else:
            os.environ.pop("MSK_SECURE_MODE", None)

        if self.orig_ro is not None:
            os.environ["MSK_PUBLIC_DEMO_READONLY"] = self.orig_ro
        else:
            os.environ.pop("MSK_PUBLIC_DEMO_READONLY", None)

        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def _http_request(self, base_url: str, path: str, method: str = "GET", data: dict | None = None, headers: dict | None = None):
        url = f"{base_url}{path}"
        hdrs = {
            "Origin": "http://127.0.0.1:8080",
            "Content-Type": "application/json",
        }
        if headers:
            hdrs.update(headers)
        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read().decode("utf-8")
                return response.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                parsed = json.loads(err_body)
            except Exception:
                parsed = {"raw": err_body}
            return e.code, parsed

    def test_demo_mode_switch_allowed(self):
        os.environ["MSK_MODE"] = "demo"
        os.environ.pop("MSK_SECURE_MODE", None)
        server = create_server(str(self.db_path), host="127.0.0.1", port=0)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            base = f"http://127.0.0.1:{port}"
            # 1. Check mode
            status, data = self._http_request(base, "/api/auth/mode")
            self.assertEqual(status, 200)
            self.assertEqual(data["mode"], "demo")
            self.assertFalse(data["is_secure"])

            # 2. Demo switch to reviewer
            status, data = self._http_request(base, "/api/auth/demo-switch", method="POST", data={"role": "reviewer"})
            self.assertEqual(status, 200)
            self.assertEqual(data["status"], "authenticated")
            self.assertEqual(data["user"]["role"], "reviewer")
            self.assertIn("session_token", data)
            self.assertIn("csrf_token", data)
        finally:
            server.shutdown()
            server.server_close()

    def test_secure_mode_blocks_demo_switch_and_enforces_auth(self):
        os.environ["MSK_MODE"] = "secure"
        server = create_server(str(self.db_path), host="127.0.0.1", port=0)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            base = f"http://127.0.0.1:{port}"
            # 1. Check mode
            status, data = self._http_request(base, "/api/auth/mode")
            self.assertEqual(status, 200)
            self.assertEqual(data["mode"], "secure")
            self.assertTrue(data["is_secure"])

            # 2. Demo switch must be rejected with 403 Forbidden
            status, data = self._http_request(base, "/api/auth/demo-switch", method="POST", data={"role": "reviewer"})
            self.assertEqual(status, 403)
            self.assertIn("strictly disabled in SECURE mode", data.get("error", ""))

            # 3. Unauthenticated mutation must return 401 Unauthorized
            status, data = self._http_request(base, "/api/visit", method="POST", data={
                "case": "DEMO-NECK-001",
                "when": "2026-10-23",
                "pain": 4,
                "rom": 45.0,
                "region": "neck",
                "flag": "none",
            })
            self.assertEqual(status, 401)
            self.assertIn("Authentication required in SECURE mode", data.get("error", ""))

            # 4. Legitimate login works
            status, auth_data = self._http_request(base, "/api/auth/login", method="POST", data={
                "username": "student",
                "password": "student123",
            })
            self.assertEqual(status, 200)
            sess_tok = auth_data["session_token"]
            csrf_tok = auth_data["csrf_token"]

            # 5. Mutation with valid session token but missing CSRF returns 403
            status, data = self._http_request(
                base, "/api/visit", method="POST",
                data={
                    "case": "DEMO-NECK-001",
                    "when": "2026-10-23",
                    "pain": 4,
                    "rom": 45.0,
                    "region": "neck",
                    "flag": "none",
                },
                headers={"Authorization": f"Bearer {sess_tok}"}
            )
            self.assertEqual(status, 403)
            self.assertIn("CSRF", data.get("error", ""))

            # 6. Mutation with session token + CSRF token succeeds
            status, data = self._http_request(
                base, "/api/visit", method="POST",
                data={
                    "case": "DEMO-NECK-001",
                    "when": "2026-10-23",
                    "pain": 4,
                    "rom": 45.0,
                    "region": "neck",
                    "flag": "none",
                },
                headers={
                    "Authorization": f"Bearer {sess_tok}",
                    "X-CSRF-Token": csrf_tok,
                }
            )
            self.assertEqual(status, 200)
            self.assertEqual(data["status"], "created")
        finally:
            server.shutdown()
            server.server_close()

    def test_soap_approval_privilege_escalation_blocked(self):
        os.environ["MSK_MODE"] = "secure"
        server = create_server(str(self.db_path), host="127.0.0.1", port=0)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            base = f"http://127.0.0.1:{port}"
            # 1. Login as student
            status, login_res = self._http_request(base, "/api/auth/login", method="POST", data={
                "username": "student",
                "password": "student123",
            })
            student_tok = login_res["session_token"]
            student_csrf = login_res["csrf_token"]

            # Create visit 1
            status, vis_res = self._http_request(
                base, "/api/visit", method="POST",
                data={
                    "case": "DEMO-NECK-001",
                    "when": "2026-10-23",
                    "pain": 4,
                    "rom": 45.0,
                    "region": "neck",
                    "flag": "none",
                },
                headers={"Authorization": f"Bearer {student_tok}", "X-CSRF-Token": student_csrf}
            )
            self.assertEqual(status, 200)

            # Create draft SOAP note as student
            status, soap_res = self._http_request(
                base, "/api/soap", method="POST",
                data={
                    "visit_id": 1,
                    "subjective": "Neck soreness after screen work",
                    "objective": "Cervical ROM rotation 45 deg",
                    "assessment": "Postural neck strain",
                    "plan": "Postural ergonomics education",
                },
                headers={"Authorization": f"Bearer {student_tok}", "X-CSRF-Token": student_csrf}
            )
            self.assertEqual(status, 200)
            soap_id = soap_res["soap_id"]

            # 2. Unauthenticated review-soap attempt MUST be rejected (401)
            status, err_res = self._http_request(
                base, "/api/review-soap", method="POST",
                data={"soap_id": soap_id, "decision": "APPROVED", "feedback": "Self-approval attempt"}
            )
            self.assertEqual(status, 401)

            # 3. Student attempt to approve SOAP note MUST be rejected (403)
            status, err_res = self._http_request(
                base, "/api/review-soap", method="POST",
                data={"soap_id": soap_id, "decision": "APPROVED", "feedback": "Student approval"},
                headers={"Authorization": f"Bearer {student_tok}", "X-CSRF-Token": student_csrf}
            )
            self.assertEqual(status, 403)
            self.assertIn("verified 'reviewer' role", err_res.get("error", ""))

            # 4. Verified Clinical Supervisor (Dr. Sarah Chen, MD) approves SOAP note
            status, dr_login = self._http_request(base, "/api/auth/login", method="POST", data={
                "username": "dr_chen",
                "password": "reviewer123",
            })
            dr_tok = dr_login["session_token"]
            dr_csrf = dr_login["csrf_token"]

            status, ok_res = self._http_request(
                base, "/api/review-soap", method="POST",
                data={"soap_id": soap_id, "decision": "APPROVED", "feedback": "Sound clinical reasoning."},
                headers={"Authorization": f"Bearer {dr_tok}", "X-CSRF-Token": dr_csrf}
            )
            self.assertEqual(status, 200)
            self.assertEqual(ok_res["decision"], "APPROVED")
        finally:
            server.shutdown()
            server.server_close()

    def test_synthetic_patient_boundary_enforcement(self):
        server = create_server(str(self.db_path), host="127.0.0.1", port=0)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            base = f"http://127.0.0.1:{port}"
            # Attempting to submit non-synthetic patient ID must be rejected immediately
            status, err_res = self._http_request(
                base, "/api/visit", method="POST",
                data={
                    "case": "REAL-PATIENT-JOHN-DOE-SSN-1234",
                    "when": "2026-10-23",
                    "pain": 5,
                    "rom": 40.0,
                    "region": "neck",
                    "flag": "none",
                }
            )
            self.assertEqual(status, 400)
            self.assertIn("Only synthetic identifiers", err_res.get("error", ""))
        finally:
            server.shutdown()
            server.server_close()

    def test_cryptographic_anti_tamper_backup_verification(self):
        conn = sqlite3.connect(str(self.db_path))
        backup_file = Path(self.temp_dir.name) / "test_anti_tamper.sqlite3"
        
        # 1. Create backup with both .sha256 and .hmac
        res = backup_database(conn, str(backup_file))
        conn.close()

        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(backup_file.exists())
        self.assertTrue(backup_file.with_suffix(".sqlite3.sha256").exists())
        self.assertTrue(backup_file.with_suffix(".sqlite3.hmac").exists())

        # 2. Safe restore from valid backup succeeds
        target_db = Path(self.temp_dir.name) / "restored.sqlite3"
        rest_res = restore_database_safely(str(target_db), str(backup_file), require_hmac=True)
        self.assertEqual(rest_res["status"], "SUCCESS")

        # 3. Tampering drill: Modify bytes in backup without updating HMAC
        with open(backup_file, "r+b") as f:
            f.seek(100)
            f.write(b"\x00\x00\x00\x00")
        
        # Recomputing SHA-256 alone (as a malicious actor would) must NOT fool HMAC anti-tamper!
        import hashlib
        new_sha = hashlib.sha256(backup_file.read_bytes()).hexdigest()
        backup_file.with_suffix(".sqlite3.sha256").write_text(f"{new_sha}  {backup_file.name}\n", encoding="utf-8")

        # Restore must fail with PermissionError due to HMAC signature mismatch!
        with self.assertRaises(PermissionError) as ctx:
            restore_database_safely(str(target_db), str(backup_file), require_hmac=True)
        self.assertIn("anti-tamper verification failed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
