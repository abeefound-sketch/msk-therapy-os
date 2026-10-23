"""M2.5 Custom Acupoint Atlas & Interactive Point Authoring Repository and Services.

Provides durable SQLite persistence, geometric validation, versioned audit revisions,
SHA-256 dataset integrity hashing, and canonical reference protection.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

MAINTENANCE_LOCK = threading.RLock()
IS_MAINTENANCE_ACTIVE = False

VALID_MESH_ID = "FJ2810"
VALID_MESH_HASH = "FJ2810_V4.0_CCBYSA"

CANONICAL_MODEL_ID = "BodyParts3D 4.0 (FJ2810)"
CANONICAL_MESH_ID = "FJ2810"
CANONICAL_MESH_HASH = "FJ2810_V4.0_CCBYSA"
CANONICAL_UNITS = "meters"
CANONICAL_COORDINATE_SYSTEM = "Right-Handed Y-Up"

CANONICAL_REFERENCE_CHECKSUMS = {
    "acupuncture_3d.json": "47df1332187f7de3f3e08aaf3a4a42a761a312e4fff8c3a728e254d99e0520df"
}

VALID_GOVERNANCE_STATUSES = (
    "VERIFIED_ANATOMICAL_ANCHOR",
    "SURFACE_REGISTERED_FJ2810",
    "GEOMETRY_VERIFIED",
    "ANATOMY_REVIEWED",
    "UNCERTAIN_POSTURE_OFFSET",
    "UNVERIFIED",
)

ALLOWED_CLINICAL_CREDENTIALS = {
    "MD", "DO", "LAC", "PT", "DPT", "DC", "PHD", "MBBS", "FACP", "ND",
    "L.AC.", "D.P.T.", "M.D.", "D.O."
}

RECOGNIZED_STANDARDS = {
    "WHO-2008", "WHO WPRO 2008", "WHO 2008", "GB/T 12346-2006", "GB/T 12346-2021",
    "BODYPARTS3D 4.0", "FMA 7163", "BODYPARTS3D 4.0 / FMA 7163"
}

BODY_ENVELOPE = {
    "x_min": -0.35, "x_max": 0.35,
    "y_min": -0.05, "y_max": 1.76,
    "z_min": -0.25, "z_max": 0.25
}

STANDARD_LIBRARIES = [
    {
        "library_id": "lib_who_classical",
        "name": "WHO Classical Meridians (362 points)",
        "namespace": "WHO_CLASSICAL",
        "description": "Standard 362 classical acupuncture points across 14 channels (WHO WPRO 2008 & GB/T 12346-2006).",
        "color": "#0284c7",
        "is_readonly": 1
    },
    {
        "library_id": "lib_extra",
        "name": "Extra Acupuncture Points (HN/CA/UE/LE)",
        "namespace": "EXTRA_POINTS",
        "description": "Classical extra-meridian acupoints (Yintang, Taiyang, Huatuojiaji, etc.).",
        "color": "#8b5cf6",
        "is_readonly": 1
    },
    {
        "library_id": "lib_thai_sen",
        "name": "Thai Sen Sib Energy Landmarks",
        "namespace": "THAI_SEN_SIB",
        "description": "Wat Po / Thai MoPH traditional energy line reference points.",
        "color": "#f59e0b",
        "is_readonly": 1
    },
    {
        "library_id": "lib_dien_chan",
        "name": "Vietnamese Dien Chan Reflex Points",
        "namespace": "DIEN_CHAN",
        "description": "Prof. Bui Quoc Chau (1980) facial reflexology diagnostic & therapeutic landmarks.",
        "color": "#ec4899",
        "is_readonly": 1
    },
    {
        "library_id": "lib_msk_landmarks",
        "name": "Musculoskeletal Palpation Landmarks",
        "namespace": "MSK_LANDMARK",
        "description": "BodyParts3D & FMA anatomical bony palpation landmarks and myofascial trigger points.",
        "color": "#10b981",
        "is_readonly": 1
    },
    {
        "library_id": "lib_custom_user",
        "name": "User-Created Custom Points",
        "namespace": "USER_CUSTOM",
        "description": "Locally authored custom acupuncture points, reflex loci, and clinical observations.",
        "color": "#06b6d4",
        "is_readonly": 0
    }
]


def init_points_tables(db: sqlite3.Connection) -> None:
    """Create point libraries, custom points, revisions, and reference overrides tables."""
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS evidence_catalog (
            evidence_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            organization TEXT NOT NULL,
            year INTEGER NOT NULL,
            license TEXT NOT NULL,
            tier INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 4),
            claim_scope TEXT NOT NULL,
            reviewed_on TEXT NOT NULL,
            reviewer TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS point_libraries (
            library_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            namespace TEXT NOT NULL CHECK (namespace IN ('WHO_CLASSICAL', 'EXTRA_POINTS', 'THAI_SEN_SIB', 'DIEN_CHAN', 'MSK_LANDMARK', 'USER_CUSTOM')),
            description TEXT,
            color TEXT DEFAULT '#38bdf8',
            is_readonly INTEGER NOT NULL DEFAULT 0,
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS custom_points (
            point_id TEXT PRIMARY KEY,
            library_id TEXT NOT NULL REFERENCES point_libraries(library_id),
            code TEXT NOT NULL,
            name_en TEXT NOT NULL,
            name_zh TEXT,
            name_vi TEXT,
            pinyin TEXT,
            aliases_json TEXT DEFAULT '[]',
            system_classification TEXT NOT NULL DEFAULT 'user_custom',
            region TEXT NOT NULL DEFAULT 'neck',
            laterality TEXT NOT NULL DEFAULT 'bilateral' CHECK (laterality IN ('bilateral', 'left', 'right', 'midline')),
            pos_x REAL NOT NULL,
            pos_y REAL NOT NULL,
            pos_z REAL NOT NULL,
            norm_x REAL DEFAULT 0.0,
            norm_y REAL DEFAULT 0.0,
            norm_z REAL DEFAULT 1.0,
            mesh_id TEXT NOT NULL DEFAULT 'FJ2810',
            mesh_hash TEXT DEFAULT 'FJ2810_V4.0_CCBYSA',
            face_index INTEGER,
            barycentric_json TEXT DEFAULT '[]',
            registration_distance REAL DEFAULT 0.0,
            registration_status TEXT NOT NULL DEFAULT 'SURFACE_REGISTERED_FJ2810' CHECK (registration_status IN ('VERIFIED_ANATOMICAL_ANCHOR', 'SURFACE_REGISTERED_FJ2810', 'GEOMETRY_VERIFIED', 'ANATOMY_REVIEWED', 'UNCERTAIN_POSTURE_OFFSET', 'UNVERIFIED')),
            review_status TEXT NOT NULL DEFAULT 'PENDING_EXPERT_REVIEW' CHECK (review_status IN ('OFFICIAL_STANDARD', 'EXPERT_VERIFIED', 'PROVISIONAL', 'PENDING_EXPERT_REVIEW')),
            indications_json TEXT DEFAULT '[]',
            cautions_json TEXT DEFAULT '[]',
            tuina_method TEXT,
            notes TEXT,
            author TEXT DEFAULT 'Clinical Educator',
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            is_deleted INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS point_revisions (
            revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
            point_id TEXT NOT NULL,
            revision_number INTEGER NOT NULL,
            change_type TEXT NOT NULL CHECK (change_type IN ('CREATE', 'UPDATE_COORDS', 'UPDATE_METADATA', 'NUDGE', 'SNAP_SURFACE', 'RELOCATE', 'OVERRIDE_REFERENCE', 'RESTORE_BASELINE', 'DELETE', 'RESTORE')),
            previous_state_json TEXT,
            new_state_json TEXT NOT NULL,
            author TEXT NOT NULL,
            notes TEXT,
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS reference_point_overrides (
            reference_code TEXT PRIMARY KEY,
            pos_x REAL NOT NULL,
            pos_y REAL NOT NULL,
            pos_z REAL NOT NULL,
            norm_x REAL,
            norm_y REAL,
            norm_z REAL,
            face_index INTEGER,
            registration_status TEXT DEFAULT 'SURFACE_REGISTERED_FJ2810',
            review_status TEXT DEFAULT 'EXPERT_VERIFIED',
            notes TEXT,
            author TEXT DEFAULT 'Clinical Educator',
            created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );
        """
    )
    # Seed standard libraries
    for lib in STANDARD_LIBRARIES:
        db.execute(
            """INSERT OR IGNORE INTO point_libraries (library_id, name, namespace, description, color, is_readonly)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                lib["library_id"],
                lib["name"],
                lib["namespace"],
                lib["description"],
                lib["color"],
                lib["is_readonly"]
            )
        )

    # Seed evidence catalog with default evidence records and recognized standards
    try:
        from msk_therapy_os.evidence import DEFAULT_EVIDENCE_CATALOG
        for item in DEFAULT_EVIDENCE_CATALOG:
            db.execute(
                """INSERT OR IGNORE INTO evidence_catalog
                   (evidence_id, title, url, organization, year, license, tier, claim_scope, reviewed_on, reviewer)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item.evidence_id, item.title, item.url, item.organization, item.year, item.license, item.tier, item.claim_scope, item.reviewed_on, item.reviewer)
            )
    except Exception:
        pass

    standards_records = [
        ("WHO-2008", "WHO Standard Acupuncture Point Locations in the Western Pacific Region", "https://iris.who.int/handle/10665/207439", "World Health Organization", 2008, "Public domain / WHO standard", 1, "Standard 361 classical points", "2026-10-19", "WHO Expert Committee"),
        ("GB/T 12346-2006", "Nomenclature and location of acupuncture points", "http://openstd.samr.gov.cn/", "Standardization Administration of China", 2006, "National Standard of PRC", 1, "Standard 362 points with Yintang", "2026-10-19", "SAC Expert Committee"),
        ("GB/T 12346-2021", "Nomenclature and location of meridian points", "http://openstd.samr.gov.cn/", "Standardization Administration of China", 2021, "National Standard of PRC", 1, "Updated 362 meridian points standard", "2026-10-19", "SAC Expert Committee"),
        ("BODYPARTS3D 4.0", "BodyParts3D Anatomical Concepts Database Release 4.0", "https://lifesciencedb.jp/bp3d/", "DBCLS Japan", 2022, "CC BY-SA 2.1 JP", 2, "Anatomical surface meshes and FMA ontology", "2026-10-19", "DBCLS Consortium"),
    ]
    for s in standards_records:
        db.execute(
            """INSERT OR IGNORE INTO evidence_catalog
               (evidence_id, title, url, organization, year, license, tier, claim_scope, reviewed_on, reviewer)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            s
        )

    migrate_governance_schema(db)
    try:
        from msk_therapy_os.auth import init_auth_tables, seed_default_users
        init_auth_tables(db)
        seed_default_users(db)
    except Exception:
        pass
    db.commit()


def validate_coordinates(x: float, y: float, z: float) -> None:
    """Validate that coordinates are finite numbers and fall within human anatomical envelope."""
    if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
        raise ValueError(f"Invalid non-finite coordinates: X={x}, Y={y}, Z={z}")
    if not (BODY_ENVELOPE["x_min"] <= x <= BODY_ENVELOPE["x_max"]):
        raise ValueError(f"Coordinate X={x:.4f}m outside anatomical envelope [{BODY_ENVELOPE['x_min']}, {BODY_ENVELOPE['x_max']}]")
    if not (BODY_ENVELOPE["y_min"] <= y <= BODY_ENVELOPE["y_max"]):
        raise ValueError(f"Coordinate Y={y:.4f}m outside anatomical envelope [{BODY_ENVELOPE['y_min']}, {BODY_ENVELOPE['y_max']}]")
    if not (BODY_ENVELOPE["z_min"] <= z <= BODY_ENVELOPE["z_max"]):
        raise ValueError(f"Coordinate Z={z:.4f}m outside anatomical envelope [{BODY_ENVELOPE['z_min']}, {BODY_ENVELOPE['z_max']}]")


def validate_mesh_identity(mesh_id: str, mesh_hash: Optional[str]) -> None:
    """Ensure points strictly attach to conforming BodyParts3D skin mesh."""
    if mesh_id and mesh_id != VALID_MESH_ID and mesh_id != "FJ2813":
        raise ValueError(f"Unsupported mesh ID '{mesh_id}'. Surface points must anchor to BodyParts3D skin {VALID_MESH_ID}.")
    if mesh_hash and mesh_hash != VALID_MESH_HASH:
        raise ValueError(f"Invalid mesh hash '{mesh_hash}'. Expected verified hash '{VALID_MESH_HASH}'.")


def compute_sha256_digest(payload: Any) -> str:
    """Compute deterministic SHA-256 digest of JSON serializable data."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Library Repository Methods
# -----------------------------------------------------------------------------

def list_libraries(db: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Return all registered point libraries with counts of active points."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT l.library_id, l.name, l.namespace, l.description, l.color, l.is_readonly, l.created_utc,
               COUNT(p.point_id) as points_count
        FROM point_libraries l
        LEFT JOIN custom_points p ON l.library_id = p.library_id AND p.is_deleted = 0
        GROUP BY l.library_id
        ORDER BY l.is_readonly DESC, l.name ASC
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "library_id": r[0],
            "name": r[1],
            "namespace": r[2],
            "description": r[3],
            "color": r[4],
            "is_readonly": bool(r[5]),
            "created_utc": r[6],
            "points_count": r[7]
        }
        for r in rows
    ]


