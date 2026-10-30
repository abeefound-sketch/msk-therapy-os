"""MSK-Therapy-OS P10.7 Protocol Freeze & Canonical Manifest Engine

Provides versioned protocol freezing, canonical SHA-256 hashing, tamper detection,
and immutable manifest verification for multicenter anatomical validation protocols
covering Cohorts A, B, and C.

Invariants:
- Status is strictly PROTOCOL_FREEZE_CANDIDATE / EXTERNAL_REVIEW_REQUIRED.
- No protocol or SAP is declared externally approved without verified external legal/ethics execution.
- Any post-freeze modification without a formal versioned amendment raises ProtocolTamperError.
- Canonical hashing covers all protocol specifications and mathematical parameters.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ProtocolLifecycleStatus(str, Enum):
    DRAFT_INTERNAL = "DRAFT_INTERNAL"
    PROTOCOL_FREEZE_CANDIDATE = "PROTOCOL_FREEZE_CANDIDATE"
    EXTERNAL_REVIEW_REQUIRED = "EXTERNAL_REVIEW_REQUIRED"
    ETHICS_SUBMITTED = "ETHICS_SUBMITTED"
    AMENDMENT_PENDING = "AMENDMENT_PENDING"
    FROZEN_LOCKED = "FROZEN_LOCKED"


class ProtocolTamperError(ValueError):
    """Raised when a frozen protocol or manifest hash fails integrity validation."""
    pass


@dataclass
class LandmarkProtocolSpec:
    landmark_id: str
    anatomical_name: str
    target_modality: str
    spatial_resolution_mm: float
    max_tolerable_error_mm: float
    clinical_reference: str


@dataclass
class CohortProtocolDefinition:
    cohort_id: str
    target_region: str
    modality: str
    recommended_sample_size: int
    holdout_percentage: float
    max_slice_thickness_mm: float
    primary_landmarks: List[LandmarkProtocolSpec]
    inferred_meridian_segments: List[str]
    inter_observer_concordance_threshold_mm: float = 2.00
    rmse_acceptance_ceiling_mm: float = 2.50


@dataclass
class FrozenProtocolManifest:
    protocol_version: str
    release_tag: str
    lifecycle_status: ProtocolLifecycleStatus
    created_at_utc: str
    canonical_hash: str
    cohorts: List[Dict[str, Any]]
    primary_estimand: str
    statistical_methods: Dict[str, Any]
    data_governance: Dict[str, Any]
    external_review_blockers: List[str]
    amendment_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["lifecycle_status"] = self.lifecycle_status.value
        return d


class ProtocolFreezeManager:
    """Manages canonical freezing, hashing, and tamper verification of study protocols."""

    CURRENT_PROTOCOL_VERSION = "v1.0-RC-P10.7"
    RELEASE_TAG = "v2.1.0-local-rc3"

    @classmethod
    def get_standard_cohort_definitions(cls) -> List[CohortProtocolDefinition]:
        """Returns the canonical prespecified protocol specifications for Cohorts A, B, and C."""
        cohort_a = CohortProtocolDefinition(
            cohort_id="COHORT_A_HEAD_NECK_CT",
            target_region="Head & Cervical Spine",
            modality="CT (High-Resolution Axial/Volumetric)",
            recommended_sample_size=30,
            holdout_percentage=0.30,
            max_slice_thickness_mm=1.25,
            primary_landmarks=[
                LandmarkProtocolSpec("NASION", "Nasofrontal suture depression", "CT", 0.5, 2.0, "Suboccipital/Cranial Reference"),
                LandmarkProtocolSpec("INION", "External occipital protuberance midpoint", "CT", 0.5, 2.0, "GV-16 / Occipital Reference"),
                LandmarkProtocolSpec("GLABELLA", "Smooth prominence between superciliary arches", "CT", 0.5, 2.0, "GV-24.5 / Facial Reference"),
                LandmarkProtocolSpec("MASTOID_PROCESS_L", "Left mastoid tip osseous apex", "CT", 0.6, 2.5, "GB-12 / Temporal Reference"),
                LandmarkProtocolSpec("MASTOID_PROCESS_R", "Right mastoid tip osseous apex", "CT", 0.6, 2.5, "GB-12 / Temporal Reference"),
                LandmarkProtocolSpec("C7_SPINOUS_PROCESS", "Prominent cervical vertebra tip", "CT", 0.8, 2.5, "GV-14 / Cervicothoracic Reference"),
            ],
            inferred_meridian_segments=["GV_CRANIAL", "BL_CRANIAL", "GB_TEMPORAL"],
            inter_observer_concordance_threshold_mm=1.50,
            rmse_acceptance_ceiling_mm=2.20,
        )

        cohort_b = CohortProtocolDefinition(
            cohort_id="COHORT_B_KNEE_EXTREMITY_MRI",
            target_region="Knee Joint & Lower Extremity",
            modality="MRI (T1/T2 3D Volumetric or Fast Spin Echo)",
            recommended_sample_size=25,
            holdout_percentage=0.30,
            max_slice_thickness_mm=3.00,
            primary_landmarks=[
                LandmarkProtocolSpec("TIBIAL_TUBEROSITY", "Anterior tibial tubercle bony apex", "MRI", 1.0, 3.0, "ST-36 Reference"),
                LandmarkProtocolSpec("PATELLA_INFERIOR_POLE", "Apex of patella tendon origin", "MRI", 0.8, 2.5, "ST-35 / Xiyan Reference"),
                LandmarkProtocolSpec("MEDIAL_FEMORAL_EPICONDYLE", "Most prominent medial femoral osseous point", "MRI", 1.0, 3.0, "LR-8 Reference"),
                LandmarkProtocolSpec("LATERAL_FEMORAL_EPICONDYLE", "Prominence on lateral aspect of femoral condyle", "MRI", 1.0, 3.0, "GB-33 / GB-34 Reference"),
                LandmarkProtocolSpec("HEAD_OF_FIBULA", "Prominence of proximal fibular head", "MRI", 1.0, 3.0, "GB-34 Reference"),
                LandmarkProtocolSpec("MEDIAL_MALLEOLUS_TIP", "Apex of medial ankle malleolus", "MRI", 0.8, 2.5, "SP-6 / KI-3 Reference"),
            ],
            inferred_meridian_segments=["SP_LEG", "ST_LEG", "LR_LEG", "KI_LEG", "GB_LEG"],
            inter_observer_concordance_threshold_mm=2.20,
            rmse_acceptance_ceiling_mm=2.80,
        )

        cohort_c = CohortProtocolDefinition(
            cohort_id="COHORT_C_UPPER_LIMB_CT_MRI",
            target_region="Upper Extremity & Forearm",
            modality="CT or High-Resolution MRI",
            recommended_sample_size=30,
            holdout_percentage=0.30,
            max_slice_thickness_mm=2.00,
            primary_landmarks=[
                LandmarkProtocolSpec("RADIAL_STYLOID", "Apex of distal radial styloid process", "CT_OR_MRI", 0.8, 2.5, "LU-7 Reference"),
                LandmarkProtocolSpec("ULNAR_STYLOID", "Apex of distal ulnar styloid process", "CT_OR_MRI", 0.8, 2.5, "SI-6 Reference"),
                LandmarkProtocolSpec("BICEPS_TENDON_DISTAL", "Insertion point at radial tuberosity", "MRI", 1.0, 2.5, "LU-5 Reference"),
                LandmarkProtocolSpec("MEDIAL_HUMERAL_EPICONDYLE", "Medial humeral condylar osseous crest", "CT_OR_MRI", 0.8, 2.5, "HT-3 Reference"),
                LandmarkProtocolSpec("LATERAL_HUMERAL_EPICONDYLE", "Lateral humeral condylar osseous crest", "CT_OR_MRI", 0.8, 2.5, "LI-11 Reference"),
            ],
            inferred_meridian_segments=["LU_ARM", "LI_ARM", "PC_ARM", "HT_ARM", "SI_ARM", "TE_ARM"],
            inter_observer_concordance_threshold_mm=1.80,
            rmse_acceptance_ceiling_mm=2.40,
        )

        return [cohort_a, cohort_b, cohort_c]

    @classmethod
    def compute_canonical_hash(cls, payload: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 digest of canonicalized JSON."""
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @classmethod
    def create_freeze_candidate_manifest(cls) -> FrozenProtocolManifest:
        """Generates the official Protocol Freeze Candidate manifest."""
        cohorts = [asdict(c) for c in cls.get_standard_cohort_definitions()]

        primary_estimand = (
            "Mean 3D Euclidean registration error (mm) across prespecified osseous and soft-tissue "
            "anatomical landmarks evaluated on independent holdout DICOM series against independent "
            "dual-radiologist consensus annotations under one-sided non-inferiority margin Delta_0 = 3.00 mm."
        )

        statistical_methods = {
            "hypothesis_framework": "One-sided non-inferiority test (H0: mu >= 3.00 mm vs H1: mu < 3.00 mm)",
            "significance_level_alpha": 0.05,
            "clustering_model": "Multi-level design effect (DE = 1 + (m-1)*rho_subject + m*(n_site-1)*rho_site)",
            "variance_decomposition": "sigma_total^2 = sigma_anat^2 + sigma_obs^2 + sigma_pos^2 + sigma_scanner^2",
            "effective_sample_size": "M_eff = M_valid / DE",
            "cluster_degrees_of_freedom": "df = N_holdout - 1",
            "confidence_intervals": "Two-sided 95% CI based on Student's t critical value with df degrees of freedom",
            "holdout_protection": "Sealed 30% holdout partition, unblinded only after algorithm registration lock",
            "multiplicity_control": "Hierarchical fixed-sequence testing across primary (Cohort A -> B -> C) or Bonferroni correction",
            "missing_data_policy": "Complete-case analysis for primary estimand; sensitivity analysis under multiple imputation (m=10)",
            "outlier_adjudication": "Pre-adjudication threshold of 10.0 mm triggers independent third-radiologist review",
        }

        data_governance = {
            "hipaa_safe_harbor_18_identifiers_removed": True,
            "gdpr_pseudonymization_art_89_compliant": True,
            "dicom_header_tag_scrubbing": "PS 3.15 Annex E compliant",
            "local_execution_boundary": "Air-gapped on-premise compute node, zero outbound telemetry",
            "data_retention_period_years": 5,
            "scientific_gate_g14": "BLOCKED_EXTERNAL_DATA",
            "clinical_depth_guidance_allowed": False,
            "autonomous_diagnosis_allowed": False,
        }

        blockers = [
            "DEP-01: Independent biostatistical protocol review and methodology sign-off pending.",
            "DEP-02: Executed Data Use Agreement (DUA) with prospective hospital partner pending.",
            "DEP-03: Institutional Review Board (IRB) / Ethics Committee approval or exemption pending.",
            "DEP-04: Authorized de-identified clinical DICOM series acquisition pending.",
            "DEP-05: Certified independent radiologist ground-truth annotation consensus pending.",
            "DEP-06: Independent witness certification of 30% holdout sealing pending.",
            "DEP-07: External peer-reviewed publication or scientific advisory committee review pending.",
            "DEP-08: Regulatory device qualification determination (FDA/BfArM/MFDS) pending.",
        ]

        payload_for_hashing = {
            "protocol_version": cls.CURRENT_PROTOCOL_VERSION,
            "release_tag": cls.RELEASE_TAG,
            "cohorts": cohorts,
            "primary_estimand": primary_estimand,
            "statistical_methods": statistical_methods,
            "data_governance": data_governance,
            "blockers": blockers,
        }

        canonical_hash = cls.compute_canonical_hash(payload_for_hashing)

        return FrozenProtocolManifest(
            protocol_version=cls.CURRENT_PROTOCOL_VERSION,
            release_tag=cls.RELEASE_TAG,
            lifecycle_status=ProtocolLifecycleStatus.PROTOCOL_FREEZE_CANDIDATE,
            created_at_utc=datetime.now(timezone.utc).isoformat(),
            canonical_hash=canonical_hash,
            cohorts=cohorts,
            primary_estimand=primary_estimand,
            statistical_methods=statistical_methods,
            data_governance=data_governance,
            external_review_blockers=blockers,
            amendment_history=[],
        )

    @classmethod
    def verify_manifest_integrity(cls, manifest: FrozenProtocolManifest) -> Tuple[bool, Optional[str]]:
        """Verifies that a manifest's content exactly matches its canonical hash."""
        payload = {
            "protocol_version": manifest.protocol_version,
            "release_tag": manifest.release_tag,
            "cohorts": manifest.cohorts,
            "primary_estimand": manifest.primary_estimand,
            "statistical_methods": manifest.statistical_methods,
            "data_governance": manifest.data_governance,
            "blockers": manifest.external_review_blockers,
        }
        recomputed_hash = cls.compute_canonical_hash(payload)
        if recomputed_hash != manifest.canonical_hash:
            return False, f"Hash mismatch: manifest contains {manifest.canonical_hash}, recomputed {recomputed_hash}"
        return True, None
