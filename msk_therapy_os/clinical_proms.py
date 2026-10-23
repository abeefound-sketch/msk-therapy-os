"""M3 Clinical PROMs, CTCAE Adverse Event Grading, and Cohort Analytics.

Provides standardized Patient-Reported Outcome Measures (NDI, QuickDASH, RMDQ),
CTCAE v5.0 Adverse Event tracking, and synthetic multi-patient cohort management.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional
from uuid import uuid4

# CTCAE v5.0 Severity Grades
CTCAE_GRADES = {
    1: "Grade 1: Mild; asymptomatic or mild symptoms; clinical observation only; intervention not indicated.",
    2: "Grade 2: Moderate; minimal, local or noninvasive intervention indicated; limiting instrumental ADL.",
    3: "Grade 3: Severe or medically significant but not immediately life-threatening; disabling; limiting self-care ADL.",
    4: "Grade 4: Life-threatening consequences; urgent intervention indicated.",
    5: "Grade 5: Death related to adverse event.",
}

# Supported PROM Questionnaires
PROM_CATALOG = {
    "NDI": {
        "title": "Neck Disability Index",
        "region": "neck",
        "num_items": 10,
        "item_score_range": (0, 5),
        "max_score": 50,
        "interpretation": "0-4: No disability, 5-14: Mild, 15-24: Moderate, 25-34: Severe, >34: Complete",
    },
    "QuickDASH": {
        "title": "Quick Disabilities of the Arm, Shoulder and Hand",
        "region": "shoulder",
        "num_items": 11,
        "item_score_range": (1, 5),
        "max_score": 100,
        "interpretation": "0-100: Higher score represents greater disability",
    },
    "RMDQ": {
        "title": "Roland-Morris Disability Questionnaire",
        "region": "low_back",
        "num_items": 24,
        "item_score_range": (0, 1),
        "max_score": 24,
        "interpretation": "0-24: Total items checked indicating functional back impairment",
    },
}


def init_prom_and_cohort_tables(db: sqlite3.Connection) -> None:
    """Initialize SQLite tables for PROMs and CTCAE Adverse Events."""
    db.executescript("""
    CREATE TABLE IF NOT EXISTS patient_proms (
        prom_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL REFERENCES cases(case_id),
        visit_id INTEGER REFERENCES visits(id),
        prom_type TEXT NOT NULL CHECK(prom_type IN ('NDI', 'QuickDASH', 'RMDQ')),
        item_responses_json TEXT NOT NULL,
        raw_score REAL NOT NULL,
        percentage_score REAL NOT NULL,
        interpretation TEXT NOT NULL,
        administered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS adverse_events (
        event_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL REFERENCES cases(case_id),
        visit_id INTEGER REFERENCES visits(id),
        event_category TEXT NOT NULL,
        ctcae_grade INTEGER NOT NULL CHECK(ctcae_grade BETWEEN 1 AND 5),
        symptom_description TEXT NOT NULL,
        onset_utc TEXT NOT NULL,
        resolution_status TEXT NOT NULL CHECK(resolution_status IN ('resolved', 'ongoing', 'sequelae')),
        action_taken TEXT NOT NULL,
        reported_by TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_proms_case ON patient_proms(case_id);
    CREATE INDEX IF NOT EXISTS idx_ae_case ON adverse_events(case_id);
    """)


def calculate_ndi_score(responses: List[int]) -> Dict[str, Any]:
    """Calculate Neck Disability Index (10 items, 0-5 each)."""
    if len(responses) != 10:
        raise ValueError("NDI requires exactly 10 item responses")
    for r in responses:
        if not (0 <= r <= 5):
            raise ValueError(f"NDI item response {r} out of range [0, 5]")
    raw = sum(responses)
    pct = round((raw / 50.0) * 100.0, 1)
    if raw <= 4:
        interp = "No disability"
    elif raw <= 14:
        interp = "Mild disability"
    elif raw <= 24:
        interp = "Moderate disability"
    elif raw <= 34:
        interp = "Severe disability"
    else:
        interp = "Complete disability"
    return {"raw_score": raw, "percentage_score": pct, "interpretation": interp}


def calculate_quickdash_score(responses: List[int]) -> Dict[str, Any]:
    """Calculate QuickDASH score (11 items, 1-5 each, scaled to 0-100)."""
    if len(responses) != 11:
        raise ValueError("QuickDASH requires exactly 11 item responses")
    for r in responses:
        if not (1 <= r <= 5):
            raise ValueError(f"QuickDASH item response {r} out of range [1, 5]")
    raw = sum(responses)
    # QuickDASH formula: [ (sum of 11 items / 11) - 1 ] * 25
    mean_val = raw / 11.0
    pct = round((mean_val - 1.0) * 25.0, 1)
    return {"raw_score": raw, "percentage_score": pct, "interpretation": f"Disability score {pct}/100"}


def calculate_rmdq_score(responses: List[int]) -> Dict[str, Any]:
    """Calculate Roland-Morris Disability Questionnaire (24 items, 0 or 1)."""
    if len(responses) != 24:
        raise ValueError("RMDQ requires exactly 24 binary items (0 or 1)")
    for r in responses:
        if r not in (0, 1):
            raise ValueError(f"RMDQ item response {r} must be 0 or 1")
    raw = sum(responses)
    pct = round((raw / 24.0) * 100.0, 1)
    return {"raw_score": raw, "percentage_score": pct, "interpretation": f"Impairment score {raw}/24 ({pct}%)"}


def record_prom_response(
    db: sqlite3.Connection,
    *,
    case_id: str,
    visit_id: Optional[int],
    prom_type: str,
    item_responses: List[int],
) -> Dict[str, Any]:
    """Validate and record a PROM questionnaire submission."""
    if not case_id.startswith("DEMO-"):
        raise ValueError("Synthetic DEMO-* cases only")
    if prom_type not in PROM_CATALOG:
        raise ValueError(f"Unknown prom_type '{prom_type}'")

    if prom_type == "NDI":
        scored = calculate_ndi_score(item_responses)
    elif prom_type == "QuickDASH":
        scored = calculate_quickdash_score(item_responses)
    elif prom_type == "RMDQ":
        scored = calculate_rmdq_score(item_responses)
    else:
        raise ValueError(f"Unsupported PROM type {prom_type}")

    prom_id = f"PROM-{uuid4().hex[:16]}"
    with db:
        db.execute(
            """INSERT INTO patient_proms
               (prom_id, case_id, visit_id, prom_type, item_responses_json, raw_score, percentage_score, interpretation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                prom_id,
                case_id,
                visit_id,
                prom_type,
                json.dumps(item_responses),
                scored["raw_score"],
                scored["percentage_score"],
                scored["interpretation"],
            ),
        )

    return {
        "prom_id": prom_id,
        "case_id": case_id,
        "prom_type": prom_type,
        "raw_score": scored["raw_score"],
        "percentage_score": scored["percentage_score"],
        "interpretation": scored["interpretation"],
    }


def list_prom_responses(db: sqlite3.Connection, case_id: str) -> List[Dict[str, Any]]:
    """List historical PROMs for a case."""
    rows = db.execute(
        """SELECT prom_id, case_id, visit_id, prom_type, raw_score, percentage_score, interpretation, administered_at
           FROM patient_proms WHERE case_id = ? ORDER BY administered_at ASC""",
        (case_id,),
    ).fetchall()
    return [
        {
            "prom_id": r[0],
            "case_id": r[1],
            "visit_id": r[2],
            "prom_type": r[3],
            "raw_score": r[4],
            "percentage_score": r[5],
            "interpretation": r[6],
            "administered_at": r[7],
        }
        for r in rows
    ]


def record_adverse_event(
    db: sqlite3.Connection,
    *,
    case_id: str,
    visit_id: Optional[int],
    event_category: str,
    ctcae_grade: int,
    symptom_description: str,
    onset_utc: str,
    resolution_status: str,
    action_taken: str,
    reported_by: str,
) -> Dict[str, Any]:
    """Record a CTCAE v5.0 classified adverse event."""
    if not case_id.startswith("DEMO-"):
        raise ValueError("Synthetic DEMO-* cases only")
    if ctcae_grade not in CTCAE_GRADES:
        raise ValueError("ctcae_grade must be an integer between 1 and 5")
    if resolution_status not in ("resolved", "ongoing", "sequelae"):
        raise ValueError("resolution_status must be resolved, ongoing, or sequelae")
    if not symptom_description.strip() or len(symptom_description) > 500:
        raise ValueError("symptom_description must be 1-500 characters")

    event_id = f"AE-{uuid4().hex[:16]}"
    with db:
        db.execute(
            """INSERT INTO adverse_events
               (event_id, case_id, visit_id, event_category, ctcae_grade, symptom_description, onset_utc, resolution_status, action_taken, reported_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event_id,
                case_id,
                visit_id,
                event_category,
                ctcae_grade,
                symptom_description.strip(),
                onset_utc,
                resolution_status,
                action_taken.strip(),
                reported_by.strip(),
            ),
        )

    return {
        "event_id": event_id,
        "case_id": case_id,
        "ctcae_grade": ctcae_grade,
        "grade_description": CTCAE_GRADES[ctcae_grade],
        "symptom_description": symptom_description,
    }


def list_adverse_events(db: sqlite3.Connection, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List adverse events filtered optionally by case."""
    sql = """SELECT event_id, case_id, visit_id, event_category, ctcae_grade, symptom_description, onset_utc, resolution_status, action_taken, reported_by, created_at
             FROM adverse_events"""
    args = ()
    if case_id:
        sql += " WHERE case_id = ?"
        args = (case_id,)
    sql += " ORDER BY created_at DESC"

    rows = db.execute(sql, args).fetchall()
    return [
        {
            "event_id": r[0],
            "case_id": r[1],
            "visit_id": r[2],
            "event_category": r[3],
            "ctcae_grade": r[4],
            "grade_description": CTCAE_GRADES[r[4]],
            "symptom_description": r[5],
            "onset_utc": r[6],
            "resolution_status": r[7],
            "action_taken": r[8],
            "reported_by": r[9],
            "created_at": r[10],
        }
        for r in rows
    ]


def seed_synthetic_m3_cohort(db: sqlite3.Connection) -> None:
    """Seed multi-patient synthetic cohort cases with diverse MSK scenarios."""
    cases_to_seed = [
        ("DEMO-SHOULDER-003", "Fictional right shoulder impingement & rotator cuff tension"),
        ("DEMO-KNEE-004", "Fictional bilateral patellofemoral tracking discomfort"),
    ]
    with db:
        for cid, lbl in cases_to_seed:
            db.execute("INSERT OR IGNORE INTO cases (case_id, label) VALUES (?, ?)", (cid, lbl))
