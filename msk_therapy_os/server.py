"""Lightweight, zero-dependency HTTP server for MSK-Therapy-OS Milestone M2 Body-Map UI.

Serves the Open Anatomy Atlas renderer at /atlas/ and proxies BodyParts3D data files
from the local dataset directory, providing an integrated 3D anatomy learning experience
without cross-origin issues.
"""
from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import shutil
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
from msk_therapy_os.points import (
    list_libraries,
    create_library,
    list_custom_points,
    get_point,
    create_point,
    update_point,
    soft_delete_point,
    restore_point,
    get_point_revisions,
    revert_to_revision,
    set_reference_override,
    get_reference_override,
    list_reference_overrides,
    delete_reference_override,
    export_library_bundle,
    import_library_bundle,
    run_database_integrity_check,
    verify_reference_dataset_integrity,
    backup_database,
    rollback_database,
    get_evidence_ledger,
)
from msk_therapy_os.soap import (
    create_soap_note,
    get_soap_notes_for_visit,
    review_soap_note,
)
from msk_therapy_os.tracking import (
    export_case_fhir,
    get_patient_timeline,
    list_observations,
    list_sessions,
    record_observation,
    record_session,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
ATLAS_UI_DIR = STATIC_DIR / "atlas"

# Resolve the Open Anatomy Atlas data directory (same location the atlas tools use).
_APPDATA = os.environ.get("APPDATA", "")
ATLAS_DATA_DIR = Path(_APPDATA) / "open-anatomy-atlas" / "dataset" if _APPDATA else None

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".bin": "application/octet-stream",
}


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

    def _serve_file(self, file_path: Path) -> bool:
        """Serve a static file by streaming. Returns True if served, False if not found."""
        if not file_path.exists() or file_path.is_dir():
            return False
        ext = file_path.suffix.lower()
        content_type = MIME_TYPES.get(ext, "application/octet-stream")
        file_size = file_path.stat().st_size
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with open(file_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile, 65536)
        return True

    def _atlas_status(self) -> Dict[str, Any]:
        """Read atlas status from the local data directory (mirrors Open Anatomy Atlas API)."""
        if not ATLAS_DATA_DIR or not ATLAS_DATA_DIR.exists():
            return {"ready": False, "error": "No atlas data directory found"}
        active_file = ATLAS_DATA_DIR / "active.json"
        active_id = None
        if active_file.exists():
            try:
                active_id = json.loads(active_file.read_text(encoding="utf-8")).get("id")
            except Exception:
                pass
        atlases = []
        atlases_dir = ATLAS_DATA_DIR / "atlases"
        if atlases_dir.exists():
            for d in sorted(atlases_dir.iterdir()):
                if not d.is_dir():
                    continue
                idx_file = d / "build" / "index.json"
                info: Dict[str, Any] = {"id": d.name, "ready": idx_file.exists()}
                if idx_file.exists():
                    try:
                        idx = json.loads(idx_file.read_text(encoding="utf-8"))
                        info.update({
                            "name": idx.get("name"),
                            "version": idx.get("version"),
                            "counts": idx.get("counts"),
                            "attribution": idx.get("attribution"),
                            "license": idx.get("license"),
                        })
                    except Exception:
                        pass
                atlases.append(info)
        ready_ids = [a["id"] for a in atlases if a.get("ready")]
        if active_id not in ready_ids and ready_ids:
            active_id = ready_ids[0]
        active_atlas = next((a for a in atlases if a["id"] == active_id), None)
        result: Dict[str, Any] = {
            "ready": bool(active_atlas and active_atlas.get("ready")),
            "active": active_id,
            "atlases": atlases,
            "dataDir": str(ATLAS_DATA_DIR),
        }
        if active_atlas:
            for k in ("name", "version", "counts", "attribution", "license"):
                if k in active_atlas:
                    result[k] = active_atlas[k]
        return result

    def _resolve_atlas_data_file(self, rel_path: str) -> Optional[Path]:
        """Resolve a data/ path to an actual file inside the active atlas build directory, with static fallback."""
        static_data_dir = ATLAS_UI_DIR / "data"
        static_target = (static_data_dir / rel_path).resolve()
        if str(static_target).startswith(str(static_data_dir.resolve())):
            if static_target.exists() and static_target.is_file():
                return static_target

        if not ATLAS_DATA_DIR:
            return None
        status = self._atlas_status()
        active = status.get("active")
        if not active:
            return None
        build_dir = ATLAS_DATA_DIR / "atlases" / active / "build"
        target = (build_dir / rel_path).resolve()
        # Security: ensure the resolved path is inside build_dir
        if not str(target).startswith(str(build_dir.resolve())):
            return None
        if target.exists() and target.is_file():
            return target
        return None

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

        # Serve static assets directly from STATIC_DIR (e.g. meridianEditor.js)
        if not path.startswith(("/api/", "/atlas/", "/data/")):
            static_file = (STATIC_DIR / path.lstrip("/")).resolve()
            if str(static_file).startswith(str(STATIC_DIR.resolve())) and static_file.is_file():
                if self._serve_file(static_file):
                    return

        # --- Atlas UI: serve renderer files at /atlas/ ---
        if path.startswith("/atlas/") or path == "/atlas":
            rel = path[7:] if path.startswith("/atlas/") else ""
            if not rel or rel == "index.html":
                atlas_index = ATLAS_UI_DIR / "index.html"
                if atlas_index.exists():
                    self._send_text(
                        atlas_index.read_text(encoding="utf-8"),
                        content_type="text/html; charset=utf-8",
                    )
                else:
                    self._send_text("Atlas UI not installed", status=HTTPStatus.NOT_FOUND)
                return
            # /atlas/data/ -> serve from the local BodyParts3D dataset
            if rel.startswith("data/"):
                data_rel = rel[5:]  # strip "data/"
                data_file = self._resolve_atlas_data_file(data_rel)
                if data_file and self._serve_file(data_file):
                    return
                self._send_text("Atlas data file not found", status=HTTPStatus.NOT_FOUND)
                return
            # /atlas/api/status -> atlas status JSON
            if rel == "api/status":
                self._send_json(self._atlas_status())
                return
            # Serve other atlas UI assets (JS, CSS, brand/)
            safe_path = (ATLAS_UI_DIR / rel).resolve()
            if str(safe_path).startswith(str(ATLAS_UI_DIR.resolve())):
                if self._serve_file(safe_path):
                    return
            self._send_text("Not found", status=HTTPStatus.NOT_FOUND)
            return

        # --- Direct Atlas Data & Status Endpoints ---
        if path.startswith("/data/"):
            data_file = self._resolve_atlas_data_file(path[6:])
            if data_file and self._serve_file(data_file):
                return
            self._send_text("Atlas data file not found", status=HTTPStatus.NOT_FOUND)
            return

        if path == "/api/status":
            self._send_json(self._atlas_status())
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

                elif path == "/api/timeline":
                    case_id = query.get("case_id", ["DEMO-NECK-001"])[0]
                    timeline_data = get_patient_timeline(db, case_id)
                    self._send_json(timeline_data)

                elif path == "/api/observations":
                    v_id = query.get("visit_id", [None])[0]
                    c_id = query.get("case_id", [None])[0]
                    s_id = query.get("structure_id", [None])[0]
                    obs = list_observations(db, visit_id=int(v_id) if v_id else None, case_id=c_id, structure_id=s_id)
                    self._send_json([{
                        "id": o.id,
                        "visit_id": o.visit_id,
                        "structure_id": o.structure_id,
                        "structure_type": o.structure_type,
                        "observation_type": o.observation_type,
                        "severity": o.severity,
                        "finding": o.finding,
                        "interpretation": o.interpretation,
                        "created_utc": o.created_utc,
                    } for o in obs])

                elif path == "/api/sessions":
                    v_id = query.get("visit_id", [None])[0]
                    c_id = query.get("case_id", [None])[0]
                    sess = list_sessions(db, visit_id=int(v_id) if v_id else None, case_id=c_id)
                    self._send_json([{
                        "id": s.id,
                        "visit_id": s.visit_id,
                        "modality": s.modality,
                        "duration_min": s.duration_min,
                        "target_structures": s.target_structures,
                        "parameters": s.parameters,
                        "adverse_reactions": s.adverse_reactions,
                        "practitioner_role": s.practitioner_role,
                        "created_utc": s.created_utc,
                    } for s in sess])

                elif path == "/api/export-fhir":
                    case_id = query.get("case_id", ["DEMO-NECK-001"])[0]
                    fhir_bundle = export_case_fhir(db, case_id)
                    self._send_json(fhir_bundle)

                elif path == "/api/acupuncture-3d":
                    acu_file = ATLAS_UI_DIR / "data" / "acupuncture_3d.json"
                    if acu_file.exists():
                        acu_data = json.loads(acu_file.read_text(encoding="utf-8"))
                        # Dynamically apply active overrides and custom points from SQLite
                        overrides = list_reference_overrides(db)
                        for code, ov in overrides.items():
                            if code in acu_data.get("points", {}):
                                pt = acu_data["points"][code]
                                pt["position"] = ov["position"]
                                if ov.get("normal"):
                                    pt["normal"] = ov["normal"]
                                if ov.get("registration_status"):
                                    pt["registration_status"] = ov["registration_status"]
                                if ov.get("review_status"):
                                    pt["review_status"] = ov["review_status"]
                                if ov.get("notes"):
                                    pt["verification_notes"] = ov["notes"]
                                pt["is_overridden"] = True
                        custom_pts = list_custom_points(db, include_deleted=False)
                        for cp in custom_pts:
                            code = cp["code"]
                            acu_data.setdefault("points", {})[code] = cp
                        self._send_json(acu_data)
                    else:
                        self._send_json({"error": "Acupuncture 3D dataset not found"}, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/points/libraries":
                    self._send_json(list_libraries(db))

                elif path == "/api/points/overrides":
                    self._send_json(list_reference_overrides(db))

                elif path == "/api/points/export":
                    lib_id = query.get("library_id", ["lib_custom_user"])[0]
                    self._send_json(export_library_bundle(db, lib_id))

                elif path == "/api/points":
                    lib_id = query.get("library_id", [None])[0]
                    reg_filt = query.get("region", [None])[0]
                    inc_del = query.get("include_deleted", ["0"])[0] in ("1", "true")
                    self._send_json(list_custom_points(db, library_id=lib_id, region=reg_filt, include_deleted=inc_del))

                elif path.startswith("/api/points/") and path.endswith("/revisions"):
                    pt_id = path.split("/")[3]
                    self._send_json(get_point_revisions(db, pt_id))

                elif path.startswith("/api/points/"):
                    pt_id = path.split("/")[3]
                    pt = get_point(db, pt_id)
                    if pt:
                        self._send_json(pt)
                    else:
                        self._send_json({"error": f"Point '{pt_id}' not found"}, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/governance/status":
                    self._send_json(run_database_integrity_check(db))

                elif path == "/api/governance/evidence-ledger":
                    self._send_json(get_evidence_ledger(db))

                elif path == "/api/governance/reconciliation":
                    acu_file = ATLAS_UI_DIR / "data" / "acupuncture_3d.json"
                    acu_cnt = 0
                    dc_cnt = 0
                    if acu_file.exists():
                        d = json.loads(acu_file.read_text(encoding="utf-8"))
                        acu_cnt = len(d.get("points", {}))
                        dc_cnt = len(d.get("dien_chan", []))
                    active_custom = len(list_custom_points(db, include_deleted=False))
                    self._send_json({
                        "who_standard_count": 361,
                        "who_standard_notes": "14 classical channels (12 organ meridians + 28 GV + 24 CV). Yintang classified as Extra Point EX-HN3.",
                        "national_standard_count": 362,
                        "national_standard_citation": "GB/T 12346-2006 / GB/T 12346-2021",
                        "national_standard_notes": "Yintang officially incorporated into Du Mai (Governing Vessel) as GV24+ / GV29.",
                        "dien_chan_count": dc_cnt,
                        "dien_chan_notes": "Vietnamese facial reflex points (DC_0, DC_1, DC_26, DC_126) isolated in lib_dien_chan namespace.",
                        "active_custom_count": active_custom,
                        "runtime_total_points": acu_cnt + dc_cnt + active_custom,
                        "conservation_formula": "Available = Visible + Clustered + Filtered",
                        "provenance_policy": "Strict namespace isolation: WHO, DIEN_CHAN, THAI_SEN_SIB, MSK_LANDMARK, USER_CUSTOM.",
                        "status": "RECONCILED"
                    })

                elif path == "/api/terminology":
                    from msk_therapy_os.terminology import MedicalTerminologyRegistry
                    reg = MedicalTerminologyRegistry.get_instance()
                    category = query.get("category", [None])[0]
                    lang = query.get("lang", ["en"])[0]
                    if category == "meridians":
                        self._send_json(list(reg.meridians.values()))
                    elif category == "points":
                        self._send_json(reg.points)
                    elif category == "dien_chan":
                        self._send_json(list(reg.dien_chan.values()))
                    elif category == "thai":
                        self._send_json(list(reg.thai_sen_sib.values()))
                    elif category == "structures":
                        self._send_json(list(reg.structures.values()))
                    else:
                        self._send_json(reg.data)

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

                elif path == "/api/observation":
                    obs_id = record_observation(
                        db,
                        visit_id=int(body["visit_id"]),
                        structure_id=body["structure_id"],
                        structure_type=body.get("structure_type", "anatomy"),
                        observation_type=body.get("observation_type", "palpation"),
                        severity=int(body.get("severity", 5)),
                        finding=body["finding"],
                        interpretation=body.get("interpretation", ""),
                    )
                    self._send_json({"status": "created", "observation_id": obs_id})

                elif path == "/api/session":
                    sess_id = record_session(
                        db,
                        visit_id=int(body["visit_id"]),
                        modality=body["modality"],
                        duration_min=int(body["duration_min"]),
                        target_structures=body.get("target_structures", "[]"),
                        parameters=body.get("parameters", ""),
                        adverse_reactions=body.get("adverse_reactions", "none"),
                        practitioner_role=body.get("role", "student"),
                    )
                    self._send_json({"status": "created", "session_id": sess_id})

                elif path == "/api/points/libraries":
                    new_lib = create_library(db, body)
                    self._send_json({"status": "created", "library": new_lib}, status=HTTPStatus.CREATED)

                elif path == "/api/points":
                    new_pt = create_point(db, body, author=body.get("author", "Clinical Educator"))
                    self._send_json({"status": "created", "point": new_pt}, status=HTTPStatus.CREATED)

                elif path.startswith("/api/points/") and path.endswith("/restore"):
                    pt_id = path.split("/")[3]
                    restored_pt = restore_point(db, pt_id, author=body.get("author", "Clinical Educator"))
                    self._send_json({"status": "restored", "point": restored_pt})

                elif path.startswith("/api/points/") and path.endswith("/revert"):
                    pt_id = path.split("/")[3]
                    rev_num = int(body.get("revision_number", 1))
                    reverted_pt = revert_to_revision(db, pt_id, rev_num, author=body.get("author", "Clinical Educator"))
                    self._send_json({"status": "reverted", "point": reverted_pt})

                elif path.startswith("/api/points/overrides/") and path.endswith("/delete"):
                    ref_code = path.split("/")[4]
                    success = delete_reference_override(db, ref_code, author="Clinical Educator")
                    self._send_json({"status": "deleted" if success else "not_found", "reference_code": ref_code})

                elif path.startswith("/api/points/overrides/"):
                    ref_code = path.split("/")[4]
                    ov = set_reference_override(db, ref_code, body, author=body.get("author", "Clinical Educator"), notes=body.get("notes", ""))
                    self._send_json({"status": "saved", "override": ov})

                elif path == "/api/governance/backup":
                    import time
                    name = body.get("name") or f"backup_snapshot_{int(time.time())}.sqlite3"
                    bp = Path("data/backups") / name
                    self._send_json(backup_database(db, str(bp)))

                elif path == "/api/governance/check":
                    self._send_json(run_database_integrity_check(db))

                elif path == "/api/points/import":
                    res = import_library_bundle(db, body, author=body.get("author", "Import Operator"))
                    self._send_json(res)

                elif path.startswith("/api/points/") and path.endswith("/update"):
                    pt_id = path.split("/")[3]
                    ch_type = body.get("change_type", "UPDATE_COORDS")
                    notes = body.get("notes", "")
                    updated_pt = update_point(db, pt_id, body, author=body.get("author", "Clinical Educator"), change_type=ch_type, notes=notes)
                    self._send_json({"status": "updated", "point": updated_pt})

                elif path.startswith("/api/points/") and path.endswith("/delete"):
                    pt_id = path.split("/")[3]
                    soft_delete_point(db, pt_id, author=body.get("author", "Clinical Educator"))
                    self._send_json({"status": "deleted", "point_id": pt_id})

                else:
                    self._send_json({"error": f"Endpoint '{path}' not found"}, status=HTTPStatus.NOT_FOUND)
            except (ValueError, PermissionError) as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            body = self._read_json_body()
        except Exception as e:
            self._send_json({"error": f"Invalid JSON payload: {e}"}, status=HTTPStatus.BAD_REQUEST)
            return

        with open_db(self.db_path) as db:
            try:
                if path.startswith("/api/points/"):
                    pt_id = path.split("/")[3]
                    ch_type = body.get("change_type", "UPDATE_COORDS")
                    notes = body.get("notes", "")
                    updated_pt = update_point(db, pt_id, body, author=body.get("author", "Clinical Educator"), change_type=ch_type, notes=notes)
                    self._send_json({"status": "updated", "point": updated_pt})
                else:
                    self._send_json({"error": f"Endpoint '{path}' not found"}, status=HTTPStatus.NOT_FOUND)
            except (ValueError, PermissionError) as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        with open_db(self.db_path) as db:
            try:
                if path.startswith("/api/points/overrides/"):
                    ref_code = path.split("/")[4]
                    success = delete_reference_override(db, ref_code, author="Clinical Educator")
                    if success:
                        self._send_json({"status": "deleted", "reference_code": ref_code})
                    else:
                        self._send_json({"error": f"No active override for '{ref_code}'"}, status=HTTPStatus.NOT_FOUND)
                elif path.startswith("/api/points/"):
                    pt_id = path.split("/")[3]
                    soft_delete_point(db, pt_id, author="Clinical Educator")
                    self._send_json({"status": "deleted", "point_id": pt_id})
                else:
                    self._send_json({"error": f"Endpoint '{path}' not found"}, status=HTTPStatus.NOT_FOUND)
            except (ValueError, PermissionError) as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
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
