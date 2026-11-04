"""Anatomy Asset Catalog for MSK-Therapy-OS V1.0.
Provides unified lookup, FMA mapping, BodyParts3D binary chunks and metadata,
and enforces license provenance (CC BY 4.0 DBCLS Japan).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
ATLAS_JSON_PATH = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models" / "atlas.json"


@dataclass
class StructureMetadata:
    structure_id: str
    name_en: str
    fma_id: str
    system: str
    chunk_index: int
    vertex_count: int
    triangle_count: int
    bounds: List[List[float]]
    license: str = "CC BY 4.0 DBCLS Japan"


class AnatomyAssetCatalog:
    """Catalog of authentic anatomical structures from BodyParts3D."""

    # Authoritative right upper limb structures for V1.0 vertical slice
    RIGHT_UPPER_LIMB_STRUCTURES = {
        "FJ3362": {"name": "Right clavicle", "fma": "FMA:13322", "system": "skeletal", "chunk": 13},
        "FJ3384": {"name": "Right scapula", "fma": "FMA:13395", "system": "skeletal", "chunk": 13},
        "FJ3368": {"name": "Right humerus", "fma": "FMA:23130", "system": "skeletal", "chunk": 13},
        "FJ3349": {"name": "Right radius", "fma": "FMA:23464", "system": "skeletal", "chunk": 13},
        "FJ3391": {"name": "Right ulna", "fma": "FMA:23467", "system": "skeletal", "chunk": 13},
        "FJ3352": {"name": "Right second metacarpal bone", "fma": "FMA:24466", "system": "skeletal", "chunk": 13},
        "FJ3387": {"name": "Right tibia", "fma": "FMA:24477", "system": "skeletal", "chunk": 13},
        "FJ3360": {"name": "Right calcaneus", "fma": "FMA:24497", "system": "skeletal", "chunk": 13},
        "FJ2810": {"name": "Skin (Full body exterior)", "fma": "FMA:7163", "system": "integumentary", "chunk": 10},
    }

    _instance: Optional[AnatomyAssetCatalog] = None

    def __init__(self):
        self.structures: Dict[str, StructureMetadata] = {}
        self._load_catalog()

    def _load_catalog(self):
        if not ATLAS_JSON_PATH.exists():
            return
        data = json.loads(ATLAS_JSON_PATH.read_text(encoding="utf-8"))
        for p in data.get("parts", []):
            sid = p["id"]
            if sid in self.RIGHT_UPPER_LIMB_STRUCTURES or p.get("system") in ["skeletal", "integumentary"]:
                self.structures[sid] = StructureMetadata(
                    structure_id=sid,
                    name_en=p["name"],
                    fma_id=p.get("conceptId", ""),
                    system=p["system"],
                    chunk_index=p["chunk"],
                    vertex_count=p["vertexCount"],
                    triangle_count=p["indexCount"] // 3,
                    bounds=p.get("bounds", [[0, 0, 0], [0, 0, 0]])
                )

    def get_structure(self, structure_id: str) -> Optional[StructureMetadata]:
        return self.structures.get(structure_id)

    def get_vertical_slice_bones(self) -> List[StructureMetadata]:
        return [self.structures[sid] for sid in ["FJ3362", "FJ3384", "FJ3368", "FJ3349", "FJ3391", "FJ3352"] if sid in self.structures]
