"""Adapter for spacejohnlf/tcm-acupoints upstream repository."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAdapter, NormalizedMeridian, NormalizedPoint


class TCMAcupointsAdapter(BaseAdapter):
    """Adapter extracting points and meridians from spacejohnlf/tcm-acupoints."""

    COMMIT_SHA = "04e35abb66585eb29c7250ea8ab5243c8c744f64"
    LICENSE = "MIT (code) / CC BY-SA 4.0 (Z-Anatomy model)"
    REPOSITORY = "https://github.com/spacejohnlf/tcm-acupoints"

    # Transformation constant from pelvis-origin (Y=0, sole=-0.86, crown=+0.86) to canonical floor-origin (sole=0, crown=1.72)
    Y_OFFSET = 0.86

    def __init__(self, upstream_dir: Path | str | None = None):
        if upstream_dir is None:
            self.upstream_dir = Path(__file__).resolve().parents[2] / "upstream" / "tcm-acupoints"
        else:
            self.upstream_dir = Path(upstream_dir)

    def get_source_name(self) -> str:
        return "spacejohnlf/tcm-acupoints"

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": self.get_source_name(),
            "repository": self.REPOSITORY,
            "commit_sha": self.COMMIT_SHA,
            "license": self.LICENSE,
            "mesh_source": "Z-Anatomy Draco-compressed GLB (8MB, 513k vertices)",
            "units": "meters",
            "origin": "pelvis center (sole Y=-0.86m, crown Y=+0.86m)",
            "canonical_transform": f"Y_canonical = Y_tcm + {self.Y_OFFSET:.2f}m",
            "handedness": "right-handed (+X right, +Y up, +Z front)",
            "algorithm": "Directional-cone ray snapping (5-step dot product test) with 12mm normal lift",
            "bilateral": True,
        }

    def _load_texts(self) -> Dict[str, Dict[str, Any]]:
        text_path = self.upstream_dir / "src" / "data" / "point-texts.json"
        if text_path.exists():
            try:
                with open(text_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _parse_ts_data(self) -> tuple[Dict[str, NormalizedPoint], Dict[str, NormalizedMeridian]]:
        ts_path = self.upstream_dir / "src" / "lib" / "acupoint-data.ts"
        if not ts_path.exists():
            return {}, {}

        text = ts_path.read_text(encoding="utf-8")
        texts_dict = self._load_texts()

        # Parse B constants
        b_dict: Dict[str, float] = {}
        b_match = re.search(r"const\s+B\s*=\s*\{([\s\S]*?)\}\s*as\s+const;", text)
        if b_match:
            for line in b_match.group(1).splitlines():
                m = re.match(r"\s*([a-zA-Z0-9_]+)\s*:\s*(-?[0-9\.]+)", line)
                if m:
                    b_dict[m.group(1)] = float(m.group(2))

        # Parse W constants
        w_dict: Dict[str, float] = {}
        w_match = re.search(r"const\s+W\s*=\s*\{([\s\S]*?)\}\s*as\s+const;", text)
        if w_match:
            for line in w_match.group(1).splitlines():
                m = re.match(r"\s*([a-zA-Z0-9_]+)\s*:\s*(-?[0-9\.]+)", line)
                if m:
                    w_dict[m.group(1)] = float(m.group(2))

        def eval_coord(expr_str: str) -> float:
            cleaned = expr_str.strip()
            for k, v in b_dict.items():
                cleaned = re.sub(rf"\bB\.{k}\b", str(v), cleaned)
            for k, v in w_dict.items():
                cleaned = re.sub(rf"\bW\.{k}\b", str(v), cleaned)
            try:
                return float(eval(cleaned, {"__builtins__": {}}, {}))
            except Exception:
                return 0.0

        points: Dict[str, NormalizedPoint] = {}
        meridians: Dict[str, NormalizedMeridian] = {}

        # 1. Parse all points via P(...) calls
        pt_pattern = re.compile(
            r'P\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*\[([^\]]+)\]'
        )

        pts_by_m: Dict[str, List[str]] = {}
        for p_match in pt_pattern.finditer(text):
            p_id, p_name, p_pinyin, p_code, p_mid, coord_str = p_match.groups()
            coords_raw = [eval_coord(c) for c in coord_str.split(",")]
            if len(coords_raw) >= 3:
                raw_pos = [coords_raw[0], coords_raw[1], coords_raw[2]]
                canonical_pos = [coords_raw[0], coords_raw[1] + self.Y_OFFSET, coords_raw[2]]

                m_code = p_mid.upper()
                pts_by_m.setdefault(m_code, []).append(p_code)

                # Look up text details
                lookup_key = p_name[:-1] if p_name.endswith("穴") else p_name
                c_text = texts_dict.get(lookup_key, texts_dict.get(p_name, texts_dict.get(f"{lookup_key}穴", {})))
                overview = c_text.get("overview", "")
                indications = [x.strip() for x in c_text.get("indications", "").split("；") if x.strip()]

                points[p_code] = NormalizedPoint(
                    code=p_code,
                    name_zh=p_name,
                    name_en=p_pinyin,
                    pinyin=p_pinyin,
                    meridian_code=m_code,
                    region="body",
                    raw_position=raw_pos,
                    canonical_position=canonical_pos,
                    normal=[0.0, 0.0, 1.0],
                    surface_distance_mm=12.0,  # tcm-acupoints uses 12mm surface lift
                    status="GEOMETRY_VERIFIED",
                    source=self.get_source_name(),
                    indications=indications,
                    location_desc=overview,
                    extra={
                        "internal_id": p_id,
                        "raw_y": raw_pos[1],
                        "y_offset_applied": self.Y_OFFSET,
                    },
                )

        # 2. Parse meridians
        for m_id in ["lu", "li", "st", "sp", "ht", "si", "bl", "ki", "pc", "te", "gb", "lr", "cv", "gv"]:
            m_code = m_id.upper()
            meta_m = re.search(rf'id:\s*"{m_id}"[\s\S]*?name:\s*"([^"]+)"[\s\S]*?accent:\s*"([^"]+)"', text)
            name_zh = meta_m.group(1) if meta_m else m_code
            accent = meta_m.group(2) if meta_m else "#3d8b7a"

            # Parse path for this meridian: find segment between id: "m_id" and points:
            path_coords: List[List[float]] = []
            segment_match = re.search(rf'id:\s*"{m_id}"[\s\S]*?path:\s*\[([\s\S]*?)\]\s*,\s*points:', text)
            if segment_match:
                for row_match in re.finditer(r"\[([^\]]+)\]", segment_match.group(1)):
                    parts = [x.strip() for x in row_match.group(1).split(",")]
                    if len(parts) >= 3:
                        x = eval_coord(parts[0])
                        y = eval_coord(parts[1])
                        z = eval_coord(parts[2])
                        path_coords.append([x, y + self.Y_OFFSET, z])

            meridians[m_code] = NormalizedMeridian(
                code=m_code,
                name_zh=name_zh,
                name_en=m_code,
                color=accent,
                point_codes=pts_by_m.get(m_code, []),
                paths=[path_coords] if path_coords else [],
                vertex_count=len(path_coords),
                source=self.get_source_name(),
            )

        return points, meridians

    def extract_points(self) -> Dict[str, NormalizedPoint]:
        pts, _ = self._parse_ts_data()
        return pts

    def extract_meridians(self) -> Dict[str, NormalizedMeridian]:
        _, mer = self._parse_ts_data()
        return mer
