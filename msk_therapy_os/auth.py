"""Authentication, Session Management, and Role-Based Authorization for MSK-Therapy-OS.

Provides lightweight, local-first offline authentication, cryptographic PBKDF2-HMAC-SHA256
password hashing, CSRF protection, session expiry, and verified clinical reviewer registry.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

SESSION_DURATION_SECONDS = 8 * 3600  # 8 hours session lifetime
PBKDF2_ITERATIONS = 100_000

VALID_ROLES = ("student", "reviewer", "admin")
VALID_CREDENTIALS = ("MD", "DO", "LAC", "PT", "DPT", "DC", "PHD", "MBBS", "FACP", "ND")
VALID_VERIFICATION_STATUSES = ("PENDING_REVIEW", "VERIFIED_ACTIVE", "REVOKED", "EXPIRED")


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Hash password using standard PBKDF2-HMAC-SHA256 with cryptographically secure salt."""
    if salt is None:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored PBKDF2 hash using constant-time comparison."""
    try:
        header, salt_hex, hash_hex = hashed.split("$")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return hmac.compare_digest(computed, expected)
    except Exception:
        return False


def init_auth_tables(db: sqlite3.Connection) -> None:
    """Create users, clinical_reviewers, and auth_sessions tables."""
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('student', 'reviewer', 'admin')),
            display_name TEXT NOT NULL,
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS clinical_reviewers (
            reviewer_id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL REFERENCES users(user_id),
            display_name TEXT NOT NULL,
            primary_credential TEXT NOT NULL CHECK (primary_credential IN ('MD', 'DO', 'LAC', 'PT', 'DPT', 'DC', 'PHD', 'MBBS', 'FACP', 'ND')),
            license_number TEXT NOT NULL,
            licensing_jurisdiction TEXT NOT NULL,
            evidence_file_or_url TEXT,
            verification_status TEXT NOT NULL DEFAULT 'PENDING_REVIEW' CHECK (verification_status IN ('PENDING_REVIEW', 'VERIFIED_ACTIVE', 'REVOKED', 'EXPIRED')),
            verified_by_admin TEXT REFERENCES users(user_id),
            verified_utc TEXT,
            notes TEXT,
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS auth_sessions (
            session_token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(user_id),
            csrf_token TEXT NOT NULL,
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            expires_epoch REAL NOT NULL,
            last_seen_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );
        """
    )
    db.commit()


DEFAULT_USER_HASHES: Dict[str, str] = {
    "admin123": "pbkdf2:sha256:100000$128abaf242cfb27cd23e56553c7dfd7f$5ecbff790edbc4418dd75833443d4b8604d3cd191ae5c32ea5a7963828296a30",
    "reviewer123": "pbkdf2:sha256:100000$37eb8b1d35ff10a43acc0172788fc557$0de69d7cf415f5eaeecae2fce74e2240bfbd5034365c9d529bccda84b5770f72",
    "pending123": "pbkdf2:sha256:100000$fc87f6e9c1371d1bcfe48484660eab1a$6aebb1100447b274624c5108949bedce04fb7ff28932dc165f43f770d9eba9f1",
    "faculty123": "pbkdf2:sha256:100000$f5f61e9c8b91a49bfc2ec7bd14d9698d$8401c383211d682ce3d98e4dafbec50c38a6e394b7ae6a9552eec5db973abc9a",
    "student123": "pbkdf2:sha256:100000$287dbb1502a1dbb75bd61f85540c08c2$dce28b03055c98a755e0241564deae6f9d1290b9dc19be1e17746548a8dffe5e",
}


