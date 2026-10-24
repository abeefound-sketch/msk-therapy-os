"""Comprehensive test suite for M2.8.2 Identity, Authentication, RBAC, and Clinical Safety Gates."""
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
from concurrent.futures import ThreadPoolExecutor

from msk_therapy_os.auth import (
    authenticate_user,
    create_session,
    get_user_from_session,
    get_verified_reviewer,
    hash_password,
    init_auth_tables,
    invalidate_session,
    list_clinical_reviewers,
    seed_default_users,
    verify_password,
    verify_reviewer,
    get_user_count,
    create_user,
    bootstrap_initial_admin,
    migrate_legacy_db_to_secure_mode,
)
from msk_therapy_os.db import init_db, open_db, seed_db
from msk_therapy_os.points import (
    init_points_tables,
    validate_governance_tier,
)
from msk_therapy_os.server import create_server
from msk_therapy_os.soap import create_soap_note, review_soap_note
from msk_therapy_os.tracking import export_case_fhir, record_session


class TestAuthAndRBACUnit(unittest.TestCase):
    """Unit tests for offline authentication, PBKDF2 hashing, sessions, and reviewer registry."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_auth.sqlite3"
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

    def test_secure_bootstrap_lifecycle(self):
        """Verify initial root admin bootstrap on clean DB and permanent lockout on subsequent attempts."""
        clean_db_path = Path(self.temp_dir.name) / "clean_bootstrap.sqlite3"
        conn = sqlite3.connect(str(clean_db_path))
        init_db(conn)
        self.assertEqual(get_user_count(conn), 0)

        # 1. Bootstrap first admin
        admin = bootstrap_initial_admin(
            conn,
            username="sysadmin",
            password="StrongAdminPassword99!",
            display_name="System Administrator"
        )
        self.assertEqual(admin["username"], "sysadmin")
        self.assertEqual(admin["role"], "admin")
        self.assertEqual(get_user_count(conn), 1)

        # 2. Subsequent bootstrap must be strictly forbidden
        with self.assertRaises(PermissionError):
            bootstrap_initial_admin(
                conn,
                username="hacker_admin",
                password="AnotherPassword123!",
                display_name="Impostor"
            )
        self.assertEqual(get_user_count(conn), 1)

        # 3. Authenticate with newly bootstrapped admin
        authed = authenticate_user(conn, "sysadmin", "StrongAdminPassword99!")
        self.assertIsNotNone(authed)
        self.assertEqual(authed["username"], "sysadmin")
        conn.close()

    def test_pbkdf2_password_hashing(self):
        """Verify PBKDF2-HMAC-SHA256 password hashing with unique salts."""
        h1 = hash_password("secret123")
        h2 = hash_password("secret123")
        self.assertNotEqual(h1, h2, "Salts must be randomly generated and unique")
        self.assertTrue(h1.startswith("pbkdf2:sha256:100000$"))
        self.assertTrue(verify_password("secret123", h1))
        self.assertTrue(verify_password("secret123", h2))
        self.assertFalse(verify_password("wrongpassword", h1))

    def test_authenticate_user_success_and_failure(self):
        """Verify user authentication against seeded credentials."""
        # Valid admin
        admin = authenticate_user(self.conn, "admin", "admin123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["username"], "admin")
        self.assertEqual(admin["role"], "admin")

        # Valid verified reviewer
        rev = authenticate_user(self.conn, "dr_chen", "reviewer123")
        self.assertIsNotNone(rev)
        self.assertEqual(rev["role"], "reviewer")
        self.assertIsNotNone(rev["reviewer_profile"])
        self.assertEqual(rev["reviewer_profile"]["verification_status"], "VERIFIED_ACTIVE")

        # Invalid password
        self.assertIsNone(authenticate_user(self.conn, "admin", "badpassword"))
        # Non-existent user
        self.assertIsNone(authenticate_user(self.conn, "nonexistent_user", "pass"))

    def test_session_lifecycle_and_expiry(self):
        """Verify session creation, retrieval, expiry, and manual revocation."""
        admin = authenticate_user(self.conn, "admin", "admin123")
        # Create session with 2 second lifetime
        sess = create_session(self.conn, admin["user_id"], duration_seconds=2)
        token = sess["session_token"]
        csrf = sess["csrf_token"]
        self.assertIsNotNone(token)
        self.assertIsNotNone(csrf)

        # Retrieve user from active session
        user = get_user_from_session(self.conn, token)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "admin")
        self.assertEqual(user["csrf_token"], csrf)

        # Invalidate session
        self.assertTrue(invalidate_session(self.conn, token))
        self.assertIsNone(get_user_from_session(self.conn, token))

        # Test expiration
        sess_short = create_session(self.conn, admin["user_id"], duration_seconds=0.1)
        short_token = sess_short["session_token"]
        time.sleep(0.15)
        self.assertIsNone(get_user_from_session(self.conn, short_token))

    def test_verified_reviewer_registry(self):
        """Verify reviewer verification workflow and administrator approval requirement."""
        # Unverified reviewer (dr_pending)
        pending = authenticate_user(self.conn, "dr_pending", "pending123")
        self.assertIsNotNone(pending)
        self.assertEqual(pending["reviewer_profile"]["verification_status"], "PENDING_REVIEW")
        self.assertIsNone(get_verified_reviewer(self.conn, pending["user_id"]))

        # Non-admin attempting to verify must fail
        with self.assertRaises(PermissionError):
            verify_reviewer(
                self.conn,
                reviewer_id="REV-PEND-02",
                admin_user_id=pending["user_id"],  # dr_pending is not admin
                status="VERIFIED_ACTIVE"
            )

        # Admin verifying reviewer must succeed
        admin = authenticate_user(self.conn, "admin", "admin123")
        res = verify_reviewer(
            self.conn,
            reviewer_id="REV-PEND-02",
            admin_user_id=admin["user_id"],
            status="VERIFIED_ACTIVE",
            notes="Documentation audited and approved"
        )
        self.assertEqual(res["verification_status"], "VERIFIED_ACTIVE")
        self.assertIsNotNone(get_verified_reviewer(self.conn, pending["user_id"]))

    def test_governance_tier_rejects_unregistered_or_unverified_reviewers(self):
        """Verify validate_governance_tier rejects credentials without registry verification."""
        # Unregistered reviewer with fake MD credential string
        with self.assertRaises(ValueError) as ctx:
            validate_governance_tier(
                "ANATOMY_REVIEWED",
                reviewer="Dr. Unregistered Fraud, MD",
                evidence_id="EVID-A-001",
                uncertainty_radius_mm=3.0,
                db=self.conn
            )
        self.assertIn("not registered in the clinical_reviewers registry", str(ctx.exception))

        # Registered reviewer whose status is PENDING_REVIEW
        with self.assertRaises(ValueError) as ctx:
            validate_governance_tier(
                "ANATOMY_REVIEWED",
                reviewer="Dr. Alex Reed, PT",
                evidence_id="EVID-A-001",
                uncertainty_radius_mm=3.0,
                db=self.conn
            )
        self.assertIn("status is 'PENDING_REVIEW'", str(ctx.exception))

        # Verified active reviewer must succeed
        validate_governance_tier(
            "ANATOMY_REVIEWED",
            reviewer="Dr. Sarah Chen, MD",
            evidence_id="EVID-A-001",
            uncertainty_radius_mm=3.0,
            db=self.conn
        )


    def test_secure_mode_rejects_legacy_demo_passwords(self):
        """Verify that SECURE MODE strictly rejects demo credentials and disallowed default passwords."""
        orig_mode = os.environ.get("MSK_MODE")
        try:
            # Under DEMO mode, admin123 works
            os.environ["MSK_MODE"] = "demo"
            demo_user = authenticate_user(self.conn, "admin", "admin123")
            self.assertIsNotNone(demo_user)

            # Under SECURE mode, all default demo passwords are hard-blocked
            os.environ["MSK_MODE"] = "secure"
            self.assertIsNone(authenticate_user(self.conn, "admin", "admin123"))
            self.assertIsNone(authenticate_user(self.conn, "dr_chen", "reviewer123"))
            self.assertIsNone(authenticate_user(self.conn, "student1", "student123"))
            self.assertIsNone(authenticate_user(self.conn, "guest_user", "guest123"))

            # Even if user enters another disallowed default password
            self.assertIsNone(authenticate_user(self.conn, "admin", "password123"))
        finally:
            if orig_mode is None:
                os.environ.pop("MSK_MODE", None)
            else:
                os.environ["MSK_MODE"] = orig_mode

    def test_bootstrap_concurrency_race_condition(self):
        """Verify concurrent attempts to bootstrap initial admin result in exactly one winner."""
        clean_db_path = Path(self.temp_dir.name) / "concurrency_bootstrap.sqlite3"
        conn = sqlite3.connect(str(clean_db_path), check_same_thread=False, timeout=15)
        init_db(conn)

        def try_bootstrap(idx):
            t_conn = sqlite3.connect(str(clean_db_path), timeout=15)
            try:
                bootstrap_initial_admin(
                    t_conn,
                    username=f"admin_{idx}",
                    password=f"StrongAdminPass{idx}!@#",
                    display_name=f"Admin {idx}"
                )
                return True
            except PermissionError:
                return False
            finally:
                t_conn.close()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(try_bootstrap, i) for i in range(8)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r is True)
        self.assertEqual(success_count, 1, "Exactly one concurrent thread must succeed bootstrapping admin")
        self.assertEqual(get_user_count(conn), 1)
        conn.close()

    def test_legacy_db_migration_to_secure(self):
        """Verify legacy DB migration locks default accounts while preserving clinical reviewer audit references."""
        # Check initial state with seeded demo users
        admin_before = authenticate_user(self.conn, "admin", "admin123")
        self.assertIsNotNone(admin_before)

        # Count reviewers before
        reviewers_before = list_clinical_reviewers(self.conn)
        self.assertGreater(len(reviewers_before), 0)

        # Run migration
        stats = migrate_legacy_db_to_secure_mode(self.conn, deactivate_demo_users=False)
        self.assertGreater(stats["migrated_count"], 0)

        # Verify admin cannot login with old password anymore
        admin_after = authenticate_user(self.conn, "admin", "admin123")
        self.assertIsNone(admin_after)

        # Inspect database row directly: password_hash must be locked
        row = self.conn.execute("SELECT password_hash FROM users WHERE username = 'admin'").fetchone()
        self.assertTrue(row[0].startswith("LOCKED_DEMO_RESET_REQUIRED_"))

        # Verify foreign keys are completely intact
        fk_errors = self.conn.execute("PRAGMA foreign_key_check").fetchall()
        self.assertEqual(len(fk_errors), 0, "No FK violations allowed after migration")

        # Reviewers must still exist and be readable
        reviewers_after = list_clinical_reviewers(self.conn)
        self.assertEqual(len(reviewers_before), len(reviewers_after))


class TestAuthAndRBACIntegration(unittest.TestCase):
    """Integration tests for HTTP endpoints with session tokens, CSRF, and RBAC enforcement."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = str(Path(cls.temp_dir.name) / "test_auth_api.sqlite3")

        with open_db(cls.db_path) as db:
            init_db(db)
            seed_db(db)
            from msk_therapy_os.db import seed_longitudinal_trajectory
            seed_longitudinal_trajectory(db)

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

    def _login(self, username, password):
        payload = json.dumps({"username": username, "password": password}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/auth/login",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["session_token"], data["csrf_token"], data["user"]

    def test_login_and_auth_me(self):
        """Verify login endpoint returns valid session token and /api/auth/me resolves identity."""
        token, csrf, user = self._login("admin", "admin123")
        self.assertEqual(user["role"], "admin")

        req_me = urllib.request.Request(
            f"{self.base_url}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req_me) as resp:
            me_data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(me_data["authenticated"])
            self.assertEqual(me_data["user"]["username"], "admin")

    def test_csrf_token_validation_on_mutating_requests(self):
        """Verify that requests with an active session require valid CSRF token."""
        token, csrf, user = self._login("admin", "admin123")

        # Mutating request with INVALID CSRF token
        bad_payload = json.dumps({
            "code": "CSRF-ATTACK-01",
            "name_en": "CSRF Attack Point",
            "position": [0.0, 1.5, 0.0],
            "csrf_token": "invalid_forged_csrf"
        }).encode("utf-8")
        req_bad = urllib.request.Request(
            f"{self.base_url}/api/points",
            data=bad_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "invalid_forged_csrf"
            }
        )
        try:
            with urllib.request.urlopen(req_bad) as resp:
                self.fail("Should reject invalid CSRF token with 403")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)
            err = json.loads(e.read().decode("utf-8"))
            self.assertIn("CSRF token", err["error"])

        # Mutating request with VALID CSRF token
        good_payload = json.dumps({
            "code": "CSRF-OK-01",
            "name_en": "Valid CSRF Point",
            "position": [0.0, 1.5, 0.0],
            "csrf_token": csrf
        }).encode("utf-8")
        req_good = urllib.request.Request(
            f"{self.base_url}/api/points",
            data=good_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf
            }
        )
        with urllib.request.urlopen(req_good) as resp:
            self.assertEqual(resp.status, 201)

    def test_rbac_backup_and_restore_access_control(self):
        """Verify backup and restore require admin role; student and unauth return 401/403."""
        # 1. Unauthenticated request -> 401
        req_unauth = urllib.request.Request(
            f"{self.base_url}/api/governance/backup",
            data=json.dumps({"name": "snap.sqlite3"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req_unauth) as resp:
                self.fail("Unauth backup should fail")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 401)

        # 2. Student role request -> 403
        s_tok, s_csrf, _ = self._login("student", "student123")
        req_student = urllib.request.Request(
            f"{self.base_url}/api/governance/backup",
            data=json.dumps({"name": "snap.sqlite3", "csrf_token": s_csrf}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {s_tok}",
                "X-CSRF-Token": s_csrf
            }
        )
        try:
            with urllib.request.urlopen(req_student) as resp:
                self.fail("Student backup should fail with 403")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)

        # 3. Admin role request -> 200
        a_tok, a_csrf, _ = self._login("admin", "admin123")
        req_admin = urllib.request.Request(
            f"{self.base_url}/api/governance/backup",
            data=json.dumps({"name": "test_rbac_snap.sqlite3", "csrf_token": a_csrf}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {a_tok}",
                "X-CSRF-Token": a_csrf
            }
        )
        with urllib.request.urlopen(req_admin) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res["status"], "SUCCESS")

    def test_clinical_safety_red_flag_downstream_session_blocked(self):
        """Verify downstream manual therapy session is blocked on visit with red flags."""
        with open_db(self.db_path) as db:
            # Create a visit with red flag STOP_AND_REFER
            cur = db.execute(
                """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
                   VALUES ('DEMO-NECK-001', '2026-10-23', 'neck', 9, 20.0, 'bowel_bladder_change', 'Emergency cauda equina concern', 'STOP_AND_REFER')"""
            )
            v_id = cur.lastrowid
            db.commit()

        # Attempt to record therapy session without referral clearance -> must be rejected
        sess_payload = json.dumps({
            "visit_id": v_id,
            "modality": "manual_massage",
            "duration_min": 30,
            "target_structures": "Trapezius"
        }).encode("utf-8")
        req_sess = urllib.request.Request(
            f"{self.base_url}/api/session",
            data=sess_payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req_sess) as resp:
                self.fail("Should reject downstream therapy session on active red flag")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            err = json.loads(e.read().decode("utf-8"))
            self.assertIn("Safety Hard Stop", err["error"])
            self.assertIn("bowel_bladder_change", err["error"])

    def test_spinal_manipulation_prohibition(self):
        """Verify high-velocity spinal manipulation is strictly prohibited across all visits."""
        with open_db(self.db_path) as db:
            cur = db.execute(
                """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
                   VALUES ('DEMO-NECK-001', '2026-10-23', 'neck', 3, 50.0, 'none', 'Routine test visit', 'DOCUMENT_ONLY')"""
            )
            clean_v_id = cur.lastrowid
            db.commit()

        bad_mod_payload = json.dumps({
            "visit_id": clean_v_id,
            "modality": "spinal_manipulation",
            "duration_min": 10
        }).encode("utf-8")
        req_bad_mod = urllib.request.Request(
            f"{self.base_url}/api/session",
            data=bad_mod_payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req_bad_mod) as resp:
                self.fail("Should reject spinal manipulation")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            err = json.loads(e.read().decode("utf-8"))
            self.assertIn("strictly prohibited", err["error"])

    def test_soap_approval_requires_verified_reviewer(self):
        """Verify SOAP approvals reject student or unverified reviewer attempts."""
        # Create student draft SOAP note
        with open_db(self.db_path) as db:
            soap_id = create_soap_note(
                db,
                visit_id=1,
                subjective="Neck tightness",
                objective="Cervical ROM 40 deg",
                assessment="Postural strain",
                plan="Rest and gentle mobility",
                author_role="student"
            )

        # 1. Student session attempting to review SOAP note -> 403 Forbidden
        s_tok, s_csrf, _ = self._login("student", "student123")
        review_payload = json.dumps({
            "soap_id": soap_id,
            "decision": "APPROVED",
            "feedback": "Student trying to self-approve",
            "csrf_token": s_csrf
        }).encode("utf-8")
        req_student_rev = urllib.request.Request(
            f"{self.base_url}/api/review-soap",
            data=review_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {s_tok}",
                "X-CSRF-Token": s_csrf
            }
        )
        try:
            with urllib.request.urlopen(req_student_rev) as resp:
                self.fail("Student cannot approve SOAP notes")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)

        # 2. Verified reviewer session -> 200 OK
        r_tok, r_csrf, _ = self._login("dr_chen", "reviewer123")
        rev_ok_payload = json.dumps({
            "soap_id": soap_id,
            "decision": "APPROVED",
            "feedback": "Approved by verified supervisor",
            "csrf_token": r_csrf
        }).encode("utf-8")
        req_ok_rev = urllib.request.Request(
            f"{self.base_url}/api/review-soap",
            data=rev_ok_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {r_tok}",
                "X-CSRF-Token": r_csrf
            }
        )
        with urllib.request.urlopen(req_ok_rev) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res["status"], "reviewed")
            self.assertEqual(res["decision"], "APPROVED")
            self.assertEqual(res["reviewer"], "Dr. Sarah Chen, MD")
