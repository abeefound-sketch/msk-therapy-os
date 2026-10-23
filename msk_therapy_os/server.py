"""Lightweight, zero-dependency HTTP server for MSK-Therapy-OS Milestone M2 Body-Map UI.

Serves the Open Anatomy Atlas renderer at /atlas/ and proxies BodyParts3D data files
from the local dataset directory, providing an integrated 3D anatomy learning experience
without cross-origin issues.
"""
from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.clinical_proms import (
    PROM_CATALOG,
    record_prom_response,
    list_prom_responses,
    record_adverse_event,
    list_adverse_events,
)
from msk_therapy_os.morphology_studio import (
    create_avatar,
    get_avatar,
    list_avatars,
    update_avatar_params,
    record_morphology_observation,
    list_morphology_observations,
)
from msk_therapy_os.pose_anatomy import (
    CURATED_ACTION_MUSCLES,
    create_pose_study,
    get_pose_study,
    list_pose_studies,
    update_landmarks,
    record_pose_observation,
    list_pose_observations,
)
from msk_therapy_os.relationship_catalog import find_entities, get_entity, get_relations
from msk_therapy_os.research_studio import (
    list_research_sets,
    get_research_set,
    create_research_set,
    create_definition,
    list_definitions,
    create_reactive_observation,
    case_research_timeline,
    diagram_visible_to,
    set_visible_to,
)
from msk_therapy_os.evidence import get_evidence_by_id, list_evidence
from msk_therapy_os.reporting import generate_case_report
from msk_therapy_os.auth import (
    authenticate_user,
    create_session,
    get_user_from_session,
    invalidate_session,
    list_clinical_reviewers,
    verify_reviewer,
)
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
    restore_database_safely,
    rollback_database,
    get_evidence_ledger,
    sanitize_backup_filename,
    get_safe_backup_path,
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
_ATLAS_DATA_ENV = os.environ.get("MSK_ATLAS_DATA_DIR", "")
ATLAS_DATA_DIR = Path(_ATLAS_DATA_ENV) if _ATLAS_DATA_ENV else (Path(_APPDATA) / "open-anatomy-atlas" / "dataset" if _APPDATA else None)

