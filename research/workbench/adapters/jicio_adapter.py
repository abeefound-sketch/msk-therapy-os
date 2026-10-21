"""Adapter for JICio/tcm-3d upstream repository preserving bilateral point identities."""
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

        # 1. Load teaching-points.json (362 points with clinical/curation metadata)
        tp_path = self.upstream_dir / "app" / "teaching-points.json"
        tp_index: Dict[str, Dict[str, Any]] = {}
        if tp_path.exists():
            with open(tp_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    c = item.get("code")
                    if c:
                        tp_index[c] = item

        # 2. Load baked surface points from meridian-surface.json (670 points)
        surf_path = self.upstream_dir / "app" / "meridian-surface.json"
        surf_points: List[Dict[str, Any]] = []
        if surf_path.exists():
            with open(surf_path, "r", encoding="utf-8") as f:
                surf_data = json.load(f)
                surf_points = surf_data.get("points", [])

        # Process each surface point, preserving side identity
        for pt_entry in surf_points:
            key = pt_entry.get("key", "")
            if not key:
                continue

            # Parse base code and side (e.g. LU1:1 -> code LU1, side 1; LU1:-1 -> code LU1, side -1)
            parts = key.split(":")
            base_code = parts[0]
            side_num = int(parts[1]) if len(parts) > 1 else 1

            tp = tp_index.get(base_code, {})
            is_midline = tp.get("midline", False)

            # Assign distinct identifier
            if is_midline or side_num == 0:
                point_code = base_code
                side_label = "midline"
            elif side_num == 1:
                point_code = f"{base_code}_R"
                side_label = "right"
            else:
                point_code = f"{base_code}_L"
                side_label = "left"

            target = pt_entry.get("target", {})
            pos = target.get("position", tp.get("position", [0.0, 0.0, 0.0]))
            norm = target.get("normal", tp.get("normal", [0.0, 0.0, 1.0]))
            face_idx = target.get("faceIndex")
            mesh_id = target.get("meshId", "FJ2810")

            # Determine clinical review status: only mark ANATOMY_REVIEWED if explicitly reviewed in teaching catalog
            reviewed = tp.get("reviewed", False)
            status = "ANATOMY_REVIEWED" if reviewed else "UNVERIFIED"

            points[point_code] = NormalizedPoint(
                code=point_code,
                name_zh=tp.get("name", base_code),
                name_en=tp.get("pinyin", base_code),
                pinyin=tp.get("pinyin", ""),
                meridian_code=tp.get("meridianId", ""),
                region=tp.get("region", "general"),
                raw_position=tp.get("originalPosition", pos),
                canonical_position=pos,
                normal=norm,
                surface_distance_mm=0.0,  # Will be accurately measured against authentic mesh
                status=status,
                source=self.get_source_name(),
                indications=[],
                location_desc=tp.get("positionProvenance", ""),
                extra={
                    "base_code": base_code,
                    "side": side_label,
                    "side_num": side_num,
                    "face_index": face_idx,
                    "mesh_id": mesh_id,
                    "midline": is_midline,
                    "generated": tp.get("generated", True),
                    "source_ref": tp.get("source", ""),
                },
            )

        # Fallback if meridian-surface.json is empty: load teaching-points directly
        if not points:
            for code, tp in tp_index.items():
                pos = tp.get("position", [0.0, 0.0, 0.0])
                reviewed = tp.get("reviewed", False)
                status = "ANATOMY_REVIEWED" if reviewed else "UNVERIFIED"
                points[code] = NormalizedPoint(
                    code=code,
                    name_zh=tp.get("name", code),
                    name_en=tp.get("pinyin", code),
                    pinyin=tp.get("pinyin", ""),
                    meridian_code=tp.get("meridianId", ""),
                    region=tp.get("region", "general"),
                    raw_position=tp.get("originalPosition", pos),
                    canonical_position=pos,
                    normal=tp.get("normal", [0.0, 0.0, 1.0]),
                    surface_distance_mm=0.0,
                    status=status,
                    source=self.get_source_name(),
                    indications=[],
                    location_desc=tp.get("positionProvenance", ""),
                    extra={"base_code": code, "side": "midline" if tp.get("midline") else "unilateral"},
                )

        return points

    def extract_meridians(self) -> Dict[str, NormalizedMeridian]:
        meridians: Dict[str, NormalizedMeridian] = {}

        m_def_path = self.upstream_dir / "app" / "meridians.json"
        color_map: Dict[str, str] = {}
        name_zh_map: Dict[str, str] = {}
        if m_def_path.exists():
            with open(m_def_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    color_map[item.get("id", "")] = item.get("color", "#ff4444")
                    name_zh_map[item.get("id", "")] = item.get("name", "")

        surf_path = self.upstream_dir / "app" / "meridian-surface.json"
        if not surf_path.exists():
            return meridians

        with open(surf_path, "r", encoding="utf-8") as f:
            surf_data = json.load(f)

        for p_item in surf_data.get("paths", []):
            m_id = p_item.get("id", "")
            raw_verts = p_item.get("vertices", [])
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
