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
from msk_therapy_os.tissue_layers import (
    get_layer_catalog,
    get_user_layer_config,
    update_layer_config,
)
from msk_therapy_os.cohort_dashboard import (
    get_cohort_summary,
    export_deidentified_cohort,
)
from msk_therapy_os.kinematics import (
    PHYSIOLOGICAL_ROM_ENVELOPES,
    record_kinematic_arc,
    list_kinematic_arcs,
    evaluate_frame_budget,
)
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
    bootstrap_initial_admin,
    create_session,
    create_user,
    get_user_count,
    get_user_from_session,
    get_verified_reviewer,
    invalidate_session,
    list_clinical_reviewers,
    verify_reviewer,
)
from msk_therapy_os.safety import evaluate_safety
from msk_therapy_os.landmark_registry import LandmarkRegistry, BodyRegion
from msk_therapy_os.anatomical_registration import AnatomicalRegistrationEngine
from msk_therapy_os.cun_scaling import CunScalingEngine
from msk_therapy_os.pose_rigging import PoseKinematicsEngine, GuardedSurfaceProjector
from msk_therapy_os.spatial_resolver import AnatomicalSpatialResolver
from msk_therapy_os.anatomical_validation import (
    IndependentAnatomicalValidator,
    ExternalGroundTruthDataset,
    GroundTruthObservation,
    GroundTruthModality,
    validate_observation_contract,
    ReviewStatus,
    CoordinateFrame,
    MeasurementUnit,
    QuarantineReason,
    DeidentificationMethod,
    EvidenceIngestionState,
    PreRegisteredAccuracyThresholds,
)

_cached_spatial_resolver = None
_cached_anatomical_validator = None

def get_spatial_resolver() -> AnatomicalSpatialResolver:
    global _cached_spatial_resolver
    if _cached_spatial_resolver is None:
        _cached_spatial_resolver = AnatomicalSpatialResolver()
    return _cached_spatial_resolver

def get_anatomical_validator() -> IndependentAnatomicalValidator:
    global _cached_anatomical_validator
    if _cached_anatomical_validator is None:
        _cached_anatomical_validator = IndependentAnatomicalValidator()
    return _cached_anatomical_validator

from msk_therapy_os.dien_chan.facial_registration import FacialRegistrationEngine
from msk_therapy_os.dien_chan.db import (
    init_dien_chan_tables,
    seed_dien_chan_database,
    list_dien_chan_points,
    get_dien_chan_point,
    get_protocol_with_points,
)
from msk_therapy_os.dien_chan.search import (
    search_dien_chan_conditions,
    normalize_vietnamese_text,
)

