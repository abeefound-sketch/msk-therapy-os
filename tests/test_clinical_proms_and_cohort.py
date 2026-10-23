"""Comprehensive unit and integration tests for M3 Clinical PROMs, CTCAE Adverse Events, and FHIR Bundles."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from msk_therapy_os.clinical_proms import (
    calculate_ndi_score,
    calculate_quickdash_score,
    calculate_rmdq_score,
    record_prom_response,
    list_prom_responses,
    record_adverse_event,
    list_adverse_events,
    PROM_CATALOG,
)
from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.server import create_server
from msk_therapy_os.tracking import export_case_fhir


class TestClinicalPROMsAndCohortUnit(unittest.TestCase):
    def setUp(self):
        self.db = open_db(":memory:")
        init_db(self.db)
        seed_db(self.db)

    def tearDown(self):
        self.db.close()

    def test_ndi_scoring_algorithm(self):
        # 10 items with score 2 each -> raw: 20, pct: 40.0% -> Moderate disability
        res = calculate_ndi_score([2] * 10)
        self.assertEqual(res["raw_score"], 20)
        self.assertEqual(res["percentage_score"], 40.0)
        self.assertEqual(res["interpretation"], "Moderate disability")

        # Rejects fewer than 10 items
        with self.assertRaises(ValueError):
            calculate_ndi_score([1, 2, 3])

        # Rejects out of bound item score
        with self.assertRaises(ValueError):
            calculate_ndi_score([6] + [1] * 9)

    def test_quickdash_scoring_algorithm(self):
        # 11 items with score 3 each -> mean: 3.0 -> ((3 - 1) * 25) = 50.0%
        res = calculate_quickdash_score([3] * 11)
        self.assertEqual(res["raw_score"], 33)
        self.assertEqual(res["percentage_score"], 50.0)

        # Rejects item score 0 (valid range is 1-5)
        with self.assertRaises(ValueError):
            calculate_quickdash_score([0] + [2] * 10)

    def test_rmdq_scoring_algorithm(self):
        # 24 binary items, 12 checked -> 12/24 = 50.0%
        res = calculate_rmdq_score([1] * 12 + [0] * 12)
        self.assertEqual(res["raw_score"], 12)
        self.assertEqual(res["percentage_score"], 50.0)

        # Rejects non-binary values
        with self.assertRaises(ValueError):
            calculate_rmdq_score([2] + [0] * 23)

    def test_record_prom_lifecycle(self):
        rec = record_prom_response(
            self.db,
            case_id="DEMO-NECK-001",
            visit_id=None,
            prom_type="NDI",
            item_responses=[1] * 10,  # 10/50 = 20% Mild disability
        )
        self.assertTrue(rec["prom_id"].startswith("PROM-"))
        self.assertEqual(rec["percentage_score"], 20.0)
        self.assertEqual(rec["interpretation"], "Mild disability")

        history = list_prom_responses(self.db, "DEMO-NECK-001")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["prom_type"], "NDI")

    def test_record_ctcae_adverse_event(self):
        ae = record_adverse_event(
            self.db,
            case_id="DEMO-NECK-001",
            visit_id=None,
            event_category="manual_therapy_reaction",
            ctcae_grade=1,
            symptom_description="Transient mild soreness in suboccipital region lasting 3 hours post-session",
            onset_utc="2026-10-23T11:00:00Z",
            resolution_status="resolved",
            action_taken="Patient advised on hydration and gentle active cervical retraction",
            reported_by="USR-ADMIN-01",
        )
        self.assertTrue(ae["event_id"].startswith("AE-"))
        self.assertEqual(ae["ctcae_grade"], 1)

        ae_list = list_adverse_events(self.db, "DEMO-NECK-001")
        self.assertEqual(len(ae_list), 1)
        self.assertIn("Grade 1", ae_list[0]["grade_description"])

    def test_fhir_r4_bundle_includes_prom_and_adverse_event(self):
        # 1. Add visit
        self.db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("DEMO-NECK-001", "2026-10-23", "neck", 5, 38.0, "none", "FHIR test visit", "TREAT_WITH_PRECAUTIONS"),
        )
        visit_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # 2. Record PROM
        record_prom_response(
            self.db,
            case_id="DEMO-NECK-001",
            visit_id=visit_id,
            prom_type="NDI",
            item_responses=[2] * 10,
        )

        # 3. Record Adverse Event
        record_adverse_event(
            self.db,
            case_id="DEMO-NECK-001",
            visit_id=visit_id,
            event_category="post_session_soreness",
            ctcae_grade=1,
            symptom_description="Mild tenderness",
            onset_utc="2026-10-23T12:00:00Z",
            resolution_status="resolved",
            action_taken="Rest",
            reported_by="USR-ADMIN-01",
        )

        # 4. Generate FHIR Bundle
        bundle = export_case_fhir(self.db, "DEMO-NECK-001")
        resources = [e["resource"] for e in bundle["entry"]]
        resource_types = [r["resourceType"] for r in resources]

        self.assertIn("Patient", resource_types)
        self.assertIn("Encounter", resource_types)
        self.assertIn("Observation", resource_types)
        self.assertIn("AdverseEvent", resource_types)

        # Verify PROM Survey observation
        prom_obs = next(r for r in resources if r["resourceType"] == "Observation" and r.get("id", "").startswith("prom-"))
        self.assertEqual(prom_obs["category"][0]["coding"][0]["code"], "survey")
        self.assertEqual(prom_obs["valueQuantity"]["value"], 40.0)

        # Verify CTCAE AdverseEvent
        ae_res = next(r for r in resources if r["resourceType"] == "AdverseEvent")
        self.assertIn("Grade-1", ae_res["severity"]["coding"][0]["code"])


class TestClinicalPROMsHTTP(unittest.TestCase):
    def test_prom_endpoints_and_readonly(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = str(Path(tmp) / "demo.sqlite3")
            server = create_server(db_path, port=0)
            t = Thread(target=server.serve_forever, daemon=True)
            t.start()
            url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                # 1. Catalog
                with urlopen(f"{url}/api/proms/catalog", timeout=5) as res:
                    cat = json.load(res)
                    self.assertIn("NDI", cat)
                    self.assertIn("QuickDASH", cat)

                # 2. List PROMs for DEMO-NECK-001
                with urlopen(f"{url}/api/proms/responses?case_id=DEMO-NECK-001", timeout=5) as res:
                    items = json.load(res)
                    self.assertIsInstance(items, list)

                # 3. Create PROM without auth -> 401
                req = Request(
                    f"{url}/api/proms/responses",
                    data=json.dumps({"case_id": "DEMO-NECK-001", "prom_type": "NDI", "item_responses": [1]*10}).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with self.assertRaises(HTTPError) as exc:
                    urlopen(req, timeout=5)
                self.assertEqual(exc.exception.code, 401)

                # 4. Under MSK_PUBLIC_DEMO_READONLY=1 -> 403 Forbidden
                with patch.dict("os.environ", {"MSK_PUBLIC_DEMO_READONLY": "1"}):
                    with self.assertRaises(HTTPError) as exc_ro:
                        urlopen(req, timeout=5)
                    self.assertEqual(exc_ro.exception.code, 403)

            finally:
                server.shutdown()
                server.server_close()
                t.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
