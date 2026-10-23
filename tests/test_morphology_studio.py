"""Comprehensive tests for M2.12 Three-Photo Patient Morphology Studio."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.morphology_studio import (
    create_avatar,
    get_avatar,
    list_avatars,
    update_avatar_params,
    record_morphology_observation,
    list_morphology_observations,
    validate_morphology_params,
)
from msk_therapy_os.server import create_server


class TestMorphologyStudioUnit(unittest.TestCase):
    def setUp(self):
        self.db = open_db(":memory:")
        init_db(self.db)
        seed_db(self.db)

    def tearDown(self):
        self.db.close()

    def test_validate_morphology_params(self):
        valid = {
            "height_cm": 172.5,
            "weight_kg": 68.0,
            "chest_circ_cm": 95.0,
            "waist_circ_cm": 80.0,
            "hip_circ_cm": 98.0,
            "abdomen_prominence": 0.5,
        }
        res = validate_morphology_params(valid)
        self.assertEqual(res["height_cm"], 172.5)
        self.assertEqual(res["waist_circ_cm"], 80.0)

        # Height too low
        with self.assertRaises(ValueError):
            validate_morphology_params({"height_cm": 50.0})

        # Waist circumference physiologically impossible
        with self.assertRaises(ValueError):
            validate_morphology_params({"waist_circ_cm": 15.0})

    def test_avatar_lifecycle_and_versioning(self):
        # 1. Version 1 for DEMO-NECK-001
        av1 = create_avatar(
            self.db,
            case_id="DEMO-NECK-001",
            title="Initial Intake Avatar Day 1",
            height_cm=175.0,
            weight_kg=72.0,
            chest_circ_cm=98.0,
            waist_circ_cm=84.0,
            hip_circ_cm=100.0,
        )
        self.assertTrue(av1["avatar_id"].startswith("AVTR-"))
        self.assertEqual(av1["version_num"], 1)
        self.assertIn("APPROXIMATE_EXTERNAL_SURFACE_ONLY", av1["disclaimer"])
        self.assertEqual(av1["model_space"], "PATIENT_SURFACE_APPROXIMATE_V1")

        # 2. Version 2 for DEMO-NECK-001
        av2 = create_avatar(
            self.db,
            case_id="DEMO-NECK-001",
            title="Follow-up Day 14 Avatar",
            height_cm=175.0,
            weight_kg=71.2,
            chest_circ_cm=98.0,
            waist_circ_cm=82.5,
            hip_circ_cm=99.0,
        )
        self.assertEqual(av2["version_num"], 2)

        # 3. List avatars
        case_avatars = list_avatars(self.db, "DEMO-NECK-001")
        self.assertEqual(len(case_avatars), 2)
        self.assertEqual(case_avatars[0]["version_num"], 2)  # descending order

        # 4. Reject real patient ID
        with self.assertRaises(ValueError):
            create_avatar(
                self.db,
                case_id="PATIENT-REAL-099",
                title="Prohibited",
                height_cm=170.0,
            )

    def test_update_draft_avatar_and_lock_protection(self):
        av = create_avatar(
            self.db,
            case_id="DEMO-NECK-001",
            title="Draft Adjustment",
            height_cm=168.0,
            waist_circ_cm=75.0,
        )
        # Update waist and shoulder
        upd = update_avatar_params(
            self.db,
            av["avatar_id"],
            {"waist_circ_cm": 73.5, "shoulder_width_cm": 42.0},
            notes="Technician adjusted waist to match calibrated tape measurement",
        )
        self.assertEqual(upd["waist_circ_cm"], 73.5)
        self.assertEqual(upd["params"]["shoulder_width_cm"], 42.0)
        self.assertIn("calibrated tape", upd["notes"])

        # Lock avatar and verify modification is rejected
        self.db.execute("UPDATE morphology_avatars SET status = 'locked' WHERE avatar_id = ?", (av["avatar_id"],))
        with self.assertRaises(PermissionError):
            update_avatar_params(self.db, av["avatar_id"], {"waist_circ_cm": 72.0})

    def test_record_morphology_observation(self):
        av = create_avatar(
            self.db,
            case_id="DEMO-NECK-001",
            title="Day 1 Baseline",
            height_cm=170.0,
        )
        self.db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("DEMO-NECK-001", "2026-10-23", "neck", 3, 42.0, "none", "Morphology note", "TREAT_WITH_PRECAUTIONS"),
        )
        visit_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]

        obs = record_morphology_observation(
            self.db,
            avatar_id=av["avatar_id"],
            case_id="DEMO-NECK-001",
            visit_id=visit_id,
            body_region="cervicothoracic_junction",
            observation_type="asymmetry",
            severity=4,
            findings_summary="Mild right shoulder elevation with 1.5 cm apparent cranial displacement",
            operator_notes="Visual inspection confirmed by plumbline and anatomical landmarker",
        )
        self.assertTrue(obs["observation_id"].startswith("MOBS-"))

        all_obs = list_morphology_observations(self.db, av["avatar_id"])
        self.assertEqual(len(all_obs), 1)
        self.assertEqual(all_obs[0]["body_region"], "cervicothoracic_junction")
        self.assertEqual(all_obs[0]["severity"], 4)


class TestMorphologyStudioHTTP(unittest.TestCase):
    def test_morphology_endpoints_and_readonly(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = str(Path(tmp) / "demo.sqlite3")
            server = create_server(db_path, port=0)
            t = Thread(target=server.serve_forever, daemon=True)
            t.start()
            url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                # 1. List avatars for DEMO-NECK-001
                with urlopen(f"{url}/api/morphology/avatars?case_id=DEMO-NECK-001", timeout=5) as res:
                    avatars = json.load(res)
                    self.assertIsInstance(avatars, list)

                # 2. Create avatar without auth -> 401
                req = Request(
                    f"{url}/api/morphology/avatars",
                    data=json.dumps({"case_id": "DEMO-NECK-001", "title": "Test Avatar", "height_cm": 170.0}).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with self.assertRaises(HTTPError) as exc:
                    urlopen(req, timeout=5)
                self.assertEqual(exc.exception.code, 401)

                # 3. Under MSK_PUBLIC_DEMO_READONLY=1 -> 403 Forbidden
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
