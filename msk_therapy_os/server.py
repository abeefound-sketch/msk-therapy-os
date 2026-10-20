"""Lightweight, zero-dependency HTTP server for MSK-Therapy-OS Milestone M2 Body-Map UI."""
from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from msk_therapy_os.__main__ import add_visit
from msk_therapy_os.anatomy import list_anatomy
from msk_therapy_os.assessment import (
    get_intake,
    get_visit_rom,
    list_questionnaires,
    record_rom,
)
from msk_therapy_os.db import open_db
from msk_therapy_os.evidence import get_evidence_by_id, list_evidence
from msk_therapy_os.reporting import generate_case_report
from msk_therapy_os.safety import evaluate_safety
from msk_therapy_os.soap import (
    create_soap_note,
    get_soap_notes_for_visit,
    review_soap_note,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class MSKRequestHandler(BaseHTTPRequestHandler):
    db_path: str = "demo.sqlite3"

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default HTTP request logging to keep console clean unless debugging."""
        pass

    def _send_json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, text: str, content_type: str = "text/plain; charset=utf-8", status: int = HTTPStatus.OK) -> None:
        payload = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _read_json_body(self) -> Dict[str, Any]:
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        raw = self.rfile.read(content_len)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            index_file = STATIC_DIR / "index.html"
            if index_file.exists():
                self._send_text(index_file.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")
            else:
                self._send_text("static/index.html not found", status=HTTPStatus.NOT_FOUND)
            return

        with open_db(self.db_path) as db:
            try:
                if path == "/api/cases":
                    rows = db.execute("SELECT case_id, label FROM cases ORDER BY case_id").fetchall()
                    self._send_json([{"case_id": r[0], "label": r[1]} for r in rows])

                elif path == "/api/case":
                    case_id = query.get("case_id", [""])[0]
                    if not case_id:
                        self._send_json({"error": "Missing case_id parameter"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    case_row = db.execute("SELECT case_id, label FROM cases WHERE case_id = ?", (case_id,)).fetchone()
                    if not case_row:
                        self._send_json({"error": f"Case '{case_id}' not found"}, status=HTTPStatus.NOT_FOUND)
                        return
                    intake = get_intake(db, case_id)
                    visits_rows = db.execute(
                        """SELECT id, visit_date, region, pain, rom_deg, flag, note, disposition, created_utc
                           FROM visits WHERE case_id = ? ORDER BY visit_date, id""",
                        (case_id,),
                    ).fetchall()
                    visits = []
                    all_soaps = []
                    for v in visits_rows:
                        v_id = v[0]
                        roms = get_visit_rom(db, v_id)
                        soaps = get_soap_notes_for_visit(db, v_id)
                        all_soaps.extend([{
                            "id": s.id,
                            "visit_id": s.visit_id,
                            "subjective": s.subjective,
                            "objective": s.objective,
                            "assessment": s.assessment,
                            "plan": s.plan,
                            "author_role": s.author_role,
                            "reviewed_by": s.reviewed_by,
                            "review_status": s.review_status,
                            "review_notes": s.review_notes,
                            "created_utc": s.created_utc,
                        } for s in soaps])
                        visits.append({
                            "id": v[0],
                            "visit_date": v[1],
                            "region": v[2],
                            "pain": v[3],
                            "rom_deg": v[4],
                            "flag": v[5],
                            "note": v[6],
                            "disposition": v[7],
                            "created_utc": v[8],
                            "rom_records": [{"id": r.id, "motion": r.motion, "side": r.side, "angle": r.angle_deg, "method": r.method} for r in roms],
                        })

                    self._send_json({
                        "case_id": case_row[0],
                        "label": case_row[1],
                        "intake": {
                            "age_band": intake.age_band,
                            "symptom_onset": intake.symptom_onset,
                            "primary_region": intake.primary_region,
                            "functional_limits": intake.functional_limits,
                            "prior_care": intake.prior_care,
                            "operator_role": intake.operator_role,
                            "created_utc": intake.created_utc,
                        } if intake else None,
                        "visits": visits,
                        "soaps": all_soaps,
                    })

                elif path == "/api/anatomy":
                    region = query.get("region", [None])[0]
                    namespace = query.get("namespace", [None])[0]
                    structs = list_anatomy(db, region=region, namespace=namespace)
                    self._send_json([{
                        "structure_id": s.structure_id,
                        "name": s.name,
                        "region": s.region,
                        "source_dataset": s.source_dataset,
                        "bodyparts3d_id": s.bodyparts3d_id,
                        "atlas_url": s.atlas_url,
                        "namespace": s.namespace,
                        "evidence_id": s.evidence_id,
                    } for s in structs])

                elif path == "/api/evidence":
                    tier_str = query.get("tier", [None])[0]
                    ev_id = query.get("id", [None])[0]
                    if ev_id:
                        item = get_evidence_by_id(db, ev_id)
                        if not item:
                            self._send_json({"error": "Evidence not found"}, status=HTTPStatus.NOT_FOUND)
                        else:
                            self._send_json({
                                "evidence_id": item.evidence_id,
                                "title": item.title,
                                "url": item.url,
                                "organization": item.organization,
                                "year": item.year,
                                "license": item.license,
                                "tier": item.tier,
                                "claim_scope": item.claim_scope,
                                "reviewed_on": item.reviewed_on,
                                "reviewer": item.reviewer,
                            })
                    else:
                        tier = int(tier_str) if tier_str and tier_str.isdigit() else None
                        items = list_evidence(db, tier=tier)
                        self._send_json([{
                            "evidence_id": e.evidence_id,
                            "title": e.title,
                            "url": e.url,
                            "organization": e.organization,
                            "year": e.year,
                            "license": e.license,
                            "tier": e.tier,
                            "claim_scope": e.claim_scope,
                            "reviewed_on": e.reviewed_on,
                            "reviewer": e.reviewer,
                        } for e in items])

                elif path == "/api/questionnaires":
                    region = query.get("region", [None])[0]
                    qs = list_questionnaires(db, region=region)
                    self._send_json([{
                        "item_id": q.item_id,
                        "region": q.region,
                        "scenario_title": q.scenario_title,
                        "question_text": q.question_text,
                        "safety_critical": q.safety_critical,
                        "evidence_id": q.evidence_id,
                    } for q in qs])

                elif path == "/api/report":
                    case_id = query.get("case_id", [""])[0]
                    if not case_id:
                        self._send_text("Missing case_id", status=HTTPStatus.BAD_REQUEST)
                        return
                    report_md = generate_case_report(db, case_id)
                    self._send_text(report_md, content_type="text/markdown; charset=utf-8")

                else:
                    self._send_json({"error": f"Endpoint '{path}' not found"}, status=HTTPStatus.NOT_FOUND)
            except Exception as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            body = self._read_json_body()
        except Exception as e:
            self._send_json({"error": f"Invalid JSON payload: {e}"}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/screen-safety":
            try:
                flag = body.get("flag", "none")
                modality = body.get("modality", None)
                if modality == "none":
                    modality = None
                contras = body.get("contraindications", None)
                res = evaluate_safety(flag=flag, modality=modality, contraindications=contras)
                self._send_json({
                    "disposition": res.disposition.value,
                    "is_safe_to_proceed": res.is_safe_to_proceed,
                    "flags_triggered": res.flags_triggered,
                    "contraindications_triggered": res.contraindications_triggered,
                    "escalation_instructions": res.escalation_instructions,
                    "clinical_rationale": res.clinical_rationale,
                    "evidence_id": res.evidence_id,
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            return

        with open_db(self.db_path) as db:
            try:
                if path == "/api/visit":
                    disposition = add_visit(
                        db,
                        case=body["case"],
                        when=body["when"],
                        pain=int(body["pain"]),
                        rom=float(body["rom"]),
                        region=body["region"],
                        flag=body["flag"],
                        note=body.get("note", ""),
                    )
                    self._send_json({"status": "created", "disposition": disposition})

                elif path == "/api/rom":
                    rom_id = record_rom(
                        db,
                        visit_id=int(body["visit_id"]),
                        motion=body["motion"],
                        side=body["side"],
                        angle_deg=float(body["angle"]),
                        method=body["method"],
                    )
                    self._send_json({"status": "created", "rom_id": rom_id})

                elif path == "/api/soap":
                    soap_id = create_soap_note(
                        db,
                        visit_id=int(body["visit_id"]),
                        subjective=body["subjective"],
                        objective=body["objective"],
                        assessment=body["assessment"],
                        plan=body["plan"],
                        author_role=body.get("role", "student"),
                    )
                    self._send_json({"status": "created", "soap_id": soap_id})

                elif path == "/api/review-soap":
                    review_soap_note(
                        db,
                        soap_id=int(body["soap_id"]),
                        reviewer_name=body.get("reviewer", "Clinical Supervisor"),
                        reviewer_role=body.get("role", "reviewer"),
                        decision=body["decision"],
                        feedback=body.get("feedback", ""),
                    )
                    self._send_json({"status": "reviewed", "decision": body["decision"]})

                else:
                    self._send_json({"error": f"Endpoint '{path}' not found"}, status=HTTPStatus.NOT_FOUND)
            except (ValueError, PermissionError) as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def create_server(db_path: str, host: str = "127.0.0.1", port: int = 8080) -> HTTPServer:
    """Create configured HTTPServer instance."""
    class ConfiguredHandler(MSKRequestHandler):
        pass

    ConfiguredHandler.db_path = db_path
    return HTTPServer((host, port), ConfiguredHandler)


def run_server(db_path: str, host: str = "127.0.0.1", port: int = 8080) -> None:
    """Run server until keyboard interrupt."""
    server = create_server(db_path, host, port)
    print("========================================================================")
    print("MSK-THERAPY-OS: Milestone M2 Body-Map Learning Server Running")
    print(f"URL: http://{host}:{port}/")
    print(f"Database: {db_path}")
    print("DEMO ONLY: Do not enter or store real patient information.")
    print("Press Ctrl+C to stop.")
    print("========================================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()