MAX_JSON_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5 MB payload limit to prevent DoS
ALLOWED_ORIGIN_HOSTS = {"localhost", "127.0.0.1", "[::1]"}

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

    def _check_maintenance_mode(self) -> bool:
        """Return True and send HTTP 503 if system is in maintenance mode for backup/restore."""
        from msk_therapy_os.points import IS_MAINTENANCE_ACTIVE
        if IS_MAINTENANCE_ACTIVE:
            payload = json.dumps({
                "error": "Service Unavailable: Database restore or maintenance operation in progress. Please retry shortly.",
                "status": 503
            }).encode("utf-8")
            self.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Retry-After", "5")
            cors_origin = self._get_cors_origin()
            if cors_origin:
                self.send_header("Access-Control-Allow-Origin", cors_origin)
            self.end_headers()
            self.wfile.write(payload)
            return True
        return False

    def _is_origin_allowed(self) -> bool:
        """Verify Origin header to prevent cross-origin abuse from unauthorized web domains.
        
        Strictly rejects external web domains and null origins for state-mutating requests.
        Direct CLI, test clients, and same-origin local connections are permitted.
        """
        origin = self.headers.get("Origin")
        if not origin:
            return True  # Direct API calls, Python urllib, cURL, CLI tools without browser Origin header
        if origin == "null":
            return False  # Reject null origins on state-mutating requests
        try:
            parsed = urlparse(origin)
            hostname = parsed.hostname or ""
            if hostname in ALLOWED_ORIGIN_HOSTS:
                return True
        except Exception:
            pass
        return False

    def _get_cors_origin(self) -> str:
        """Return permitted CORS origin or empty string to deny foreign access."""
        origin = self.headers.get("Origin")
        if not origin or origin == "null":
            return ""
        try:
            parsed = urlparse(origin)
            if parsed.hostname in ALLOWED_ORIGIN_HOSTS:
                return origin
        except Exception:
            pass
        return ""

    def _get_session_token(self) -> Optional[str]:
        """Extract session token from Authorization: Bearer, X-Session-Token, or cookie."""
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        x_tok = self.headers.get("X-Session-Token", "")
        if x_tok:
            return x_tok.strip()
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("session_token="):
                return part[len("session_token="):].strip()
        return None

    def _get_authenticated_user(self, db: sqlite3.Connection) -> Optional[Dict[str, Any]]:
        """Retrieve authenticated user record from current session token, if valid."""
        token = self._get_session_token()
        if not token:
            return None
        return get_user_from_session(db, token)

    def _validate_csrf_if_session(self, user: Optional[Dict[str, Any]], body: Dict[str, Any]) -> bool:
        """Validate CSRF token against session when an authenticated user session is active."""
        if not user:
            return True  # Direct unauthenticated or CLI requests do not carry a web session
        expected_csrf = user.get("csrf_token")
        if not expected_csrf:
            return True
        received_csrf = self.headers.get("X-CSRF-Token", "") or body.get("csrf_token", "")
        return bool(received_csrf and received_csrf == expected_csrf)

    def _send_json(self, data: Any, status: int = HTTPStatus.OK, set_cookie: Optional[str] = None) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        cors_origin = self._get_cors_origin()
        if cors_origin:
            self.send_header("Access-Control-Allow-Origin", cors_origin)
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, text: str, content_type: str = "text/plain; charset=utf-8", status: int = HTTPStatus.OK) -> None:
        payload = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        cors_origin = self._get_cors_origin()
        if cors_origin:
            self.send_header("Access-Control-Allow-Origin", cors_origin)
        self.end_headers()
        self.wfile.write(payload)

    def _read_json_body(self) -> Dict[str, Any]:
        content_len_str = self.headers.get("Content-Length", "0")
        try:
            content_len = int(content_len_str)
        except ValueError:
            content_len = 0
        if content_len > MAX_JSON_PAYLOAD_SIZE:
            raise ValueError(f"Payload too large ({content_len} bytes). Maximum allowed size is {MAX_JSON_PAYLOAD_SIZE} bytes.")
        if content_len <= 0:
            return {}
        raw = self.rfile.read(content_len)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON: {e}")

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests securely."""
        origin = self._get_cors_origin()
        self.send_response(HTTPStatus.NO_CONTENT)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

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
        cors_origin = self._get_cors_origin()
        if cors_origin:
            self.send_header("Access-Control-Allow-Origin", cors_origin)
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
        if self._check_maintenance_mode():
            return
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
                if path == "/api/auth/me":
                    user = self._get_authenticated_user(db)
                    if user:
                        self._send_json({"authenticated": True, "user": user})
                    else:
                        self._send_json({"authenticated": False, "user": None})

                elif path == "/api/auth/reviewers":
                    self._send_json(list_clinical_reviewers(db))

                elif path == "/api/explore/search":
                    self._send_json(
                        {
                            "results": find_entities(
                                db,
                                query.get("q", [""])[0],
                                kind=query.get("type", [None])[0],
                            )
                        }
                    )

                elif path.startswith("/api/explore/entities/"):
                    entity_id = path.removeprefix("/api/explore/entities/")
                    entity = get_entity(db, entity_id)
                    if entity:
                        self._send_json(entity)
                    else:
                        self._send_json({"error": "Entity not documented"}, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/explore/relations":
                    entity_id = query.get("entity_id", [""])[0]
                    try:
                        self._send_json(
                            {
                                "entity_id": entity_id,
                                "relations": get_relations(
                                    db,
                                    entity_id,
                                    relation_class=query.get("relation_class", [None])[0],
                                ),
                            }
                        )
                    except ValueError as error:
                        self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

                elif path == "/api/research/sets":
                    user = self._get_authenticated_user(db)
                    self._send_json(list_research_sets(db, user["user_id"] if user else None))

                elif path.startswith("/api/research/sets/"):
                    set_id = path.removeprefix("/api/research/sets/")
                    user = self._get_authenticated_user(db)
                    result = (
                        get_research_set(db, set_id)
                        if set_visible_to(db, set_id, user["user_id"] if user else None)
                        else None
                    )
                    if result:
                        self._send_json(result)
                    else:
                        self._send_json({"error": "Point set not found"}, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/research/definitions":
                    diagram_id = query.get("diagram_id", [""])[0]
                    user = self._get_authenticated_user(db)
                    if not diagram_visible_to(db, diagram_id, user["user_id"] if user else None):
                        self._send_json({"error": "Diagram unavailable"}, status=HTTPStatus.NOT_FOUND)
                    else:
                        self._send_json(list_definitions(db, diagram_id=diagram_id))

                elif path == "/api/research/timeline":
                    case_id = query.get("case_id", [""])[0]
                    user = self._get_authenticated_user(db)
                    try:
                        self._send_json(
                            {
                                "case_id": case_id,
                                "observations": case_research_timeline(
                                    db, case_id, user["user_id"] if user else None
                                ),
                            }
                        )
                    except ValueError as error:
                        self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

                elif path == "/api/pose/actions":
                    self._send_json(CURATED_ACTION_MUSCLES)

                elif path == "/api/pose/studies":
                    case_id = query.get("case_id", [""])[0]
                    self._send_json(list_pose_studies(db, case_id))

                elif path.startswith("/api/pose/studies/"):
                    study_id = path.removeprefix("/api/pose/studies/")
                    study = get_pose_study(db, study_id)
                    if study:
                        self._send_json(study)
                    else:
                        self._send_json({"error": "Pose study not found"}, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/pose/observations":
                    study_id = query.get("study_id", [""])[0]
                    self._send_json(list_pose_observations(db, study_id))

                elif path == "/api/morphology/avatars":
                    case_id = query.get("case_id", [""])[0]
                    self._send_json(list_avatars(db, case_id))

                elif path.startswith("/api/morphology/avatars/"):
                    avatar_id = path.removeprefix("/api/morphology/avatars/")
                    avatar = get_avatar(db, avatar_id)
                    if avatar:
                        self._send_json(avatar)
                    else:
                        self._send_json({"error": "Avatar not found"}, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/morphology/observations":
                    avatar_id = query.get("avatar_id", [""])[0]
                    self._send_json(list_morphology_observations(db, avatar_id))

                elif path == "/api/proms/catalog":
                    self._send_json(PROM_CATALOG)

                elif path == "/api/proms/responses":
                    case_id = query.get("case_id", [""])[0]
                    self._send_json(list_prom_responses(db, case_id))

                elif path == "/api/adverse-events":
                    case_id = query.get("case_id", [None])[0]
                    self._send_json(list_adverse_events(db, case_id))

                elif path == "/api/cases":
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
        if self._check_maintenance_mode():
            return
        if not self._is_origin_allowed():
            self._send_json({"error": "Forbidden: Cross-origin requests from external web origins or untrusted null origins are rejected."}, status=HTTPStatus.FORBIDDEN)
            return

        parsed = urlparse(self.path)
        path = parsed.path

        try:
            body = self._read_json_body()
        except Exception as e:
            self._send_json({"error": f"Invalid JSON payload: {e}"}, status=HTTPStatus.BAD_REQUEST)
            return

        # Public Spaces must not expose local-auth, writable clinical or research APIs.
        # The safety drill is stateless and remains available as a calculation.
        if os.environ.get("MSK_PUBLIC_DEMO_READONLY") == "1" and path != "/api/screen-safety":
            self._send_json({"error": "Public demonstration is read-only."}, status=HTTPStatus.FORBIDDEN)
            return

        if path == "/api/auth/login":
            uname = body.get("username", "")
            pwd = body.get("password", "")
            with open_db(self.db_path) as db:
                u = authenticate_user(db, uname, pwd)
                if not u:
                    self._send_json({"error": "Invalid username or password"}, status=HTTPStatus.UNAUTHORIZED)
                    return
                sess = create_session(db, u["user_id"])
                u["session_token"] = sess["session_token"]
                u["csrf_token"] = sess["csrf_token"]
                cookie = f"session_token={sess['session_token']}; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800"
                self._send_json({
                    "status": "authenticated",
                    "user": u,
                    "session_token": sess["session_token"],
                    "csrf_token": sess["csrf_token"],
                    "expires_utc": sess["expires_utc"],
                }, set_cookie=cookie)
            return

        if path == "/api/auth/logout":
            token = self._get_session_token()
            if token:
                with open_db(self.db_path) as db:
                    invalidate_session(db, token)
            cookie = "session_token=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"
            self._send_json({"status": "logged_out"}, set_cookie=cookie)
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
                user = self._get_authenticated_user(db)
                if user and not self._validate_csrf_if_session(user, body):
                    self._send_json({"error": "Forbidden: Invalid or missing CSRF token."}, status=HTTPStatus.FORBIDDEN)
                    return

                if path.startswith("/api/research/"):
                    if not user:
                        self._send_json(
                            {"error": "Authentication required for private research editing"},
                            status=HTTPStatus.UNAUTHORIZED,
                        )
                        return
                    if path == "/api/research/sets":
                        result = create_research_set(
                            db,
                            title=body.get("title"),
                            framework=body.get("framework", "custom"),
                            owner=user["user_id"],
                        )
                        self._send_json({"status": "created", "set": result}, status=HTTPStatus.CREATED)
                    elif path == "/api/research/definitions":
                        result = create_definition(db, body, user["user_id"])
                        self._send_json({"status": "created", "definition": result}, status=HTTPStatus.CREATED)
                    elif path == "/api/research/observations":
                        result = create_reactive_observation(db, body, user["user_id"])
                        self._send_json({"status": "created", "observation": result}, status=HTTPStatus.CREATED)
                    else:
                        self._send_json({"error": "Unknown research endpoint"}, status=HTTPStatus.NOT_FOUND)
                    return

                if path == "/api/pose/studies":
                    if not user:
                        self._send_json({"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    res = create_pose_study(
                        db,
                        case_id=body.get("case_id", ""),
                        title=body.get("title", ""),
                        camera_view=body.get("camera_view", "front"),
                        image_asset=body.get("image_asset", ""),
                        image_sha256=body.get("image_sha256", ""),
                        raw_landmarks=body.get("landmarks", []),
                    )
                    self._send_json({"status": "created", "study": res}, status=HTTPStatus.CREATED)
                    return

                if path == "/api/pose/observations":
                    if not user:
                        self._send_json({"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    res = record_pose_observation(
                        db,
                        study_id=body.get("study_id", ""),
                        case_id=body.get("case_id", ""),
                        visit_id=body.get("visit_id"),
                        symptom_zone=body.get("symptom_zone", ""),
                        pain_score=body.get("pain_score"),
                        movement_phase=body.get("movement_phase", ""),
                        reported_symptoms=body.get("reported_symptoms", ""),
                        functional_limitation=body.get("functional_limitation", ""),
                        notes=body.get("notes", ""),
                    )
                    self._send_json({"status": "created", "observation": res}, status=HTTPStatus.CREATED)
                    return

                if path == "/api/morphology/avatars":
                    if not user:
                        self._send_json({"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    res = create_avatar(
                        db,
                        case_id=body.get("case_id", ""),
                        title=body.get("title", ""),
                        height_cm=float(body.get("height_cm", 170.0)),
                        weight_kg=float(body["weight_kg"]) if body.get("weight_kg") is not None else None,
                        chest_circ_cm=float(body["chest_circ_cm"]) if body.get("chest_circ_cm") is not None else None,
                        waist_circ_cm=float(body["waist_circ_cm"]) if body.get("waist_circ_cm") is not None else None,
                        hip_circ_cm=float(body["hip_circ_cm"]) if body.get("hip_circ_cm") is not None else None,
                        extra_params=body.get("extra_params"),
                        photo_front=body.get("photo_front", ""),
                        photo_side=body.get("photo_side", ""),
                        photo_back=body.get("photo_back", ""),
                        notes=body.get("notes", ""),
                    )
                    self._send_json({"status": "created", "avatar": res}, status=HTTPStatus.CREATED)
                    return

                if path == "/api/morphology/observations":
                    if not user:
                        self._send_json({"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    res = record_morphology_observation(
                        db,
                        avatar_id=body.get("avatar_id", ""),
                        case_id=body.get("case_id", ""),
                        visit_id=body.get("visit_id"),
                        body_region=body.get("body_region", ""),
                        observation_type=body.get("observation_type", "circumference_delta"),
                        severity=body.get("severity"),
                        findings_summary=body.get("findings_summary", ""),
                        operator_notes=body.get("operator_notes", ""),
                    )
                    self._send_json({"status": "created", "observation": res}, status=HTTPStatus.CREATED)
                    return

                if path == "/api/proms/responses":
                    if not user:
                        self._send_json({"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    res = record_prom_response(
                        db,
                        case_id=body.get("case_id", ""),
                        visit_id=body.get("visit_id"),
                        prom_type=body.get("prom_type", ""),
                        item_responses=body.get("item_responses", []),
                    )
                    self._send_json({"status": "created", "prom": res}, status=HTTPStatus.CREATED)
                    return

                if path == "/api/adverse-events":
                    if not user:
                        self._send_json({"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    res = record_adverse_event(
                        db,
                        case_id=body.get("case_id", ""),
                        visit_id=body.get("visit_id"),
                        event_category=body.get("event_category", "musculoskeletal"),
                        ctcae_grade=int(body.get("ctcae_grade", 1)),
                        symptom_description=body.get("symptom_description", ""),
                        onset_utc=body.get("onset_utc", ""),
                        resolution_status=body.get("resolution_status", "resolved"),
                        action_taken=body.get("action_taken", ""),
                        reported_by=user.get("user_id", "USR-SYSTEM"),
                    )
                    self._send_json({"status": "created", "adverse_event": res}, status=HTTPStatus.CREATED)
                    return

                if path == "/api/auth/verify-reviewer":
                    if not user:
                        self._send_json({"error": "Authentication required. Admin privileges required."}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    if user.get("role") != "admin":
                        self._send_json({"error": "Forbidden: Administrator role required to verify reviewer credentials."}, status=HTTPStatus.FORBIDDEN)
                        return
                    rev_id = body.get("reviewer_id")
                    st = body.get("status", "VERIFIED_ACTIVE")
                    nts = body.get("notes", "")
                    res = verify_reviewer(db, rev_id, user["user_id"], status=st, notes=nts)
                    self._send_json({"status": "verified", "reviewer": res})
                    return

                elif path == "/api/visit":
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
                    author_role = user.get("role") if user else body.get("role", "student")
                    soap_id = create_soap_note(
                        db,
                        visit_id=int(body["visit_id"]),
                        subjective=body["subjective"],
                        objective=body["objective"],
                        assessment=body["assessment"],
                        plan=body["plan"],
                        author_role=author_role,
                    )
                    self._send_json({"status": "created", "soap_id": soap_id})

                elif path == "/api/review-soap":
                    if user:
                        reviewer_role = user.get("role", "")
                        reviewer_name = user.get("display_name", "")
                    else:
                        reviewer_role = body.get("role", "reviewer")
                        reviewer_name = body.get("reviewer", "Clinical Supervisor")

                    if reviewer_role != "reviewer":
                        self._send_json({"error": "Forbidden: Only users with 'reviewer' role can approve or reject SOAP notes."}, status=HTTPStatus.FORBIDDEN)
                        return

                    review_soap_note(
                        db,
                        soap_id=int(body["soap_id"]),
                        reviewer_name=reviewer_name,
                        reviewer_role=reviewer_role,
                        decision=body["decision"],
                        feedback=body.get("feedback", ""),
                    )
                    self._send_json({"status": "reviewed", "decision": body["decision"], "reviewer": reviewer_name})

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
                    p_role = user.get("role") if user else body.get("role", "student")
                    sess_id = record_session(
                        db,
                        visit_id=int(body["visit_id"]),
                        modality=body["modality"],
                        duration_min=int(body["duration_min"]),
                        target_structures=body.get("target_structures", "[]"),
                        parameters=body.get("parameters", ""),
                        adverse_reactions=body.get("adverse_reactions", "none"),
                        practitioner_role=p_role,
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
                    if not user:
                        self._send_json({"error": "Authentication required. Admin privileges required for database backup."}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    if user.get("role") != "admin":
                        self._send_json({"error": "Forbidden: Administrator role required for database backup."}, status=HTTPStatus.FORBIDDEN)
                        return
                    name = body.get("name")
                    try:
                        bp = get_safe_backup_path(name)
                    except (ValueError, PermissionError) as pe:
                        self._send_json({"error": str(pe)}, status=HTTPStatus.BAD_REQUEST)
                        return
                    self._send_json(backup_database(db, str(bp)))

                elif path == "/api/governance/restore":
                    if not user:
                        self._send_json({"error": "Authentication required. Admin privileges required for database restore."}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    if user.get("role") != "admin":
                        self._send_json({"error": "Forbidden: Administrator role required for database restore."}, status=HTTPStatus.FORBIDDEN)
                        return
                    name = body.get("name") or body.get("backup_name")
                    if not name:
                        self._send_json({"error": "Missing backup name to restore"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        bp = get_safe_backup_path(name)
                    except (ValueError, PermissionError) as pe:
                        self._send_json({"error": str(pe)}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        res = restore_database_safely(self.db_path, str(bp))
                        self._send_json(res)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

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
            except (ValueError, PermissionError, sqlite3.IntegrityError) as e:
                db.rollback()
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as e:
                db.rollback()
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_PUT(self) -> None:
        if self._check_maintenance_mode():
            return
        if not self._is_origin_allowed():
            self._send_json({"error": "Forbidden: Cross-origin requests from external web origins or untrusted null origins are rejected."}, status=HTTPStatus.FORBIDDEN)
            return

        parsed = urlparse(self.path)
        path = parsed.path
        try:
            body = self._read_json_body()
        except Exception as e:
            self._send_json({"error": f"Invalid JSON payload: {e}"}, status=HTTPStatus.BAD_REQUEST)
            return

        # Public Spaces must not expose local-auth, writable clinical or research APIs.
        # The safety drill is stateless and remains available as a calculation.
        if os.environ.get("MSK_PUBLIC_DEMO_READONLY") == "1" and path != "/api/screen-safety":
            self._send_json({"error": "Public demonstration is read-only."}, status=HTTPStatus.FORBIDDEN)
            return

        with open_db(self.db_path) as db:
            try:
                user = self._get_authenticated_user(db)
                if user and not self._validate_csrf_if_session(user, body):
                    self._send_json({"error": "Forbidden: Invalid or missing CSRF token."}, status=HTTPStatus.FORBIDDEN)
                    return

                if path.startswith("/api/pose/studies/") and path.endswith("/landmarks"):
                    parts = path.split("/")
                    study_id = parts[4]
                    res = update_landmarks(db, study_id, body.get("landmarks", []))
                    self._send_json({"status": "updated", "study": res})
                    return

                if path.startswith("/api/morphology/avatars/"):
                    parts = path.split("/")
                    avatar_id = parts[4]
                    res = update_avatar_params(db, avatar_id, body.get("params", {}), notes=body.get("notes"))
                    self._send_json({"status": "updated", "avatar": res})
                    return

                if path.startswith("/api/points/"):
                    pt_id = path.split("/")[3]
                    ch_type = body.get("change_type", "UPDATE_COORDS")
                    notes = body.get("notes", "")
                    updated_pt = update_point(db, pt_id, body, author=body.get("author", "Clinical Educator"), change_type=ch_type, notes=notes)
                    self._send_json({"status": "updated", "point": updated_pt})
                else:
                    self._send_json({"error": f"Endpoint '{path}' not found"}, status=HTTPStatus.NOT_FOUND)
            except (ValueError, PermissionError, sqlite3.IntegrityError) as e:
                db.rollback()
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as e:
                db.rollback()
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_DELETE(self) -> None:
        if os.environ.get("MSK_PUBLIC_DEMO_READONLY") == "1":
            self._send_json({"error": "Public demonstration is read-only."}, status=HTTPStatus.FORBIDDEN)
            return
        if self._check_maintenance_mode():
            return
        if not self._is_origin_allowed():
            self._send_json({"error": "Forbidden: Cross-origin requests from external web origins or untrusted null origins are rejected."}, status=HTTPStatus.FORBIDDEN)
            return

        parsed = urlparse(self.path)
        path = parsed.path

        with open_db(self.db_path) as db:
            try:
                user = self._get_authenticated_user(db)
                if user and not self._validate_csrf_if_session(user, {}):
                    self._send_json({"error": "Forbidden: Invalid or missing CSRF token."}, status=HTTPStatus.FORBIDDEN)
                    return

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
            except (ValueError, PermissionError, sqlite3.IntegrityError) as e:
                db.rollback()
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as e:
                db.rollback()
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def create_server(db_path: str, host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """Create configured HTTPServer instance."""
    if host not in ("127.0.0.1", "localhost", "::1") and os.environ.get("MSK_PUBLIC_DEMO_READONLY") != "1":
        raise PermissionError("Non-local binding requires MSK_PUBLIC_DEMO_READONLY=1; writable demo server must remain on localhost")
    with open_db(db_path) as db:
        init_db(db)
        seed_db(db)

    class ConfiguredHandler(MSKRequestHandler):
        pass

    ConfiguredHandler.db_path = db_path
    return ThreadingHTTPServer((host, port), ConfiguredHandler)


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
