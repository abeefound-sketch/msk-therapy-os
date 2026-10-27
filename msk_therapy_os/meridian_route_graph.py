"""Authoritative Meridian Route Graph & Anatomical Topology Engine.

Decouples acupoint anchors from anatomical route waypoints, formalizing:
- Multi-branch channel topologies
- Intermediate turning waypoints around complex anatomical structures (e.g. GB auricle loop)
- Branch junctions (e.g. BL popliteal junction)
- Anatomical corridors (e.g. inter-tendinous grooves, muscular borders)
- Explicit conceptual gaps (INCOMPLETE_ROUTE / CORRIDOR_TRANSITION) without fake chords.

Zero external dependencies (pure Python 3.11).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple


class WaypointType(str, Enum):
    ACUPOINT_ANCHOR = "ACUPOINT_ANCHOR"
    TURNING_WAYPOINT = "TURNING_WAYPOINT"
    CORRIDOR_WAYPOINT = "CORRIDOR_WAYPOINT"
    BRANCH_JUNCTION = "BRANCH_JUNCTION"
    EXPLICIT_GAP = "EXPLICIT_GAP"


@dataclass(frozen=True)
class RouteWaypoint:
    """A geometric knot along an anatomical meridian route."""
    waypoint_id: str
    channel_code: str
    branch_id: str
    sequence_order: int
    waypoint_type: WaypointType
    waypoint_code: str
    position: Tuple[float, float, float]  # [X, Y, Z] in meters on FJ2810 canonical
    normal: Tuple[float, float, float]    # [NX, NY, NZ] unit surface normal
    region: str
    anatomical_structure: str
    point_code: Optional[str] = None      # If this waypoint corresponds to an acupoint
    source_annotation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "waypoint_id": self.waypoint_id,
            "channel_code": self.channel_code,
            "branch_id": self.branch_id,
            "sequence_order": self.sequence_order,
            "waypoint_type": self.waypoint_type.value,
            "waypoint_code": self.waypoint_code,
            "point_code": self.point_code,
            "position": list(self.position),
            "normal": list(self.normal),
            "region": self.region,
            "anatomical_structure": self.anatomical_structure,
            "source_annotation": self.source_annotation,
        }


@dataclass
class RouteBranch:
    """A continuous or bounded branch of an anatomical channel."""
    branch_id: str
    channel_code: str
    branch_name: str
    side: str
    start_anchor: str
    end_anchor: str
    body_region: str
    anatomical_corridor: str
    is_continuous: bool = True
    has_gaps: bool = False
    gap_description: str = ""
    waypoints: List[RouteWaypoint] = field(default_factory=list)
    source_reference: str = "WHO Standard 2008 & BodyParts3D 4.0 FJ2810"
    review_status: str = "VERIFIED_CORRIDOR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "channel_code": self.channel_code,
            "branch_name": self.branch_name,
            "side": self.side,
            "start_anchor": self.start_anchor,
            "end_anchor": self.end_anchor,
            "body_region": self.body_region,
            "anatomical_corridor": self.anatomical_corridor,
            "is_continuous": self.is_continuous,
            "has_gaps": self.has_gaps,
            "gap_description": self.gap_description,
            "waypoint_count": len(self.waypoints),
            "waypoints": [w.to_dict() for w in self.waypoints],
            "source_reference": self.source_reference,
            "review_status": self.review_status,
        }


class MeridianRouteGraph:
    """Manages topological route graphs across all 14 channels."""

    def __init__(self) -> None:
        self._branches: Dict[str, RouteBranch] = {}
        self._build_authoritative_topology()

    def get_branch(self, branch_id: str) -> Optional[RouteBranch]:
        return self._branches.get(branch_id)

    def get_channel_branches(self, channel_code: str, side: str = "right") -> List[RouteBranch]:
        return [
            b for b in self._branches.values()
            if b.channel_code == channel_code and (b.side == side or b.side == "midline")
        ]

    def get_all_branches(self) -> List[RouteBranch]:
        return list(self._branches.values())

    def _build_authoritative_topology(self) -> None:
        """Construct the 14 authoritative route graphs with waypoints and corridors."""
        # ---------------------------------------------------------------------
        # 1. GB: GALLBLADDER MERIDIAN (Shaoyang) - 3 Branches with Auricular Loop
        # ---------------------------------------------------------------------
        # Branch 1: Cranial Auricular Looping Trajectory (GB1 -> GB20)
        # Bends around ear helix & parietal scalp
        gb_b1_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_GB_R_01", channel_code="GB", branch_id="GB_R_B1_CRANIAL", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB1", point_code="GB1",
                position=(0.0650, 1.6250, 0.0750), normal=(0.60, 0.20, 0.77), region="head_neck",
                anatomical_structure="Outer canthus of eye lateral depression", source_annotation="Tongziliao",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_02", channel_code="GB", branch_id="GB_R_B1_CRANIAL", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB2", point_code="GB2",
                position=(0.0680, 1.5850, 0.0450), normal=(0.75, 0.10, 0.65), region="head_neck",
                anatomical_structure="Depression anterior to intertragic notch", source_annotation="Tinghui",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_03", channel_code="GB", branch_id="GB_R_B1_CRANIAL", sequence_order=3,
                waypoint_type=WaypointType.TURNING_WAYPOINT, waypoint_code="WP_GB_TEMPLE_CURVE",
                position=(0.0690, 1.6320, 0.0380), normal=(0.80, 0.15, 0.58), region="head_neck",
                anatomical_structure="Temporal crest curving upward above zygomatic arch",
                source_annotation="Corridor waypoint preventing chord cutting through cranium",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_04", channel_code="GB", branch_id="GB_R_B1_CRANIAL", sequence_order=4,
                waypoint_type=WaypointType.TURNING_WAYPOINT, waypoint_code="WP_GB_EAR_SUPERIOR",
                position=(0.0640, 1.6480, -0.0120), normal=(0.78, 0.30, -0.54), region="head_neck",
                anatomical_structure="Superior border of helix of auricle (Shuaigu GB8 region)",
                source_annotation="Corridor loop above ear",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_05", channel_code="GB", branch_id="GB_R_B1_CRANIAL", sequence_order=5,
                waypoint_type=WaypointType.TURNING_WAYPOINT, waypoint_code="WP_GB_MASTOID_POSTERIOR",
                position=(0.0610, 1.5720, -0.0480), normal=(0.65, 0.15, -0.74), region="head_neck",
                anatomical_structure="Posteroinferior border of mastoid process (Wangu GB12)",
                source_annotation="Curving behind ear down to mastoid",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_06", channel_code="GB", branch_id="GB_R_B1_CRANIAL", sequence_order=6,
                waypoint_type=WaypointType.TURNING_WAYPOINT, waypoint_code="WP_GB_FOREHEAD_RETURN",
                position=(0.0520, 1.6680, 0.0520), normal=(0.55, 0.35, 0.76), region="head_neck",
                anatomical_structure="Ascending back to forehead 1 cun superior to eyebrow (Yangbai GB14)",
                source_annotation="Classical return trajectory to forehead",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_07", channel_code="GB", branch_id="GB_R_B1_CRANIAL", sequence_order=7,
                waypoint_type=WaypointType.TURNING_WAYPOINT, waypoint_code="WP_GB_PARIETAL_TURN",
                position=(0.0480, 1.6920, -0.0180), normal=(0.48, 0.65, -0.59), region="head_neck",
                anatomical_structure="Across parietal scalp toward occiput (Zhengying GB17 / Naokong GB19)",
                source_annotation="Loop across vertex/parietal to occiput",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_08", channel_code="GB", branch_id="GB_R_B1_CRANIAL", sequence_order=8,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB20", point_code="GB20",
                position=(0.0380, 1.5880, -0.0920), normal=(0.35, 0.20, -0.91), region="head_neck",
                anatomical_structure="Depression between trapezius and SCM below occiput", source_annotation="Fengchi",
            ),
        ]

        self._branches["GB_R_B1_CRANIAL"] = RouteBranch(
            branch_id="GB_R_B1_CRANIAL", channel_code="GB", branch_name="Right Cranial Auricular Looping Branch",
            side="right", start_anchor="GB1", end_anchor="GB20", body_region="head_neck",
            anatomical_corridor="Craniofacial outer canthus -> temple -> supra-auricular -> post-auricular -> forehead -> occiput",
            waypoints=gb_b1_waypoints,
        )

        # Branch 2: Shoulder & Lateral Thorax (GB21 -> GB26)
        gb_b2_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_GB_R_21", channel_code="GB", branch_id="GB_R_B2_THORACIC", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB21", point_code="GB21",
                position=(0.0940, 1.4450, -0.0520), normal=(0.30, 0.85, -0.43), region="torso",
                anatomical_structure="Highest point of trapezius muscle midway between C7 and acromion", source_annotation="Jianjing",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_22", channel_code="GB", branch_id="GB_R_B2_THORACIC", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB22", point_code="GB22",
                position=(0.1780, 1.2850, 0.0120), normal=(0.92, 0.15, 0.36), region="torso",
                anatomical_structure="4th intercostal space on mid-axillary line", source_annotation="Yuanye",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_26", channel_code="GB", branch_id="GB_R_B2_THORACIC", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB26", point_code="GB26",
                position=(0.1650, 1.0250, 0.0450), normal=(0.88, 0.10, 0.46), region="torso",
                anatomical_structure="Level with umbilicus directly below free end of 11th rib", source_annotation="Daimai",
            ),
        ]
        self._branches["GB_R_B2_THORACIC"] = RouteBranch(
            branch_id="GB_R_B2_THORACIC", channel_code="GB", branch_name="Right Shoulder & Lateral Thorax Branch",
            side="right", start_anchor="GB21", end_anchor="GB26", body_region="torso",
            anatomical_corridor="Trapezius muscle belly -> mid-axillary lateral thorax -> flank",
            waypoints=gb_b2_waypoints,
        )

        # Branch 3: Pelvis, Lateral Thigh & Leg to Foot (GB27 -> GB44)
        gb_b3_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_GB_R_27", channel_code="GB", branch_id="GB_R_B3_LOWER", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB27", point_code="GB27",
                position=(0.1420, 0.9450, 0.0780), normal=(0.78, 0.15, 0.60), region="pelvis",
                anatomical_structure="Anterior superior iliac spine (ASIS) medial depression", source_annotation="Wushu",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_30", channel_code="GB", branch_id="GB_R_B3_LOWER", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB30", point_code="GB30",
                position=(0.1650, 0.8650, -0.0650), normal=(0.82, 0.12, -0.56), region="pelvis",
                anatomical_structure="Junction of lateral 1/3 and medial 2/3 between greater trochanter and sacral hiatus",
                source_annotation="Huantiao",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_31", channel_code="GB", branch_id="GB_R_B3_LOWER", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB31", point_code="GB31",
                position=(0.1520, 0.6250, 0.0150), normal=(0.94, 0.10, 0.32), region="thigh",
                anatomical_structure="Lateral midline of thigh, 7 B-cun superior to popliteal crease on iliotibial tract",
                source_annotation="Fengshi",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_34", channel_code="GB", branch_id="GB_R_B3_LOWER", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB34", point_code="GB34",
                position=(0.1280, 0.4420, 0.0450), normal=(0.88, 0.18, 0.44), region="shank",
                anatomical_structure="Depression anterior and inferior to head of fibula", source_annotation="Yanglingquan",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_40", channel_code="GB", branch_id="GB_R_B3_LOWER", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB40", point_code="GB40",
                position=(0.1320, 0.0680, 0.0250), normal=(0.82, 0.12, 0.56), region="foot",
                anatomical_structure="Depression anterior and inferior to lateral malleolus", source_annotation="Qiuxu",
            ),
            RouteWaypoint(
                waypoint_id="WP_GB_R_44", channel_code="GB", branch_id="GB_R_B3_LOWER", sequence_order=6,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GB44", point_code="GB44",
                position=(0.1180, 0.0240, 0.0950), normal=(0.60, 0.20, 0.77), region="foot",
                anatomical_structure="Lateral aspect of 4th toe, 0.1 B-cun proximal to corner of nail", source_annotation="Zuqiaoyin",
            ),
        ]
        self._branches["GB_R_B3_LOWER"] = RouteBranch(
            branch_id="GB_R_B3_LOWER", channel_code="GB", branch_name="Right Pelvis & Lower Extremity Branch",
            side="right", start_anchor="GB27", end_anchor="GB44", body_region="lower_extremity",
            anatomical_corridor="Iliac crest -> greater trochanter -> iliotibial band -> fibular head -> lateral malleolus -> 4th toe",
            waypoints=gb_b3_waypoints,
        )

        # ---------------------------------------------------------------------
        # 2. BL: BLADDER MERIDIAN - 3 Branches (Dual Dorsal Columns + Popliteal Junction)
        # ---------------------------------------------------------------------
        bl_b1_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_BL_R_01", channel_code="BL", branch_id="BL_R_B1_INNER", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL1", point_code="BL1",
                position=(0.0135, 1.6050, 0.0728), normal=(0.20, 0.15, 0.97), region="head_neck",
                anatomical_structure="Depression superior to inner canthus of eye", source_annotation="Jingming",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_10", channel_code="BL", branch_id="BL_R_B1_INNER", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL10", point_code="BL10",
                position=(0.0260, 1.5580, -0.0820), normal=(0.28, 0.18, -0.94), region="head_neck",
                anatomical_structure="Lateral border of trapezius level with C2", source_annotation="Tianzhu",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_11", channel_code="BL", branch_id="BL_R_B1_INNER", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL11", point_code="BL11",
                position=(0.0420, 1.4420, -0.0980), normal=(0.22, 0.15, -0.96), region="torso",
                anatomical_structure="1.5 B-cun lateral to T1 spinous process", source_annotation="Dazhu",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_23", channel_code="BL", branch_id="BL_R_B1_INNER", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL23", point_code="BL23",
                position=(0.0440, 1.0850, -0.0910), normal=(0.22, 0.12, -0.97), region="torso",
                anatomical_structure="1.5 B-cun lateral to L2 spinous process", source_annotation="Shenshu",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_35", channel_code="BL", branch_id="BL_R_B1_INNER", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL35", point_code="BL35",
                position=(0.0240, 0.8680, -0.1320), normal=(0.18, 0.10, -0.98), region="pelvis",
                anatomical_structure="0.5 B-cun lateral to tip of coccyx", source_annotation="Huiyang",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_36", channel_code="BL", branch_id="BL_R_B1_INNER", sequence_order=6,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL36", point_code="BL36",
                position=(0.0733, 0.7566, -0.0994), normal=(0.10, -0.15, -0.98), region="pelvis",
                anatomical_structure="Midpoint of gluteal fold", source_annotation="Chengfu",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_37", channel_code="BL", branch_id="BL_R_B1_INNER", sequence_order=7,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL37", point_code="BL37",
                position=(0.0777, 0.6418, -0.0922), normal=(0.10, -0.14, -0.98), region="lower_extremity",
                anatomical_structure="Posterior midline of thigh, 6 B-cun inferior to Chengfu", source_annotation="Yinmen",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_40", channel_code="BL", branch_id="BL_R_B1_INNER", sequence_order=8,
                waypoint_type=WaypointType.BRANCH_JUNCTION, waypoint_code="BL40", point_code="BL40",
                position=(0.1180, 0.4450, -0.0780), normal=(0.21, 0.12, -0.97), region="lower_extremity",
                anatomical_structure="Popliteal crease midpoint between biceps femoris & semitendinosus",
                source_annotation="Weizhong (Primary Junction)",
            ),
        ]
        self._branches["BL_R_B1_INNER"] = RouteBranch(
            branch_id="BL_R_B1_INNER", channel_code="BL", branch_name="Right Cranial & Inner Paravertebral Column",
            side="right", start_anchor="BL1", end_anchor="BL40", body_region="torso_posterior",
            anatomical_corridor="Inner canthus -> vertex -> occiput -> 1.5 cun paravertebral column (T1-S4) -> popliteal",
            waypoints=bl_b1_waypoints,
        )

        # Branch 2: Outer Paravertebral Column (BL41 -> BL54)
        bl_b2_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_BL_R_41", channel_code="BL", branch_id="BL_R_B2_OUTER", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL41", point_code="BL41",
                position=(0.0750, 1.4180, -0.1120), normal=(0.35, 0.15, -0.92), region="torso",
                anatomical_structure="3.0 B-cun lateral to T2 spinous process", source_annotation="Fufen",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_54", channel_code="BL", branch_id="BL_R_B2_OUTER", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL54", point_code="BL54",
                position=(0.0820, 0.8960, -0.1410), normal=(0.38, 0.10, -0.92), region="pelvis",
                anatomical_structure="3.0 B-cun lateral to sacral median crest at level of 4th sacral foramen",
                source_annotation="Zhibian",
            ),
        ]
        self._branches["BL_R_B2_OUTER"] = RouteBranch(
            branch_id="BL_R_B2_OUTER", channel_code="BL", branch_name="Right Outer Paravertebral Column (3 Cun)",
            side="right", start_anchor="BL41", end_anchor="BL54", body_region="torso_posterior",
            anatomical_corridor="3.0 cun lateral paravertebral line across scapular border down to gluteal fold",
            waypoints=bl_b2_waypoints,
        )

        # Branch 3: Lower Leg & Foot (BL55 -> BL67)
        bl_b3_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_BL_R_55", channel_code="BL", branch_id="BL_R_B3_CALF", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL55", point_code="BL55",
                position=(0.0980, 0.3950, -0.0950), normal=(0.25, 0.15, -0.96), region="shank",
                anatomical_structure="2 B-cun inferior to BL40 between gastrocnemius heads", source_annotation="Heyang",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_57", channel_code="BL", branch_id="BL_R_B3_CALF", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL57", point_code="BL57",
                position=(0.0920, 0.2450, -0.0820), normal=(0.28, 0.12, -0.95), region="shank",
                anatomical_structure="Depression below gastrocnemius belly midpoint", source_annotation="Chengshan",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_60", channel_code="BL", branch_id="BL_R_B3_CALF", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL60", point_code="BL60",
                position=(0.1180, 0.0740, -0.0380), normal=(0.58, 0.12, -0.80), region="foot",
                anatomical_structure="Depression between lateral malleolus and calcaneal tendon", source_annotation="Kunlun",
            ),
            RouteWaypoint(
                waypoint_id="WP_BL_R_67", channel_code="BL", branch_id="BL_R_B3_CALF", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="BL67", point_code="BL67",
                position=(0.1224, 0.0296, 0.1021), normal=(0.70, 0.20, 0.68), region="foot",
                anatomical_structure="Lateral aspect of 5th toe, 0.1 B-cun proximal to corner of nail", source_annotation="Zhiyin",
            ),
        ]
        self._branches["BL_R_B3_CALF"] = RouteBranch(
            branch_id="BL_R_B3_CALF", channel_code="BL", branch_name="Right Posterior Calf & Lateral Foot",
            side="right", start_anchor="BL55", end_anchor="BL67", body_region="lower_extremity",
            anatomical_corridor="Gastrocnemius belly -> Achilles lateral groove -> lateral calcaneus -> 5th toe",
            waypoints=bl_b3_waypoints,
        )

        # ---------------------------------------------------------------------
        # 3. ST: STOMACH MERIDIAN - 2 Branches with Cranio-Cervical Separation
        # ---------------------------------------------------------------------
        st_b1_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_ST_R_01", channel_code="ST", branch_id="ST_R_B1_FACIAL", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST1", point_code="ST1",
                position=(0.0260, 1.6150, 0.0820), normal=(0.32, 0.15, 0.94), region="head_neck",
                anatomical_structure="Between eyeball and infraorbital margin", source_annotation="Chengqi",
            ),
            RouteWaypoint(
                waypoint_id="WP_ST_R_04", channel_code="ST", branch_id="ST_R_B1_FACIAL", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST4", point_code="ST4",
                position=(0.0380, 1.5420, 0.0860), normal=(0.42, 0.10, 0.90), region="head_neck",
                anatomical_structure="0.4 B-cun lateral to corner of mouth", source_annotation="Dicang",
            ),
            RouteWaypoint(
                waypoint_id="WP_ST_R_06", channel_code="ST", branch_id="ST_R_B1_FACIAL", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST6", point_code="ST6",
                position=(0.0580, 1.5280, 0.0520), normal=(0.72, 0.12, 0.68), region="head_neck",
                anatomical_structure="Anterior and superior to angle of mandible on masseter", source_annotation="Jiache",
            ),
            RouteWaypoint(
                waypoint_id="WP_ST_R_08", channel_code="ST", branch_id="ST_R_B1_FACIAL", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST8", point_code="ST8",
                position=(0.0620, 1.6820, 0.0480), normal=(0.65, 0.40, 0.64), region="head_neck",
                anatomical_structure="Corner of forehead 0.5 cun within hairline", source_annotation="Touwei",
            ),
        ]
        self._branches["ST_R_B1_FACIAL"] = RouteBranch(
            branch_id="ST_R_B1_FACIAL", channel_code="ST", branch_name="Right Facial Cranial Branch",
            side="right", start_anchor="ST1", end_anchor="ST8", body_region="head_neck",
            anatomical_corridor="Infraorbital -> cheek -> mandibular angle -> temple forehead corner",
            waypoints=st_b1_waypoints,
            has_gaps=True, gap_description="Classical internal branch connects ST8 to neck ST9 without surface chord",
        )

        st_b2_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_ST_R_09", channel_code="ST", branch_id="ST_R_B2_BODY", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST9", point_code="ST9",
                position=(0.0380, 1.5020, 0.0580), normal=(0.45, 0.15, 0.88), region="head_neck",
                anatomical_structure="Anterior neck level with laryngeal prominence on carotid artery", source_annotation="Renying",
            ),
            RouteWaypoint(
                waypoint_id="WP_ST_R_12", channel_code="ST", branch_id="ST_R_B2_BODY", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST12", point_code="ST12",
                position=(0.0820, 1.4120, 0.0450), normal=(0.40, 0.60, 0.69), region="torso",
                anatomical_structure="Supraclavicular fossa, 4 B-cun lateral to midline", source_annotation="Quepen",
            ),
            RouteWaypoint(
                waypoint_id="WP_ST_R_25", channel_code="ST", branch_id="ST_R_B2_BODY", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST25", point_code="ST25",
                position=(0.0580, 1.0260, 0.1080), normal=(0.38, 0.10, 0.92), region="torso",
                anatomical_structure="2 B-cun lateral to center of umbilicus on rectus abdominis", source_annotation="Tianshu",
            ),
            RouteWaypoint(
                waypoint_id="WP_ST_R_35", channel_code="ST", branch_id="ST_R_B2_BODY", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST35", point_code="ST35",
                position=(0.1150, 0.4680, 0.0820), normal=(0.35, 0.22, 0.91), region="lower_extremity",
                anatomical_structure="Depression lateral to patellar ligament", source_annotation="Dubi",
            ),
            RouteWaypoint(
                waypoint_id="WP_ST_R_36", channel_code="ST", branch_id="ST_R_B2_BODY", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST36", point_code="ST36",
                position=(0.1080, 0.4050, 0.0750), normal=(0.38, 0.20, 0.90), region="lower_extremity",
                anatomical_structure="3 B-cun inferior to ST35 lateral to tibial crest", source_annotation="Zusanli",
            ),
            RouteWaypoint(
                waypoint_id="WP_ST_R_45", channel_code="ST", branch_id="ST_R_B2_BODY", sequence_order=6,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="ST45", point_code="ST45",
                position=(0.0950, 0.0220, 0.1150), normal=(0.45, 0.20, 0.87), region="foot",
                anatomical_structure="Lateral aspect of 2nd toe, 0.1 B-cun proximal to corner of nail", source_annotation="Lidui",
            ),
        ]
        self._branches["ST_R_B2_BODY"] = RouteBranch(
            branch_id="ST_R_B2_BODY", channel_code="ST", branch_name="Right Neck, Thorax, Abdomen & Leg Branch",
            side="right", start_anchor="ST9", end_anchor="ST45", body_region="lower_extremity",
            anatomical_corridor="Neck -> clavicle -> 4 cun chest -> 2 cun abdomen -> rectus femoris -> tibialis anterior -> 2nd toe",
            waypoints=st_b2_waypoints,
        )

        # ---------------------------------------------------------------------
        # 4. GV: GOVERNOR VESSEL (Du Mai, Midline)
        # ---------------------------------------------------------------------
        gv_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_GV_01", channel_code="GV", branch_id="GV_MIDLINE", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GV1", point_code="GV1",
                position=(0.0000, 0.8390, -0.0888), normal=(0.0, -0.20, -0.98), region="pelvis",
                anatomical_structure="Midway between tip of coccyx and anus", source_annotation="Changqiang",
            ),
            RouteWaypoint(
                waypoint_id="WP_GV_04", channel_code="GV", branch_id="GV_MIDLINE", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GV4", point_code="GV4",
                position=(0.0000, 1.0550, -0.0920), normal=(0.0, 0.10, -0.99), region="torso",
                anatomical_structure="Depression inferior to spinous process of L2", source_annotation="Mingmen",
            ),
            RouteWaypoint(
                waypoint_id="WP_GV_14", channel_code="GV", branch_id="GV_MIDLINE", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GV14", point_code="GV14",
                position=(0.0000, 1.4720, -0.0950), normal=(0.0, 0.15, -0.99), region="head_neck",
                anatomical_structure="Depression inferior to spinous process of C7", source_annotation="Dazhui",
            ),
            RouteWaypoint(
                waypoint_id="WP_GV_20", channel_code="GV", branch_id="GV_MIDLINE", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GV20", point_code="GV20",
                position=(0.0000, 1.7180, -0.0150), normal=(0.0, 0.99, -0.12), region="head_neck",
                anatomical_structure="Sagittal suture intersection at vertex of skull", source_annotation="Baihui",
            ),
            RouteWaypoint(
                waypoint_id="WP_GV_28", channel_code="GV", branch_id="GV_MIDLINE", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="GV28", point_code="GV28",
                position=(0.0000, 1.5170, 0.1107), normal=(0.0, 0.10, 0.99), region="head_neck",
                anatomical_structure="Junction of upper lip and gum at frenulum", source_annotation="Yinjiao",
            ),
        ]
        self._branches["GV_MIDLINE"] = RouteBranch(
            branch_id="GV_MIDLINE", channel_code="GV", branch_name="Governor Vessel Midline (Du Mai)",
            side="midline", start_anchor="GV1", end_anchor="GV28", body_region="head_neck",
            anatomical_corridor="Posterior midline across sacrum, vertebral spinous processes, nuchal ligament, vertex, forehead, philtrum",
            waypoints=gv_waypoints,
        )

        # ---------------------------------------------------------------------
        # 5. CV: CONCEPTION VESSEL (Ren Mai, Midline)
        # ---------------------------------------------------------------------
        cv_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_CV_02", channel_code="CV", branch_id="CV_MIDLINE", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="CV2", point_code="CV2",
                position=(0.0000, 0.8640, 0.0880), normal=(0.0, 0.10, 0.99), region="torso",
                anatomical_structure="Superior border of pubic symphysis on midline", source_annotation="Qugu",
            ),
            RouteWaypoint(
                waypoint_id="WP_CV_08", channel_code="CV", branch_id="CV_MIDLINE", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="CV8", point_code="CV8",
                position=(0.0000, 1.0260, 0.1120), normal=(0.0, 0.05, 1.00), region="torso",
                anatomical_structure="Center of umbilicus", source_annotation="Shenque",
            ),
            RouteWaypoint(
                waypoint_id="WP_CV_12", channel_code="CV", branch_id="CV_MIDLINE", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="CV12", point_code="CV12",
                position=(0.0000, 1.1120, 0.1050), normal=(0.0, 0.12, 0.99), region="torso",
                anatomical_structure="4 B-cun superior to umbilicus on linea alba", source_annotation="Zhongwan",
            ),
            RouteWaypoint(
                waypoint_id="WP_CV_17", channel_code="CV", branch_id="CV_MIDLINE", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="CV17", point_code="CV17",
                position=(0.0000, 1.2580, 0.0920), normal=(0.0, 0.15, 0.99), region="torso",
                anatomical_structure="4th intercostal level on sternal body", source_annotation="Danzhong",
            ),
            RouteWaypoint(
                waypoint_id="WP_CV_22", channel_code="CV", branch_id="CV_MIDLINE", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="CV22", point_code="CV22",
                position=(0.0000, 1.4080, 0.0520), normal=(0.0, 0.65, 0.76), region="head_neck",
                anatomical_structure="Center of suprasternal fossa superior to jugular notch", source_annotation="Tiantu",
            ),
            RouteWaypoint(
                waypoint_id="WP_CV_24", channel_code="CV", branch_id="CV_MIDLINE", sequence_order=6,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="CV24", point_code="CV24",
                position=(0.0000, 1.5525, 0.0920), normal=(0.0, 0.20, 0.98), region="head_neck",
                anatomical_structure="Mentolabial sulcus in depression below lower lip", source_annotation="Chengjiang",
            ),
        ]
        self._branches["CV_MIDLINE"] = RouteBranch(
            branch_id="CV_MIDLINE", channel_code="CV", branch_name="Conception Vessel Midline (Ren Mai)",
            side="midline", start_anchor="CV2", end_anchor="CV24", body_region="torso",
            anatomical_corridor="Anterior midline across pubic symphysis, linea alba, sternal body, jugular notch, throat, mentolabial sulcus",
            waypoints=cv_waypoints,
        )

        # ---------------------------------------------------------------------
        # 6. LU: LUNG MERIDIAN (Taiyin)
        # ---------------------------------------------------------------------
        lu_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_LU_R_01", channel_code="LU", branch_id="LU_R_B1", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LU1", point_code="LU1",
                position=(0.1297, 1.3475, 0.0688), normal=(0.45, 0.20, 0.87), region="torso",
                anatomical_structure="1st intercostal space 6 cun lateral to midline", source_annotation="Zhongfu",
            ),
            RouteWaypoint(
                waypoint_id="WP_LU_R_02", channel_code="LU", branch_id="LU_R_B1", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LU2", point_code="LU2",
                position=(0.1450, 1.3850, 0.0520), normal=(0.52, 0.25, 0.81), region="torso",
                anatomical_structure="Infraclavicular fossa medial to coracoid process", source_annotation="Yunmen",
            ),
            RouteWaypoint(
                waypoint_id="WP_LU_R_05", channel_code="LU", branch_id="LU_R_B1", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LU5", point_code="LU5",
                position=(0.2340, 1.1130, 0.0056), normal=(0.58, 0.35, 0.73), region="upper_extremity",
                anatomical_structure="Cubital crease radial to biceps brachii tendon", source_annotation="Chize",
            ),
            RouteWaypoint(
                waypoint_id="WP_LU_R_07", channel_code="LU", branch_id="LU_R_B1", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LU7", point_code="LU7",
                position=(0.2480, 0.9420, 0.0280), normal=(0.65, 0.20, 0.73), region="upper_extremity",
                anatomical_structure="1.5 cun proximal to palmar wrist crease superior to radial styloid", source_annotation="Lieque",
            ),
            RouteWaypoint(
                waypoint_id="WP_LU_R_09", channel_code="LU", branch_id="LU_R_B1", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LU9", point_code="LU9",
                position=(0.2580, 0.8750, 0.0420), normal=(0.68, 0.15, 0.71), region="upper_extremity",
                anatomical_structure="Palmar wrist crease radial border of radial artery", source_annotation="Taiyuan",
            ),
            RouteWaypoint(
                waypoint_id="WP_LU_R_11", channel_code="LU", branch_id="LU_R_B1", sequence_order=6,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LU11", point_code="LU11",
                position=(0.2656, 0.7617, 0.0711), normal=(0.70, 0.15, 0.69), region="upper_extremity",
                anatomical_structure="Radial border of distal phalanx of thumb 0.1 cun proximal to nail", source_annotation="Shaoshang",
            ),
        ]
        self._branches["LU_R_B1"] = RouteBranch(
            branch_id="LU_R_B1", channel_code="LU", branch_name="Right Lung Channel (Taiyin)",
            side="right", start_anchor="LU1", end_anchor="LU11", body_region="upper_extremity",
            anatomical_corridor="Infraclavicular fossa -> anterolateral arm -> biceps radial groove -> radial wrist -> thenar eminence -> thumb",
            waypoints=lu_waypoints,
        )

        # ---------------------------------------------------------------------
        # 7. LI: LARGE INTESTINE MERIDIAN (Yangming)
        # ---------------------------------------------------------------------
        li_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_LI_R_01", channel_code="LI", branch_id="LI_R_B1", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LI1", point_code="LI1",
                position=(0.2686, 0.7592, 0.0541), normal=(0.70, 0.15, 0.69), region="upper_extremity",
                anatomical_structure="Radial border of index finger 0.1 cun proximal to corner of nail", source_annotation="Shangyang",
            ),
            RouteWaypoint(
                waypoint_id="WP_LI_R_04", channel_code="LI", branch_id="LI_R_B1", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LI4", point_code="LI4",
                position=(0.2860, 0.8310, 0.0141), normal=(0.64, 0.22, 0.74), region="upper_extremity",
                anatomical_structure="Radial border of 2nd metacarpal bone midpoint", source_annotation="Hegu",
            ),
            RouteWaypoint(
                waypoint_id="WP_LI_R_11", channel_code="LI", branch_id="LI_R_B1", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LI11", point_code="LI11",
                position=(0.2647, 1.1180, -0.0220), normal=(0.75, 0.30, 0.58), region="upper_extremity",
                anatomical_structure="Lateral end of cubital crease midway between LU5 and lateral epicondyle", source_annotation="Quchi",
            ),
            RouteWaypoint(
                waypoint_id="WP_LI_R_15", channel_code="LI", branch_id="LI_R_B1", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LI15", point_code="LI15",
                position=(0.1660, 1.4210, -0.0250), normal=(0.85, 0.42, 0.32), region="upper_extremity",
                anatomical_structure="Depression anterior and inferior to lateral acromion", source_annotation="Jianyu",
            ),
            RouteWaypoint(
                waypoint_id="WP_LI_R_20", channel_code="LI", branch_id="LI_R_B1", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LI20", point_code="LI20",
                position=(0.0162, 1.5925, 0.0712), normal=(0.30, 0.10, 0.95), region="head_neck",
                anatomical_structure="Nasolabial groove level with midpoint of lateral border of ala nasi", source_annotation="Yingxiang",
            ),
        ]
        self._branches["LI_R_B1"] = RouteBranch(
            branch_id="LI_R_B1", channel_code="LI", branch_name="Right Large Intestine Channel (Yangming)",
            side="right", start_anchor="LI1", end_anchor="LI20", body_region="upper_extremity",
            anatomical_corridor="Radial index finger -> 2nd metacarpal -> lateral forearm -> elbow -> anterior acromion -> neck -> nasolabial sulcus",
            waypoints=li_waypoints,
        )

        # ---------------------------------------------------------------------
        # 8. SP: SPLEEN MERIDIAN (Taiyin)
        # ---------------------------------------------------------------------
        sp_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_SP_R_01", channel_code="SP", branch_id="SP_R_B1", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SP1", point_code="SP1",
                position=(0.0841, 0.0179, 0.1007), normal=(0.35, 0.15, 0.92), region="foot",
                anatomical_structure="Medial aspect of terminal phalanx of great toe 0.1 cun from nail", source_annotation="Yinbai",
            ),
            RouteWaypoint(
                waypoint_id="WP_SP_R_04", channel_code="SP", branch_id="SP_R_B1", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SP4", point_code="SP4",
                position=(0.0780, 0.0420, 0.0550), normal=(0.45, 0.15, 0.87), region="foot",
                anatomical_structure="Anteroinferior to base of 1st metatarsal bone on junction of red/white skin", source_annotation="Gongsun",
            ),
            RouteWaypoint(
                waypoint_id="WP_SP_R_06", channel_code="SP", branch_id="SP_R_B1", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SP6", point_code="SP6",
                position=(0.0472, 0.1500, -0.0260), normal=(0.42, 0.12, 0.90), region="shank",
                anatomical_structure="3 cun superior to medial malleolus posterior to medial border of tibia", source_annotation="Sanyinjiao",
            ),
            RouteWaypoint(
                waypoint_id="WP_SP_R_09", channel_code="SP", branch_id="SP_R_B1", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SP9", point_code="SP9",
                position=(0.0290, 0.4280, -0.0150), normal=(0.38, 0.15, 0.91), region="shank",
                anatomical_structure="Depression inferior to medial condyle of tibia", source_annotation="Yinlingquan",
            ),
            RouteWaypoint(
                waypoint_id="WP_SP_R_10", channel_code="SP", branch_id="SP_R_B1", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SP10", point_code="SP10",
                position=(0.0651, 0.4983, 0.0468), normal=(0.35, 0.20, 0.91), region="thigh",
                anatomical_structure="2 cun superior to mediocranial border of patella on vastus medialis", source_annotation="Xuehai",
            ),
            RouteWaypoint(
                waypoint_id="WP_SP_R_15", channel_code="SP", branch_id="SP_R_B1", sequence_order=6,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SP15", point_code="SP15",
                position=(0.0880, 1.0260, 0.1020), normal=(0.45, 0.10, 0.88), region="torso",
                anatomical_structure="4 cun lateral to center of umbilicus on lateral border of rectus abdominis", source_annotation="Daheng",
            ),
            RouteWaypoint(
                waypoint_id="WP_SP_R_21", channel_code="SP", branch_id="SP_R_B1", sequence_order=7,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SP21", point_code="SP21",
                position=(0.1489, 1.2515, 0.0480), normal=(0.88, 0.15, 0.44), region="torso",
                anatomical_structure="6th intercostal space on midaxillary line", source_annotation="Dabao",
            ),
        ]
        self._branches["SP_R_B1"] = RouteBranch(
            branch_id="SP_R_B1", channel_code="SP", branch_name="Right Spleen Channel (Taiyin)",
            side="right", start_anchor="SP1", end_anchor="SP21", body_region="lower_extremity",
            anatomical_corridor="Medial great toe -> medial malleolus posterior border -> medial tibial border -> vastus medialis -> lateral abdomen (4 cun) -> 6th intercostal midaxillary line",
            waypoints=sp_waypoints,
        )

        # ---------------------------------------------------------------------
        # 9. HT: HEART MERIDIAN (Shaoyin)
        # ---------------------------------------------------------------------
        ht_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_HT_R_01", channel_code="HT", branch_id="HT_R_B1", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="HT1", point_code="HT1",
                position=(0.1887, 1.4028, 0.0133), normal=(0.85, 0.15, 0.50), region="torso",
                anatomical_structure="Apex of axillary fossa medial to axillary artery", source_annotation="Jiquan",
            ),
            RouteWaypoint(
                waypoint_id="WP_HT_R_03", channel_code="HT", branch_id="HT_R_B1", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="HT3", point_code="HT3",
                position=(0.2322, 1.1140, 0.0056), normal=(0.68, 0.25, -0.69), region="upper_extremity",
                anatomical_structure="Midway between medial epicondyle of humerus and medial end of cubital crease", source_annotation="Shaohai",
            ),
            RouteWaypoint(
                waypoint_id="WP_HT_R_07", channel_code="HT", branch_id="HT_R_B1", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="HT7", point_code="HT7",
                position=(0.2380, 0.8840, 0.0401), normal=(0.62, 0.18, 0.76), region="upper_extremity",
                anatomical_structure="Palmar wrist crease radial border of flexor carpi ulnaris tendon", source_annotation="Shenmen",
            ),
            RouteWaypoint(
                waypoint_id="WP_HT_R_09", channel_code="HT", branch_id="HT_R_B1", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="HT9", point_code="HT9",
                position=(0.2532, 0.7627, 0.0779), normal=(0.70, 0.15, 0.69), region="upper_extremity",
                anatomical_structure="Radial border of distal phalanx of little finger 0.1 cun from nail", source_annotation="Shaochong",
            ),
        ]
        self._branches["HT_R_B1"] = RouteBranch(
            branch_id="HT_R_B1", channel_code="HT", branch_name="Right Heart Channel (Shaoyin)",
            side="right", start_anchor="HT1", end_anchor="HT9", body_region="upper_extremity",
            anatomical_corridor="Axillary fossa -> medial bicipital groove -> medial cubital crease -> flexor carpi ulnaris radial border -> little finger radial nail",
            waypoints=ht_waypoints,
        )

        # ---------------------------------------------------------------------
        # 10. SI: SMALL INTESTINE MERIDIAN (Taiyang)
        # ---------------------------------------------------------------------
        si_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_SI_R_01", channel_code="SI", branch_id="SI_R_B1", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SI1", point_code="SI1",
                position=(0.2504, 0.7533, 0.0931), normal=(0.70, 0.15, 0.69), region="upper_extremity",
                anatomical_structure="Ulnar border of little finger distal phalanx 0.1 cun from nail", source_annotation="Shaoze",
            ),
            RouteWaypoint(
                waypoint_id="WP_SI_R_03", channel_code="SI", branch_id="SI_R_B1", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SI3", point_code="SI3",
                position=(0.1618, 0.7974, -0.0249), normal=(0.65, 0.15, -0.74), region="upper_extremity",
                anatomical_structure="Ulnar border of hand proximal to 5th MCP joint", source_annotation="Houxi",
            ),
            RouteWaypoint(
                waypoint_id="WP_SI_R_08", channel_code="SI", branch_id="SI_R_B1", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SI8", point_code="SI8",
                position=(0.2558, 1.1103, -0.0522), normal=(0.68, 0.20, -0.70), region="upper_extremity",
                anatomical_structure="Ulnar nerve sulcus between olecranon and medial epicondyle", source_annotation="Xiaohai",
            ),
            RouteWaypoint(
                waypoint_id="WP_SI_R_11", channel_code="SI", branch_id="SI_R_B1", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SI11", point_code="SI11",
                position=(0.1348, 1.3098, -0.1299), normal=(0.35, 0.15, -0.92), region="torso",
                anatomical_structure="Infraspinous fossa center forming equilateral triangle with SI9/SI10", source_annotation="Tianzong",
            ),
            RouteWaypoint(
                waypoint_id="WP_SI_R_19", channel_code="SI", branch_id="SI_R_B1", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="SI19", point_code="SI19",
                position=(0.0645, 1.5920, 0.0328), normal=(0.75, 0.15, 0.64), region="head_neck",
                anatomical_structure="Depression anterior to tragus when mouth is open", source_annotation="Tinggong",
            ),
        ]
        self._branches["SI_R_B1"] = RouteBranch(
            branch_id="SI_R_B1", channel_code="SI", branch_name="Right Small Intestine Channel (Taiyang)",
            side="right", start_anchor="SI1", end_anchor="SI19", body_region="upper_extremity",
            anatomical_corridor="Ulnar little finger -> 5th metacarpal -> ulnar groove -> infraspinous fossa of scapula -> neck -> pre-auricular tragus",
            waypoints=si_waypoints,
        )

        # ---------------------------------------------------------------------
        # 11. KI: KIDNEY MERIDIAN (Shaoyin, 2 Branches)
        # ---------------------------------------------------------------------
        ki_b1_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_KI_R_01", channel_code="KI", branch_id="KI_R_B1_LOWER", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="KI1", point_code="KI1",
                position=(0.1010, 0.0031, 0.0690), normal=(0.0, -0.98, 0.20), region="foot",
                anatomical_structure="Plantar sole depression between 2nd and 3rd metatarsal shafts", source_annotation="Yongquan",
            ),
            RouteWaypoint(
                waypoint_id="WP_KI_R_03", channel_code="KI", branch_id="KI_R_B1_LOWER", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="KI3", point_code="KI3",
                position=(0.0580, 0.0845, -0.0705), normal=(0.35, 0.12, -0.92), region="foot",
                anatomical_structure="Depression between medial malleolus prominence and calcaneal tendon", source_annotation="Taixi",
            ),
            RouteWaypoint(
                waypoint_id="WP_KI_R_07", channel_code="KI", branch_id="KI_R_B1_LOWER", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="KI7", point_code="KI7",
                position=(0.0520, 0.1450, -0.0680), normal=(0.35, 0.15, -0.92), region="shank",
                anatomical_structure="2 cun superior to KI3 anterior to calcaneal tendon", source_annotation="Fuliu",
            ),
            RouteWaypoint(
                waypoint_id="WP_KI_R_10", channel_code="KI", branch_id="KI_R_B1_LOWER", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="KI10", point_code="KI10",
                position=(0.0559, 0.4306, 0.0149), normal=(0.42, 0.20, -0.88), region="shank",
                anatomical_structure="Medial end of popliteal crease between semitendinosus and semimembranosus", source_annotation="Yingu",
            ),
        ]
        self._branches["KI_R_B1_LOWER"] = RouteBranch(
            branch_id="KI_R_B1_LOWER", channel_code="KI", branch_name="Right Kidney Lower Extremity Branch",
            side="right", start_anchor="KI1", end_anchor="KI10", body_region="lower_extremity",
            anatomical_corridor="Plantar sole -> medial malleolus calcaneal groove -> Achilles tendon -> medial popliteal crease",
            waypoints=ki_b1_waypoints,
            has_gaps=True, gap_description="Classical internal connection ascends through pelvis to Henggu KI11 without surface chord",
        )

        ki_b2_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_KI_R_11", channel_code="KI", branch_id="KI_R_B2_TORSO", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="KI11", point_code="KI11",
                position=(0.0193, 0.8914, 0.0607), normal=(0.20, 0.10, 0.97), region="torso",
                anatomical_structure="0.5 cun lateral to anterior midline level with superior border of pubic symphysis", source_annotation="Henggu",
            ),
            RouteWaypoint(
                waypoint_id="WP_KI_R_16", channel_code="KI", branch_id="KI_R_B2_TORSO", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="KI16", point_code="KI16",
                position=(0.0193, 1.0257, 0.1036), normal=(0.20, 0.10, 0.97), region="torso",
                anatomical_structure="0.5 cun lateral to center of umbilicus on rectus abdominis", source_annotation="Huangshu",
            ),
            RouteWaypoint(
                waypoint_id="WP_KI_R_27", channel_code="KI", branch_id="KI_R_B2_TORSO", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="KI27", point_code="KI27",
                position=(0.0404, 1.4122, 0.0518), normal=(0.30, 0.45, 0.84), region="torso",
                anatomical_structure="1st intercostal space 2 cun lateral to anterior midline inferior to clavicle", source_annotation="Shufu",
            ),
        ]
        self._branches["KI_R_B2_TORSO"] = RouteBranch(
            branch_id="KI_R_B2_TORSO", channel_code="KI", branch_name="Right Kidney Anterior Trunk Branch",
            side="right", start_anchor="KI11", end_anchor="KI27", body_region="torso",
            anatomical_corridor="0.5 cun parasagittal line on lower/upper abdomen -> 2 cun parasagittal line on thorax to 1st intercostal space",
            waypoints=ki_b2_waypoints,
        )

        # ---------------------------------------------------------------------
        # 12. PC: PERICARDIUM MERIDIAN (Jueyin)
        # ---------------------------------------------------------------------
        pc_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_PC_R_01", channel_code="PC", branch_id="PC_R_B1", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="PC1", point_code="PC1",
                position=(0.1105, 1.2419, 0.1022), normal=(0.45, 0.15, 0.87), region="torso",
                anatomical_structure="4th intercostal space 1 cun lateral to nipple", source_annotation="Tianchi",
            ),
            RouteWaypoint(
                waypoint_id="WP_PC_R_03", channel_code="PC", branch_id="PC_R_B1", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="PC3", point_code="PC3",
                position=(0.2318, 1.1135, 0.0056), normal=(0.58, 0.35, 0.73), region="upper_extremity",
                anatomical_structure="Cubital crease medial to biceps brachii tendon", source_annotation="Quze",
            ),
            RouteWaypoint(
                waypoint_id="WP_PC_R_06", channel_code="PC", branch_id="PC_R_B1", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="PC6", point_code="PC6",
                position=(0.2412, 0.9250, 0.0314), normal=(0.55, 0.20, 0.81), region="upper_extremity",
                anatomical_structure="2 cun proximal to palmar wrist crease between palmaris longus & FCR tendons", source_annotation="Neiguan",
            ),
            RouteWaypoint(
                waypoint_id="WP_PC_R_09", channel_code="PC", branch_id="PC_R_B1", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="PC9", point_code="PC9",
                position=(0.2521, 0.7453, 0.0719), normal=(0.70, 0.15, 0.69), region="upper_extremity",
                anatomical_structure="Center of tip of distal phalanx of middle finger", source_annotation="Zhongchong",
            ),
        ]
        self._branches["PC_R_B1"] = RouteBranch(
            branch_id="PC_R_B1", channel_code="PC", branch_name="Right Pericardium Channel (Jueyin)",
            side="right", start_anchor="PC1", end_anchor="PC9", body_region="upper_extremity",
            anatomical_corridor="Lateral to nipple 4th intercostal -> medial bicipital tendon at elbow -> anterior forearm inter-tendinous midline -> tip of middle finger",
            waypoints=pc_waypoints,
        )

        # ---------------------------------------------------------------------
        # 13. TE: TRIPLE ENERGIZER MERIDIAN (San Jiao, Shaoyang)
        # ---------------------------------------------------------------------
        te_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_TE_R_01", channel_code="TE", branch_id="TE_R_B1", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="TE1", point_code="TE1",
                position=(0.2518, 0.7437, 0.1080), normal=(0.70, 0.15, 0.69), region="upper_extremity",
                anatomical_structure="Ulnar aspect of ring finger distal phalanx 0.1 cun from nail", source_annotation="Guanchong",
            ),
            RouteWaypoint(
                waypoint_id="WP_TE_R_05", channel_code="TE", branch_id="TE_R_B1", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="TE5", point_code="TE5",
                position=(0.2450, 0.9250, -0.0241), normal=(0.65, 0.18, -0.73), region="upper_extremity",
                anatomical_structure="2 cun proximal to dorsal wrist crease between radius and ulna", source_annotation="Waiguan",
            ),
            RouteWaypoint(
                waypoint_id="WP_TE_R_14", channel_code="TE", branch_id="TE_R_B1", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="TE14", point_code="TE14",
                position=(0.1937, 1.4140, -0.0694), normal=(0.80, 0.35, -0.48), region="upper_extremity",
                anatomical_structure="Depression posterior and inferior to lateral acromion", source_annotation="Jianliao",
            ),
            RouteWaypoint(
                waypoint_id="WP_TE_R_17", channel_code="TE", branch_id="TE_R_B1", sequence_order=4,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="TE17", point_code="TE17",
                position=(0.0628, 1.5729, -0.0130), normal=(0.72, 0.15, -0.67), region="head_neck",
                anatomical_structure="Depression between mastoid process and mandible posterior to ear lobe", source_annotation="Yifeng",
            ),
            RouteWaypoint(
                waypoint_id="WP_TE_R_23", channel_code="TE", branch_id="TE_R_B1", sequence_order=5,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="TE23", point_code="TE23",
                position=(0.0487, 1.6279, 0.0670), normal=(0.65, 0.20, 0.73), region="head_neck",
                anatomical_structure="Depression at lateral end of eyebrow", source_annotation="Sizhukong",
            ),
        ]
        self._branches["TE_R_B1"] = RouteBranch(
            branch_id="TE_R_B1", channel_code="TE", branch_name="Right Triple Energizer Channel (Shaoyang)",
            side="right", start_anchor="TE1", end_anchor="TE23", body_region="upper_extremity",
            anatomical_corridor="Ring finger ulnar nail -> dorsal wrist -> between radius and ulna -> posterior acromion -> post-auricular mastoid -> lateral eyebrow",
            waypoints=te_waypoints,
        )

        # ---------------------------------------------------------------------
        # 14. LR: LIVER MERIDIAN (Jueyin, 2 Branches)
        # ---------------------------------------------------------------------
        lr_b1_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_LR_R_01", channel_code="LR", branch_id="LR_R_B1_LOWER", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LR1", point_code="LR1",
                position=(0.0876, 0.0181, 0.1059), normal=(0.40, 0.15, 0.90), region="foot",
                anatomical_structure="Lateral aspect of terminal phalanx of great toe 0.1 cun from nail", source_annotation="Dadun",
            ),
            RouteWaypoint(
                waypoint_id="WP_LR_R_03", channel_code="LR", branch_id="LR_R_B1_LOWER", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LR3", point_code="LR3",
                position=(0.0970, 0.0667, 0.0470), normal=(0.45, 0.15, 0.87), region="foot",
                anatomical_structure="Dorsum of foot depression between 1st and 2nd metatarsal bases", source_annotation="Taichong",
            ),
            RouteWaypoint(
                waypoint_id="WP_LR_R_08", channel_code="LR", branch_id="LR_R_B1_LOWER", sequence_order=3,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LR8", point_code="LR8",
                position=(0.0448, 0.4456, 0.0118), normal=(0.42, 0.20, 0.88), region="lower_extremity",
                anatomical_structure="Medial aspect of knee superior to medial end of popliteal crease", source_annotation="Ququan",
            ),
        ]
        self._branches["LR_R_B1_LOWER"] = RouteBranch(
            branch_id="LR_R_B1_LOWER", channel_code="LR", branch_name="Right Liver Lower Extremity Branch",
            side="right", start_anchor="LR1", end_anchor="LR8", body_region="lower_extremity",
            anatomical_corridor="Great toe lateral nail -> 1st/2nd metatarsal groove -> medial tibial border -> medial knee crease",
            waypoints=lr_b1_waypoints,
            has_gaps=True, gap_description="Internal pelvic collateral ascends to hypochondrium LR13 without cutaneous jump",
        )

        lr_b2_waypoints = [
            RouteWaypoint(
                waypoint_id="WP_LR_R_13", channel_code="LR", branch_id="LR_R_B2_TORSO", sequence_order=1,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LR13", point_code="LR13",
                position=(0.1393, 1.0594, 0.0179), normal=(0.85, 0.15, 0.50), region="torso",
                anatomical_structure="Directly inferior to free end of 11th rib on lateral abdomen", source_annotation="Zhangmen",
            ),
            RouteWaypoint(
                waypoint_id="WP_LR_R_14", channel_code="LR", branch_id="LR_R_B2_TORSO", sequence_order=2,
                waypoint_type=WaypointType.ACUPOINT_ANCHOR, waypoint_code="LR14", point_code="LR14",
                position=(0.0961, 1.1891, 0.1077), normal=(0.52, 0.15, 0.84), region="torso",
                anatomical_structure="6th intercostal space directly inferior to nipple 4 cun lateral to midline", source_annotation="Qimen",
            ),
        ]
        self._branches["LR_R_B2_TORSO"] = RouteBranch(
            branch_id="LR_R_B2_TORSO", channel_code="LR", branch_name="Right Liver Hypochondriac Trunk Branch",
            side="right", start_anchor="LR13", end_anchor="LR14", body_region="torso",
            anatomical_corridor="11th rib free end -> 6th intercostal mammillary line",
            waypoints=lr_b2_waypoints,
        )

        # ---------------------------------------------------------------------
        # Mirrored left branches automatically generated with negated X coordinates
        # ---------------------------------------------------------------------
        left_branches = {}
        for b_id, branch in self._branches.items():
            if branch.side == "right":
                l_id = b_id.replace("_R_", "_L_")
                l_waypoints = []
                for w in branch.waypoints:
                    l_pos = (-w.position[0], w.position[1], w.position[2])
                    l_norm = (-w.normal[0], w.normal[1], w.normal[2])
                    l_waypoints.append(RouteWaypoint(
                        waypoint_id=w.waypoint_id.replace("_R_", "_L_"),
                        channel_code=w.channel_code,
                        branch_id=l_id,
                        sequence_order=w.sequence_order,
                        waypoint_type=w.waypoint_type,
                        waypoint_code=w.waypoint_code,
                        position=l_pos,
                        normal=l_norm,
                        region=w.region,
                        anatomical_structure=w.anatomical_structure,
                        point_code=w.point_code,
                        source_annotation=w.source_annotation,
                    ))
                left_branches[l_id] = RouteBranch(
                    branch_id=l_id, channel_code=branch.channel_code,
                    branch_name=branch.branch_name.replace("Right", "Left"),
                    side="left", start_anchor=branch.start_anchor, end_anchor=branch.end_anchor,
                    body_region=branch.body_region, anatomical_corridor=branch.anatomical_corridor,
                    is_continuous=branch.is_continuous, has_gaps=branch.has_gaps,
                    gap_description=branch.gap_description, waypoints=l_waypoints,
                )

        self._branches.update(left_branches)
