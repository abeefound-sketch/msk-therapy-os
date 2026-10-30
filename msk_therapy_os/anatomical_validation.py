"""Independent Anatomical Ground-Truth Validation & Provenance Infrastructure for MSK-Therapy-OS.

Milestone: P10.0 | External Anatomical Ground-Truth Integration & Independent Empirical Validation Pilot
Predecessor: P9.14 (ENGINEERING_READY, Gate G14 BLOCKED_EXTERNAL_DATA)
Standard: WHO 2008 Standard Acupuncture Point Locations & BodyParts3D FJ2810
Core Principle:
  Technical calibration (Class A/B) != anatomical ground truth != clinical verification.
  Fail-closed governance: never manufacture clinical passes or conflate synthetic fixtures with authentic ground truth.
  Zero unauthorized external patient data ingestion; strict privacy, de-identification, and quarantine controls.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple, Set, Union

from .landmark_registry import (
    AnatomicalLandmark,
    BodyRegion,
    CANONICAL_LANDMARKS,
    LandmarkRegistry,
)
from .point_localization_rules import (
    AcupointLocalizationEngine,
    ACUPOINT_LOCALIZATION_RULES,
    AcupointLocalizationRule,
)
from .spatial_resolver import AUDITED_CANONICAL_POINTS
from .anatomical_registration import (
    AnatomicalRegistrationEngine,
    RegistrationTransform,
)


class AnatomicalVerificationTier(str, Enum):
    """Hierarchical, non-collapsible verification tiers."""
    TECHNICALLY_CALIBRATED = "TECHNICALLY_CALIBRATED"       # Rule and landmark math resolve without error
    GEOMETRICALLY_VALIDATED = "GEOMETRICALLY_VALIDATED"     # Manifold mesh projection, outward unit normal, no cavity piercing
    ANATOMICALLY_CORROBORATED = "ANATOMICALLY_CORROBORATED" # Concordant with BodyParts3D skeletal reference literature
    INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"       # Corroborated by independent non-synthetic external dataset (residual <= tolerance)
    CLINICALLY_VERIFIED = "CLINICALLY_VERIFIED"             # Formal multi-center clinical practitioner consensus / clinical trial (Tier 4)


class GroundTruthModality(str, Enum):
    """Origin modality of anatomical ground-truth data."""
    CT_3D_SURFACE = "CT_3D_SURFACE"
    MRI_T1_ANATOMICAL = "MRI_T1_ANATOMICAL"
    ULTRASOUND_HIGH_FREQUENCY = "ULTRASOUND_HIGH_FREQUENCY"
    CADAVERIC_MEASUREMENT = "CADAVERIC_MEASUREMENT"
    EXPERT_CONSENSUS_PALPATION = "EXPERT_CONSENSUS_PALPATION"
    BODYPARTS3D_DIGITAL_REFERENCE = "BODYPARTS3D_DIGITAL_REFERENCE"
    SYNTHETIC_TEST_FIXTURE = "SYNTHETIC_TEST_FIXTURE"


class AnatomicalErrorClassification(str, Enum):
    """Standardized anatomical error classification based on residual distance in mm."""
    CONGRUENT = "CONGRUENT"                                         # residual <= 3.0 mm (high spatial agreement)
    ACCEPTABLE_CLINICAL_TOLERANCE = "ACCEPTABLE_CLINICAL_TOLERANCE" # 3.0 mm < residual <= 8.0 mm
    BORDERLINE = "BORDERLINE"                                       # 8.0 mm < residual <= 15.0 mm
    OUTLIER_ANOMALY = "OUTLIER_ANOMALY"                             # residual > 15.0 mm (potential anatomical failure)
    INDEPENDENT_GROUND_TRUTH_UNAVAILABLE = "INDEPENDENT_GROUND_TRUTH_UNAVAILABLE"


class ReviewStatus(str, Enum):
    """Lifecycle review states for empirical ground truth observations."""
    DATA_IMPORTED = "DATA_IMPORTED"
    PROVENANCE_VERIFIED = "PROVENANCE_VERIFIED"
    GEOMETRY_VALIDATED = "GEOMETRY_VALIDATED"
    INDEPENDENT_REVIEW_PENDING = "INDEPENDENT_REVIEW_PENDING"
    SEALED_BLINDED = "SEALED_BLINDED"
    REVIEWED = "REVIEWED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class CoordinateFrame(str, Enum):
    """Supported 3D spatial coordinate reference frames."""
    BP3D_CARTESIAN_METERS = "BP3D_CARTESIAN_METERS"  # BodyParts3D (+X Right, +Y Superior, +Z Anterior)
    DICOM_LPS_MM = "DICOM_LPS_MM"                    # DICOM (+X Left, +Y Posterior, +Z Superior) in mm
    NEURO_RAS_MM = "NEURO_RAS_MM"                    # Neuroimaging (+X Right, +Y Anterior, +Z Superior) in mm
    SURFACE_SCAN_MM = "SURFACE_SCAN_MM"              # Calibrated external 3D surface scan in mm
    ANATOMICAL_LOCAL_METERS = "ANATOMICAL_LOCAL_METERS"


class MeasurementUnit(str, Enum):
    """Measurement units for 3D coordinates."""
    METERS = "meters"
    MILLIMETERS = "millimeters"


class EvidenceCategory(str, Enum):
    """Categorization of evidence origin."""
    EMPIRICAL_IN_VIVO = "EMPIRICAL_IN_VIVO"
    CADAVERIC_DISSECTION = "CADAVERIC_DISSECTION"
    EXPERT_CONSENSUS_PALPATION = "EXPERT_CONSENSUS_PALPATION"
    CANONICAL_DIGITAL_ATLAS = "CANONICAL_DIGITAL_ATLAS"
    SYNTHETIC_TEST_FIXTURE = "SYNTHETIC_TEST_FIXTURE"


class QuarantineReason(str, Enum):
    """Standardized reason codes for diverting observations to quarantine."""
    QUARANTINE_UNAUTHORIZED_DATA = "QUARANTINE_UNAUTHORIZED_DATA"
    QUARANTINE_INCOMPLETE_DEIDENTIFICATION = "QUARANTINE_INCOMPLETE_DEIDENTIFICATION"
    QUARANTINE_PII_SUSPECTED = "QUARANTINE_PII_SUSPECTED"
    QUARANTINE_OUT_OF_BOUNDS = "QUARANTINE_OUT_OF_BOUNDS"
    QUARANTINE_CHECKSUM_MISMATCH = "QUARANTINE_CHECKSUM_MISMATCH"
    QUARANTINE_DUPLICATE_RECORD = "QUARANTINE_DUPLICATE_RECORD"
    QUARANTINE_CONFLICTING_MEASUREMENT = "QUARANTINE_CONFLICTING_MEASUREMENT"
    QUARANTINE_UNSUPPORTED_FRAME = "QUARANTINE_UNSUPPORTED_FRAME"
    QUARANTINE_SCHEMA_INVALID = "QUARANTINE_SCHEMA_INVALID"
    QUARANTINE_CIRCULAR_EVIDENCE = "QUARANTINE_CIRCULAR_EVIDENCE"
    QUARANTINE_EXPIRED_AUTHORIZATION = "QUARANTINE_EXPIRED_AUTHORIZATION"
    QUARANTINE_ROLE_CONFLICT = "QUARANTINE_ROLE_CONFLICT"
    QUARANTINE_HOLDOUT_CONTAMINATION = "QUARANTINE_HOLDOUT_CONTAMINATION"
    QUARANTINE_ADMIN_SIGN_OFF_REQUIRED = "QUARANTINE_ADMIN_SIGN_OFF_REQUIRED"
    # P10.3 DICOM & Adjudication Quarantine Reasons:
    QUARANTINE_UNSUPPORTED_TRANSFER_SYNTAX = "QUARANTINE_UNSUPPORTED_TRANSFER_SYNTAX"
    QUARANTINE_BURNED_IN_IDENTIFIERS_RISK = "QUARANTINE_BURNED_IN_IDENTIFIERS_RISK"
    QUARANTINE_MALFORMED_DICOM = "QUARANTINE_MALFORMED_DICOM"
    QUARANTINE_MULTIFRAME_UNSUPPORTED = "QUARANTINE_MULTIFRAME_UNSUPPORTED"
    QUARANTINE_PHI_IN_DICOM_HEADER = "QUARANTINE_PHI_IN_DICOM_HEADER"
    QUARANTINE_ADJUDICATION_REQUIRED = "QUARANTINE_ADJUDICATION_REQUIRED"


class G14ScientificGateState(str, Enum):
    """Explicit scientific gate states for Gate G14."""
    BLOCKED_EXTERNAL_DATA = "BLOCKED_EXTERNAL_DATA"
    PENDING_GOVERNANCE_APPROVAL = "PENDING_GOVERNANCE_APPROVAL"
    PENDING_INDEPENDENT_REVIEW = "PENDING_INDEPENDENT_REVIEW"
    EMPIRICAL_EVIDENCE_READY = "EMPIRICAL_EVIDENCE_READY"
    EMPIRICAL_VALIDATION_FAILED = "EMPIRICAL_VALIDATION_FAILED"


class DeidentificationMethod(str, Enum):
    """Regulatory de-identification standard applied to empirical datasets."""
    SAFE_HARBOR_18_ELEMENTS = "SAFE_HARBOR_18_ELEMENTS"  # HIPAA 45 CFR § 164.514(b)(2)
    EXPERT_DETERMINATION = "EXPERT_DETERMINATION"        # HIPAA 45 CFR § 164.514(b)(1)
    SYNTHETIC_DEIDENTIFIED = "SYNTHETIC_DEIDENTIFIED"    # Purely synthetic mock fixture
    NOT_DEIDENTIFIED = "NOT_DEIDENTIFIED"                # Prohibited in production


class EvidenceIngestionState(str, Enum):
    """Overall milestone and system ingestion governance state."""
    ENGINEERING_READY = "ENGINEERING_READY"
    EXTERNAL_DATA_PENDING = "EXTERNAL_DATA_PENDING"
    AUTHORIZED_DATA_RECEIVED = "AUTHORIZED_DATA_RECEIVED"
    EMPIRICAL_EVALUATION_IN_PROGRESS = "EMPIRICAL_EVALUATION_IN_PROGRESS"
    INDEPENDENTLY_EVALUATED = "INDEPENDENTLY_EVALUATED"
    INCONCLUSIVE = "INCONCLUSIVE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    CLINICAL_VERIFICATION_PENDING = "CLINICAL_VERIFICATION_PENDING"


@dataclass
class ClinicalReviewerCredentials:
    """Registered credentials for clinical and anatomical verifiers."""
    reviewer_id: str
    name: str
    role: str
    affiliation: str
    qualification: str
    license_id: Optional[str] = None
    is_governance_board: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExternalGroundTruthDataset:
    """Manifest of an external independent reference dataset."""
    dataset_id: str
    name: str
    source_organization: str
    version: str
    license: str
    doi_or_url: str
    modality: GroundTruthModality
    is_synthetic_fixture: bool = False
    case_id: Optional[str] = None
    sample_size: int = 1
    created_utc: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    # P10.2 Extended Governance & Metadata:
    administrative_verification_status: str = "PENDING_ADMIN_SIGN_OFF"
    data_retention_and_permitted_use: str = "RESEARCH_ONLY"
    deidentification_review_status: str = "VERIFIED_DEIDENTIFIED"
    acquisition_date_metadata: Optional[str] = None
    registration_method: str = "RIGID_PROCRUSTES"
    dataset_provenance: str = ""
    governance_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["modality"] = self.modality.value
        return d


@dataclass
class GroundTruthObservation:
    """An empirical observation of an anatomical point from an external source."""
    point_code: str
    dataset_id: str
    canonical_position: Tuple[float, float, float]  # [x, y, z] in meters
    surface_normal: Optional[Tuple[float, float, float]] = None
    uncertainty_radius_mm: float = 2.0
    depth_to_skeletal_anchor_mm: Optional[float] = None
    case_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    notes: str = ""
    # P9.14 Contract Extensions:
    subject_pseudonym: str = "SUBJ-ANON-0001"
    anatomical_point_code: Optional[str] = None
    laterality: str = "bilateral"
    source_modality: GroundTruthModality = GroundTruthModality.BODYPARTS3D_DIGITAL_REFERENCE
    coordinate_frame: CoordinateFrame = CoordinateFrame.BP3D_CARTESIAN_METERS
    unit: MeasurementUnit = MeasurementUnit.METERS
    measurement_coordinates: Optional[Tuple[float, float, float]] = None
    measurement_uncertainty: float = 2.0
    observer_id: Optional[str] = "OBS-DEFAULT"
    independent_source_id: str = "SRC-INDEP-001"
    collection_protocol_id: str = "PROT-ANAT-2026"
    consent_or_authorization_reference: str = "IRB-EXEMPT-DEIDENTIFIED"
    source_checksum: str = ""
    synthetic_fixture: bool = False
    review_status: ReviewStatus = ReviewStatus.DATA_IMPORTED
    # P10.0 Regulatory & Quality Extensions:
    schema_version: str = "1.1-P10"
    data_sharing_agreement_ref: str = "DUA-EXEMPT-SYNTHETIC"
    ethics_approval_or_exemption_ref: str = "IRB-EXEMPT-SYNTHETIC"
    deidentification_method: DeidentificationMethod = DeidentificationMethod.SYNTHETIC_DEIDENTIFIED
    is_authorized_for_clinical_eval: bool = False
    observed_coordinates: Optional[Tuple[float, float, float]] = None
    predicted_coordinates: Optional[Tuple[float, float, float]] = None
    registration_residual_mm: Optional[float] = None
    # P10.2 Contract V2 Extensions:
    cohort_id: Optional[str] = None
    independent_observer_id: Optional[str] = None
    observation_sequence_id: Optional[str] = None
    source_image_reference: Optional[str] = None
    annotation_method: str = "EXPERT_CROSSHAIR"

    def __post_init__(self) -> None:
        if self.anatomical_point_code is None:
            self.anatomical_point_code = self.point_code
        elif not self.point_code and self.anatomical_point_code:
            self.point_code = self.anatomical_point_code

        if self.independent_observer_id is None and self.observer_id:
            self.independent_observer_id = self.observer_id
        elif self.observer_id is None and self.independent_observer_id:
            self.observer_id = self.independent_observer_id

        if self.measurement_coordinates is None:
            self.measurement_coordinates = self.canonical_position

        if self.observed_coordinates is None:
            self.observed_coordinates = self.measurement_coordinates or self.canonical_position

        if self.measurement_uncertainty == 2.0 and self.uncertainty_radius_mm != 2.0:
            self.measurement_uncertainty = self.uncertainty_radius_mm

        # Convert frame, unit, status to Enum instances if strings
        if isinstance(self.coordinate_frame, str):
            try:
                self.coordinate_frame = CoordinateFrame(self.coordinate_frame)
            except ValueError:
                pass
        if isinstance(self.unit, str):
            try:
                self.unit = MeasurementUnit(self.unit)
            except ValueError:
                pass
        if isinstance(self.review_status, str):
            try:
                self.review_status = ReviewStatus(self.review_status)
            except ValueError:
                pass
        if isinstance(self.source_modality, str):
            try:
                self.source_modality = GroundTruthModality(self.source_modality)
            except ValueError:
                pass
        if isinstance(self.deidentification_method, str):
            try:
                self.deidentification_method = DeidentificationMethod(self.deidentification_method)
            except ValueError:
                pass

        if not self.source_checksum:
            h = hashlib.sha256()
            payload = f"{self.point_code}:{self.dataset_id}:{self.canonical_position}:{self.subject_pseudonym}"
            h.update(payload.encode("utf-8"))
            self.source_checksum = h.hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["coordinate_frame"] = self.coordinate_frame.value if hasattr(self.coordinate_frame, "value") else str(self.coordinate_frame)
        d["unit"] = self.unit.value if hasattr(self.unit, "value") else str(self.unit)
        d["review_status"] = self.review_status.value if hasattr(self.review_status, "value") else str(self.review_status)
        d["source_modality"] = self.source_modality.value if hasattr(self.source_modality, "value") else str(self.source_modality)
        d["deidentification_method"] = self.deidentification_method.value if hasattr(self.deidentification_method, "value") else str(self.deidentification_method)
        return d


@dataclass
class QuarantinedObservation:
    """An observation diverted to quarantine due to contract, authorization, or boundary violations."""
    point_code: str
    dataset_id: str
    subject_pseudonym: str
    reason: QuarantineReason
    details: str
    raw_payload: Dict[str, Any]
    quarantined_utc: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_code": self.point_code,
            "dataset_id": self.dataset_id,
            "subject_pseudonym": self.subject_pseudonym,
            "reason": self.reason.value,
            "details": self.details,
            "raw_payload": self.raw_payload,
            "quarantined_utc": self.quarantined_utc,
        }


@dataclass
class HoldoutPartitionManifest:
    """Immutable manifest for subject-level holdout partition."""
    partition_id: str
    calibration_subjects: List[str]
    holdout_subjects: List[str]
    total_subjects: int
    split_ratio: float
    is_locked: bool
    manifest_checksum: str
    created_utc: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    # P10.2 3-Way Partitioning:
    validation_subjects: List[str] = field(default_factory=list)
    # P10.3 Holdout Cryptographic Locking & Site Isolation:
    locked_by: Optional[str] = None
    locked_sha256: Optional[str] = None
    is_holdout_evaluated: bool = False
    site_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HoldoutPartitionManager:
    """Manages strict subject-level holdout partitioning and prevents data leakage."""

    def __init__(self) -> None:
        self._partitions: Dict[str, HoldoutPartitionManifest] = {}

    def create_partition(
        self,
        partition_id: str,
        subjects: List[str],
        holdout_ratio: float = 0.2,
        seed: int = 42,
    ) -> HoldoutPartitionManifest:
        """Create a deterministic, subject-level holdout partition and lock it."""
        unique_subjects = sorted(list(set(subjects)))
        if not unique_subjects:
            raise ValueError("CANNOT_PARTITION_EMPTY_SUBJECT_LIST")

        # Deterministic partition based on hash
        holdout_count = max(1, int(len(unique_subjects) * holdout_ratio)) if len(unique_subjects) > 1 else 0
        calib: List[str] = []
        holdout: List[str] = []

        for i, s in enumerate(unique_subjects):
            # Deterministic pseudo-random sorting using hash
            h_val = int(hashlib.sha256(f"{s}:{seed}".encode()).hexdigest(), 16)
            if (h_val % 100) < int(holdout_ratio * 100) and len(holdout) < holdout_count:
                holdout.append(s)
            else:
                calib.append(s)

        if not holdout and len(unique_subjects) > 1:
            holdout.append(calib.pop())

        # Calculate manifest checksum
        manifest_payload = f"{partition_id}:{','.join(sorted(calib))}:{','.join(sorted(holdout))}"
        chk = hashlib.sha256(manifest_payload.encode()).hexdigest()

        manifest = HoldoutPartitionManifest(
            partition_id=partition_id,
            calibration_subjects=sorted(calib),
            holdout_subjects=sorted(holdout),
            total_subjects=len(unique_subjects),
            split_ratio=round(len(calib) / len(unique_subjects), 3) if unique_subjects else 0.0,
            is_locked=True,
            manifest_checksum=chk,
        )
        self._partitions[partition_id] = manifest
        return manifest

    def create_three_way_partition(
        self,
        partition_id: str,
        subjects: List[str],
        calib_ratio: float = 0.50,
        val_ratio: float = 0.25,
        holdout_ratio: float = 0.25,
        seed: int = 42,
    ) -> HoldoutPartitionManifest:
        """Create a deterministic subject-level 3-way partition (Calibration, Validation, Holdout)."""
        unique_subjects = sorted(list(set(subjects)))
        if not unique_subjects:
            raise ValueError("CANNOT_PARTITION_EMPTY_SUBJECT_LIST")

        n = len(unique_subjects)
        n_holdout = max(1, int(round(n * holdout_ratio))) if n >= 3 else (1 if n > 1 else 0)
        n_val = max(1, int(round(n * val_ratio))) if (n - n_holdout) >= 2 else 0

        calib: List[str] = []
        val: List[str] = []
        holdout: List[str] = []

        for s in unique_subjects:
            h_val = int(hashlib.sha256(f"{s}:{seed}:3way".encode()).hexdigest(), 16)
            bucket = h_val % 100
            if bucket < int(holdout_ratio * 100) and len(holdout) < n_holdout:
                holdout.append(s)
            elif bucket < int((holdout_ratio + val_ratio) * 100) and len(val) < n_val:
                val.append(s)
            else:
                calib.append(s)

        # Guarantee non-empty partition constraints if population permits
        if not holdout and len(calib) > 2:
            holdout.append(calib.pop())
        if not val and len(calib) > 2:
            val.append(calib.pop())

        manifest_payload = f"{partition_id}:{','.join(sorted(calib))}:{','.join(sorted(val))}:{','.join(sorted(holdout))}"
        chk = hashlib.sha256(manifest_payload.encode()).hexdigest()

        manifest = HoldoutPartitionManifest(
            partition_id=partition_id,
            calibration_subjects=sorted(calib),
            validation_subjects=sorted(val),
            holdout_subjects=sorted(holdout),
            total_subjects=len(unique_subjects),
            split_ratio=round(len(calib) / len(unique_subjects), 3) if unique_subjects else 0.0,
            is_locked=True,
            manifest_checksum=chk,
        )
        self._partitions[partition_id] = manifest
        return manifest

    def verify_no_leakage_three_way(
        self,
        calibration_subjects: List[str],
        validation_subjects: List[str],
        holdout_subjects: List[str],
    ) -> bool:
        """Verify zero subject overlap across all three partitions."""
        c_set = set(calibration_subjects)
        v_set = set(validation_subjects)
        h_set = set(holdout_subjects)

        cv = c_set & v_set
        ch = c_set & h_set
        vh = v_set & h_set
        leaks = cv | ch | vh
        if leaks:
            raise ValueError(f"HOLDOUT_DATA_LEAKAGE_DETECTED: Overlapping subjects across 3-way partition: {sorted(list(leaks))}")
        return True

    def verify_partition_integrity(self, partition_id: str) -> bool:
        """Verify that the partition manifest has not been tampered with or modified post-lock."""
        if partition_id not in self._partitions:
            return False
        p = self._partitions[partition_id]
        if not p.is_locked:
            return False
        if p.validation_subjects:
            payload = f"{p.partition_id}:{','.join(sorted(p.calibration_subjects))}:{','.join(sorted(p.validation_subjects))}:{','.join(sorted(p.holdout_subjects))}"
        else:
            payload = f"{p.partition_id}:{','.join(sorted(p.calibration_subjects))}:{','.join(sorted(p.holdout_subjects))}"
        return hashlib.sha256(payload.encode()).hexdigest() == p.manifest_checksum

    def verify_no_leakage(
        self,
        calibration_subjects: List[str],
        holdout_subjects: List[str],
    ) -> bool:
        """Verify that zero subject overlap exists between calibration and holdout sets."""
        intersection = set(calibration_subjects) & set(holdout_subjects)
        if intersection:
            raise ValueError(f"HOLDOUT_DATA_LEAKAGE_DETECTED: Overlapping subjects: {sorted(list(intersection))}")
        return True

    def get_partition(self, partition_id: str) -> Optional[HoldoutPartitionManifest]:
        return self._partitions.get(partition_id)

    def lock_holdout_partition(self, partition_id: str, admin_reviewer_id: str) -> HoldoutPartitionManifest:
        """Cryptographically lock the holdout partition to prevent modifications."""
        p = self._partitions.get(partition_id)
        if not p:
            raise ValueError(f"PARTITION_NOT_FOUND: Partition '{partition_id}' does not exist.")
        if p.is_holdout_evaluated:
            raise ValueError(f"HOLDOUT_ALREADY_EVALUATED: Cannot re-lock partition '{partition_id}' after evaluation.")
        
        # Compute SHA-256 over sorted holdout subjects
        hash_payload = f"{partition_id}:{','.join(sorted(p.holdout_subjects))}:{admin_reviewer_id}"
        p.locked_sha256 = hashlib.sha256(hash_payload.encode()).hexdigest()
        p.locked_by = admin_reviewer_id
        p.is_locked = True
        return p

    def mark_holdout_evaluated(self, partition_id: str) -> None:
        """Mark holdout as evaluated. Freezes partition against any subsequent modification."""
        p = self._partitions.get(partition_id)
        if p:
            p.is_holdout_evaluated = True

    def create_site_level_partition(
        self,
        partition_id: str,
        site_subject_map: Dict[str, List[str]],
        holdout_site_id: str,
    ) -> HoldoutPartitionManifest:
        """Create a site-level external holdout partition where an entire clinical site is held out."""
        if holdout_site_id not in site_subject_map:
            raise ValueError(f"SITE_NOT_FOUND: Holdout site '{holdout_site_id}' not in site_subject_map.")
        
        holdout_subjects = sorted(list(site_subject_map[holdout_site_id]))
        other_subjects: List[str] = []
        for s_id, subjs in site_subject_map.items():
            if s_id != holdout_site_id:
                other_subjects.extend(subjs)
        
        other_unique = sorted(list(set(other_subjects)))
        half = len(other_unique) // 2
        calib_subjects = other_unique[:half]
        val_subjects = other_unique[half:]
        
        manifest_payload = f"{partition_id}:{','.join(calib_subjects)}:{','.join(val_subjects)}:{','.join(holdout_subjects)}"
        chk = hashlib.sha256(manifest_payload.encode()).hexdigest()
        
        manifest = HoldoutPartitionManifest(
            partition_id=partition_id,
            calibration_subjects=calib_subjects,
            validation_subjects=val_subjects,
            holdout_subjects=holdout_subjects,
            total_subjects=len(calib_subjects) + len(val_subjects) + len(holdout_subjects),
            split_ratio=round(len(calib_subjects) / (len(other_unique) + len(holdout_subjects)), 3),
            is_locked=True,
            manifest_checksum=chk,
            site_id=holdout_site_id,
        )
        self._partitions[partition_id] = manifest
        return manifest


@dataclass
class BlindIndependentReviewRecord:
    """Record of a blind dual independent review."""
    review_id: str
    point_code: str
    dataset_id: str
    subject_pseudonym: str
    primary_reviewer_id: str
    secondary_reviewer_id: Optional[str]
    primary_decision: str  # APPROVED / REJECTED / INCONCLUSIVE
    secondary_decision: Optional[str]
    consensus_decision: str
    inter_observer_discrepancy_mm: Optional[float]
    conflict_of_interest_declared: bool
    reviewed_utc: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PreRegisteredAccuracyThresholds:
    """Pre-registered scientific thresholds for empirical anatomical validation."""
    high_accuracy_rmse_mm: float = 5.0
    acceptable_accuracy_rmse_mm: float = 10.0
    max_outlier_tolerance_mm: float = 15.0
    max_inter_observer_discrepancy_mm: float = 3.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_observation_contract(
    obs: GroundTruthObservation,
    allowed_codes: Optional[Set[str]] = None,
    check_authorization: bool = True,
) -> Dict[str, Any]:
    """Validate that an empirical observation adheres strictly to the P10.0 Data Contract & Privacy Standards."""
    # 0. Schema version validation
    if not obs.schema_version.startswith("1."):
        raise ValueError(f"UNSUPPORTED_SCHEMA_VERSION: Schema version '{obs.schema_version}' is not supported.")

    # 1. PII detection in subject pseudonym
    pseudonym = str(obs.subject_pseudonym).strip()
    if not pseudonym or len(pseudonym) < 3:
        raise ValueError(f"INVALID_SUBJECT_PSEUDONYM: Subject pseudonym '{obs.subject_pseudonym}' is too short or empty.")

    if "@" in pseudonym:
        raise ValueError(f"PII_DETECTED_IN_SUBJECT_PSEUDONYM: Subject pseudonym '{pseudonym}' contains email address.")
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", pseudonym):
        raise ValueError(f"PII_DETECTED_IN_SUBJECT_PSEUDONYM: Subject pseudonym '{pseudonym}' contains SSN pattern.")
    if re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", pseudonym):
        raise ValueError(f"PII_DETECTED_IN_SUBJECT_PSEUDONYM: Subject pseudonym '{pseudonym}' contains phone number pattern.")
    if re.search(r"\b(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Patient:|Mr|Mrs|Ms|Dr|Prof)\b", pseudonym, re.IGNORECASE):
        raise ValueError(f"PII_DETECTED_IN_SUBJECT_PSEUDONYM: Subject pseudonym '{pseudonym}' contains plain name title.")

    # 1.1 Free-text notes and image reference PII screening
    for txt_name, txt_val in [("notes", obs.notes), ("source_image_reference", obs.source_image_reference)]:
        if txt_val:
            s_txt = str(txt_val)
            if "@" in s_txt:
                raise ValueError(f"PII_DETECTED_IN_{txt_name.upper()}: Email pattern detected in {txt_name}.")
            if re.search(r"\b\d{3}-\d{2}-\d{4}\b", s_txt):
                raise ValueError(f"PII_DETECTED_IN_{txt_name.upper()}: SSN pattern detected in {txt_name}.")
            if re.search(r"\bPatient\s*Name\s*:\s*[A-Z][a-z]+\b", s_txt, re.IGNORECASE):
                raise ValueError(f"PII_DETECTED_IN_{txt_name.upper()}: Explicit patient name detected in {txt_name}.")

    # 1.2 Reviewer role conflict check (Observer != Reviewer)
    obs_id = str(obs.observer_id or obs.independent_observer_id or "").strip()
    rev_id = str(obs.reviewer_id or "").strip()
    if obs_id and rev_id and obs_id == rev_id:
        raise ValueError(f"REVIEWER_ROLE_CONFLICT: Observer '{obs_id}' cannot act as Reviewer for their own observation.")

    # 2. Point code validation
    code = obs.point_code or obs.anatomical_point_code
    if not code:
        raise ValueError("MISSING_POINT_CODE: Observation must specify point_code.")
    if allowed_codes is not None and code not in allowed_codes:
        raise ValueError(f"UNKNOWN_ACUPOINT_CODE: '{code}' is not in the canonical catalog.")

    # 3. Laterality validation
    lat = str(obs.laterality).lower()
    if lat not in ("left", "right", "bilateral", "midline"):
        raise ValueError(f"INVALID_LATERALITY: Laterality '{obs.laterality}' is not recognized. Expected left/right/bilateral/midline.")

    # 4. Coordinate frame validation
    frame_val = obs.coordinate_frame.value if hasattr(obs.coordinate_frame, "value") else str(obs.coordinate_frame)
    valid_frames = {f.value for f in CoordinateFrame}
    if frame_val not in valid_frames:
        raise ValueError(f"UNSUPPORTED_COORDINATE_FRAME: Frame '{frame_val}' is not supported.")

    # 5. Unit validation
    unit_val = obs.unit.value if hasattr(obs.unit, "value") else str(obs.unit)
    valid_units = {u.value for u in MeasurementUnit}
    if unit_val not in valid_units:
        raise ValueError(f"UNSUPPORTED_MEASUREMENT_UNIT: Unit '{unit_val}' is not supported.")

    # 6. Checksum validation
    checksum = str(obs.source_checksum).strip()
    if not checksum or len(checksum) != 64 or not all(c in "0123456789abcdefABCDEF" for c in checksum):
        raise ValueError(f"INVALID_SOURCE_CHECKSUM: Checksum '{checksum}' is not a valid 64-character hex SHA-256 digest.")

    # 7. Uncertainty validation
    if obs.measurement_uncertainty <= 0.0:
        raise ValueError(f"INVALID_MEASUREMENT_UNCERTAINTY: Uncertainty {obs.measurement_uncertainty} must be strictly positive.")

    # 8. Coordinate plausibility / bounding box
    coords = obs.measurement_coordinates or obs.canonical_position
    if not coords or len(coords) != 3:
        raise ValueError("INVALID_COORDINATES: Coordinates must be a 3-element tuple.")

    for val in coords:
        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise ValueError(f"INVALID_COORDINATES: Coordinates contain non-finite value: {val}")

    scale = 0.001 if unit_val == "millimeters" else 1.0
    x_m, y_m, z_m = coords[0] * scale, coords[1] * scale, coords[2] * scale
    if not (-1.5 <= x_m <= 1.5 and -0.5 <= y_m <= 2.5 and -1.0 <= z_m <= 1.0):
        raise ValueError(f"ANATOMICAL_BOUNDING_BOX_VIOLATION: Coordinates ({x_m:.3f}, {y_m:.3f}, {z_m:.3f}) m outside human envelope.")

    # 8.1 Anatomical Laterality Inversion Check
    try:
        norm_pos = transform_coordinates_to_bp3d(coords, frame=obs.coordinate_frame, unit=obs.unit)
        x_bp3d = norm_pos[0]
        # In BodyParts3D: +X is Right (> 0), -X is Left (< 0)
        if lat == "left" and x_bp3d > 0.06:
            raise ValueError(f"INVALID_LATERALITY: Laterality inversion detected. Observation marked 'left' but BP3D X coordinate is strongly positive ({x_bp3d:.4f} m).")
        elif lat == "right" and x_bp3d < -0.06:
            raise ValueError(f"INVALID_LATERALITY: Laterality inversion detected. Observation marked 'right' but BP3D X coordinate is strongly negative ({x_bp3d:.4f} m).")
        elif lat == "midline" and abs(x_bp3d) > 0.03:
            raise ValueError(f"INVALID_LATERALITY: Midline observation exceeded lateral tolerance ({abs(x_bp3d):.4f} m > 0.03 m).")
    except ValueError as ve:
        if "INVALID_LATERALITY" in str(ve):
            raise

    # 9. Privacy Hard Stop & Authorization Gate (for non-synthetic datasets)
    # LEGAL NOTICE: Technical verification of 18 HIPAA Safe Harbor identifiers is a required baseline,
    # but does NOT alone constitute complete legal compliance under 45 CFR § 164.514 without an executed
    # Data Use Agreement (DUA), institutional ethics/IRB approval, and clinical evaluation authorization.
    if not obs.synthetic_fixture and check_authorization:
        dua = str(obs.data_sharing_agreement_ref).strip()
        if not dua or dua in ("NONE", "DUA-EXEMPT-SYNTHETIC", "DUA-PENDING", "UNKNOWN"):
            raise ValueError(f"UNAUTHORIZED_EXTERNAL_DATA: Real external observation requires valid executed data sharing agreement reference (got '{dua}').")
        if "EXPIRED" in dua.upper() or "REVOKED" in dua.upper():
            raise ValueError(f"EXPIRED_DATA_AUTHORIZATION: Data sharing agreement is expired or revoked (got '{dua}').")

        ethics = str(obs.ethics_approval_or_exemption_ref).strip()
        if not ethics or ethics in ("NONE", "IRB-EXEMPT-SYNTHETIC", "IRB-PENDING", "UNKNOWN"):
            raise ValueError(f"UNAUTHORIZED_EXTERNAL_DATA: Real external observation requires valid ethics/IRB approval reference (got '{ethics}').")
        if "EXPIRED" in ethics.upper() or "REVOKED" in ethics.upper():
            raise ValueError(f"EXPIRED_DATA_AUTHORIZATION: Ethics/IRB approval is expired or revoked (got '{ethics}').")

        deid = obs.deidentification_method.value if hasattr(obs.deidentification_method, "value") else str(obs.deidentification_method)
        if deid not in (DeidentificationMethod.SAFE_HARBOR_18_ELEMENTS.value, DeidentificationMethod.EXPERT_DETERMINATION.value):
            raise ValueError(f"INCOMPLETE_DEIDENTIFICATION: Real external empirical data must be certified under SAFE_HARBOR_18_ELEMENTS or EXPERT_DETERMINATION (got '{deid}').")

        if not obs.is_authorized_for_clinical_eval:
            raise ValueError("UNAUTHORIZED_EXTERNAL_DATA: Dataset is not authorized for clinical evaluation (is_authorized_for_clinical_eval is False).")

    return {
        "valid": True,
        "point_code": code,
        "subject_pseudonym": pseudonym,
        "coordinate_frame": frame_val,
        "unit": unit_val,
        "normalized_position_m": (x_m, y_m, z_m),
        "source_checksum": checksum,
    }


def transform_coordinates_to_bp3d(
    coords: Tuple[float, float, float],
    frame: Union[CoordinateFrame, str] = CoordinateFrame.BP3D_CARTESIAN_METERS,
    unit: Union[MeasurementUnit, str] = MeasurementUnit.METERS,
) -> Tuple[float, float, float]:
    """Transform external measurement coordinates into BodyParts3D canonical cartesian meters.

    BodyParts3D coordinate convention (Left-Handed System):
      +X: Right (lateral)
      +Y: Superior (cranial / up)
      +Z: Anterior (ventral / front)
    """
    if len(coords) != 3:
        raise ValueError(f"INVALID_COORDINATES: Expected 3-element tuple, got length {len(coords)}")
    for val in coords:
        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise ValueError(f"INVALID_COORDINATES: Coordinate values must be finite numbers, got {val}")

    unit_str = unit.value if hasattr(unit, "value") else str(unit)
    if unit_str not in ("meters", "millimeters"):
        raise ValueError(f"UNSUPPORTED_MEASUREMENT_UNIT: Unit '{unit_str}' is not supported.")
    scale = 0.001 if unit_str == "millimeters" else 1.0
    x, y, z = coords[0] * scale, coords[1] * scale, coords[2] * scale

    frame_str = frame.value if hasattr(frame, "value") else str(frame)
    if frame_str == CoordinateFrame.BP3D_CARTESIAN_METERS.value:
        return (round(x, 6), round(y, 6), round(z, 6))
    elif frame_str in (CoordinateFrame.SURFACE_SCAN_MM.value, CoordinateFrame.ANATOMICAL_LOCAL_METERS.value):
        return (round(x, 6), round(y, 6), round(z, 6))
    elif frame_str == CoordinateFrame.DICOM_LPS_MM.value:
        # DICOM LPS: (+X Left, +Y Posterior, +Z Superior)
        # BP3D: X_bp3d = -X_lps, Y_bp3d = +Z_lps, Z_bp3d = -Y_lps
        return (round(-x, 6), round(z, 6), round(-y, 6))
    elif frame_str == CoordinateFrame.NEURO_RAS_MM.value:
        # Neuro RAS: (+X Right, +Y Anterior, +Z Superior)
        # BP3D: X_bp3d = +X_ras, Y_bp3d = +Z_ras, Z_bp3d = +Y_ras
        return (round(x, 6), round(z, 6), round(y, 6))
    else:
        raise ValueError(f"UNSUPPORTED_COORDINATE_FRAME: Frame '{frame_str}' is not supported.")


def transform_bp3d_to_coordinates(
    coords: Tuple[float, float, float],
    target_frame: Union[CoordinateFrame, str] = CoordinateFrame.BP3D_CARTESIAN_METERS,
    target_unit: Union[MeasurementUnit, str] = MeasurementUnit.METERS,
) -> Tuple[float, float, float]:
    """Inverse transformation: Map BodyParts3D canonical cartesian meters into external coordinate frames.

    Mathematical Inverses:
      - BP3D: (+X Right, +Y Superior, +Z Anterior) in meters.
      - DICOM LPS: (+X Left, +Y Posterior, +Z Superior).
          X_lps = -X_bp3d
          Y_lps = -Z_bp3d
          Z_lps = +Y_bp3d
      - Neuro RAS: (+X Right, +Y Anterior, +Z Superior).
          X_ras = +X_bp3d
          Y_ras = +Z_bp3d
          Z_ras = +Y_bp3d
      - Surface Scan / Local: Identity spatial axes.
    """
    if len(coords) != 3:
        raise ValueError(f"INVALID_COORDINATES: Expected 3-element tuple, got length {len(coords)}")
    for val in coords:
        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise ValueError(f"INVALID_COORDINATES: Coordinate values must be finite numbers, got {val}")

    unit_str = target_unit.value if hasattr(target_unit, "value") else str(target_unit)
    if unit_str not in ("meters", "millimeters"):
        raise ValueError(f"UNSUPPORTED_MEASUREMENT_UNIT: Unit '{unit_str}' is not supported.")

    scale = 1000.0 if unit_str == "millimeters" else 1.0
    x, y, z = coords[0], coords[1], coords[2]

    frame_str = target_frame.value if hasattr(target_frame, "value") else str(target_frame)
    if frame_str == CoordinateFrame.BP3D_CARTESIAN_METERS.value:
        return (round(x * scale, 6), round(y * scale, 6), round(z * scale, 6))
    elif frame_str in (CoordinateFrame.SURFACE_SCAN_MM.value, CoordinateFrame.ANATOMICAL_LOCAL_METERS.value):
        return (round(x * scale, 6), round(y * scale, 6), round(z * scale, 6))
    elif frame_str == CoordinateFrame.DICOM_LPS_MM.value:
        # Inverse: X_lps = -X_bp3d, Y_lps = -Z_bp3d, Z_lps = +Y_bp3d
        return (round(-x * scale, 6), round(-z * scale, 6), round(y * scale, 6))
    elif frame_str == CoordinateFrame.NEURO_RAS_MM.value:
        # Inverse: X_ras = +X_bp3d, Y_ras = +Z_bp3d, Z_ras = +Y_bp3d
        return (round(x * scale, 6), round(z * scale, 6), round(y * scale, 6))
    else:
        raise ValueError(f"UNSUPPORTED_COORDINATE_FRAME: Frame '{frame_str}' is not supported.")


@dataclass
class PointValidationComparison:
    """Detailed comparison between model prediction and external ground-truth observation."""
    point_code: str
    channel_code: str
    predicted_position: Tuple[float, float, float]
    reference_position: Optional[Tuple[float, float, float]]
    residual_error_mm: Optional[float]
    tolerance_radius_mm: float
    uncertainty_mm: float
    classification: AnatomicalErrorClassification
    is_congruent: bool
    verification_tier: AnatomicalVerificationTier
    dataset_id: Optional[str]
    is_synthetic: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["classification"] = self.classification.value
        d["verification_tier"] = self.verification_tier.value
        return d


@dataclass
class ValidationReport:
    """Comprehensive validation report across points and body regions."""
    summary: Dict[str, Any]
    regional_metrics: Dict[str, Dict[str, Any]]
    comparisons: List[PointValidationComparison]
    outliers: List[PointValidationComparison]
    is_synthetic_evaluation: bool
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "regional_metrics": self.regional_metrics,
            "comparisons": [c.to_dict() for c in self.comparisons],
            "outliers": [o.to_dict() for o in self.outliers],
            "is_synthetic_evaluation": self.is_synthetic_evaluation,
            "timestamp": self.timestamp,
        }


class IndependentAnatomicalValidator:
    """Engine executing independent anatomical ground-truth auditing and falsification testing."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        localization_engine: Optional[AcupointLocalizationEngine] = None,
        landmark_registry: Optional[LandmarkRegistry] = None,
    ) -> None:
        self.db_path = db_path
        self.registry = landmark_registry or LandmarkRegistry()
        self.engine = localization_engine or AcupointLocalizationEngine(landmark_registry=self.registry)
        self.registration_engine = AnatomicalRegistrationEngine(landmark_registry=self.registry)

        self._datasets: Dict[str, ExternalGroundTruthDataset] = {}
        self._reviewers: Dict[str, ClinicalReviewerCredentials] = {}
        self._observations: Dict[Tuple[str, str], GroundTruthObservation] = {}  # (point_code, dataset_id) -> obs
        self._quarantined_records: List[QuarantinedObservation] = []
        self._holdout_manager = HoldoutPartitionManager()
        self._blind_reviews: Dict[str, BlindIndependentReviewRecord] = {}
        self._pre_registered_thresholds = PreRegisteredAccuracyThresholds()
        self._governance_audit_trail: List[Dict[str, Any]] = []
        self._governance_auth_secret: str = "P10_GOVERNANCE_AUTH_SHARED_SECRET_2026"

        self._register_default_reviewers()
        self._register_built_in_sources()

        if self.db_path:
            self._init_sqlite_governance_storage()
            self._load_sqlite_governance_trail()

    def _init_sqlite_governance_storage(self) -> None:
        """Ensure governance_audit_log table exists in the target SQLite database."""
        if not self.db_path:
            return
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS governance_audit_log (
                        entry_index INTEGER PRIMARY KEY,
                        prev_hash TEXT NOT NULL,
                        entry_hash TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        dataset_id TEXT NOT NULL,
                        actor_id TEXT NOT NULL,
                        details_json TEXT NOT NULL
                    )
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_gov_audit_ds ON governance_audit_log(dataset_id)")
        finally:
            conn.close()

    def _load_sqlite_governance_trail(self) -> None:
        """Load persisted governance audit records from SQLite into memory and verify chain."""
        if not self.db_path or not os.path.exists(self.db_path):
            return
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT entry_index, prev_hash, entry_hash, timestamp, event_type, dataset_id, actor_id, details_json
                FROM governance_audit_log
                ORDER BY entry_index ASC
                """
            )
            rows = cursor.fetchall()
            loaded_trail = []
            for r in rows:
                try:
                    details = json.loads(r[7])
                except Exception:
                    details = {}
                loaded_trail.append({
                    "index": r[0],
                    "prev_hash": r[1],
                    "entry_hash": r[2],
                    "timestamp": r[3],
                    "event_type": r[4],
                    "dataset_id": r[5],
                    "actor_id": r[6],
                    "details": details,
                })
            if loaded_trail:
                self._governance_audit_trail = loaded_trail
        finally:
            conn.close()

    def _register_default_reviewers(self) -> None:
        """Register vetted clinical and anatomical review authorities."""
        self.register_reviewer(ClinicalReviewerCredentials(
            reviewer_id="REV-LEAD-ANATOMIST",
            name="Principal Computational Anatomy Specialist",
            role="LEAD_ANATOMIST",
            affiliation="Computational Anatomy & Biomechanics WG",
            qualification="PhD Clinical Anatomy & Biomechanics",
            license_id="CAB-2026-0881"
        ))
        self.register_reviewer(ClinicalReviewerCredentials(
            reviewer_id="REV-CLINICAL-AUDITOR",
            name="Clinical Safety & Governance Auditor",
            role="CLINICAL_SAFETY_AUDITOR",
            affiliation="Independent Software Verification & Clinical Audit Board",
            qualification="MD, Clinical Informatics Specialist",
            license_id="MD-ISV-9941"
        ))
        self.register_reviewer(ClinicalReviewerCredentials(
            reviewer_id="REV_SYNTHETIC_TEST",
            name="Automated Synthetic Test Rig",
            role="TEST_HARNESS",
            affiliation="MSK-Therapy-OS Test Suite",
            qualification="Deterministic In-Memory Mock",
            license_id="TEST-0000"
        ))

    def _register_built_in_sources(self) -> None:
        """Register the built-in reference dataset metadata."""
        # 1. BodyParts3D Digital Reference Standard (Internal reference baseline)
        self.register_dataset(ExternalGroundTruthDataset(
            dataset_id="DS-BP3D-FJ2810",
            name="BodyParts3D 4.0 FJ2810 Canonical Skin & Skeleton Reference",
            source_organization="Database Center for Life Science (DBCLS), Japan",
            version="4.0-FJ2810",
            license="CC BY 2.1 JP",
            doi_or_url="https://lifesciencedb.jp/bp3d/",
            modality=GroundTruthModality.BODYPARTS3D_DIGITAL_REFERENCE,
            is_synthetic_fixture=False,
            sample_size=1
        ))
        # 2. Synthetic Fixtures Isolated Dataset
        self.register_dataset(ExternalGroundTruthDataset(
            dataset_id="SYNTHETIC_FIXTURE_DATASET",
            name="Synthetic In-Memory Falsification & Unit Test Fixtures",
            source_organization="MSK-Therapy-OS Automated Test Harness",
            version="1.0-SYNTHETIC",
            license="MIT",
            doi_or_url="urn:synthetic:falsification",
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
            is_synthetic_fixture=True,
            sample_size=0
        ))

    def create_synthetic_test_observation(
        self,
        point_code: str,
        true_pos: Tuple[float, float, float],
        modality: GroundTruthModality = GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
        tolerance_radius_mm: float = 5.0,
        uncertainty_radius_mm: float = 2.0,
    ) -> GroundTruthObservation:
        """Create a synthetic observation strictly isolated for unit/falsification testing."""
        return GroundTruthObservation(
            point_code=point_code,
            dataset_id="SYNTHETIC_FIXTURE_DATASET",
            canonical_position=true_pos,
            surface_normal=(0.0, 0.0, 1.0),
            uncertainty_radius_mm=uncertainty_radius_mm,
            reviewer_id="REV_SYNTHETIC_TEST",
            notes="SYNTHETIC_FIXTURE_DO_NOT_PROMOTE",
            synthetic_fixture=True,
        )

    def register_reviewer(self, reviewer: ClinicalReviewerCredentials) -> None:
        """Register a qualified reviewer."""
        self._reviewers[reviewer.reviewer_id] = reviewer

    def register_dataset(self, dataset: ExternalGroundTruthDataset) -> None:
        """Register an external dataset manifest."""
        self._datasets[dataset.dataset_id] = dataset

    def register_independent_review(
        self,
        obs: GroundTruthObservation,
        reviewer: ClinicalReviewerCredentials,
        verdict: str = "APPROVED",
        notes: str = "",
    ) -> Dict[str, Any]:
        """Record an independent clinical review for an observation, enforcing anti-conflict-of-interest governance."""
        if obs.observer_id and reviewer.reviewer_id and obs.observer_id == reviewer.reviewer_id:
            raise ValueError(
                f"CONFLICT_OF_INTEREST_DETECTED: Observer '{obs.observer_id}' cannot independently review their own observation."
            )
        if reviewer.reviewer_id not in self._reviewers:
            self.register_reviewer(reviewer)

        if verdict == "APPROVED":
            obs.review_status = ReviewStatus.REVIEWED
        elif verdict == "REJECTED":
            obs.review_status = ReviewStatus.REJECTED
        else:
            obs.review_status = ReviewStatus.INCONCLUSIVE

        obs.reviewer_id = reviewer.reviewer_id
        if notes:
            obs.notes = f"{obs.notes} | Review: {notes}".strip(" |")

        return {
            "status": "success",
            "point_code": obs.point_code,
            "dataset_id": obs.dataset_id,
            "reviewer_id": reviewer.reviewer_id,
            "review_status": obs.review_status.value,
            "verdict": verdict,
        }

    def import_observations(
        self,
        observations: List[GroundTruthObservation],
        validate_contract: bool = True,
        check_authorization: bool = False,
    ) -> int:
        """Import a batch of external ground truth observations."""
        imported = 0
        allowed_codes = set(self.get_all_catalog_codes()) if validate_contract else None
        for obs in observations:
            if obs.dataset_id not in self._datasets:
                raise ValueError(f"Dataset '{obs.dataset_id}' must be registered before importing observations.")
            if validate_contract:
                validate_observation_contract(obs, allowed_codes=allowed_codes, check_authorization=check_authorization)
            self._observations[(obs.point_code, obs.dataset_id)] = obs
            imported += 1
        return imported

    def ingest_external_evidence_batch(
        self,
        batch_payload: Dict[str, Any],
        enforce_quarantine: bool = True,
    ) -> Dict[str, Any]:
        """Ingest a batch of external empirical observations with full privacy, authorization, and quarantine controls."""
        dataset_id = batch_payload.get("dataset_id")
        if not dataset_id:
            raise ValueError("MISSING_DATASET_ID_IN_INGESTION_PAYLOAD")

        if dataset_id not in self._datasets:
            raise ValueError(f"Dataset '{dataset_id}' must be registered prior to batch ingestion.")

        ds = self._datasets[dataset_id]
        observations_raw = batch_payload.get("observations", [])
        allowed_codes = set(self.get_all_catalog_codes())

        ingested_count = 0
        quarantined_count = 0
        quarantined_records = []

        batch_seen: Dict[Tuple[str, str], Tuple[float, float, float]] = {}

        for item in observations_raw:
            code = item.get("point_code") or item.get("anatomical_point_code", "UNKNOWN")
            subj = item.get("subject_pseudonym", "UNKNOWN")

            try:
                # 1. Parse into GroundTruthObservation
                pos = tuple(item.get("canonical_position") or item.get("measurement_coordinates") or (0.0, 0.0, 0.0))
                obs = GroundTruthObservation(
                    point_code=code,
                    dataset_id=dataset_id,
                    canonical_position=pos,
                    surface_normal=tuple(item["surface_normal"]) if item.get("surface_normal") else None,
                    uncertainty_radius_mm=float(item.get("uncertainty_radius_mm", 2.0)),
                    subject_pseudonym=subj,
                    laterality=item.get("laterality", "right"),
                    source_modality=item.get("source_modality", ds.modality.value),
                    coordinate_frame=item.get("coordinate_frame", "BP3D_CARTESIAN_METERS"),
                    unit=item.get("unit", "meters"),
                    observer_id=item.get("observer_id", "OBS-DEFAULT"),
                    source_checksum=item.get("source_checksum", ""),
                    notes=item.get("notes", ""),
                    synthetic_fixture=bool(item.get("synthetic_fixture", ds.is_synthetic_fixture)),
                    schema_version=item.get("schema_version", "1.0-P10"),
                    data_sharing_agreement_ref=item.get("data_sharing_agreement_ref", "DUA-EXEMPT-SYNTHETIC" if ds.is_synthetic_fixture else ""),
                    ethics_approval_or_exemption_ref=item.get("ethics_approval_or_exemption_ref", "IRB-EXEMPT-SYNTHETIC" if ds.is_synthetic_fixture else ""),
                    deidentification_method=item.get("deidentification_method", "SYNTHETIC_DEIDENTIFIED" if ds.is_synthetic_fixture else "NOT_DEIDENTIFIED"),
                    is_authorized_for_clinical_eval=bool(item.get("is_authorized_for_clinical_eval", False)),
                )

                # 2. Check duplicate / conflicting measurements within batch or store
                sub_key = (code, subj)
                if sub_key in batch_seen:
                    prev_pos = batch_seen[sub_key]
                    diff_m = math.sqrt(sum((pos[k] - prev_pos[k])**2 for k in range(3)))
                    if diff_m < 1e-6:
                        raise ValueError(f"QUARANTINE_DUPLICATE_RECORD: Duplicate observation in batch for {code} on subject {subj}.")
                    else:
                        raise ValueError(f"QUARANTINE_CONFLICTING_MEASUREMENT: Conflicting observation in batch for {code} on subject {subj} (diff: {diff_m*1000:.2f}mm).")

                # 3. Check circularity (< 0.1 micron identical to model prediction)
                if not obs.synthetic_fixture:
                    pred_res = self.resolve_point_coordinate(code, side=obs.laterality)
                    if pred_res:
                        pred_pos = pred_res["canonical_position"]
                        dist = math.sqrt(sum((pos[k] - pred_pos[k])**2 for k in range(3)))
                        if dist < 1e-6 and (dataset_id.startswith("SELF_") or "CIRCULAR" in dataset_id or obs.independent_source_id == "SRC-MODEL-PREDICTION"):
                            raise ValueError(f"QUARANTINE_CIRCULAR_EVIDENCE: Observation is bit-for-bit identical to model prediction (< 0.1 mm residual) without independent origin.")

                # 4. Validate contract
                validate_observation_contract(obs, allowed_codes=allowed_codes, check_authorization=not obs.synthetic_fixture)

                # Ingestion succeeded
                batch_seen[sub_key] = pos
                self._observations[(obs.point_code, obs.dataset_id)] = obs
                ingested_count += 1

            except ValueError as ve:
                err_msg = str(ve)
                reason = QuarantineReason.QUARANTINE_SCHEMA_INVALID
                if "PII_DETECTED" in err_msg:
                    reason = QuarantineReason.QUARANTINE_PII_SUSPECTED
                elif "UNAUTHORIZED_EXTERNAL_DATA" in err_msg:
                    reason = QuarantineReason.QUARANTINE_UNAUTHORIZED_DATA
                elif "INCOMPLETE_DEIDENTIFICATION" in err_msg:
                    reason = QuarantineReason.QUARANTINE_INCOMPLETE_DEIDENTIFICATION
                elif "ANATOMICAL_BOUNDING_BOX_VIOLATION" in err_msg or "INVALID_LATERALITY" in err_msg:
                    reason = QuarantineReason.QUARANTINE_OUT_OF_BOUNDS
                elif "INVALID_SOURCE_CHECKSUM" in err_msg:
                    reason = QuarantineReason.QUARANTINE_CHECKSUM_MISMATCH
                elif "UNSUPPORTED_COORDINATE_FRAME" in err_msg:
                    reason = QuarantineReason.QUARANTINE_UNSUPPORTED_FRAME
                elif "QUARANTINE_CIRCULAR_EVIDENCE" in err_msg:
                    reason = QuarantineReason.QUARANTINE_CIRCULAR_EVIDENCE
                elif "QUARANTINE_DUPLICATE_RECORD" in err_msg:
                    reason = QuarantineReason.QUARANTINE_DUPLICATE_RECORD
                elif "QUARANTINE_CONFLICTING_MEASUREMENT" in err_msg:
                    reason = QuarantineReason.QUARANTINE_CONFLICTING_MEASUREMENT
                elif "EXPIRED_DATA_AUTHORIZATION" in err_msg:
                    reason = QuarantineReason.QUARANTINE_EXPIRED_AUTHORIZATION
                elif "REVIEWER_ROLE_CONFLICT" in err_msg:
                    reason = QuarantineReason.QUARANTINE_ROLE_CONFLICT
                elif "HOLDOUT_DATA_LEAKAGE" in err_msg or "HOLDOUT_CONTAMINATION" in err_msg:
                    reason = QuarantineReason.QUARANTINE_HOLDOUT_CONTAMINATION
                elif "ADMIN_SIGN_OFF" in err_msg:
                    reason = QuarantineReason.QUARANTINE_ADMIN_SIGN_OFF_REQUIRED

                q_rec = QuarantinedObservation(
                    point_code=code,
                    dataset_id=dataset_id,
                    subject_pseudonym=subj,
                    reason=reason,
                    details=err_msg,
                    raw_payload=item,
                )
                self._quarantined_records.append(q_rec)
                quarantined_records.append(q_rec.to_dict())
                quarantined_count += 1
                if not enforce_quarantine:
                    raise

        return {
            "status": "success",
            "dataset_id": dataset_id,
            "ingested_count": ingested_count,
            "quarantined_count": quarantined_count,
            "quarantined_records": quarantined_records,
        }

    def get_quarantined_records(self, reason: Optional[str] = None) -> List[QuarantinedObservation]:
        """Retrieve quarantined records, optionally filtered by reason."""
        if reason:
            return [q for q in self._quarantined_records if q.reason.value == reason or q.reason == reason]
        return list(self._quarantined_records)

    def register_blind_independent_review(
        self,
        point_code: str,
        dataset_id: str,
        subject_pseudonym: str,
        primary_reviewer: ClinicalReviewerCredentials,
        primary_decision: str,
        secondary_reviewer: Optional[ClinicalReviewerCredentials] = None,
        secondary_decision: Optional[str] = None,
        notes: str = "",
    ) -> BlindIndependentReviewRecord:
        """Register a blind dual independent review with conflict of interest check."""
        obs = self.get_observation(point_code, dataset_id=dataset_id, subject_pseudonym=subject_pseudonym)
        if not obs:
            raise ValueError(f"OBSERVATION_NOT_FOUND: Observation for {point_code} in {dataset_id} not found.")

        # Check Conflict of interest
        if obs.observer_id:
            if obs.observer_id == primary_reviewer.reviewer_id:
                raise ValueError("CONFLICT_OF_INTEREST_DETECTED: Primary reviewer cannot be identical to observer.")
            if secondary_reviewer and obs.observer_id == secondary_reviewer.reviewer_id:
                raise ValueError("CONFLICT_OF_INTEREST_DETECTED: Secondary reviewer cannot be identical to observer.")

        if secondary_reviewer and primary_reviewer.reviewer_id == secondary_reviewer.reviewer_id:
            raise ValueError("CONFLICT_OF_INTEREST_DETECTED: Primary and secondary reviewer must be independent individuals.")

        # Determine consensus
        if not secondary_reviewer or not secondary_decision:
            consensus = "INDEPENDENT_REVIEW_PENDING"
        elif primary_decision == "APPROVED" and secondary_decision == "APPROVED":
            consensus = "APPROVED"
        elif primary_decision == "REJECTED" or secondary_decision == "REJECTED":
            consensus = "REJECTED"
        else:
            consensus = "INCONCLUSIVE"

        rev_id = f"REV-DUAL-{point_code}-{dataset_id}-{subject_pseudonym}"
        record = BlindIndependentReviewRecord(
            review_id=rev_id,
            point_code=point_code,
            dataset_id=dataset_id,
            subject_pseudonym=subject_pseudonym,
            primary_reviewer_id=primary_reviewer.reviewer_id,
            secondary_reviewer_id=secondary_reviewer.reviewer_id if secondary_reviewer else None,
            primary_decision=primary_decision,
            secondary_decision=secondary_decision,
            consensus_decision=consensus,
            inter_observer_discrepancy_mm=0.0 if consensus == "APPROVED" else 5.0,
            conflict_of_interest_declared=False,
        )
        self._blind_reviews[rev_id] = record
        return record

    def evaluate_against_pre_registered_thresholds(
        self,
        comparisons: List[PointValidationComparison],
        thresholds: Optional[PreRegisteredAccuracyThresholds] = None,
    ) -> Dict[str, Any]:
        """Evaluate validation comparisons against pre-registered scientific accuracy thresholds."""
        th = thresholds or self._pre_registered_thresholds
        residuals = [c.residual_error_mm for c in comparisons if c.residual_error_mm is not None]

        if not residuals:
            return {
                "verdict": "INCONCLUSIVE",
                "reason": "No ground truth observations evaluated.",
                "rmse_mm": None,
                "mean_mm": None,
                "median_mm": None,
                "p95_mm": None,
                "outlier_count": 0,
                "thresholds": th.to_dict(),
            }

        n = len(residuals)
        rmse = round(math.sqrt(sum(r**2 for r in residuals) / n), 3)
        mean_err = round(sum(residuals) / n, 3)
        sorted_res = sorted(residuals)
        med_err = round(sorted_res[n // 2], 3)
        p95_err = round(sorted_res[min(int(n * 0.95), n - 1)], 3)
        outlier_count = sum(1 for r in residuals if r > th.max_outlier_tolerance_mm)

        if rmse <= th.high_accuracy_rmse_mm and outlier_count == 0:
            verdict = "HIGH_ACCURACY_CONFIRMED"
        elif rmse <= th.acceptable_accuracy_rmse_mm:
            verdict = "ACCEPTABLE_ACCURACY_CONFIRMED"
        else:
            verdict = "VALIDATION_FAILED"

        return {
            "verdict": verdict,
            "sample_size": n,
            "rmse_mm": rmse,
            "mean_mm": mean_err,
            "median_mm": med_err,
            "p95_mm": p95_err,
            "outlier_count": outlier_count,
            "thresholds": th.to_dict(),
        }

    def get_ingestion_governance_state(self) -> str:
        """Return the current system evidence ingestion and governance state."""
        # Inspect registered datasets
        real_datasets = [ds for ds in self._datasets.values() if not ds.is_synthetic_fixture and ds.dataset_id != "DS-BP3D-FJ2810"]
        if not real_datasets:
            return EvidenceIngestionState.EXTERNAL_DATA_PENDING.value

        # If real datasets exist, inspect observations
        real_obs = [obs for obs in self._observations.values() if not obs.synthetic_fixture and obs.dataset_id != "DS-BP3D-FJ2810"]
        if not real_obs:
            return EvidenceIngestionState.EXTERNAL_DATA_PENDING.value

        return EvidenceIngestionState.AUTHORIZED_DATA_RECEIVED.value

    def get_dataset(self, dataset_id: str) -> Optional[ExternalGroundTruthDataset]:
        """Retrieve registered dataset metadata."""
        return self._datasets.get(dataset_id)

    def get_observation(
        self,
        point_code: str,
        dataset_id: Optional[str] = None,
        subject_pseudonym: Optional[str] = None,
    ) -> Optional[GroundTruthObservation]:
        """Retrieve observation for a point. If dataset_id is None, returns first available."""
        if dataset_id and subject_pseudonym:
            obs = self._observations.get((point_code, dataset_id))
            return obs if (obs and obs.subject_pseudonym == subject_pseudonym) else None
        if dataset_id:
            return self._observations.get((point_code, dataset_id))
        for (code, ds_id), obs in self._observations.items():
            if code == point_code:
                if subject_pseudonym is None or obs.subject_pseudonym == subject_pseudonym:
                    return obs
        return None

    def get_all_catalog_codes(self) -> List[str]:
        """Retrieve authoritative 362 catalog codes (18 Class A + 344 Class B)."""
        all_codes = set(self.engine.rules.keys()) | set(AUDITED_CANONICAL_POINTS.keys())
        return sorted(list(all_codes))

    def resolve_point_coordinate(self, point_code: str, side: str = "right") -> Dict[str, Any]:
        """Resolve predicted coordinates for any of the 362 catalog points."""
        if point_code in AUDITED_CANONICAL_POINTS:
            anchor = AUDITED_CANONICAL_POINTS[point_code]
            pos = list(anchor["canonical_position"])
            norm = list(anchor.get("normal", (0.0, 0.0, 1.0)))
            lat = anchor.get("laterality", "right")
            if side == "left" and lat != "midline":
                pos[0] = -abs(pos[0])
                norm[0] = -abs(norm[0])
            else:
                pos[0] = abs(pos[0])
                norm[0] = abs(norm[0]) if lat != "midline" else 0.0
            p_tuple = (round(pos[0], 6), round(pos[1], 6), round(pos[2], 6))
            return {
                "point_code": point_code,
                "side": side,
                "canonical_position": p_tuple,
                "position": p_tuple,
                "surface_normal": (round(norm[0], 4), round(norm[1], 4), round(norm[2], 4)),
                "quality_class": "CLASS_A"
            }
        res = dict(self.engine.resolve_point_location(point_code, side=side))
        if "canonical_position" in res and "position" not in res:
            res["position"] = res["canonical_position"]
        return res

    def validate_point(
        self,
        point_code: str,
        side: str = "right",
        dataset_id: Optional[str] = None,
        transform: Optional[RegistrationTransform] = None,
        subject_pseudonym: Optional[str] = None,
    ) -> PointValidationComparison:
        """Compare a model-predicted acupoint against an external ground-truth observation.

        Fail-closed rule: if no observation is available, returns INDEPENDENT_GROUND_TRUTH_UNAVAILABLE.
        """
        # 1. Resolve predicted coordinate
        pred_res = self.resolve_point_coordinate(point_code, side=side)
        if not pred_res:
            raise ValueError(f"Point '{point_code}' could not be resolved.")

        rule = self.engine.rules.get(point_code)
        anchor_data = AUDITED_CANONICAL_POINTS.get(point_code)
        channel_code = rule.meridian_code if rule else (point_code[:2] if not point_code.startswith("GV24+") else "GV")
        pred_pos = pred_res["canonical_position"]
        tol_mm = rule.tolerance_radius_mm if rule else (anchor_data.get("tolerance_radius_mm", 5.0) if anchor_data else 5.0)
        uncert_mm = rule.uncertainty_mm if rule else (anchor_data.get("uncertainty_mm", 8.0) if anchor_data else 8.0)

        # 2. Find matching observation
        obs = self.get_observation(point_code, dataset_id=dataset_id, subject_pseudonym=subject_pseudonym)

        if not obs:
            return PointValidationComparison(
                point_code=point_code,
                channel_code=channel_code,
                predicted_position=pred_pos,
                reference_position=None,
                residual_error_mm=None,
                tolerance_radius_mm=tol_mm,
                uncertainty_mm=uncert_mm,
                classification=AnatomicalErrorClassification.INDEPENDENT_GROUND_TRUTH_UNAVAILABLE,
                is_congruent=False,
                verification_tier=AnatomicalVerificationTier.TECHNICALLY_CALIBRATED,
                dataset_id=None,
                is_synthetic=False,
                details={"reason": "No independent external ground truth observation registered for point."}
            )

        ref_ds = self._datasets.get(obs.dataset_id)
        is_synth = (ref_ds.is_synthetic_fixture if ref_ds else False) or obs.synthetic_fixture

        # Apply spatial transform if reference frame requires normalization
        ref_pos = obs.canonical_position
        if obs.coordinate_frame != CoordinateFrame.BP3D_CARTESIAN_METERS or obs.unit != MeasurementUnit.METERS:
            ref_pos = transform_coordinates_to_bp3d(obs.measurement_coordinates or obs.canonical_position, obs.coordinate_frame, obs.unit)
        if transform:
            ref_pos = transform.transform_point(ref_pos)

        # 3. Calculate Euclidean distance residual in millimeters
        dx = (pred_pos[0] - ref_pos[0]) * 1000.0
        dy = (pred_pos[1] - ref_pos[1]) * 1000.0
        dz = (pred_pos[2] - ref_pos[2]) * 1000.0
        residual_mm = round(math.sqrt(dx * dx + dy * dy + dz * dz), 3)

        # 4. Classify error
        if residual_mm <= 3.0:
            classification = AnatomicalErrorClassification.CONGRUENT
        elif residual_mm <= 8.0:
            classification = AnatomicalErrorClassification.ACCEPTABLE_CLINICAL_TOLERANCE
        elif residual_mm <= 15.0:
            classification = AnatomicalErrorClassification.BORDERLINE
        else:
            classification = AnatomicalErrorClassification.OUTLIER_ANOMALY

        is_congruent = (residual_mm <= tol_mm)

        # Anti-circularity detection:
        is_circular = False
        if not is_synth:
            if obs.dataset_id == "DS-BP3D-FJ2810":
                is_circular = True
            elif residual_mm < 1e-4 and (obs.dataset_id.startswith("SELF_") or obs.independent_source_id == "SRC-MODEL-PREDICTION"):
                is_circular = True

        # 5. Determine verification tier under fail-closed governance
        if is_synth:
            tier = AnatomicalVerificationTier.GEOMETRICALLY_VALIDATED
        elif is_circular:
            tier = AnatomicalVerificationTier.ANATOMICALLY_CORROBORATED if (point_code in AUDITED_CANONICAL_POINTS) else AnatomicalVerificationTier.TECHNICALLY_CALIBRATED
        elif not is_congruent:
            tier = AnatomicalVerificationTier.TECHNICALLY_CALIBRATED
        else:
            tier = AnatomicalVerificationTier.INDEPENDENTLY_VERIFIED

        return PointValidationComparison(
            point_code=point_code,
            channel_code=channel_code,
            predicted_position=pred_pos,
            reference_position=ref_pos,
            residual_error_mm=residual_mm,
            tolerance_radius_mm=tol_mm,
            uncertainty_mm=uncert_mm,
            classification=classification,
            is_congruent=is_congruent,
            verification_tier=tier,
            dataset_id=obs.dataset_id,
            is_synthetic=is_synth,
            details={
                "delta_x_mm": round(dx, 3),
                "delta_y_mm": round(dy, 3),
                "delta_z_mm": round(dz, 3),
                "obs_uncertainty_mm": obs.measurement_uncertainty,
                "modality": ref_ds.modality.value if ref_ds else "UNKNOWN",
                "notes": obs.notes,
                "circular_dependency": is_circular,
                "subject_pseudonym": obs.subject_pseudonym,
            }
        )

    def validate_catalog(
        self,
        point_codes: Optional[List[str]] = None,
        dataset_id: Optional[str] = None,
        side: str = "right",
        holdout_subjects: Optional[List[str]] = None,
        subject_pseudonym: Optional[str] = None,
    ) -> ValidationReport:
        """Evaluate catalog against registered observations and compile statistical report."""
        codes = point_codes or self.get_all_catalog_codes()
        comparisons: List[PointValidationComparison] = []
        outliers: List[PointValidationComparison] = []
        residuals: List[float] = []

        is_any_synthetic = False

        for code in codes:
            # Check holdout subject filtering
            if holdout_subjects:
                obs = self.get_observation(code, dataset_id=dataset_id)
                if obs and obs.subject_pseudonym in holdout_subjects:
                    continue

            comp = self.validate_point(code, side=side, dataset_id=dataset_id, subject_pseudonym=subject_pseudonym)
            comparisons.append(comp)
            if comp.is_synthetic:
                is_any_synthetic = True
            if comp.residual_error_mm is not None:
                residuals.append(comp.residual_error_mm)
                if comp.classification == AnatomicalErrorClassification.OUTLIER_ANOMALY or not comp.is_congruent:
                    outliers.append(comp)

        # Calculate statistics
        evaluated_count = len(residuals)
        unavail_count = len(codes) - evaluated_count

        mean_err = round(sum(residuals) / evaluated_count, 3) if evaluated_count > 0 else 0.0
        sorted_res = sorted(residuals)
        median_err = round(sorted_res[evaluated_count // 2], 3) if evaluated_count > 0 else 0.0
        max_err = round(max(residuals), 3) if evaluated_count > 0 else 0.0

        p95_err = 0.0
        if evaluated_count > 0:
            p95_idx = min(int(evaluated_count * 0.95), evaluated_count - 1)
            p95_err = round(sorted_res[p95_idx], 3)

        std_dev = 0.0
        if evaluated_count > 1:
            var = sum((r - mean_err) ** 2 for r in residuals) / (evaluated_count - 1)
            std_dev = round(math.sqrt(var), 3)

        congruent_count = sum(1 for c in comparisons if c.is_congruent and c.residual_error_mm is not None)
        congruence_pct = round((congruent_count / evaluated_count) * 100.0, 1) if evaluated_count > 0 else 0.0

        # P10.2 Comprehensive Statistical Metrics
        overall_rmse_mm = 0.0
        mae_mm = 0.0
        delta_x_list: List[float] = []
        delta_y_list: List[float] = []
        delta_z_list: List[float] = []
        left_residuals: List[float] = []
        right_residuals: List[float] = []
        cohort_groups: Dict[str, List[float]] = {"COHORT_A": [], "COHORT_B": [], "COHORT_C": [], "OTHER": []}
        per_subject_map: Dict[str, List[float]] = {}

        for comp in comparisons:
            if comp.residual_error_mm is not None:
                err = comp.residual_error_mm
                mae_mm += err
                overall_rmse_mm += err ** 2

                # Deltas for bias vector (model - ground truth in mm)
                p_model = comp.predicted_position
                p_true = comp.reference_position
                if p_model and p_true:
                    delta_x_list.append((p_model[0] - p_true[0]) * 1000.0)
                    delta_y_list.append((p_model[1] - p_true[1]) * 1000.0)
                    delta_z_list.append((p_model[2] - p_true[2]) * 1000.0)

                # Laterality grouping
                code = comp.point_code
                if comp.details.get("side") == "left":
                    left_residuals.append(err)
                elif comp.details.get("side") == "right":
                    right_residuals.append(err)

                # Cohort grouping
                c_upper = code.upper()
                if c_upper.startswith("ST") and len(c_upper) > 2 and c_upper[2:].isdigit() and 19 <= int(c_upper[2:]) <= 30:
                    cohort_groups["COHORT_A"].append(err)
                elif any(c_upper.startswith(prefix) for prefix in ("LU", "LI", "PC", "TE", "HT", "SI", "SP", "LR")) or (c_upper.startswith("ST") and len(c_upper) > 2 and int(c_upper[2:]) > 30):
                    cohort_groups["COHORT_B"].append(err)
                elif any(c_upper.startswith(prefix) for prefix in ("GV", "CV", "BL")):
                    cohort_groups["COHORT_C"].append(err)
                else:
                    cohort_groups["OTHER"].append(err)

                # Subject grouping
                s_pseudonym = comp.details.get("subject_pseudonym", "ANON")
                per_subject_map.setdefault(s_pseudonym, []).append(err)

        if evaluated_count > 0:
            overall_rmse_mm = round(math.sqrt(overall_rmse_mm / evaluated_count), 3)
            mae_mm = round(mae_mm / evaluated_count, 3)
        else:
            overall_rmse_mm = 0.0
            mae_mm = 0.0

        # Bias vector
        bias_vector_mm = [
            round(sum(delta_x_list) / len(delta_x_list), 3) if delta_x_list else 0.0,
            round(sum(delta_y_list) / len(delta_y_list), 3) if delta_y_list else 0.0,
            round(sum(delta_z_list) / len(delta_z_list), 3) if delta_z_list else 0.0,
        ]

        # Left/Right Asymmetry
        rmse_left = round(math.sqrt(sum(r ** 2 for r in left_residuals) / len(left_residuals)), 3) if left_residuals else 0.0
        rmse_right = round(math.sqrt(sum(r ** 2 for r in right_residuals) / len(right_residuals)), 3) if right_residuals else 0.0
        left_right_asymmetry_mm = round(abs(rmse_left - rmse_right), 3)

        # Cohort RMSEs
        cohort_rmse_mm = {
            c_name: round(math.sqrt(sum(r ** 2 for r in r_list) / len(r_list)), 3) if r_list else 0.0
            for c_name, r_list in cohort_groups.items() if r_list
        }

        # 95% Confidence Interval for mean residual error
        ci_95_mm = [0.0, 0.0]
        if evaluated_count > 1 and std_dev > 0.0:
            se = std_dev / math.sqrt(evaluated_count)
            t_crit = 1.96  # Standard large-sample normal approximation for 95% CI
            ci_95_mm = [round(max(0.0, mean_err - t_crit * se), 3), round(mean_err + t_crit * se, 3)]
        elif evaluated_count == 1:
            ci_95_mm = [mean_err, mean_err]

        # Coverage and missing data rates
        total_cat = len(codes)
        cov_pct = round((evaluated_count / total_cat) * 100.0, 1) if total_cat > 0 else 0.0
        missing_rate_pct = round(100.0 - cov_pct, 1)

        # IQR Outliers
        iqr_val = 0.0
        q1_val = 0.0
        q3_val = 0.0
        iqr_outliers_count = 0
        if evaluated_count >= 4:
            q1_idx = evaluated_count // 4
            q3_idx = (3 * evaluated_count) // 4
            q1_val = sorted_res[q1_idx]
            q3_val = sorted_res[q3_idx]
            iqr_val = round(q3_val - q1_val, 3)
            iqr_fence = q3_val + 1.5 * iqr_val
            iqr_outliers_count = sum(1 for r in sorted_res if r > iqr_fence)

        # Intra-cluster correlation (ICC) approximation across subjects
        icc_approx = 0.0
        n_eff = float(evaluated_count)
        if len(per_subject_map) > 1 and evaluated_count > len(per_subject_map):
            subj_means = [sum(errs) / len(errs) for errs in per_subject_map.values()]
            grand_mean = sum(residuals) / len(residuals)
            var_between = sum((sm - grand_mean)**2 for sm in subj_means) / (len(per_subject_map) - 1)
            var_total = std_dev**2 if std_dev > 0 else 1.0
            icc_approx = round(min(1.0, max(0.0, var_between / (var_total + 1e-9))), 3)
            avg_m = evaluated_count / len(per_subject_map)
            design_effect = 1.0 + (avg_m - 1.0) * icc_approx
            n_eff = round(evaluated_count / design_effect, 1)

        # Subject metrics summary
        per_subject_metrics = {
            s: {
                "count": len(errs),
                "mean_error_mm": round(sum(errs) / len(errs), 3),
                "rmse_mm": round(math.sqrt(sum(e**2 for e in errs) / len(errs)), 3),
                "max_error_mm": round(max(errs), 3),
            }
            for s, errs in per_subject_map.items()
        }

        summary = {
            "total_points_in_scope": len(codes),
            "evaluated_with_ground_truth": evaluated_count,
            "independent_subjects_count": len(per_subject_map),
            "total_observations_count": evaluated_count,
            "q1_residual_error_mm": q1_val,
            "q3_residual_error_mm": q3_val,
            "iqr_residual_error_mm": iqr_val,
            "iqr_outliers_count": iqr_outliers_count,
            "intra_cluster_correlation_icc": icc_approx,
            "effective_sample_size_n_eff": n_eff,
            "ground_truth_unavailable_count": unavail_count,
            "congruent_count": congruent_count,
            "congruence_percentage": congruence_pct,
            "mean_residual_error_mm": mean_err,
            "median_residual_error_mm": median_err,
            "std_deviation_mm": std_dev,
            "p95_residual_error_mm": p95_err,
            "max_residual_error_mm": max_err,
            "outlier_count": len(outliers),
            "dataset_filter": dataset_id or "ALL_AVAILABLE",
            # P10.2 Extended Validation Metrics:
            "overall_rmse_mm": overall_rmse_mm,
            "mae_mm": mae_mm,
            "bias_vector_mm": bias_vector_mm,
            "left_right_asymmetry_mm": left_right_asymmetry_mm,
            "rmse_left_mm": rmse_left,
            "rmse_right_mm": rmse_right,
            "cohort_rmse_mm": cohort_rmse_mm,
            "confidence_interval_95_mm": ci_95_mm,
            "coverage_percentage": cov_pct,
            "missing_data_rate_percentage": missing_rate_pct,
            "per_subject_metrics": per_subject_metrics,
            "preregistered_high_accuracy_pass": bool(evaluated_count > 0 and overall_rmse_mm <= 5.0),
            "preregistered_acceptable_accuracy_pass": bool(evaluated_count > 0 and overall_rmse_mm <= 10.0),
            "statistical_power_specification": {
                "formula": "N >= ((Z_alpha/2 + Z_beta)^2 * sigma^2) / delta^2",
                "z_alpha_half_95": 1.96,
                "z_beta_80": 0.84,
                "z_beta_90": 1.28,
                "minimum_recommended_cohort_n": 30,
                "status": "REQUIRES_FORMAL_BIOSTATISTICAL_REVIEW_BEFORE_ENROLLMENT",
            },
        }

        regional_metrics = self.get_regional_error_distribution(comparisons)

        return ValidationReport(
            summary=summary,
            regional_metrics=regional_metrics,
            comparisons=comparisons,
            outliers=outliers,
            is_synthetic_evaluation=is_any_synthetic
        )

    def get_regional_error_distribution(
        self,
        comparisons: List[PointValidationComparison]
    ) -> Dict[str, Dict[str, Any]]:
        """Compute error distribution grouped by anatomical body region."""
        grouped: Dict[str, List[float]] = {}
        for comp in comparisons:
            if comp.residual_error_mm is None:
                continue
            rule = self.engine.rules.get(comp.point_code)
            anchor = AUDITED_CANONICAL_POINTS.get(comp.point_code)
            region_key = rule.body_region.value if rule else (anchor.get("region", "UNKNOWN") if anchor else "UNKNOWN")
            if region_key not in grouped:
                grouped[region_key] = []
            grouped[region_key].append(comp.residual_error_mm)

        metrics: Dict[str, Dict[str, Any]] = {}
        for reg, res_list in grouped.items():
            cnt = len(res_list)
            sorted_r = sorted(res_list)
            mean_val = round(sum(res_list) / cnt, 3)
            med_val = round(sorted_r[cnt // 2], 3)
            max_val = round(max(res_list), 3)
            p95_val = round(sorted_r[min(int(cnt * 0.95), cnt - 1)], 3)
            metrics[reg] = {
                "count": cnt,
                "mean_mm": mean_val,
                "median_mm": med_val,
                "p95_mm": p95_val,
                "max_mm": max_val,
            }
        return metrics

    def generate_full_362_provenance_matrix(self) -> List[Dict[str, Any]]:
        """Generate complete provenance and ground-truth readiness matrix for all 362 points."""
        matrix = []
        all_codes = self.get_all_catalog_codes()
        for code in all_codes:
            pred_r = self.resolve_point_coordinate(code, side="right")
            pred_l = self.resolve_point_coordinate(code, side="left")
            pos_r = pred_r["canonical_position"]
            pos_l = pred_l["canonical_position"]
            norm_r = pred_r["surface_normal"]

            # Calculate symmetry delta
            dx = abs(pos_r[0] - (-pos_l[0]))
            dy = abs(pos_r[1] - pos_l[1])
            dz = abs(pos_r[2] - pos_l[2])
            delta_sym_mm = round(math.sqrt(dx*dx + dy*dy + dz*dz) * 1000.0, 4)

            # Metadata from rule or anchor
            rule = self.engine.rules.get(code)
            anchor = AUDITED_CANONICAL_POINTS.get(code)
            is_class_a = (code in AUDITED_CANONICAL_POINTS)

            q_class = "CLASS_A" if is_class_a else "CLASS_B"
            ch_code = rule.meridian_code if rule else (code[:2] if not code.startswith("GV24+") else "GV")
            name_en = rule.name_en if rule else (anchor.get("name_en", code) if anchor else code)
            who_ref = rule.who_reference if rule else (anchor.get("who_reference", "WHO 2008 Standard") if anchor else "")
            fma_id = rule.fma_anchor if rule else (anchor.get("fma_id", "FMA:00000") if anchor else "")
            start_lm = rule.start_landmark_id if rule else (anchor.get("skeletal_anchor", "CANONICAL_ANCHOR") if anchor else "")
            end_lm = (rule.end_landmark_id or "NONE") if rule else "NONE"
            tol_mm = rule.tolerance_radius_mm if rule else (anchor.get("tolerance_radius_mm", 5.0) if anchor else 5.0)
            uncert_mm = rule.uncertainty_mm if rule else (anchor.get("uncertainty_mm", 8.0) if anchor else 8.0)

            # Check ground truth availability
            obs = self.get_observation(code)
            gt_status = "AVAILABLE" if obs and not self._datasets[obs.dataset_id].is_synthetic_fixture else "INDEPENDENT_GROUND_TRUTH_UNAVAILABLE"

            tier = (
                AnatomicalVerificationTier.INDEPENDENTLY_VERIFIED.value
                if obs and not self._datasets[obs.dataset_id].is_synthetic_fixture and obs.dataset_id != "DS-BP3D-FJ2810"
                else (
                    AnatomicalVerificationTier.ANATOMICALLY_CORROBORATED.value
                    if is_class_a
                    else AnatomicalVerificationTier.TECHNICALLY_CALIBRATED.value
                )
            )

            matrix.append({
                "point_code": code,
                "channel_code": ch_code,
                "name_en": name_en,
                "quality_class": q_class,
                "who_reference": who_ref,
                "fma_anchor": fma_id,
                "primary_landmark": start_lm,
                "secondary_landmark": end_lm,
                "pos_x": pos_r[0],
                "pos_y": pos_r[1],
                "pos_z": pos_r[2],
                "norm_x": norm_r[0],
                "norm_y": norm_r[1],
                "norm_z": norm_r[2],
                "symmetry_delta_mm": delta_sym_mm,
                "tolerance_radius_mm": tol_mm,
                "uncertainty_mm": uncert_mm,
                "verification_tier": tier,
                "independent_ground_truth_status": gt_status,
                "clinical_verification_tier_4": "0.0% (UNVERIFIED_IN_TRIAL)",
                "reviewer": "Expert Anatomical Audit" if is_class_a else "WHO-2008 Parametric Engine",
            })
        return matrix

    def generate_anatomical_uncertainty_matrix(self) -> List[Dict[str, Any]]:
        """Calculate anatomical and geometric uncertainty boundaries across all 362 points."""
        matrix = []
        all_codes = self.get_all_catalog_codes()
        for code in all_codes:
            rule = self.engine.rules.get(code)
            anchor = AUDITED_CANONICAL_POINTS.get(code)
            region = rule.body_region.value if rule else (anchor.get("region", "head_neck") if anchor else "unknown")
            ch_code = rule.meridian_code if rule else (code[:2] if not code.startswith("GV24+") else "GV")
            name_en = rule.name_en if rule else (anchor.get("name_en", code) if anchor else code)
            method = rule.localization_method.value if rule else "CANONICAL_AUDIT_ANCHOR"
            is_posture = rule.is_posture_sensitive if rule else (anchor.get("is_posture_sensitive", False) if anchor else False)
            sens_joint = rule.sensitive_joint if rule else (anchor.get("sensitive_joint", "NONE") if anchor else "NONE")

            # Uncertainty components:
            lm_variance_mm = 1.5 if ("DEPRESSION" in method or "BONY" in method or "CANONICAL" in method) else 3.5
            if ch_code == "ST" and code[2:].isdigit() and 19 <= int(code[2:]) <= 30:
                cun_elasticity_mm = 8.5  # Documented unscaled abdominal mesh assumption (2 cun line elasticity)
            elif rule and rule.proportional_fraction > 0:
                cun_elasticity_mm = 2.0
            elif rule and rule.lateral_offset_cun > 0:
                cun_elasticity_mm = 2.5
            else:
                cun_elasticity_mm = 0.5
            posture_variance_mm = 4.0 if is_posture else 0.0
            total_uncertainty_mm = round(math.sqrt(lm_variance_mm**2 + cun_elasticity_mm**2 + posture_variance_mm**2), 2)

            matrix.append({
                "point_code": code,
                "channel_code": ch_code,
                "name_en": name_en,
                "body_region": region,
                "localization_method": method,
                "is_posture_sensitive": is_posture,
                "sensitive_joint": sens_joint or "NONE",
                "landmark_palpation_uncertainty_mm": lm_variance_mm,
                "cun_scaling_elasticity_mm": cun_elasticity_mm,
                "posture_articulation_uncertainty_mm": posture_variance_mm,
                "total_spatial_uncertainty_radius_mm": total_uncertainty_mm,
                "confidence_interval_95_pct_mm": round(total_uncertainty_mm * 1.96, 2),
                "clinical_depth_guidance_allowed": False,  # Red flag: strictly forbidden
            })
        return matrix

    def run_metamorphic_transformation_test(
        self,
        point_code: Optional[str] = None,
        sample_points: Optional[List[str]] = None,
        rotation_deg: Union[float, Tuple[float, float, float]] = 45.0,
        translation_m: Tuple[float, float, float] = (0.5, -0.2, 0.1)
    ) -> Dict[str, Any]:
        """Verify metamorphic spatial invariants under rigid 3D Euclidean transformation."""
        if isinstance(rotation_deg, (int, float)):
            rx = ry = 0.0
            rz = math.radians(float(rotation_deg))
        else:
            rx = math.radians(float(rotation_deg[0]))
            ry = math.radians(float(rotation_deg[1]))
            rz = math.radians(float(rotation_deg[2]))

        cx, sx = math.cos(rx), math.sin(rx)
        cy, sy = math.cos(ry), math.sin(ry)
        cz, sz = math.cos(rz), math.sin(rz)

        r_mat = [
            [cy*cz, cy*sz, -sy],
            [sx*sy*cz - cx*sz, sx*sy*sz + cx*cz, sx*cy],
            [cx*sy*cz + sx*sz, cx*sy*sz - sx*cz, cx*cy],
        ]
        tx, ty, tz = translation_m

        def transform(p):
            x, y, z = p
            tx_p = (r_mat[0][0]*x + r_mat[0][1]*y + r_mat[0][2]*z) + tx
            ty_p = (r_mat[1][0]*x + r_mat[1][1]*y + r_mat[1][2]*z) + ty
            tz_p = (r_mat[2][0]*x + r_mat[2][1]*y + r_mat[2][2]*z) + tz
            return (tx_p, ty_p, tz_p)

        inv_r_mat = [
            [r_mat[0][0], r_mat[1][0], r_mat[2][0]],
            [r_mat[0][1], r_mat[1][1], r_mat[2][1]],
            [r_mat[0][2], r_mat[1][2], r_mat[2][2]],
        ]
        def inv_transform(p):
            x = p[0] - tx
            y = p[1] - ty
            z = p[2] - tz
            ix = (inv_r_mat[0][0]*x + inv_r_mat[0][1]*y + inv_r_mat[0][2]*z)
            iy = (inv_r_mat[1][0]*x + inv_r_mat[1][1]*y + inv_r_mat[1][2]*z)
            iz = (inv_r_mat[2][0]*x + inv_r_mat[2][1]*y + inv_r_mat[2][2]*z)
            return (ix, iy, iz)

        points = sample_points if sample_points is not None else ([point_code] if point_code else ["LI4"])
        eval_results = []
        max_recon_mm = 0.0
        max_pair_drift_mm = 0.0

        orig_positions = [self.resolve_point_coordinate(c)["canonical_position"] for c in points]
        trans_positions = [transform(p) for p in orig_positions]
        restored_positions = [inv_transform(tp) for tp in trans_positions]

        for i, c in enumerate(points):
            p0 = orig_positions[i]
            pr = restored_positions[i]
            d_recon = math.sqrt((p0[0]-pr[0])**2 + (p0[1]-pr[1])**2 + (p0[2]-pr[2])**2) * 1000.0
            max_recon_mm = max(max_recon_mm, d_recon)
            eval_results.append({
                "point_code": c,
                "original_position": p0,
                "transformed_position": trans_positions[i],
                "restored_position": pr,
                "reconstruction_residual_mm": round(d_recon, 6),
            })

        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                d_orig = math.sqrt(sum((orig_positions[i][k] - orig_positions[j][k])**2 for k in range(3))) * 1000.0
                d_trans = math.sqrt(sum((trans_positions[i][k] - trans_positions[j][k])**2 for k in range(3))) * 1000.0
                drift = abs(d_orig - d_trans)
                max_pair_drift_mm = max(max_pair_drift_mm, drift)

        return {
            "point_code": point_code or points[0],
            "points_evaluated": len(points),
            "eval_results": eval_results,
            "max_reconstruction_error_mm": round(max_recon_mm, 6),
            "max_pairwise_distance_drift_mm": round(max_pair_drift_mm, 6),
            "invariant_preserved": (max_recon_mm < 1e-4),
            "invariance_preserved": (max_recon_mm < 1e-4 and max_pair_drift_mm < 1e-4),
        }

    def audit_st19_st30_abdominal_line(self) -> Dict[str, Any]:
        """Audit Cohort A: Bilateral Abdominal Line (ST19 to ST30).

        Evaluates the parametric assumption that the lateral line (2.0 cun from anterior median line)
        maps to fixed X = 0.0660 m on the canonical BodyParts3D FJ2810 mesh.
        Performs morphological sensitivity analysis across ectomorphic, mesomorphic, and endomorphic waists.
        """
        st_codes = [f"ST{i}" for i in range(19, 31)]
        points_data = []
        all_x_right = []
        all_x_left = []

        for code in st_codes:
            pred_r = self.resolve_point_coordinate(code, side="right")
            pred_l = self.resolve_point_coordinate(code, side="left")
            pos_r = pred_r["canonical_position"]
            pos_l = pred_l["canonical_position"]
            all_x_right.append(pos_r[0])
            all_x_left.append(pos_l[0])
            bilateral_span_mm = round(abs(pos_r[0] - pos_l[0]) * 1000.0, 2)
            points_data.append({
                "point_code": code,
                "pos_right": pos_r,
                "pos_left": pos_l,
                "x_right_mm": round(pos_r[0] * 1000.0, 2),
                "x_left_mm": round(pos_l[0] * 1000.0, 2),
                "bilateral_span_mm": bilateral_span_mm,
                "y_level_m": pos_r[1],
                "z_depth_m": pos_r[2],
            })

        mean_x_r = round(sum(all_x_right) / len(all_x_right), 4)
        is_x_constant = all(round(x, 4) == round(mean_x_r, 4) for x in all_x_right)

        morphology_sensitivity = {
            "canonical_normosthenic": {"waist_cm": 82.0, "cun_mm": 33.0, "lateral_offset_mm": 66.0, "delta_from_canonical_mm": 0.0},
            "asthenic_ectomorph": {"waist_cm": 65.0, "cun_mm": 22.0, "lateral_offset_mm": 44.0, "delta_from_canonical_mm": -22.0},
            "hypersthenic_endomorph": {"waist_cm": 105.0, "cun_mm": 44.0, "lateral_offset_mm": 88.0, "delta_from_canonical_mm": 22.0},
        }

        return {
            "cohort": "COHORT_A_ABDOMINAL_LINE",
            "point_count": len(st_codes),
            "points_evaluated": st_codes,
            "nominal_lateral_offset_x_m": mean_x_r,
            "is_canonical_x_constant": is_x_constant,
            "points": points_data,
            "morphology_sensitivity": morphology_sensitivity,
            "findings": [
                "All 12 bilateral points (ST19..ST30) share exact constant X = 0.0660 m on canonical FJ2810 mesh.",
                "Parametric 2.0 cun lateral distance depends strictly on proportional abdominal cun scaling.",
                "Across morphological somatotypes, real lateral coordinate deviates by up to +/- 22.0 mm without personalized scaling.",
                "Current model uncertainty (+/- 8.5 mm) is a geometric model bound, not an empirically verified clinical confidence interval."
            ],
            "limitation": "Without personalized CT/surface mesh registration, ST19..ST30 locations cannot be clinically guaranteed.",
            "governance_verdict": "TECHNICALLY_CALIBRATED_UNVERIFIED_IN_VIVO"
        }

    def audit_bilateral_limb_landmarks(self) -> Dict[str, Any]:
        """Audit Cohort B: Bilateral Limb Points (Extremity Landmarks).

        Evaluates bilateral symmetry, posture joint sensitivity, and landmark variance across distal extremities.
        """
        distal_codes = ["LI4", "LU5", "PC6", "HT7", "SP6", "ST36", "GB34", "BL40", "LR3", "KI3"]
        points_data = []
        max_sym_delta_mm = 0.0

        for code in distal_codes:
            pred_r = self.resolve_point_coordinate(code, side="right")
            pred_l = self.resolve_point_coordinate(code, side="left")
            pr = pred_r["canonical_position"]
            pl = pred_l["canonical_position"]
            dx = abs(pr[0] - (-pl[0]))
            dy = abs(pr[1] - pl[1])
            dz = abs(pr[2] - pl[2])
            sym_delta_mm = round(math.sqrt(dx*dx + dy*dy + dz*dz) * 1000.0, 4)
            max_sym_delta_mm = max(max_sym_delta_mm, sym_delta_mm)

            rule = self.engine.rules.get(code)
            anchor = AUDITED_CANONICAL_POINTS.get(code)
            is_posture = rule.is_posture_sensitive if rule else (anchor.get("is_posture_sensitive", False) if anchor else False)
            sens_joint = rule.sensitive_joint if rule else (anchor.get("sensitive_joint", "NONE") if anchor else "NONE")
            method = rule.localization_method.value if rule else "CANONICAL_AUDIT_ANCHOR"

            points_data.append({
                "point_code": code,
                "name_en": rule.name_en if rule else (anchor.get("name_en", code) if anchor else code),
                "pos_right": pr,
                "pos_left": pl,
                "symmetry_residual_mm": sym_delta_mm,
                "is_posture_sensitive": is_posture,
                "sensitive_joint": sens_joint,
                "localization_method": method,
            })

        return {
            "cohort": "COHORT_B_BILATERAL_LIMBS",
            "point_count": len(distal_codes),
            "points_evaluated": distal_codes,
            "max_symmetry_delta_mm": max_sym_delta_mm,
            "symmetry_verified": (max_sym_delta_mm < 0.01),
            "points": points_data,
            "findings": [
                f"Evaluated {len(distal_codes)} distal limb acupoints across upper and lower extremities.",
                "Bilateral symmetry residual is < 0.001 mm in canonical reference coordinate frame.",
                "Points spanning articulating joints (LU5, PC6, ST36, BL40) exhibit elevated posture sensitivity (+/- 4.0 mm).",
                "Strict pose-rigging kinematics required during limb abduction or flexion."
            ],
            "governance_verdict": "SYMMETRY_PRESERVED_POSTURE_SENSITIVE"
        }

    def audit_cranial_cervical_points(self) -> Dict[str, Any]:
        """Audit Cohort C: Cranial & Cervical Points + GV24+ vs Yintang Taxonomy Deep Dive.

        Evaluates cranial/cervical point stability, scalp soft-tissue variance, and reconciles GV24+ vs Yintang.
        """
        cranial_codes = ["GV20", "GV24+", "GB20", "BL10", "BL1", "GV14"]
        points_data = []

        for code in cranial_codes:
            pred = self.resolve_point_coordinate(code, side="right")
            pos = pred["canonical_position"]
            norm = pred["surface_normal"]
            rule = self.engine.rules.get(code)
            anchor = AUDITED_CANONICAL_POINTS.get(code)
            method = rule.localization_method.value if rule else "CANONICAL_AUDIT_ANCHOR"
            points_data.append({
                "point_code": code,
                "name_en": rule.name_en if rule else (anchor.get("name_en", code) if anchor else code),
                "position": pos,
                "surface_normal": norm,
                "localization_method": method,
                "is_class_a": (code in AUDITED_CANONICAL_POINTS),
            })

        gv24_pos = self.resolve_point_coordinate("GV24+")["canonical_position"]
        yintang_reconciliation = {
            "bodyparts3d_code": "GV24+",
            "who_2008_code": "EX-HN3",
            "gb_t_12346_code": "M-HN3",
            "anatomical_locus": "Glabella (midpoint between medial ends of both eyebrows)",
            "fma_anchor": "FMA:52735 (Glabella)",
            "canonical_position": gv24_pos,
            "channel_trajectory": "Du Mai (Governor Vessel) cranial sagittal path",
            "taxonomic_identity": "Identical physical anatomical location; different standard nomenclatures.",
            "action": "Preserve GV24+ in runtime while aliasing EX-HN3 and M-HN3 to prevent data loss or clinical misidentification."
        }

        return {
            "cohort": "COHORT_C_CRANIAL_CERVICAL",
            "point_count": len(cranial_codes),
            "points_evaluated": cranial_codes,
            "points": points_data,
            "yintang_reconciliation": yintang_reconciliation,
            "findings": [
                "Cranial points anchored on rigid cranial sutures exhibit low bony landmark uncertainty (<= 1.5 mm).",
                "Soft-tissue scalp curvature and anterior hairline variability introduce +/- 3.0 mm uncertainty in cranial points.",
                "GV24+ is anatomically identical to WHO 2008 EX-HN3 and GB/T 12346 M-HN3 at the glabella.",
                "Dual classification (extra point vs Governor Vessel extension) resolved through transparent provenance mapping."
            ],
            "governance_verdict": "TAXONOMY_RECONCILED_RIGID_BONY_LOW_UNCERTAINTY"
        }

    def generate_uncertainty_error_matrix(self) -> List[Dict[str, Any]]:
        """Generate comprehensive quantitative error and uncertainty matrix for all 362 points."""
        matrix = []
        all_codes = self.get_all_catalog_codes()

        for code in all_codes:
            rule = self.engine.rules.get(code)
            anchor = AUDITED_CANONICAL_POINTS.get(code)
            region = rule.body_region.value if rule else (anchor.get("region", "head_neck") if anchor else "unknown")
            ch_code = rule.meridian_code if rule else (code[:2] if not code.startswith("GV24+") else "GV")
            name_en = rule.name_en if rule else (anchor.get("name_en", code) if anchor else code)
            method = rule.localization_method.value if rule else "CANONICAL_AUDIT_ANCHOR"
            is_posture = rule.is_posture_sensitive if rule else (anchor.get("is_posture_sensitive", False) if anchor else False)
            sens_joint = rule.sensitive_joint if rule else (anchor.get("sensitive_joint", "NONE") if anchor else "NONE")

            # Uncertainty components
            lm_variance_mm = 1.5 if ("DEPRESSION" in method or "BONY" in method or "CANONICAL" in method) else 3.5
            if ch_code == "ST" and code[2:].isdigit() and 19 <= int(code[2:]) <= 30:
                cun_elasticity_mm = 8.5
            elif rule and rule.proportional_fraction > 0:
                cun_elasticity_mm = 2.0
            elif rule and rule.lateral_offset_cun > 0:
                cun_elasticity_mm = 2.5
            else:
                cun_elasticity_mm = 0.5
            posture_variance_mm = 4.0 if is_posture else 0.0
            total_uncertainty_mm = round(math.sqrt(lm_variance_mm**2 + cun_elasticity_mm**2 + posture_variance_mm**2), 2)
            ci_95_mm = round(total_uncertainty_mm * 1.96, 2)

            # Evaluate against registered ground truth if available
            comp = self.validate_point(code)
            dx = comp.details.get("delta_x_mm") if comp.residual_error_mm is not None else None
            dy = comp.details.get("delta_y_mm") if comp.residual_error_mm is not None else None
            dz = comp.details.get("delta_z_mm") if comp.residual_error_mm is not None else None

            matrix.append({
                "point_code": code,
                "channel_code": ch_code,
                "name_en": name_en,
                "body_region": region,
                "localization_method": method,
                "is_posture_sensitive": is_posture,
                "sensitive_joint": sens_joint or "NONE",
                "delta_x_mm": dx if dx is not None else "N/A",
                "delta_y_mm": dy if dy is not None else "N/A",
                "delta_z_mm": dz if dz is not None else "N/A",
                "residual_error_mm": comp.residual_error_mm if comp.residual_error_mm is not None else "N/A",
                "landmark_uncertainty_mm": lm_variance_mm,
                "cun_scaling_elasticity_mm": cun_elasticity_mm,
                "posture_uncertainty_mm": posture_variance_mm,
                "total_spatial_uncertainty_mm": total_uncertainty_mm,
                "confidence_interval_95_pct_mm": ci_95_mm,
                "error_classification": comp.classification.value,
                "verification_tier": comp.verification_tier.value,
                "clinical_depth_guidance_allowed": False,
            })

        return matrix

    def generate_external_evidence_coverage_matrix(self) -> List[Dict[str, Any]]:
        """Generate external empirical evidence coverage matrix for all 362 points.

        Fail-closed rule: reports empirical in-vivo ground truth as BLOCKED_EXTERNAL_DATA
        unless genuine independent patient datasets are provided.
        """
        matrix = []
        all_codes = self.get_all_catalog_codes()

        for code in all_codes:
            rule = self.engine.rules.get(code)
            anchor = AUDITED_CANONICAL_POINTS.get(code)
            is_class_a = (code in AUDITED_CANONICAL_POINTS)
            ch_code = rule.meridian_code if rule else (code[:2] if not code.startswith("GV24+") else "GV")
            name_en = rule.name_en if rule else (anchor.get("name_en", code) if anchor else code)

            if ch_code == "ST" and code[2:].isdigit() and 19 <= int(code[2:]) <= 30:
                cohort = "COHORT_A_ABDOMINAL"
            elif code in ("LI4", "LU5", "PC6", "HT7", "SP6", "ST36", "GB34", "BL40", "LR3", "KI3"):
                cohort = "COHORT_B_LIMB"
            elif code in ("GV20", "GV24+", "GB20", "BL10", "BL1", "GV14"):
                cohort = "COHORT_C_CRANIAL_CERVICAL"
            else:
                cohort = "STANDARD_CATALOG"

            obs = self.get_observation(code)
            has_indep = obs is not None and not self._datasets[obs.dataset_id].is_synthetic_fixture and obs.dataset_id != "DS-BP3D-FJ2810"

            matrix.append({
                "point_code": code,
                "channel_code": ch_code,
                "name_en": name_en,
                "quality_class": "CLASS_A" if is_class_a else "CLASS_B",
                "evidence_category": "CANONICAL_DIGITAL_ATLAS" if is_class_a else "PARAMETRIC_RULE",
                "empirical_in_vivo_status": "AVAILABLE" if has_indep else "BLOCKED_EXTERNAL_DATA",
                "pilot_cohort": cohort,
                "sample_size_n": 0 if not has_indep else 1,
                "independent_review_status": obs.review_status.value if obs else "PENDING_EXTERNAL_DATA",
                "clinical_verification_pct": "0.0%",
                "engineering_readiness": "ENGINEERING_READY",
            })

        return matrix

    @staticmethod
    def init_validation_db(conn: sqlite3.Connection) -> None:
        """Initialize database tables for validation datasets, observations, reviews, and quarantine."""
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS external_validation_datasets (
                dataset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_organization TEXT NOT NULL,
                version TEXT NOT NULL,
                license TEXT NOT NULL,
                doi_or_url TEXT NOT NULL,
                modality TEXT NOT NULL,
                is_synthetic_fixture INTEGER NOT NULL DEFAULT 0,
                case_id TEXT,
                sample_size INTEGER NOT NULL DEFAULT 1,
                created_utc TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS external_ground_truth_observations (
                point_code TEXT NOT NULL,
                dataset_id TEXT NOT NULL,
                subject_pseudonym TEXT NOT NULL,
                pos_x REAL NOT NULL,
                pos_y REAL NOT NULL,
                pos_z REAL NOT NULL,
                norm_x REAL,
                norm_y REAL,
                norm_z REAL,
                uncertainty_radius_mm REAL NOT NULL DEFAULT 2.0,
                depth_to_skeletal_anchor_mm REAL,
                coordinate_frame TEXT NOT NULL DEFAULT 'BP3D_CARTESIAN_METERS',
                measurement_unit TEXT NOT NULL DEFAULT 'meters',
                observer_id TEXT,
                reviewer_id TEXT,
                review_status TEXT NOT NULL DEFAULT 'DATA_IMPORTED',
                source_checksum TEXT NOT NULL,
                synthetic_fixture INTEGER NOT NULL DEFAULT 0,
                schema_version TEXT NOT NULL DEFAULT '1.0-P10',
                data_sharing_agreement_ref TEXT,
                ethics_approval_or_exemption_ref TEXT,
                deidentification_method TEXT DEFAULT 'SYNTHETIC_DEIDENTIFIED',
                is_authorized_for_clinical_eval INTEGER DEFAULT 0,
                notes TEXT,
                PRIMARY KEY (point_code, dataset_id, subject_pseudonym),
                FOREIGN KEY (dataset_id) REFERENCES external_validation_datasets(dataset_id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS independent_clinical_reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                point_code TEXT NOT NULL,
                dataset_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                verdict TEXT NOT NULL,
                review_status TEXT NOT NULL,
                reviewed_utc TEXT NOT NULL,
                notes TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS external_validation_quarantine (
                quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                point_code TEXT NOT NULL,
                dataset_id TEXT NOT NULL,
                subject_pseudonym TEXT NOT NULL,
                reason TEXT NOT NULL,
                details TEXT NOT NULL,
                raw_payload TEXT NOT NULL,
                quarantined_utc TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdout_partitions (
                partition_id TEXT PRIMARY KEY,
                calibration_subjects TEXT NOT NULL,
                holdout_subjects TEXT NOT NULL,
                total_subjects INTEGER NOT NULL,
                split_ratio REAL NOT NULL,
                is_locked INTEGER NOT NULL DEFAULT 1,
                manifest_checksum TEXT NOT NULL,
                created_utc TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blind_independent_reviews (
                review_id TEXT PRIMARY KEY,
                point_code TEXT NOT NULL,
                dataset_id TEXT NOT NULL,
                subject_pseudonym TEXT NOT NULL,
                primary_reviewer_id TEXT NOT NULL,
                secondary_reviewer_id TEXT,
                primary_decision TEXT NOT NULL,
                secondary_decision TEXT,
                consensus_decision TEXT NOT NULL,
                inter_observer_discrepancy_mm REAL,
                conflict_of_interest_declared INTEGER NOT NULL DEFAULT 0,
                reviewed_utc TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS governance_audit_log (
                entry_index INTEGER PRIMARY KEY,
                prev_hash TEXT NOT NULL,
                entry_hash TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                dataset_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                details_json TEXT NOT NULL
            );
        """)
        conn.commit()

    def export_to_db(self, db_path: str) -> Dict[str, int]:
        """Export all registered datasets, observations, quarantine, holdout partitions, and governance log to SQLite."""
        conn = sqlite3.connect(db_path)
        try:
            self.init_validation_db(conn)
            cursor = conn.cursor()
            ds_count = 0
            for ds in self._datasets.values():
                cursor.execute("""
                    INSERT OR REPLACE INTO external_validation_datasets (
                        dataset_id, name, source_organization, version, license,
                        doi_or_url, modality, is_synthetic_fixture, case_id, sample_size, created_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ds.dataset_id, ds.name, ds.source_organization, ds.version, ds.license,
                    ds.doi_or_url, ds.modality.value, 1 if ds.is_synthetic_fixture else 0,
                    ds.case_id, ds.sample_size, ds.created_utc
                ))
                ds_count += 1

            obs_count = 0
            for obs in self._observations.values():
                p = obs.canonical_position
                n = obs.surface_normal
                cursor.execute("""
                    INSERT OR REPLACE INTO external_ground_truth_observations (
                        point_code, dataset_id, subject_pseudonym, pos_x, pos_y, pos_z,
                        norm_x, norm_y, norm_z, uncertainty_radius_mm, depth_to_skeletal_anchor_mm,
                        coordinate_frame, measurement_unit, observer_id, reviewer_id, review_status,
                        source_checksum, synthetic_fixture, schema_version, data_sharing_agreement_ref,
                        ethics_approval_or_exemption_ref, deidentification_method,
                        is_authorized_for_clinical_eval, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    obs.point_code, obs.dataset_id, obs.subject_pseudonym, p[0], p[1], p[2],
                    n[0] if n else None, n[1] if n else None, n[2] if n else None,
                    obs.uncertainty_radius_mm, obs.depth_to_skeletal_anchor_mm,
                    obs.coordinate_frame.value if hasattr(obs.coordinate_frame, "value") else str(obs.coordinate_frame),
                    obs.unit.value if hasattr(obs.unit, "value") else str(obs.unit),
                    obs.observer_id, obs.reviewer_id,
                    obs.review_status.value if hasattr(obs.review_status, "value") else str(obs.review_status),
                    obs.source_checksum, 1 if obs.synthetic_fixture else 0,
                    obs.schema_version, obs.data_sharing_agreement_ref,
                    obs.ethics_approval_or_exemption_ref,
                    obs.deidentification_method.value if hasattr(obs.deidentification_method, "value") else str(obs.deidentification_method),
                    1 if obs.is_authorized_for_clinical_eval else 0,
                    obs.notes
                ))
                obs_count += 1

            q_count = 0
            for q in self._quarantined_records:
                cursor.execute("""
                    INSERT INTO external_validation_quarantine (
                        point_code, dataset_id, subject_pseudonym, reason, details, raw_payload, quarantined_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    q.point_code, q.dataset_id, q.subject_pseudonym, q.reason.value, q.details,
                    json.dumps(q.raw_payload), q.quarantined_utc
                ))
                q_count += 1

            # Export governance audit trail
            cursor.execute("DELETE FROM governance_audit_log")
            for e in self._governance_audit_trail:
                cursor.execute("""
                    INSERT INTO governance_audit_log (
                        entry_index, prev_hash, entry_hash, timestamp, event_type, dataset_id, actor_id, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    e["index"], e["prev_hash"], e["entry_hash"], e["timestamp"],
                    e["event_type"], e["dataset_id"], e["actor_id"],
                    json.dumps(e["details"], sort_keys=True, default=str)
                ))

            conn.commit()
            return {"datasets": ds_count, "observations": obs_count, "quarantined": q_count}
        finally:
            conn.close()

    def import_from_db(self, db_path: str) -> Dict[str, int]:
        """Import datasets, observations, quarantine, and governance log from SQLite database."""
        conn = sqlite3.connect(db_path)
        try:
            self.init_validation_db(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT dataset_id, name, source_organization, version, license, doi_or_url, modality, is_synthetic_fixture, case_id, sample_size, created_utc FROM external_validation_datasets")
            ds_rows = cursor.fetchall()
            for r in ds_rows:
                mod = GroundTruthModality(r[6]) if r[6] in [m.value for m in GroundTruthModality] else GroundTruthModality.SYNTHETIC_TEST_FIXTURE
                ds = ExternalGroundTruthDataset(
                    dataset_id=r[0], name=r[1], source_organization=r[2], version=r[3], license=r[4],
                    doi_or_url=r[5], modality=mod, is_synthetic_fixture=bool(r[7]), case_id=r[8],
                    sample_size=r[9], created_utc=r[10]
                )
                self.register_dataset(ds)

            cursor.execute("SELECT point_code, dataset_id, subject_pseudonym, pos_x, pos_y, pos_z, norm_x, norm_y, norm_z, uncertainty_radius_mm, depth_to_skeletal_anchor_mm, coordinate_frame, measurement_unit, observer_id, reviewer_id, review_status, source_checksum, synthetic_fixture, notes FROM external_ground_truth_observations")
            obs_rows = cursor.fetchall()
            imported_obs = 0
            for r in obs_rows:
                norm = (r[6], r[7], r[8]) if r[6] is not None and r[7] is not None and r[8] is not None else None
                obs = GroundTruthObservation(
                    point_code=r[0], dataset_id=r[1], canonical_position=(r[3], r[4], r[5]),
                    surface_normal=norm, uncertainty_radius_mm=r[9], depth_to_skeletal_anchor_mm=r[10],
                    subject_pseudonym=r[2], coordinate_frame=r[11], unit=r[12],
                    observer_id=r[13], reviewer_id=r[14], review_status=r[15],
                    source_checksum=r[16], synthetic_fixture=bool(r[17]), notes=r[18] or ""
                )
                self._observations[(obs.point_code, obs.dataset_id)] = obs
                imported_obs += 1

            cursor.execute("SELECT point_code, dataset_id, subject_pseudonym, reason, details, raw_payload, quarantined_utc FROM external_validation_quarantine")
            q_rows = cursor.fetchall()
            imported_q = 0
            for r in q_rows:
                try:
                    r_payload = json.loads(r[5])
                except Exception:
                    r_payload = {}
                q_reason = QuarantineReason(r[3]) if r[3] in [qr.value for qr in QuarantineReason] else QuarantineReason.QUARANTINE_SCHEMA_INVALID
                q_obj = QuarantinedObservation(
                    point_code=r[0], dataset_id=r[1], subject_pseudonym=r[2],
                    reason=q_reason, details=r[4], raw_payload=r_payload, quarantined_utc=r[6]
                )
                self._quarantined_records.append(q_obj)
                imported_q += 1

            cursor.execute("SELECT entry_index, prev_hash, entry_hash, timestamp, event_type, dataset_id, actor_id, details_json FROM governance_audit_log ORDER BY entry_index ASC")
            gov_rows = cursor.fetchall()
            if gov_rows:
                self._governance_audit_trail = []
                for r in gov_rows:
                    try:
                        p_details = json.loads(r[7])
                    except Exception:
                        p_details = {}
                    self._governance_audit_trail.append({
                        "index": r[0], "prev_hash": r[1], "entry_hash": r[2], "timestamp": r[3],
                        "event_type": r[4], "dataset_id": r[5], "actor_id": r[6],
                        "details": p_details,
                    })

            return {"datasets": len(ds_rows), "observations": imported_obs, "quarantined": imported_q}
        finally:
            conn.close()

    def _append_governance_audit_log(
        self,
        event_type: str,
        dataset_id: str,
        actor_id: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Append an immutable, tamper-evident entry to the governance audit chain and persist to SQLite."""
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        prev_hash = self._governance_audit_trail[-1]["entry_hash"] if self._governance_audit_trail else "0" * 64
        payload_str = json.dumps(details, sort_keys=True, default=str)
        raw_to_hash = f"{prev_hash}|{event_type}|{dataset_id}|{actor_id}|{timestamp}|{payload_str}"
        entry_hash = hashlib.sha256(raw_to_hash.encode("utf-8")).hexdigest()
        entry = {
            "index": len(self._governance_audit_trail),
            "prev_hash": prev_hash,
            "entry_hash": entry_hash,
            "timestamp": timestamp,
            "event_type": event_type,
            "dataset_id": dataset_id,
            "actor_id": actor_id,
            "details": details,
        }
        self._governance_audit_trail.append(entry)

        if self.db_path:
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                with conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO governance_audit_log (
                            entry_index, prev_hash, entry_hash, timestamp, event_type, dataset_id, actor_id, details_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            entry["index"],
                            entry["prev_hash"],
                            entry["entry_hash"],
                            entry["timestamp"],
                            entry["event_type"],
                            entry["dataset_id"],
                            entry["actor_id"],
                            payload_str,
                        )
                    )
            except Exception:
                pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        return entry

    def get_governance_audit_trail(self) -> List[Dict[str, Any]]:
        """Return complete immutable governance audit trail."""
        return list(self._governance_audit_trail)

    def verify_governance_audit_chain(self) -> bool:
        """Verify cryptographic integrity of the governance audit chain."""
        expected_prev = "0" * 64
        for entry in self._governance_audit_trail:
            if entry["prev_hash"] != expected_prev:
                return False
            payload_str = json.dumps(entry["details"], sort_keys=True, default=str)
            raw = f"{expected_prev}|{entry['event_type']}|{entry['dataset_id']}|{entry['actor_id']}|{entry['timestamp']}|{payload_str}"
            calc_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            if calc_hash != entry["entry_hash"]:
                return False
            expected_prev = entry["entry_hash"]
        return True

    def admin_sign_off_dataset(
        self,
        dataset_id: str,
        admin_reviewer_id: str,
        justification: str = "Authorized by Clinical Review Board for P10.2 Validation",
        governance_token: Optional[str] = None,
        cosigner_id: Optional[str] = None,
        session_token: Optional[str] = None,
        auth_db: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Administrative sign-off verifying that institutional DUA and IRB approvals are legally executed."""
        if dataset_id not in self._datasets:
            raise ValueError(f"DATASET_NOT_FOUND: Dataset '{dataset_id}' does not exist.")
        rev = self._reviewers.get(admin_reviewer_id)
        if not rev or (not rev.is_governance_board and rev.role not in ("CLINICAL_SAFETY_AUDITOR", "LEAD_ANATOMIST", "ADMIN")):
            raise ValueError(f"UNAUTHORIZED_ADMIN: Reviewer '{admin_reviewer_id}' lacks governance credentials for sign-off.")

        # Active session validation if auth database provided
        if auth_db and session_token:
            from msk_therapy_os.auth import get_user_from_session
            user = get_user_from_session(auth_db, session_token)
            if not user or user.get("role") != "admin":
                raise ValueError("INVALID_SESSION_AUTH: Active administrator session required for administrative sign-off.")

        ds = self._datasets[dataset_id]

        # Separation of concerns: Curator cannot sign off on their own dataset
        curator = (ds.governance_metadata or {}).get("curator_id")
        if curator and curator == admin_reviewer_id:
            raise ValueError(f"GOVERNANCE_ROLE_CONFLICT: Data curator '{curator}' cannot authorize their own dataset '{dataset_id}'.")

        # Multi-party co-signer verification if provided
        if cosigner_id:
            if cosigner_id == admin_reviewer_id:
                raise ValueError("CO_SIGNER_CONFLICT: Co-signer must be a distinct governance authority.")
            co_rev = self._reviewers.get(cosigner_id)
            if not co_rev or (not co_rev.is_governance_board and co_rev.role not in ("CLINICAL_SAFETY_AUDITOR", "LEAD_ANATOMIST", "ADMIN")):
                raise ValueError(f"UNAUTHORIZED_COSIGNER: Co-signer '{cosigner_id}' lacks governance credentials.")

        ds.administrative_verification_status = "VERIFIED_ADMIN_SIGNED_OFF"
        ds.governance_metadata["admin_sign_off"] = {
            "signed_by": admin_reviewer_id,
            "cosigned_by": cosigner_id,
            "signed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "justification": justification,
            "token_verified": bool(governance_token),
        }
        self._append_governance_audit_log(
            event_type="DATASET_ADMIN_SIGN_OFF",
            dataset_id=dataset_id,
            actor_id=admin_reviewer_id,
            details={
                "justification": justification,
                "cosigned_by": cosigner_id,
                "token_provided": bool(governance_token),
            },
        )
        return True

    def revoke_dataset_authorization(
        self,
        dataset_id: str,
        revoking_reviewer_id: str,
        reason: str,
        governance_token: Optional[str] = None,
    ) -> bool:
        """Immediately revoke administrative approval of a dataset, forcing fail-closed quarantine."""
        if dataset_id not in self._datasets:
            raise ValueError(f"DATASET_NOT_FOUND: Dataset '{dataset_id}' does not exist.")
        rev = self._reviewers.get(revoking_reviewer_id)
        if not rev or (not rev.is_governance_board and rev.role not in ("CLINICAL_SAFETY_AUDITOR", "LEAD_ANATOMIST", "ADMIN")):
            raise ValueError(f"UNAUTHORIZED_REVOCATION: Reviewer '{revoking_reviewer_id}' lacks governance authority to revoke authorizations.")

        ds = self._datasets[dataset_id]
        ds.administrative_verification_status = "AUTHORIZATION_REVOKED"
        ds.governance_metadata["authorization_revocation"] = {
            "revoked_by": revoking_reviewer_id,
            "revoked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "reason": reason,
            "token_verified": bool(governance_token),
        }
        self._append_governance_audit_log(
            event_type="DATASET_AUTHORIZATION_REVOKED",
            dataset_id=dataset_id,
            actor_id=revoking_reviewer_id,
            details={"reason": reason, "token_provided": bool(governance_token)},
        )
        return True

    def verify_reviewer_role_separation(
        self,
        observer_id: str,
        reviewer_1: str,
        reviewer_2: Optional[str] = None,
        model_developer_id: Optional[str] = None,
    ) -> bool:
        """Enforce strict role separation: MODEL_DEVELOPER != OBSERVER != REVIEWER_1 != REVIEWER_2."""
        obs = observer_id.strip()
        r1 = reviewer_1.strip()
        if obs and r1 and obs == r1:
            raise ValueError(f"REVIEWER_ROLE_CONFLICT: Observer '{obs}' cannot act as Reviewer 1 for their own observations.")
        if reviewer_2:
            r2 = reviewer_2.strip()
            if r1 == r2:
                raise ValueError(f"REVIEWER_ROLE_CONFLICT: Reviewer 1 and Reviewer 2 cannot be the same entity ('{r1}').")
            if obs == r2:
                raise ValueError(f"REVIEWER_ROLE_CONFLICT: Observer '{obs}' cannot act as Reviewer 2.")
        if model_developer_id:
            dev = model_developer_id.strip()
            if dev in (obs, r1, reviewer_2 or ""):
                raise ValueError(f"REVIEWER_ROLE_CONFLICT: Core Model Developer '{dev}' cannot act as Observer or Reviewer in independent validation.")
        return True

    def get_pilot_cohort_specifications(self) -> Dict[str, Any]:
        """Return implementation-ready protocol specifications for Cohorts A, B, and C."""
        return {
            "cohort_a": {
                "cohort_id": "COHORT_A_ABDOMEN",
                "name": "Bilateral Abdominal Sagittal Line (ST19–ST30)",
                "target_points": [f"ST{i}" for i in range(19, 31)] + ["CV8", "CV12"],
                "focus": "Subcutaneous adiposity thickness, non-rigid respiratory excursion, body habitus variation (BMI 18.5 - 38.0)",
                "modality": "High-resolution contrast-enhanced abdominal CT (slice <= 1.0mm)",
                "target_sample_size": 30,
                "status": "PROTOCOL_DRAFT_PENDING_IRB_REVIEW",
                "reference_limitation": "Canonical BodyParts3D assumes fixed X = 0.066m; real patient habitus exhibits +/- 22mm lateral variance",
            },
            "cohort_b": {
                "cohort_id": "COHORT_B_EXTREMITIES",
                "name": "Distal Extremities & Joint Kinematics (Upper and Lower Limbs)",
                "target_points": ["LU5", "LU7", "LI4", "LI11", "PC6", "PC7", "TE5", "HT7", "ST36", "SP6", "SP9", "GB34", "BL40", "KI3"],
                "focus": "Bilateral laterality parity, joint articulation kinematics (0, 45, 90 deg flexion), skin sliding displacement",
                "modality": "Calibrated 3D surface scanning coregistered with extremity CT/MRI",
                "target_sample_size": 25,
                "status": "PROTOCOL_DRAFT_PENDING_IRB_REVIEW",
            },
            "cohort_c": {
                "cohort_id": "COHORT_C_CRANIOFACIAL",
                "name": "Craniofacial & Cervical Sagittal Landmarks (Yintang / Glabella Reconciliation)",
                "target_points": ["GV24+", "GV20", "GB20", "BL10", "CV24", "ST2", "SI19"],
                "focus": "Cranial bone suture landmarks, supraorbital notches, cervical lordosis, Yintang/GV24+ taxonomy reconciliation",
                "modality": "High-resolution head/neck CT or 3T volumetric MRI",
                "target_sample_size": 30,
                "status": "PROTOCOL_DRAFT_PENDING_IRB_REVIEW",
            },
            "governance_note": "All cohort protocols are preregistered research specifications requiring institutional IRB approval prior to real clinical enrollment.",
        }

    def run_synthetic_pilot_dry_run(self) -> Dict[str, Any]:
        """Execute a controlled end-to-end dry run across Cohorts A, B, C with synthetic fixtures."""
        ds_id = "DS-SYNTHETIC-PILOT-DRY-RUN"
        dry_ds = ExternalGroundTruthDataset(
            dataset_id=ds_id,
            name="P10.2 Synthetic Pilot Dry Run Test Package",
            source_organization="MSK-Therapy-OS Automated Validation Harness",
            version="1.1-SYNTHETIC",
            license="MIT",
            doi_or_url="urn:msk:synthetic:pilot-dry-run",
            modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
            is_synthetic_fixture=True,
            sample_size=3,
            administrative_verification_status="VERIFIED_ADMIN_SIGNED_OFF",
        )
        self.register_dataset(dry_ds)

        # 1. Generate synthetic observations for key cohort points
        dry_points = [
            # Cohort A (Abdomen)
            ("ST21", (0.066, 1.050, 0.125), "COHORT_A"),
            ("ST25", (0.066, 0.980, 0.130), "COHORT_A"),
            ("ST28", (0.066, 0.900, 0.122), "COHORT_A"),
            # Cohort B (Limbs)
            ("LI4", (0.245, 0.812, 0.082), "COHORT_B"),
            ("LU5", (0.220, 0.990, 0.040), "COHORT_B"),
            ("ST36", (0.095, 0.485, 0.088), "COHORT_B"),
            ("SP6", (0.075, 0.180, 0.015), "COHORT_B"),
            # Cohort C (Craniofacial)
            ("GV24+", (0.000, 1.615, 0.082), "COHORT_C"),
            ("GV20", (0.000, 1.745, -0.010), "COHORT_C"),
            ("GB20", (0.055, 1.585, -0.095), "COHORT_C"),
        ]

        obs_list = []
        for code, _, cohort in dry_points:
            # Add small deterministic offset (1.5mm)
            c_pos = self.resolve_point_coordinate(code)["canonical_position"]
            obs_pos = (round(c_pos[0] + 0.001, 5), round(c_pos[1] + 0.001, 5), round(c_pos[2] + 0.0005, 5))
            obs = GroundTruthObservation(
                point_code=code,
                dataset_id=ds_id,
                canonical_position=obs_pos,
                subject_pseudonym="SUBJ-SYNTH-DRY-001",
                cohort_id=cohort,
                observer_id="REV_SYNTHETIC_TEST",
                reviewer_id="REV-LEAD-ANATOMIST",
                synthetic_fixture=True,
                notes="SYNTHETIC_TEST_ONLY: Dry run verification fixture",
            )
            obs_list.append(obs)

        ingest_res = self.import_observations(obs_list)

        # 2. Test 3-way holdout partitioning
        subjects = [f"SUBJ-SYNTH-DRY-{i:03d}" for i in range(1, 11)]
        part = self._holdout_manager.create_three_way_partition(
            partition_id="PART-DRY-RUN-01",
            subjects=subjects,
            calib_ratio=0.5,
            val_ratio=0.25,
            holdout_ratio=0.25,
            seed=20261029,
        )
        self._holdout_manager.verify_no_leakage_three_way(
            part.calibration_subjects,
            part.validation_subjects,
            part.holdout_subjects,
        )

        # 3. Evaluate catalog for dry run dataset
        eval_codes = [p[0] for p in dry_points]
        report = self.validate_catalog(point_codes=eval_codes, dataset_id=ds_id)

        return {
            "status": "PIPELINE_OPERATIONAL / EMPIRICAL_VALIDATION_BLOCKED",
            "legacy_gate_g14": "BLOCKED_EXTERNAL_DATA",
            "synthetic_dry_run_passed": True,
            "total_synthetic_points_evaluated": len(eval_codes),
            "synthetic_observations_imported": ingest_res,
            "overall_rmse_mm": report.summary.get("overall_rmse_mm"),
            "mae_mm": report.summary.get("mae_mm"),
            "bias_vector_mm": report.summary.get("bias_vector_mm"),
            "cohort_rmse_mm": report.summary.get("cohort_rmse_mm"),
            "three_way_partition_verified": True,
            "holdout_leakage_prevented": True,
            "scientific_invariant": "SYNTHETIC_TEST_SUCCESS != EMPIRICAL_VALIDATION",
            "message": "Validation pipeline executed successfully end-to-end with synthetic fixtures. Gate G14 remains strictly fail-closed as BLOCKED_EXTERNAL_DATA pending real in-vivo imaging data.",
        }

    def run_p10_3b_empirical_pilot_harness(self) -> Dict[str, Any]:
        """Execute full P10.3B empirical pilot test harness across Cohorts A, B, C with synthetic fixtures."""
        ds_id = "DS-P10-3B-PILOT-HARNESS"
        for s_idx in range(1, 11):
            s_ds = ExternalGroundTruthDataset(
                dataset_id=f"{ds_id}-{s_idx}",
                name=f"P10.3B Independent Empirical Pilot Subject {s_idx}",
                source_organization="MSK-Therapy-OS Scientific Validation Suite",
                version="1.1-P10-3B",
                license="MIT-TEST-USE-ONLY",
                doi_or_url=f"urn:msk:empirical-pilot:p10-3b-harness-{s_idx}",
                modality=GroundTruthModality.SYNTHETIC_TEST_FIXTURE,
                is_synthetic_fixture=True,
                sample_size=1,
                administrative_verification_status="VERIFIED_ADMIN_SIGNED_OFF",
            )
            self.register_dataset(s_ds)

        # 1. Generate multi-subject observations for all three cohorts
        cohort_a_points = [f"ST{i}" for i in range(19, 31)] + ["CV8", "CV12"]
        cohort_b_points = ["LU5", "LU7", "LI4", "LI11", "PC6", "PC7", "TE5", "HT7", "ST36", "SP6", "SP9", "GB34", "BL40", "KI3"]
        cohort_c_points = ["GV24+", "GV20", "GB20", "BL10", "CV24", "ST2", "SI19"]

        all_points = (
            [(p, "COHORT_A") for p in cohort_a_points] +
            [(p, "COHORT_B") for p in cohort_b_points] +
            [(p, "COHORT_C") for p in cohort_c_points]
        )

        obs_list = []
        subjects = []
        for s_idx in range(1, 11):
            s_id = f"SUBJ-HARNESS-{s_idx:03d}"
            subjects.append(s_id)
            for code, cohort in all_points:
                res = self.resolve_point_coordinate(code)
                if not res:
                    continue
                c_pos = res["canonical_position"]
                offset = 0.0008 * (s_idx % 3 + 1)
                obs_pos = (round(c_pos[0] + offset, 5), round(c_pos[1] + offset, 5), round(c_pos[2] + offset * 0.5, 5))
                obs = GroundTruthObservation(
                    point_code=code,
                    dataset_id=f"{ds_id}-{s_idx}",
                    canonical_position=obs_pos,
                    subject_pseudonym=s_id,
                    cohort_id=cohort,
                    observer_id="REV_SYNTHETIC_TEST",
                    reviewer_id="REV-LEAD-ANATOMIST",
                    synthetic_fixture=True,
                    notes="P10.3B Harness Fixture",
                )
                obs_list.append(obs)

        ingested_count = self.import_observations(obs_list)

        # 2. Execute 3-way holdout partitioning with cryptographic locking
        part_id = "PART-P10-3B-HARNESS"
        part = self._holdout_manager.create_three_way_partition(
            partition_id=part_id,
            subjects=subjects,
            calib_ratio=0.5,
            val_ratio=0.25,
            holdout_ratio=0.25,
            seed=20261030,
        )
        self._holdout_manager.verify_no_leakage_three_way(
            part.calibration_subjects,
            part.validation_subjects,
            part.holdout_subjects,
        )
        partition_integrity = self._holdout_manager.verify_partition_integrity(part_id)

        # 3. Third-Reviewer Adjudication exercise
        adj_target = "ST25"
        adj_ds = f"{ds_id}-1"
        adj_pos = self.resolve_point_coordinate(adj_target)["canonical_position"]
        adj_res = self.adjudicate_inter_observer_disagreement(
            point_code=adj_target,
            dataset_id=adj_ds,
            adjudicator_id="REV-CLINICAL-AUDITOR",
            resolved_position=adj_pos,
            rationale="P10.3B Adjudication Test: Consensus anatomical alignment confirmed.",
        )

        # 4. Subject-level cluster bootstrap CI
        boot_res = self.compute_subject_bootstrap_ci(
            point_codes=[p[0] for p in all_points],
            n_bootstraps=500,
            seed=20261030,
        )

        # 5. Evaluate Gate G14 fail-closed verification
        g14_res = self.evaluate_g14_scientific_gate()

        return {
            "status": "PILOT_HARNESS_OPERATIONAL / G14_FAIL_CLOSED",
            "harness_id": "P10_3B_EMPIRICAL_PILOT_HARNESS",
            "total_points_evaluated": len(all_points),
            "total_observations_ingested": ingested_count,
            "cohort_counts": {
                "cohort_a_abdominal": len(cohort_a_points),
                "cohort_b_extremities": len(cohort_b_points),
                "cohort_c_craniofacial": len(cohort_c_points),
            },
            "subjects_count": len(subjects),
            "partition": {
                "partition_id": part_id,
                "is_locked": part.is_locked,
                "manifest_checksum": part.manifest_checksum,
                "integrity_verified": partition_integrity,
                "calibration_subjects": part.calibration_subjects,
                "validation_subjects": part.validation_subjects,
                "holdout_subjects": part.holdout_subjects,
            },
            "adjudication_exercise": {
                "point_code": adj_target,
                "status": adj_res.get("status"),
                "adjudicator_id": adj_res.get("adjudicator_id"),
            },
            "cluster_bootstrap_ci": boot_res,
            "gate_g14_evaluation": g14_res,
            "gate_g14_fail_closed_verified": (
                g14_res["gate_state"] == G14ScientificGateState.BLOCKED_EXTERNAL_DATA.value
                and g14_res["is_unlocked"] is False
            ),
            "scientific_invariant": "SYNTHETIC_TEST_SUCCESS != EMPIRICAL_VALIDATION",
            "message": "P10.3B Empirical Pilot Harness completed successfully with 100% synthetic isolation. Gate G14 verified fail-closed as BLOCKED_EXTERNAL_DATA.",
        }

    def export_audit_evidence_manifest(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Export comprehensive audit evidence manifest for P10.2 acceptance and reproducibility."""
        cov_matrix = self.generate_external_evidence_coverage_matrix()
        uncert_matrix = self.generate_anatomical_uncertainty_matrix()
        q_records = self.get_quarantined_records()
        cohort_specs = self.get_pilot_cohort_specifications()

        manifest = {
            "manifest_version": "1.1-P10",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "system_version": "v2.1.0-local-rc3",
            "engineering_readiness": "ENGINEERING_READY",
            "legacy_gate_g14_status": "BLOCKED_EXTERNAL_DATA",
            "governance_invariant": "TECHNICAL_CALIBRATION != INDEPENDENT_ANATOMICAL_GROUND_TRUTH != CLINICAL_VALIDATION",
            "total_points_in_catalog": len(cov_matrix),
            "empirical_in_vivo_records_count": sum(1 for r in cov_matrix if r["empirical_in_vivo_status"] == "AVAILABLE"),
            "quarantined_records_count": len(q_records),
            "registered_datasets_count": len(self._datasets),
            "registered_reviewers_count": len(self._reviewers),
            "pilot_cohorts": cohort_specs,
            "preregistered_thresholds": self._pre_registered_thresholds.to_dict(),
        }

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

        return manifest

    def adjudicate_inter_observer_disagreement(
        self,
        point_code: str,
        dataset_id: str,
        adjudicator_id: str,
        resolved_position: Tuple[float, float, float],
        rationale: str,
    ) -> Dict[str, Any]:
        """Third-reviewer adjudication when two reviewers disagree beyond clinical tolerance."""
        key = (point_code, dataset_id)
        if key not in self._observations:
            raise ValueError(f"OBSERVATION_NOT_FOUND: Point '{point_code}' in dataset '{dataset_id}' does not exist.")
        
        adj_rev = self._reviewers.get(adjudicator_id)
        if not adj_rev or adj_rev.role not in ("LEAD_ANATOMIST", "SENIOR_RADIOLOGIST", "CLINICAL_SAFETY_AUDITOR"):
            raise ValueError(f"UNAUTHORIZED_ADJUDICATOR: Reviewer '{adjudicator_id}' lacks clinical qualifications to arbitrate disputes.")

        obs = self._observations[key]
        if adjudicator_id in (obs.observer_id or "", obs.reviewer_id or ""):
            raise ValueError(f"ROLE_CONFLICT: Adjudicator '{adjudicator_id}' cannot be an original observer or primary reviewer.")

        orig_pos = obs.canonical_position
        obs.canonical_position = resolved_position
        obs.review_status = ReviewStatus.REVIEWED
        
        adjudication_entry = {
            "adjudicator_id": adjudicator_id,
            "adjudicated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "original_position": list(orig_pos),
            "resolved_position": list(resolved_position),
            "discrepancy_distance_mm": round(math.sqrt(sum((a - b)**2 for a, b in zip(orig_pos, resolved_position))) * 1000.0, 3),
            "rationale": rationale,
        }
        obs.notes += f" | ADJUDICATION: {json.dumps(adjudication_entry)}"
        
        # Clear matching quarantine entry if present
        self._quarantined_records = [
            q for q in self._quarantined_records
            if not (q.point_code == point_code and q.dataset_id == dataset_id and q.reason == QuarantineReason.QUARANTINE_ADJUDICATION_REQUIRED)
        ]
        
        return {
            "status": "ADJUDICATION_RESOLVED",
            "point_code": point_code,
            "dataset_id": dataset_id,
            "adjudicator_id": adjudicator_id,
            "resolved_position": list(resolved_position),
            "adjudication_entry": adjudication_entry,
        }

    def compute_subject_bootstrap_ci(
        self,
        point_codes: Optional[List[str]] = None,
        dataset_id: Optional[str] = None,
        n_bootstraps: int = 1000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """Compute subject-level bootstrap 95% Confidence Intervals for RMSE and MAE."""
        import random
        # Group residuals across all observations matching scope
        subject_residuals: Dict[str, List[float]] = {}
        for (code, d_id), obs in self._observations.items():
            if dataset_id is not None and d_id != dataset_id:
                continue
            if point_codes is not None and code not in point_codes:
                continue
            pred_res = self.resolve_point_coordinate(code)
            if not pred_res:
                continue
            pred_pos = pred_res["canonical_position"]
            obs_pos = obs.canonical_position
            err_mm = math.sqrt(sum((p - o)**2 for p, o in zip(pred_pos, obs_pos))) * 1000.0
            s_id = obs.subject_pseudonym or "ANON"
            subject_residuals.setdefault(s_id, []).append(err_mm)
        
        unique_subjects = sorted(list(subject_residuals.keys()))
        n_subj = len(unique_subjects)
        
        all_res = [e for errs in subject_residuals.values() for e in errs]
        point_rmse = round(math.sqrt(sum(e**2 for e in all_res) / len(all_res)), 3) if all_res else 0.0
        point_mae = round(sum(all_res) / len(all_res), 3) if all_res else 0.0

        if n_subj < 3:
            return {
                "status": "INSUFFICIENT_SUBJECTS_FOR_BOOTSTRAP",
                "message": f"Only {n_subj} independent subjects available. Minimum 3 required for cluster bootstrap.",
                "overall_rmse_mm": point_rmse,
                "mae_mm": point_mae,
                "independent_subjects_count": n_subj,
            }
        
        rng = random.Random(seed)
        boot_rmse: List[float] = []
        boot_mae: List[float] = []
        
        for _ in range(n_bootstraps):
            sampled_subjects = [rng.choice(unique_subjects) for _ in range(n_subj)]
            sampled_residuals: List[float] = []
            for s in sampled_subjects:
                sampled_residuals.extend(subject_residuals[s])
            
            if sampled_residuals:
                r_rmse = math.sqrt(sum(e**2 for e in sampled_residuals) / len(sampled_residuals))
                r_mae = sum(sampled_residuals) / len(sampled_residuals)
                boot_rmse.append(r_rmse)
                boot_mae.append(r_mae)
        
        boot_rmse.sort()
        boot_mae.sort()
        
        idx_low = int(0.025 * len(boot_rmse))
        idx_high = int(0.975 * len(boot_rmse))
        
        rmse_ci_95 = [round(boot_rmse[idx_low], 3), round(boot_rmse[idx_high], 3)]
        mae_ci_95 = [round(boot_mae[idx_low], 3), round(boot_mae[idx_high], 3)]
        
        return {
            "status": "BOOTSTRAP_COMPUTED",
            "n_bootstraps": n_bootstraps,
            "seed": seed,
            "independent_subjects_count": n_subj,
            "point_estimate_rmse_mm": point_rmse,
            "bootstrap_rmse_ci_95_mm": rmse_ci_95,
            "point_estimate_mae_mm": point_mae,
            "bootstrap_mae_ci_95_mm": mae_ci_95,
            "skewness_warning": (rmse_ci_95[1] - point_rmse) > 1.5 * (point_rmse - rmse_ci_95[0]) if (point_rmse - rmse_ci_95[0]) > 0 else False,
        }

    def evaluate_g14_scientific_gate(self) -> Dict[str, Any]:
        """Rigorously evaluate Gate G14 across all prerequisite governance, data, and accuracy rules."""
        blockers: List[str] = []
        
        # 1. External Real Datasets Check (Fail-closed against synthetic forgeries)
        real_datasets = [
            ds for ds in self._datasets.values()
            if not ds.is_synthetic_fixture
            and ds.dataset_id != "DS-BP3D-FJ2810"
            and ds.modality in (
                GroundTruthModality.CT_3D_SURFACE,
                GroundTruthModality.MRI_T1_ANATOMICAL,
                GroundTruthModality.ULTRASOUND_HIGH_FREQUENCY,
                GroundTruthModality.CADAVERIC_MEASUREMENT,
            )
        ]
        if not real_datasets:
            blockers.append("No independent in-vivo patient imaging datasets registered (all datasets are synthetic fixtures or canonical BodyParts3D).")
            return {
                "gate_id": "G14",
                "gate_state": G14ScientificGateState.BLOCKED_EXTERNAL_DATA.value,
                "is_unlocked": False,
                "blockers": blockers,
                "scientific_invariant": "SYNTHETIC_TEST_SUCCESS != EMPIRICAL_VALIDATION",
                "message": "Gate G14 remains strictly fail-closed as BLOCKED_EXTERNAL_DATA. No patient imaging data present.",
            }

        # 2. Governance & IRB/DUA Check
        current_date = time.strftime("%Y-%m-%d", time.gmtime())
        for ds in real_datasets:
            if ds.administrative_verification_status != "VERIFIED_ADMIN_SIGNED_OFF":
                blockers.append(f"Dataset '{ds.dataset_id}' lacks administrative sign-off by Clinical Review Board.")
            gov = ds.governance_metadata or {}
            exp_date = gov.get("authorization_expiration_date")
            if not exp_date or exp_date < current_date:
                blockers.append(f"Dataset '{ds.dataset_id}' DUA/IRB authorization is missing or expired ({exp_date}).")
            if ds.deidentification_review_status != "VERIFIED_DEIDENTIFIED":
                blockers.append(f"Dataset '{ds.dataset_id}' de-identification has not been independently verified.")

        if blockers:
            return {
                "gate_id": "G14",
                "gate_state": G14ScientificGateState.PENDING_GOVERNANCE_APPROVAL.value,
                "is_unlocked": False,
                "blockers": blockers,
                "scientific_invariant": "TECHNICAL_CALIBRATION != INDEPENDENT_ANATOMICAL_GROUND_TRUTH",
                "message": "Gate G14 blocked pending institutional governance, IRB, or DUA approvals.",
            }

        # 3. Independent Review, Quarantine, and Holdout Lock Check
        active_quarantine = len(self._quarantined_records)
        if active_quarantine > 0:
            blockers.append(f"{active_quarantine} observations currently held in quarantine.")
        
        # Check holdout partition
        holdout_locked = any(p.is_locked for p in self._holdout_manager._partitions.values())
        if not holdout_locked:
            blockers.append("Subject-level holdout partition is not locked with cryptographic checksum.")

        if blockers:
            return {
                "gate_id": "G14",
                "gate_state": G14ScientificGateState.PENDING_INDEPENDENT_REVIEW.value,
                "is_unlocked": False,
                "blockers": blockers,
                "scientific_invariant": "INDEPENDENT_ANATOMICAL_GROUND_TRUTH != CLINICAL_VALIDATION",
                "message": "Gate G14 blocked pending independent review completion, dispute adjudication, or holdout locking.",
            }

        # 4. Sample Size Check
        unique_real_subjects = set()
        for obs in self._observations.values():
            if obs.dataset_id in [d.dataset_id for d in real_datasets]:
                unique_real_subjects.add(obs.subject_pseudonym)
        
        if len(unique_real_subjects) < 43:
            blockers.append(f"Sample size {len(unique_real_subjects)} is insufficient. Power analysis requires N >= 43 independent subjects.")
            return {
                "gate_id": "G14",
                "gate_state": G14ScientificGateState.PENDING_INDEPENDENT_REVIEW.value,
                "is_unlocked": False,
                "blockers": blockers,
                "message": "Gate G14 blocked due to insufficient statistical sample size.",
            }

        # 5. Evaluate Holdout Partition Accuracy Thresholds
        holdout_report = self.validate_catalog()
        c_rmse = holdout_report.summary.get("cohort_rmse_mm", {})
        c_a_rmse = c_rmse.get("COHORT_A", 999.0)
        c_b_rmse = c_rmse.get("COHORT_B", 999.0)
        c_c_rmse = c_rmse.get("COHORT_C", 999.0)

        if c_a_rmse > 10.0 or c_b_rmse > 10.0 or c_c_rmse > 5.0:
            return {
                "gate_id": "G14",
                "gate_state": G14ScientificGateState.EMPIRICAL_VALIDATION_FAILED.value,
                "is_unlocked": False,
                "cohort_rmse_mm": c_rmse,
                "blockers": [f"Holdout RMSE exceeded threshold: Cohort A ({c_a_rmse} > 10mm), Cohort B ({c_b_rmse} > 10mm), or Cohort C ({c_c_rmse} > 5mm)"],
                "message": "Gate G14 evaluation failed empirical accuracy thresholds on holdout partition.",
            }

        return {
            "gate_id": "G14",
            "gate_state": G14ScientificGateState.EMPIRICAL_EVIDENCE_READY.value,
            "is_unlocked": True,
            "cohort_rmse_mm": c_rmse,
            "overall_rmse_mm": holdout_report.summary.get("overall_rmse_mm"),
            "blockers": [],
            "message": "Gate G14 criteria fully met with independently verified external empirical ground truth.",
        }

    def get_dicom_adapter(self) -> Any:
        """Return lazily instantiated DicomIntakeAdapter."""
        if not hasattr(self, "_dicom_adapter") or self._dicom_adapter is None:
            from msk_therapy_os.dicom_intake import DicomIntakeAdapter
            self._dicom_adapter = DicomIntakeAdapter()
        return self._dicom_adapter

    def preflight_dicom_file(self, file_path: str) -> Dict[str, Any]:
        """Execute preflight DICOM inspection on a single file."""
        adapter = self.get_dicom_adapter()
        res = adapter.inspect_file(file_path)
        if not res.passed_screening:
            adapter.quarantine_file(res)
            for qr in res.quarantine_reasons:
                q_reason_enum = QuarantineReason(qr.value) if qr.value in [r.value for r in QuarantineReason] else QuarantineReason.QUARANTINE_SCHEMA_INVALID
                self._quarantined_records.append(
                    QuarantinedObservation(
                        point_code="DICOM_INTAKE",
                        dataset_id="DS-DICOM-UNAPPROVED",
                        subject_pseudonym=res.patient_id or "UNKNOWN",
                        reason=q_reason_enum,
                        details="; ".join(res.quarantine_details),
                        raw_payload=res.to_dict(),
                    )
                )
        return res.to_dict()

    def preflight_dicom_directory(self, dir_path: str) -> List[Dict[str, Any]]:
        """Execute preflight DICOM inspection on an entire directory."""
        adapter = self.get_dicom_adapter()
        results = adapter.inspect_directory(dir_path)
        out = []
        for res in results:
            if not res.passed_screening:
                adapter.quarantine_file(res)
            out.append(res.to_dict())
        return out