def create_library(db: sqlite3.Connection, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new custom user point library."""
    lib_id = data.get("library_id") or f"lib_user_{int(time.time())}"
    name = data.get("name")
    if not name or not name.strip():
        raise ValueError("Library name cannot be empty.")
    namespace = data.get("namespace", "USER_CUSTOM")
    if namespace not in ("USER_CUSTOM", "EXTRA_POINTS", "THAI_SEN_SIB", "DIEN_CHAN", "MSK_LANDMARK"):
        raise ValueError(f"Invalid namespace '{namespace}'.")
    desc = data.get("description", "")
    color = data.get("color", "#06b6d4")

    db.execute(
        """INSERT INTO point_libraries (library_id, name, namespace, description, color, is_readonly)
           VALUES (?, ?, ?, ?, ?, 0)""",
        (lib_id, name.strip(), namespace, desc, color)
    )
    db.commit()
    return {
        "library_id": lib_id,
        "name": name.strip(),
        "namespace": namespace,
        "description": desc,
        "color": color,
        "is_readonly": False
    }


# -----------------------------------------------------------------------------
# Custom Point CRUD & Revision Logging
# -----------------------------------------------------------------------------

def list_custom_points(
    db: sqlite3.Connection,
    library_id: Optional[str] = None,
    region: Optional[str] = None,
    include_deleted: bool = False
) -> List[Dict[str, Any]]:
    """List custom points with optional library and region filtering."""
    query = """
        SELECT point_id, library_id, code, name_en, name_zh, name_vi, pinyin,
               aliases_json, system_classification, region, laterality,
               pos_x, pos_y, pos_z, norm_x, norm_y, norm_z,
               mesh_id, mesh_hash, face_index, barycentric_json, registration_distance,
               registration_status, review_status, indications_json, cautions_json,
               tuina_method, notes, author, created_utc, updated_utc, is_deleted,
               evidence_id, reviewer, verification_method, uncertainty_radius_mm
        FROM custom_points
        WHERE 1=1
    """
    params: List[Any] = []
    if not include_deleted:
        query += " AND is_deleted = 0"
    if library_id:
        query += " AND library_id = ?"
        params.append(library_id)
    if region and region != "all":
        query += " AND region = ?"
        params.append(region)
    query += " ORDER BY code ASC"

    cursor = db.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()

    points = []
    for r in rows:
        points.append({
            "point_id": r[0],
            "library_id": r[1],
            "code": r[2],
            "name_en": r[3],
            "name_zh": r[4] or "",
            "name_vi": r[5] or "",
            "pinyin": r[6] or "",
            "aliases": json.loads(r[7] or "[]"),
            "system_classification": r[8],
            "region": r[9],
            "laterality": r[10],
            "position": [r[11], r[12], r[13]],
            "normal": [r[14], r[15], r[16]],
            "mesh_id": r[17],
            "mesh_hash": r[18],
            "face_index": r[19],
            "barycentric": json.loads(r[20] or "[]"),
            "registration_distance": r[21],
            "registration_status": r[22],
            "review_status": r[23],
            "indications": json.loads(r[24] or "[]"),
            "cautions": json.loads(r[25] or "[]"),
            "tuina_method": r[26] or "",
            "notes": r[27] or "",
            "author": r[28],
            "created_utc": r[29],
            "updated_utc": r[30],
            "is_deleted": bool(r[31]),
            "evidence_id": r[32] if len(r) > 32 else None,
            "reviewer": r[33] if len(r) > 33 else None,
            "verification_method": r[34] if len(r) > 34 else "SURFACE_RAYCAST_INTERSECTION",
            "uncertainty_radius_mm": r[35] if len(r) > 35 else 0.0
        })
    return points


def get_point(db: sqlite3.Connection, point_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single point by ID (or code)."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT point_id, library_id, code, name_en, name_zh, name_vi, pinyin,
               aliases_json, system_classification, region, laterality,
               pos_x, pos_y, pos_z, norm_x, norm_y, norm_z,
               mesh_id, mesh_hash, face_index, barycentric_json, registration_distance,
               registration_status, review_status, indications_json, cautions_json,
               tuina_method, notes, author, created_utc, updated_utc, is_deleted,
               evidence_id, reviewer, verification_method, uncertainty_radius_mm
        FROM custom_points
        WHERE point_id = ? OR code = ?
        """,
        (point_id, point_id)
    )
    r = cursor.fetchone()
    if not r:
        return None
    return {
        "point_id": r[0],
        "library_id": r[1],
        "code": r[2],
        "name_en": r[3],
        "name_zh": r[4] or "",
        "name_vi": r[5] or "",
        "pinyin": r[6] or "",
        "aliases": json.loads(r[7] or "[]"),
        "system_classification": r[8],
        "region": r[9],
        "laterality": r[10],
        "position": [r[11], r[12], r[13]],
        "normal": [r[14], r[15], r[16]],
        "mesh_id": r[17],
        "mesh_hash": r[18],
        "face_index": r[19],
        "barycentric": json.loads(r[20] or "[]"),
        "registration_distance": r[21],
        "registration_status": r[22],
        "review_status": r[23],
        "indications": json.loads(r[24] or "[]"),
        "cautions": json.loads(r[25] or "[]"),
        "tuina_method": r[26] or "",
        "notes": r[27] or "",
        "author": r[28],
        "created_utc": r[29],
        "updated_utc": r[30],
        "is_deleted": bool(r[31]),
        "evidence_id": r[32] if len(r) > 32 else None,
        "reviewer": r[33] if len(r) > 33 else None,
        "verification_method": r[34] if len(r) > 34 else "SURFACE_RAYCAST_INTERSECTION",
        "uncertainty_radius_mm": r[35] if len(r) > 35 else 0.0
    }


