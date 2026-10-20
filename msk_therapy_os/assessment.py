"""Structured clinical intake, objective ROM measurements, and scenario questionnaires."""
from __future__ import annotations

import sqlite3
from typing import List, Optional
from msk_therapy_os.models import (
    IntakeRecord,
    QuestionnaireItem,
    ROMMethod,
    ROMRecord,
    ROMSide,
)

VALID_AGE_BANDS = ("18-29", "30-49", "50-64", "65-79", "80+")
VALID_REGIONS = ("neck", "low_back", "thoracic", "shoulder", "hip", "face", "general")
VALID_SIDES = tuple(s.value for s in ROMSide)
VALID_METHODS = tuple(m.value for m in ROMMethod)

DEFAULT_QUESTIONNAIRES: List[QuestionnaireItem] = [
    QuestionnaireItem(
        item_id="Q-NECK-001",
        region="neck",
        scenario_title="Cervical Spine Red Flags Screening",
        question_text="Does the individual report numbness/clumsiness in both hands, progressive balance difficulty, or electric shock sensations down the spine when bending the neck (Lhermitte's)?",
        safety_critical=True,
        evidence_id="EVID-G-002",
    ),
    QuestionnaireItem(
        item_id="Q-NECK-002",
        region="neck",
        scenario_title="Cervical Range of Motion & Mechanical Assessment",
        question_text="Is neck movement restricted primarily in rotation or lateral flexion, and does movement reproduce localized muscular tenderness versus radicular arm pain?",
        safety_critical=False,
        evidence_id="EVID-A-002",
    ),
    QuestionnaireItem(
        item_id="Q-LUMB-001",
        region="low_back",
        scenario_title="Lumbar Spine Red Flags Screening",
        question_text="Does the individual report new-onset urinary incontinence/retention, loss of bowel control, or sensory loss in the perianal/saddle area?",
        safety_critical=True,
        evidence_id="EVID-G-001",
    ),
    QuestionnaireItem(
        item_id="Q-LUMB-002",
        region="low_back",
        scenario_title="Lumbar Functional Limitation & Sciatic Screening",
        question_text="Does pain radiate below the knee with sensory change in dermatomal distribution, or is pain confined to the lumbosacral region without neurological deficit?",
        safety_critical=False,
        evidence_id="EVID-G-001",
    ),
]


def validate_intake_data(
    case_id: str,
    age_band: str,
    symptom_onset: str,
    primary_region: str,
    functional_limits: str,
    prior_care: str,
    operator_role: str,
) -> None:
    if not case_id.startswith("DEMO-"):
        raise ValueError("Synthetic DEMO-* cases only; real patient identifiers are rejected.")
    if age_band not in VALID_AGE_BANDS:
        raise ValueError(f"age_band must be one of: {', '.join(VALID_AGE_BANDS)}")
    if primary_region.lower() not in VALID_REGIONS:
        raise ValueError(f"primary_region must be one of: {', '.join(VALID_REGIONS)}")
    if not symptom_onset.strip():
        raise ValueError("symptom_onset cannot be empty")
    if not functional_limits.strip():
        raise ValueError("functional_limits cannot be empty")
    if operator_role not in ("student", "reviewer"):
        raise ValueError("operator_role must be 'student' or 'reviewer'")


