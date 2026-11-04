"""
MSK-Therapy-OS V1.2 — Anatomical Binding System: Surface Anchor Binding
=======================================================================
Manages the anatomical correspondence of acupoint surface landmarks
(LI4, LI11, LI14, LI15) attached simultaneously to:
1. The canonical kinematic skeleton bones (for motion hierarchy).
2. The authentic underlying bone/muscle mesh landmarks.
3. The parametric skin surface (dynamic normal projection).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from msk_therapy_os.canonical_skeleton_adapter import Laterality


@dataclass
class SurfaceAnchorEntry:
    code: str                           # e.g., "LI4"
    name_vi: str                        # "Hợp Cốc"
    name_en: str                        # "Hegu"
    meridian: str                       # "Thủ Dương Minh Đại Trường Kinh (LI)"
    parent_bone: str                    # Canonical bone ID (e.g., "hand_r")
    reference_anatomy_id: str           # BodyParts3D ID (e.g., "FJ3352")
    reference_structure_name: str       # e.g., "Right second metacarpal bone"
    local_offset_m: Tuple[float, float, float]  # Local offset in meters
    surface_normal: Tuple[float, float, float]  # Unit normal vector
    cun_measurement: str               # Anatomical proportional reference
    laterality: Laterality
    verification_status: str = "REGISTERED_ACTIVE"
    clinical_safety_notice: str = "ENGINEERING_RESEARCH_ONLY; NOT_FOR_ACUPUNCTURE_PRACTICE"


class SurfaceAnchorAdapter:
    """Manages surface anchor points and their real-time evaluation across kinematic changes."""

    def __init__(self):
        self._anchors: Dict[str, SurfaceAnchorEntry] = {}
        self._init_canonical_anchors()

    def _init_canonical_anchors(self):
        # 1. LI4 (Hợp Cốc) - Dorsum of hand, radial side of midpoint of 2nd metacarpal bone
        self._anchors["LI4"] = SurfaceAnchorEntry(
            code="LI4",
            name_vi="Hợp Cốc",
            name_en="Hegu",
            meridian="Large Intestine (LI)",
            parent_bone="hand_r",
            reference_anatomy_id="FJ3352",
            reference_structure_name="Right second metacarpal bone",
            local_offset_m=(0.015, 0.025, 0.012),
            surface_normal=(0.0, 0.0, 1.0),
            cun_measurement="Giữa xương bàn ngón 2 và ngón 1, hơi chếch về phía xương bàn 2",
            laterality=Laterality.RIGHT,
        )

        # 2. LI11 (Khúc Trì) - At lateral end of transverse cubital crease when elbow is flexed
        self._anchors["LI11"] = SurfaceAnchorEntry(
            code="LI11",
            name_vi="Khúc Trì",
            name_en="Quchi",
            meridian="Large Intestine (LI)",
            parent_bone="lowerarm_r",
            reference_anatomy_id="FJ3349",
            reference_structure_name="Right radius & lateral humeral epicondyle",
            local_offset_m=(-0.020, 0.005, 0.035),
            surface_normal=(-0.707, 0.0, 0.707),
            cun_measurement="Nếp gấp khuỷu ngoài khi gập khuỷu tay 90 độ",
            laterality=Laterality.RIGHT,
        )

        # 3. LI14 (Tí Nhu) - Lateral aspect of arm, 7 cun superior to LI11, at deltoid insertion
        self._anchors["LI14"] = SurfaceAnchorEntry(
            code="LI14",
            name_vi="Tí Nhu",
            name_en="Binao",
            meridian="Large Intestine (LI)",
            parent_bone="upperarm_r",
            reference_anatomy_id="FJ3368",
            reference_structure_name="Right humerus (deltoid tuberosity)",
            local_offset_m=(-0.040, 0.120, 0.010),
            surface_normal=(-1.0, 0.0, 0.0),
            cun_measurement="Trên đường nối LI11 và LI15, cách LI11 7 thốn, đầu dưới cơ delta",
            laterality=Laterality.RIGHT,
        )

        # 4. LI15 (Kiên Ngung) - In depression anterior and inferior to acromion
        self._anchors["LI15"] = SurfaceAnchorEntry(
            code="LI15",
            name_vi="Kiên Ngung",
            name_en="Jianyu",
            meridian="Large Intestine (LI)",
            parent_bone="clavicle_r",
            reference_anatomy_id="FJ3362",
            reference_structure_name="Right clavicle & acromion",
            local_offset_m=(-0.140, -0.010, 0.025),
            surface_normal=(0.0, 1.0, 0.0),
            cun_measurement="Hõm dưới mỏm cùng vai khi cánh tay dạng ngang",
            laterality=Laterality.RIGHT,
        )

    def get_anchor(self, code: str) -> Optional[SurfaceAnchorEntry]:
        return self._anchors.get(code)

    def list_anchors(self) -> List[Dict[str, Any]]:
        return [asdict(a) for a in self._anchors.values()]


surface_anchor_adapter = SurfaceAnchorAdapter()