def seed_default_users(db: sqlite3.Connection) -> None:
    """Seed default local users: admin, verified reviewer, unverified reviewer, student."""
    init_auth_tables(db)

    # 1. Administrator
    admin_hash = DEFAULT_USER_HASHES.get("admin123") or hash_password("admin123")
    db.execute(
        """INSERT OR IGNORE INTO users (user_id, username, password_hash, role, display_name)
           VALUES ('USR-ADMIN-01', 'admin', ?, 'admin', 'System Administrator')""",
        (admin_hash,)
    )

    # 2. Verified Clinical Supervisor (Dr. Sarah Chen, MD)
    reviewer_hash = DEFAULT_USER_HASHES.get("reviewer123") or hash_password("reviewer123")
    db.execute(
        """INSERT OR IGNORE INTO users (user_id, username, password_hash, role, display_name)
           VALUES ('USR-REV-CHEN-01', 'dr_chen', ?, 'reviewer', 'Dr. Sarah Chen, MD')""",
        (reviewer_hash,)
    )
    db.execute(
        """INSERT OR IGNORE INTO clinical_reviewers (
               reviewer_id, user_id, display_name, primary_credential, license_number,
               licensing_jurisdiction, evidence_file_or_url, verification_status,
               verified_by_admin, verified_utc, notes
           ) VALUES (
               'REV-CHEN-01', 'USR-REV-CHEN-01', 'Dr. Sarah Chen, MD', 'MD', 'CA-MED-94021',
               'Medical Board of California', 'https://mbc.ca.gov/verify/94021', 'VERIFIED_ACTIVE',
               'USR-ADMIN-01', strftime('%Y-%m-%dT%H:%M:%SZ','now'), 'Board-certified Physical Medicine & Rehabilitation'
           )"""
    )

    # 3. Unverified / Pending Reviewer (Dr. Pending, PT)
    pending_hash = DEFAULT_USER_HASHES.get("pending123") or hash_password("pending123")
    db.execute(
        """INSERT OR IGNORE INTO users (user_id, username, password_hash, role, display_name)
           VALUES ('USR-REV-PEND-02', 'dr_pending', ?, 'reviewer', 'Dr. Alex Reed, PT')""",
        (pending_hash,)
    )
    db.execute(
        """INSERT OR IGNORE INTO clinical_reviewers (
               reviewer_id, user_id, display_name, primary_credential, license_number,
               licensing_jurisdiction, evidence_file_or_url, verification_status, notes
           ) VALUES (
               'REV-PEND-02', 'USR-REV-PEND-02', 'Dr. Alex Reed, PT', 'PT', 'PT-APP-2026-99',
               'Physical Therapy Board of California', 'evidence/pt_diploma_reed.pdf', 'PENDING_REVIEW',
               'Credential verification documentation submitted; awaiting administrator sign-off.'
           )"""
    )

    # 4. Additional Verified Clinical Faculty / Reviewers
    faculty_reviewers = [
        ("USR-FAC-01", "li_wei", "Li Wei, LAc", "LAC", "REV-WEI-01", "CA-ACU-5521", "California Acupuncture Board"),
        ("USR-FAC-02", "robert_vance", "Robert Vance, PT, DPT", "DPT", "REV-VANCE-01", "CA-PT-8812", "Physical Therapy Board of California"),
        ("USR-FAC-03", "david_miller", "David Miller, DC", "DC", "REV-MILLER-01", "CA-DC-3419", "California Board of Chiropractic"),
        ("USR-FAC-04", "elena_rostova", "Prof. Elena Rostova, PhD", "PHD", "REV-ROSTOVA-01", "FAC-PHD-901", "Stanford University Anatomy Dept"),
        ("USR-FAC-05", "marcus_brown", "Dr. Marcus Brown, DO", "DO", "REV-BROWN-01", "CA-OST-1123", "Osteopathic Medical Board of California"),
        ("USR-FAC-06", "priya_patel", "Dr. Priya Patel, MBBS, FACP", "MBBS", "REV-PATEL-01", "CA-MED-7714", "Medical Board of California"),
        ("USR-FAC-07", "hanna_kim", "Hanna Kim, ND", "ND", "REV-KIM-01", "CA-ND-4402", "California Naturopathic Medicine Committee"),
        ("USR-FAC-08", "alice_smith", "Dr. Alice Smith, MD", "MD", "REV-SMITH-01", "CA-MED-3312", "Medical Board of California"),
        ("USR-FAC-09", "alice_smith_lac", "Dr. Alice Smith, MD / LAc", "MD", "REV-SMITH-02", "CA-MED-3312", "Medical Board of California"),
        ("USR-FAC-10", "clinical_mentor", "Dr. Clinical Mentor", "MD", "REV-MENTOR-01", "CA-MED-1234", "Medical Board of California"),
        ("USR-FAC-11", "clinical_instructor", "Clinical Instructor", "PT", "REV-INST-01", "CA-PT-9988", "Physical Therapy Board of California"),
        ("USR-FAC-12", "dr_taylor", "Dr. Taylor (PT Reviewer)", "PT", "REV-TAYLOR-01", "CA-PT-7766", "Physical Therapy Board of California"),
    ]
    faculty_hash = DEFAULT_USER_HASHES.get("faculty123") or hash_password("faculty123")
    for uid, uname, dname, cred, revid, lic, juris in faculty_reviewers:
        db.execute(
            """INSERT OR IGNORE INTO users (user_id, username, password_hash, role, display_name)
               VALUES (?, ?, ?, 'reviewer', ?)""",
            (uid, uname, faculty_hash, dname)
        )
        db.execute(
            """INSERT OR IGNORE INTO clinical_reviewers (
                   reviewer_id, user_id, display_name, primary_credential, license_number,
                   licensing_jurisdiction, verification_status, verified_by_admin, verified_utc, notes
               ) VALUES (?, ?, ?, ?, ?, ?, 'VERIFIED_ACTIVE', 'USR-ADMIN-01', strftime('%Y-%m-%dT%H:%M:%SZ','now'), 'Faculty Practitioner')""",
            (revid, uid, dname, cred, lic, juris)
        )

    # 5. Student Practitioner
    student_hash = DEFAULT_USER_HASHES.get("student123") or hash_password("student123")
    db.execute(
        """INSERT OR IGNORE INTO users (user_id, username, password_hash, role, display_name)
           VALUES ('USR-STUDENT-01', 'student', ?, 'student', 'Clinical Student Practitioner')""",
        (student_hash,)
    )
    db.commit()