def create_point(db: sqlite3.Connection, data: Dict[str, Any], author: str = "Clinical Educator") -> Dict[str, Any]:
    """Create a new point with geometric validation and audit logging."""
    code = (data.get("code") or "").strip().upper()
    if not code:
        raise ValueError("Point code is required.")
    name_en = (data.get("name_en") or "").strip()
    if not name_en:
        raise ValueError("Point English display name is required.")

    # Validate coordinates
    pos = data.get("position", [0.0, 0.0, 0.0])
    if not isinstance(pos, (list, tuple)) or len(pos) != 3:
        raise ValueError("Point position must be a 3-element list [X, Y, Z].")
    validate_coordinates(pos[0], pos[1], pos[2])

    # Validate mesh
    mesh_id = data.get("mesh_id", VALID_MESH_ID)
    mesh_hash = data.get("mesh_hash", VALID_MESH_HASH)
    validate_mesh_identity(mesh_id, mesh_hash)

    library_id = data.get("library_id", "lib_custom_user")
    # Verify library exists and is not readonly
    cursor = db.cursor()
    cursor.execute("SELECT is_readonly FROM point_libraries WHERE library_id = ?", (library_id,))
    lib_row = cursor.fetchone()
    if not lib_row:
        raise ValueError(f"Library '{library_id}' does not exist.")
    if lib_row[0] == 1:
        raise ValueError(f"Cannot add custom points to read-only canonical library '{library_id}'.")

    # Check duplicate code within active library
    cursor.execute("SELECT point_id FROM custom_points WHERE library_id = ? AND code = ? AND is_deleted = 0", (library_id, code))
    if cursor.fetchone():
        raise ValueError(f"Point code '{code}' already exists in library '{library_id}'.")

    point_id = data.get("point_id") or f"PT-{code}-{int(time.time())}"
    norm = data.get("normal", [0.0, 0.0, 1.0])
    system = data.get("system_classification", "user_custom")
    region = data.get("region", "neck")
    laterality = data.get("laterality", "bilateral")
    face_index = data.get("face_index")
    bary = json.dumps(data.get("barycentric", []))
    reg_dist = float(data.get("registration_distance", 0.0))
    reg_status = data.get("registration_status", "SURFACE_REGISTERED_FJ2810")
    rev_status = data.get("review_status", "PENDING_EXPERT_REVIEW")
    indications = json.dumps(data.get("indications", []))
    cautions = json.dumps(data.get("cautions", []))
    tuina = data.get("tuina_method", "")
    notes = data.get("notes", "")

    evidence_id = data.get("evidence_id")
    reviewer = data.get("reviewer")
    verif_method = data.get("verification_method", "SURFACE_RAYCAST_INTERSECTION")
    uncert_radius = float(data.get("uncertainty_radius_mm", 0.0) or 0.0)

    validate_governance_tier(
        reg_status,
        reviewer=reviewer,
        evidence_id=evidence_id,
        uncertainty_radius_mm=uncert_radius,
        db=db,
        is_custom=(library_id == "lib_custom_user" or system == "user_custom"),
        review_status=rev_status
    )

    db.execute(
        """
        INSERT INTO custom_points (
            point_id, library_id, code, name_en, name_zh, name_vi, pinyin,
            aliases_json, system_classification, region, laterality,
            pos_x, pos_y, pos_z, norm_x, norm_y, norm_z,
            mesh_id, mesh_hash, face_index, barycentric_json, registration_distance,
            registration_status, review_status, indications_json, cautions_json,
            tuina_method, notes, author,
            evidence_id, reviewer, verification_method, uncertainty_radius_mm
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            point_id, library_id, code, name_en, data.get("name_zh", ""), data.get("name_vi", ""),
            data.get("pinyin", ""), json.dumps(data.get("aliases", [])), system, region, laterality,
            pos[0], pos[1], pos[2], norm[0], norm[1], norm[2],
            mesh_id, mesh_hash, face_index, bary, reg_dist,
            reg_status, rev_status, indications, cautions,
            tuina, notes, author,
            evidence_id, reviewer, verif_method, uncert_radius
        )
    )

    created_point = get_point(db, point_id)
    # Log CREATE revision
    db.execute(
        """
        INSERT INTO point_revisions (
            point_id, revision_number, change_type, previous_state_json, new_state_json, author, notes,
            evidence_id, reviewer, verification_method, uncertainty_radius_mm
        )
        VALUES (?, 1, 'CREATE', NULL, ?, ?, ?, ?, ?, ?, ?)
        """,
        (point_id, json.dumps(created_point), author, "Initial point creation on 3D skin mesh", evidence_id, reviewer, verif_method, uncert_radius)
    )
    db.commit()
    return created_point


def update_point(
    db: sqlite3.Connection,
    point_id: str,
    data: Dict[str, Any],
    author: str = "Clinical Educator",
    change_type: str = "UPDATE_COORDS",
    notes: str = ""
) -> Dict[str, Any]:
    """Update point coordinates or metadata with revision tracking."""
    existing = get_point(db, point_id)
    if not existing:
        raise ValueError(f"Point '{point_id}' not found.")
    canonical_id = existing["point_id"]

    pos = data.get("position", existing["position"])
    validate_coordinates(pos[0], pos[1], pos[2])

    norm = data.get("normal", existing["normal"])
    reg_status = data.get("registration_status", existing["registration_status"])
    rev_status = data.get("review_status", existing["review_status"])
    name_en = data.get("name_en", existing["name_en"])
    name_zh = data.get("name_zh", existing["name_zh"])
    name_vi = data.get("name_vi", existing["name_vi"])
    pinyin = data.get("pinyin", existing["pinyin"])
    region = data.get("region", existing["region"])
    face_idx = data.get("face_index", existing["face_index"])
    indications = json.dumps(data.get("indications", existing["indications"]))
    cautions = json.dumps(data.get("cautions", existing["cautions"]))
    tuina = data.get("tuina_method", existing["tuina_method"])
    pt_notes = data.get("notes", existing["notes"])

    evidence_id = data.get("evidence_id", existing.get("evidence_id"))
    reviewer = data.get("reviewer", existing.get("reviewer"))
    verif_method = data.get("verification_method", existing.get("verification_method") or "SURFACE_RAYCAST_INTERSECTION")
    uncert_radius = float(data.get("uncertainty_radius_mm", existing.get("uncertainty_radius_mm") or 0.0) or 0.0)

    validate_governance_tier(
        reg_status,
        reviewer=reviewer,
        evidence_id=evidence_id,
        uncertainty_radius_mm=uncert_radius,
        db=db,
        is_custom=True,
        review_status=rev_status
    )

    # Determine revision number
    cursor = db.cursor()
    cursor.execute("SELECT MAX(revision_number) FROM point_revisions WHERE point_id = ? OR point_id = ?", (canonical_id, existing["code"]))
    rev_row = cursor.fetchone()
    next_rev = (rev_row[0] or 0) + 1

    db.execute(
        """
        UPDATE custom_points
        SET name_en = ?, name_zh = ?, name_vi = ?, pinyin = ?, region = ?,
            pos_x = ?, pos_y = ?, pos_z = ?, norm_x = ?, norm_y = ?, norm_z = ?,
            face_index = ?, registration_status = ?, review_status = ?,
            indications_json = ?, cautions_json = ?, tuina_method = ?, notes = ?,
            evidence_id = ?, reviewer = ?, verification_method = ?, uncertainty_radius_mm = ?,
            updated_utc = strftime('%Y-%m-%dT%H:%M:%SZ','now')
        WHERE point_id = ?
        """,
        (
            name_en, name_zh, name_vi, pinyin, region,
            pos[0], pos[1], pos[2], norm[0], norm[1], norm[2],
            face_idx, reg_status, rev_status,
            indications, cautions, tuina, pt_notes,
            evidence_id, reviewer, verif_method, uncert_radius,
            canonical_id
        )
    )

    updated_point = get_point(db, canonical_id)
    # Log revision
    db.execute(
        """
        INSERT INTO point_revisions (
            point_id, revision_number, change_type, previous_state_json, new_state_json, author, notes,
            evidence_id, reviewer, verification_method, uncertainty_radius_mm
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (canonical_id, next_rev, change_type, json.dumps(existing), json.dumps(updated_point), author, notes or f"Point {change_type}", evidence_id, reviewer, verif_method, uncert_radius)
    )
    db.commit()
    return updated_point


def soft_delete_point(db: sqlite3.Connection, point_id: str, author: str = "Clinical Educator") -> bool:
    """Soft-delete a custom point with audit trail."""
    existing = get_point(db, point_id)
    if not existing:
        raise ValueError(f"Point '{point_id}' not found.")
    canonical_id = existing["point_id"]

    cursor = db.cursor()
    cursor.execute("SELECT MAX(revision_number) FROM point_revisions WHERE point_id = ? OR point_id = ?", (canonical_id, existing["code"]))
    next_rev = (cursor.fetchone()[0] or 0) + 1

    db.execute(
        "UPDATE custom_points SET is_deleted = 1, updated_utc = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE point_id = ?",
        (canonical_id,)
    )
    db.execute(
        """
        INSERT INTO point_revisions (point_id, revision_number, change_type, previous_state_json, new_state_json, author, notes)
        VALUES (?, ?, 'DELETE', ?, ?, ?, 'Soft-deleted custom point')
        """,
        (canonical_id, next_rev, json.dumps(existing), json.dumps({"is_deleted": True}), author)
    )
    db.commit()
    return True


def restore_point(db: sqlite3.Connection, point_id: str, author: str = "Clinical Educator") -> Dict[str, Any]:
    """Restore a soft-deleted custom point."""
    cursor = db.cursor()
    cursor.execute("SELECT point_id FROM custom_points WHERE point_id = ? OR code = ?", (point_id, point_id))
    r = cursor.fetchone()
    if not r:
        raise ValueError(f"Point '{point_id}' not found.")
    canonical_id = r[0]

    cursor.execute("SELECT MAX(revision_number) FROM point_revisions WHERE point_id = ?", (canonical_id,))
    next_rev = (cursor.fetchone()[0] or 0) + 1

    db.execute(
        "UPDATE custom_points SET is_deleted = 0, updated_utc = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE point_id = ?",
        (canonical_id,)
    )
    restored = get_point(db, canonical_id)
    db.execute(
        """
        INSERT INTO point_revisions (point_id, revision_number, change_type, previous_state_json, new_state_json, author, notes)
        VALUES (?, ?, 'RESTORE', ?, ?, ?, 'Restored soft-deleted point')
        """,
        (canonical_id, next_rev, json.dumps({"is_deleted": True}), json.dumps(restored), author)
    )
    db.commit()
    return restored


def get_point_revisions(db: sqlite3.Connection, point_id: str) -> List[Dict[str, Any]]:
    """Retrieve full audit history for a point."""
    cursor = db.cursor()
    cursor.execute("SELECT point_id FROM custom_points WHERE point_id = ? OR code = ?", (point_id, point_id))
    r = cursor.fetchone()
    canonical_id = r[0] if r else point_id

    cursor.execute(
        """
        SELECT revision_id, revision_number, change_type, previous_state_json, new_state_json, author, notes, created_utc
        FROM point_revisions
        WHERE point_id = ? OR point_id = ?
        ORDER BY revision_number DESC
        """,
        (canonical_id, point_id)
    )
    rows = cursor.fetchall()
    return [
        {
            "revision_id": r[0],
            "revision_number": r[1],
            "change_type": r[2],
            "previous_state": json.loads(r[3]) if r[3] else None,
            "new_state": json.loads(r[4]),
            "author": r[5],
            "notes": r[6] or "",
            "created_utc": r[7]
        }
        for r in rows
    ]


def revert_to_revision(db: sqlite3.Connection, point_id: str, revision_number: int, author: str = "Clinical Educator") -> Dict[str, Any]:
    """Undo/revert point state to a specific revision number."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT new_state_json FROM point_revisions WHERE point_id = ? AND revision_number = ?",
        (point_id, revision_number)
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Revision #{revision_number} for point '{point_id}' not found.")
    target_state = json.loads(row[0])
    return update_point(db, point_id, target_state, author=author, change_type="REVERT", notes=f"Reverted to revision #{revision_number}")


# -----------------------------------------------------------------------------
# Canonical Reference Point Overrides
# -----------------------------------------------------------------------------

def set_reference_override(
    db: sqlite3.Connection,
    reference_code: str,
    data: Dict[str, Any],
    author: str = "Clinical Educator",
    notes: str = ""
) -> Dict[str, Any]:
    """Create or update a versioned override of a canonical reference point without mutating source file."""
    ref_code = reference_code.strip().upper()
    pos = data.get("position")
    if not pos or len(pos) != 3:
        raise ValueError("Valid 3D position [X, Y, Z] is required for override.")
    validate_coordinates(pos[0], pos[1], pos[2])

    norm = data.get("normal", [0.0, 0.0, 1.0])
    reg_status = data.get("registration_status", "SURFACE_REGISTERED_FJ2810")
    rev_status = data.get("review_status", "EXPERT_VERIFIED")
    face_idx = data.get("face_index")

    evidence_id = data.get("evidence_id")
    reviewer = data.get("reviewer")
    verif_method = data.get("verification_method", "SURFACE_RAYCAST_INTERSECTION")
    uncert_radius = float(data.get("uncertainty_radius_mm", 0.0) or 0.0)

    validate_governance_tier(
        reg_status,
        reviewer=reviewer,
        evidence_id=evidence_id,
        uncertainty_radius_mm=uncert_radius,
        db=db,
        is_custom=False,
        review_status=rev_status
    )

    db.execute(
        """
        INSERT INTO reference_point_overrides (
            reference_code, pos_x, pos_y, pos_z, norm_x, norm_y, norm_z, face_index,
            registration_status, review_status, notes, author,
            evidence_id, reviewer, verification_method, uncertainty_radius_mm,
            updated_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        ON CONFLICT(reference_code) DO UPDATE SET
            pos_x=excluded.pos_x, pos_y=excluded.pos_y, pos_z=excluded.pos_z,
            norm_x=excluded.norm_x, norm_y=excluded.norm_y, norm_z=excluded.norm_z,
            face_index=excluded.face_index, registration_status=excluded.registration_status,
            review_status=excluded.review_status, notes=excluded.notes,
            author=excluded.author,
            evidence_id=excluded.evidence_id, reviewer=excluded.reviewer,
            verification_method=excluded.verification_method,
            uncertainty_radius_mm=excluded.uncertainty_radius_mm,
            updated_utc=strftime('%Y-%m-%dT%H:%M:%SZ','now')
        """,
        (ref_code, pos[0], pos[1], pos[2], norm[0], norm[1], norm[2], face_idx, reg_status, rev_status, notes, author, evidence_id, reviewer, verif_method, uncert_radius)
    )

    # Log revision for reference point
    cursor = db.cursor()
    cursor.execute("SELECT MAX(revision_number) FROM point_revisions WHERE point_id = ?", (ref_code,))
    next_rev = (cursor.fetchone()[0] or 0) + 1
    db.execute(
        """
        INSERT INTO point_revisions (
            point_id, revision_number, change_type, previous_state_json, new_state_json, author, notes,
            evidence_id, reviewer, verification_method, uncertainty_radius_mm
        )
        VALUES (?, ?, 'OVERRIDE_REFERENCE', NULL, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ref_code, next_rev, json.dumps(data), author, notes or f"Override reference point {ref_code}", evidence_id, reviewer, verif_method, uncert_radius)
    )
    db.commit()
    return get_reference_override(db, ref_code)


def get_reference_override(db: sqlite3.Connection, reference_code: str) -> Optional[Dict[str, Any]]:
    """Retrieve an active reference override for a given code."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT reference_code, pos_x, pos_y, pos_z, norm_x, norm_y, norm_z, face_index,
               registration_status, review_status, notes, author, created_utc, updated_utc,
               evidence_id, reviewer, verification_method, uncertainty_radius_mm
        FROM reference_point_overrides
        WHERE reference_code = ?
        """,
        (reference_code.strip().upper(),)
    )
    r = cursor.fetchone()
    if not r:
        return None
    return {
        "reference_code": r[0],
        "position": [r[1], r[2], r[3]],
        "normal": [r[4], r[5], r[6]],
        "face_index": r[7],
        "registration_status": r[8],
        "review_status": r[9],
        "notes": r[10] or "",
        "author": r[11],
        "created_utc": r[12],
        "updated_utc": r[13],
        "evidence_id": r[14] if len(r) > 14 else None,
        "reviewer": r[15] if len(r) > 15 else None,
        "verification_method": r[16] if len(r) > 16 else "SURFACE_RAYCAST_INTERSECTION",
        "uncertainty_radius_mm": r[17] if len(r) > 17 else 0.0
    }


