"""Adapter for WaterCMY/anatomy-3d upstream repository."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAdapter, NormalizedMeridian, NormalizedPoint


class WaterCMYAdapter(BaseAdapter):
    """Adapter extracting points, meridians, and analytical hull primitives from WaterCMY/anatomy-3d."""

    COMMIT_SHA = "e8d40dca7b1f63f54567395df21d8b1b38a7e840"
    LICENSE = "MIT (code) / CC BY-SA 4.0 (models)"
    REPOSITORY = "https://github.com/WaterCMY/anatomy-3d"

    def __init__(self, upstream_dir: Path | str | None = None):
        if upstream_dir is None:
            self.upstream_dir = Path(__file__).resolve().parents[2] / "upstream" / "anatomy-3d"
        else:
            self.upstream_dir = Path(upstream_dir)

    def get_source_name(self) -> str:
        return "WaterCMY/anatomy-3d"

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": self.get_source_name(),
            "repository": self.REPOSITORY,
            "commit_sha": self.COMMIT_SHA,
            "license": self.LICENSE,
            "mesh_source": "BodyParts3D (9MB glb, 54 muscle groups, 634k triangles)",
            "units": "meters",
            "origin": "ground (Y=0), crown Y≈1.70m",
            "handedness": "right-handed (+X right, +Y up, +Z front)",
            "algorithm": "Analytical Bounding Hull (ellipsoids + capsules) projection + depthTest false overlay",
            "bilateral": True,
        }

    def _parse_html(self) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[List[Any]]]:
        index_path = self.upstream_dir / "index.html"
        if not index_path.exists():
            return [], [], []

        text = index_path.read_text(encoding="utf-8")

        # Extract ACUPOINTS array
        points_raw: List[Dict[str, Any]] = []
        p_match = re.search(r"const\s+ACUPOINTS\s*=\s*(\[[\s\S]*?\]);", text)
        if p_match:
            try:
                # Remove JS comments and trailing commas before JSON parsing
                cleaned = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", "", p_match.group(1))
                # Standardize object keys to JSON quotes
                cleaned = re.sub(r"(\s*)([a-zA-Z0-9_]+)\s*:", r'\1"\2":', cleaned)
                # Remove trailing commas in arrays/objects
                cleaned = re.sub(r",\s*([\]\}])", r"\1", cleaned)
                points_raw = json.loads(cleaned)
            except Exception:
                # Fallback regex extraction per item
                for m in re.finditer(r"id:\s*'([^']+)'\s*,\s*ab:\s*'([^']+)'\s*,\s*py:\s*'([^']*)'\s*,\s*me:\s*'([^']+)'(?:\s*,\s*mi:\s*(\d+))?\s*,\s*p:\s*\[([^\]]+)\](?:\s*,\s*loc:\s*'([^']*)')?(?:\s*,\s*use:\s*'([^']*)')?", text):
                    coords = [float(x.strip()) for x in m.group(6).split(",")]
                    points_raw.append({
                        "id": m.group(1),
                        "ab": m.group(2),
                        "py": m.group(3),
                        "me": m.group(4),
                        "mi": int(m.group(5) or 0),
                        "p": coords,
                        "loc": m.group(7) or "",
                        "use": m.group(8) or "",
                    })

        # Extract MERIDIANS array
        meridians_raw: List[Dict[str, Any]] = []
        m_match = re.search(r"const\s+MERIDIANS\s*=\s*(\[[\s\S]*?\]);", text)
        if m_match:
            try:
                cleaned = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", "", m_match.group(1))
                cleaned = re.sub(r"(\s*)([a-zA-Z0-9_]+)\s*:", r'\1"\2":', cleaned)
                cleaned = re.sub(r",\s*([\]\}])", r"\1", cleaned)
                meridians_raw = json.loads(cleaned)
            except Exception:
                for m in re.finditer(r"k:\s*'([^']+)'\s*,\s*zh:\s*'([^']+)'(?:\s*,\s*s:\s*'([^']*)')?\s*,\s*c:\s*'([^']+)'", text):
                    meridians_raw.append({
                        "k": m.group(1),
                        "zh": m.group(2),
                        "s": m.group(3) or "",
                        "c": m.group(4),
                    })

        # Extract HULL array
        hull_raw: List[List[Any]] = []
        h_match = re.search(r"const\s+HULL\s*=\s*(\[[\s\S]*?\]);", text)
        if h_match:
            try:
                cleaned = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", "", h_match.group(1))
                cleaned = re.sub(r",\s*([\]\}])", r"\1", cleaned)
                # Ensure quotes around string primitives
                cleaned = re.sub(r"\[\s*'([a-z])'", r'["\1"', cleaned)
                hull_raw = json.loads(cleaned)
            except Exception:
                pass

        return points_raw, meridians_raw, hull_raw

    def extract_points(self) -> Dict[str, NormalizedPoint]:
        points_raw, _, _ = self._parse_html()
        points: Dict[str, NormalizedPoint] = {}

        for item in points_raw:
            code = item.get("id", "")
            if not code:
                continue

            pos = item.get("p", [0.0, 0.0, 0.0])
            indications = [x.strip() for x in item.get("use", "").split("·") if x.strip()]

            points[code] = NormalizedPoint(
                code=code,
                name_zh=item.get("ab", ""),
                name_en=item.get("py", ""),
                pinyin=item.get("py", ""),
                meridian_code=item.get("me", ""),
                region="body",
                raw_position=pos,
                canonical_position=pos,  # Same BodyParts3D coordinate space as canonical
                normal=None,
                surface_distance_mm=0.0,
                status="UNVERIFIED",  # WaterCMY points are approximated/hand-placed
                source=self.get_source_name(),
                indications=indications,
                location_desc=item.get("loc", ""),
                extra={
                    "mirror": bool(item.get("mi", 0)),
                },
            )

        return points

    def extract_meridians(self) -> Dict[str, NormalizedMeridian]:
        points_raw, meridians_raw, hull_raw = self._parse_html()
        meridians: Dict[str, NormalizedMeridian] = {}

        # Group point codes by meridian
        pts_by_m: Dict[str, List[str]] = {}
        coords_by_m: Dict[str, List[List[float]]] = {}
        for p in points_raw:
            m_code = p.get("me", "")
            code = p.get("id", "")
            pts_by_m.setdefault(m_code, []).append(code)
            coords_by_m.setdefault(m_code, []).append(p.get("p", [0.0, 0.0, 0.0]))

        for m_item in meridians_raw:
            k = m_item.get("k", "")
            p_codes = pts_by_m.get(k, [])
            path_coords = coords_by_m.get(k, [])

            paths = [path_coords] if path_coords else []
            v_count = len(path_coords)

            meridians[k] = NormalizedMeridian(
                code=k,
                name_zh=m_item.get("zh", k),
                name_en=m_item.get("s", k),
                color=m_item.get("c", "#ff8f8f"),
                point_codes=p_codes,
                paths=paths,
                vertex_count=v_count,
                source=self.get_source_name(),
            )

        return meridians

    def extract_hull(self) -> List[Dict[str, Any]]:
        _, _, hull_raw = self._parse_html()
        primitives = []
        for row in hull_raw:
            if not row:
                continue
            p_type = row[0]
            if p_type == "e" and len(row) >= 7:
                primitives.append({
                    "type": "ellipsoid",
                    "center": [float(row[1]), float(row[2]), float(row[3])],
                    "radii": [float(row[4]), float(row[5]), float(row[6])],
                })
            elif p_type == "c" and len(row) >= 8:
                primitives.append({
                    "type": "capsule",
                    "p0": [float(row[1]), float(row[2]), float(row[3])],
                    "p1": [float(row[4]), float(row[5]), float(row[6])],
                    "radius": float(row[7]),
                })
        return primitives
