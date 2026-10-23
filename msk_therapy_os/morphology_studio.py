"""M2.12 Three-Photo Patient Morphology Studio.

Generates and adjusts approximate, editable 3D/2D patient surface-only avatars
from anthropometric girths and three-view silhouettes.
Strictly prohibits internal tissue reconstruction or patient-specific acupuncture depth claims.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Anthropometric physiological ranges
PARAM_BOUNDS = {
    "height_cm": (100.0, 230.0),
    "weight_kg": (30.0, 250.0),
    "chest_circ_cm": (50.0, 180.0),
    "waist_circ_cm": (40.0, 180.0),
    "hip_circ_cm": (50.0, 180.0),
    "arm_circ_cm": (15.0, 65.0),
    "thigh_circ_cm": (25.0, 95.0),
    "calf_circ_cm": (18.0, 65.0),
    "shoulder_width_cm": (25.0, 65.0),
    "abdomen_prominence": (-1.0, 2.0),
    "pelvic_tilt_deg": (-25.0, 25.0),
}


def init_morphology_tables(db: sqlite3.Connection) -> None:
    """Initialize SQLite tables for M2.12 Morphology Studio."""
    db.executescript("""
    CREATE TABLE IF NOT EXISTS morphology_avatars (
        avatar_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL REFERENCES cases(case_id),
        version_num INTEGER NOT NULL DEFAULT 1,
        title TEXT NOT NULL,
        height_cm REAL NOT NULL CHECK(height_cm BETWEEN 100.0 AND 230.0),
        weight_kg REAL CHECK(weight_kg BETWEEN 30.0 AND 250.0),
        chest_circ_cm REAL CHECK(chest_circ_cm BETWEEN 50.0 AND 180.0),
        waist_circ_cm REAL CHECK(waist_circ_cm BETWEEN 40.0 AND 180.0),
        hip_circ_cm REAL CHECK(hip_circ_cm BETWEEN 50.0 AND 180.0),
        params_json TEXT NOT NULL DEFAULT '{}',
        photo_front_asset TEXT NOT NULL DEFAULT '',
        photo_side_asset TEXT NOT NULL DEFAULT '',
        photo_back_asset TEXT NOT NULL DEFAULT '',
        model_space TEXT NOT NULL DEFAULT 'PATIENT_SURFACE_APPROXIMATE_V1',
        disclaimer TEXT NOT NULL DEFAULT 'APPROXIMATE_EXTERNAL_SURFACE_ONLY; Not validated for internal anatomy or tissue depth',
        status TEXT NOT NULL CHECK(status IN ('draft', 'reviewed', 'locked')) DEFAULT 'draft',
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (case_id, version_num)
    );
    CREATE TABLE IF NOT EXISTS morphology_observations (
        observation_id TEXT PRIMARY KEY,
        avatar_id TEXT NOT NULL REFERENCES morphology_avatars(avatar_id) ON DELETE CASCADE,
        case_id TEXT NOT NULL REFERENCES cases(case_id),
        visit_id INTEGER REFERENCES visits(id),
        body_region TEXT NOT NULL,
        observation_type TEXT NOT NULL CHECK(observation_type IN ('circumference_delta', 'edema_swelling', 'asymmetry', 'palpable_finding', 'posture')),
        severity INTEGER CHECK(severity BETWEEN 0 AND 10),
        findings_summary TEXT NOT NULL,
        operator_notes TEXT NOT NULL DEFAULT '',
        observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_morph_avatar_case ON morphology_avatars(case_id);
    CREATE INDEX IF NOT EXISTS idx_morph_obs_avatar ON morphology_observations(avatar_id);
    """)


def validate_morphology_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate anthropometric parameters against physiological bounds."""
    cleaned: Dict[str, Any] = {}
    for key, (min_v, max_v) in PARAM_BOUNDS.items():
        if key in params and params[key] is not None:
            try:
                val = float(params[key])
                if not (min_v <= val <= max_v):
                    raise ValueError(f"Parameter '{key}' value {val} out of bounds [{min_v}, {max_v}]")
                cleaned[key] = round(val, 2)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid value for parameter '{key}': {e}")
    return cleaned


def create_avatar(
    db: sqlite3.Connection,
    *,
    case_id: str,
    title: str,
    height_cm: float,
    weight_kg: Optional[float] = None,
    chest_circ_cm: Optional[float] = None,
    waist_circ_cm: Optional[float] = None,
    hip_circ_cm: Optional[float] = None,
    extra_params: Optional[Dict[str, Any]] = None,
    photo_front: str = "",
    photo_side: str = "",
    photo_back: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    """Create a new versioned surface avatar record."""
    if not case_id.startswith("DEMO-"):
        raise ValueError("Only synthetic DEMO-* cases are permitted in Morphology Studio")
    if not title.strip() or len(title) > 120:
        raise ValueError("Title must be between 1 and 120 characters")

    # Validate height
    if not (100.0 <= height_cm <= 230.0):
        raise ValueError("Height must be between 100.0 and 230.0 cm")

    # Validate optional circumferences
    params_to_validate = {
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "chest_circ_cm": chest_circ_cm,
        "waist_circ_cm": waist_circ_cm,
        "hip_circ_cm": hip_circ_cm,
        **(extra_params or {}),
    }
    validated_params = validate_morphology_params(params_to_validate)

    avatar_id = f"AVTR-{uuid4().hex[:16]}"
    # Determine version number for this case
    max_ver = db.execute("SELECT MAX(version_num) FROM morphology_avatars WHERE case_id = ?", (case_id,)).fetchone()[0]
    next_ver = (max_ver or 0) + 1

    with db:
        db.execute(
            """INSERT INTO morphology_avatars
               (avatar_id, case_id, version_num, title, height_cm, weight_kg, chest_circ_cm, waist_circ_cm, hip_circ_cm,
                params_json, photo_front_asset, photo_side_asset, photo_back_asset, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                avatar_id,
                case_id,
                next_ver,
                title.strip(),
                validated_params["height_cm"],
                validated_params.get("weight_kg"),
                validated_params.get("chest_circ_cm"),
                validated_params.get("waist_circ_cm"),
                validated_params.get("hip_circ_cm"),
                json.dumps(validated_params),
                photo_front,
                photo_side,
                photo_back,
                notes,
            ),
        )

    return get_avatar(db, avatar_id)  # type: ignore


def update_avatar_params(
    db: sqlite3.Connection,
    avatar_id: str,
    updated_params: Dict[str, Any],
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Update editable surface parameters of a draft avatar."""
    row = db.execute("SELECT status, params_json FROM morphology_avatars WHERE avatar_id = ?", (avatar_id,)).fetchone()
    if not row:
        raise ValueError(f"Avatar '{avatar_id}' not found")
    if row[0] == "locked":
        raise PermissionError("Locked avatar cannot be modified; create a new version")

    cur_params = json.loads(row[1])
    cur_params.update(updated_params)
    validated = validate_morphology_params(cur_params)

    with db:
        sql = """UPDATE morphology_avatars
                 SET height_cm = ?, weight_kg = ?, chest_circ_cm = ?, waist_circ_cm = ?, hip_circ_cm = ?, params_json = ?"""
        args: List[Any] = [
            validated.get("height_cm", 170.0),
            validated.get("weight_kg"),
            validated.get("chest_circ_cm"),
            validated.get("waist_circ_cm"),
            validated.get("hip_circ_cm"),
            json.dumps(validated),
        ]
        if notes is not None:
            sql += ", notes = ?"
            args.append(notes)
        sql += " WHERE avatar_id = ?"
        args.append(avatar_id)
        db.execute(sql, args)

    return get_avatar(db, avatar_id)  # type: ignore


def get_avatar(db: sqlite3.Connection, avatar_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full avatar representation."""
    row = db.execute(
        """SELECT avatar_id, case_id, version_num, title, height_cm, weight_kg, chest_circ_cm, waist_circ_cm, hip_circ_cm,
                  params_json, photo_front_asset, photo_side_asset, photo_back_asset, model_space, disclaimer, status, notes, created_at
           FROM morphology_avatars WHERE avatar_id = ?""",
        (avatar_id,),
    ).fetchone()
    if not row:
        return None

    return {
        "avatar_id": row[0],
        "case_id": row[1],
        "version_num": row[2],
        "title": row[3],
        "height_cm": row[4],
        "weight_kg": row[5],
        "chest_circ_cm": row[6],
        "waist_circ_cm": row[7],
        "hip_circ_cm": row[8],
        "params": json.loads(row[9]),
        "photo_front_asset": row[10],
        "photo_side_asset": row[11],
        "photo_back_asset": row[12],
        "model_space": row[13],
        "disclaimer": row[14],
        "status": row[15],
        "notes": row[16],
        "created_at": row[17],
    }


def list_avatars(db: sqlite3.Connection, case_id: str) -> List[Dict[str, Any]]:
    """List avatars for a specific case."""
    rows = db.execute(
        """SELECT avatar_id, case_id, version_num, title, height_cm, weight_kg, status, created_at
           FROM morphology_avatars WHERE case_id = ? ORDER BY version_num DESC""",
        (case_id,),
    ).fetchall()
    return [
        {
            "avatar_id": r[0],
            "case_id": r[1],
            "version_num": r[2],
            "title": r[3],
            "height_cm": r[4],
            "weight_kg": r[5],
            "status": r[6],
            "created_at": r[7],
        }
        for r in rows
    ]


def record_morphology_observation(
    db: sqlite3.Connection,
    *,
    avatar_id: str,
    case_id: str,
    visit_id: Optional[int],
    body_region: str,
    observation_type: str,
    severity: Optional[int],
    findings_summary: str,
    operator_notes: str = "",
) -> Dict[str, Any]:
    """Attach structured observation to avatar surface region."""
    if not case_id.startswith("DEMO-"):
        raise ValueError("Only synthetic DEMO-* cases are permitted")
    if observation_type not in ('circumference_delta', 'edema_swelling', 'asymmetry', 'palpable_finding', 'posture'):
        raise ValueError("Invalid observation_type")
    if severity is not None and not (0 <= severity <= 10):
        raise ValueError("severity must be between 0 and 10")
    if not findings_summary.strip() or len(findings_summary) > 500:
        raise ValueError("findings_summary must be 1-500 characters")

    obs_id = f"MOBS-{uuid4().hex[:16]}"
    with db:
        db.execute(
            """INSERT INTO morphology_observations
               (observation_id, avatar_id, case_id, visit_id, body_region, observation_type, severity, findings_summary, operator_notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (obs_id, avatar_id, case_id, visit_id, body_region, observation_type, severity, findings_summary.strip(), operator_notes),
        )

    return {
        "observation_id": obs_id,
        "avatar_id": avatar_id,
        "case_id": case_id,
        "body_region": body_region,
        "observation_type": observation_type,
    }


def list_morphology_observations(db: sqlite3.Connection, avatar_id: str) -> List[Dict[str, Any]]:
    """List all observations anchored to an avatar."""
    rows = db.execute(
        """SELECT observation_id, avatar_id, case_id, visit_id, body_region, observation_type, severity, findings_summary, operator_notes, observed_at
           FROM morphology_observations WHERE avatar_id = ? ORDER BY observed_at DESC""",
        (avatar_id,),
    ).fetchall()
    return [
        {
            "observation_id": r[0],
            "avatar_id": r[1],
            "case_id": r[2],
            "visit_id": r[3],
            "body_region": r[4],
            "observation_type": r[5],
            "severity": r[6],
            "findings_summary": r[7],
            "operator_notes": r[8],
            "observed_at": r[9],
        }
        for r in rows
    ]