# -----------------------------------------------------------------------------
# Authentication & Session Handlers
# -----------------------------------------------------------------------------

def authenticate_user(db: sqlite3.Connection, username: str, password: str) -> Optional[Dict[str, Any]]:
    """Validate username and password, returning user dictionary if valid."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT user_id, username, password_hash, role, display_name, is_active FROM users WHERE username = ?",
        (username.strip().lower(),)
    )
    row = cursor.fetchone()
    if not row:
        return None
    user_id, uname, p_hash, role, disp_name, is_active = row
    if not is_active:
        return None
    if not verify_password(password, p_hash):
        return None

    # Check if user has an associated clinical reviewer profile
    cursor.execute(
        """SELECT reviewer_id, primary_credential, license_number, licensing_jurisdiction,
                  verification_status, verified_utc
           FROM clinical_reviewers WHERE user_id = ?""",
        (user_id,)
    )
    rev_row = cursor.fetchone()
    reviewer_profile = None
    if rev_row:
        reviewer_profile = {
            "reviewer_id": rev_row[0],
            "primary_credential": rev_row[1],
            "license_number": rev_row[2],
            "licensing_jurisdiction": rev_row[3],
            "verification_status": rev_row[4],
            "verified_utc": rev_row[5],
        }

    return {
        "user_id": user_id,
        "username": uname,
        "role": role,
        "display_name": disp_name,
        "reviewer_profile": reviewer_profile,
    }


def create_session(db: sqlite3.Connection, user_id: str, duration_seconds: int = SESSION_DURATION_SECONDS) -> Dict[str, Any]:
    """Create new session and CSRF tokens with expiration timestamp."""
    session_token = secrets.token_hex(32)
    csrf_token = secrets.token_hex(32)
    expires_epoch = time.time() + duration_seconds

    db.execute(
        """INSERT INTO auth_sessions (session_token, user_id, csrf_token, expires_epoch)
           VALUES (?, ?, ?, ?)""",
        (session_token, user_id, csrf_token, expires_epoch)
    )
    db.commit()

    return {
        "session_token": session_token,
        "csrf_token": csrf_token,
        "expires_epoch": expires_epoch,
        "expires_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(expires_epoch)),
    }


def get_user_from_session(db: sqlite3.Connection, session_token: str) -> Optional[Dict[str, Any]]:
    """Retrieve active user for a valid, non-expired session."""
    if not session_token:
        return None

    cursor = db.cursor()
    cursor.execute(
        """
        SELECT s.session_token, s.csrf_token, s.expires_epoch,
               u.user_id, u.username, u.role, u.display_name, u.is_active
        FROM auth_sessions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.session_token = ?
        """,
        (session_token,)
    )
    row = cursor.fetchone()
    if not row:
        return None

    sess_tok, csrf_tok, exp_epoch, u_id, uname, role, disp_name, is_active = row

    # Check expiration
    if time.time() > exp_epoch or not is_active:
        # Invalidate expired session
        db.execute("DELETE FROM auth_sessions WHERE session_token = ?", (session_token,))
        db.commit()
        return None

    # Update last_seen
    db.execute(
        "UPDATE auth_sessions SET last_seen_utc = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE session_token = ?",
        (session_token,)
    )
    db.commit()

    # Fetch reviewer profile if present
    cursor.execute(
        """SELECT reviewer_id, primary_credential, license_number, licensing_jurisdiction,
                  verification_status, verified_utc
           FROM clinical_reviewers WHERE user_id = ?""",
        (u_id,)
    )
    rev_row = cursor.fetchone()
    reviewer_profile = None
    if rev_row:
        reviewer_profile = {
            "reviewer_id": rev_row[0],
            "primary_credential": rev_row[1],
            "license_number": rev_row[2],
            "licensing_jurisdiction": rev_row[3],
            "verification_status": rev_row[4],
            "verified_utc": rev_row[5],
        }

    return {
        "user_id": u_id,
        "username": uname,
        "role": role,
        "display_name": disp_name,
        "session_token": sess_tok,
        "csrf_token": csrf_tok,
        "reviewer_profile": reviewer_profile,
    }


def invalidate_session(db: sqlite3.Connection, session_token: str) -> bool:
    """Log out / delete an active session."""
    cur = db.execute("DELETE FROM auth_sessions WHERE session_token = ?", (session_token,))
    db.commit()
    return cur.rowcount > 0


def clean_expired_sessions(db: sqlite3.Connection) -> int:
    """Prune expired sessions from database."""
    cur = db.execute("DELETE FROM auth_sessions WHERE expires_epoch < ?", (time.time(),))
    db.commit()
    return cur.rowcount


# -----------------------------------------------------------------------------
# Clinical Reviewer Verification Registry
# -----------------------------------------------------------------------------

def get_verified_reviewer(db: sqlite3.Connection, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve verified reviewer profile if active and approved by an administrator."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT reviewer_id, user_id, display_name, primary_credential, license_number,
               licensing_jurisdiction, evidence_file_or_url, verification_status,
               verified_by_admin, verified_utc
        FROM clinical_reviewers
        WHERE user_id = ? AND verification_status = 'VERIFIED_ACTIVE'
        """,
        (user_id,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "reviewer_id": row[0],
        "user_id": row[1],
        "display_name": row[2],
        "primary_credential": row[3],
        "license_number": row[4],
        "licensing_jurisdiction": row[5],
        "evidence_file_or_url": row[6],
        "verification_status": row[7],
        "verified_by_admin": row[8],
        "verified_utc": row[9],
    }


