"""Authentic BodyParts3D FJ2810 skin mesh parser and spatial distance query engine."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class BodyPartsSkinMesh:
    """Authentic BodyParts3D FJ2810 Skin Mesh Geometry with spatial index for sub-millisecond queries."""

    EXPECTED_BIN_SHA256 = "4a959d998acd35cf88518a0f2f8ab99b42d9f69c7ce0d6a814df315eeac807ac"

    def __init__(self, models_dir: Path | str | None = None):
        if models_dir is None:
            self.models_dir = Path(__file__).resolve().parents[1] / "upstream" / "tcm-3d" / "public" / "models"
        else:
            self.models_dir = Path(models_dir)

        atlas_path = self.models_dir / "atlas.json"
        if not atlas_path.exists():
            raise FileNotFoundError(f"atlas.json not found in {self.models_dir}")

        atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
        self.part_meta = next((p for p in atlas.get("parts", []) if p.get("id") == "FJ2810"), None)
        if not self.part_meta:
            raise ValueError("Part FJ2810 (Skin) not found in atlas.json")

        chunk_idx = self.part_meta["chunk"]
        bin_path = self.models_dir / f"body-{chunk_idx}.bin"
        if not bin_path.exists():
            raise FileNotFoundError(f"body-{chunk_idx}.bin not found in {self.models_dir}")

        bin_bytes = bin_path.read_bytes()
        self.bin_sha256 = hashlib.sha256(bin_bytes).hexdigest()

        # Unpack vertices and indices
        v_offset = self.part_meta["positions"]
        v_count = self.part_meta["vertexCount"]
        v_raw = struct.unpack_from(f"<{v_count * 3}f", bin_bytes, v_offset)
        self.vertices = np.array(v_raw, dtype=np.float32).reshape(-1, 3)

        i_offset = self.part_meta["indices"]
        i_count = self.part_meta["indexCount"]
        i_raw = struct.unpack_from(f"<{i_count}I", bin_bytes, i_offset)
        self.indices = np.array(i_raw, dtype=np.uint32).reshape(-1, 3)
        self.num_faces = len(self.indices)

        # Precompute triangle vertices
        self.tri_a = self.vertices[self.indices[:, 0]]
        self.tri_b = self.vertices[self.indices[:, 1]]
        self.tri_c = self.vertices[self.indices[:, 2]]

        # Compute face normals
        ab = self.tri_b - self.tri_a
        ac = self.tri_c - self.tri_a
        cross = np.cross(ab, ac)
        norms = np.linalg.norm(cross, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.face_normals = cross / norms

        # Triangle centroids
        self.centroids = (self.tri_a + self.tri_b + self.tri_c) / 3.0

        # Build 3D spatial hash grid (40mm cell size)
        self.cell_size = 0.04
        self.min_bound = np.min(self.vertices, axis=0) - self.cell_size
        self.grid: Dict[Tuple[int, int, int], List[int]] = {}
        for f in range(self.num_faces):
            c = self.centroids[f]
            cell_idx = tuple(np.floor((c - self.min_bound) / self.cell_size).astype(int))
            self.grid.setdefault(cell_idx, []).append(f)

    @staticmethod
    def _closest_point_on_triangle(p: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
        ab = b - a
        ac = c - a
        ap = p - a

        d1 = np.dot(ab, ap)
        d2 = np.dot(ac, ap)
        if d1 <= 0 and d2 <= 0:
            return a

        bp = p - b
        d3 = np.dot(ab, bp)
        d4 = np.dot(ac, bp)
        if d3 >= 0 and d4 <= d3:
            return b

        vc = d1 * d4 - d3 * d2
        if vc <= 0 and d1 >= 0 and d3 <= 0:
            v = d1 / (d1 - d3)
            return a + v * ab

        cp = p - c
        d5 = np.dot(ab, cp)
        d6 = np.dot(ac, cp)
        if d6 >= 0 and d5 <= d6:
            return c

        vb = d5 * d2 - d1 * d6
        if vb <= 0 and d2 >= 0 and d6 <= 0:
            w = d2 / (d2 - d6)
            return a + w * ac

        va = d3 * d6 - d5 * d4
        if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
            w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
            return b + w * (c - b)

        denom = 1.0 / (va + vb + vc)
        v = vb * denom
        w = vc * denom
        return a + ab * v + ac * w

    def query_point(
        self,
        point: List[float] | np.ndarray,
        point_normal: Optional[List[float] | np.ndarray] = None,
        recorded_face_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compute exact point-to-triangle distance, signed distance, true face, and normal alignment."""
        pt = np.asarray(point, dtype=np.float32)

        cell_idx = tuple(np.floor((pt - self.min_bound) / self.cell_size).astype(int))
        candidate_faces = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    neighbor = (cell_idx[0] + dx, cell_idx[1] + dy, cell_idx[2] + dz)
                    if neighbor in self.grid:
                        candidate_faces.extend(self.grid[neighbor])

        if not candidate_faces:
            dists_sq = np.sum((self.centroids - pt) ** 2, axis=1)
            candidate_faces = np.argsort(dists_sq)[:60].tolist()

        best_dist = 1e9
        best_f = -1
        best_q = None

        for f in candidate_faces:
            q = self._closest_point_on_triangle(pt, self.tri_a[f], self.tri_b[f], self.tri_c[f])
            d = np.linalg.norm(pt - q)
            if d < best_dist:
                best_dist = d
                best_f = f
                best_q = q

        fn = self.face_normals[best_f]
        vec = pt - best_q

        # Normal alignment and signed distance
        normal_dot = None
        if point_normal is not None:
            pn = np.asarray(point_normal, dtype=np.float32)
            pn_norm = np.linalg.norm(pn)
            if pn_norm > 0:
                pn = pn / pn_norm
                normal_dot = float(np.dot(pn, fn))
                # Signed distance along point's outward normal: positive = outside, negative = penetrating
                signed_dist_mm = float(np.dot(vec, pn) * 1000.0)
            else:
                is_outside = np.dot(vec, fn) >= 0
                signed_dist_mm = float((best_dist if is_outside else -best_dist) * 1000.0)
        else:
            is_outside = np.dot(vec, fn) >= 0
            signed_dist_mm = float((best_dist if is_outside else -best_dist) * 1000.0)

        # Check recorded face index if provided
        face_index_match = None
        face_index_dist_mm = None
        if recorded_face_index is not None and 0 <= recorded_face_index < self.num_faces:
            face_index_match = (recorded_face_index == best_f)
            q_rec = self._closest_point_on_triangle(
                pt,
                self.tri_a[recorded_face_index],
                self.tri_b[recorded_face_index],
                self.tri_c[recorded_face_index],
            )
            face_index_dist_mm = float(np.linalg.norm(pt - q_rec) * 1000.0)

        return {
            "closest_point": [float(c) for c in best_q],
            "distance_mm": round(float(best_dist * 1000.0), 3),
            "signed_distance_mm": round(float(signed_dist_mm), 3),
            "closest_face_index": int(best_f),
            "mesh_face_normal": [round(float(c), 5) for c in fn],
            "normal_alignment_dot": round(normal_dot, 3) if normal_dot is not None else None,
            "recorded_face_index": recorded_face_index,
            "recorded_face_match": face_index_match,
            "recorded_face_dist_mm": round(face_index_dist_mm, 3) if face_index_dist_mm is not None else None,
            "mesh_id": "FJ2810",
            "model_sha256": self.bin_sha256,
        }
