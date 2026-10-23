"""M2.11 Pose-to-Anatomy Explorer.

Provides pose landmark parsing, joint angle estimation, candidate muscle role mapping,
and manual landmark correction with strict clinical abstention semantics.
Never converts a 2D photograph into a diagnosis, measured muscle activation, or medical claim.
"""
from __future__ import annotations

import json
import math
import sqlite3
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Standard MediaPipe 33 Landmark Names
MEDIAPIPE_LANDMARK_NAMES = {
    0: "nose",
    1: "left_eye_inner", 2: "left_eye", 3: "left_eye_outer",
    4: "right_eye_inner", 5: "right_eye", 6: "right_eye_outer",
    7: "left_ear", 8: "right_ear",
    9: "mouth_left", 10: "mouth_right",
    11: "left_shoulder", 12: "right_shoulder",
    13: "left_elbow", 14: "right_elbow",
    15: "left_wrist", 16: "right_wrist",
    17: "left_pinky", 18: "right_pinky",
    19: "left_index", 20: "right_index",
    21: "left_thumb", 22: "right_thumb",
    23: "left_hip", 24: "right_hip",
    25: "left_knee", 26: "right_knee",
    27: "left_ankle", 28: "right_ankle",
    29: "left_heel", 30: "right_heel",
    31: "left_foot_index", 32: "right_foot_index",
}

# Curated reference biomechanical action catalog (Educational only; not measured EMG)
CURATED_ACTION_MUSCLES: Dict[str, Dict[str, Any]] = {
    "cervical_flexion": {
        "region": "neck",
        "description": "Forward bending of the cervical spine",
        "reference_range_deg": [0, 45],
        "candidate_muscles": [
            {"name": "Sternocleidomastoid", "role": "agonist", "evidence_source": "Kendall_FP_2005"},
            {"name": "Longus colli", "role": "agonist_deep", "evidence_source": "Standring_Gray_2020"},
            {"name": "Scalenus anterior", "role": "synergist", "evidence_source": "Neumann_Kinesiology_2016"},
        ],
    },
    "cervical_extension": {
        "region": "neck",
        "description": "Backward bending of the cervical spine",
        "reference_range_deg": [0, 45],
        "candidate_muscles": [
            {"name": "Splenius capitis", "role": "agonist", "evidence_source": "Kendall_FP_2005"},
            {"name": "Trapezius (upper)", "role": "synergist", "evidence_source": "Neumann_Kinesiology_2016"},
            {"name": "Semispinalis capitis", "role": "deep_extensor", "evidence_source": "Standring_Gray_2020"},
        ],
    },
    "cervical_lateral_flexion": {
        "region": "neck",
        "description": "Side bending of the neck toward the shoulder",
        "reference_range_deg": [0, 45],
        "candidate_muscles": [
            {"name": "Sternocleidomastoid (ipsilateral)", "role": "agonist", "evidence_source": "Kendall_FP_2005"},
            {"name": "Scalenes (anterior/medius)", "role": "synergist", "evidence_source": "Neumann_Kinesiology_2016"},
            {"name": "Levator scapulae", "role": "stabilizer", "evidence_source": "Standring_Gray_2020"},
        ],
    },
    "shoulder_abduction": {
        "region": "shoulder",
        "description": "Elevation of the arm laterally away from the trunk",
        "reference_range_deg": [0, 180],
        "candidate_muscles": [
            {"name": "Deltoid (middle)", "role": "prime_mover_above_15deg", "evidence_source": "Inman_Abduction_1944"},
            {"name": "Supraspinatus", "role": "initiator_0_to_15deg", "evidence_source": "Inman_Abduction_1944"},
            {"name": "Serratus anterior", "role": "scapular_upward_rotator", "evidence_source": "Neumann_Kinesiology_2016"},
            {"name": "Trapezius (upper/lower)", "role": "scapular_force_couple", "evidence_source": "Kendall_FP_2005"},
        ],
    },
    "shoulder_flexion": {
        "region": "shoulder",
        "description": "Forward elevation of the arm in the sagittal plane",
        "reference_range_deg": [0, 180],
        "candidate_muscles": [
            {"name": "Deltoid (anterior)", "role": "prime_mover", "evidence_source": "Neumann_Kinesiology_2016"},
            {"name": "Pectoralis major (clavicular head)", "role": "synergist", "evidence_source": "Kendall_FP_2005"},
            {"name": "Biceps brachii (coracobrachialis)", "role": "assistant", "evidence_source": "Standring_Gray_2020"},
        ],
    },
    "shoulder_elevation": {
        "region": "shoulder",
        "description": "Shrugging or upward displacement of the scapula",
        "reference_range_deg": [0, 40],
        "candidate_muscles": [
            {"name": "Trapezius (upper)", "role": "prime_mover", "evidence_source": "Kendall_FP_2005"},
            {"name": "Levator scapulae", "role": "synergist", "evidence_source": "Neumann_Kinesiology_2016"},
            {"name": "Rhomboids", "role": "stabilizer", "evidence_source": "Standring_Gray_2020"},
        ],
    },
}


