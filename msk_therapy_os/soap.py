"""Structured SOAP note management with student drafting and clinical supervisor review."""
from __future__ import annotations

import sqlite3
from typing import List, Optional
from msk_therapy_os.models import ReviewStatus, SOAPRecord, UserRole


def create_soap_note(
    db: sqlite3.Connection,
    *,
    visit_id: int,
    subjective: str,
    objective: str,
    assessment: str,
    plan: str,
    author_role: str = "student",
) -> int:
    """Create a structured SOAP note for a visit.

    Enforces that:
    1. Visit exists.
    2. Author role is valid.
    3. If visit has a red flag (disposition == STOP_AND_REFER), Plan must reflect referral.
    4. Notes start in DRAFT status when created by student.
    """
    if author_role not in (UserRole.STUDENT.value, UserRole.REVIEWER.value):
        raise ValueError("author_role must be 'student' or 'reviewer'")

    visit_row = db.execute(
        "SELECT case_id, disposition, flag FROM visits WHERE id = ?", (visit_id,)
    ).fetchone()
    if not visit_row:
        raise ValueError(f"Visit ID {visit_id} does not exist.")

    case_id, disposition, flag = visit_row

    if not subjective.strip():
        raise ValueError("Subjective (S) section cannot be empty")
    if not objective.strip():
        raise ValueError("Objective (O) section cannot be empty")
    if not assessment.strip():
        raise ValueError("Assessment (A) section cannot be empty")
    if not plan.strip():
        raise ValueError("Plan (P) section cannot be empty")

    # Safety constraint: if visit disposition is STOP_AND_REFER, ensure plan warns/refers
    if disposition == "STOP_AND_REFER":
        if "refer" not in plan.lower() and "stop" not in plan.lower():
            raise ValueError(
                f"Safety Hard Stop: Visit {visit_id} has red flag '{flag}' (STOP_AND_REFER). "
                "Plan must explicitly indicate medical referral/escalation and cease physical interventions."
            )

    status = ReviewStatus.SUPERVISED.value if author_role == UserRole.REVIEWER.value else ReviewStatus.DRAFT.value
    reviewer = "Supervisor (Self-Authored)" if author_role == UserRole.REVIEWER.value else None

    cur = db.execute(
        """
        INSERT INTO soap_notes (visit_id, subjective, objective, assessment, plan,
                                author_role, reviewed_by, review_status, review_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visit_id,
            subjective.strip(),
            objective.strip(),
            assessment.strip(),
            plan.strip(),
            author_role,
            reviewer,
            status,
            None,
        ),
    )
    db.commit()
    return cur.lastrowid


def review_soap_note(
    db: sqlite3.Connection,
    *,
    soap_id: int,
    reviewer_name: str,
    reviewer_role: str,
    decision: str,
    feedback: str = "",
) -> None:
    """Supervisory review of a student SOAP note.

    Requires reviewer role. Decision can be APPROVED, REJECTED, or SUPERVISED.
    """
    if reviewer_role != UserRole.REVIEWER.value:
        raise PermissionError("Only users with 'reviewer' role can approve or reject SOAP notes.")

    if not reviewer_name or not reviewer_name.strip():
        raise ValueError("reviewer_name is required for supervisory audit trail")

    decision_upper = decision.strip().upper()
    valid_decisions = (ReviewStatus.APPROVED.value, ReviewStatus.REJECTED.value, ReviewStatus.SUPERVISED.value)
    if decision_upper not in valid_decisions:
        raise ValueError(f"decision must be one of: {', '.join(valid_decisions)}")

    soap_row = db.execute("SELECT id FROM soap_notes WHERE id = ?", (soap_id,)).fetchone()
    if not soap_row:
        raise ValueError(f"SOAP note ID {soap_id} does not exist.")

    db.execute(
        """
        UPDATE soap_notes
        SET reviewed_by = ?, review_status = ?, review_notes = ?
        WHERE id = ?
        """,
        (reviewer_name.strip(), decision_upper, feedback.strip(), soap_id),
    )
    db.commit()


def get_soap_notes_for_visit(db: sqlite3.Connection, visit_id: int) -> List[SOAPRecord]:
    """Retrieve all SOAP notes associated with a visit."""
    rows = db.execute(
        """
        SELECT id, visit_id, subjective, objective, assessment, plan,
               author_role, reviewed_by, review_status, review_notes, created_utc
        FROM soap_notes WHERE visit_id = ? ORDER BY id
        """,
        (visit_id,),
    ).fetchall()
    return [
        SOAPRecord(
            id=r[0],
            visit_id=r[1],
            subjective=r[2],
            objective=r[3],
            assessment=r[4],
            plan=r[5],
            author_role=r[6],
            reviewed_by=r[7],
            review_status=r[8],
            review_notes=r[9],
            created_utc=r[10],
        )
        for r in rows
    ]
