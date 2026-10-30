"""MSK-Therapy-OS P10.6 External Dependency & Evidence Governance Register

Manages the lifecycle and verification state of external scientific, legal,
and ethical dependencies required before empirical clinical data validation may proceed.

Tracked Dependencies:
1. STATISTICAL_PROTOCOL_REVIEW: Independent biostatistician sign-off on SAP.
2. RESEARCH_COLLABORATION_ACCEPTANCE: Authorized institutional partner representative.
3. DATA_USE_AGREEMENT: Executed bilateral DUA/MTA with hospital legal counsel.
4. ETHICAL_APPROVAL_OR_DETERMINATION: IRB / IEC ethics approval or formal waiver.
5. IMAGING_DATA_AUTHORIZATION: Hospital PACS / imaging data custodian sign-off.
6. INDEPENDENT_ANATOMICAL_ANNOTATIONS: Board-certified radiologist & anatomist consensus.
7. HOLDOUT_VERIFICATION: Independent QA auditor witnessing 30% holdout sealing.
8. SCIENTIFIC_CONCLUSIONS: Authorized independent external review committee.

Status Vocabulary:
- NOT_STARTED
- DRAFT_PREPARED
- SUBMITTED_EXTERNALLY
- UNDER_EXTERNAL_REVIEW
- APPROVED_VERIFIED
- REJECTED
- EXPIRED
- BLOCKED_EXTERNAL

Security Invariants:
- Coding Agent or developer self-certification is STRICTLY PROHIBITED.
- Transition to APPROVED_VERIFIED requires external verification artifact, digest, and credentialed authority.
- Scientific Gate G14 cannot transition away from BLOCKED_EXTERNAL_DATA while any core dependency is unverified.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ExternalDependencyType(str, Enum):
    STATISTICAL_PROTOCOL_REVIEW = "STATISTICAL_PROTOCOL_REVIEW"
    RESEARCH_COLLABORATION_ACCEPTANCE = "RESEARCH_COLLABORATION_ACCEPTANCE"
    DATA_USE_AGREEMENT = "DATA_USE_AGREEMENT"
    ETHICAL_APPROVAL_OR_DETERMINATION = "ETHICAL_APPROVAL_OR_DETERMINATION"
    IMAGING_DATA_AUTHORIZATION = "IMAGING_DATA_AUTHORIZATION"
    INDEPENDENT_ANATOMICAL_ANNOTATIONS = "INDEPENDENT_ANATOMICAL_ANNOTATIONS"
    HOLDOUT_VERIFICATION = "HOLDOUT_VERIFICATION"
    SCIENTIFIC_CONCLUSIONS = "SCIENTIFIC_CONCLUSIONS"


class DependencyStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    DRAFT_PREPARED = "DRAFT_PREPARED"
    SUBMITTED_EXTERNALLY = "SUBMITTED_EXTERNALLY"
    UNDER_EXTERNAL_REVIEW = "UNDER_EXTERNAL_REVIEW"
    APPROVED_VERIFIED = "APPROVED_VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL"


@dataclass
class ExternalAuthorityInfo:
    authority_name: str
    organization: str
    credential_title: str
    contact_email: Optional[str] = None
    verification_method: str = "OFFICIAL_DIGITAL_SIGNATURE"


@dataclass
class DependencyRecord:
    dependency_type: ExternalDependencyType
    institution_id: str
    cohort_scope: str
    current_status: DependencyStatus
    responsible_authority_role: str
    external_authority: Optional[ExternalAuthorityInfo] = None
    evidence_document_hash: Optional[str] = None
    approval_certificate_id: Optional[str] = None
    effective_date_iso: Optional[str] = None
    expiration_date_iso: Optional[str] = None
    blockers: List[str] = field(default_factory=list)
    last_updated_iso: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["dependency_type"] = self.dependency_type.value
        d["current_status"] = self.current_status.value
        return d


class ExternalDependencyRegistry:
    """Manages the persistent registry of external dependencies backed by SQLite."""

    INTERNAL_DEVELOPER_ROLES = {"CODING_AGENT", "DEVELOPER", "LOCAL_TESTER", "SYSTEM_SIMULATOR"}

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._mem_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS external_dependency_registry (
                    dependency_key TEXT PRIMARY KEY,
                    dependency_type TEXT NOT NULL,
                    institution_id TEXT NOT NULL,
                    cohort_scope TEXT NOT NULL,
                    current_status TEXT NOT NULL,
                    responsible_authority_role TEXT NOT NULL,
                    external_authority_json TEXT,
                    evidence_document_hash TEXT,
                    approval_certificate_id TEXT,
                    effective_date_iso TEXT,
                    expiration_date_iso TEXT,
                    blockers_json TEXT NOT NULL,
                    last_updated_iso TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dependency_audit_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dependency_key TEXT NOT NULL,
                    from_status TEXT NOT NULL,
                    to_status TEXT NOT NULL,
                    actor_role TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    timestamp_iso TEXT NOT NULL,
                    FOREIGN KEY (dependency_key) REFERENCES external_dependency_registry(dependency_key)
                );
            """)

    @staticmethod
    def make_key(dep_type: ExternalDependencyType, institution_id: str, cohort: str) -> str:
        return f"{dep_type.value}::{institution_id}::{cohort}"

    def initialize_standard_dependencies(
        self,
        institution_id: str,
        cohort_scope: str = "ALL_COHORTS_ABC",
    ) -> List[DependencyRecord]:
        """Initializes all 8 standard dependencies in DRAFT_PREPARED status."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        records = []
        dep_defaults = [
            (ExternalDependencyType.STATISTICAL_PROTOCOL_REVIEW, "Independent Biostatistician", ["SAP draft pending external statistician review."]),
            (ExternalDependencyType.RESEARCH_COLLABORATION_ACCEPTANCE, "Institutional Authorizing Official", ["Formal partnership transmittal package not yet executed."]),
            (ExternalDependencyType.DATA_USE_AGREEMENT, "Institutional Legal Counsel", ["Bilateral DUA terms pending negotiation."]),
            (ExternalDependencyType.ETHICAL_APPROVAL_OR_DETERMINATION, "Institutional Review Board (IRB / IEC)", ["Ethics application or retrospective waiver pending submission."]),
            (ExternalDependencyType.IMAGING_DATA_AUTHORIZATION, "Institutional PACS Custodian", ["Anonymized retrospective series not yet staged."]),
            (ExternalDependencyType.INDEPENDENT_ANATOMICAL_ANNOTATIONS, "Board-Certified Radiologists & Anatomists", ["Double-blind annotators pending COI screening and assignment."]),
            (ExternalDependencyType.HOLDOUT_VERIFICATION, "Independent QA Auditor", ["Holdout partition sealing awaiting dataset authorization."]),
            (ExternalDependencyType.SCIENTIFIC_CONCLUSIONS, "External Independent Review Committee", ["Empirical review pending trial completion."]),
        ]

        with self._get_conn() as conn:
            for dep_type, auth_role, initial_blockers in dep_defaults:
                key = self.make_key(dep_type, institution_id, cohort_scope)
                rec = DependencyRecord(
                    dependency_type=dep_type,
                    institution_id=institution_id,
                    cohort_scope=cohort_scope,
                    current_status=DependencyStatus.DRAFT_PREPARED,
                    responsible_authority_role=auth_role,
                    blockers=initial_blockers,
                    last_updated_iso=now_iso,
                )
                conn.execute("""
                    INSERT OR REPLACE INTO external_dependency_registry
                    (dependency_key, dependency_type, institution_id, cohort_scope,
                     current_status, responsible_authority_role, external_authority_json,
                     evidence_document_hash, approval_certificate_id, effective_date_iso,
                     expiration_date_iso, blockers_json, last_updated_iso)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key, rec.dependency_type.value, rec.institution_id, rec.cohort_scope,
                    rec.current_status.value, rec.responsible_authority_role, None,
                    None, None, None, None, json.dumps(rec.blockers), rec.last_updated_iso
                ))
                records.append(rec)
        return records

    def update_dependency_status(
        self,
        dep_type: ExternalDependencyType,
        institution_id: str,
        cohort_scope: str,
        new_status: DependencyStatus,
        actor_role: str,
        actor_id: str,
        rationale: str,
        external_authority: Optional[ExternalAuthorityInfo] = None,
        evidence_document_hash: Optional[str] = None,
        approval_certificate_id: Optional[str] = None,
        effective_date_iso: Optional[str] = None,
        expiration_date_iso: Optional[str] = None,
        resolved_blockers: Optional[List[str]] = None,
    ) -> DependencyRecord:
        """Transitions dependency status while enforcing anti-self-certification guards."""
        key = self.make_key(dep_type, institution_id, cohort_scope)
        rec = self.get_dependency(dep_type, institution_id, cohort_scope)
        if not rec:
            raise KeyError(f"Dependency '{key}' does not exist in registry.")

        # Guard 1: Anti-self-certification
        if new_status == DependencyStatus.APPROVED_VERIFIED:
            if actor_role in self.INTERNAL_DEVELOPER_ROLES:
                raise PermissionError(
                    f"Self-certification prohibited: Actor role '{actor_role}' cannot approve external scientific/legal dependencies."
                )
            if not external_authority or not external_authority.authority_name:
                raise ValueError("Cannot mark APPROVED_VERIFIED without credentialed external authority info.")
            if not evidence_document_hash or len(evidence_document_hash) < 16:
                raise ValueError("Cannot mark APPROVED_VERIFIED without valid cryptographic evidence document hash.")

        # Guard 2: Expiration verification
        if expiration_date_iso and new_status == DependencyStatus.APPROVED_VERIFIED:
            today = datetime.date.today()
            exp_date = datetime.date.fromisoformat(expiration_date_iso)
            if today > exp_date:
                raise PermissionError(f"Cannot approve dependency: Approval expired on {expiration_date_iso}.")

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        from_status = rec.current_status.value
        rec.current_status = new_status
        rec.last_updated_iso = now_iso

        if external_authority:
            rec.external_authority = external_authority
        if evidence_document_hash:
            rec.evidence_document_hash = evidence_document_hash
        if approval_certificate_id:
            rec.approval_certificate_id = approval_certificate_id
        if effective_date_iso:
            rec.effective_date_iso = effective_date_iso
        if expiration_date_iso:
            rec.expiration_date_iso = expiration_date_iso

        if resolved_blockers:
            rec.blockers = [b for b in rec.blockers if b not in resolved_blockers]

        evt_hash = hashlib.sha256(f"{key}:{from_status}:{new_status.value}:{actor_id}:{now_iso}".encode("utf-8")).hexdigest()

        with self._get_conn() as conn:
            conn.execute("""
                UPDATE external_dependency_registry
                SET current_status = ?, external_authority_json = ?, evidence_document_hash = ?,
                    approval_certificate_id = ?, effective_date_iso = ?, expiration_date_iso = ?,
                    blockers_json = ?, last_updated_iso = ?
                WHERE dependency_key = ?
            """, (
                rec.current_status.value,
                json.dumps(asdict(rec.external_authority)) if rec.external_authority else None,
                rec.evidence_document_hash, rec.approval_certificate_id,
                rec.effective_date_iso, rec.expiration_date_iso,
                json.dumps(rec.blockers), rec.last_updated_iso, key
            ))
            conn.execute("""
                INSERT INTO dependency_audit_events
                (dependency_key, from_status, to_status, actor_role, actor_id, rationale, event_hash, timestamp_iso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key, from_status, rec.current_status.value, actor_role, actor_id, rationale, evt_hash, now_iso
            ))

        return rec

    def get_dependency(
        self,
        dep_type: ExternalDependencyType,
        institution_id: str,
        cohort_scope: str,
    ) -> Optional[DependencyRecord]:
        key = self.make_key(dep_type, institution_id, cohort_scope)
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM external_dependency_registry WHERE dependency_key = ?", (key,))
            row = cur.fetchone()
            if not row:
                return None
            auth_info = None
            if row["external_authority_json"]:
                d = json.loads(row["external_authority_json"])
                auth_info = ExternalAuthorityInfo(**d)
            return DependencyRecord(
                dependency_type=ExternalDependencyType(row["dependency_type"]),
                institution_id=row["institution_id"],
                cohort_scope=row["cohort_scope"],
                current_status=DependencyStatus(row["current_status"]),
                responsible_authority_role=row["responsible_authority_role"],
                external_authority=auth_info,
                evidence_document_hash=row["evidence_document_hash"],
                approval_certificate_id=row["approval_certificate_id"],
                effective_date_iso=row["effective_date_iso"],
                expiration_date_iso=row["expiration_date_iso"],
                blockers=json.loads(row["blockers_json"]),
                last_updated_iso=row["last_updated_iso"],
            )

    def get_institutional_readiness_summary(self, institution_id: str) -> Dict[str, Any]:
        """Renders comprehensive readiness score and blocker summary for a partner institution."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT * FROM external_dependency_registry WHERE institution_id = ? ORDER BY dependency_type",
                (institution_id,)
            )
            rows = cur.fetchall()
            deps = []
            status_counts: Dict[str, int] = {s.value: 0 for s in DependencyStatus}
            all_blockers = []

            for r in rows:
                status_counts[r["current_status"]] += 1
                b_list = json.loads(r["blockers_json"])
                all_blockers.extend(b_list)
                deps.append({
                    "dependency_type": r["dependency_type"],
                    "status": r["current_status"],
                    "authority_role": r["responsible_authority_role"],
                    "blockers_count": len(b_list),
                    "has_verified_evidence": r["evidence_document_hash"] is not None,
                })

            total_deps = len(rows)
            approved_count = status_counts[DependencyStatus.APPROVED_VERIFIED.value]
            is_intake_permitted = (total_deps >= 4) and (
                status_counts[DependencyStatus.DATA_USE_AGREEMENT.value if hasattr(DependencyStatus, "DATA_USE_AGREEMENT") else "APPROVED_VERIFIED"] > 0
            )

            return {
                "institution_id": institution_id,
                "total_dependencies_tracked": total_deps,
                "status_distribution": status_counts,
                "approved_dependencies": approved_count,
                "is_fully_approved_for_pilot": (approved_count == total_deps) and (total_deps > 0),
                "outstanding_blockers_count": len(all_blockers),
                "all_outstanding_blockers": all_blockers,
                "dependencies": deps,
                "scientific_gate_g14": "BLOCKED_EXTERNAL_DATA",
            }
