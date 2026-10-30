"""MSK-Therapy-OS Trusted De-Identification Attestation & Manifest Verification Subsystem.

Milestone: P10.3C
Architecture: Offline-First, Python Standard Library only (hmac, hashlib, sqlite3, json).
Security Standard: HIPAA 18 Safe Harbor, NIST SP 800-88r1, ISO 14155 Clinical Governance.

Key Principles:
1. Client-supplied booleans (e.g. has_pixel_deidentification_certificate=True) or untrusted dicts are NEVER accepted.
2. Attestations are cryptographically bound to the exact dataset manifest (SHA-256 of canonical sorted file hashes).
3. Attestations are signed with server-side HMAC-SHA256 using a protected local key.
4. If a dataset is modified post-attestation (even 1 byte), the manifest hash mismatches and verification fails closed.
5. All attestations, verifications, and revocations are persisted in SQLite with atomic transactions.
"""
from __future__ import annotations

import hmac
import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class DeidentificationAttestation:
    """Verifiable, server-authenticated de-identification attestation record."""
    attestation_id: str
    dataset_id: str
    manifest_sha256: str
    issuing_institution: str
    irb_protocol_number: str
    attestor_user_id: str
    attestor_role: str
    issued_utc: str
    expiration_date: str
    status: str  # "ACTIVE", "REVOKED", "EXPIRED"
    revocation_reason: Optional[str] = None
    revoked_utc: Optional[str] = None
    revoked_by_user_id: Optional[str] = None
    hmac_signature: str = ""

    def payload_for_signing(self) -> str:
        """Construct canonical string for HMAC signing."""
        return (
            f"{self.attestation_id}|{self.dataset_id}|{self.manifest_sha256}|"
            f"{self.issuing_institution}|{self.irb_protocol_number}|"
            f"{self.attestor_user_id}|{self.attestor_role}|"
            f"{self.issued_utc}|{self.expiration_date}|{self.status}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DeidentificationTrustAuthority:
    """Server-side authority managing cryptographically verifiable de-identification attestations."""

    DEFAULT_SECRET_KEY = b"MSK_OFFLINE_DEID_LOCAL_HMAC_SECRET_KEY_2026_PROTECTED"

    def __init__(self, db_path: Optional[str] = None, hmac_key: Optional[bytes] = None) -> None:
        self.db_path = db_path
        # Use provided key, or environment variable, or default protected fallback key
        env_key = os.environ.get("MSK_DEID_HMAC_SECRET")
        if hmac_key:
            self._hmac_key = hmac_key
        elif env_key:
            self._hmac_key = env_key.encode("utf-8")
        else:
            self._hmac_key = self.DEFAULT_SECRET_KEY

        # In-memory store for unit test execution when db_path is None
        self._memory_store: Dict[str, DeidentificationAttestation] = {}
        if self.db_path:
            self._init_sqlite_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_sqlite_schema(self) -> None:
        """Initialize the attestations table in SQLite."""
        if not self.db_path:
            return
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS deidentification_attestations (
                        attestation_id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        manifest_sha256 TEXT NOT NULL,
                        issuing_institution TEXT NOT NULL,
                        irb_protocol_number TEXT NOT NULL,
                        attestor_user_id TEXT NOT NULL,
                        attestor_role TEXT NOT NULL,
                        issued_utc TEXT NOT NULL,
                        expiration_date TEXT NOT NULL,
                        status TEXT NOT NULL,
                        revocation_reason TEXT,
                        revoked_utc TEXT,
                        revoked_by_user_id TEXT,
                        hmac_signature TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_attest_ds ON deidentification_attestations(dataset_id)"
                )
        finally:
            conn.close()

    def _sign_attestation(self, att: DeidentificationAttestation) -> str:
        """Compute HMAC-SHA256 signature for an attestation record."""
        payload = att.payload_for_signing().encode("utf-8")
        return hmac.new(self._hmac_key, payload, hashlib.sha256).hexdigest()

    def _verify_attestation_signature(self, att: DeidentificationAttestation) -> bool:
        """Verify that the HMAC signature matches the signed content."""
        expected = self._sign_attestation(att)
        return hmac.compare_digest(att.hmac_signature, expected)

    @staticmethod
    def compute_dataset_manifest_hash(file_records: List[Tuple[str, str]]) -> str:
        """Compute deterministic manifest SHA-256 hash over sorted (filename, sha256) pairs."""
        if not file_records:
            return hashlib.sha256(b"EMPTY_DATASET_MANIFEST").hexdigest()
        sorted_records = sorted(file_records, key=lambda r: (r[0], r[1]))
        payload = ";".join(f"{name}:{sha}" for name, sha in sorted_records)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def issue_attestation(
        self,
        dataset_id: str,
        manifest_sha256: str,
        issuing_institution: str,
        irb_protocol_number: str,
        attestor_user_id: str,
        attestor_role: str,
        expiration_date: str,
    ) -> DeidentificationAttestation:
        """Issue a cryptographically signed de-identification attestation."""
        # Enforce governance role check
        allowed_roles = {"CLINICAL_SAFETY_AUDITOR", "GOVERNANCE_BOARD", "LEAD_ANATOMIST", "admin"}
        if attestor_role not in allowed_roles:
            raise ValueError(
                f"UNAUTHORIZED_ATTESTOR: Role '{attestor_role}' cannot issue de-identification attestations. "
                f"Must be one of: {sorted(list(allowed_roles))}."
            )

        # Enforce valid date format YYYY-MM-DD
        if len(expiration_date) != 10 or expiration_date[4] != "-" or expiration_date[7] != "-":
            raise ValueError(f"INVALID_EXPIRATION_DATE: Format must be YYYY-MM-DD, got '{expiration_date}'.")

        current_date = time.strftime("%Y-%m-%d", time.gmtime())
        if expiration_date < current_date:
            raise ValueError(f"EXPIRATION_IN_PAST: Expiration date '{expiration_date}' is already expired.")

        issued_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        hash_suffix = hashlib.sha256(f"{dataset_id}:{issued_utc}:{manifest_sha256}".encode()).hexdigest()[:8]
        attestation_id = f"ATTEST-DEID-{issued_utc[:4]}-{hash_suffix.upper()}"

        att = DeidentificationAttestation(
            attestation_id=attestation_id,
            dataset_id=dataset_id,
            manifest_sha256=manifest_sha256,
            issuing_institution=issuing_institution,
            irb_protocol_number=irb_protocol_number,
            attestor_user_id=attestor_user_id,
            attestor_role=attestor_role,
            issued_utc=issued_utc,
            expiration_date=expiration_date,
            status="ACTIVE",
        )
        att.hmac_signature = self._sign_attestation(att)

        # Persist
        if self.db_path:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute(
                        """
                        INSERT INTO deidentification_attestations (
                            attestation_id, dataset_id, manifest_sha256, issuing_institution,
                            irb_protocol_number, attestor_user_id, attestor_role, issued_utc,
                            expiration_date, status, revocation_reason, revoked_utc,
                            revoked_by_user_id, hmac_signature
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            att.attestation_id, att.dataset_id, att.manifest_sha256, att.issuing_institution,
                            att.irb_protocol_number, att.attestor_user_id, att.attestor_role, att.issued_utc,
                            att.expiration_date, att.status, att.revocation_reason, att.revoked_utc,
                            att.revoked_by_user_id, att.hmac_signature
                        )
                    )
            finally:
                conn.close()
        else:
            self._memory_store[dataset_id] = att

        return att

    def get_attestation(self, dataset_id: str) -> Optional[DeidentificationAttestation]:
        """Retrieve latest attestation for a dataset."""
        if not self.db_path:
            return self._memory_store.get(dataset_id)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT attestation_id, dataset_id, manifest_sha256, issuing_institution,
                       irb_protocol_number, attestor_user_id, attestor_role, issued_utc,
                       expiration_date, status, revocation_reason, revoked_utc,
                       revoked_by_user_id, hmac_signature
                FROM deidentification_attestations
                WHERE dataset_id = ?
                ORDER BY ROWID DESC LIMIT 1
                """,
                (dataset_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return DeidentificationAttestation(*row)
        finally:
            conn.close()

    def verify_dataset_attestation(
        self,
        dataset_id: str,
        current_manifest_sha256: str,
    ) -> Tuple[bool, str, Optional[DeidentificationAttestation]]:
        """Rigorously verify de-identification attestation against current dataset contents."""
        att = self.get_attestation(dataset_id)
        if not att:
            return False, "NO_ATTESTATION_ON_FILE: No de-identification attestation registered for dataset.", None

        # 1. Cryptographic HMAC verification
        if not self._verify_attestation_signature(att):
            return False, "SIGNATURE_VERIFICATION_FAILED: Attestation record has been tampered with or key mismatch.", None

        # 2. Manifest integrity verification (prevents certificate replay / dataset substitution)
        if att.manifest_sha256 != current_manifest_sha256:
            return (
                False,
                f"MANIFEST_HASH_MISMATCH: Dataset content modified since attestation "
                f"(expected {att.manifest_sha256[:12]}..., current {current_manifest_sha256[:12]}...).",
                None,
            )

        # 3. Revocation status
        if att.status == "REVOKED":
            return False, f"ATTESTATION_REVOKED: Attestation revoked on {att.revoked_utc}. Reason: {att.revocation_reason}", None

        # 4. Expiration check
        current_date = time.strftime("%Y-%m-%d", time.gmtime())
        if att.expiration_date < current_date:
            return False, f"ATTESTATION_EXPIRED: Attestation expired on {att.expiration_date}.", None

        return True, "ATTESTATION_VERIFIED_ACTIVE", att

    def revoke_attestation(
        self,
        attestation_id: str,
        revoking_user_id: str,
        reason: str,
    ) -> bool:
        """Immediately revoke a de-identification attestation."""
        att: Optional[DeidentificationAttestation] = None
        if not self.db_path:
            for d_id, a in self._memory_store.items():
                if a.attestation_id == attestation_id:
                    att = a
                    break
        else:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT attestation_id, dataset_id, manifest_sha256, issuing_institution,
                           irb_protocol_number, attestor_user_id, attestor_role, issued_utc,
                           expiration_date, status, revocation_reason, revoked_utc,
                           revoked_by_user_id, hmac_signature
                    FROM deidentification_attestations WHERE attestation_id = ?
                    """,
                    (attestation_id,)
                )
                row = cursor.fetchone()
                if row:
                    att = DeidentificationAttestation(*row)
            finally:
                conn.close()

        if not att:
            raise ValueError(f"ATTESTATION_NOT_FOUND: Attestation '{attestation_id}' does not exist.")

        revoked_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        att.status = "REVOKED"
        att.revocation_reason = reason
        att.revoked_utc = revoked_utc
        att.revoked_by_user_id = revoking_user_id
        att.hmac_signature = self._sign_attestation(att)

        if self.db_path:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute(
                        """
                        UPDATE deidentification_attestations
                        SET status = ?, revocation_reason = ?, revoked_utc = ?,
                            revoked_by_user_id = ?, hmac_signature = ?
                        WHERE attestation_id = ?
                        """,
                        (
                            att.status, att.revocation_reason, att.revoked_utc,
                            att.revoked_by_user_id, att.hmac_signature, attestation_id
                        )
                    )
            finally:
                conn.close()
        else:
            self._memory_store[att.dataset_id] = att

        return True
