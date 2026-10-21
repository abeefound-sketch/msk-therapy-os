"""Base classes and data models for the Anatomical Research Workbench adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedPoint:
    code: str
    name_zh: str
    name_en: str
    pinyin: str
    meridian_code: str
    region: str
    raw_position: List[float]
    canonical_position: List[float]
    normal: Optional[List[float]] = None
    surface_distance_mm: float = 0.0
    status: str = "UNVERIFIED"
    source: str = ""
    indications: List[str] = field(default_factory=list)
    location_desc: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedMeridian:
    code: str
    name_zh: str
    name_en: str
    color: str
    point_codes: List[str]
    paths: List[List[List[float]]]  # list of paths, each path is list of [x, y, z]
    vertex_count: int = 0
    source: str = ""


class BaseAdapter(ABC):
    """Abstract interface for all upstream research adapters."""

    @abstractmethod
    def get_source_name(self) -> str:
        """Name of the upstream repository or project."""
        pass

    @abstractmethod
    def extract_points(self) -> Dict[str, NormalizedPoint]:
        """Extract and normalize all acupuncture points to canonical meters coordinates."""
        pass

    @abstractmethod
    def extract_meridians(self) -> Dict[str, NormalizedMeridian]:
        """Extract and normalize meridian pathways and continuous surface paths."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Extract license, commit SHA, model source, and algorithm characteristics."""
        pass
