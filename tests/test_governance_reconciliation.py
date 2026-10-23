"""Unit and Integration Tests for Milestone M2.7 & M2.8: Atlas Data Governance and Acupoint Reconciliation."""
import json
import sqlite3
import tempfile
from pathlib import Path
import pytest

from msk_therapy_os.points import (
    CANONICAL_REFERENCE_CHECKSUMS,
    CANONICAL_MESH_HASH,
    CANONICAL_MODEL_ID,
    VALID_GOVERNANCE_STATUSES,
    init_points_tables,
    migrate_governance_schema,
    validate_governance_tier,
    verify_reference_dataset_integrity,
    run_database_integrity_check,
    backup_database,
    rollback_database,
    get_evidence_ledger,
    create_point,
    get_point,
    update_point,
    set_reference_override,
    get_reference_override,
    delete_reference_override,
    list_custom_points,
)


@pytest.fixture
def test_db():
    """Create an in-memory test database initialized with points schema."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    init_points_tables(conn)
    yield conn
    conn.close()


def test_immutable_reference_dataset_checksum():
    """Verify that canonical acupuncture_3d.json matches immutable SHA-256 hash."""
    result = verify_reference_dataset_integrity()
    assert result["is_valid"] is True, f"Reference dataset hash mismatch: {result}"
    assert result["status"] == "VALID"
    assert result["actual_sha256"] == CANONICAL_REFERENCE_CHECKSUMS["acupuncture_3d.json"]


def test_canonical_reconciliation_math():
    """Verify mathematical reconciliation: WHO 361 vs GB/T 12346 362 vs Dien Chan 4."""
    acu_file = Path("msk_therapy_os/static/atlas/data/acupuncture_3d.json")
    if not acu_file.exists():
        acu_file = Path(__file__).resolve().parent.parent / "msk_therapy_os/static/atlas/data/acupuncture_3d.json"
    assert acu_file.exists(), "acupuncture_3d.json must exist"

    with open(acu_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    points = data.get("points", {})
    dien_chan = data.get("dien_chan", [])

    # GB/T 12346 includes Yintang in Du Mai (GV24+), bringing total regular points to 362
    assert len(points) == 362, f"Expected 362 canonical points, found {len(points)}"
    assert "GV24+" in points, "GV24+ (Yintang) must exist in GB/T 12346 canonical points"
    assert points["GV24+"]["name_zh"] == "印堂"

    # Vietnamese Dien Chan reflex points
    assert len(dien_chan) == 4, f"Expected 4 Dien Chan points, found {len(dien_chan)}"

    # Check meridian counts: 361 WHO + 1 Yintang (GV24+) = 362
    gv_points = [k for k in points if k.startswith("GV")]
    assert len(gv_points) == 29, "GV must contain 28 WHO points + 1 national standard point (GV24+)"


def test_governance_tier_validation_rules():
    """Verify strict validation rules: GEOMETRY_VERIFIED vs ANATOMY_REVIEWED."""
    # 1. GEOMETRY_VERIFIED passes without reviewer
    validate_governance_tier("GEOMETRY_VERIFIED")
    validate_governance_tier("SURFACE_REGISTERED_FJ2810")
    validate_governance_tier("UNVERIFIED")

    # 2. ANATOMY_REVIEWED without reviewer raises ValueError
    with pytest.raises(ValueError, match="require a named qualified human reviewer"):
        validate_governance_tier("ANATOMY_REVIEWED", reviewer="", evidence_id="EVID-A-002")

    # 3. ANATOMY_REVIEWED with AI reviewer raises ValueError
    with pytest.raises(ValueError, match="Human clinical governance requires qualified practitioner review"):
        validate_governance_tier("ANATOMY_REVIEWED", reviewer="AI System", evidence_id="EVID-A-002")

    with pytest.raises(ValueError, match="Human clinical governance requires qualified practitioner review"):
        validate_governance_tier("ANATOMY_REVIEWED", reviewer="ChatGPT Bot", evidence_id="EVID-A-002")

    # 4. ANATOMY_REVIEWED without evidence raises ValueError
    with pytest.raises(ValueError, match="require an explicit evidence catalog reference"):
        validate_governance_tier("ANATOMY_REVIEWED", reviewer="Dr. Alice Smith, MD", evidence_id="")

    # 5. ANATOMY_REVIEWED with negative uncertainty raises ValueError
    with pytest.raises(ValueError, match="Uncertainty radius must be non-negative"):
        validate_governance_tier("ANATOMY_REVIEWED", reviewer="Dr. Alice Smith, MD", evidence_id="EVID-A-002", uncertainty_radius_mm=-2.0)

    # 6. Qualified human reviewer passes
    validate_governance_tier("ANATOMY_REVIEWED", reviewer="Dr. Alice Smith, MD / LAc", evidence_id="EVID-A-002", uncertainty_radius_mm=3.0)


def test_database_integrity_and_governance_audit(test_db):
    """Test full database integrity audit on clean database."""
    result = run_database_integrity_check(test_db)
    assert result["status"] == "PASS"
    assert result["integrity_check"] == "ok"
    assert result["foreign_key_violations_count"] == 0
    assert result["governance_compliance"]["is_compliant"] is True


def test_custom_point_with_governance_and_audit_trail(test_db):
    """Create custom point with qualified review and verify evidence ledger."""
    # Create point with GEOMETRY_VERIFIED
    pt_data = {
        "code": "CUST-GOV-01",
        "name_en": "Infra-Occipital Palpation Locus",
        "position": [0.035, 1.542, -0.075],
        "normal": [0.3, 0.4, -0.8],
        "registration_status": "GEOMETRY_VERIFIED",
        "review_status": "EXPERT_VERIFIED",
        "reviewer": "Dr. Robert Vance, PT",
        "evidence_id": "EVID-A-001",
        "uncertainty_radius_mm": 4.5,
        "notes": "Calibrated against C2-C3 articular pillar"
    }
    created = create_point(test_db, pt_data, author="Clinical Researcher")
    assert created["code"] == "CUST-GOV-01"

    # Verify ledger entry
    ledger = get_evidence_ledger(test_db)
    assert len(ledger) >= 1
    latest = ledger[0]
    assert latest["point_id"] == created["point_id"]
    assert latest["change_type"] == "CREATE"


def test_atomic_backup_and_rollback():
    """Verify atomic backup and rollback functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_db_path = Path(tmpdir) / "source.sqlite3"
        backup_db_path = Path(tmpdir) / "backup.sqlite3"

        # Create source db and insert data
        conn = sqlite3.connect(str(src_db_path))
        init_points_tables(conn)
        create_point(conn, {
            "code": "BACKUP-TEST-01",
            "name_en": "Pre-Backup Anchor",
            "position": [0.05, 1.45, -0.05]
        })
        conn.close()

        # Backup
        conn = sqlite3.connect(str(src_db_path))
        b_res = backup_database(conn, str(backup_db_path))
        conn.close()
        assert b_res["status"] == "SUCCESS"
        assert backup_db_path.exists()
        assert backup_db_path.stat().st_size > 0

        # Modify source db
        conn = sqlite3.connect(str(src_db_path))
        create_point(conn, {
            "code": "POST-BACKUP-02",
            "name_en": "Post-Backup Point",
            "position": [0.06, 1.46, -0.05]
        })
        pts_before_rollback = list_custom_points(conn)
        assert len(pts_before_rollback) == 2
        conn.close()

        # Rollback
        r_res = rollback_database(str(src_db_path), str(backup_db_path))
        assert r_res["status"] == "SUCCESS"

        # Verify restored state
        conn = sqlite3.connect(str(src_db_path))
        pts_after_rollback = list_custom_points(conn)
        assert len(pts_after_rollback) == 1
        assert pts_after_rollback[0]["code"] == "BACKUP-TEST-01"
        conn.close()
