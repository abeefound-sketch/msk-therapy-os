"""Adapter for JICio/tcm-3d upstream repository."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAdapter, NormalizedMeridian, NormalizedPoint


class JICioAdapter(BaseAdapter):
    """Adapter extracting points and pre-baked surface meridians from JICio/tcm-3d."""

    COMMIT_SHA = "e8b9ad1c17e67a25e94406100e3fb5c296c24f7a"
    LICENSE = "MIT"
    REPOSITORY = "https://github.com/JICio/tcm-3d"

    def __init__(self, upstream_dir: Path | str | None = None):
        if upstream_dir is None:
            self.upstream_dir = Path(__file__).resolve().parents[2] / "upstream" / "tcm-3d"
        else:
            self.upstream_dir = Path(upstream_dir)

    def get_source_name(self) -> str:
        return "JICio/tcm-3d"

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": self.get_source_name(),
            "repository": self.REPOSITORY,
            "commit_sha": self.COMMIT_SHA,
            "license": self.LICENSE,
            "mesh_source": "BodyParts3D (FJ2810 skin mesh)",
            "units": "meters",
            "origin": "ground (Y=0), crown Y≈1.72m",
            "handedness": "right-handed (+X right, +Y up, +Z front)",
            "algorithm": "Pre-baked triangle raycast snapping with 3.5mm normal offset",
            "bilateral": True,
        }

    def extract_points(self) -> Dict[str, NormalizedPoint]:
        points: Dict[str, NormalizedPoint] = {}

        # 1. Load teaching-points.json (362 points with rich clinical/curation metadata)
        tp_path = self.upstream_dir / "app" / "teaching-points.json"
        tp_data: List[Dict[str, Any]] = []
        if tp_path.exists():
            with open(tp_path, "r", encoding="utf-8") as f:
                tp_data = json.load(f)

        # Index teaching points by code
        tp_index = {item.get("code", ""): item for item in tp_data if item.get("code")}

        # 2. Load baked surface points from meridian-surface.json
        surf_path = self.upstream_dir / "app" / "meridian-surface.json"
        surf_points: Dict[str, Dict[str, Any]] = {}
        if surf_path.exists():
            with open(surf_path, "r", encoding="utf-8") as f:
                surf_data = json.load(f)
                for pt in surf_data.get("points", []):
                    key = pt.get("key", "")
                    base_code = key.split(":")[0]
                    if base_code not in surf_points:
                        surf_points[base_code] = pt

        # Merge points
        for code, tp in tp_index.items():
            pos = tp.get("position", [0.0, 0.0, 0.0])
            norm = tp.get("normal", [0.0, 0.0, 1.0])
            surface_dist = 0.0
            face_idx = None
            mesh_id = "FJ2810"

            if code in surf_points:
                s_pt = surf_points[code].get("target", {})
                if "position" in s_pt:
                    pos = s_pt["position"]
                if "normal" in s_pt:
                    norm = s_pt["normal"]
                face_idx = s_pt.get("faceIndex")
                mesh_id = s_pt.get("meshId", "FJ2810")
                surface_dist = 3.5  # JICio pre-bake applies 3.5mm normal offset

            # Determine clinical review status
            reviewed = tp.get("reviewed", False)
            status = "ANATOMY_REVIEWED" if reviewed else "GEOMETRY_VERIFIED"

            points[code] = NormalizedPoint(
                code=code,
                name_zh=tp.get("name", ""),
                name_en=tp.get("pinyin", ""),
                pinyin=tp.get("pinyin", ""),
                meridian_code=tp.get("meridianId", ""),
                region=tp.get("region", "general"),
                raw_position=tp.get("originalPosition", pos),
                canonical_position=pos,
                normal=norm,
                surface_distance_mm=surface_dist,
                status=status,
                source=self.get_source_name(),
                indications=[],
                location_desc=tp.get("positionProvenance", ""),
                extra={
                    "face_index": face_idx,
                    "mesh_id": mesh_id,
                    "midline": tp.get("midline", False),
                    "generated": tp.get("generated", True),
                    "source_ref": tp.get("source", ""),
                },
            )

        return points

    def extract_meridians(self) -> Dict[str, NormalizedMeridian]:
        meridians: Dict[str, NormalizedMeridian] = {}

        # Load meridian definitions
        m_def_path = self.upstream_dir / "app" / "meridians.json"
        color_map: Dict[str, str] = {}
        name_zh_map: Dict[str, str] = {}
        if m_def_path.exists():
            with open(m_def_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    color_map[item.get("id", "")] = item.get("color", "#ff4444")
                    name_zh_map[item.get("id", "")] = item.get("name", "")

        # Load baked paths from meridian-surface.json
        surf_path = self.upstream_dir / "app" / "meridian-surface.json"
        if not surf_path.exists():
            return meridians

        with open(surf_path, "r", encoding="utf-8") as f:
            surf_data = json.load(f)

        for p_item in surf_data.get("paths", []):
            m_id = p_item.get("id", "")
            raw_verts = p_item.get("vertices", [])
            # Vertices are stored as flat list: [x0, y0, z0, x1, y1, z1, ...]
            # Group into [x, y, z] vectors
            path_pts: List[List[float]] = []
            for i in range(0, len(raw_verts), 3):
                if i + 2 < len(raw_verts):
                    path_pts.append([
                        float(raw_verts[i]),
                        float(raw_verts[i + 1]),
                        float(raw_verts[i + 2]),
                    ])

            if m_id not in meridians:
                meridians[m_id] = NormalizedMeridian(
                    code=m_id,
                    name_zh=name_zh_map.get(m_id, m_id),
                    name_en=m_id,
                    color=color_map.get(m_id, "#ff4444"),
                    point_codes=[],
                    paths=[],
                    vertex_count=0,
                    source=self.get_source_name(),
                )

            meridians[m_id].paths.append(path_pts)
            meridians[m_id].vertex_count += len(path_pts)

        return meridians