def init_pose_tables(db: sqlite3.Connection) -> None:
    """Initialize SQLite tables for M2.11 Pose Studies and Observations."""
    db.executescript("""
    CREATE TABLE IF NOT EXISTS pose_studies (
        study_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL REFERENCES cases(case_id),
        title TEXT NOT NULL,
        camera_view TEXT NOT NULL CHECK(camera_view IN ('front', 'side_left', 'side_right', 'back', 'uncertain')),
        image_asset TEXT NOT NULL,
        image_sha256 TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS pose_landmarks (
        study_id TEXT NOT NULL REFERENCES pose_studies(study_id) ON DELETE CASCADE,
        landmark_index INTEGER NOT NULL CHECK(landmark_index BETWEEN 0 AND 32),
        name TEXT NOT NULL,
        u REAL NOT NULL CHECK(u BETWEEN 0.0 AND 1.0),
        v REAL NOT NULL CHECK(v BETWEEN 0.0 AND 1.0),
        confidence REAL NOT NULL CHECK(confidence BETWEEN 0.0 AND 1.0),
        is_manual_override INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (study_id, landmark_index)
    );
    CREATE TABLE IF NOT EXISTS pose_symptom_observations (
        observation_id TEXT PRIMARY KEY,
        study_id TEXT NOT NULL REFERENCES pose_studies(study_id) ON DELETE CASCADE,
        case_id TEXT NOT NULL REFERENCES cases(case_id),
        visit_id INTEGER REFERENCES visits(id),
        symptom_zone TEXT NOT NULL,
        pain_score INTEGER CHECK(pain_score BETWEEN 0 AND 10),
        movement_phase TEXT NOT NULL,
        reported_symptoms TEXT NOT NULL,
        functional_limitation TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_pose_study_case ON pose_studies(case_id);
    CREATE INDEX IF NOT EXISTS idx_pose_obs_case ON pose_symptom_observations(case_id, study_id);
    """)


def calculate_joint_angle(p1: tuple[float, float], vertex: tuple[float, float], p2: tuple[float, float]) -> Optional[float]:
    """Calculate 2D planar angle in degrees at vertex between p1 and p2.
    
    Returns angle in degrees [0.0, 180.0], or None if vectors are degenerate.
    """
    v1 = (p1[0] - vertex[0], p1[1] - vertex[1])
    v2 = (p2[0] - vertex[0], p2[1] - vertex[1])
    mag1 = math.hypot(v1[0], v1[1])
    mag2 = math.hypot(v2[0], v2[1])
    if mag1 < 1e-6 or mag2 < 1e-6:
        return None
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_theta))


