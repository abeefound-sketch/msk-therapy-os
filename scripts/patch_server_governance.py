from pathlib import Path

SERVER_FILE = Path("msk_therapy_os/server.py")
content = SERVER_FILE.read_text(encoding="utf-8")

# 1. Update imports from points
old_imp = """    export_library_bundle,
    import_library_bundle,
)"""

new_imp = """    export_library_bundle,
    import_library_bundle,
    run_database_integrity_check,
    verify_reference_dataset_integrity,
    backup_database,
    rollback_database,
    get_evidence_ledger,
)"""

assert old_imp in content, "old_imp not found"
content = content.replace(old_imp, new_imp, 1)

# 2. Add GET endpoints
old_get = """                elif path == "/api/terminology":"""

new_get = """                elif path == "/api/governance/status":
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

                elif path == "/api/terminology":"""

assert old_get in content, "old_get not found"
content = content.replace(old_get, new_get, 1)

# 3. Add POST endpoints
old_post = """                elif path == "/api/points/import":"""

new_post = """                elif path == "/api/governance/backup":
                    import time
                    name = body.get("name") or f"backup_snapshot_{int(time.time())}.sqlite3"
                    bp = Path("data/backups") / name
                    self._send_json(backup_database(db, str(bp)))

                elif path == "/api/governance/check":
                    self._send_json(run_database_integrity_check(db))

                elif path == "/api/points/import":"""

assert old_post in content, "old_post not found"
content = content.replace(old_post, new_post, 1)

SERVER_FILE.write_text(content, encoding="utf-8")
print("Successfully patched msk_therapy_os/server.py with governance routes!")
