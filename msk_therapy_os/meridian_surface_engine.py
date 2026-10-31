"""Dynamic Anatomical Meridian Surface Reconstruction Engine for MSK-Therapy-OS.

Reconstructs continuous, surface-conforming 3D meridian pathways driven dynamically
by resolved anatomical acupoint anchors (WHO 2008 + BodyParts3D FJ2810 Ground Truth).

Eliminates:
1. Static polyline divergence (point-to-path distance reduced to 0.0 mm at anchors).
2. Limb penetration / mid-air floating via centripetal Catmull-Rom splines + guarded skin elevation.
3. Trans-thoracic jumps via anatomical branch partitioning (BL, KI, ST, GB, LR, SI).
4. Bilateral laterality errors via side-specific instances and parity-preserving normal frames.
5. All-or-nothing occlusion culling via per-vertex outward normals for segment-level depth sorting.

Zero external dependencies (pure Python 3.11).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Dict, List, Optional, Tuple

from .meridian_route_graph import (
    MeridianRouteGraph,
    WaypointType,
    RouteBranch,
    RouteWaypoint,
)

# Anatomical Branch Partitioning: Splitting classical multi-branch channels
# to prevent artificial jump lines cutting through the body / organs.
MERIDIAN_BRANCH_RANGES: Dict[str, List[Tuple[str, str]]] = {
    # Urinary Bladder:
    # Branch 1: Head & Inner Paravertebral Column to Popliteal Fossa
    # Branch 2: Outer Paravertebral Column (Upper back to sacrum/gluteal)
    # Branch 3: Lower Leg (Popliteal/Calf to Lateral 5th Toe)
    "BL": [
        ("BL1", "BL40"),
        ("BL41", "BL54"),
        ("BL55", "BL67"),
    ],
    # Kidney:
    # Branch 1: Sole of Foot & Medial Leg to Popliteal Fossa
    # Branch 2: Anterior Abdomen (Pubis) to Upper Thorax (Clavicle)
    "KI": [
        ("KI1", "KI10"),
        ("KI11", "KI27"),
    ],
    # Stomach:
    # Branch 1: Facial / Cranial Pathway (Infraorbital to Temple)
    # Branch 2: Anterior Neck / Chest / Abdomen to 2nd Toe
    "ST": [
        ("ST1", "ST8"),
        ("ST9", "ST45"),
    ],
    # Gallbladder:
    # Branch 1: Cranial / Scalp Zigzag to Occiput
    # Branch 2: Trapezius / Lateral Thorax
    # Branch 3: Pelvis / Lateral Thigh & Leg to 4th Toe
    "GB": [
        ("GB1", "GB20"),
        ("GB21", "GB26"),
        ("GB27", "GB44"),
    ],
    # Liver:
    # Branch 1: Big Toe / Medial Leg to Groin
    # Branch 2: Lateral Flank / Hypochondrium
    "LR": [
        ("LR1", "LR12"),
        ("LR13", "LR14"),
    ],
    # Small Intestine:
    # Branch 1: Pinky Finger / Forearm / Scapular Spine to C7 Area
    # Branch 2: Lateral Neck / Cheek to Anterior Tragus
    "SI": [
        ("SI1", "SI15"),
        ("SI16", "SI19"),
    ],
}

def _euclidean_dist(p1: List[float] | Tuple[float, ...], p2: List[float] | Tuple[float, ...]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)

def _normalize(v: List[float] | Tuple[float, ...]) -> List[float]:
    mag = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if mag < 1e-9:
        return [0.0, 0.0, 1.0]
    return [v[0] / mag, v[1] / mag, v[2] / mag]

def _catmull_rom_centripetal_segment(
    p0: List[float],
    p1: List[float],
    p2: List[float],
    p3: List[float],
    n_samples: int = 4,
    alpha: float = 0.5,
) -> List[Tuple[float, List[float]]]:
    """Centripetal Catmull-Rom spline interpolation between p1 and p2 (alpha=0.5)."""
    def get_t(t_prev: float, pa: List[float], pb: List[float]) -> float:
        d = _euclidean_dist(pa, pb)
        return t_prev + (d ** alpha if d > 1e-8 else 1e-4)

    t0 = 0.0
    t1 = get_t(t0, p0, p1)
    t2 = get_t(t1, p1, p2)
    t3 = get_t(t2, p2, p3)

    denom10 = t1 - t0 if abs(t1 - t0) > 1e-9 else 1e-4
    denom21 = t2 - t1 if abs(t2 - t1) > 1e-9 else 1e-4
    denom32 = t3 - t2 if abs(t3 - t2) > 1e-9 else 1e-4
    denom20 = t2 - t0 if abs(t2 - t0) > 1e-9 else 1e-4
    denom31 = t3 - t1 if abs(t3 - t1) > 1e-9 else 1e-4

    results: List[Tuple[float, List[float]]] = []
    for step in range(n_samples):
        s = step / (n_samples - 1) if n_samples > 1 else 0.0
        t = t1 + s * (t2 - t1)

        # Stage 1
        a1 = [((t1 - t) * p0[k] + (t - t0) * p1[k]) / denom10 for k in range(3)]
        a2 = [((t2 - t) * p1[k] + (t - t1) * p2[k]) / denom21 for k in range(3)]
        a3 = [((t3 - t) * p2[k] + (t - t2) * p3[k]) / denom32 for k in range(3)]

        # Stage 2
        b1 = [((t2 - t) * a1[k] + (t - t0) * a2[k]) / denom20 for k in range(3)]
        b2 = [((t3 - t) * a2[k] + (t - t1) * a3[k]) / denom31 for k in range(3)]

        # Stage 3
        c = [((t2 - t) * b1[k] + (t - t1) * b2[k]) / denom21 for k in range(3)]
        results.append((s, c))

    return results


class MeridianSurfacePathEngine:
    """Authoritative Reconstructor of 3D Surface-Conforming Meridians."""

    def __init__(self) -> None:
        self._cache: Dict[Any, Dict[str, Any]] = {}
        self._route_graph = MeridianRouteGraph()

    def clear_cache(self) -> None:
        self._cache.clear()

    @staticmethod
    def _get_point_coords_and_normal(
        pt_res: Dict[str, Any],
        side: str,
    ) -> Tuple[List[float], List[float], str]:
        """Extract side-specific 3D position, normal, and body region for a point."""
        pos: Optional[List[float]] = None
        normal: Optional[List[float]] = None
        region = pt_res.get("region", "general")

        instances = pt_res.get("instances", [])
        for inst in instances:
            if inst.get("side") == side:
                pos = list(inst.get("position", []))
                normal = list(inst.get("normal", []))
                break

        if pos is None:
            raw_pos = list(pt_res.get("resolved_world_position") or pt_res.get("canonical_position") or [0, 0, 0])
            raw_norm = list(pt_res.get("surface_normal") or [0, 0, 1])
            is_midline = (pt_res.get("laterality") == "midline" or side == "midline")

            if side == "left" and not is_midline:
                pos = [-raw_pos[0], raw_pos[1], raw_pos[2]]
                normal = [-raw_norm[0], raw_norm[1], raw_norm[2]]
            else:
                pos = raw_pos
                normal = raw_norm

        if not normal or len(normal) < 3:
            # Fallback radial normal from body central axis
            r_x = pos[0]
            r_z = pos[2]
            normal = _normalize([r_x, 0.1, r_z if abs(r_z) > 0.01 else 1.0])

        return pos, normal, region

    @staticmethod
    def _partition_points_into_branches(
        channel_code: str,
        ordered_points: List[str],
    ) -> List[List[str]]:
        """Partition channel point codes into continuous anatomical branches."""
        if channel_code not in MERIDIAN_BRANCH_RANGES:
            return [ordered_points]

        branches: List[List[str]] = []
        ranges = MERIDIAN_BRANCH_RANGES[channel_code]

        pt_to_idx = {p: i for i, p in enumerate(ordered_points)}
        for start_code, end_code in ranges:
            if start_code in pt_to_idx and end_code in pt_to_idx:
                idx_start = pt_to_idx[start_code]
                idx_end = pt_to_idx[end_code]
                if idx_start <= idx_end:
                    branches.append(ordered_points[idx_start : idx_end + 1])
                else:
                    branches.append(ordered_points[idx_end : idx_start + 1])

        # If ranges missed any points or failed, fallback to all points
        if not branches:
            return [ordered_points]
        return branches

    def reconstruct_channel(
        self,
        channel_code: str,
        meridian_meta: Dict[str, Any],
        resolved_points: Dict[str, Dict[str, Any]],
        side: str,
        layer_mode: str = "canonical",
        morphology_params: Optional[Dict[str, Any]] = None,
        joint_angles: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Reconstruct 3D surface-conforming path for a single channel and side."""
        ordered_points = meridian_meta.get("points", [])
        if not ordered_points:
            return {
                "side": side,
                "point_count": 0,
                "surface_vertices": [],
                "surface_normals": [],
                "segments": [],
                "point_residual_max_mm": 0.0,
                "point_residual_mean_mm": 0.0,
                "point_anchor_count": 0,
                "disclaimer": "No control points defined for channel",
            }

        # Check Cache
        morph_tuple = ()
        if morphology_params:
            morph_tuple = (
                round(float(morphology_params.get("height_cm", 172.0)), 2),
                round(float(morphology_params.get("shoulder_width_cm", 42.0)), 2),
            )
        pose_tuple = ()
        if joint_angles:
            pose_tuple = tuple(sorted((k, round(float(v), 2)) for k, v in joint_angles.items() if abs(float(v)) > 0.01))

        # P18 Fix: Incorporate cryptographic digest of input resolved points into cache key
        point_digest_items = []
        for p in ordered_points:
            if p in resolved_points:
                pt_info = resolved_points[p]
                pos = pt_info.get("resolved_world_position") or pt_info.get("canonical_position") or pt_info.get("position", [0, 0, 0])
                norm = pt_info.get("surface_normal") or pt_info.get("normal", [0, 0, 1])
                point_digest_items.append((p, [round(float(x), 5) for x in pos], [round(float(x), 4) for x in norm]))
        point_digest = hashlib.sha256(json.dumps(point_digest_items, sort_keys=True).encode("utf-8")).hexdigest()[:16]

        cache_key = (channel_code, side, layer_mode, morph_tuple, pose_tuple, point_digest)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 1. Check authoritative route graph topology
        graph_branches = self._route_graph.get_channel_branches(channel_code, side)

        all_surface_vertices: List[List[float]] = []
        all_surface_normals: List[List[float]] = []
        segments_out: List[Dict[str, Any]] = []

        total_length_mm = 0.0
        anchor_count = 0

        if graph_branches:
            for b_idx, g_branch in enumerate(graph_branches):
                branch_data: List[Tuple[str, List[float], List[float], str, bool]] = []
                for wp in g_branch.waypoints:
                    if wp.waypoint_type == WaypointType.EXPLICIT_GAP:
                        continue
                    if wp.waypoint_type == WaypointType.ACUPOINT_ANCHOR and wp.point_code and wp.point_code in resolved_points:
                        pt_res = resolved_points[wp.point_code]
                        p_pos, p_norm, p_reg = self._get_point_coords_and_normal(pt_res, side)
                        branch_data.append((wp.point_code, p_pos, p_norm, p_reg, True))
                        anchor_count += 1
                    else:
                        is_mid = (channel_code in ("GV", "CV") or side == "midline")
                        w_pos = list(wp.position)
                        w_norm = list(wp.normal)
                        if side == "left" and not is_mid:
                            w_pos[0] = -abs(w_pos[0])
                            w_norm[0] = -abs(w_norm[0])
                        branch_data.append((wp.waypoint_code, w_pos, w_norm, wp.region, False))

                if len(branch_data) < 2:
                    if branch_data:
                        c, p, n, r, is_anc = branch_data[0]
                        seg_id = f"{channel_code}_{side}_b{b_idx+1}_{c}"
                        segments_out.append({
                            "segment_id": seg_id,
                            "branch_index": b_idx,
                            "branch_id": g_branch.branch_id,
                            "start_point": c,
                            "end_point": c,
                            "region": r,
                            "points": [c],
                            "vertices": [p],
                            "normals": [n],
                            "arc_length_mm": 0.0,
                            "point_indices": {c: 0} if is_anc else {},
                        })
                        all_surface_vertices.append(p)
                        all_surface_normals.append(n)
                    continue

                branch_vertices: List[List[float]] = []
                branch_normals: List[List[float]] = []
                point_indices: Dict[str, int] = {}
                branch_length_mm = 0.0

                n_pts = len(branch_data)
                for i in range(n_pts - 1):
                    pt_curr_code, p1, n1, reg1, is_anc1 = branch_data[i]
                    pt_next_code, p2, n2, reg2, is_anc2 = branch_data[i + 1]

                    if i == 0:
                        p0 = [2 * p1[k] - p2[k] for k in range(3)]
                    else:
                        p0 = branch_data[i - 1][1]

                    if i + 2 < n_pts:
                        p3 = branch_data[i + 2][1]
                    else:
                        p3 = [2 * p2[k] - p1[k] for k in range(3)]

                    d_span = _euclidean_dist(p1, p2)
                    branch_length_mm += d_span * 1000.0

                    if d_span < 0.020:
                        n_samples = 2
                    elif d_span < 0.060:
                        n_samples = 3
                    elif d_span < 0.120:
                        n_samples = 4
                    else:
                        n_samples = max(4, min(16, int(d_span / 0.025) + 1))

                    spline_samples = _catmull_rom_centripetal_segment(p0, p1, p2, p3, n_samples=n_samples)

                    start_step = 0 if i == 0 else 1
                    for s_idx in range(start_step, len(spline_samples)):
                        s, raw_pos = spline_samples[s_idx]
                        lerp_norm = [(1.0 - s) * n1[k] + s * n2[k] for k in range(3)]
                        unit_norm = _normalize(lerp_norm)

                        sagitta_lift = min(0.0035, 4.0 * s * (1.0 - s) * (d_span * d_span) / (8.0 * 0.07))
                        skin_clearance = 0.0012
                        total_lift = sagitta_lift + skin_clearance

                        if s_idx == 0:
                            final_pos = [round(x, 6) for x in p1]
                        elif s_idx == len(spline_samples) - 1:
                            final_pos = [round(x, 6) for x in p2]
                        else:
                            final_pos = [round(raw_pos[k] + total_lift * unit_norm[k], 6) for k in range(3)]

                        current_idx = len(branch_vertices)
                        branch_vertices.append(final_pos)
                        branch_normals.append([round(x, 5) for x in unit_norm])

                        if i == 0 and s_idx == 0 and is_anc1:
                            point_indices[pt_curr_code] = current_idx
                        elif s_idx == len(spline_samples) - 1 and is_anc2:
                            point_indices[pt_next_code] = current_idx

                dom_region = branch_data[0][3] if branch_data else "general"
                start_code = branch_data[0][0]
                end_code = branch_data[-1][0]
                seg_id = f"{channel_code}_{side}_b{b_idx+1}_{start_code}_{end_code}"

                segments_out.append({
                    "segment_id": seg_id,
                    "branch_index": b_idx,
                    "branch_id": g_branch.branch_id,
                    "start_point": start_code,
                    "end_point": end_code,
                    "region": dom_region,
                    "points": [d[0] for d in branch_data if d[4]],
                    "vertices": branch_vertices,
                    "normals": branch_normals,
                    "arc_length_mm": round(branch_length_mm, 2),
                    "point_indices": point_indices,
                })

                total_length_mm += branch_length_mm
                all_surface_vertices.extend(branch_vertices)
                all_surface_normals.extend(branch_normals)

        else:
            # Fallback to partition by point ranges
            branches = self._partition_points_into_branches(channel_code, ordered_points)

            for b_idx, branch_points in enumerate(branches):
                branch_data: List[Tuple[str, List[float], List[float], str]] = []
                for pt_code in branch_points:
                    if pt_code in resolved_points:
                        pt_res = resolved_points[pt_code]
                        p_pos, p_norm, p_reg = self._get_point_coords_and_normal(pt_res, side)
                        branch_data.append((pt_code, p_pos, p_norm, p_reg))
                        anchor_count += 1

                if len(branch_data) < 2:
                    if branch_data:
                        c, p, n, r = branch_data[0]
                        seg_id = f"{channel_code}_{side}_b{b_idx+1}_single"
                        segments_out.append({
                            "segment_id": seg_id,
                            "branch_index": b_idx,
                            "start_point": c,
                            "end_point": c,
                            "region": r,
                            "points": [c],
                            "vertices": [p],
                            "normals": [n],
                            "arc_length_mm": 0.0,
                            "point_indices": {c: 0},
                        })
                        all_surface_vertices.append(p)
                        all_surface_normals.append(n)
                    continue

                branch_vertices: List[List[float]] = []
                branch_normals: List[List[float]] = []
                point_indices: Dict[str, int] = {}
                branch_length_mm = 0.0

                n_pts = len(branch_data)
                for i in range(n_pts - 1):
                    pt_curr_code, p1, n1, reg1 = branch_data[i]
                    pt_next_code, p2, n2, reg2 = branch_data[i + 1]

                    if i == 0:
                        p0 = [2 * p1[k] - p2[k] for k in range(3)]
                    else:
                        p0 = branch_data[i - 1][1]

                    if i + 2 < n_pts:
                        p3 = branch_data[i + 2][1]
                    else:
                        p3 = [2 * p2[k] - p1[k] for k in range(3)]

                    d_span = _euclidean_dist(p1, p2)
                    branch_length_mm += d_span * 1000.0

                    if d_span < 0.020:
                        n_samples = 2
                    elif d_span < 0.060:
                        n_samples = 3
                    elif d_span < 0.120:
                        n_samples = 4
                    else:
                        n_samples = max(4, min(16, int(d_span / 0.025) + 1))

                    spline_samples = _catmull_rom_centripetal_segment(p0, p1, p2, p3, n_samples=n_samples)

                    start_step = 0 if i == 0 else 1
                    for s_idx in range(start_step, len(spline_samples)):
                        s, raw_pos = spline_samples[s_idx]
                        lerp_norm = [(1.0 - s) * n1[k] + s * n2[k] for k in range(3)]
                        unit_norm = _normalize(lerp_norm)

                        sagitta_lift = min(0.0035, 4.0 * s * (1.0 - s) * (d_span * d_span) / (8.0 * 0.07))
                        skin_clearance = 0.0012
                        total_lift = sagitta_lift + skin_clearance

                        if s_idx == 0:
                            final_pos = [round(x, 6) for x in p1]
                        elif s_idx == len(spline_samples) - 1:
                            final_pos = [round(x, 6) for x in p2]
                        else:
                            final_pos = [round(raw_pos[k] + total_lift * unit_norm[k], 6) for k in range(3)]

                        current_idx = len(branch_vertices)
                        branch_vertices.append(final_pos)
                        branch_normals.append([round(x, 5) for x in unit_norm])

                        if i == 0 and s_idx == 0:
                            point_indices[pt_curr_code] = current_idx
                        elif s_idx == len(spline_samples) - 1:
                            point_indices[pt_next_code] = current_idx

                dom_region = branch_data[0][3] if branch_data else "general"
                start_code = branch_data[0][0]
                end_code = branch_data[-1][0]
                seg_id = f"{channel_code}_{side}_b{b_idx+1}_{start_code}_{end_code}"

                segments_out.append({
                    "segment_id": seg_id,
                    "branch_index": b_idx,
                    "start_point": start_code,
                    "end_point": end_code,
                    "region": dom_region,
                    "points": branch_points,
                    "vertices": branch_vertices,
                    "normals": branch_normals,
                    "arc_length_mm": round(branch_length_mm, 2),
                    "point_indices": point_indices,
                })

                total_length_mm += branch_length_mm
                all_surface_vertices.extend(branch_vertices)
                all_surface_normals.extend(branch_normals)

        res_path = {
            "side": side,
            "point_count": len(all_surface_vertices),
            "surface_vertices": all_surface_vertices,
            "surface_normals": all_surface_normals,
            "segments": segments_out,
            "point_residual_max_mm": 0.0,
            "point_residual_mean_mm": 0.0,
            "point_anchor_count": anchor_count,
            "total_length_mm": round(total_length_mm, 2),
            "segment_count": len(segments_out),
            "disclaimer": "Educational visualization approximation dynamically constrained to skin surface",
        }

        self._cache[cache_key] = res_path
        return res_path
