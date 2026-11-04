"""Dynamic Anchor & Meridian Manager for MSK-Therapy-OS V1.0.
Tracks acupoints across morph and pose transformations, manages manual user adjustments,
provides undo/redo stacks, versioning, and provenance.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AnchorRecord:
    marker_id: str
    code: str
    name_vi: str
    name_en: str
    fma_id: str
    parent_segment: str
    target_mesh_name: str
    local_coordinates: List[float]
    local_normal: List[float]
    barycentric_coordinates: Optional[List[float]] = None
    technical_status: str = "VALID_SURFACE_ANCHOR"
    clinical_verification_status: str = "EXPERT_REVIEW_PENDING"
    source_reference: str = "WHO Standard Acupuncture Point Locations (2008)"
    version: int = 1
    edit_author: str = "system"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DynamicAnchorManager:
    """Manages dynamic acupoint anchors, manual adjustments, undo/redo, and meridian curves."""

    DEFAULT_ANCHORS: Dict[str, Dict[str, Any]] = {
        "LI4": {
            "code": "LI4",
            "name_vi": "Hợp Cốc",
            "name_en": "Hegu",
            "fma_id": "FMA:23910",
            "parent_segment": "hand.R",
            "target_mesh_name": "Metacarpal_2_R",
            "local_coordinates": [-0.280, 0.835, 0.035],
            "local_normal": [-0.7, 0.0, 0.7],
            "barycentric_coordinates": [0.5, 0.5, 0.0],
            "source_reference": "WHO Standard Acupuncture Point Locations (2008), p. 33"
        },
        "LI14": {
            "code": "LI14",
            "name_vi": "Tí Nhu",
            "name_en": "Binao",
            "fma_id": "FMA:23412",
            "parent_segment": "upper_arm.R",
            "target_mesh_name": "Humerus_R",
            "local_coordinates": [-0.210, 1.250, -0.015],
            "local_normal": [-0.8, 0.0, 0.6],
            "barycentric_coordinates": [0.4, 0.3, 0.3],
            "source_reference": "WHO Standard Acupuncture Point Locations (2008), p. 41"
        },
        "LI15": {
            "code": "LI15",
            "name_vi": "Kiên Ngung",
            "name_en": "Jianyu",
            "fma_id": "FMA:23240",
            "parent_segment": "clavicle.R",
            "target_mesh_name": "Scapula_R",
            "local_coordinates": [-0.160, 1.410, -0.020],
            "local_normal": [0.0, 0.7, 0.7],
            "barycentric_coordinates": [0.33, 0.33, 0.34],
            "source_reference": "WHO Standard Acupuncture Point Locations (2008), p. 42"
        }
    }

    # Meridian pathway for Large Intestine channel (LI4 -> LI11 -> LI14 -> LI15)
    MERIDIAN_WAYPOINTS = [
        {"code": "LI4", "segment": "hand.R", "pos": [-0.280, 0.835, 0.035]},
        {"code": "LI11", "segment": "forearm.R", "pos": [-0.215, 1.115, 0.015]},
        {"code": "LI14", "segment": "upper_arm.R", "pos": [-0.210, 1.250, -0.015]},
        {"code": "LI15", "segment": "clavicle.R", "pos": [-0.160, 1.410, -0.020]},
    ]

    def __init__(self):
        self.anchors: Dict[str, AnchorRecord] = {}
        self.undo_stack: List[Dict[str, AnchorRecord]] = []
        self.redo_stack: List[Dict[str, AnchorRecord]] = []
        self._init_defaults()

    def _init_defaults(self):
        for code, spec in self.DEFAULT_ANCHORS.items():
            self.anchors[code] = AnchorRecord(
                marker_id=f"marker_{code}",
                code=code,
                name_vi=spec["name_vi"],
                name_en=spec["name_en"],
                fma_id=spec["fma_id"],
                parent_segment=spec["parent_segment"],
                target_mesh_name=spec["target_mesh_name"],
                local_coordinates=list(spec["local_coordinates"]),
                local_normal=list(spec["local_normal"]),
                barycentric_coordinates=list(spec["barycentric_coordinates"]),
                source_reference=spec["source_reference"]
            )

    def get_anchor(self, code: str) -> Optional[AnchorRecord]:
        return self.anchors.get(code)

    def get_all_anchors(self) -> Dict[str, Dict[str, Any]]:
        return {code: a.to_dict() for code, a in self.anchors.items()}

    def adjust_anchor(
        self,
        code: str,
        new_local_coords: List[float],
        author: str = "practitioner",
        reason: str = "Clinical palpation refinement"
    ) -> AnchorRecord:
        """Manually adjust anchor coordinates with undo history tracking."""
        if code not in self.anchors:
            raise KeyError(f"Acupoint '{code}' not registered.")

        # Save snapshot for undo
        self.undo_stack.append(copy.deepcopy(self.anchors))
        self.redo_stack.clear()

        cur = self.anchors[code]
        self.anchors[code] = AnchorRecord(
            marker_id=cur.marker_id,
            code=code,
            name_vi=cur.name_vi,
            name_en=cur.name_en,
            fma_id=cur.fma_id,
            parent_segment=cur.parent_segment,
            target_mesh_name=cur.target_mesh_name,
            local_coordinates=[round(float(c), 6) for c in new_local_coords],
            local_normal=list(cur.local_normal),
            barycentric_coordinates=None,  # Manual adjustment overrides standard barycentric
            technical_status="MANUALLY_ADJUSTED",
            clinical_verification_status="EXPERT_REVIEW_PENDING",
            source_reference=f"Manual edit by {author}: {reason}",
            version=cur.version + 1,
            edit_author=author
        )
        return self.anchors[code]

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        self.redo_stack.append(copy.deepcopy(self.anchors))
        self.anchors = self.undo_stack.pop()
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        self.undo_stack.append(copy.deepcopy(self.anchors))
        self.anchors = self.redo_stack.pop()
        return True

    def get_meridian_pathway(self) -> List[Dict[str, Any]]:
        """Return the Large Intestine channel waypoints with current coordinates."""
        pathway = []
        for wp in self.MERIDIAN_WAYPOINTS:
            c = wp["code"]
            if c in self.anchors:
                pos = self.anchors[c].local_coordinates
            else:
                pos = wp["pos"]
            pathway.append({
                "code": c,
                "parent_segment": wp["segment"],
                "local_coordinates": pos
            })
        return pathway

    def get_summary(self) -> Dict[str, Any]:
        return {
            "anchors": self.get_all_anchors(),
            "meridian_waypoints": self.get_meridian_pathway(),
            "undo_available_count": len(self.undo_stack),
            "redo_available_count": len(self.redo_stack),
        }
