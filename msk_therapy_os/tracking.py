"""Longitudinal tracking, structured anatomical observations, therapy sessions, and FHIR R4 export."""
from __future__ import annotations

import base64

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

        # SOAP Clinical Documentation (DocumentReference) & Supervisor Sign-off (Provenance)
        for sp in v.get("soaps", []):
            doc_id = f"docref-soap-{sp['id']}"
            doc_content = (
                f"SOAP Note #{sp['id']} (Visit #{v['visit_id']})\n"
                f"Subjective: {sp.get('subjective', '')}\n"
                f"Objective: {sp.get('objective', '')}\n"
                f"Assessment: {sp.get('assessment', '')}\n"
                f"Plan: {sp.get('plan', '')}\n"
                f"Author Role: {sp.get('author_role', 'student')}\n"
                f"Review Status: {sp.get('review_status', 'DRAFT')}\n"
                f"Reviewed By: {sp.get('reviewed_by', 'None')}\n"
                f"Feedback: {sp.get('review_notes', '')}"
            )
            is_approved = sp.get("review_status") in ("APPROVED", "SUPERVISED")
            doc_res = {
                "fullUrl": f"urn:uuid:{doc_id}",
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": doc_id,
                    "status": "current" if is_approved else "preliminary",
                    "docStatus": "final" if is_approved else "preliminary",
                    "type": {
                        "coding": [
                            {"system": "http://loinc.org", "code": "11488-4", "display": "Consultation note"}
                        ],
                        "text": "SOAP Clinical Documentation"
                    },
                    "subject": {"reference": f"Patient/patient-{case_id.lower()}"},
                    "context": {
                        "encounter": [{"reference": f"Encounter/{enc_id}"}],
                    },
                    "date": f"{v['visit_date']}T12:00:00Z",
                    "author": [{"display": f"Role: {sp.get('author_role', 'student')}"}],
                    "description": f"SOAP Note - Visit {v['visit_id']}",
                    "content": [
                        {
                            "attachment": {
                                "contentType": "text/plain",
                                "data": base64.b64encode(doc_content.encode("utf-8")).decode("ascii"),
                                "title": f"SOAP Note #{sp['id']}"
                            }
                        }
                    ]
                }
            }
            bundle["entry"].append(doc_res)

            if sp.get("reviewed_by") and is_approved:
                prov_id = f"provenance-soap-{sp['id']}"
                prov_res = {
                    "fullUrl": f"urn:uuid:{prov_id}",
                    "resource": {
                        "resourceType": "Provenance",
                        "id": prov_id,
                        "target": [{"reference": f"DocumentReference/{doc_id}"}],
                        "recorded": f"{v['visit_date']}T12:30:00Z",
                        "activity": {
                            "coding": [
                                {"system": "http://terminology.hl7.org/CodeSystem/v3-DocumentCompletion", "code": "AU", "display": "authenticated"}
                            ],
                            "text": "Clinical Supervisor Approval Sign-Off (Workflow Electronic Sign-off; not a PKI cryptographic signature)"
                        },
                        "agent": [
                            {
                                "type": {
                                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type", "code": "verifier", "display": "Verifier"}]
                                },
                                "who": {"display": sp.get("reviewed_by")}
                            }
                        ],
                        "signature": [
                            {
                                "type": [
                                    {"system": "urn:iso-astm:E1762-95:2013", "code": "1.2.840.10065.1.12.1.5", "display": "Verification Signature"}
                                ],
                                "when": f"{v['visit_date']}T12:30:00Z",
                                "who": {"display": sp.get("reviewed_by")},
                                "data": base64.b64encode(f"Clinical Supervisor Sign-off: {sp.get('reviewed_by')} - {sp.get('review_status')}".encode("utf-8")).decode("ascii")
                            }
                        ]
                    }
                }
                bundle["entry"].append(prov_res)

    # 4. Patient PROMs (Survey Observations)
    try:
        prom_rows = db.execute(
            """SELECT prom_id, visit_id, prom_type, raw_score, percentage_score, interpretation, administered_at
               FROM patient_proms WHERE case_id = ? ORDER BY administered_at ASC""",
            (case_id,),
        ).fetchall()
        for pr in prom_rows:
            prom_obs = {
                "fullUrl": f"urn:uuid:{pr[0].lower()}",
                "resource": {
                    "resourceType": "Observation",
                    "id": pr[0].lower(),
                    "status": "final",
                    "category": [
                        {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "survey"}]}
                    ],
                    "code": {
                        "coding": [{"system": "https://msk-therapy-os.local/prom", "code": pr[2], "display": f"{pr[2]} Survey Score"}]
                    },
                    "subject": {"reference": f"Patient/patient-{case_id.lower()}"},
                    "effectiveDateTime": pr[6],
                    "valueQuantity": {"value": pr[4], "unit": "%", "system": "http://unitsofmeasure.org", "code": "%"},
                    "interpretation": [{"text": pr[5]}],
                }
            }
            if pr[1]:
                prom_obs["resource"]["encounter"] = {"reference": f"Encounter/encounter-v{pr[1]}"}
            bundle["entry"].append(prom_obs)
    except sqlite3.OperationalError:
        pass

    # 5. Adverse Events (CTCAE Graded)
    try:
        ae_rows = db.execute(
            """SELECT event_id, visit_id, event_category, ctcae_grade, symptom_description, onset_utc, resolution_status, action_taken
               FROM adverse_events WHERE case_id = ? ORDER BY onset_utc ASC""",
            (case_id,),
        ).fetchall()
        for ae in ae_rows:
            ae_res = {
                "fullUrl": f"urn:uuid:{ae[0].lower()}",
                "resource": {
                    "resourceType": "AdverseEvent",
                    "id": ae[0].lower(),
                    "actuality": "actual",
                    "category": [
                        {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/adverse-event-category", "code": "incident"}]}
                    ],
                    "event": {
                        "text": f"[{ae[2]}] {ae[4]}"
                    },
                    "subject": {"reference": f"Patient/patient-{case_id.lower()}"},
                    "date": ae[5],
                    "severity": {
                        "coding": [{"system": "http://evs.nci.nih.gov/ftp1/CTCAE/CTCAE_5.0", "code": f"Grade-{ae[3]}", "display": f"CTCAE Grade {ae[3]}"}]
                    },
                    "outcome": {
                        "text": f"Status: {ae[6]} | Action: {ae[7]}"
                    }
                }
            }
            if ae[1]:
                ae_res["resource"]["encounter"] = {"reference": f"Encounter/encounter-v{ae[1]}"}
            bundle["entry"].append(ae_res)
    except sqlite3.OperationalError:
        pass

    return bundle


def validate_fhir_r4_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Validate an HL7 FHIR R4 Bundle for structural compliance, reference integrity, and required elements."""
    errors: List[str] = []
    warnings: List[str] = []
    resource_counts: Dict[str, int] = {}

    if not isinstance(bundle, dict):
        return {"is_valid": False, "errors": ["Bundle must be a JSON object"], "warnings": [], "resource_counts": {}}

    if bundle.get("resourceType") != "Bundle":
        errors.append(f"Expected resourceType 'Bundle', got '{bundle.get('resourceType')}'")

    if not bundle.get("id"):
        errors.append("Bundle missing required 'id'")

    entries = bundle.get("entry", [])
    if not isinstance(entries, list):
        errors.append("Bundle 'entry' must be an array")
        return {"is_valid": False, "errors": errors, "warnings": warnings, "resource_counts": resource_counts}

    # Collect all resource identifiers
    known_resources = set()
    for i, entry in enumerate(entries):
        res = entry.get("resource")
        if not res or not isinstance(res, dict):
            errors.append(f"Entry #{i} missing valid 'resource' object")
            continue
        rtype = res.get("resourceType")
        rid = res.get("id")
        if not rtype or not rid:
            errors.append(f"Entry #{i} missing 'resourceType' or 'id'")
            continue
        full_ref = f"{rtype}/{rid}"
        known_resources.add(full_ref)
        resource_counts[rtype] = resource_counts.get(rtype, 0) + 1

    # Check reference integrity across all entries
    def inspect_references(node: Any, path: str = "") -> None:
        if isinstance(node, dict):
            if "reference" in node and isinstance(node["reference"], str):
                ref_val = node["reference"]
                # Skip pure UUID urns or external URLs
                if not ref_val.startswith(("urn:uuid:", "http://", "https://")):
                    if "/" in ref_val:
                        target_type = ref_val.split("/")[0]
                        if target_type in ("Patient", "Encounter", "Observation", "DocumentReference", "Provenance", "AdverseEvent"):
                            if ref_val not in known_resources:
                                errors.append(f"Broken internal reference '{ref_val}' at {path}")
            for k, v in node.items():
                inspect_references(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                inspect_references(item, f"{path}[{idx}]")

    for entry in entries:
        if "resource" in entry:
            inspect_references(entry["resource"], entry["resource"].get("resourceType", "Resource"))

    # Required field verification per FHIR R4 resource profile
    for entry in entries:
        res = entry.get("resource", {})
        rtype = res.get("resourceType")
        rid = res.get("id", "unknown")

        if rtype == "Patient":
            if not res.get("identifier"):
                warnings.append(f"Patient/{rid} lacks 'identifier'")
        elif rtype == "Encounter":
            if not res.get("status"):
                errors.append(f"Encounter/{rid} missing required 'status'")
            if not res.get("class"):
                errors.append(f"Encounter/{rid} missing required 'class'")
            if not res.get("subject"):
                errors.append(f"Encounter/{rid} missing required 'subject'")
        elif rtype == "Observation":
            if not res.get("status"):
                errors.append(f"Observation/{rid} missing required 'status'")
            if not res.get("code"):
                errors.append(f"Observation/{rid} missing required 'code'")
            if not res.get("subject"):
                errors.append(f"Observation/{rid} missing required 'subject'")
        elif rtype == "DocumentReference":
            if not res.get("status"):
                errors.append(f"DocumentReference/{rid} missing required 'status'")
            if not res.get("type"):
                errors.append(f"DocumentReference/{rid} missing required 'type'")
            if not res.get("content"):
                errors.append(f"DocumentReference/{rid} missing required 'content'")
        elif rtype == "Provenance":
            if not res.get("target"):
                errors.append(f"Provenance/{rid} missing required 'target'")
            if not res.get("agent"):
                errors.append(f"Provenance/{rid} missing required 'agent'")
        elif rtype == "AdverseEvent":
            if not res.get("actuality"):
                errors.append(f"AdverseEvent/{rid} missing required 'actuality'")
            if not res.get("event"):
                errors.append(f"AdverseEvent/{rid} missing required 'event'")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "entry_count": len(entries),
        "resource_counts": resource_counts,
    }
