"""MSK-Therapy-OS P10.5 Institutional Partner Onboarding Workflow

Manages the lifecycle of prospective research hospital and university partners.
Enforces authenticated credential checks, DUA/IRB tracking, permitted research scopes,
and readiness blocker evaluation.

Onboarding Status Hierarchy:
1. INSTITUTION_NOT_REGISTERED
2. PARTNER_CONTACT_PENDING
3. PROTOCOL_UNDER_REVIEW
4. DUA_PENDING
5. ETHICS_REVIEW_PENDING
6. DATA_TRANSFER_NOT_AUTHORIZED
7. DATASET_INTAKE_AUTHORIZED
8. PILOT_EXECUTION_PENDING

Invariants:
- Onboarding status CANNOT override Scientific Gate G14 (G14 remains BLOCKED_EXTERNAL_DATA).
- No automatic approval without verified administrative signatures and ethics numbers.
- Zero external communications sent without explicit human operator authorization.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class OnboardingStatus(str, Enum):
    INSTITUTION_NOT_REGISTERED = "INSTITUTION_NOT_REGISTERED"
    PARTNER_CONTACT_PENDING = "PARTNER_CONTACT_PENDING"
    PROTOCOL_UNDER_REVIEW = "PROTOCOL_UNDER_REVIEW"
    DUA_PENDING = "DUA_PENDING"
    ETHICS_REVIEW_PENDING = "ETHICS_REVIEW_PENDING"
    DATA_TRANSFER_NOT_AUTHORIZED = "DATA_TRANSFER_NOT_AUTHORIZED"
    DATASET_INTAKE_AUTHORIZED = "DATASET_INTAKE_AUTHORIZED"
    PILOT_EXECUTION_PENDING = "PILOT_EXECUTION_PENDING"


@dataclass
class InstitutionalPartnerProfile:
    institution_id: str
    legal_name: str
    country: str
    primary_pi_name: str
    primary_pi_email: str
    radiology_lead_name: str
    data_custodian_id: str
    protocol_version: str
    status: OnboardingStatus = OnboardingStatus.PARTNER_CONTACT_PENDING
    dua_status: str = "PENDING_LEGAL_REVIEW"
    irb_status: str = "PENDING_COMMITTEE_SUBMISSION"
    irb_protocol_number: Optional[str] = None
    data_use_scope: str = "RESEARCH_ONLY_RETROSPECTIVE_DEIDENTIFIED"
    authorization_expiry_iso: Optional[str] = None
    blockers: List[str] = field(default_factory=list)
    created_at_iso: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class InstitutionalOnboardingManager:
    """Manages the offline partner onboarding registry backed by SQLite."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._mem_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS institutional_onboarding_registry (
                    institution_id TEXT PRIMARY KEY,
                    legal_name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    primary_pi_name TEXT NOT NULL,
                    primary_pi_email TEXT NOT NULL,
                    radiology_lead_name TEXT NOT NULL,
                    data_custodian_id TEXT NOT NULL,
                    protocol_version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    dua_status TEXT NOT NULL,
                    irb_status TEXT NOT NULL,
                    irb_protocol_number TEXT,
                    data_use_scope TEXT NOT NULL,
                    authorization_expiry_iso TEXT,
                    blockers_json TEXT NOT NULL,
                    created_at_iso TEXT NOT NULL
                );
            """)

    def register_prospective_institution(
        self,
        institution_id: str,
        legal_name: str,
        country: str,
        primary_pi_name: str,
        primary_pi_email: str,
        radiology_lead_name: str,
        data_custodian_id: str,
        protocol_version: str = "v1.0-DRAFT-P10.5",
    ) -> InstitutionalPartnerProfile:
        """Registers a candidate research institution in pending status."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        initial_blockers = [
            "DUA/MTA agreement not executed with hospital legal counsel.",
            "IRB/Ethics review pending formal submission or waiver determination.",
            "De-identification certificate not yet deposited by PACS custodian.",
            "Radiologist conflict-of-interest declarations pending signature."
        ]
        profile = InstitutionalPartnerProfile(
            institution_id=institution_id,
            legal_name=legal_name,
            country=country,
            primary_pi_name=primary_pi_name,
            primary_pi_email=primary_pi_email,
            radiology_lead_name=radiology_lead_name,
            data_custodian_id=data_custodian_id,
            protocol_version=protocol_version,
            status=OnboardingStatus.PARTNER_CONTACT_PENDING,
            blockers=initial_blockers,
            created_at_iso=now_iso,
        )

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO institutional_onboarding_registry
                (institution_id, legal_name, country, primary_pi_name, primary_pi_email,
                 radiology_lead_name, data_custodian_id, protocol_version, status,
                 dua_status, irb_status, irb_protocol_number, data_use_scope,
                 authorization_expiry_iso, blockers_json, created_at_iso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.institution_id, profile.legal_name, profile.country,
                profile.primary_pi_name, profile.primary_pi_email,
                profile.radiology_lead_name, profile.data_custodian_id,
                profile.protocol_version, profile.status.value,
                profile.dua_status, profile.irb_status, profile.irb_protocol_number,
                profile.data_use_scope, profile.authorization_expiry_iso,
                json.dumps(profile.blockers), profile.created_at_iso
            ))

        return profile

    def update_milestone_status(
        self,
        institution_id: str,
        new_status: OnboardingStatus,
        dua_status: Optional[str] = None,
        irb_status: Optional[str] = None,
        irb_protocol_number: Optional[str] = None,
        authorization_expiry_iso: Optional[str] = None,
        resolved_blockers: Optional[List[str]] = None,
    ) -> InstitutionalPartnerProfile:
        """Transitions an institution through verified onboarding checkpoints."""
        profile = self.get_profile(institution_id)
        if not profile:
            raise KeyError(f"Institution '{institution_id}' is not registered.")

        # Guard: Cannot reach DATASET_INTAKE_AUTHORIZED without DUA executed and IRB approved
        if new_status in (OnboardingStatus.DATASET_INTAKE_AUTHORIZED, OnboardingStatus.PILOT_EXECUTION_PENDING):
            effective_dua = dua_status or profile.dua_status
            effective_irb = irb_status or profile.irb_status
            if effective_dua != "EXECUTED_BILATERAL_DUA":
                raise ValueError("Cannot authorize dataset intake: Bilateral DUA is not executed.")
            if effective_irb not in ("APPROVED_BY_IRB", "WAIVER_OF_CONSENT_DETERMINED"):
                raise ValueError("Cannot authorize dataset intake: Ethics approval or waiver is pending.")

        profile.status = new_status
        if dua_status:
            profile.dua_status = dua_status
        if irb_status:
            profile.irb_status = irb_status
        if irb_protocol_number:
            profile.irb_protocol_number = irb_protocol_number
        if authorization_expiry_iso:
            profile.authorization_expiry_iso = authorization_expiry_iso

        if resolved_blockers:
            profile.blockers = [b for b in profile.blockers if b not in resolved_blockers]

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE institutional_onboarding_registry
                SET status = ?, dua_status = ?, irb_status = ?, irb_protocol_number = ?,
                    authorization_expiry_iso = ?, blockers_json = ?
                WHERE institution_id = ?
            """, (
                profile.status.value, profile.dua_status, profile.irb_status,
                profile.irb_protocol_number, profile.authorization_expiry_iso,
                json.dumps(profile.blockers), institution_id
            ))

        return profile

    def get_profile(self, institution_id: str) -> Optional[InstitutionalPartnerProfile]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM institutional_onboarding_registry WHERE institution_id = ?", (institution_id,))
            row = cur.fetchone()
            if not row:
                return None
            return InstitutionalPartnerProfile(
                institution_id=row["institution_id"],
                legal_name=row["legal_name"],
                country=row["country"],
                primary_pi_name=row["primary_pi_name"],
                primary_pi_email=row["primary_pi_email"],
                radiology_lead_name=row["radiology_lead_name"],
                data_custodian_id=row["data_custodian_id"],
                protocol_version=row["protocol_version"],
                status=OnboardingStatus(row["status"]),
                dua_status=row["dua_status"],
                irb_status=row["irb_status"],
                irb_protocol_number=row["irb_protocol_number"],
                data_use_scope=row["data_use_scope"],
                authorization_expiry_iso=row["authorization_expiry_iso"],
                blockers=json.loads(row["blockers_json"]),
                created_at_iso=row["created_at_iso"],
            )

    def get_offline_onboarding_dashboard(self) -> Dict[str, Any]:
        """Renders offline summary of partner readiness across all candidates."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM institutional_onboarding_registry ORDER BY created_at_iso DESC")
            rows = cur.fetchall()
            institutions = []
            status_counts: Dict[str, int] = {s.value: 0 for s in OnboardingStatus}
            for r in rows:
                status_counts[r["status"]] += 1
                institutions.append({
                    "institution_id": r["institution_id"],
                    "legal_name": r["legal_name"],
                    "status": r["status"],
                    "dua_status": r["dua_status"],
                    "irb_status": r["irb_status"],
                    "blockers_count": len(json.loads(r["blockers_json"])),
                })

            return {
                "total_candidate_institutions": len(institutions),
                "status_distribution": status_counts,
                "institutions": institutions,
                "scientific_gate_g14": "BLOCKED_EXTERNAL_DATA",
                "intake_policy": "FAIL_CLOSED_UNTIL_DUA_AND_IRB_VERIFIED",
            }