def list_clinical_reviewers(db: sqlite3.Connection) -> List[Dict[str, Any]]:
    """List all registered clinical reviewers with verification status."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT cr.reviewer_id, cr.user_id, cr.display_name, cr.primary_credential,
               cr.license_number, cr.licensing_jurisdiction, cr.verification_status,
               cr.verified_utc, u.username
        FROM clinical_reviewers cr
        JOIN users u ON cr.user_id = u.user_id
        ORDER BY cr.display_name ASC
        """
    )
    return [
        {
            "reviewer_id": r[0],
            "user_id": r[1],
            "display_name": r[2],
            "primary_credential": r[3],
            "license_number": r[4],
            "licensing_jurisdiction": r[5],
            "verification_status": r[6],
            "verified_utc": r[7],
            "username": r[8],
        }
        for r in cursor.fetchall()
    ]


def verify_reviewer(
    db: sqlite3.Connection,
    reviewer_id: str,
    admin_user_id: str,
    status: str = "VERIFIED_ACTIVE",
    notes: str = ""
) -> Dict[str, Any]:
    """Administrator verification of clinical credentials."""
    if status not in VALID_VERIFICATION_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Allowed: {VALID_VERIFICATION_STATUSES}")

    # Verify admin user has admin role
    cursor = db.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (admin_user_id,))
    admin_row = cursor.fetchone()
    if not admin_row or admin_row[0] != "admin":
        raise PermissionError("Only system administrators can verify reviewer credentials.")

    now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    db.execute(
        """
        UPDATE clinical_reviewers
        SET verification_status = ?, verified_by_admin = ?, verified_utc = ?, notes = ?
        WHERE reviewer_id = ?
        """,
        (status, admin_user_id, now_utc if status == "VERIFIED_ACTIVE" else None, notes, reviewer_id)
    )
    db.commit()

    cursor.execute(
        "SELECT reviewer_id, display_name, verification_status, verified_utc FROM clinical_reviewers WHERE reviewer_id = ?",
        (reviewer_id,)
    )
    r = cursor.fetchone()
    if not r:
        raise ValueError(f"Reviewer '{reviewer_id}' not found.")
    return {
        "reviewer_id": r[0],
        "display_name": r[1],
        "verification_status": r[2],
        "verified_utc": r[3],
    }
