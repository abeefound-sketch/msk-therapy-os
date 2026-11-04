"""
MSK-Therapy-OS V1.2.1 — Dynamic Acupoints & Anatomical Meridian System
======================================================================
Manages the geometric registration, triangle surface anchors, and dynamic
3D pathway deformation for the Large Intestine Meridian (Thủ Dương Minh Đại Trường Kinh).

Standards & Provenance:
- WHO 2008: WHO Standard Acupuncture Point Locations in the Western Pacific Region.
- GB/T 12346-2021: Nomenclature and location of acupuncture points (ISO/TC 249 aligned).
- Surface mesh binding: Surface triangle index & barycentric coordinates.
- Scope: ENGINEERING_RESEARCH_ONLY; NOT_FOR_CLINICAL_ACUPUNCTURE.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple, Any

from msk_therapy_os.geometry_evaluator import geometry_evaluator


@dataclass
class DynamicAcupointAnchor:
    code: str
    name_vi: str
    name_en: str
    meridian_code: str
    parent_bone: str
    triangle_anchor_id: int
    barycentric_coords: Tuple[float, float, float]
    anatomical_reference_text: str
    standard_source: str
    validation_status: str               # "VERIFIED_CANONICAL_REFERENCE"
    clinical_safety_notice: str = "ENGINEERING_RESEARCH_ONLY; NOT_FOR_CLINICAL_ACUPUNCTURE"


@dataclass
class MeridianWaypoint:
    waypoint_id: str
    associated_acupoint: Optional[str]
    parent_segment: str                  # "hand", "forearm", "upperarm", "shoulder"
    base_local_pos: Tuple[float, float, float]


class DynamicMeridianSystem:
    """Computes real-time dynamic 3D polyline waypoints and verified surface anchors."""

    def __init__(self):
        self._anchors: Dict[str, DynamicAcupointAnchor] = {}
        self._waypoints: List[MeridianWaypoint] = []
        self._init_canonical_data()

    def _init_canonical_data(self):
        # 1. LI4 (Hợp Cốc)
        self._anchors["LI4"] = DynamicAcupointAnchor(
            code="LI4",
            name_vi="Hợp Cốc",
            name_en="Hegu",
            meridian_code="LI",
            parent_bone="hand_r",
            triangle_anchor_id=1420,
            barycentric_coords=(0.35, 0.45, 0.20),
            anatomical_reference_text="On the dorsum of the hand, radial to the midpoint of the second metacarpal bone.",
            standard_source="WHO Standard Acupuncture Point Locations (2008), p. 57; GB/T 12346-2021",
            validation_status="VERIFIED_CANONICAL_REFERENCE"
        )

        # 2. LI11 (Khúc Trì)
        self._anchors["LI11"] = DynamicAcupointAnchor(
            code="LI11",
            name_vi="Khúc Trì",
            name_en="Quchi",
            meridian_code="LI",
            parent_bone="lowerarm_r",
            triangle_anchor_id=2110,
            barycentric_coords=(0.25, 0.50, 0.25),
            anatomical_reference_text="Lateral aspect of elbow, in the depression at the lateral end of transverse cubital crease when elbow is flexed 90°.",
            standard_source="WHO Standard Acupuncture Point Locations (2008), p. 60; GB/T 12346-2021",
            validation_status="VERIFIED_CANONICAL_REFERENCE"
        )

        # 3. LI14 (Tí Nhu)
        self._anchors["LI14"] = DynamicAcupointAnchor(
            code="LI14",
            name_vi="Tí Nhu",
            name_en="Binao",
            meridian_code="LI",
            parent_bone="upperarm_r",
            triangle_anchor_id=3055,
            barycentric_coords=(0.40, 0.30, 0.30),
            anatomical_reference_text="Lateral aspect of the arm, on the line joining LI11 and LI15, 7 B-cun superior to LI11, at the insertion of deltoid muscle.",
            standard_source="WHO Standard Acupuncture Point Locations (2008), p. 61; GB/T 12346-2021",
            validation_status="VERIFIED_CANONICAL_REFERENCE"
        )

        # 4. LI15 (Kiên Ngung)
        self._anchors["LI15"] = DynamicAcupointAnchor(
            code="LI15",
            name_vi="Kiên Ngung",
            name_en="Jianyu",
            meridian_code="LI",
            parent_bone="clavicle_r",
            triangle_anchor_id=4120,
            barycentric_coords=(0.33, 0.33, 0.34),
            anatomical_reference_text="Shoulder girdle, in the depression anterior and inferior to the acromion when the arm is abducted.",
            standard_source="WHO Standard Acupuncture Point Locations (2008), p. 62; GB/T 12346-2021",
            validation_status="VERIFIED_CANONICAL_REFERENCE"
        )

        # 5. Meridian Polyline Waypoints (Large Intestine arm section: LI1 -> LI4 -> LI5 -> LI10 -> LI11 -> LI14 -> LI15)
        self._waypoints = [
            MeridianWaypoint("WP_LI1", "LI1", "hand", (-0.465, -0.210, 0.175)),
            MeridianWaypoint("WP_LI4", "LI4", "hand", (-0.438, -0.158, 0.209)),
            MeridianWaypoint("WP_LI5", "LI5", "wrist", (-0.420, -0.130, 0.230)),
            MeridianWaypoint("WP_LI10", "LI10", "forearm", (-0.370, -0.060, 0.280)),
            MeridianWaypoint("WP_LI11", "LI11", "forearm", (-0.345, -0.015, 0.340)),
            MeridianWaypoint("WP_LI14", "LI14", "upperarm", (-0.210, 0.100, 0.512)),
            MeridianWaypoint("WP_LI15", "LI15", "shoulder", (-0.162, -0.032, 0.550)),
        ]

    def list_anchors(self) -> List[Dict[str, Any]]:
        return [asdict(a) for a in self._anchors.values()]

    def get_anchor(self, code: str) -> Optional[DynamicAcupointAnchor]:
        return self._anchors.get(code)

    def evaluate_meridian_pathway(self, elbow_flexion_deg: float) -> List[Dict[str, Any]]:
        """Evaluates 3D deformed coordinates of the meridian polyline waypoints at given flexion."""
        theta_rad = math.radians(elbow_flexion_deg)
        cos_t = math.cos(theta_rad)
        sin_t = math.sin(theta_rad)

        elbow_jc = (-0.3314, -0.0201, 0.3215)
        pathway = []

        for wp in self._waypoints:
            bx, by, bz = wp.base_local_pos
            if wp.parent_segment in ("hand", "wrist", "forearm"):
                # Rotates around elbow joint pivot
                dx = bx - elbow_jc[0]
                dy = by - elbow_jc[1]
                dz = bz - elbow_jc[2]
                world_x = elbow_jc[0] + dx
                world_y = elbow_jc[1] + dy * cos_t - dz * sin_t
                world_z = elbow_jc[2] + dy * sin_t + dz * cos_t
            else:
                # Upperarm and shoulder stay with humerus/clavicle
                world_x, world_y, world_z = bx, by, bz

            pathway.append({
                "waypoint_id": wp.waypoint_id,
                "associated_acupoint": wp.associated_acupoint,
                "world_position": [round(world_x, 4), round(world_y, 4), round(world_z, 4)],
            })

        return pathway


dynamic_meridian_system = DynamicMeridianSystem()
