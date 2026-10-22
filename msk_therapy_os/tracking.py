"""Longitudinal tracking, structured anatomical observations, therapy sessions, and FHIR R4 export."""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

from msk_therapy_os.models import ObservationRecord, SessionRecord


def record_observation(
    db: sqlite3.Connection,
    visit_id: int,
    structure_id: str,
    structure_type: str,
    observation_type: str,
    severity: int,
    finding: str,
    interpretation: str = "",
) -> int:
    """Record an objective anatomical or acupoint observation linked to a specific visit."""
    if not (0 <= severity <= 10):
        raise ValueError(f"Severity must be between 0 and 10, got {severity}")
    if structure_type not in ("anatomy", "acupoint", "traditional_sen"):
        raise ValueError(f"Invalid structure_type: {structure_type}")
    if observation_type not in (
        "palpation",
        "pain_location",
        "trigger_point",
        "neurological",
        "rom_restriction",
        "traditional_pattern",
    ):
        raise ValueError(f"Invalid observation_type: {observation_type}")

    # Verify visit exists
    visit = db.execute("SELECT id FROM visits WHERE id = ?", (visit_id,)).fetchone()
    if not visit:
        raise ValueError(f"Visit ID {visit_id} does not exist")

    # Verify structure exists in catalog
    struct = db.execute("SELECT structure_id FROM anatomy_structures WHERE structure_id = ?", (structure_id,)).fetchone()
    if not struct:
        raise ValueError(f"Structure ID '{structure_id}' not found in anatomy catalog")

    cur = db.execute(
        """
        INSERT INTO clinical_observations
        (visit_id, structure_id, structure_type, observation_type, severity, finding, interpretation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (visit_id, structure_id, structure_type, observation_type, severity, finding.strip(), interpretation.strip()),
    )
    db.commit()
    return int(cur.lastrowid)


def list_observations(
    db: sqlite3.Connection,
    visit_id: Optional[int] = None,
    case_id: Optional[str] = None,
    structure_id: Optional[str] = None,
) -> List[ObservationRecord]:
    """Query observations filtered by visit, case, or structure ID."""
    query = (
        "SELECT o.id, o.visit_id, o.structure_id, o.structure_type, o.observation_type, "
        "o.severity, o.finding, o.interpretation, o.created_utc "
        "FROM clinical_observations o "
        "JOIN visits v ON o.visit_id = v.id"
    )
    conditions = []
    params: list = []
    if visit_id is not None:
        conditions.append("o.visit_id = ?")
        params.append(visit_id)
    if case_id is not None:
        conditions.append("v.case_id = ?")
        params.append(case_id)
    if structure_id is not None:
        conditions.append("o.structure_id = ?")
        params.append(structure_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY v.visit_date ASC, o.id ASC"

    rows = db.execute(query, params).fetchall()
    return [
        ObservationRecord(
            id=r[0],
            visit_id=r[1],
            structure_id=r[2],
            structure_type=r[3],
            observation_type=r[4],
            severity=r[5],
            finding=r[6],
            interpretation=r[7],
            created_utc=r[8],
        )
        for r in rows
    ]


def record_session(
    db: sqlite3.Connection,
    visit_id: int,
    modality: str,
    duration_min: int,
    target_structures: str,
    parameters: str,
    adverse_reactions: str = "none",
    practitioner_role: str = "student",
) -> int:
    """Record a therapy session (massage, Thai massage, DDS, acupressure)."""
    if duration_min <= 0:
        raise ValueError(f"Duration must be greater than 0, got {duration_min}")
    if practitioner_role not in ("student", "reviewer"):
        raise ValueError(f"Invalid practitioner role: {practitioner_role}")

    mod_clean = modality.strip().lower()
    if mod_clean == "spinal_manipulation":
        raise ValueError("Safety Hard Stop: High-velocity spinal manipulation is strictly prohibited in MSK-Therapy-OS.")

    # Verify visit exists and check safety flags
    visit = db.execute("SELECT id, case_id, flag, disposition FROM visits WHERE id = ?", (visit_id,)).fetchone()
    if not visit:
        raise ValueError(f"Visit ID {visit_id} does not exist")

    v_id, case_id, flag, disposition = visit
    if disposition == "STOP_AND_REFER" or (flag and flag.lower() != "none"):
        # Check if specialist referral clearance has been recorded and approved
        cursor = db.cursor()
        has_clearance = False
        cursor.execute(
            """SELECT plan, assessment, review_status, review_notes FROM soap_notes
               WHERE visit_id = ? AND review_status IN ('APPROVED', 'SUPERVISED')""",
            (visit_id,)
        )
        for s_plan, s_assess, s_status, s_notes in cursor.fetchall():
            content = f"{s_plan} {s_assess} {s_notes}".lower()
            if any(term in content for term in ("specialist clearance", "referral clearance", "medical clearance", "cleared by physician", "cleared by specialist")):
                has_clearance = True
                break
        if not has_clearance:
            raise ValueError(
                f"Safety Hard Stop: Visit {visit_id} has active red flag '{flag}' (disposition: {disposition}). "
                "Downstream manual therapy and treatment sessions are strictly prohibited without documented and approved specialist referral clearance."
            )

    cur = db.execute(
        """
        INSERT INTO therapy_sessions
        (visit_id, modality, duration_min, target_structures, parameters, adverse_reactions, practitioner_role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (visit_id, modality.strip(), duration_min, target_structures.strip(), parameters.strip(), adverse_reactions.strip(), practitioner_role),
    )
    db.commit()
    return int(cur.lastrowid)


def list_sessions(
    db: sqlite3.Connection,
    visit_id: Optional[int] = None,
    case_id: Optional[str] = None,
) -> List[SessionRecord]:
    """Query therapy sessions filtered by visit or case ID."""
    query = (
        "SELECT s.id, s.visit_id, s.modality, s.duration_min, s.target_structures, "
        "s.parameters, s.adverse_reactions, s.practitioner_role, s.created_utc "
        "FROM therapy_sessions s "
        "JOIN visits v ON s.visit_id = v.id"
    )
    conditions = []
    params: list = []
    if visit_id is not None:
        conditions.append("s.visit_id = ?")
        params.append(visit_id)
    if case_id is not None:
        conditions.append("v.case_id = ?")
        params.append(case_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY v.visit_date ASC, s.id ASC"

    rows = db.execute(query, params).fetchall()
    return [
        SessionRecord(
            id=r[0],
            visit_id=r[1],
            modality=r[2],
            duration_min=r[3],
            target_structures=r[4],
            parameters=r[5],
            adverse_reactions=r[6],
            practitioner_role=r[7],
            created_utc=r[8],
        )
        for r in rows
    ]


def get_patient_timeline(db: sqlite3.Connection, case_id: str) -> Dict[str, Any]:
    """Compile a complete longitudinal patient profile and visit timeline."""
    case_row = db.execute("SELECT case_id, label FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if not case_row:
        raise ValueError(f"Case '{case_id}' not found")

    intake_row = db.execute(
        "SELECT age_band, symptom_onset, primary_region, functional_limits, prior_care, operator_role, created_utc "
        "FROM intakes WHERE case_id = ?",
        (case_id,),
    ).fetchone()

    visits_rows = db.execute(
        "SELECT id, visit_date, region, pain, rom_deg, flag, note, disposition, created_utc "
        "FROM visits WHERE case_id = ? ORDER BY visit_date ASC, id ASC",
        (case_id,),
    ).fetchall()

    timeline_visits = []
    pain_trend = []
    rom_trend = []

    for v in visits_rows:
        v_id = v[0]
        v_date = v[1]
        pain = v[3]
        rom_deg = v[4]

        pain_trend.append({"date": v_date, "pain": pain, "visit_id": v_id})
        rom_trend.append({"date": v_date, "rom_deg": rom_deg, "visit_id": v_id})

        # Observations
        obs = list_observations(db, visit_id=v_id)
        # Sessions
        sess = list_sessions(db, visit_id=v_id)
        # ROM tests
        rom_rows = db.execute(
            "SELECT id, motion, side, angle_deg, method FROM rom_assessments WHERE visit_id = ?",
            (v_id,),
        ).fetchall()
        # SOAPs
        soap_rows = db.execute(
            "SELECT id, subjective, objective, assessment, plan, author_role, reviewed_by, review_status, review_notes, created_utc "
            "FROM soap_notes WHERE visit_id = ?",
            (v_id,),
        ).fetchall()

        timeline_visits.append({
            "visit_id": v_id,
            "visit_date": v_date,
            "region": v[2],
            "pain": pain,
            "rom_deg": rom_deg,
            "flag": v[5],
            "note": v[6],
            "disposition": v[7],
            "created_utc": v[8],
            "rom_records": [
                {"id": r[0], "motion": r[1], "side": r[2], "angle": r[3], "method": r[4]}
                for r in rom_rows
            ],
            "observations": [
                {
                    "id": o.id,
                    "structure_id": o.structure_id,
                    "structure_type": o.structure_type,
                    "observation_type": o.observation_type,
                    "severity": o.severity,
                    "finding": o.finding,
                    "interpretation": o.interpretation,
                    "created_utc": o.created_utc,
                }
                for o in obs
            ],
            "sessions": [
                {
                    "id": s.id,
                    "modality": s.modality,
                    "duration_min": s.duration_min,
                    "target_structures": s.target_structures,
                    "parameters": s.parameters,
                    "adverse_reactions": s.adverse_reactions,
                    "practitioner_role": s.practitioner_role,
                    "created_utc": s.created_utc,
                }
                for s in sess
            ],
            "soaps": [
                {
                    "id": sp[0],
                    "subjective": sp[1],
                    "objective": sp[2],
                    "assessment": sp[3],
                    "plan": sp[4],
                    "author_role": sp[5],
                    "reviewed_by": sp[6],
                    "review_status": sp[7],
                    "review_notes": sp[8],
                    "created_utc": sp[9],
                }
                for sp in soap_rows
            ],
        })

    return {
        "case_id": case_row[0],
        "label": case_row[1],
        "intake": {
            "age_band": intake_row[0],
            "symptom_onset": intake_row[1],
            "primary_region": intake_row[2],
            "functional_limits": intake_row[3],
            "prior_care": intake_row[4],
            "operator_role": intake_row[5],
            "created_utc": intake_row[6],
        } if intake_row else None,
        "visits": timeline_visits,
        "trends": {
            "pain": pain_trend,
            "rom": rom_trend,
            "total_visits": len(timeline_visits),
            "pain_delta": (pain_trend[-1]["pain"] - pain_trend[0]["pain"]) if pain_trend else 0,
            "rom_delta": (rom_trend[-1]["rom_deg"] - rom_trend[0]["rom_deg"]) if rom_trend else 0,
        },
    }


def export_case_fhir(db: sqlite3.Connection, case_id: str, require_approved_soap: bool = False) -> Dict[str, Any]:
    """Export synthetic case data as an HL7 FHIR R4 Bundle compliant with Medplum/FHIR specifications."""
    timeline = get_patient_timeline(db, case_id)

    bundle: Dict[str, Any] = {
        "resourceType": "Bundle",
        "id": f"bundle-{case_id.lower()}",
        "type": "collection",
        "meta": {
            "lastUpdated": "2026-10-20T00:00:00Z",
            "tag": [
                {"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationValue", "code": "SYNTHETIC", "display": "Synthetic Educational Case"}
            ]
        },
        "entry": []
    }

    # 1. Patient Resource (strictly synthetic)
    patient_res = {
        "fullUrl": f"urn:uuid:patient-{case_id.lower()}",
        "resource": {
            "resourceType": "Patient",
            "id": f"patient-{case_id.lower()}",
            "identifier": [
                {"system": "https://msk-therapy-os.local/patient-id", "value": case_id}
            ],
            "active": True,
            "name": [{"use": "anonymous", "text": timeline["label"]}],
        }
    }
    bundle["entry"].append(patient_res)

    # 2. Encounters and Observations per Visit
    for v in timeline["visits"]:
        soap_statuses = [sp.get("review_status") for sp in v.get("soaps", [])]
        if "REJECTED" in soap_statuses:
            enc_status = "entered-in-error"
        elif require_approved_soap and not any(st in ("APPROVED", "SUPERVISED") for st in soap_statuses):
            enc_status = "cancelled"
        else:
            enc_status = "finished"

        enc_id = f"encounter-v{v['visit_id']}"
        enc_res = {
            "fullUrl": f"urn:uuid:{enc_id}",
            "resource": {
                "resourceType": "Encounter",
                "id": enc_id,
                "status": enc_status,
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "AMB",
                    "display": "ambulatory"
                },
                "subject": {"reference": f"Patient/patient-{case_id.lower()}"},
                "period": {"start": f"{v['visit_date']}T09:00:00Z"},
            }
        }
        bundle["entry"].append(enc_res)

        # Pain Observation
        pain_obs = {
            "fullUrl": f"urn:uuid:obs-pain-v{v['visit_id']}",
            "resource": {
                "resourceType": "Observation",
                "id": f"obs-pain-v{v['visit_id']}",
                "status": "final",
                "category": [
                    {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}
                ],
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": "72514-3", "display": "Pain severity - 0-10 verbal numeric rating score"}]
                },
                "subject": {"reference": f"Patient/patient-{case_id.lower()}"},
                "encounter": {"reference": f"Encounter/{enc_id}"},
                "effectiveDateTime": v["visit_date"],
                "valueInteger": v["pain"],
            }
        }
        bundle["entry"].append(pain_obs)

        # ROM Observation
        rom_obs = {
            "fullUrl": f"urn:uuid:obs-rom-v{v['visit_id']}",
            "resource": {
                "resourceType": "Observation",
                "id": f"obs-rom-v{v['visit_id']}",
                "status": "final",
                "category": [
                    {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "exam"}]}
                ],
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": "80255-3", "display": "Range of motion test"}]
                },
                "subject": {"reference": f"Patient/patient-{case_id.lower()}"},
                "encounter": {"reference": f"Encounter/{enc_id}"},
                "effectiveDateTime": v["visit_date"],
                "valueQuantity": {"value": v["rom_deg"], "unit": "degrees", "system": "http://unitsofmeasure.org", "code": "deg"},
            }
        }
        bundle["entry"].append(rom_obs)

        # Anatomical / Acupoint Observations
        for o in v["observations"]:
            struct_obs = {
                "fullUrl": f"urn:uuid:obs-struct-{o['id']}",
                "resource": {
                    "resourceType": "Observation",
                    "id": f"obs-struct-{o['id']}",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "https://msk-therapy-os.local/structure-id", "code": o["structure_id"]}],
                        "text": f"{o['structure_type']}: {o['structure_id']} ({o['observation_type']})"
                    },
                    "subject": {"reference": f"Patient/patient-{case_id.lower()}"},
                    "encounter": {"reference": f"Encounter/{enc_id}"},
                    "note": [{"text": f"Finding: {o['finding']} | Interpretation: {o['interpretation']}"}],
                    "valueInteger": o["severity"],
                }
            }
            bundle["entry"].append(struct_obs)

    return bundle