def list_reference_overrides(db: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    """Return dictionary of all active reference point overrides."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT reference_code, pos_x, pos_y, pos_z, norm_x, norm_y, norm_z, face_index,
               registration_status, review_status, notes, author, created_utc, updated_utc,
               evidence_id, reviewer, verification_method, uncertainty_radius_mm
        FROM reference_point_overrides
        """
    )
    rows = cursor.fetchall()
    overrides = {}
    for r in rows:
        overrides[r[0]] = {
            "reference_code": r[0],
            "position": [r[1], r[2], r[3]],
            "normal": [r[4], r[5], r[6]],
            "face_index": r[7],
            "registration_status": r[8],
            "review_status": r[9],
            "notes": r[10] or "",
            "author": r[11],
            "created_utc": r[12],
            "updated_utc": r[13],
            "evidence_id": r[14] if len(r) > 14 else None,
            "reviewer": r[15] if len(r) > 15 else None,
            "verification_method": r[16] if len(r) > 16 else "SURFACE_RAYCAST_INTERSECTION",
            "uncertainty_radius_mm": r[17] if len(r) > 17 else 0.0
        }
    return overrides


def delete_reference_override(db: sqlite3.Connection, reference_code: str, author: str = "Clinical Educator") -> bool:
    """Restore reference point to original canonical location by removing the override."""
    ref_code = reference_code.strip().upper()
    existing = get_reference_override(db, ref_code)
    if not existing:
        return False

    cursor = db.cursor()
    cursor.execute("SELECT MAX(revision_number) FROM point_revisions WHERE point_id = ?", (ref_code,))
    next_rev = (cursor.fetchone()[0] or 0) + 1

    db.execute("DELETE FROM reference_point_overrides WHERE reference_code = ?", (ref_code,))
    db.execute(
        """
        INSERT INTO point_revisions (point_id, revision_number, change_type, previous_state_json, new_state_json, author, notes)
        VALUES (?, ?, 'RESTORE_BASELINE', ?, '{"status":"restored_to_baseline"}', ?, 'Removed override; restored canonical coordinates')
        """,
        (ref_code, next_rev, json.dumps(existing), author)
    )
    db.commit()
    return True


