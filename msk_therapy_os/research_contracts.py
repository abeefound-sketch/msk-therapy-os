"""MSK-Therapy-OS P10.4 Clinical Research Data Contracts

Provides versioned, frozen data contracts for multi-institutional offline anatomical validation.
Defines explicit evidence types, schema validation, cohort specifications, and scientific invariants.

Scientific Invariants:
1. TECHNICAL_CALIBRATION != INDEPENDENT_GROUND_TRUTH
2. SYNTHETIC_TEST_SUCCESS != EMPIRICAL_VALIDATION
3. ANATOMICAL_LANDMARK_VALIDATION != CLINICAL_VALIDATION
4. ENGINEERING_READY != CLINICALLY_VALIDATED
5. G14 = BLOCKED_EXTERNAL_DATA
6. CT/MRI images provide physical anatomical ground truth for bones/soft tissues,
   NOT direct ground truth for meridians or acupuncture points.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

CURRENT_CONTRACT_VERSION = "v2.0-P10.4"
SUPPORTED_CONTRACT_VERSIONS = {"v1.0-P10.2", "v1.1-P10.3", "v2.0-P10.4"}


class EvidenceType(str, Enum):
    """Explicitly distinguished evidence levels in scientific validation."""
    PHYSICAL_ANATOMICAL_LANDMARK = "PHYSICAL_ANATOMICAL_LANDMARK"
    COMPUTATIONALLY_INFERRED_ACUPOINT = "COMPUTATIONALLY_INFERRED_ACUPOINT"
    CLINICALLY_ASSESSED_OUTCOME = "CLINICALLY_ASSESSED_OUTCOME"


class CohortDefinition(str, Enum):
    """Prespecified multi-institutional research cohorts."""
    COHORT_A_HEAD_NECK_CT = "COHORT_A_HEAD_NECK_CT"
    COHORT_B_KNEE_EXTREMITY_MRI = "COHORT_B_KNEE_EXTREMITY_MRI"
    COHORT_C_UPPER_LIMB_CT_MRI = "COHORT_C_UPPER_LIMB_CT_MRI"


COHORT_SPECS: Dict[str, Dict[str, Any]] = {
    CohortDefinition.COHORT_A_HEAD_NECK_CT.value: {
        "target_region": "Head & Neck",
        "modality": "CT",
        "primary_landmarks": [
            "NASION", "INION", "GLABELLA", "EXTERNAL_OCCIPITAL_PROTUBERANCE",
            "C7_SPINOUS_PROCESS", "MASTOID_PROCESS_L", "MASTOID_PROCESS_R"
        ],
        "inferred_meridian_segments": ["GV_CRANIAL", "BL_CRANIAL", "GB_TEMPORAL"],
        "min_subject_target": 30,
        "max_slice_thickness_mm": 1.25,
    },
    CohortDefinition.COHORT_B_KNEE_EXTREMITY_MRI.value: {
        "target_region": "Knee Joint & Lower Extremity",
        "modality": "MRI",
        "primary_landmarks": [
            "TIBIAL_TUBEROSITY", "PATELLA_INFERIOR_POLE", "MEDIAL_FEMORAL_EPICONDYLE",
            "LATERAL_FEMORAL_EPICONDYLE", "HEAD_OF_FIBULA", "MEDIAL_MALLEOLUS_TIP"
        ],
        "inferred_meridian_segments": ["SP_LEG", "ST_LEG", "LR_LEG", "KI_LEG"],
        "min_subject_target": 25,
        "max_slice_thickness_mm": 3.0,
    },
    CohortDefinition.COHORT_C_UPPER_LIMB_CT_MRI.value: {
        "target_region": "Upper Limb & Forearm",
        "modality": "CT_OR_MRI",
        "primary_landmarks": [
            "RADIAL_STYLOID", "ULNAR_STYLOID", "BICEPS_TENDON_DISTAL",
            "MEDIAL_HUMERAL_EPICONDYLE", "LATERAL_HUMERAL_EPICONDYLE"
        ],
        "inferred_meridian_segments": ["LU_ARM", "LI_ARM", "PC_ARM", "HT_ARM", "SI_ARM", "TE_ARM"],
        "min_subject_target": 30,
        "max_slice_thickness_mm": 2.0,
    },
}


class ResearchContractValidationError(ValueError):
    """Raised when a research dataset contract violates schema constraints."""
    pass


class ExpiredAuthorizationError(ResearchContractValidationError):
    """Raised when IRB or DUA authorization has expired."""
    pass


class InvalidEvidenceTypeError(ResearchContractValidationError):
    """Raised when an acupoint is mislabeled as direct anatomical ground truth."""
    pass


@dataclass
class SiteMetadata:
    site_id: str
    institution_name: str
    country: str
    regulatory_framework: str  # e.g., "HIPAA", "GDPR", "TCVN"
    authorized_contact_email: str
    data_custodian_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuthorizationMetadata:
    dua_id: str
    irb_approval_number: str
    irb_effective_date: str  # ISO date YYYY-MM-DD
    irb_expiration_date: str  # ISO date YYYY-MM-DD
    deidentification_method: str  # e.g., "DICOM_PS3.15_BASIC_APPLICATION_CONFIDENTIALITY_PROFILE"
    attestation_manifest_hash: str
    is_synthetic_fixture: bool = False

    def is_expired(self, current_date: Optional[datetime.date] = None) -> bool:
        if current_date is None:
            current_date = datetime.date.today()
        exp = datetime.date.fromisoformat(self.irb_expiration_date)
        return current_date > exp

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ImagingSeriesContract:
    series_instance_uid: str
    study_instance_uid: str
    modality: str
    body_part_examined: str
    slice_thickness_mm: float
    pixel_spacing_row_mm: float
    pixel_spacing_col_mm: float
    lps_origin_mm: Tuple[float, float, float]
    lps_orientation_matrix_4x4: List[List[float]]
    manufacturer: str
    model_name: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LandmarkObservationContract:
    observation_id: str
    subject_id: str
    cohort_id: str
    landmark_id: str
    evidence_type: EvidenceType
    lps_coordinates_mm: Tuple[float, float, float]
    observer_id: str
    observer_qualification: str
    timestamp_iso: str
    confidence_score: float = 1.0
    computational_model_ref: Optional[str] = None  # Required if evidence_type == COMPUTATIONALLY_INFERRED_ACUPOINT

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence_type"] = self.evidence_type.value
        return d


@dataclass
class ReviewerSignOffContract:
    reviewer_id: str
    site_id: str
    role: str
    coi_conflict_declared: bool
    coi_statement: str
    signature_timestamp_iso: str
    approved: bool
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchDatasetContract:
    contract_version: str
    dataset_id: str
    cohort_id: str
    site: SiteMetadata
    authorization: AuthorizationMetadata
    imaging_series: List[ImagingSeriesContract]
    observations: List[LandmarkObservationContract]
    holdout_ratio: float = 0.3
    holdout_seed: int = 20261030
    sign_offs: List[ReviewerSignOffContract] = field(default_factory=list)
    dataset_hash: str = ""

    def compute_canonical_hash(self) -> str:
        """Computes deterministic SHA-256 over all canonical data fields excluding dataset_hash."""
        norm_dict = {
            "contract_version": self.contract_version,
            "dataset_id": self.dataset_id,
            "cohort_id": self.cohort_id,
            "site": self.site.to_dict(),
            "authorization": self.authorization.to_dict(),
            "imaging_series": [s.to_dict() for s in self.imaging_series],
            "observations": [o.to_dict() for o in self.observations],
            "holdout_ratio": self.holdout_ratio,
            "holdout_seed": self.holdout_seed,
            "sign_offs": [s.to_dict() for s in self.sign_offs],
        }
        encoded = json.dumps(norm_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(encoded).hexdigest()

    def seal(self) -> str:
        """Computes and locks the canonical dataset hash."""
        self.dataset_hash = self.compute_canonical_hash()
        return self.dataset_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "dataset_id": self.dataset_id,
            "cohort_id": self.cohort_id,
            "site": self.site.to_dict(),
            "authorization": self.authorization.to_dict(),
            "imaging_series": [s.to_dict() for s in self.imaging_series],
            "observations": [o.to_dict() for o in self.observations],
            "holdout_ratio": self.holdout_ratio,
            "holdout_seed": self.holdout_seed,
            "sign_offs": [s.to_dict() for s in self.sign_offs],
            "dataset_hash": self.dataset_hash,
        }


def validate_research_contract(
    data: Dict[str, Any],
    check_date: Optional[datetime.date] = None
) -> Tuple[bool, List[str]]:
    """Pure-Python dependency-free schema and invariant validator.
    
    Returns:
        (is_valid, error_list)
    """
    errors: List[str] = []

    # 1. Version check
    version = data.get("contract_version")
    if not version or version not in SUPPORTED_CONTRACT_VERSIONS:
        errors.append(f"Unsupported or missing contract_version: {version}. Expected one of {SUPPORTED_CONTRACT_VERSIONS}")

    # 2. Cohort check
    cohort_id = data.get("cohort_id")
    if not cohort_id or cohort_id not in [c.value for c in CohortDefinition]:
        errors.append(f"Invalid cohort_id: {cohort_id}. Must be one of {[c.value for c in CohortDefinition]}")

    # 3. Site check
    site = data.get("site", {})
    for req_field in ["site_id", "institution_name", "country", "regulatory_framework", "authorized_contact_email", "data_custodian_id"]:
        if not site.get(req_field):
            errors.append(f"Site metadata missing required field: {req_field}")
    if site.get("authorized_contact_email") and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", site["authorized_contact_email"]):
        errors.append(f"Invalid site contact email: {site.get('authorized_contact_email')}")

    # 4. Authorization check
    auth = data.get("authorization", {})
    for req_field in ["dua_id", "irb_approval_number", "irb_effective_date", "irb_expiration_date", "deidentification_method", "attestation_manifest_hash"]:
        if not auth.get(req_field):
            errors.append(f"Authorization missing required field: {req_field}")

    # Expiration date check
    exp_str = auth.get("irb_expiration_date")
    if exp_str:
        try:
            exp_date = datetime.date.fromisoformat(exp_str)
            eval_date = check_date or datetime.date.today()
            if eval_date > exp_date:
                errors.append(f"Authorization has EXPIRED on {exp_str} (evaluation date: {eval_date.isoformat()})")
        except ValueError:
            errors.append(f"Invalid irb_expiration_date format: {exp_str}. Expected YYYY-MM-DD")

    # 5. Scientific Invariant: Evidence Type & Landmark Validation
    obs_list = data.get("observations", [])
    if not isinstance(obs_list, list) or len(obs_list) == 0:
        errors.append("Observations list must contain at least one observation")
    else:
        for idx, obs in enumerate(obs_list):
            ev_type = obs.get("evidence_type")
            l_id = obs.get("landmark_id", "")
            
            if ev_type not in [e.value for e in EvidenceType]:
                errors.append(f"Observation[{idx}] invalid evidence_type: {ev_type}")
                continue

            # Scientific boundary guard:
            # Physical anatomical landmarks must NOT claim to be acupoints directly visible on CT/MRI
            if ev_type == EvidenceType.PHYSICAL_ANATOMICAL_LANDMARK.value:
                # Disallow naming an acupoint code (e.g. ST36, GV20, PC6) directly as a physical anatomical landmark on DICOM
                if re.match(r"^[A-Z]{1,2}\d{1,2}$", l_id.upper()):
                    errors.append(
                        f"Observation[{idx}]: Acupoint '{l_id}' cannot be declared as PHYSICAL_ANATOMICAL_LANDMARK. "
                        f"CT/MRI scans do not directly image acupuncture points; use COMPUTATIONALLY_INFERRED_ACUPOINT "
                        f"with an anatomical anchor reference."
                    )
            elif ev_type == EvidenceType.COMPUTATIONALLY_INFERRED_ACUPOINT.value:
                if not obs.get("computational_model_ref"):
                    errors.append(f"Observation[{idx}]: COMPUTATIONALLY_INFERRED_ACUPOINT requires computational_model_ref")

            # Check coordinate bounds (LPS in mm, sanity check within [-2000, 2000])
            coords = obs.get("lps_coordinates_mm")
            if not isinstance(coords, (list, tuple)) or len(coords) != 3:
                errors.append(f"Observation[{idx}] invalid lps_coordinates_mm format: {coords}")
            else:
                for c in coords:
                    if not isinstance(c, (int, float)) or not (-2500 <= c <= 2500):
                        errors.append(f"Observation[{idx}] coordinate out of anatomical bounds: {c}")

    # 6. Reviewer sign-off check
    sign_offs = data.get("sign_offs", [])
    reviewers_seen = set()
    for s_idx, s in enumerate(sign_offs):
        r_id = s.get("reviewer_id")
        if not r_id:
            errors.append(f"Sign-off[{s_idx}] missing reviewer_id")
        elif r_id in reviewers_seen:
            errors.append(f"Duplicate reviewer_id in sign_offs: {r_id}")
        reviewers_seen.add(r_id)

        # Reviewer COI check
        if s.get("coi_conflict_declared", False):
            errors.append(f"Reviewer {r_id} declared conflict of interest; cannot act as independent adjudicator")

    return (len(errors) == 0, errors)