def estimate_pose_actions(landmarks: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Estimate candidate joint actions with strict abstention semantics.
    
    If key landmarks are missing or confidence < 0.5, returns ABSTAIN instead of guessing.
    """
    estimates = []

    # 1. Left Shoulder Abduction: Angle between left hip (23), left shoulder (11), left elbow (13)
    p_hip_l = landmarks.get(23)
    p_shld_l = landmarks.get(11)
    p_elb_l = landmarks.get(13)

    if (p_hip_l and p_shld_l and p_elb_l and
        p_hip_l["confidence"] >= 0.5 and p_shld_l["confidence"] >= 0.5 and p_elb_l["confidence"] >= 0.5):
        angle = calculate_joint_angle(
            (p_hip_l["u"], p_hip_l["v"]),
            (p_shld_l["u"], p_shld_l["v"]),
            (p_elb_l["u"], p_elb_l["v"]),
        )
        if angle is not None:
            # Planar abduction approximation from trunk
            abduction_deg = round(angle, 1)
            estimates.append({
                "action": "shoulder_abduction",
                "side": "left",
                "estimated_angle_deg": abduction_deg,
                "confidence": min(p_hip_l["confidence"], p_shld_l["confidence"], p_elb_l["confidence"]),
                "status": "ESTIMATED_MODEL",
                "disclaimer": "2D single-image estimation; not clinical goniometry.",
                "candidate_muscles": CURATED_ACTION_MUSCLES["shoulder_abduction"]["candidate_muscles"],
            })
    else:
        estimates.append({
            "action": "shoulder_abduction",
            "side": "left",
            "estimated_angle_deg": None,
            "status": "ABSTAIN",
            "reason": "Key landmarks (left hip/shoulder/elbow) occluded or confidence < 0.5",
        })

    # 2. Right Shoulder Abduction: Right hip (24), Right shoulder (12), Right elbow (14)
    p_hip_r = landmarks.get(24)
    p_shld_r = landmarks.get(12)
    p_elb_r = landmarks.get(14)

    if (p_hip_r and p_shld_r and p_elb_r and
        p_hip_r["confidence"] >= 0.5 and p_shld_r["confidence"] >= 0.5 and p_elb_r["confidence"] >= 0.5):
        angle_r = calculate_joint_angle(
            (p_hip_r["u"], p_hip_r["v"]),
            (p_shld_r["u"], p_shld_r["v"]),
            (p_elb_r["u"], p_elb_r["v"]),
        )
        if angle_r is not None:
            estimates.append({
                "action": "shoulder_abduction",
                "side": "right",
                "estimated_angle_deg": round(angle_r, 1),
                "confidence": min(p_hip_r["confidence"], p_shld_r["confidence"], p_elb_r["confidence"]),
                "status": "ESTIMATED_MODEL",
                "disclaimer": "2D single-image estimation; not clinical goniometry.",
                "candidate_muscles": CURATED_ACTION_MUSCLES["shoulder_abduction"]["candidate_muscles"],
            })
    else:
        estimates.append({
            "action": "shoulder_abduction",
            "side": "right",
            "estimated_angle_deg": None,
            "status": "ABSTAIN",
            "reason": "Key landmarks (right hip/shoulder/elbow) occluded or confidence < 0.5",
        })

    # 3. Shoulder Elevation / Shrug (Relative height of shoulders vs ears/nose)
    p_nose = landmarks.get(0)
    if p_shld_l and p_shld_r and p_nose and p_shld_l["confidence"] >= 0.5 and p_shld_r["confidence"] >= 0.5:
        # If shoulders are elevated towards ears
        estimates.append({
            "action": "shoulder_elevation",
            "side": "bilateral",
            "estimated_angle_deg": None,
            "status": "CANDIDATE_POSTURE",
            "candidate_muscles": CURATED_ACTION_MUSCLES["shoulder_elevation"]["candidate_muscles"],
            "disclaimer": "Scapular posture candidate; muscle activation requires EMG validation.",
        })

    return estimates


def create_pose_study(
    db: sqlite3.Connection,
    *,
    case_id: str,
    title: str,
    camera_view: str,
    image_asset: str,
    image_sha256: str,
    raw_landmarks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Store a pose study with its landmark skeleton."""
    if not case_id.startswith("DEMO-"):
        raise ValueError("Only DEMO-* cases are permitted in Pose Explorer")
    if camera_view not in ("front", "side_left", "side_right", "back", "uncertain"):
        raise ValueError("Invalid camera_view")
    if not title.strip() or len(title) > 120:
        raise ValueError("Title must be between 1 and 120 chars")

    study_id = f"PSTD-{uuid4().hex[:16]}"
    with db:
        db.execute(
            """INSERT INTO pose_studies (study_id, case_id, title, camera_view, image_asset, image_sha256)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (study_id, case_id, title.strip(), camera_view, image_asset, image_sha256),
        )
        for lm in raw_landmarks:
            idx = int(lm["index"])
            name = MEDIAPIPE_LANDMARK_NAMES.get(idx, f"landmark_{idx}")
            u = float(lm["u"])
            v = float(lm["v"])
            conf = float(lm.get("confidence", 0.0))
            if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 and 0.0 <= conf <= 1.0):
                raise ValueError(f"Landmark {idx} coordinates or confidence out of bounds [0.0, 1.0]")
            is_manual = 1 if lm.get("is_manual_override") else 0
            db.execute(
                """INSERT INTO pose_landmarks (study_id, landmark_index, name, u, v, confidence, is_manual_override)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (study_id, idx, name, u, v, conf, is_manual),
            )
    return get_pose_study(db, study_id)  # type: ignore


def update_landmarks(
    db: sqlite3.Connection,
    study_id: str,
    overrides: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Apply manual educator corrections to key landmarks, preserving audit flag."""
    existing = db.execute("SELECT study_id FROM pose_studies WHERE study_id = ?", (study_id,)).fetchone()
    if not existing:
        raise ValueError(f"Study '{study_id}' not found")

    with db:
        for ovr in overrides:
            idx = int(ovr["index"])
            u = float(ovr["u"])
            v = float(ovr["v"])
            conf = float(ovr.get("confidence", 1.0))
            if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 and 0.0 <= conf <= 1.0):
                raise ValueError(f"Landmark {idx} override out of range [0.0, 1.0]")
            db.execute(
                """UPDATE pose_landmarks
                   SET u = ?, v = ?, confidence = ?, is_manual_override = 1
                   WHERE study_id = ? AND landmark_index = ?""",
                (u, v, conf, study_id, idx),
            )
    return get_pose_study(db, study_id)  # type: ignore


def get_pose_study(db: sqlite3.Connection, study_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full pose study including landmarks and dynamic action estimates."""
    row = db.execute(
        "SELECT study_id, case_id, title, camera_view, image_asset, image_sha256, created_at FROM pose_studies WHERE study_id = ?",
        (study_id,),
    ).fetchone()
    if not row:
        return None

    study = {
        "study_id": row[0],
        "case_id": row[1],
        "title": row[2],
        "camera_view": row[3],
        "image_asset": row[4],
        "image_sha256": row[5],
        "created_at": row[6],
    }

    lm_rows = db.execute(
        """SELECT landmark_index, name, u, v, confidence, is_manual_override
           FROM pose_landmarks WHERE study_id = ? ORDER BY landmark_index""",
        (study_id,),
    ).fetchall()

    landmarks_dict: Dict[int, Dict[str, Any]] = {}
    landmarks_list: List[Dict[str, Any]] = []
    for lm in lm_rows:
        item = {
            "index": lm[0],
            "name": lm[1],
            "u": lm[2],
            "v": lm[3],
            "confidence": lm[4],
            "is_manual_override": bool(lm[5]),
        }
        landmarks_dict[lm[0]] = item
        landmarks_list.append(item)

    study["landmarks"] = landmarks_list
    study["action_estimates"] = estimate_pose_actions(landmarks_dict)
    return study


def list_pose_studies(db: sqlite3.Connection, case_id: str) -> List[Dict[str, Any]]:
    """List all pose studies for a case."""
    rows = db.execute(
        "SELECT study_id, case_id, title, camera_view, image_asset, created_at FROM pose_studies WHERE case_id = ? ORDER BY created_at DESC",
        (case_id,),
    ).fetchall()
    return [
        {
            "study_id": r[0],
            "case_id": r[1],
            "title": r[2],
            "camera_view": r[3],
            "image_asset": r[4],
            "created_at": r[5],
        }
        for r in rows
    ]


def record_pose_observation(
    db: sqlite3.Connection,
    *,
    study_id: str,
    case_id: str,
    visit_id: Optional[int],
    symptom_zone: str,
    pain_score: Optional[int],
    movement_phase: str,
    reported_symptoms: str,
    functional_limitation: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    """Record symptom report associated with a pose study."""
    if not case_id.startswith("DEMO-"):
        raise ValueError("Only DEMO-* cases are permitted")
    if pain_score is not None and not (0 <= pain_score <= 10):
        raise ValueError("pain_score must be between 0 and 10")
    if not symptom_zone.strip() or len(symptom_zone) > 120:
        raise ValueError("symptom_zone must be 1-120 characters")

    obs_id = f"POBS-{uuid4().hex[:16]}"
    with db:
        db.execute(
            """INSERT INTO pose_symptom_observations
               (observation_id, study_id, case_id, visit_id, symptom_zone, pain_score, movement_phase, reported_symptoms, functional_limitation, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (obs_id, study_id, case_id, visit_id, symptom_zone.strip(), pain_score, movement_phase, reported_symptoms, functional_limitation, notes),
        )
    return {
        "observation_id": obs_id,
        "study_id": study_id,
        "case_id": case_id,
        "symptom_zone": symptom_zone,
        "pain_score": pain_score,
    }


def list_pose_observations(db: sqlite3.Connection, study_id: str) -> List[Dict[str, Any]]:
    """List recorded observations for a pose study."""
    rows = db.execute(
        """SELECT observation_id, study_id, case_id, visit_id, symptom_zone, pain_score, movement_phase, reported_symptoms, functional_limitation, notes, observed_at
           FROM pose_symptom_observations WHERE study_id = ? ORDER BY observed_at DESC""",
        (study_id,),
    ).fetchall()
    return [
        {
            "observation_id": r[0],
            "study_id": r[1],
            "case_id": r[2],
            "visit_id": r[3],
            "symptom_zone": r[4],
            "pain_score": r[5],
            "movement_phase": r[6],
            "reported_symptoms": r[7],
            "functional_limitation": r[8],
            "notes": r[9],
            "observed_at": r[10],
        }
        for r in rows
    ]
