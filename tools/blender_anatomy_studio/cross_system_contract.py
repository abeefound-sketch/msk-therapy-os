"""Cross-System Data Exchange Contract for Milestone P31.
Standardizes data exchange between Blender Anatomy Studio, MSK Web Atlas,
and the Knowledge Vault under strict ENGINEERING_RESEARCH_ONLY scope.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

RELEASE_SCOPE = "ENGINEERING_RESEARCH_ONLY"
CLINICAL_SAFETY_BARRIER = "STRICT_RESEARCH_ONLY - NO_AUTONOMOUS_DIAGNOSIS_OR_PRESCRIPTION"
FORBIDDEN_PII_KEYS = {"patient_name", "patient_id", "ssn", "dob", "phone", "email", "address", "mrn"}


@dataclass
class AssetManifestEntry:
    asset_id: str
    mesh_name: str
    bone_parent: Optional[str]
    fma_id: Optional[str]
    vertex_count: int
    face_count: int
    sha256_hash: str
    license_tag: str
    availability_status: str  # "AVAILABLE" or "ASSET_NOT_AVAILABLE"


@dataclass
class SurfaceAnchorEntry:
    marker_id: str
    anatomy_structure_id: str
    bone_parent: Optional[str]
    fma_id: str
    who_reference: str
    local_coords: List[float]
    world_coords_rest: List[float]
    world_coords_elevated: List[float]
    surface_drift_mm: float
    status: str  # "VALID_SURFACE_ANCHOR", "ASSET_NOT_AVAILABLE", "PROHIBITED_CROSS_BINDING"


@dataclass
class MotionFrameEntry:
    frame: int
    timestamp_sec: float
    joint_angles_deg: Dict[str, float]
    bone_translations_mm: Dict[str, float]
    observability_state: Dict[str, str]


@dataclass
class KnowledgeLinkEntry:
    code: str
    name_zh: str
    name_en: str
    skeletal_anchor: str
    fma_id: str
    who_reference: str
    clinical_uncertainty_mm: float
    review_status: str
    availability_status: str  # "AVAILABLE" or "ASSET_NOT_AVAILABLE"
    claims: List[Dict[str, Any]]
    citations: List[str]


@dataclass
class CrossSystemExchangeBundle:
    bundle_id: str
    created_at_utc: str
    release_scope: str = RELEASE_SCOPE
    clinical_safety_barrier: str = CLINICAL_SAFETY_BARRIER
    schema_version: str = "1.0.0"
    source_milestone: str = "P31"
    scene_assets: List[Dict[str, Any]] = field(default_factory=list)
    surface_anchors: List[Dict[str, Any]] = field(default_factory=list)
    motion_sequence: List[Dict[str, Any]] = field(default_factory=list)
    validation_metrics: Dict[str, Any] = field(default_factory=dict)
    knowledge_links: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        self.verify_no_pii(d)
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CrossSystemExchangeBundle:
        cls.verify_no_pii(data)
        if data.get("release_scope") != RELEASE_SCOPE:
            raise ValueError(f"Invalid release scope: {data.get('release_scope')}. Must be {RELEASE_SCOPE}.")
        return cls(
            bundle_id=data.get("bundle_id", "bundle_unknown"),
            created_at_utc=data.get("created_at_utc", datetime.now(timezone.utc).isoformat()),
            release_scope=data.get("release_scope", RELEASE_SCOPE),
            clinical_safety_barrier=data.get("clinical_safety_barrier", CLINICAL_SAFETY_BARRIER),
            schema_version=data.get("schema_version", "1.0.0"),
            source_milestone=data.get("source_milestone", "P31"),
            scene_assets=data.get("scene_assets", []),
            surface_anchors=data.get("surface_anchors", []),
            motion_sequence=data.get("motion_sequence", []),
            validation_metrics=data.get("validation_metrics", {}),
            knowledge_links=data.get("knowledge_links", {})
        )

    @classmethod
    def verify_no_pii(cls, obj: Any) -> None:
        """Recursively ensure no patient identifiers or PII fields exist in the bundle."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in FORBIDDEN_PII_KEYS:
                    raise ValueError(f"PII Leakage Detected: Forbidden key '{k}' found in data exchange bundle.")
                cls.verify_no_pii(v)
        elif isinstance(obj, list):
            for item in obj:
                cls.verify_no_pii(item)

    def save(self, filepath: str | Path) -> None:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, filepath: str | Path) -> CrossSystemExchangeBundle:
        p = Path(filepath)
        if not p.exists():
            raise FileNotFoundError(f"Bundle file not found: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)
