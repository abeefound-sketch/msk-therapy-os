"""Comprehensive tests for M6 De-identified Synthetic Cohort Research Dashboard."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.request import Request, urlopen

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.clinical_proms import (
    record_prom_response,
    record_adverse_event,
)
from msk_therapy_os.cohort_dashboard import (
    pseudonymize_case_id,
    get_cohort_summary,
    export_deidentified_cohort,
    COHORT_ANALYTICS_DISCLAIMER,
)
from msk_therapy_os.server import create_server


def seed_test_cohort_records(db):
    """Seed synthetic visits, PROMs, and adverse events for testing M6 cohort analytics."""
    with db:
        # Case 1: DEMO-NECK-001 (2 visits, NDI, 1 AE)
        c1_v1 = db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES ('DEMO-NECK-001', '2026-10-10', 'cervical', 7.0, 40.0, 'none', 'Baseline neck pain', 'TREAT_WITH_PRECAUTIONS')"""
        ).lastrowid
        c1_v2 = db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES ('DEMO-NECK-001', '2026-10-24', 'cervical', 3.0, 65.0, 'none', 'Followup neck pain', 'TREAT_WITH_PRECAUTIONS')"""
        ).lastrowid

        # Case 2: DEMO-LOWBACK-002 (2 visits, RMDQ)
        c2_v1 = db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES ('DEMO-LOWBACK-002', '2026-10-12', 'lumbar', 8.0, 35.0, 'none', 'Baseline lumbar pain', 'TREAT_WITH_PRECAUTIONS')"""
        ).lastrowid
        c2_v2 = db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES ('DEMO-LOWBACK-002', '2026-10-26', 'lumbar', 4.0, 55.0, 'none', 'Followup lumbar pain', 'TREAT_WITH_PRECAUTIONS')"""
        ).lastrowid

        # Case 3: DEMO-SHOULDER-003 (2 visits, QuickDASH)
        c3_v1 = db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES ('DEMO-SHOULDER-003', '2026-10-15', 'shoulder', 6.0, 100.0, 'none', 'Baseline shoulder', 'TREAT_WITH_PRECAUTIONS')"""
        ).lastrowid
        c3_v2 = db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES ('DEMO-SHOULDER-003', '2026-10-29', 'shoulder', 2.0, 150.0, 'none', 'Followup shoulder', 'TREAT_WITH_PRECAUTIONS')"""
        ).lastrowid

        # Case 4: DEMO-KNEE-004 (1 visit, no follow-up -> tests missingness)
        c4_v1 = db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES ('DEMO-KNEE-004', '2026-10-18', 'knee', 5.0, 110.0, 'none', 'Baseline knee only', 'TREAT_WITH_PRECAUTIONS')"""
        ).lastrowid

    # PROMs
    record_prom_response(db, case_id="DEMO-NECK-001", visit_id=c1_v1, prom_type="NDI", item_responses=[3] * 10)
    record_prom_response(db, case_id="DEMO-NECK-001", visit_id=c1_v2, prom_type="NDI", item_responses=[1] * 10)

    record_prom_response(db, case_id="DEMO-LOWBACK-002", visit_id=c2_v1, prom_type="RMDQ", item_responses=[1] * 12 + [0] * 12)
    record_prom_response(db, case_id="DEMO-LOWBACK-002", visit_id=c2_v2, prom_type="RMDQ", item_responses=[1] * 5 + [0] * 19)

    record_prom_response(db, case_id="DEMO-SHOULDER-003", visit_id=c3_v1, prom_type="QuickDASH", item_responses=[3] * 11)
    record_prom_response(db, case_id="DEMO-SHOULDER-003", visit_id=c3_v2, prom_type="QuickDASH", item_responses=[1] * 11)

    # Adverse Events
    record_adverse_event(
        db,
        case_id="DEMO-NECK-001",
        visit_id=c1_v1,
        event_category="post_session_soreness",
        ctcae_grade=1,
        symptom_description="Mild post-needling soreness lasting 4 hours",
        onset_utc="2026-10-10T14:00:00Z",
        resolution_status="resolved",
        action_taken="Reassurance and gentle active movement",
        reported_by="USR-ADMIN-01",
    )