def record_intake(
    db: sqlite3.Connection,
    *,
    case_id: str,
    age_band: str,
    symptom_onset: str,
    primary_region: str,
    functional_limits: str,
    prior_care: str,
    operator_role: str = "student",
) -> None:
    """Validate and record a structured intake questionnaire response."""
    validate_intake_data(
        case_id, age_band, symptom_onset, primary_region, functional_limits, prior_care, operator_role
    )
    # Check that case exists
    case_row = db.execute("SELECT 1 FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if not case_row:
        raise ValueError(f"Case '{case_id}' does not exist. Initialize or seed case first.")

    db.execute(
        """
        INSERT INTO intakes (case_id, age_band, symptom_onset, primary_region,
                             functional_limits, prior_care, operator_role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(case_id) DO UPDATE SET
            age_band = excluded.age_band,
            symptom_onset = excluded.symptom_onset,
            primary_region = excluded.primary_region,
            functional_limits = excluded.functional_limits,
            prior_care = excluded.prior_care,
            operator_role = excluded.operator_role
        """,
        (
            case_id,
            age_band,
            symptom_onset.strip(),
            primary_region.strip().lower(),
            functional_limits.strip(),
            prior_care.strip(),
            operator_role,
        ),
    )
    db.commit()


def get_intake(db: sqlite3.Connection, case_id: str) -> Optional[IntakeRecord]:
    """Retrieve intake record for a case."""
    row = db.execute(
        """SELECT case_id, age_band, symptom_onset, primary_region, functional_limits,
                  prior_care, operator_role, created_utc
           FROM intakes WHERE case_id = ?""",
        (case_id,),
    ).fetchone()
    if not row:
        return None
    return IntakeRecord(
        case_id=row[0],
        age_band=row[1],
        symptom_onset=row[2],
        primary_region=row[3],
        functional_limits=row[4],
        prior_care=row[5],
        operator_role=row[6],
        created_utc=row[7],
    )


def validate_rom_measurement(motion: str, side: str, angle_deg: float, method: str) -> None:
    """Validate objective ROM measurement schema."""
    if not motion or not motion.strip():
        raise ValueError("motion description cannot be empty")
    if side.lower() not in VALID_SIDES:
        raise ValueError(f"side must be one of: {', '.join(VALID_SIDES)}")
    if not (0.0 <= angle_deg <= 360.0):
        raise ValueError("angle_deg must be between 0.0 and 360.0 degrees")
    if method.lower() not in VALID_METHODS:
        raise ValueError(f"method must be one of: {', '.join(VALID_METHODS)}")


def record_rom(
    db: sqlite3.Connection,
    *,
    visit_id: int,
    motion: str,
    side: str,
    angle_deg: float,
    method: str,
) -> int:
    """Record a structured ROM measurement tied to a visit."""
    validate_rom_measurement(motion, side, angle_deg, method)
    visit = db.execute("SELECT 1 FROM visits WHERE id = ?", (visit_id,)).fetchone()
    if not visit:
        raise ValueError(f"Visit ID {visit_id} does not exist.")

    cur = db.execute(
        """INSERT INTO rom_assessments (visit_id, motion, side, angle_deg, method)
           VALUES (?, ?, ?, ?, ?)""",
        (visit_id, motion.strip().lower(), side.lower(), angle_deg, method.lower()),
    )
    db.commit()
    return cur.lastrowid


def get_visit_rom(db: sqlite3.Connection, visit_id: int) -> List[ROMRecord]:
    """Get all structured ROM records for a visit."""
    rows = db.execute(
        "SELECT id, visit_id, motion, side, angle_deg, method FROM rom_assessments WHERE visit_id = ? ORDER BY id",
        (visit_id,),
    ).fetchall()
    return [
        ROMRecord(id=r[0], visit_id=r[1], motion=r[2], side=r[3], angle_deg=r[4], method=r[5])
        for r in rows
    ]


def list_questionnaires(
    db: sqlite3.Connection, region: Optional[str] = None
) -> List[QuestionnaireItem]:
    """List scenario-based assessment questionnaires."""
    query = (
        "SELECT item_id, region, scenario_title, question_text, safety_critical, evidence_id "
        "FROM questionnaires"
    )
    params = []
    if region:
        query += " WHERE region = ?"
        params.append(region.strip().lower())
    query += " ORDER BY region, item_id"

    rows = db.execute(query, params).fetchall()
    return [
        QuestionnaireItem(
            item_id=r[0],
            region=r[1],
            scenario_title=r[2],
            question_text=r[3],
            safety_critical=bool(r[4]),
            evidence_id=r[5],
        )
        for r in rows
    ]