# -----------------------------------------------------------------------------
# JSON Export & Import with SHA-256 Digest Verification
# -----------------------------------------------------------------------------

def export_library_bundle(db: sqlite3.Connection, library_id: str = "lib_custom_user") -> Dict[str, Any]:
    """Generate structured export with schema version, anatomy base, points, and SHA-256 digest."""
    cursor = db.cursor()
    cursor.execute("SELECT library_id, name, namespace, description, color FROM point_libraries WHERE library_id = ?", (library_id,))
    lib_row = cursor.fetchone()
    if not lib_row:
        raise ValueError(f"Library '{library_id}' not found.")

    points = list_custom_points(db, library_id=library_id, include_deleted=False)

    payload = {
        "$schema": "https://msk-therapy-os.org/schemas/v2.5/custom-acupoint-atlas.json",
        "schema_version": "2.5.0",
        "exported_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "library": {
            "library_id": lib_row[0],
            "name": lib_row[1],
            "namespace": lib_row[2],
            "description": lib_row[3],
            "color": lib_row[4]
        },
        "anatomy_base": {
            "mesh_id": VALID_MESH_ID,
            "mesh_name": "Skin of body",
            "standard": "BodyParts3D 4.0 / FMA 7163",
            "mesh_hash": VALID_MESH_HASH
        },
        "points_count": len(points),
        "points": points
    }

    # Calculate cryptographic SHA-256 digest of payload
    digest = compute_sha256_digest(payload)
    payload["sha256_checksum"] = digest
    return payload


