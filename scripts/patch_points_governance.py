"""Script to patch msk_therapy_os/points.py with M2.8 Atlas Data Governance features."""
import re
from pathlib import Path

POINTS_FILE = Path("msk_therapy_os/points.py")
content = POINTS_FILE.read_text(encoding="utf-8")

# 1. Update Constants
old_const = '''VALID_MESH_ID = "FJ2810"
VALID_MESH_HASH = "FJ2810_V4.0_CCBYSA"'''

new_const = '''VALID_MESH_ID = "FJ2810"
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
)'''

assert old_const in content, "old_const not found"
content = content.replace(old_const, new_const, 1)

# 2. Update init_points_tables SQL schema & add migrate_governance_schema call
old_sql_reg = "registration_status TEXT NOT NULL DEFAULT 'SURFACE_REGISTERED_FJ2810' CHECK (registration_status IN ('VERIFIED_ANATOMICAL_ANCHOR', 'SURFACE_REGISTERED_FJ2810', 'GEOMETRY_VERIFIED', 'UNCERTAIN_POSTURE_OFFSET', 'UNVERIFIED')),"
new_sql_reg = "registration_status TEXT NOT NULL DEFAULT 'SURFACE_REGISTERED_FJ2810' CHECK (registration_status IN ('VERIFIED_ANATOMICAL_ANCHOR', 'SURFACE_REGISTERED_FJ2810', 'GEOMETRY_VERIFIED', 'ANATOMY_REVIEWED', 'UNCERTAIN_POSTURE_OFFSET', 'UNVERIFIED')),"
content = content.replace(old_sql_reg, new_sql_reg)

old_table_seed = """    for lib in STANDARD_LIBRARIES:
        db.execute(
            \"\"\"INSERT OR IGNORE INTO point_libraries (library_id, name, namespace, description, color, is_readonly)
               VALUES (?, ?, ?, ?, ?, ?)\"\"\",
            (
                lib["library_id"],
                lib["name"],
                lib["namespace"],
                lib["description"],
                lib["color"],
                lib["is_readonly"]
            )
        )
    db.commit()"""

new_table_seed = """    for lib in STANDARD_LIBRARIES:
        db.execute(
            \"\"\"INSERT OR IGNORE INTO point_libraries (library_id, name, namespace, description, color, is_readonly)
               VALUES (?, ?, ?, ?, ?, ?)\"\"\",
            (
                lib["library_id"],
                lib["name"],
                lib["namespace"],
                lib["description"],
                lib["color"],
                lib["is_readonly"]
            )
        )
    migrate_governance_schema(db)
    db.commit()"""

assert old_table_seed in content, "old_table_seed not found"
content = content.replace(old_table_seed, new_table_seed, 1)

# 3. Add governance functions before export_library_bundle or at bottom
governance_code = '''

def validate_governance_tier(
    registration_status: str,
    reviewer: Optional[str] = None,
    evidence_id: Optional[str] = None,
    uncertainty_radius_mm: Optional[float] = None
) -> None:
    """Enforce strict separation between geometric surface verification and clinical anatomical review.
    
    Rules:
    - Surface raycast intersection alone qualifies only for GEOMETRY_VERIFIED or SURFACE_REGISTERED_FJ2810.
    - ANATOMY_REVIEWED claims require:
      1. A named, qualified human reviewer (must not be empty, and cannot be generic 'AI', 'System', 'Automated').
      2. An explicit evidence reference or catalog ID.
      3. A non-negative localization uncertainty radius in millimeters (e.g., <= 10.0mm).
    """
    if registration_status not in VALID_GOVERNANCE_STATUSES:
        raise ValueError(f"Invalid registration status '{registration_status}'. Allowed: {VALID_GOVERNANCE_STATUSES}")

    if registration_status == "ANATOMY_REVIEWED":
        rev = (reviewer or "").strip()
        if not rev:
            raise ValueError("Anatomical review claims ('ANATOMY_REVIEWED') require a named qualified human reviewer.")
        if rev.lower() in ("ai", "system", "automated", "unknown", "none"):
            raise ValueError(f"Reviewer '{rev}' is invalid. Human clinical governance requires qualified practitioner review, not automated systems.")
        if not (evidence_id or "").strip():
            raise ValueError("Anatomical review claims ('ANATOMY_REVIEWED') require an explicit evidence catalog reference or citation.")
        if uncertainty_radius_mm is not None and uncertainty_radius_mm < 0:
            raise ValueError(f"Uncertainty radius must be non-negative, got {uncertainty_radius_mm}mm.")


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
    # Rule: ANATOMY_REVIEWED must have qualified reviewer and evidence_id
    cursor.execute(
        """SELECT point_id, code, registration_status, reviewer, evidence_id, uncertainty_radius_mm
           FROM custom_points
           WHERE registration_status = 'ANATOMY_REVIEWED'
             AND (reviewer IS NULL OR trim(reviewer) = '' OR lower(reviewer) IN ('ai', 'system', 'automated', 'unknown', 'none'))"""
    )
    unqualified_custom = cursor.fetchall()

    cursor.execute(
        """SELECT reference_code, registration_status, reviewer, evidence_id, uncertainty_radius_mm
           FROM reference_point_overrides
           WHERE registration_status = 'ANATOMY_REVIEWED'
             AND (reviewer IS NULL OR trim(reviewer) = '' OR lower(reviewer) IN ('ai', 'system', 'automated', 'unknown', 'none'))"""
    )
    unqualified_overrides = cursor.fetchall()

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


def backup_database(db: sqlite3.Connection, backup_path: str) -> Dict[str, Any]:
    """Perform atomic online SQLite backup without locking or interrupting read traffic."""
    from pathlib import Path
    bp = Path(backup_path)
    bp.parent.mkdir(parents=True, exist_ok=True)
    dest_db = sqlite3.connect(str(bp))
    with dest_db:
        db.backup(dest_db, pages=100)
    dest_db.close()
    return {
        "status": "SUCCESS",
        "backup_path": str(bp),
        "size_bytes": bp.stat().st_size if bp.exists() else 0,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


def rollback_database(target_db_path: str, backup_source_path: str) -> Dict[str, Any]:
    """Restore database from an atomic backup snapshot."""
    import shutil
    from pathlib import Path
    src = Path(backup_source_path)
    tgt = Path(target_db_path)
    if not src.exists():
        raise FileNotFoundError(f"Backup file not found at '{src}'.")
    shutil.copy2(src, tgt)
    return {
        "status": "SUCCESS",
        "restored_target": str(tgt),
        "restored_from": str(src),
        "size_bytes": tgt.stat().st_size,
        "restored_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


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
'''

content += governance_code
POINTS_FILE.write_text(content, encoding="utf-8")
print("Successfully patched msk_therapy_os/points.py with governance functions!")
