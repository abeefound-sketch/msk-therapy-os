"""Domain data models and enums for MSK-Therapy-OS M1."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    STUDENT = "student"
    REVIEWER = "reviewer"


class ReviewStatus(str, Enum):
    DRAFT = "DRAFT"
    SUPERVISED = "SUPERVISED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class EvidenceTier(int, Enum):
    TIER_1_CLINICAL_GUIDELINE = 1
    TIER_2_PEER_REVIEWED_ANATOMY = 2
    TIER_3_MANUFACTURER_MANUAL = 3
    TIER_4_TRADITIONAL_SCHEMA = 4


class KnowledgeNamespace(str, Enum):
    ANATOMY_EVIDENCE = "ANATOMY_EVIDENCE"
    TRADITIONAL_MERIDIAN = "TRADITIONAL_MERIDIAN"
    DIEN_CHAN_REFLEX = "DIEN_CHAN_REFLEX"


class Disposition(str, Enum):
    DOCUMENT_ONLY = "DOCUMENT_ONLY"
    STOP_AND_REFER = "STOP_AND_REFER"


class ROMSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    BILATERAL = "bilateral"
    MIDLINE = "midline"


class ROMMethod(str, Enum):
    GONIOMETER = "goniometer"
    INCLINOMETER = "inclinometer"
    VISUAL_ESTIMATE = "visual_estimate"
    TAPE_MEASURE = "tape_measure"


@dataclass(frozen=True)
class CaseRecord:
    case_id: str
    label: str


@dataclass(frozen=True)
class IntakeRecord:
    case_id: str
    age_band: str
    symptom_onset: str
    primary_region: str
    functional_limits: str
    prior_care: str
    operator_role: str
    created_utc: str


@dataclass(frozen=True)
class ROMRecord:
    id: Optional[int]
    visit_id: int
    motion: str
    side: str
    angle_deg: float
    method: str


@dataclass(frozen=True)
class SOAPRecord:
    id: Optional[int]
    visit_id: int
    subjective: str
    objective: str
    assessment: str
    plan: str
    author_role: str
    reviewed_by: Optional[str]
    review_status: str
    review_notes: Optional[str]
    created_utc: str


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    title: str
    url: str
    organization: str
    year: int
    license: str
    tier: int
    claim_scope: str
    reviewed_on: str
    reviewer: str


@dataclass(frozen=True)
class AnatomyRecord:
    structure_id: str
    name: str
    region: str
    source_dataset: str
    bodyparts3d_id: Optional[str]
    atlas_url: str
    namespace: str
    evidence_id: str


@dataclass(frozen=True)
class ObservationRecord:
    id: Optional[int]
    visit_id: int
    structure_id: str
    structure_type: str
    observation_type: str
    severity: int
    finding: str
    interpretation: str
    created_utc: str


@dataclass(frozen=True)
class SessionRecord:
    id: Optional[int]
    visit_id: int
    modality: str
    duration_min: int
    target_structures: str
    parameters: str
    adverse_reactions: str
    practitioner_role: str
    created_utc: str


@dataclass(frozen=True)
class QuestionnaireItem:
    item_id: str
    region: str
    scenario_title: str
    question_text: str
    safety_critical: bool
    evidence_id: str
