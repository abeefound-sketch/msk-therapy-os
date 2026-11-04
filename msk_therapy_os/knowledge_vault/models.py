"""Data contracts and model definitions for Knowledge Vault (Milestone P20)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DocumentNamespace(str, Enum):
    ANATOMY_EVIDENCE = "ANATOMY_EVIDENCE"
    TRADITIONAL_MERIDIAN = "TRADITIONAL_MERIDIAN"
    DIEN_CHAN_REFLEX = "DIEN_CHAN_REFLEX"
    BIOMECHANICS = "BIOMECHANICS"
    CLINICAL_PROTOCOL = "CLINICAL_PROTOCOL"
    RESEARCH_NOTE = "RESEARCH_NOTE"
    HISTORICAL_TEXT = "HISTORICAL_TEXT"


class ClaimType(str, Enum):
    ANATOMICAL_LOCATION = "ANATOMICAL_LOCATION"
    MERIDIAN_PATHWAY = "MERIDIAN_PATHWAY"
    REFLEX_INDICATION = "REFLEX_INDICATION"
    CONTRAINDICATION = "CONTRAINDICATION"
    BIOMECHANICAL_MECHANISM = "BIOMECHANICAL_MECHANISM"
    HISTORICAL_ORIGIN = "HISTORICAL_ORIGIN"


class AssertionType(str, Enum):
    ASSERTION = "ASSERTION"    # Direct factual statement in source
    INFERENCE = "INFERENCE"    # Derived or synthesized conclusion


class ClaimStatus(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    SUPPORTED = "SUPPORTED"
    CONTESTED = "CONTESTED"
    REJECTED = "REJECTED"
    RETRACTED = "RETRACTED"


class EvidenceTier(str, Enum):
    TIER_1_RCT = "TIER_1_RCT"                      # Systematic review / RCT
    TIER_2_COHORT = "TIER_2_COHORT"                # Controlled cohort / observational
    TIER_3_CASE_REPORT = "TIER_3_CASE_REPORT"      # Case report / series
    TIER_4_CLASSICAL_TEXT = "TIER_4_CLASSICAL_TEXT"# Classical canonical literature
    TIER_5_EXPERT_OPINION = "TIER_5_EXPERT_OPINION"# Expert consensus / clinical note
    TIER_UNGRADED = "TIER_UNGRADED"                # Unclassified evidence


class CitationRelationship(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXT = "CONTEXT"
    CITES = "CITES"


class RelationType(str, Enum):
    CONTRADICTS = "CONTRADICTS"
    CORROBORATES = "CORROBORATES"
    SPECIALIZES = "SPECIALIZES"
    SUPERSEDES = "SUPERSEDES"


@dataclass
class Document:
    doc_id: str
    sha256_hash: str
    title: str
    author: str = "UNKNOWN"
    publication_date: str = "UNKNOWN"
    document_type: str = "MARKDOWN"
    namespace: str = DocumentNamespace.RESEARCH_NOTE.value
    language: str = "vi"
    source_uri: str = "UNKNOWN"
    original_path: str = "UNKNOWN"
    license: str = "UNKNOWN"
    imported_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    raw_content: str = ""
    review_status: str = "UNREVIEWED"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Claim:
    claim_id: str
    doc_id: str
    source_quote: str
    claim_text: str
    claim_type: str = ClaimType.ANATOMICAL_LOCATION.value
    assertion_type: str = AssertionType.ASSERTION.value
    status: str = ClaimStatus.UNREVIEWED.value
    evidence_tier: str = EvidenceTier.TIER_UNGRADED.value
    created_by: str = "system"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    uncertainty_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Citation:
    citation_id: str
    claim_id: str
    doc_id: str
    locator: str = ""
    relationship: str = CitationRelationship.SUPPORTS.value
    retrieval_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClaimRelation:
    relation_id: str
    source_claim_id: str
    target_claim_id: str
    relationship_type: str = RelationType.CONTRADICTS.value
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEvent:
    event_id: str
    entity_type: str  # DOCUMENT, CLAIM, RELATION, CITATION
    entity_id: str
    action: str       # IMPORT, CREATE, UPDATE, CONFLICT, REVIEW
    actor: str
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    rationale: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Review:
    review_id: str
    entity_type: str
    entity_id: str
    reviewer: str
    decision: str
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchFilter:
    query: str
    namespace: Optional[str] = None
    status: Optional[str] = None
    tag: Optional[str] = None
    doc_id: Optional[str] = None
    limit: int = 50


@dataclass
class SearchResult:
    result_type: str  # "DOCUMENT" or "CLAIM"
    id: str
    title_or_code: str
    snippet: str
    namespace: str
    status: str
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