def import_library_bundle(
    db: sqlite3.Connection,
    bundle_data: Dict[str, Any],
    author: str = "Import Operator"
) -> Dict[str, Any]:
    """Validate, preview conflicts, and import points safely without overwriting canonical data."""
    if not isinstance(bundle_data, dict):
        raise ValueError("Invalid bundle: JSON must be an object.")

    # 1. Verify schema or points presence
    points = bundle_data.get("points")
    if not isinstance(points, list):
        # Fallback to dictionary format if legacy
        if isinstance(points, dict):
            points = list(points.values())
        else:
            raise ValueError("Invalid bundle: 'points' array is missing.")

    # 2. Check mesh hash if present
    anatomy = bundle_data.get("anatomy_base", {})
    mesh_hash = anatomy.get("mesh_hash")
    if mesh_hash and mesh_hash != VALID_MESH_HASH:
        raise ValueError(f"Incompatible anatomical mesh hash '{mesh_hash}'. Refusing import to protect surface integrity.")

    # 3. Check SHA-256 digest if present
    claimed_sha = bundle_data.get("sha256_checksum")
    if claimed_sha:
        payload_copy = {k: v for k, v in bundle_data.items() if k != "sha256_checksum"}
        calculated_sha = compute_sha256_digest(payload_copy)
        if claimed_sha.lower() != calculated_sha.lower():
            raise ValueError("Cryptographic SHA-256 checksum mismatch! The file may have been modified or corrupted.")

    lib_info = bundle_data.get("library", {})
    target_lib_id = lib_info.get("library_id", "lib_custom_user")
    # Ensure library exists
    cursor = db.cursor()
    cursor.execute("SELECT library_id, is_readonly FROM point_libraries WHERE library_id = ?", (target_lib_id,))
    lib_row = cursor.fetchone()
    if not lib_row:
        # Create user custom library
        create_library(db, {
            "library_id": target_lib_id,
            "name": lib_info.get("name", "Imported Custom Library"),
            "namespace": lib_info.get("namespace", "USER_CUSTOM"),
            "description": lib_info.get("description", "Imported from JSON bundle"),
            "color": lib_info.get("color", "#06b6d4")
        })
    elif lib_row[1] == 1:
        raise ValueError(f"Cannot import directly into read-only canonical library '{target_lib_id}'.")

    imported_count = 0
    skipped_count = 0
    updated_count = 0

    for pt in points:
        code = pt.get("code")
        if not code:
            continue
        # Geometric validation
        pos = pt.get("position")
        if not pos or len(pos) != 3:
            continue
        try:
            validate_coordinates(pos[0], pos[1], pos[2])
        except ValueError:
            skipped_count += 1
            continue

        existing = get_point(db, pt.get("point_id", code))
        if existing:
            # Update existing custom point
            update_point(db, existing["point_id"], pt, author=author, change_type="UPDATE_METADATA", notes="Imported update from JSON bundle")
            updated_count += 1
        else:
            pt["library_id"] = target_lib_id
            create_point(db, pt, author=author)
            imported_count += 1

    return {
        "status": "SUCCESS",
        "imported_count": imported_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "total_processed": len(points)
    }


def sanitize_backup_filename(name: Optional[str]) -> str:
    """Sanitize and validate backup filename to prevent directory traversal and arbitrary writes."""
    if not name or not str(name).strip():
        return f"backup_snapshot_{int(time.time())}.sqlite3"
    clean = str(name).strip()
    if "/" in clean or "\\" in clean or "\0" in clean or ".." in clean:
        raise ValueError("Path traversal sequences and directory separators are not allowed in backup filenames.")
    clean = Path(clean).name
    if not clean.endswith(".sqlite3"):
        clean += ".sqlite3"
    if not re.match(r"^[a-zA-Z0-9_\-]+\.sqlite3$", clean):
        raise ValueError("Backup filename may only contain alphanumeric characters, hyphens, and underscores.")
    return clean


def get_safe_backup_path(filename: Optional[str], base_dir: Optional[Path] = None) -> Path:
    """Resolve and enforce approved directory isolation for database backups."""
    clean_name = sanitize_backup_filename(filename)
    if base_dir is None:
        if (Path("2data") / "backups").exists():
            base_dir = (Path("2data") / "backups").resolve()
        else:
            base_dir = (Path("data") / "backups").resolve()
    else:
        base_dir = base_dir.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    target = (base_dir / clean_name).resolve()
    if not str(target).startswith(str(base_dir)):
        raise PermissionError("Path traversal attack detected: target escapes approved backup directory.")
    return target


def validate_governance_tier(
    registration_status: str,
    reviewer: Optional[str] = None,
    evidence_id: Optional[str] = None,
    uncertainty_radius_mm: Optional[float] = None,
    db: Optional[sqlite3.Connection] = None,
    is_custom: bool = False,
    review_status: Optional[str] = None,
) -> None:
    """Enforce strict separation between geometric surface verification and clinical anatomical review.
    
    Rules:
    - User custom points cannot claim 'OFFICIAL_STANDARD' review status (reserved for WHO/national standards).
    - Surface raycast intersection alone qualifies only for GEOMETRY_VERIFIED or SURFACE_REGISTERED_FJ2810.
    - ANATOMY_REVIEWED claims require:
      1. A named qualified human reviewer possessing recognized clinical credentials (MD, DO, LAc, PT, DPT, DC, PhD, MBBS, FACP, ND).
      2. An explicit evidence reference or catalog ID registered in evidence_catalog or recognized standards.
      3. A non-zero, physically bounded localization uncertainty radius in millimeters: 0.0 < uncertainty_radius_mm <= 25.0 mm.
    """
    if is_custom and review_status == "OFFICIAL_STANDARD":
        raise ValueError("User custom points cannot claim 'OFFICIAL_STANDARD' review status. Official standards are reserved for canonical WHO/national standard datasets.")

    if registration_status not in VALID_GOVERNANCE_STATUSES:
        raise ValueError(f"Invalid registration status '{registration_status}'. Allowed: {VALID_GOVERNANCE_STATUSES}")

    if registration_status == "ANATOMY_REVIEWED":
        rev = (reviewer or "").strip()
        if not rev:
            raise ValueError("Anatomical review claims ('ANATOMY_REVIEWED') require a named qualified human reviewer.")
        rev_words = set(rev.lower().replace('-', ' ').replace('_', ' ').split())
        invalid_tokens = {'ai', 'system', 'automated', 'unknown', 'none', 'bot', 'algorithm', 'gpt', 'llm'}
        if rev_words & invalid_tokens or rev.lower() in invalid_tokens:
            raise ValueError(f"Reviewer '{rev}' is invalid. Human clinical governance requires qualified practitioner review, not automated systems.")
        
        # Clinical credential and identity verification
        tokens = {tok.strip('.,()').upper() for tok in re.findall(r'[A-Za-z\.]+', rev)}
        if not (tokens & ALLOWED_CLINICAL_CREDENTIALS):
            raise ValueError(f"Reviewer '{rev}' lacks verifiable clinical credentials. Allowed credentials include: {', '.join(sorted(ALLOWED_CLINICAL_CREDENTIALS))}")

        if db is not None:
            # Check verified reviewer registry in clinical_reviewers
            has_cr_table = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='clinical_reviewers'").fetchone()
            if has_cr_table:
                cr_row = db.execute(
                    """SELECT reviewer_id, display_name, primary_credential, verification_status
                       FROM clinical_reviewers
                       WHERE (reviewer_id = ? OR display_name = ? OR user_id = ? OR user_id IN (SELECT user_id FROM users WHERE username = ?))""",
                    (rev, rev, rev, rev)
                ).fetchone()
                if not cr_row:
                    raise ValueError(f"Reviewer '{rev}' is not registered in the clinical_reviewers registry. Clinical governance requires an administrator-verified reviewer identity.")
                if cr_row[3] != 'VERIFIED_ACTIVE':
                    raise ValueError(f"Reviewer '{rev}' is registered but verification status is '{cr_row[3]}'. Only 'VERIFIED_ACTIVE' reviewers may approve anatomical review claims.")

        ev = (evidence_id or "").strip()
        if not ev:
            raise ValueError("Anatomical review claims ('ANATOMY_REVIEWED') require an explicit evidence catalog reference or citation.")
        if db is not None:
            ev_found = db.execute("SELECT 1 FROM evidence_catalog WHERE evidence_id = ?", (ev,)).fetchone()
            if not ev_found and ev.upper() not in RECOGNIZED_STANDARDS:
                raise ValueError(f"Evidence ID '{ev}' is not registered in evidence_catalog or recognized standards.")

        if uncertainty_radius_mm is not None and uncertainty_radius_mm < 0:
            raise ValueError(f"Uncertainty radius must be non-negative, got {uncertainty_radius_mm}mm.")
        if uncertainty_radius_mm is None or uncertainty_radius_mm == 0.0 or uncertainty_radius_mm > 25.0:
            raise ValueError(f"Uncertainty radius must be physically bounded between (0.0, 25.0] mm for anatomical review claims, got {uncertainty_radius_mm}mm.")


