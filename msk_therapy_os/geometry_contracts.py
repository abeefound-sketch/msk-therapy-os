"""MSK-Therapy-OS - Anatomical Geometry & Mesh Contracts.

Defines immutable data classes, taxonomy enums, and provenance structures for:
1. Mesh Identity and Asset Provenance.
2. Acupoint Quality Tiers (Classification Governance).
3. Surface Registration Contracts.
4. Route Graph Revisions and Invalidation Digests.

Zero external dependencies (stdlib dataclasses, typing, enum, json).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple


class AcupointQualityTier(str, Enum):
    """Authoritative 5-tier classification taxonomy for acupuncture points."""
    EXPERT_REVIEWED = "CLASS_A"           # Ground-truth audited on verified bony/soft tissue landmarks
    LANDMARK_DERIVED = "CLASS_B"          # Derived parametrically via WHO B-cun proportional rules from audited landmarks
    SURFACE_ONLY_APPROXIMATE = "CLASS_D"  # Pre-baked surface raycast coordinates; uncalibrated skeletal correspondence
    UNVERIFIED = "CLASS_E"                # Conflicting or missing data
    UNAVAILABLE = "UNAVAILABLE"           # Deliberately withheld due to lack of empirical evidence


class MeshVerificationStatus(str, Enum):
    """Integrity and availability status of the anatomical reference mesh."""
    VERIFIED_AUTHENTIC_FJ2810 = "VERIFIED_AUTHENTIC_FJ2810"
    PROCEDURAL_DEMO_MANNEQUIN = "PROCEDURAL_DEMO_MANNEQUIN"
    ASSET_UNAVAILABLE = "ASSET_UNAVAILABLE"
    ASSET_HASH_MISMATCH = "ASSET_HASH_MISMATCH"


@dataclass(frozen=True)
class MeshIdentity:
    """Immutable identity record for 3D anatomical meshes."""
    mesh_id: str
    mesh_sha256: str
    coordinate_frame: str = "RIGHT_HANDED_CARTESIAN_METERS"
    axis_orientation: str = "+X right, +Y superior/up, +Z anterior/front"
    units: str = "meters"
    scale_factor: float = 1.0
    vertex_count: int = 0
    triangle_count: int = 0
    verification_status: MeshVerificationStatus = MeshVerificationStatus.VERIFIED_AUTHENTIC_FJ2810
    is_procedural_fallback: bool = False
    disclaimer: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["verification_status"] = self.verification_status.value
        return d


@dataclass(frozen=True)
class AcupointLocalizationRecord:
    """Authoritative coordinate and quality record for a single acupuncture point."""
    point_code: str
    meridian_code: str
    name_zh: str
    name_en: str
    canonical_position: Tuple[float, float, float]
    surface_normal: Tuple[float, float, float]
    quality_tier: AcupointQualityTier
    registration_status: str
    who_reference: str
    fma_anchor: Optional[str] = None
    skeletal_structure: Optional[str] = None
    localization_method: str = "WHO_2008_STANDARD"
    tolerance_radius_mm: float = 5.0
    uncertainty_mm: Optional[float] = None
    mesh_id: str = "FJ2810"
    mesh_hash: str = "05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808"
    is_posture_sensitive: bool = False
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["quality_tier"] = self.quality_tier.value
        return d


def compute_point_set_digest(points: Dict[str, Any]) -> str:
    """Computes a deterministic cryptographic digest over a set of resolved points."""
    normalized = []
    for code in sorted(points.keys()):
        p = points[code]
        pos = p.get("resolved_world_position") or p.get("canonical_position") or p.get("position", [0, 0, 0])
        norm = p.get("surface_normal") or p.get("normal", [0, 0, 1])
        normalized.append((code, [round(float(x), 5) for x in pos], [round(float(x), 4) for x in norm]))
    serialized = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
