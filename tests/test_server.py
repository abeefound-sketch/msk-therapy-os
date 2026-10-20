"""Automated test suite for MSK-Therapy-OS Milestone M2 Body-Map HTTP Server."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

from msk_therapy_os.db import init_db, open_db, seed_db
from msk_therapy_os.server import create_server


class TestWebServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = str(Path(cls.temp_dir.name) / "test_web.sqlite3")

        with open_db(cls.db_path) as db:
            init_db(db)
            seed_db(db)

        # Port 0 lets OS allocate an available port
        cls.server = create_server(cls.db_path, host="127.0.0.1", port=0)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1.0)
        time.sleep(0.1)
        try:
            cls.temp_dir.cleanup()
        except PermissionError:
            pass

    def test_get_index_html(self):
        req = urllib.request.Request(f"{self.base_url}/")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode("utf-8")
            self.assertIn("MSK-Therapy-OS", html)
            self.assertIn("SYNTHETIC EDUCATIONAL PROOF OF CONCEPT", html)
            self.assertIn("body-svg", html)

    def test_get_api_cases(self):
        req = urllib.request.Request(f"{self.base_url}/api/cases")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIsInstance(data, list)
            case_ids = [c["case_id"] for c in data]
            self.assertIn("DEMO-NECK-001", case_ids)

    def test_get_api_case_details(self):
        req = urllib.request.Request(f"{self.base_url}/api/case?case_id=DEMO-NECK-001")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["case_id"], "DEMO-NECK-001")
            self.assertIsNotNone(data["intake"])
            self.assertEqual(data["intake"]["primary_region"], "neck")

    def test_get_api_anatomy(self):
        req = urllib.request.Request(f"{self.base_url}/api/anatomy?region=neck")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            structs = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(len(structs) >= 2)
            cerv = [s for s in structs if s["structure_id"] == "STR-CERV-001"][0]
            self.assertEqual(cerv["bodyparts3d_id"], "FJ9914")
            self.assertIn("FJ9914", cerv["atlas_url"])

    def test_get_api_evidence(self):
        req = urllib.request.Request(f"{self.base_url}/api/evidence?tier=1")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            items = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(len(items) >= 3)
            self.assertTrue(all(item["tier"] == 1 for item in items))

    def test_get_api_questionnaires(self):
        req = urllib.request.Request(f"{self.base_url}/api/questionnaires?region=neck")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            qs = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(len(qs) >= 2)

    def test_post_screen_safety(self):
        payload = json.dumps({
            "flag": "progressive_weakness",
            "modality": "manual_massage",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/screen-safety",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["disposition"], "STOP_AND_REFER")
            self.assertFalse(data["is_safe_to_proceed"])

    def test_post_visit_and_soap_lifecycle(self):
        # 1. Post Visit
        visit_payload = json.dumps({
            "case": "DEMO-NECK-001",
            "when": "2026-10-20",
            "pain": 4,
            "rom": 46.0,
            "region": "neck",
            "flag": "none",
            "note": "Web test visit",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/visit",
            data=visit_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            out = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(out["disposition"], "DOCUMENT_ONLY")

        # 2. Post SOAP Note
        soap_payload = json.dumps({
            "visit_id": 1,
            "subjective": "Neck soreness after desk work.",
            "objective": "Cervical lateral flexion 35 deg.",
            "assessment": "Postural muscle discomfort hypothesis.",
            "plan": "Ergonomics education and active pauses.",
            "role": "student",
        }).encode("utf-8")
        req_soap = urllib.request.Request(
            f"{self.base_url}/api/soap",
            data=soap_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_soap) as resp:
            self.assertEqual(resp.status, 200)
            soap_res = json.loads(resp.read().decode("utf-8"))
            soap_id = soap_res["soap_id"]
            self.assertGreater(soap_id, 0)

        # 3. Supervisory Review
        review_payload = json.dumps({
            "soap_id": soap_id,
            "reviewer": "Dr. Clinical Mentor",
            "role": "reviewer",
            "decision": "APPROVED",
            "feedback": "Clear educational note.",
        }).encode("utf-8")
        req_rev = urllib.request.Request(
            f"{self.base_url}/api/review-soap",
            data=review_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_rev) as resp:
            self.assertEqual(resp.status, 200)
            rev_res = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(rev_res["decision"], "APPROVED")

    def test_get_report(self):
        req = urllib.request.Request(f"{self.base_url}/api/report?case_id=DEMO-NECK-001")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            text = resp.read().decode("utf-8")
            self.assertIn("SYNTHETIC CLINICAL LEARNING REPORT", text)
            self.assertIn("DEMO-NECK-001", text)

    def test_get_atlas_html(self):
        req = urllib.request.Request(f"{self.base_url}/atlas/")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
            html = resp.read().decode("utf-8")
            self.assertIn("Open Anatomy Atlas", html)
            self.assertIn('id="viewport"', html)

    def test_get_atlas_status(self):
        for endpoint in ["/atlas/api/status", "/api/status"]:
            req = urllib.request.Request(f"{self.base_url}{endpoint}")
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                status = json.loads(resp.read().decode("utf-8"))
                self.assertIn("ready", status)
                self.assertTrue(status["ready"])
                self.assertEqual(status["active"], "bp3d40")
                self.assertIn("counts", status)
                self.assertGreaterEqual(status["counts"]["elements"], 1000)

    def test_get_atlas_data_index(self):
        for endpoint in ["/atlas/data/index.json", "/data/index.json"]:
            req = urllib.request.Request(f"{self.base_url}{endpoint}")
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                idx = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(idx["name"], "BodyParts3D")
                self.assertEqual(idx["version"], "4.0")
                self.assertIn("concepts", idx)
                self.assertGreater(len(idx["concepts"]), 2000)

    def test_get_atlas_assets(self):
        for asset, expected_type in [("/atlas/app.js", "javascript"), ("/atlas/style.css", "css")]:
            req = urllib.request.Request(f"{self.base_url}{asset}")
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn(expected_type, resp.headers.get("Content-Type", ""))


if __name__ == "__main__":
    unittest.main()
