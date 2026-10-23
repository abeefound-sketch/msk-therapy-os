"""M4 Joint Kinematic Arcs, Motion Analytics, and Frame Budgeting.

Calculates 2D/3D planar joint kinematic arcs, compares measured ROM to
established normal physiological envelopes (AAOS/Kendall), and monitors frame time budgets.
"""
from __future__ import annotations

import json
import math
import sqlite3
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Reference Normal Physiological Envelopes (AAOS / Kendall Standard Reference Values)
PHYSIOLOGICAL_ROM_ENVELOPES = {
    "cervical_rotation": {"min_deg": 0.0, "normal_deg": 80.0, "plane": "transverse", "region": "neck"},
    "cervical_flexion": {"min_deg": 0.0, "normal_deg": 45.0, "plane": "sagittal", "region": "neck"},
    "cervical_extension": {"min_deg": 0.0, "normal_deg": 45.0, "plane": "sagittal", "region": "neck"},
    "cervical_lateral_flexion": {"min_deg": 0.0, "normal_deg": 45.0, "plane": "frontal", "region": "neck"},
    "shoulder_abduction": {"min_deg": 0.0, "normal_deg": 180.0, "plane": "frontal", "region": "shoulder"},
    "shoulder_flexion": {"min_deg": 0.0, "normal_deg": 180.0, "plane": "sagittal", "region": "shoulder"},
    "shoulder_external_rotation": {"min_deg": 0.0, "normal_deg": 90.0, "plane": "transverse", "region": "shoulder"},
    "shoulder_internal_rotation": {"min_deg": 0.0, "normal_deg": 70.0, "plane": "transverse", "region": "shoulder"},
    "lumbar_flexion": {"min_deg": 0.0, "normal_deg": 60.0, "plane": "sagittal", "region": "low_back"},
    "lumbar_extension": {"min_deg": 0.0, "normal_deg": 25.0, "plane": "sagittal", "region": "low_back"},
}


def init_kinematics_tables(db: sqlite3.Connection) -> None:
    """Initialize SQLite tables for M4 Kinematic Arcs."""
    db.executescript("""
    CREATE TABLE IF NOT EXISTS kinematic_arcs (
        arc_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL REFERENCES cases(case_id),
        visit_id INTEGER REFERENCES visits(id),
        joint_name TEXT NOT NULL,
        plane_of_motion TEXT NOT NULL,
        measured_rom_deg REAL NOT NULL,
        reference_normal_deg REAL NOT NULL,
        percentage_of_normal REAL NOT NULL,
        mobility_status TEXT NOT NULL CHECK(mobility_status IN ('HYPOMOBILITY', 'NORMAL_MOBILITY', 'HYPERMOBILITY')),
        arc_points_json TEXT NOT NULL,
        disclaimer TEXT NOT NULL DEFAULT 'MODEL_ESTIMATE; Not a substitute for clinical radiography or dynamic fluoroscopy',
        recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_kinematics_case ON kinematic_arcs(case_id);
    """)


def classify_mobility(measured_deg: float, normal_deg: float) -> tuple[str, float]:
    """Classify mobility against reference normal envelope."""
    if normal_deg <= 0:
        return "NORMAL_MOBILITY", 100.0
    pct = round((measured_deg / normal_deg) * 100.0, 1)
    if pct < 85.0:
        return "HYPOMOBILITY", pct
    elif pct > 115.0:
        return "HYPERMOBILITY", pct
    return "NORMAL_MOBILITY", pct


def generate_arc_trajectory(
    center: tuple[float, float],
    radius: float,
    start_angle_deg: float,
    sweep_angle_deg: float,
    num_points: int = 20,
) -> List[Dict[str, float]]:
    """Generate planar 2D arc trajectory points for visualization."""
    points = []
    step = sweep_angle_deg / max(1, num_points - 1)
    for i in range(num_points):
        ang_deg = start_angle_deg + (i * step)
        rad = math.radians(ang_deg)
        x = round(center[0] + radius * math.cos(rad), 3)
        y = round(center[1] + radius * math.sin(rad), 3)
        points.append({"angle_deg": round(ang_deg, 1), "x": x, "y": y})
    return points