def migrate_governance_schema(db: sqlite3.Connection) -> None:
    """Safely migrate database to include governance and evidence ledger columns."""
    cursor = db.cursor()
    # Check custom_points columns
    cp_cols = {r[1] for r in cursor.execute("PRAGMA table_info(custom_points)").fetchall()}
    if "evidence_id" not in cp_cols:
        cursor.execute("ALTER TABLE custom_points ADD COLUMN evidence_id TEXT REFERENCES evidence_catalog(evidence_id)")
    if "reviewer" not in cp_cols:
        cursor.execute("ALTER TABLE custom_points ADD COLUMN reviewer TEXT")
    if "verification_method" not in cp_cols:
        cursor.execute("ALTER TABLE custom_points ADD COLUMN verification_method TEXT DEFAULT 'SURFACE_RAYCAST_INTERSECTION'")
    if "uncertainty_radius_mm" not in cp_cols:
        cursor.execute("ALTER TABLE custom_points ADD COLUMN uncertainty_radius_mm REAL DEFAULT 0.0")

    # Check reference_point_overrides columns
    ro_cols = {r[1] for r in cursor.execute("PRAGMA table_info(reference_point_overrides)").fetchall()}
    if "evidence_id" not in ro_cols:
        cursor.execute("ALTER TABLE reference_point_overrides ADD COLUMN evidence_id TEXT REFERENCES evidence_catalog(evidence_id)")
    if "reviewer" not in ro_cols:
        cursor.execute("ALTER TABLE reference_point_overrides ADD COLUMN reviewer TEXT")
    if "verification_method" not in ro_cols:
        cursor.execute("ALTER TABLE reference_point_overrides ADD COLUMN verification_method TEXT DEFAULT 'SURFACE_RAYCAST_INTERSECTION'")
    if "uncertainty_radius_mm" not in ro_cols:
        cursor.execute("ALTER TABLE reference_point_overrides ADD COLUMN uncertainty_radius_mm REAL DEFAULT 0.0")

    # Check point_revisions columns
    pr_cols = {r[1] for r in cursor.execute("PRAGMA table_info(point_revisions)").fetchall()}
    if "evidence_id" not in pr_cols:
        cursor.execute("ALTER TABLE point_revisions ADD COLUMN evidence_id TEXT")
    if "reviewer" not in pr_cols:
        cursor.execute("ALTER TABLE point_revisions ADD COLUMN reviewer TEXT")
    if "verification_method" not in pr_cols:
        cursor.execute("ALTER TABLE point_revisions ADD COLUMN verification_method TEXT")
    if "uncertainty_radius_mm" not in pr_cols:
        cursor.execute("ALTER TABLE point_revisions ADD COLUMN uncertainty_radius_mm REAL DEFAULT 0.0")

    db.commit()


def verify_reference_dataset_integrity(base_path: Optional[str] = None) -> Dict[str, Any]:
    """Verify cryptographic integrity of immutable canonical reference datasets."""
    from pathlib import Path
    if base_path:
        acu_path = Path(base_path)
    else:
        acu_path = Path(__file__).resolve().parent / "static" / "atlas" / "data" / "acupuncture_3d.json"

    if not acu_path.exists():
        return {
            "status": "MISSING",
            "file": str(acu_path),
            "expected_sha256": CANONICAL_REFERENCE_CHECKSUMS["acupuncture_3d.json"],
            "actual_sha256": None,
            "is_valid": False
        }

    raw = acu_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected = CANONICAL_REFERENCE_CHECKSUMS["acupuncture_3d.json"]
    is_valid = (digest == expected)

    return {
        "status": "VALID" if is_valid else "CORRUPTED_OR_MODIFIED",
        "file": str(acu_path),
        "expected_sha256": expected,
        "actual_sha256": digest,
        "is_valid": is_valid
    }


def run_database_integrity_check(db: sqlite3.Connection) -> Dict[str, Any]:
    """Execute complete database integrity audit, schema check, and governance compliance."""
    migrate_governance_schema(db)
    cursor = db.cursor()

    # 1. PRAGMA integrity_check
    cursor.execute("PRAGMA integrity_check")
    integrity_rows = cursor.fetchall()
    integrity_ok = len(integrity_rows) == 1 and integrity_rows[0][0] == "ok"

    # 2. PRAGMA foreign_key_check
    cursor.execute("PRAGMA foreign_key_check")
    fk_violations = cursor.fetchall()
    fk_ok = (len(fk_violations) == 0)

    # 3. Reference dataset hash verification
    ref_integrity = verify_reference_dataset_integrity()

    # 4. Governance compliance audit
    # Rule: ANATOMY_REVIEWED must have qualified reviewer with clinical credentials, evidence_id, and 0 < uncertainty <= 25mm
    cursor.execute(
        """SELECT point_id, code, registration_status, reviewer, evidence_id, uncertainty_radius_mm
           FROM custom_points
           WHERE registration_status = 'ANATOMY_REVIEWED'"""
    )
    unqualified_custom = []
    for r in cursor.fetchall():
        rev = r[3] or ""
        ev = r[4] or ""
        rad = r[5]
        tokens = {tok.strip('.,()').upper() for tok in re.findall(r'[A-Za-z\.]+', rev)}
        has_cred = bool(tokens & ALLOWED_CLINICAL_CREDENTIALS)
        rev_words = set(rev.lower().replace('-', ' ').replace('_', ' ').split())
        invalid_tokens = {'ai', 'system', 'automated', 'unknown', 'none', 'bot', 'algorithm', 'gpt', 'llm'}
        if not rev.strip() or (rev_words & invalid_tokens) or not has_cred or not ev.strip() or rad is None or rad <= 0.0 or rad > 25.0:
            unqualified_custom.append(r)

    cursor.execute(
        """SELECT reference_code, registration_status, reviewer, evidence_id, uncertainty_radius_mm
           FROM reference_point_overrides
           WHERE registration_status = 'ANATOMY_REVIEWED'"""
    )
    unqualified_overrides = []
    for r in cursor.fetchall():
        rev = r[2] or ""
        ev = r[3] or ""
        rad = r[4]
        tokens = {tok.strip('.,()').upper() for tok in re.findall(r'[A-Za-z\.]+', rev)}
        has_cred = bool(tokens & ALLOWED_CLINICAL_CREDENTIALS)
        rev_words = set(rev.lower().replace('-', ' ').replace('_', ' ').split())
        invalid_tokens = {'ai', 'system', 'automated', 'unknown', 'none', 'bot', 'algorithm', 'gpt', 'llm'}
        if not rev.strip() or (rev_words & invalid_tokens) or not has_cred or not ev.strip() or rad is None or rad <= 0.0 or rad > 25.0:
            unqualified_overrides.append(r)

    governance_compliant = (len(unqualified_custom) == 0 and len(unqualified_overrides) == 0)

    # 5. Point counts by governance tier
    cursor.execute(
        """SELECT registration_status, COUNT(*) FROM custom_points WHERE is_deleted = 0 GROUP BY registration_status"""
    )
    custom_tier_counts = dict(cursor.fetchall())

    cursor.execute(
        """SELECT registration_status, COUNT(*) FROM reference_point_overrides GROUP BY registration_status"""
    )
    override_tier_counts = dict(cursor.fetchall())

    overall_pass = integrity_ok and fk_ok and ref_integrity.get("is_valid", False) and governance_compliant

    return {
        "status": "PASS" if overall_pass else "FAIL",
        "integrity_check": "ok" if integrity_ok else str(integrity_rows),
        "foreign_key_violations_count": len(fk_violations),
        "reference_dataset_integrity": ref_integrity,
        "governance_compliance": {
            "is_compliant": governance_compliant,
            "unqualified_reviewed_points_count": len(unqualified_custom) + len(unqualified_overrides),
            "unqualified_points": [r[0] for r in unqualified_custom] + [r[0] for r in unqualified_overrides]
        },
        "counts_by_status": {
            "custom_points": custom_tier_counts,
            "reference_overrides": override_tier_counts
        }
    }


def get_backup_signing_key() -> bytes:
    """Retrieve or generate persistent HMAC secret key for backup anti-tamper authentication."""
    env_key = os.environ.get("MSK_BACKUP_HMAC_KEY")
    if env_key:
        return env_key.encode("utf-8")
    
    # Check 2data/.backup_hmac_key or .backup_hmac_key
    target_dir = Path("2data") if Path("2data").exists() else Path(".")
    key_file = target_dir / ".backup_hmac_key"
    if key_file.exists():
        try:
            k = key_file.read_bytes().strip()
            if len(k) >= 16:
                return k
        except Exception:
            pass
    
    # Generate persistent 32-byte secret
    new_key = secrets.token_bytes(32)
    try:
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_bytes(new_key)
    except Exception:
        pass
    return new_key