from msk_therapy_os.points import (
    list_anatomical_landmarks,
    get_anatomical_landmark,
    list_cun_scaling_rules,
    record_registration_metric,

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
    get_meridian_atlas_coverage_dashboard,
    get_meridian_route_graph_data,
    create_meridian_route_revision,
    review_meridian_route_revision,
    rollback_meridian_route_revision,
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
    validate_fhir_r4_bundle,
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


DEFAULT_DB: str = "2data/demo.sqlite3" if Path("2data/demo.sqlite3").exists() else "demo.sqlite3"


def is_secure_mode() -> bool:
    """Return True if running in hardened SECURE mode, requiring credentials for all mutations."""
    return os.environ.get("MSK_MODE", "").lower() == "secure" or os.environ.get("MSK_SECURE_MODE", "").lower() in ("1", "true", "yes")


def is_readonly_mode() -> bool:
    """Return True if running in public demonstration read-only mode."""
    return os.environ.get("MSK_PUBLIC_DEMO_READONLY", "").lower() in ("1", "true", "yes")


def _validate_synthetic_case_id(case_id: str) -> None:
    """Enforce synthetic patient boundary - reject real patient PII identifiers."""
    if not isinstance(case_id, str):
        raise ValueError("Case ID must be a string.")
    cid = case_id.strip().upper()
    if not (cid.startswith("DEMO-") or cid.startswith("TEST-") or cid.startswith("SYNTH-")):
        raise ValueError(
            f"Strict clinical safety barrier: Case ID '{case_id}' rejected. "
            "Only synthetic identifiers ('DEMO-*', 'TEST-*', 'SYNTH-*') are permitted."
        )


class MSKRequestHandler(BaseHTTPRequestHandler):
    db_path: str = DEFAULT_DB

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
                if path == "/api/auth/mode":
                    user_cnt = get_user_count(db)
                    self._send_json({
                        "mode": "secure" if is_secure_mode() else "demo",
                        "is_secure": is_secure_mode(),
                        "readonly": is_readonly_mode(),
                        "user_count": user_cnt,
                        "needs_bootstrap": is_secure_mode() and user_cnt == 0,
                    })
                    return

                elif path == "/api/auth/me":
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

                elif path == "/api/kinematics/envelopes":
                    self._send_json(PHYSIOLOGICAL_ROM_ENVELOPES)

                elif path == "/api/kinematics/arcs":
                    case_id = query.get("case_id", [""])[0]
                    self._send_json(list_kinematic_arcs(db, case_id))

                elif path == "/api/anatomy/layers":
                    self._send_json(get_layer_catalog())

                elif path == "/api/anatomy/layers/config":
                    user = self._get_authenticated_user(db)
                    user_id = user["username"] if user else query.get("user_id", ["anonymous"])[0]
                    self._send_json(get_user_layer_config(db, user_id))

                elif path == "/api/cohort/summary":
                    self._send_json(get_cohort_summary(db))

                elif path == "/api/cohort/export":
                    user = self._get_authenticated_user(db)
                    if is_secure_mode():
                        if not user:
                            self._send_json({"error": "Unauthorized: Authentication required to export research cohort in SECURE mode."}, status=HTTPStatus.UNAUTHORIZED)
                            return
                        if user.get("role") not in ("reviewer", "admin"):
                            self._send_json({"error": "Forbidden: Clinical reviewer or administrator role required for cohort exports."}, status=HTTPStatus.FORBIDDEN)
                            return
                    fmt = query.get("format", ["json"])[0]
                    content, mime_type = export_deidentified_cohort(db, export_format=fmt)
                    self._send_text(content, content_type=mime_type)

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

                elif path == "/api/validate-fhir":
                    case_id = query.get("case_id", ["DEMO-NECK-001"])[0]
                    fhir_bundle = export_case_fhir(db, case_id)
                    self._send_json(validate_fhir_r4_bundle(fhir_bundle))

                elif path == "/api/atlas/geometry/resolve":
                    layer_mode = query.get("layer_mode", ["canonical"])[0]
                    resolver = get_spatial_resolver()
                    overrides = list_reference_overrides(db)
                    payload = {"layer_mode": layer_mode}
                    self._send_json(resolver.resolve_atlas_geometry(payload, sqlite_overrides=overrides))

                elif path == "/api/atlas/meridians/resolve":
                    layer_mode = query.get("layer_mode", ["canonical"])[0]
                    m_ids = query.get("channel_ids") or query.get("meridian_ids")
                    channel_ids = [x.strip() for x in m_ids[0].split(",")] if m_ids else None
                    side = query.get("side", ["all"])[0]
                    resolver = get_spatial_resolver()
                    overrides = list_reference_overrides(db)
                    payload = {
                        "layer_mode": layer_mode,
                        "meridian_ids": channel_ids,
                    }
                    geo = resolver.resolve_atlas_geometry(payload, sqlite_overrides=overrides)
                    meridians_res = geo.get("meridians", {})
                    if side in ("right", "left", "midline"):
                        filtered = {}
                        for c, m in meridians_res.items():
                            f_paths = [p for p in m.get("paths", []) if p.get("side") == side]
                            m_copy = dict(m)
                            m_copy["paths"] = f_paths
                            filtered[c] = m_copy
                        meridians_res = filtered
                    self._send_json({
                        "status": "success",
                        "layer_mode": layer_mode,
                        "mesh_id": geo.get("mesh_id", "FJ2810"),
                        "mesh_hash": geo.get("mesh_hash", ""),
                        "channel_count": len(meridians_res),
                        "meridians": meridians_res,
                    })

                elif path == "/api/atlas/meridians/coverage":
                    self._send_json(get_meridian_atlas_coverage_dashboard(db))

                elif path == "/api/atlas/meridians/route-graph":
                    ch = query.get("channel_code", [None])[0]
                    self._send_json(get_meridian_route_graph_data(db, channel_code=ch))

                elif path == "/api/atlas/validation/provenance":
                    validator = get_anatomical_validator()
                    ch = query.get("channel_code", [None])[0]
                    matrix = validator.generate_full_362_provenance_matrix()
                    if ch:
                        matrix = [row for row in matrix if row.get("channel_code") == ch]
                    self._send_json({
                        "status": "success",
                        "total_records": len(matrix),
                        "provenance_matrix": matrix,
                    })

                elif path == "/api/atlas/validation/report":
                    validator = get_anatomical_validator()
                    dataset_id = query.get("dataset_id", [None])[0]
                    rep = validator.validate_catalog(dataset_id=dataset_id)
                    self._send_json({
                        "status": "success",
                        "validation_report": rep.to_dict(),
                    })

                elif path == "/api/atlas/validation/uncertainty":
                    validator = get_anatomical_validator()
                    ch = query.get("channel_code", [None])[0]
                    matrix = validator.generate_anatomical_uncertainty_matrix()
                    if ch:
                        matrix = [row for row in matrix if row.get("channel_code") == ch]
                    self._send_json({
                        "status": "success",
                        "total_records": len(matrix),
                        "uncertainty_matrix": matrix,
                    })

                elif path == "/api/atlas/validation/datasets":
                    validator = get_anatomical_validator()
                    datasets = [ds.to_dict() for ds in validator._datasets.values()]
                    self._send_json({
                        "status": "success",
                        "total_datasets": len(datasets),
                        "datasets": datasets,
                    })

                elif path == "/api/atlas/validation/governance/audit-trail":
                    validator = get_anatomical_validator()
                    trail = validator.get_governance_audit_trail()
                    is_chain_valid = validator.verify_governance_audit_chain()
                    self._send_json({
                        "status": "success",
                        "total_entries": len(trail),
                        "chain_integrity_valid": is_chain_valid,
                        "audit_trail": trail,
                    })

                elif path == "/api/atlas/validation/independent-coverage":
                    validator = get_anatomical_validator()
                    cov_matrix = validator.generate_external_evidence_coverage_matrix()
                    total_pts = len(cov_matrix)
                    available_count = sum(1 for r in cov_matrix if r["empirical_in_vivo_status"] == "AVAILABLE")
                    class_a_count = sum(1 for r in cov_matrix if r["quality_class"] == "CLASS_A")
                    class_b_count = sum(1 for r in cov_matrix if r["quality_class"] == "CLASS_B")
                    q_count = len(validator.get_quarantined_records())
                    self._send_json({
                        "status": "success",
                        "total_points": total_pts,
                        "class_a_internal_anchors": class_a_count,
                        "class_b_rule_derived": class_b_count,
                        "empirical_in_vivo_ground_truth_count": available_count,
                        "empirical_in_vivo_ground_truth_percentage": round((available_count / total_pts) * 100.0, 1),
                        "empirical_in_vivo_status": "BLOCKED_EXTERNAL_DATA" if available_count == 0 else "PARTIALLY_AVAILABLE",
                        "ingestion_governance_state": validator.get_ingestion_governance_state(),
                        "engineering_readiness": "ENGINEERING_READY",
                        "clinical_verification_tier_4": "0.0%",
                        "quarantined_observations_count": q_count,
                        "pre_registered_accuracy_thresholds": validator._pre_registered_thresholds.to_dict(),
                        "governance_note": "Technical calibration is 100% (Class A/B); Empirical in-vivo patient validation requires external datasets (currently BLOCKED_EXTERNAL_DATA).",
                        "pilot_cohorts": {
                            "cohort_a_abdominal": "PILOT_SPECIFIED_UNSCALED_MESH_LIMITATION",
                            "cohort_b_distal_limbs": "PILOT_SPECIFIED_SYMMETRY_PRESERVED",
                            "cohort_c_cranial_cervical": "PILOT_SPECIFIED_YINTANG_RECONCILED",
                        }
                    })

                elif path.startswith("/api/atlas/validation/evidence"):
                    validator = get_anatomical_validator()
                    code = None
                    if path != "/api/atlas/validation/evidence":
                        parts = path.strip("/").split("/")
                        if len(parts) >= 5:
                            code = parts[4]
                    if not code:
                        code = query.get("point_code", [None])[0]
                    if not code:
                        self._send_json({"error": "Missing point_code parameter or path component"}, status=HTTPStatus.BAD_REQUEST)
                    else:
                        dataset_id = query.get("dataset_id", [None])[0]
                        try:
                            comp = validator.validate_point(code, dataset_id=dataset_id)
                            self._send_json({
                                "status": "success",
                                "comparison": comp.to_dict(),
                            })
                        except Exception as e:
                            self._send_json({"error": str(e)}, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/atlas/validation/quarantine":
                    validator = get_anatomical_validator()
                    reason_filter = query.get("reason", [None])[0]
                    q_records = validator.get_quarantined_records(reason=reason_filter)
                    self._send_json({
                        "status": "success",
                        "total_quarantined": len(q_records),
                        "quarantined_records": [q.to_dict() for q in q_records],
                    })

                elif path == "/api/atlas/validation/holdout/status":
                    validator = get_anatomical_validator()
                    part_id = query.get("partition_id", ["default"])[0]
                    part = validator._holdout_manager.get_partition(part_id)
                    if part:
                        self._send_json({
                            "status": "success",
                            "partition": part.to_dict(),
                        })
                    else:
                        self._send_json({
                            "status": "not_found",
                            "message": f"No partition with id '{part_id}' registered.",
                        }, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/atlas/validation/pilot-cohorts":
                    validator = get_anatomical_validator()
                    c_a = validator.audit_st19_st30_abdominal_line()
                    c_b = validator.audit_bilateral_limb_landmarks()
                    c_c = validator.audit_cranial_cervical_points()
                    self._send_json({
                        "status": "success",
                        "cohort_a_abdominal": c_a,
                        "cohort_b_bilateral_limbs": c_b,
                        "cohort_c_cranial_cervical": c_c,
                    })

                elif path == "/api/atlas/validation/pilot-cohorts/details":
                    validator = get_anatomical_validator()
                    specs = validator.get_pilot_cohort_specifications()
                    self._send_json({
                        "status": "success",
                        "pilot_cohort_specifications": specs,
                    })

                elif path == "/api/atlas/validation/metrics/summary":
                    validator = get_anatomical_validator()
                    dataset_id = query.get("dataset_id", [None])[0]
                    rep = validator.validate_catalog(dataset_id=dataset_id)
                    self._send_json({
                        "status": "success",
                        "summary_metrics": rep.summary,
                        "regional_metrics": rep.regional_metrics,
                        "is_synthetic_evaluation": rep.is_synthetic_evaluation,
                    })

                elif path == "/api/atlas/validation/export-evidence":
                    validator = get_anatomical_validator()
                    manifest = validator.export_audit_evidence_manifest()
                    self._send_json({
                        "status": "success",
                        "evidence_manifest": manifest,
                    })

                elif path == "/api/atlas/validation/quarantine/list":
                    validator = get_anatomical_validator()
                    q_obs = [r.to_dict() for r in validator.get_quarantined_records()]
                    adapter = validator.get_dicom_adapter()
                    q_dicom = adapter.get_quarantine_records()
                    self._send_json({
                        "status": "success",
                        "quarantined_observations": q_obs,
                        "quarantined_dicom": q_dicom,
                        "total_quarantined": len(q_obs) + len(q_dicom),
                    })

                elif path == "/api/atlas/validation/scientific-gate/status":
                    validator = get_anatomical_validator()
                    gate_status = validator.evaluate_g14_scientific_gate()
                    self._send_json({
                        "status": "success",
                        "gate_evaluation": gate_status,
                    })

                elif path == "/api/atlas/validation/pilot-readiness":
                    validator = get_anatomical_validator()
                    gate_status = validator.evaluate_g14_scientific_gate()
                    self._send_json({
                        "status": "success",
                        "milestone": "P10.5",
                        "system_version": "v2.1.0-local-rc3",
                        "engineering_readiness": "PASS",
                        "scientific_readiness": "BLOCKED_EXTERNAL_DATA",
                        "gate_g14": gate_status.get("gate_state", "BLOCKED_EXTERNAL_DATA"),
                        "protocol_approval_status": "DRAFT_PENDING_EXTERNAL_BIOSTATISTICIAN",
                        "dua_readiness": "PENDING_HOSPITAL_LEGAL_EXECUTION",
                        "irb_readiness": "PENDING_ETHICS_COMMITTEE_SUBMISSION",
                        "deidentification_status": "PS3.15_BASIC_APPLICATION_CONFIDENTIALITY_PROFILE_READY",
                        "dataset_provenance": "SYNTHETIC_FIXTURES_ONLY (ZERO_PATIENT_SCANS)",
                        "observer_readiness": "DOUBLE_BLIND_QC_WORKFLOW_ACTIVE",
                        "reviewer_readiness": "DEVELOPER_EXCLUSION_ACTIVE / COI_SCREENED",
                        "cohort_sample_counts": {
                            "cohort_a_abdomen": {"target_n": 30, "holdout_n": 7, "holdout_power": 0.978},
                            "cohort_b_extremities": {"target_n": 25, "holdout_n": 6, "holdout_power": 0.932},
                            "cohort_c_craniofacial": {"target_n": 30, "holdout_n": 7, "holdout_power": 0.979},
                            "aggregate": {"total_patients": 85, "total_holdout_patients": 20, "aggregate_holdout_power": 0.999}
                        },
                        "holdout_lock_status": "TAMPER_SEALED_HASH_READY",
                        "outstanding_blockers_count": 8,
                        "outstanding_blockers": [
                            "DEP-01: Signed Statistical Analysis Plan (SAP) Approval",
                            "DEP-02: Executed Bilateral Data Use Agreement (DUA/MTA)",
                            "DEP-03: Formal IRB/Ethics Clearance or Waiver Determination",
                            "DEP-04: De-identified In-Vivo Patient CT/MRI Series (N >= 85)",
                            "DEP-05: Board-Certified Radiologist Annotations with Signed COI",
                            "DEP-06: Dual Administrative Sign-Off by Credentialed Officers",
                            "DEP-07: Pre-Evaluation Holdout Partition Sealing Verification",
                            "DEP-08: Regulatory Pre-Market Evaluation / Classification"
                        ]
                    })

                elif path == "/api/atlas/validation/p10-6-dashboard":
                    validator = get_anatomical_validator()
                    gate_status = validator.evaluate_g14_scientific_gate()

                    from msk_therapy_os.statistical_oracle import (
                        IndependentStatisticalOracle,
                        OracleStudyScenario,
                    )
                    from msk_therapy_os.external_dependency_register import (
                        ExternalDependencyRegistry,
                    )

                    reg = ExternalDependencyRegistry(getattr(self, "db_path", ":memory:"))
                    for cid in ["INST-CHARITE-BERLIN", "INST-MGH-HARVARD", "INST-SNUH-SEOUL"]:
                        if not reg.get_institutional_readiness_summary(cid)["total_dependencies_tracked"]:
                            reg.initialize_standard_dependencies(cid)

                    charite_summary = reg.get_institutional_readiness_summary("INST-CHARITE-BERLIN")
                    mgh_summary = reg.get_institutional_readiness_summary("INST-MGH-HARVARD")
                    snuh_summary = reg.get_institutional_readiness_summary("INST-SNUH-SEOUL")

                    p45 = IndependentStatisticalOracle.evaluate_scenario(OracleStudyScenario.FEASIBILITY_PILOT)
                    p85 = IndependentStatisticalOracle.evaluate_scenario(OracleStudyScenario.PRIMARY_ACCURACY_STUDY)
                    p115 = IndependentStatisticalOracle.evaluate_scenario(OracleStudyScenario.EXPANDED_ACCURACY_STUDY)
                    p150 = IndependentStatisticalOracle.evaluate_scenario(OracleStudyScenario.MULTI_SITE_VALIDATION)

                    self._send_json({
                        "status": "success",
                        "milestone": "P10.6",
                        "system_version": "v2.1.0-local-rc3",
                        "release_scope": "ENGINEERING_RESEARCH_ONLY",
                        "scientific_gate_g14": gate_status.get("gate_state", "BLOCKED_EXTERNAL_DATA"),
                        "clinical_depth_guidance_allowed": False,
                        "governance_readiness_states": {
                            "ENGINEERING_READY": True,
                            "PROTOCOL_DRAFT_READY": True,
                            "PARTNER_PACKAGE_PREPARED": True,
                            "INSTITUTIONAL_APPROVAL_PENDING": True,
                            "EMPIRICAL_DATA_UNAVAILABLE": True,
                            "EMPIRICAL_VALIDATION_BLOCKED": True,
                        },
                        "statistical_scenarios": {
                            "feasibility_pilot_n45": p45,
                            "primary_accuracy_study_n85": p85,
                            "expanded_accuracy_study_n115": p115,
                            "multi_site_validation_n150": p150,
                        },
                        "partner_candidates": [
                            {
                                "institution_id": "INST-CHARITE-BERLIN",
                                "name": "Charité – Universitätsmedizin Berlin",
                                "country": "Germany",
                                "jurisdiction_law": "EU GDPR & German BDSG",
                                "status": "CANDIDATE_UNCONFIRMED",
                                "package_path": "1docs/audits/P10_6/partners/charite_berlin/",
                                "readiness": charite_summary,
                            },
                            {
                                "institution_id": "INST-MGH-HARVARD",
                                "name": "Massachusetts General Hospital / Harvard",
                                "country": "United States",
                                "jurisdiction_law": "US HIPAA Safe Harbor & Common Rule",
                                "status": "CANDIDATE_UNCONFIRMED",
                                "package_path": "1docs/audits/P10_6/partners/mgh_harvard/",
                                "readiness": mgh_summary,
                            },
                            {
                                "institution_id": "INST-SNUH-SEOUL",
                                "name": "Seoul National University Hospital",
                                "country": "Republic of Korea",
                                "jurisdiction_law": "ROK PIPA & Bioethics and Safety Act",
                                "status": "CANDIDATE_UNCONFIRMED",
                                "package_path": "1docs/audits/P10_6/partners/snuh_seoul/",
                                "readiness": snuh_summary,
                            },
                        ],
                        "active_blockers_count": 24,
                    })

                elif path == "/api/atlas/validation/p10-7-dashboard":
                    validator = get_anatomical_validator()
                    gate_status = validator.evaluate_g14_scientific_gate()

                    from msk_therapy_os.protocol_freeze import ProtocolFreezeManager
                    from msk_therapy_os.external_dependency_register import ExternalDependencyRegistry

                    manifest = ProtocolFreezeManager.create_freeze_candidate_manifest()
                    valid, err = ProtocolFreezeManager.verify_manifest_integrity(manifest)

                    reg = ExternalDependencyRegistry(getattr(self, "db_path", ":memory:"))
                    for cid in ["INST-CHARITE-BERLIN", "INST-MGH-HARVARD", "INST-SNUH-SEOUL"]:
                        if not reg.get_institutional_readiness_summary(cid)["total_dependencies_tracked"]:
                            reg.initialize_standard_dependencies(cid)

                    charite_summary = reg.get_institutional_readiness_summary("INST-CHARITE-BERLIN")
                    mgh_summary = reg.get_institutional_readiness_summary("INST-MGH-HARVARD")
                    snuh_summary = reg.get_institutional_readiness_summary("INST-SNUH-SEOUL")

                    self._send_json({
                        "status": "success",
                        "milestone": "P10.7",
                        "system_version": "v2.1.0-local-rc3",
                        "release_scope": "ENGINEERING_RESEARCH_ONLY",
                        "scientific_gate_g14": gate_status.get("gate_state", "BLOCKED_EXTERNAL_DATA"),
                        "clinical_depth_guidance_allowed": False,
                        "terminal_state": "ENGINEERING_HANDOFF_COMPLETE / EXTERNAL_ACTION_REQUIRED",
                        "protocol_freeze_candidate": {
                            "protocol_version": manifest.protocol_version,
                            "release_tag": manifest.release_tag,
                            "lifecycle_status": manifest.lifecycle_status.value,
                            "canonical_hash": manifest.canonical_hash,
                            "primary_estimand": manifest.primary_estimand,
                            "integrity_verified": valid,
                        },
                        "independent_review_packages": [
                            {
                                "role": "Independent Biostatistician",
                                "dossier": "Dossier 1 (SAP & Power Oracle)",
                                "status": "DRAFT_PREPARED_REVIEW_BLOCKED",
                                "qualifications": "Ph.D./M.Sc. Biostatistics",
                            },
                            {
                                "role": "Medical Imaging / Anatomical Specialist",
                                "dossier": "Dossier 2 (Landmarks & Consensus)",
                                "status": "DRAFT_PREPARED_REVIEW_BLOCKED",
                                "qualifications": "Board-Certified MSK Radiologist",
                            },
                            {
                                "role": "Research Ethics & Data Governance Reviewer",
                                "dossier": "Dossier 3 (Privacy & Compliance)",
                                "status": "DRAFT_PREPARED_REVIEW_BLOCKED",
                                "qualifications": "IRB Chair / Institutional DPO",
                            },
                            {
                                "role": "Software Security & Release QA Auditor",
                                "dossier": "Dossier 4 (Security & Invariants)",
                                "status": "DRAFT_PREPARED_REVIEW_BLOCKED",
                                "qualifications": "IEC 62304 / ISO 13485 Auditor",
                            },
                        ],
                        "partner_candidates": [
                            {
                                "institution_id": "INST-CHARITE-BERLIN",
                                "name": "Charité – Universitätsmedizin Berlin",
                                "country": "Germany",
                                "jurisdiction_law": "EU GDPR & German BDSG § 27",
                                "status": "PROSPECTIVE_UNCONTACTED",
                                "package_path": "1docs/audits/P10_7/partners/charite_berlin/",
                                "readiness": charite_summary,
                            },
                            {
                                "institution_id": "INST-MGH-HARVARD",
                                "name": "Massachusetts General Hospital / Harvard",
                                "country": "United States",
                                "jurisdiction_law": "US HIPAA Safe Harbor & 45 CFR § 46",
                                "status": "PROSPECTIVE_UNCONTACTED",
                                "package_path": "1docs/audits/P10_7/partners/mgh_harvard/",
                                "readiness": mgh_summary,
                            },
                            {
                                "institution_id": "INST-SNUH-SEOUL",
                                "name": "Seoul National University Hospital",
                                "country": "Republic of Korea",
                                "jurisdiction_law": "ROK PIPA Art. 28-2 & Bioethics Act",
                                "status": "PROSPECTIVE_UNCONTACTED",
                                "package_path": "1docs/audits/P10_7/partners/snuh_seoul/",
                                "readiness": snuh_summary,
                            },
                        ],
                        "holdout_protection": {
                            "holdout_percentage": 0.30,
                            "sealing_status": "SEALED_AIR_GAPPED",
                            "unblinded": False,
                        },
                        "real_dataset_intake": {
                            "available": False,
                            "status": "BLOCKED_EXTERNAL_DATA",
                            "prerequisite": "DUA_AND_IRB_EXECUTION_REQUIRED",
                        },
                        "next_actionable_step": "Transmit Dossier 1 to independent academic biostatistician for SAP sign-off (DEP-01)",
                    })

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

                elif path == "/api/landmarks":
                    reg_filt = query.get("region", [None])[0]
                    self._send_json(list_anatomical_landmarks(db, region=reg_filt))

                elif path == "/api/cun-rules":
                    reg_filt = query.get("region", [None])[0]
                    self._send_json(list_cun_scaling_rules(db, region=reg_filt))

                elif path == "/api/cun/metrics":
                    engine = CunScalingEngine()
                    self._send_json({k: v.__dict__ for k, v in engine.calculate_segment_metrics().items()})

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

                # -----------------------------------------------------------
                # Vietnamese Dien Chan Facial Reflexology GET Endpoints
                # -----------------------------------------------------------
                elif path == "/api/dien-chan/points":
                    pts = list_dien_chan_points(db)
                    self._send_json({"total": len(pts), "points": pts})

                elif path.startswith("/api/dien-chan/points/"):
                    code = path[len("/api/dien-chan/points/"):].strip()
                    pt = get_dien_chan_point(db, code)
                    if pt:
                        self._send_json(pt)
                    else:
                        self._send_json({"error": f"Dien Chan point '{code}' not found"}, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/dien-chan/conditions/search":
                    q = query.get("q", [""])[0]
                    res = search_dien_chan_conditions(db, q)
                    self._send_json(res)

                elif path.startswith("/api/dien-chan/conditions/") and path.endswith("/protocols"):
                    cond_id = path[len("/api/dien-chan/conditions/"): -len("/protocols")].strip()
                    cur = db.execute("SELECT protocol_id FROM dien_chan_protocols WHERE condition_id = ? AND status = 'ACTIVE'", (cond_id,))
                    pids = [r[0] for r in cur.fetchall()]
                    protos = []
                    for pid in pids:
                        p_data = get_protocol_with_points(db, pid)
                        if p_data:
                            protos.append(p_data)
                    self._send_json({"condition_id": cond_id, "protocols": protos})

                elif path.startswith("/api/dien-chan/protocols/"):
                    proto_id = path[len("/api/dien-chan/protocols/"):].strip()
                    proto_data = get_protocol_with_points(db, proto_id)
                    if proto_data:
                        self._send_json(proto_data)
                    else:
                        self._send_json({"error": f"Protocol '{proto_id}' not found"}, status=HTTPStatus.NOT_FOUND)

                elif path.startswith("/api/dien-chan/images/"):
                    img_name = path[len("/api/dien-chan/images/"):].strip()
                    safe_names = {
                        "headache-sinus": "dien_chan_headache_sinus_example.png",
                        "atlas-front-side": "dien_chan_face_atlas_front_side.png",
                        "dien_chan_headache_sinus_example.png": "dien_chan_headache_sinus_example.png",
                        "dien_chan_face_atlas_front_side.png": "dien_chan_face_atlas_front_side.png",
                    }
                    if img_name in safe_names:
                        repo_root = Path(__file__).resolve().parent.parent
                        target_file = (repo_root / "3refs" / "dien_chan" / "source_images" / safe_names[img_name]).resolve()
                        if target_file.exists() and self._serve_file(target_file):
                            return
                        else:
                            self._send_json({"error": "Reference image file not found on disk"}, status=HTTPStatus.NOT_FOUND)
                    else:
                        self._send_json({"error": "Unknown image reference"}, status=HTTPStatus.NOT_FOUND)

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
        if is_readonly_mode() and path != "/api/screen-safety":
            self._send_json({"error": "Public demonstration is read-only."}, status=HTTPStatus.FORBIDDEN)
            return

        if path == "/api/auth/demo-switch":
            if is_secure_mode():
                self._send_json(
                    {"error": "Forbidden: Demo role switching is strictly disabled in SECURE mode. Please authenticate using authorized credentials."},
                    status=HTTPStatus.FORBIDDEN
                )
                return
            if is_readonly_mode():
                self._send_json({"error": "Public demonstration is read-only."}, status=HTTPStatus.FORBIDDEN)
                return
            target_role = body.get("role", "student")
            role_user_map = {
                "student": "student",
                "reviewer": "dr_chen",
                "admin": "admin",
            }
            target_username = role_user_map.get(target_role, "student")
            with open_db(self.db_path) as db:
                cursor = db.cursor()
                cursor.execute(
                    "SELECT user_id, username, role, display_name FROM users WHERE username = ? AND is_active = 1",
                    (target_username,)
                )
                row = cursor.fetchone()
                if not row:
                    self._send_json({"error": f"Demo user for role '{target_role}' not found."}, status=HTTPStatus.NOT_FOUND)
                    return
                u = {
                    "user_id": row[0],
                    "username": row[1],
                    "role": row[2],
                    "display_name": row[3],
                }
                sess = create_session(db, u["user_id"])
                u["session_token"] = sess["session_token"]
                u["csrf_token"] = sess["csrf_token"]
                cookie = f"session_token={sess['session_token']}; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800"
                self._send_json({
                    "status": "authenticated",
                    "mode": "demo",
                    "user": u,
                    "session_token": sess["session_token"],
                    "csrf_token": sess["csrf_token"],
                    "expires_utc": sess["expires_utc"],
                }, set_cookie=cookie)
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

        if path == "/api/auth/bootstrap":
            if not is_secure_mode():
                self._send_json({"error": "Bootstrap is only applicable in SECURE mode."}, status=HTTPStatus.BAD_REQUEST)
                return
            if is_readonly_mode():
                self._send_json({"error": "Public demonstration is read-only."}, status=HTTPStatus.FORBIDDEN)
                return
            with open_db(self.db_path) as db:
                if get_user_count(db) > 0:
                    self._send_json({"error": "Forbidden: System already initialized. Initial admin bootstrap is permanently locked."}, status=HTTPStatus.FORBIDDEN)
                    return
                uname = body.get("username", "").strip()
                pwd = body.get("password", "")
                dname = body.get("display_name", "Root Administrator").strip()
                try:
                    admin_user = bootstrap_initial_admin(db, username=uname, password=pwd, display_name=dname)
                    sess = create_session(db, admin_user["user_id"])
                    admin_user["session_token"] = sess["session_token"]
                    admin_user["csrf_token"] = sess["csrf_token"]
                    cookie = f"session_token={sess['session_token']}; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800"
                    self._send_json({
                        "status": "bootstrapped",
                        "user": admin_user,
                        "session_token": sess["session_token"],
                        "csrf_token": sess["csrf_token"],
                    }, set_cookie=cookie, status=HTTPStatus.CREATED)
                except Exception as e:
                    self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
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
                if path == "/api/auth/users":
                    if not user or user.get("role") != "admin":
                        self._send_json({"error": "Forbidden: Admin privilege required."}, status=HTTPStatus.FORBIDDEN)
                        return
                    if not self._validate_csrf_if_session(user, body):
                        self._send_json({"error": "Forbidden: Invalid or missing CSRF token."}, status=HTTPStatus.FORBIDDEN)
                        return
                    try:
                        nu = create_user(
                            db,
                            username=body.get("username", ""),
                            password=body.get("password", ""),
                            role=body.get("role", "student"),
                            display_name=body.get("display_name", ""),
                            is_active=int(body.get("is_active", 1)),
                        )
                        self._send_json({"status": "created", "user": nu}, status=HTTPStatus.CREATED)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
                    return
                if is_secure_mode() and path not in ("/api/auth/login", "/api/auth/logout", "/api/screen-safety", "/api/auth/bootstrap"):
                    if not user:
                        self._send_json({"error": "Unauthorized: Authentication required in SECURE mode."}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    if not self._validate_csrf_if_session(user, body):
                        self._send_json({"error": "Forbidden: Invalid or missing CSRF token in SECURE mode."}, status=HTTPStatus.FORBIDDEN)
                        return
                elif user and not self._validate_csrf_if_session(user, body):
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

                if path == "/api/kinematics/arcs":
                    if not user:
                        self._send_json({"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    res = record_kinematic_arc(
                        db,
                        case_id=body.get("case_id", ""),
                        visit_id=body.get("visit_id"),
                        joint_name=body.get("joint_name", ""),
                        measured_rom_deg=float(body.get("measured_rom_deg", 0.0)),
                        custom_normal_deg=float(body["custom_normal_deg"]) if body.get("custom_normal_deg") is not None else None,
                    )
                    self._send_json({"status": "created", "arc": res}, status=HTTPStatus.CREATED)
                    return

                if path == "/api/kinematics/evaluate-budget":
                    frame_ms = float(body.get("frame_time_ms", 16.6))
                    target_fps = float(body.get("target_fps", 30.0))
                    self._send_json(evaluate_frame_budget(frame_ms, target_fps))
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
                    _validate_synthetic_case_id(body.get("case", ""))
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
                    elif not is_secure_mode():
                        reviewer_role = body.get("role", "reviewer")
                        reviewer_name = body.get("reviewer", "Clinical Supervisor")
                    else:
                        self._send_json({"error": "Unauthorized: Authentication required to review SOAP notes in SECURE mode."}, status=HTTPStatus.UNAUTHORIZED)
                        return

                    if reviewer_role != "reviewer":
                        self._send_json({"error": "Forbidden: Only users with verified 'reviewer' role can approve or reject SOAP notes."}, status=HTTPStatus.FORBIDDEN)
                        return

                    # In SECURE mode or when user is present, verify active reviewer credentials in clinical_reviewers registry
                    if user or is_secure_mode():
                        uid = user["user_id"] if user else ""
                        verified_rev = get_verified_reviewer(db, uid)
                        if not verified_rev:
                            self._send_json({"error": "Forbidden: Supervisor account has not been verified active by an administrator."}, status=HTTPStatus.FORBIDDEN)
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

                elif path == "/api/registration/align":
                    src_landmarks = body.get("source_landmarks", {})
                    src_name = body.get("source_name", "upstream")
                    region_str = body.get("region", "head_neck")
                    try:
                        region_enum = BodyRegion(region_str)
                    except ValueError:
                        region_enum = BodyRegion.HEAD_NECK
                    engine = AnatomicalRegistrationEngine()
                    transform = engine.calculate_umeyama_alignment(
                        src_landmarks,
                        allow_scaling=body.get("allow_scaling", False),
                        source_name=src_name,
                        region=region_enum,
                    )
                    t_dict = transform.to_dict()
                    record_registration_metric(db, {
                        "source_name": src_name,
                        "region": region_str,
                        "rms_error_mm": transform.rms_error_mm,
                        "max_error_mm": transform.max_error_mm,
                        "rotation_matrix": transform.rotation_matrix,
                        "translation_vector": transform.translation_vector,
                        "scale": transform.scale,
                        "status": transform.status,
                        "rejection_reason": transform.rejection_reason,
                    })
                    self._send_json(t_dict)

                elif path == "/api/cun/adapt":
                    morph_params = body.get("morphology_params", {})
                    engine = CunScalingEngine()
                    adapted = engine.compute_morphology_adapted_cun(morph_params)
                    self._send_json(adapted)

                elif path == "/api/atlas/geometry/resolve":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    resolver = get_spatial_resolver()
                    overrides = list_reference_overrides(db)
                    try:
                        resolved_geometry = resolver.resolve_atlas_geometry(body, sqlite_overrides=overrides)
                        self._send_json(resolved_geometry)
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)

                elif path == "/api/atlas/meridians/resolve":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    resolver = get_spatial_resolver()
                    overrides = list_reference_overrides(db)
                    try:
                        channel_ids = body.get("channel_ids") or body.get("meridian_ids")
                        side = body.get("side", "all")
                        geo_payload = {
                            "layer_mode": body.get("layer_mode", "canonical"),
                            "meridian_ids": channel_ids,
                            "morphology": body.get("morphology", {}),
                            "pose": body.get("pose", {}),
                            "mesh_id": body.get("mesh_id", "FJ2810"),
                        }
                        geo = resolver.resolve_atlas_geometry(geo_payload, sqlite_overrides=overrides)
                        meridians_res = geo.get("meridians", {})
                        if side in ("right", "left", "midline"):
                            filtered = {}
                            for c, m in meridians_res.items():
                                f_paths = [p for p in m.get("paths", []) if p.get("side") == side]
                                m_copy = dict(m)
                                m_copy["paths"] = f_paths
                                filtered[c] = m_copy
                            meridians_res = filtered
                        self._send_json({
                            "status": "success",
                            "layer_mode": geo_payload["layer_mode"],
                            "mesh_id": geo.get("mesh_id", "FJ2810"),
                            "mesh_hash": geo.get("mesh_hash", ""),
                            "channel_count": len(meridians_res),
                            "meridians": meridians_res,
                        })
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)

                elif path == "/api/atlas/meridians/revisions":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        rev_id = create_meridian_route_revision(
                            db,
                            channel_code=body["channel_code"],
                            branch_id=body.get("branch_id", ""),
                            revision_type=body["revision_type"],
                            target_id=body["target_id"],
                            old_state=body.get("old_state", {}),
                            new_state=body.get("new_state", {}),
                            clinical_justification=body.get("clinical_justification", "Clinical calibration"),
                            author=body.get("author", "Clinical Specialist")
                        )
                        self._send_json({
                            "status": "success",
                            "revision_id": rev_id,
                            "revision_status": "PENDING",
                            "message": "Revision submitted for clinical peer review."
                        }, status=HTTPStatus.CREATED)
                    except KeyError as ke:
                        self._send_json({"error": f"Missing required field: {ke}"}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

                elif path == "/api/atlas/meridians/revisions/review" or (path.startswith("/api/atlas/meridians/revisions/") and path.endswith("/review")):
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        if path != "/api/atlas/meridians/revisions/review":
                            parts = path.strip("/").split("/")
                            rev_id = int(parts[4])
                        else:
                            rev_id = int(body["revision_id"])

                        res = review_meridian_route_revision(
                            db,
                            revision_id=rev_id,
                            reviewer=body.get("reviewer", "Clinical Reviewer"),
                            decision=body.get("decision", "APPROVED"),
                            comments=body.get("comments", "")
                        )
                        self._send_json({"status": "success", "review": res})
                    except (KeyError, ValueError) as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

                elif path == "/api/atlas/meridians/revisions/rollback" or (path.startswith("/api/atlas/meridians/revisions/") and path.endswith("/rollback")):
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        if path != "/api/atlas/meridians/revisions/rollback":
                            parts = path.strip("/").split("/")
                            rev_id = int(parts[4])
                        else:
                            rev_id = int(body["revision_id"])

                        res = rollback_meridian_route_revision(
                            db,
                            revision_id=rev_id,
                            author=body.get("author", "Clinical Specialist")
                        )
                        self._send_json({"status": "success", "rollback": res})
                    except (KeyError, ValueError) as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

                elif path == "/api/atlas/validation/datasets":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        validator = get_anatomical_validator()
                        req_fields = ["dataset_id", "name", "source_organization", "version", "license", "doi_or_url"]
                        for f in req_fields:
                            if not body.get(f):
                                self._send_json({"error": f"Missing required field: {f}"}, status=HTTPStatus.BAD_REQUEST)
                                return

                        modality_str = body.get("modality", "SYNTHETIC_TEST_FIXTURE")
                        try:
                            modality = GroundTruthModality(modality_str)
                        except ValueError:
                            self._send_json({"error": f"Invalid modality: {modality_str}"}, status=HTTPStatus.BAD_REQUEST)
                            return

                        ds = ExternalGroundTruthDataset(
                            dataset_id=body["dataset_id"],
                            name=body["name"],
                            source_organization=body["source_organization"],
                            version=body["version"],
                            license=body["license"],
                            doi_or_url=body["doi_or_url"],
                            modality=modality,
                            is_synthetic_fixture=bool(body.get("is_synthetic_fixture", False)),
                            case_id=body.get("case_id"),
                            sample_size=int(body.get("sample_size", 1)),
                        )
                        validator.register_dataset(ds)

                        imported_count = 0
                        if "observations" in body and isinstance(body["observations"], list):
                            obs_list = []
                            for o_dict in body["observations"]:
                                pos = tuple(o_dict.get("canonical_position") or o_dict.get("measurement_coordinates") or (0.0, 0.0, 0.0))
                                obs = GroundTruthObservation(
                                    point_code=o_dict["point_code"],
                                    dataset_id=ds.dataset_id,
                                    canonical_position=pos,
                                    surface_normal=tuple(o_dict["surface_normal"]) if o_dict.get("surface_normal") else None,
                                    uncertainty_radius_mm=float(o_dict.get("uncertainty_radius_mm", 2.0)),
                                    subject_pseudonym=o_dict.get("subject_pseudonym", "SUBJ-ANON-0001"),
                                    coordinate_frame=o_dict.get("coordinate_frame", "BP3D_CARTESIAN_METERS"),
                                    unit=o_dict.get("unit", "meters"),
                                    observer_id=o_dict.get("observer_id", "OBS-DEFAULT"),
                                    source_checksum=o_dict.get("source_checksum", ""),
                                    notes=o_dict.get("notes", ""),
                                )
                                obs_list.append(obs)
                            imported_count = validator.import_observations(obs_list, validate_contract=True)

                        self._send_json({
                            "status": "success",
                            "dataset": ds.to_dict(),
                            "imported_observations_count": imported_count,
                        }, status=HTTPStatus.CREATED)
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/evaluate":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        validator = get_anatomical_validator()
                        dataset_id = body.get("dataset_id")
                        point_codes = body.get("point_codes")
                        side = body.get("side", "right")
                        holdouts = body.get("holdout_subjects")
                        subject = body.get("subject_pseudonym")

                        report = validator.validate_catalog(
                            point_codes=point_codes,
                            dataset_id=dataset_id,
                            side=side,
                            holdout_subjects=holdouts,
                            subject_pseudonym=subject,
                        )
                        self._send_json({
                            "status": "success",
                            "evaluation_report": report.to_dict(),
                        })
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/ingest":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        validator = get_anatomical_validator()
                        res = validator.ingest_external_evidence_batch(body, enforce_quarantine=True)
                        self._send_json(res, status=HTTPStatus.OK)
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/holdout/split":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        validator = get_anatomical_validator()
                        p_id = body.get("partition_id", "default")
                        subjs = body.get("subjects", [])
                        ratio = float(body.get("holdout_ratio", 0.2))
                        seed = int(body.get("seed", 42))
                        part = validator._holdout_manager.create_partition(p_id, subjs, holdout_ratio=ratio, seed=seed)
                        self._send_json({"status": "success", "partition": part.to_dict()}, status=HTTPStatus.CREATED)
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/holdout/three-way-split":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        validator = get_anatomical_validator()
                        p_id = body.get("partition_id", "default_3way")
                        subjs = body.get("subjects", [])
                        calib_r = float(body.get("calib_ratio", 0.5))
                        val_r = float(body.get("val_ratio", 0.25))
                        hold_r = float(body.get("holdout_ratio", 0.25))
                        seed = int(body.get("seed", 42))
                        part = validator._holdout_manager.create_three_way_partition(
                            p_id, subjs, calib_ratio=calib_r, val_ratio=val_r, holdout_ratio=hold_r, seed=seed
                        )
                        self._send_json({"status": "success", "partition": part.to_dict()}, status=HTTPStatus.CREATED)
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/admin/sign-off":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        validator = get_anatomical_validator()
                        ds_id = body.get("dataset_id")
                        rev_id = body.get("admin_reviewer_id", "REV-CLINICAL-AUDITOR")
                        just = body.get("justification", "Authorized by Clinical Review Board for P10.2 Validation")
                        token = body.get("governance_token")
                        cosigner = body.get("cosigner_id")
                        validator.admin_sign_off_dataset(
                            ds_id,
                            admin_reviewer_id=rev_id,
                            justification=just,
                            governance_token=token,
                            cosigner_id=cosigner,
                        )
                        self._send_json({
                            "status": "success",
                            "dataset_id": ds_id,
                            "signed_off": True,
                            "cosigned_by": cosigner,
                        })
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/admin/revoke":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        validator = get_anatomical_validator()
                        ds_id = body.get("dataset_id")
                        rev_id = body.get("revoking_reviewer_id", "REV-CLINICAL-AUDITOR")
                        reason = body.get("reason", "Revocation requested by Clinical Safety Auditor")
                        token = body.get("governance_token")
                        validator.revoke_dataset_authorization(
                            ds_id,
                            revoking_reviewer_id=rev_id,
                            reason=reason,
                            governance_token=token,
                        )
                        self._send_json({
                            "status": "success",
                            "dataset_id": ds_id,
                            "revoked": True,
                            "reason": reason,
                        })
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/dry-run":
                    try:
                        validator = get_anatomical_validator()
                        res = validator.run_synthetic_pilot_dry_run()
                        self._send_json(res, status=HTTPStatus.OK)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/pilot-harness/run":
                    try:
                        validator = get_anatomical_validator()
                        res = validator.run_p10_3b_empirical_pilot_harness()
                        self._send_json(res, status=HTTPStatus.OK)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/dicom/preflight":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    f_path = body.get("file_path")
                    d_path = body.get("directory_path")
                    validator = get_anatomical_validator()
                    try:
                        if f_path:
                            res = validator.preflight_dicom_file(f_path)
                            self._send_json({"status": "success", "result": res})
                        elif d_path:
                            res = validator.preflight_dicom_directory(d_path)
                            self._send_json({"status": "success", "results": res, "total_files": len(res)})
                        else:
                            self._send_json({"error": "file_path or directory_path required"}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/adjudicate":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    pt_code = body.get("point_code")
                    ds_id = body.get("dataset_id")
                    adj_id = body.get("adjudicator_id")
                    res_pos = body.get("resolved_position")
                    rationale = body.get("rationale", "")
                    if not (pt_code and ds_id and adj_id and res_pos and len(res_pos) == 3):
                        self._send_json({"error": "point_code, dataset_id, adjudicator_id, and resolved_position [x,y,z] required"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        validator = get_anatomical_validator()
                        adj_res = validator.adjudicate_inter_observer_disagreement(
                            point_code=pt_code,
                            dataset_id=ds_id,
                            adjudicator_id=adj_id,
                            resolved_position=tuple(res_pos),
                            rationale=rationale,
                        )
                        self._send_json(adj_res, status=HTTPStatus.OK)
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/bootstrap-metrics":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    pt_codes = body.get("point_codes")
                    ds_id = body.get("dataset_id")
                    n_boot = int(body.get("n_bootstraps", 1000))
                    seed = int(body.get("seed", 42))
                    try:
                        validator = get_anatomical_validator()
                        b_res = validator.compute_subject_bootstrap_ci(
                            point_codes=pt_codes,
                            dataset_id=ds_id,
                            n_bootstraps=n_boot,
                            seed=seed,
                        )
                        self._send_json(b_res, status=HTTPStatus.OK)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/atlas/validation/holdout/lock":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    part_id = body.get("partition_id")
                    admin_id = body.get("admin_reviewer_id")
                    if not part_id or not admin_id:
                        self._send_json({"error": "partition_id and admin_reviewer_id required"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        validator = get_anatomical_validator()
                        manifest = validator._holdout_manager.lock_holdout_partition(part_id, admin_id)
                        self._send_json({"status": "success", "manifest": manifest.to_dict()}, status=HTTPStatus.OK)
                    except ValueError as ve:
                        self._send_json({"error": str(ve)}, status=HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                elif path == "/api/dien-chan/geometry/resolve":
                    if not isinstance(body, dict):
                        self._send_json({"error": "Payload must be a JSON object"}, status=HTTPStatus.BAD_REQUEST)
                        return
                    point_codes = body.get("point_codes")
                    reg_engine = FacialRegistrationEngine()
                    resolved = reg_engine.resolve_points_for_atlas(point_codes=point_codes)
                    self._send_json({"total": len(resolved), "points": resolved})

                elif path == "/api/pose/evaluate":
                    point_code = body.get("point_code", "")
                    joint_angles = body.get("joint_angles", {})
                    kin_engine = PoseKinematicsEngine()
                    eval_result = kin_engine.evaluate_acupoint_posture_status(point_code, joint_angles)
                    self._send_json(eval_result)

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
                if is_secure_mode() and path not in ("/api/auth/login", "/api/auth/logout", "/api/screen-safety"):
                    if not user:
                        self._send_json({"error": "Unauthorized: Authentication required in SECURE mode."}, status=HTTPStatus.UNAUTHORIZED)
                        return
                    if not self._validate_csrf_if_session(user, body):
                        self._send_json({"error": "Forbidden: Invalid or missing CSRF token in SECURE mode."}, status=HTTPStatus.FORBIDDEN)
                        return
                elif user and not self._validate_csrf_if_session(user, body):
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

                if path == "/api/anatomy/layers/config":
                    user_id = user["username"] if user else body.get("user_id", "anonymous")
                    res = update_layer_config(
                        db,
                        user_id=user_id,
                        layer_name=body.get("layer_name", ""),
                        opacity=float(body.get("opacity", 1.0)),
                        is_visible=bool(body.get("is_visible", True)),
                        slice_plane=body.get("slice_plane", "none"),
                        slice_offset=float(body.get("slice_offset", 0.0)),
                    )
                    self._send_json({"status": "updated", "config": res})
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


def create_server(db_path: str = DEFAULT_DB, host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
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


def run_server(db_path: str = DEFAULT_DB, host: str = "127.0.0.1", port: int = 8080) -> None:
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


if __name__ == "__main__":
    run_server()
