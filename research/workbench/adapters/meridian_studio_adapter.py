"""Adapter for eb-barry/acupuncture-3d-authoring (Meridian Studio)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAdapter, NormalizedMeridian, NormalizedPoint


class MeridianStudioAdapter(BaseAdapter):
    """Adapter extracting points catalog and authoring documents from eb-barry/acupuncture-3d-authoring."""

    COMMIT_SHA = "cb7a41692276adcbf696538d30f2e3d8ecb4bbc6"
    LICENSE = "MIT (code) / CC BY 4.0 (models)"
    REPOSITORY = "https://github.com/eb-barry/acupuncture-3d-authoring"

    def __init__(self, upstream_dir: Path | str | None = None):
        if upstream_dir is None:
            self.upstream_dir = Path(__file__).resolve().parents[2] / "upstream" / "acupuncture-3d-authoring"
        else:
            self.upstream_dir = Path(upstream_dir)

    def get_source_name(self) -> str:
        return "eb-barry/acupuncture-3d-authoring"

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": self.get_source_name(),
            "repository": self.REPOSITORY,
            "commit_sha": self.COMMIT_SHA,
            "license": self.LICENSE,
            "mesh_source": "MakeHuman/Custom Male (13.5MB) & Female (24MB) GLBs",
            "units": "meters",
            "origin": "BVH bounding box centered",
            "handedness": "right-handed (+X right, +Y up, +Z front)",
            "algorithm": "BVH raycast surface picking + CatmullRom ribbon spline extrusions with depthBias -0.0005",
            "bilateral": True,
            "has_authoring_ui": True,
        }

    def _load_catalog(self) -> Dict[str, Any]:
        cat_path = self.upstream_dir / "src" / "data" / "acupuncture-data.json"
        if cat_path.exists():
            with open(cat_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def extract_points(self) -> Dict[str, NormalizedPoint]:
        catalog = self._load_catalog()
        points: Dict[str, NormalizedPoint] = {}

        # Meridian name to code mapping
        m_map = {
            "手太陰肺經": "LU",
            "手陽明大腸經": "LI",
            "足陽明胃經": "ST",
            "足太陰脾經": "SP",
            "手少陰心經": "HT",
            "手太陽小腸經": "SI",
            "足太陽膀胱經": "BL",
            "足少陰腎經": "KI",
            "手厥陰心包經": "PC",
            "手少陽三焦經": "TE",
            "足少陽膽經": "GB",
            "足厥陰肝經": "LR",
            "任脈": "CV",
            "督脈": "GV",
        }

        for name_zh, item in catalog.items():
            code = item.get("國際代碼", "")
            if not code:
                continue

            m_name = item.get("所屬經脈", "")
            m_code = m_map.get(m_name, "")
            indications = []
            if item.get("主治"):
                indications.append(item["主治"])
            if item.get("現代醫學闡釋"):
                indications.append(f"现代医学: {item['現代醫學闡釋']}")

            contraindications = item.get("針灸禁忌")
            c_desc = item.get("禁忌說明")
            location_guide = item.get("取穴要領", "")

            points[code] = NormalizedPoint(
                code=code,
                name_zh=name_zh,
                name_en=code,
                pinyin="",
                meridian_code=m_code,
                region="body",
                raw_position=[0.0, 0.0, 0.0],
                canonical_position=[0.0, 0.0, 0.0],
                normal=None,
                surface_distance_mm=0.0,
                status="UNVERIFIED",  # Catalog has clinical text; authoring creates 3D coordinates interactively
                source=self.get_source_name(),
                indications=indications,
                location_desc=location_guide,
                extra={
                    "traditional_meridian": m_name,
                    "attributes": item.get("經穴屬性", []),
                    "contraindications": contraindications,
                    "contraindication_details": c_desc,
                    "quick_location": item.get("簡易取穴法", ""),
                },
            )

        return points

    def extract_meridians(self) -> Dict[str, NormalizedMeridian]:
        # Meridian Studio catalog meridians
        meridians: Dict[str, NormalizedMeridian] = {}
        m_defs = [
            ("LU", "手太陰肺經", "#3b82f6"),
            ("LI", "手陽明大腸經", "#ffb066"),
            ("ST", "足陽明胃經", "#ffd24d"),
            ("SP", "足太陰脾經", "#b8e986"),
            ("HT", "手少陰心經", "#ff4d4f"),
            ("SI", "手太陽小腸經", "#ff7a45"),
            ("BL", "足太陽膀胱經", "#ffa940"),
            ("KI", "足少陰腎經", "#36cfc9"),
            ("PC", "手厥陰心包經", "#9254de"),
            ("TE", "手少陽三焦經", "#f759ab"),
            ("GB", "足少陽膽經", "#73d13d"),
            ("LR", "足厥陰肝經", "#40a9ff"),
            ("CV", "任脈", "#faad14"),
            ("GV", "督脈", "#f5222d"),
        ]
        for code, name, color in m_defs:
            meridians[code] = NormalizedMeridian(
                code=code,
                name_zh=name,
                name_en=code,
                color=color,
                point_codes=[],
                paths=[],
                vertex_count=0,
                source=self.get_source_name(),
            )
        return meridians