def backup_database(db: sqlite3.Connection, backup_path: str) -> Dict[str, Any]:
    """Perform atomic online SQLite backup with cryptographic SHA-256 verification and HMAC-SHA256 anti-tamper signing."""
    with MAINTENANCE_LOCK:
        bp = Path(backup_path).resolve()
        bp.parent.mkdir(parents=True, exist_ok=True)
        dest_db = sqlite3.connect(str(bp))
        with dest_db:
            db.backup(dest_db, pages=100)
        dest_db.close()

        raw_bytes = bp.read_bytes()
        checksum = hashlib.sha256(raw_bytes).hexdigest()
        sha_file = bp.with_suffix(bp.suffix + ".sha256")
        sha_file.write_text(f"{checksum}  {bp.name}\n", encoding="utf-8")

        # Anti-tamper keyed HMAC-SHA256 signature
        hmac_key = get_backup_signing_key()
        hmac_sig = hmac.new(hmac_key, raw_bytes, hashlib.sha256).hexdigest()
        hmac_file = bp.with_suffix(bp.suffix + ".hmac")
        hmac_file.write_text(f"{hmac_sig}  {bp.name}\n", encoding="utf-8")

        return {
            "status": "SUCCESS",
            "backup_path": str(bp),
            "sha256_checksum": checksum,
            "hmac_signature": hmac_sig,
            "size_bytes": len(raw_bytes),
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }


def restore_database_safely(target_db_path: str, backup_source_path: str, require_hmac: bool = False) -> Dict[str, Any]:
    """Safely restore SQLite database using native backup API with anti-tamper verification and exclusive maintenance lock."""
    global IS_MAINTENANCE_ACTIVE
    src = Path(backup_source_path).resolve()
    tgt = Path(target_db_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Backup file not found at '{src}'.")

    # 1. Verify SHA-256 digest if .sha256 file exists (bit-rot/corruption check)
    sha_file = src.with_suffix(src.suffix + ".sha256")
    if sha_file.exists():
        expected_sha = sha_file.read_text(encoding="utf-8").split()[0].strip().lower()
        actual_sha = hashlib.sha256(src.read_bytes()).hexdigest().lower()
        if expected_sha != actual_sha:
            raise ValueError(f"Backup SHA-256 checksum mismatch (expected {expected_sha}, got {actual_sha}).")

    # 2. Anti-tamper verification (HMAC-SHA256)
    is_secure = os.environ.get("MSK_MODE") == "secure" or os.environ.get("MSK_SECURE_MODE") in ("1", "true", "True")
    hmac_file = src.with_suffix(src.suffix + ".hmac")
    if hmac_file.exists():
        expected_hmac = hmac_file.read_text(encoding="utf-8").split()[0].strip().lower()
        key = get_backup_signing_key()
        actual_hmac = hmac.new(key, src.read_bytes(), hashlib.sha256).hexdigest().lower()
        if not hmac.compare_digest(expected_hmac, actual_hmac):
            raise PermissionError(f"Backup anti-tamper verification failed: cryptographic HMAC signature mismatch. File has been tampered with or signed with an unauthorized key.")
    elif require_hmac or is_secure:
        raise PermissionError(f"Backup anti-tamper verification failed: missing companion .hmac signature file ({hmac_file.name}). In SECURE mode, backups must be cryptographically authenticated.")

    # 3. Verify SQLite database integrity & schema compatibility before restoring
    try:
        test_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
        res = test_conn.execute("PRAGMA integrity_check").fetchall()
        if len(res) != 1 or res[0][0] != "ok":
            test_conn.close()
            raise ValueError(f"Corrupted backup file: SQLite integrity check failed ({res})")

        fk_res = test_conn.execute("PRAGMA foreign_key_check").fetchall()
        if len(fk_res) > 0:
            test_conn.close()
            raise ValueError(f"Backup foreign key violations detected: {fk_res}")

        # Check required schema tables
        tables = {r[0] for r in test_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        required_tables = {"point_libraries", "custom_points"}
        if not required_tables.issubset(tables):
            test_conn.close()
            raise ValueError(f"Incompatible backup schema: missing required tables {required_tables - tables}")
        test_conn.close()
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Invalid or corrupted SQLite backup database: {e}")

    # 3. Restore within exclusive server-wide maintenance lock
    with MAINTENANCE_LOCK:
        IS_MAINTENANCE_ACTIVE = True
        temp_rollback = None
        try:
            # Create safety snapshot of current target if it exists
            if tgt.exists():
                temp_rollback = tgt.with_suffix(".rollback_snapshot_tmp")
                try:
                    curr_conn = sqlite3.connect(str(tgt), timeout=10.0)
                    snap_conn = sqlite3.connect(str(temp_rollback))
                    with snap_conn:
                        curr_conn.backup(snap_conn, pages=100)
                    snap_conn.close()
                    curr_conn.close()
                except Exception:
                    temp_rollback = None

            # Execute online SQLite backup API restore (NO shutil.copy2 on live database)
            tgt.parent.mkdir(parents=True, exist_ok=True)
            target_conn = sqlite3.connect(str(tgt), timeout=30.0)
            backup_conn = sqlite3.connect(str(src))
            with target_conn:
                backup_conn.backup(target_conn, pages=100)
            backup_conn.close()

            # Verify restored target DB
            res = target_conn.execute("PRAGMA integrity_check").fetchall()
            fk_res = target_conn.execute("PRAGMA foreign_key_check").fetchall()
            target_conn.close()

            if len(res) != 1 or res[0][0] != "ok":
                raise ValueError(f"Post-restore integrity check failed on target: {res}")
            if len(fk_res) > 0:
                raise ValueError(f"Post-restore foreign key check failed on target: {fk_res}")

            # Successful restore: remove temp rollback snapshot
            if temp_rollback and temp_rollback.exists():
                try:
                    temp_rollback.unlink()
                except Exception:
                    pass

        except Exception as restore_err:
            # Atomic rollback to last known good state
            if temp_rollback and temp_rollback.exists():
                try:
                    snap_conn = sqlite3.connect(str(temp_rollback))
                    rb_tgt = sqlite3.connect(str(tgt), timeout=30.0)
                    with rb_tgt:
                        snap_conn.backup(rb_tgt, pages=100)
                    snap_conn.close()
                    rb_tgt.close()
                    temp_rollback.unlink()
                except Exception:
                    pass
            raise restore_err
        finally:
            IS_MAINTENANCE_ACTIVE = False

    return {
        "status": "SUCCESS",
        "restored_target": str(tgt),
        "restored_from": str(src),
        "size_bytes": tgt.stat().st_size,
        "restored_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": "sqlite3_online_backup_api"
    }


def rollback_database(target_db_path: str, backup_source_path: str) -> Dict[str, Any]:
    """Restore database from an atomic backup snapshot after verifying SQLite integrity and SHA-256."""
    try:
        return restore_database_safely(target_db_path, backup_source_path)
    except PermissionError as pe:
        raise ValueError(f"Backup validation failed: {pe}") from pe


def get_evidence_ledger(db: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Retrieve complete audit ledger of all point coordinate modifications joined with evidence references."""
    migrate_governance_schema(db)
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT pr.revision_id, pr.point_id, pr.revision_number, pr.change_type,
               pr.author, pr.reviewer, pr.verification_method, pr.uncertainty_radius_mm,
               pr.evidence_id, ec.title as evidence_title, ec.tier as evidence_tier,
               pr.notes, pr.created_utc
        FROM point_revisions pr
        LEFT JOIN evidence_catalog ec ON pr.evidence_id = ec.evidence_id
        ORDER BY pr.revision_id DESC
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "revision_id": r[0],
            "point_id": r[1],
            "revision_number": r[2],
            "change_type": r[3],
            "author": r[4],
            "reviewer": r[5] or "Not Specified",
            "verification_method": r[6] or "SURFACE_RAYCAST_INTERSECTION",
            "uncertainty_radius_mm": r[7] or 0.0,
            "evidence_id": r[8],
            "evidence_title": r[9],
            "evidence_tier": r[10],
            "notes": r[11],
            "created_utc": r[12]
        }
        for r in rows
    ]