class TestCohortDashboardUnit(unittest.TestCase):
    def setUp(self):
        self.db = open_db(":memory:")
        init_db(self.db)
        seed_db(self.db)
        seed_test_cohort_records(self.db)

    def tearDown(self):
        self.db.close()

    def test_pseudonymize_case_id(self):
        p1 = pseudonymize_case_id("DEMO-NECK-001")
        p2 = pseudonymize_case_id("DEMO-NECK-001")
        p3 = pseudonymize_case_id("DEMO-LOWBACK-002")
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        self.assertTrue(p1.startswith("SYNTH-"))
        self.assertNotIn("DEMO-NECK-001", p1)

    def test_get_cohort_summary_seeded(self):
        summary = get_cohort_summary(self.db)
        self.assertEqual(summary["total_cases"], 4)
        self.assertEqual(summary["total_visits"], 7)

        # Pain
        pain = summary["pain_analytics"]
        self.assertIsNotNone(pain["baseline_mean"])
        self.assertIsNotNone(pain["followup_mean"])
        self.assertIsNotNone(pain["mean_delta"])
        self.assertGreater(pain["mean_delta"], 0)
        self.assertEqual(pain["cases_evaluated"], 3)

        # ROM
        rom = summary["rom_analytics"]
        self.assertIsNotNone(rom["baseline_mean"])
        self.assertIsNotNone(rom["mean_delta"])
        self.assertEqual(rom["cases_evaluated"], 3)

        # PROMs
        proms = summary["prom_analytics"]
        self.assertIn("NDI", proms)
        self.assertIn("QuickDASH", proms)
        self.assertIn("RMDQ", proms)
        self.assertEqual(proms["NDI"]["cases_administered"], 1)
        self.assertEqual(proms["NDI"]["cases_paired_followup"], 1)
        self.assertGreater(proms["NDI"]["mean_disability_reduction_pct"], 0)

        # Adverse Events
        ae = summary["adverse_events_summary"]
        self.assertEqual(ae["total_events"], 1)
        self.assertEqual(ae["grade_distribution"][1], 1)
        self.assertEqual(ae["resolution_distribution"]["resolved"], 1)

        # Missingness
        miss = summary["missingness_report"]
        self.assertEqual(miss["total_cohort_cases"], 4)
        self.assertEqual(miss["cases_missing_followup"], 1)  # DEMO-KNEE-004 has single visit
        self.assertEqual(miss["case_retention_rate_pct"], 75.0)

        # Disclaimer
        self.assertEqual(summary["disclaimer"], COHORT_ANALYTICS_DISCLAIMER)

    def test_cohort_summary_empty_db(self):
        empty_db = open_db(":memory:")
        init_db(empty_db)
        summary = get_cohort_summary(empty_db)
        self.assertEqual(summary["total_cases"], 0)
        self.assertEqual(summary["total_visits"], 0)
        empty_db.close()

    def test_export_deidentified_json(self):
        content, mime = export_deidentified_cohort(self.db, export_format="json")
        self.assertIn("application/json", mime)
        data = json.loads(content)
        self.assertEqual(data["metadata"]["study_type"], "SYNTHETIC_COHORT_DEIDENTIFIED_RESEARCH_EXPORT")
        self.assertEqual(len(data["records"]), 4)
        for rec in data["records"]:
            self.assertTrue(rec["pseudo_case_id"].startswith("SYNTH-"))
            self.assertNotIn("DEMO-", rec["pseudo_case_id"])
            self.assertIn("region", rec)
            self.assertIn("visit_count", rec)

    def test_export_deidentified_csv(self):
        content, mime = export_deidentified_cohort(self.db, export_format="csv")
        self.assertIn("text/csv", mime)
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        self.assertEqual(len(rows), 4)
        for r in rows:
            self.assertTrue(r["pseudo_case_id"].startswith("SYNTH-"))
            self.assertNotIn("DEMO-", r["pseudo_case_id"])
            self.assertIn(r["region"], ("cervical", "lumbar", "shoulder", "knee"))


class TestCohortDashboardAPI(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.tmp_dir.name) / "test_m6.sqlite3"
        with open_db(self.db_path) as db:
            init_db(db)
            seed_db(db)
            seed_test_cohort_records(db)
        self.server = create_server(self.db_path, port=0)
        self.port = self.server.server_address[1]
        self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp_dir.cleanup()

    def test_api_cohort_summary_get(self):
        req = Request(f"http://127.0.0.1:{self.port}/api/cohort/summary")
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["total_cases"], 4)
            self.assertIn("pain_analytics", data)
            self.assertIn("missingness_report", data)
            self.assertIn("disclaimer", data)

    def test_api_cohort_export_json(self):
        req = Request(f"http://127.0.0.1:{self.port}/api/cohort/export?format=json")
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("application/json", resp.headers.get("Content-Type", ""))
            data = json.loads(resp.read().decode())
            self.assertEqual(len(data["records"]), 4)

    def test_api_cohort_export_csv(self):
        req = Request(f"http://127.0.0.1:{self.port}/api/cohort/export?format=csv")
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/csv", resp.headers.get("Content-Type", ""))
            body = resp.read().decode()
            self.assertIn("pseudo_case_id,region,visit_count", body)


if __name__ == "__main__":
    unittest.main()
