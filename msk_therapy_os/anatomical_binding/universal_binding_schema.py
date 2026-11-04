"""
MSK-Therapy-OS V1.3 — Universal Anatomical Binding System: Binding Schema
========================================================================
Defines the universal declarative contract and data structures for anatomical
structures (bones, muscles, ligaments, surface anchors) mapped to the canonical humanoid skeleton.

Guarantees:
- Strict schema validation with fail-closed semantics.
- Provenance tracking (source asset ID, hash, DBCLS / FMA citation).
- Strategy polymorphism (RIGID_BONE, MULTI_BONE_SKINNING, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union


class StructureType(str, Enum):
    BONE = "BONE"
    MUSCLE = "MUSCLE"
    SURFACE_ANCHOR = "SURFACE_ANCHOR"
    LIGAMENT_TENDON = "LIGAMENT_TENDON"
    SKIN_SURFACE = "SKIN_SURFACE"


class Laterality(str, Enum):
    RIGHT = "RIGHT"
    LEFT = "LEFT"
    BILATERAL = "BILATERAL"
    MIDLINE = "MIDLINE"


class BindingStrategyType(str, Enum):
    RIGID_BONE = "RIGID_BONE"
    MULTI_BONE_SKINNING = "MULTI_BONE_SKINNING"
    ATTACHMENT_DRIVEN_DEFORMATION = "ATTACHMENT_DRIVEN_DEFORMATION"
    SURFACE_BARYCENTRIC = "SURFACE_BARYCENTRIC"
    MORPH_AWARE_REGISTRATION = "MORPH_AWARE_REGISTRATION"


class RegistrationStatus(str, Enum):
    REGISTERED_ACTIVE = "REGISTERED_ACTIVE"
    PENDING = "PENDING"
    REQUIRES_REGISTRATION_REVIEW = "REQUIRES_REGISTRATION_REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class AttachmentLandmark:
    landmark_name: str
    target_bone_id: str
    local_position_m: Tuple[float, float, float]
    anatomical_feature: str  # e.g., "tuberositas tibiae", "tuberculum supraglenoidale"


@dataclass
class AnatomicalStructureDefinition:
    structure_id: str                          # e.g., "FJ3365", "FJ1433", "LI4"
    structure_type: StructureType
    anatomical_name_en: str
    anatomical_name_vi: str
    laterality: Laterality
    source_mesh_id: str
    source_mesh_file: str
    source_hash: str                           # SHA-256 of source mesh
    canonical_skeleton_id: str                 # e.g., "makehuman_game_engine_53"
    primary_bone_id: str                       # Main parent bone in canonical rig
    secondary_bone_id: Optional[str] = None    # Secondary bone for dual/multi-bone structures
    origin_attachment: Optional[AttachmentLandmark] = None
    insertion_attachment: Optional[AttachmentLandmark] = None
    deformation_strategy: BindingStrategyType = BindingStrategyType.RIGID_BONE
    registration_status: RegistrationStatus = RegistrationStatus.PENDING
    fma_id: Optional[str] = None               # Foundational Model of Anatomy ID
    source_reference: Optional[str] = None     # e.g., "BodyParts3D CC BY 4.0 DBCLS Japan"
    metadata: Dict[str, Any] = field(default_factory=dict)
    clinical_safety_notice: str = "ENGINEERING_RESEARCH_ONLY; NOT_FOR_CLINICAL_USE"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["structure_type"] = self.structure_type.value
        d["laterality"] = self.laterality.value
        d["deformation_strategy"] = self.deformation_strategy.value
        d["registration_status"] = self.registration_status.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnatomicalStructureDefinition":
        # Fail-closed validation of required fields
        required_fields = [
            "structure_id", "structure_type", "anatomical_name_en", "laterality",
            "source_mesh_id", "source_hash", "canonical_skeleton_id", "primary_bone_id"
        ]
        for rf in required_fields:
            if rf not in data or data[rf] is None or data[rf] == "":
                raise ValueError(f"Universal ABS Validation Failure: missing required field '{rf}'")

        data_copy = dict(data)
        data_copy.setdefault("source_mesh_file", f"{data_copy.get('source_mesh_id', '')}.obj")
        data_copy.setdefault("anatomical_name_vi", data_copy.get("anatomical_name_en", ""))
        data_copy["structure_type"] = StructureType(data_copy["structure_type"])
        data_copy["laterality"] = Laterality(data_copy["laterality"])
        data_copy["deformation_strategy"] = BindingStrategyType(data_copy.get("deformation_strategy", BindingStrategyType.RIGID_BONE))
        data_copy["registration_status"] = RegistrationStatus(data_copy.get("registration_status", RegistrationStatus.PENDING))

        if "origin_attachment" in data_copy and isinstance(data_copy["origin_attachment"], dict):
            orig = data_copy["origin_attachment"]
            data_copy["origin_attachment"] = AttachmentLandmark(
                orig["landmark_name"],
                orig["target_bone_id"],
                tuple(orig["local_position_m"]),
                orig.get("anatomical_feature", "")
            )

        if "insertion_attachment" in data_copy and isinstance(data_copy["insertion_attachment"], dict):
            ins = data_copy["insertion_attachment"]
            data_copy["insertion_attachment"] = AttachmentLandmark(
                ins["landmark_name"],
                ins["target_bone_id"],
                tuple(ins["local_position_m"]),
                ins.get("anatomical_feature", "")
            )

        return cls(**data_copy)


@dataclass
class ValidationResult:
    is_valid: bool
    structure_id: str
    strategy: BindingStrategyType
    rms_error_mm: float
    max_drift_mm: float
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