def record_kinematic_arc(
    db: sqlite3.Connection,
    *,
    case_id: str,
    visit_id: Optional[int],
    joint_name: str,
    measured_rom_deg: float,
    custom_normal_deg: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate and store a joint kinematic arc."""
    if not case_id.startswith("DEMO-"):
        raise ValueError("Synthetic DEMO-* cases only")
    if joint_name not in PHYSIOLOGICAL_ROM_ENVELOPES and custom_normal_deg is None:
        raise ValueError(f"Unknown joint motion '{joint_name}' and no custom normal provided")

    envelope = PHYSIOLOGICAL_ROM_ENVELOPES.get(joint_name, {"plane": "custom", "normal_deg": custom_normal_deg or 90.0})
    ref_normal = float(custom_normal_deg or envelope["normal_deg"])
    status, pct = classify_mobility(measured_rom_deg, ref_normal)

    # Generate 20-point arc path
    arc_points = generate_arc_trajectory((0.0, 0.0), 100.0, 0.0, measured_rom_deg, 20)
    arc_id = f"KARC-{uuid4().hex[:16]}"

    with db:
        db.execute(
            """INSERT INTO kinematic_arcs
               (arc_id, case_id, visit_id, joint_name, plane_of_motion, measured_rom_deg, reference_normal_deg, percentage_of_normal, mobility_status, arc_points_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                arc_id,
                case_id,
                visit_id,
                joint_name,
                envelope["plane"],
                measured_rom_deg,
                ref_normal,
                pct,
                status,
                json.dumps(arc_points),
            ),
        )

    return {
        "arc_id": arc_id,
        "case_id": case_id,
        "joint_name": joint_name,
        "measured_rom_deg": measured_rom_deg,
        "reference_normal_deg": ref_normal,
        "percentage_of_normal": pct,
        "mobility_status": status,
        "arc_points": arc_points,
    }


def list_kinematic_arcs(db: sqlite3.Connection, case_id: str) -> List[Dict[str, Any]]:
    """List recorded kinematic arcs for a case."""
    rows = db.execute(
        """SELECT arc_id, case_id, visit_id, joint_name, plane_of_motion, measured_rom_deg, reference_normal_deg, percentage_of_normal, mobility_status, arc_points_json, recorded_at
           FROM kinematic_arcs WHERE case_id = ? ORDER BY recorded_at ASC""",
        (case_id,),
    ).fetchall()
    return [
        {
            "arc_id": r[0],
            "case_id": r[1],
            "visit_id": r[2],
            "joint_name": r[3],
            "plane_of_motion": r[4],
            "measured_rom_deg": r[5],
            "reference_normal_deg": r[6],
            "percentage_of_normal": r[7],
            "mobility_status": r[8],
            "arc_points": json.loads(r[9]),
            "recorded_at": r[10],
        }
        for r in rows
    ]


def evaluate_frame_budget(frame_time_ms: float, target_fps: float = 30.0) -> Dict[str, Any]:
    """Evaluate whether render latency meets Intel HD 5500 30 FPS budget."""
    target_budget_ms = 1000.0 / target_fps
    is_within_budget = frame_time_ms <= target_budget_ms
    effective_fps = round(1000.0 / max(1e-3, frame_time_ms), 1)
    return {
        "frame_time_ms": round(frame_time_ms, 2),
        "target_budget_ms": round(target_budget_ms, 2),
        "is_within_budget": is_within_budget,
        "effective_fps": effective_fps,
        "target_fps": target_fps,
        "hardware_target": "Intel Core i7-5600U / HD Graphics 5500",
    }
