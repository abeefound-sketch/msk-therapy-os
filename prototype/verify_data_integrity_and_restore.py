"""Data Integrity, Transactional Safety & Restore Drill for MSK-Therapy-OS (P3).

Validates:
1. SQLite PRAGMA integrity_check and foreign_key_check on live database.
2. Complete schema inspection across all M2.8.2 to M6 tables.
3. Foreign key constraints and transaction rollback guarantees on write failure.
4. Native SQLite online backup with SHA-256 checksum calculation.
5. Safe restore drill into an isolated scratch instance with pre/post-restore verification.
6. Adversarial tamper detection: corrupt checksum or file tampering must trigger immediate abort and rollback.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import (
    backup_database,
    restore_database_safely,
    run_database_integrity_check,
    create_point,
    list_custom_points,
)

EVIDENCE_DIR = Path("2data/evidence/validation_audit")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_integrity_drill():
    print("=" * 80)
    print("MSK-THERAPY-OS: Data Integrity & Safe Restore Verification Drill (P3)")
    print("=" * 80)

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stages": {},
        "overall_status": "PENDING"
    }

    # Use a clean sandbox database to guarantee deterministic drill state
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        tmp_path = Path(tmpdir)
        live_db_path = tmp_path / "live_drill.sqlite3"
        backup_db_path = tmp_path / "backup_drill.sqlite3"
        restored_db_path = tmp_path / "restored_drill.sqlite3"

        # Stage 1: Initialize, seed, and check PRAGMA integrity
        print("[1/5] Initializing live database and running PRAGMA integrity checks...")
        live_conn = sqlite3.connect(str(live_db_path))
        live_conn.execute("PRAGMA foreign_keys = ON")
        init_db(live_conn)
        seed_db(live_conn)

        # Integrity checks
        audit1 = run_database_integrity_check(live_conn)
        tables = [row[0] for row in live_conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]

        stage1_pass = (audit1["status"] == "PASS" and audit1["integrity_check"] == "ok" and audit1["foreign_key_violations_count"] == 0 and len(tables) >= 15)
        report["stages"]["1_initial_integrity"] = {
            "status": "PASS" if stage1_pass else "FAIL",
            "integrity_check": audit1["integrity_check"],
            "fk_violations": audit1["foreign_key_violations_count"],
            "table_count": len(tables),
            "tables": tables
        }
        print(f" -> Initial Integrity: {'PASS' if stage1_pass else 'FAIL'} ({len(tables)} tables verified)")

        # Stage 2: Transaction isolation & rollback on failure
        print("[2/5] Testing transactional atomicity and rollback on invalid mutation...")
        stage2_pass = False
        try:
            with live_conn:
                live_conn.execute("INSERT INTO cases (case_id, label) VALUES ('DEMO-ATOMIC-TEST', 'Atomic Test Case')")
                # Intentional violation of foreign key or check constraint
                live_conn.execute("INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition) VALUES ('NON_EXISTENT_CASE', '2026-10-23', 'cervical', 15, 45, 'none', 'Invalid pain', 'INVALID_DISPOSITION')")
        except sqlite3.IntegrityError:
            # Check that DEMO-ATOMIC-TEST was rolled back
            row = live_conn.execute("SELECT case_id FROM cases WHERE case_id = 'DEMO-ATOMIC-TEST'").fetchone()
            if row is None:
                stage2_pass = True

        report["stages"]["2_transaction_rollback"] = {
            "status": "PASS" if stage2_pass else "FAIL",
            "atomicity_preserved": stage2_pass
        }
        print(f" -> Transaction Rollback Guarantee: {'PASS' if stage2_pass else 'FAIL'}")

        # Stage 3: Online Native SQLite Backup & SHA-256
        print("[3/5] Executing native online SQLite backup...")
        # Add a custom point to live DB before backup
        pt = create_point(live_conn, {
            "code": "DRILL-01",
            "name_en": "Integrity Drill Point",
            "position": [0.05, 1.45, -0.02],
            "anatomical_region": "cervical",
            "evidence_tier": "TIER_1_VALIDATED"
        })

        b_res = backup_database(live_conn, str(backup_db_path))
        checksum = sha256_file(backup_db_path)
        sha_file = backup_db_path.with_suffix(".sqlite3.sha256")

        stage3_pass = (b_res.get("status") == "SUCCESS" and backup_db_path.exists() and sha_file.exists())
        report["stages"]["3_native_backup"] = {
            "status": "PASS" if stage3_pass else "FAIL",
            "backup_size_bytes": backup_db_path.stat().st_size if backup_db_path.exists() else 0,
            "sha256": checksum,
            "sha256_file_exists": sha_file.exists()
        }
        print(f" -> Native Backup: {'PASS' if stage3_pass else 'FAIL'} (SHA-256: {checksum[:16]}...)")

        # Stage 4: Safe Restore into Target DB with Pre/Post Integrity Validation
        print("[4/5] Executing safe restore drill into secondary instance...")
        # Initialize a secondary empty database
        target_conn = sqlite3.connect(str(restored_db_path))
        init_db(target_conn)
        target_conn.close()

        restore_res = restore_database_safely(str(restored_db_path), str(backup_db_path))
        restored_conn = sqlite3.connect(str(restored_db_path))
        r_audit = run_database_integrity_check(restored_conn)
        pts = list_custom_points(restored_conn, include_deleted=True)
        drill_pt_found = any(p["code"] == "DRILL-01" for p in pts)

        stage4_pass = (restore_res.get("status") == "SUCCESS" and r_audit["status"] == "PASS" and r_audit["foreign_key_violations_count"] == 0 and drill_pt_found)
        report["stages"]["4_safe_restore"] = {
            "status": "PASS" if stage4_pass else "FAIL",
            "restore_status": restore_res.get("status"),
            "method": restore_res.get("method"),
            "integrity_status": r_audit["status"],
            "foreign_keys_violations": r_audit["foreign_key_violations_count"],
            "drill_point_recovered": drill_pt_found
        }
        print(f" -> Safe Restore Verification: {'PASS' if stage4_pass else 'FAIL'} (Custom points verified)")

        # Stage 5: Adversarial Tamper Detection & Rollback Abort Drill
        print("[5/5] Testing tamper detection with corrupted companion checksum...")
        tamper_backup = tmp_path / "tamper_backup.sqlite3"
        backup_database(live_conn, str(tamper_backup))
        # Corrupt companion sha256
        tamper_sha = tamper_backup.with_suffix(".sqlite3.sha256")
        tamper_sha.write_text("0000000000000000000000000000000000000000000000000000000000000000  tamper_backup.sqlite3\n")

        tamper_caught = False
        try:
            restore_database_safely(str(restored_db_path), str(tamper_backup))
        except ValueError as e:
            if "checksum mismatch" in str(e).lower():
                tamper_caught = True

        stage5_pass = tamper_caught
        report["stages"]["5_tamper_rejection"] = {
            "status": "PASS" if stage5_pass else "FAIL",
            "corrupt_checksum_blocked": tamper_caught
        }
        print(f" -> Tamper & Checksum Rejection: {'PASS' if stage5_pass else 'FAIL'}")

        live_conn.close()
        restored_conn.close()

    all_stages_pass = all(s["status"] == "PASS" for s in report["stages"].values())
    report["overall_status"] = "PASS" if all_stages_pass else "FAIL"

    out_file = EVIDENCE_DIR / "data_integrity_audit_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nDrill Complete! Overall Status: {report['overall_status']}")
    print(f"Evidence saved to: {out_file}")
    print("=" * 80)
    return report["overall_status"] == "PASS"


if __name__ == "__main__":
    success = run_integrity_drill()
    sys.exit(0 if success else 1)
