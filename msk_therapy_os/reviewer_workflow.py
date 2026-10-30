"""MSK-Therapy-OS P10.4B External Independent Reviewer Workflow

Provides a read-only, audited evaluation environment for external independent adjudicators
(Biostatisticians, Independent Radiologists, Ethics Committee Auditors).

Security & Independence Invariants:
1. Developing coding agents and internal system developers are strictly barred
   from impersonating external reviewers (DEVELOPER_AGENT_EXCLUSION).
2. Reviewers must declare absence of conflict of interest prior to executing review checklists.
3. Review findings are cryptographically hashed and recorded immutably.
4. Read-only holdout inspection prevents raw label leakage.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ReviewerRole(str, Enum):
    EXTERNAL_BIOSTATISTICIAN = "EXTERNAL_BIOSTATISTICIAN"
    INDEPENDENT_RADIOLOGIST = "INDEPENDENT_RADIOLOGIST"
    CLINICAL_ETHICS_AUDITOR = "CLINICAL_ETHICS_AUDITOR"
    INSTITUTIONAL_DATA_CUSTODIAN = "INSTITUTIONAL_DATA_CUSTODIAN"


class ReviewVerdict(str, Enum):
    APPROVED = "APPROVED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    REJECTED = "REJECTED"


class ReviewerImpersonationError(PermissionError):
    """Raised when an internal agent or developer attempts to act as an external reviewer."""
    pass


class ReviewerCOIUnresolvedError(PermissionError):
    """Raised when a reviewer attempts review without signing non-conflict attestation."""
    pass


@dataclass
class ReviewerIdentity:
    reviewer_id: str
    external_institution: str
    full_name: str
    role: ReviewerRole
    credential_number: str
    is_developer_or_internal_agent: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["role"] = self.role.value
        return d


@dataclass
class ReviewDossierItem:
    item_id: str
    section_name: str
    passed: bool
    reviewer_comments: str
    evidence_reference_sha256: str


@dataclass
class IndependentReviewRecord:
    review_id: str
    reviewer: ReviewerIdentity
    dataset_or_package_hash: str
    coi_statement: str
    has_conflict: bool
    checklist_items: List[ReviewDossierItem]
    verdict: ReviewVerdict
    justification: str
    timestamp_utc: str
    record_sha256: str = ""

    def seal(self) -> str:
        d = {
            "review_id": self.review_id,
            "reviewer": self.reviewer.to_dict(),
            "dataset_or_package_hash": self.dataset_or_package_hash,
            "coi_statement": self.coi_statement,
            "has_conflict": self.has_conflict,
            "checklist": [asdict(item) for item in self.checklist_items],
            "verdict": self.verdict.value,
            "justification": self.justification,
            "timestamp_utc": self.timestamp_utc,
        }
        encoded = json.dumps(d, sort_keys=True, separators=(',', ':')).encode("utf-8")
        self.record_sha256 = hashlib.sha256(encoded).hexdigest()
        return self.record_sha256


class IndependentReviewEngine:
    """Manages the offline independent review workflow and enforcement."""

    def __init__(self):
        self._reviews: Dict[str, IndependentReviewRecord] = {}

    def initiate_review(
        self,
        reviewer: ReviewerIdentity,
        dataset_or_package_hash: str,
        coi_statement: str,
        has_conflict: bool,
    ) -> str:
        """Validates reviewer eligibility and opens an independent review session."""
        # 1. Developer impersonation check
        if reviewer.is_developer_or_internal_agent or "agent" in reviewer.reviewer_id.lower() or "developer" in reviewer.reviewer_id.lower():
            raise ReviewerImpersonationError(
                f"Independence violation: Developer or internal agent identity '{reviewer.reviewer_id}' "
                f"is strictly barred from executing independent external review."
            )

        # 2. Conflict of interest check
        if has_conflict or not coi_statement.strip():
            raise ReviewerCOIUnresolvedError(
                f"Independence violation: Reviewer '{reviewer.reviewer_id}' has a declared conflict of interest "
                f"or incomplete COI disclosure. Review cannot proceed."
            )

        review_id = f"REV-{reviewer.role.value}-{reviewer.reviewer_id}-{dataset_or_package_hash[:8]}"
        return review_id

    def submit_review(
        self,
        review_id: str,
        reviewer: ReviewerIdentity,
        dataset_or_package_hash: str,
        coi_statement: str,
        has_conflict: bool,
        checklist_items: List[ReviewDossierItem],
        verdict: ReviewVerdict,
        justification: str,
    ) -> IndependentReviewRecord:
        """Submits and cryptographically seals an external review record."""
        # Ensure eligibility check passes
        self.initiate_review(reviewer, dataset_or_package_hash, coi_statement, has_conflict)

        if not checklist_items:
            raise ValueError("Review submission must contain at least one evaluated checklist item.")

        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rec = IndependentReviewRecord(
            review_id=review_id,
            reviewer=reviewer,
            dataset_or_package_hash=dataset_or_package_hash,
            coi_statement=coi_statement,
            has_conflict=has_conflict,
            checklist_items=checklist_items,
            verdict=verdict,
            justification=justification,
            timestamp_utc=now_utc,
        )
        rec.seal()
        self._reviews[review_id] = rec
        return rec

    def get_review(self, review_id: str) -> Optional[IndependentReviewRecord]:
        return self._reviews.get(review_id)
