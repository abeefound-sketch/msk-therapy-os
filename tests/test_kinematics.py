"""Comprehensive tests for M4 Joint Kinematics Arcs and Frame Budgeting."""
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
from msk_therapy_os.kinematics import (
    classify_mobility,
    generate_arc_trajectory,
    record_kinematic_arc,
    list_kinematic_arcs,
    evaluate_frame_budget,
    PHYSIOLOGICAL_ROM_ENVELOPES,
)
from msk_therapy_os.server import create_server


class TestKinematicsUnit(unittest.TestCase):
    def setUp(self):
        self.db = open_db(":memory:")
        init_db(self.db)
        seed_db(self.db)

    def tearDown(self):
        self.db.close()

    def test_mobility_classification(self):
        # Normal cervical rotation is 80 deg.
        # 40 deg -> 50% -> HYPOMOBILITY
        status, pct = classify_mobility(40.0, 80.0)
        self.assertEqual(status, "HYPOMOBILITY")
        self.assertEqual(pct, 50.0)

        # 76 deg -> 95% -> NORMAL_MOBILITY
        status_norm, pct_norm = classify_mobility(76.0, 80.0)
        self.assertEqual(status_norm, "NORMAL_MOBILITY")
        self.assertEqual(pct_norm, 95.0)

        # 96 deg -> 120% -> HYPERMOBILITY
        status_hyper, pct_hyper = classify_mobility(96.0, 80.0)
        self.assertEqual(status_hyper, "HYPERMOBILITY")
        self.assertEqual(pct_hyper, 120.0)

    def test_arc_trajectory_generation(self):
        pts = generate_arc_trajectory((0.0, 0.0), 100.0, 0.0, 90.0, 10)
        self.assertEqual(len(pts), 10)
        self.assertEqual(pts[0]["angle_deg"], 0.0)
        self.assertAlmostEqual(pts[0]["x"], 100.0, places=2)
        self.assertAlmostEqual(pts[0]["y"], 0.0, places=2)
        self.assertEqual(pts[-1]["angle_deg"], 90.0)
        self.assertAlmostEqual(pts[-1]["x"], 0.0, places=2)
        self.assertAlmostEqual(pts[-1]["y"], 100.0, places=2)

    def test_record_kinematic_arc_lifecycle(self):
        arc = record_kinematic_arc(
            self.db,
            case_id="DEMO-NECK-001",
            visit_id=None,
            joint_name="cervical_rotation",
            measured_rom_deg=48.0,
        )
        self.assertTrue(arc["arc_id"].startswith("KARC-"))
        self.assertEqual(arc["mobility_status"], "HYPOMOBILITY")
        self.assertEqual(arc["percentage_of_normal"], 60.0)
        self.assertEqual(len(arc["arc_points"]), 20)

        arcs = list_kinematic_arcs(self.db, "DEMO-NECK-001")
        self.assertEqual(len(arcs), 1)
        self.assertEqual(arcs[0]["joint_name"], "cervical_rotation")

        # Reject real patient ID
        with self.assertRaises(ValueError):
            record_kinematic_arc(
                self.db,
                case_id="REAL-PATIENT-123",
                visit_id=None,
                joint_name="cervical_rotation",
                measured_rom_deg=48.0,
            )

    def test_evaluate_frame_budget(self):
        # 16.6ms -> 60 FPS -> within 30 FPS budget (33.3ms)
        b60 = evaluate_frame_budget(16.6, 30.0)
        self.assertTrue(b60["is_within_budget"])
        self.assertGreaterEqual(b60["effective_fps"], 60.0)

        # 45.0ms -> ~22 FPS -> exceeds budget
        b22 = evaluate_frame_budget(45.0, 30.0)
        self.assertFalse(b22["is_within_budget"])
        self.assertLess(b22["effective_fps"], 30.0)


class TestKinematicsHTTP(unittest.TestCase):
    def test_kinematics_endpoints_and_readonly(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = str(Path(tmp) / "demo.sqlite3")
            server = create_server(db_path, port=0)
            t = Thread(target=server.serve_forever, daemon=True)
            t.start()
            url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                # 1. Envelopes catalog
                with urlopen(f"{url}/api/kinematics/envelopes", timeout=5) as res:
                    envs = json.load(res)
                    self.assertIn("cervical_rotation", envs)
                    self.assertIn("shoulder_abduction", envs)

                # 2. Evaluate budget POST (stateless computation)
                req_b = Request(
                    f"{url}/api/kinematics/evaluate-budget",
                    data=json.dumps({"frame_time_ms": 20.0, "target_fps": 30.0}).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req_b, timeout=5) as res:
                    bud = json.load(res)
                    self.assertTrue(bud["is_within_budget"])

                # 3. Create arc without auth -> 401
                req_a = Request(
                    f"{url}/api/kinematics/arcs",
                    data=json.dumps({"case_id": "DEMO-NECK-001", "joint_name": "cervical_rotation", "measured_rom_deg": 50.0}).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with self.assertRaises(HTTPError) as exc:
                    urlopen(req_a, timeout=5)
                self.assertEqual(exc.exception.code, 401)

                # 4. Under MSK_PUBLIC_DEMO_READONLY=1 -> 403 Forbidden
                with patch.dict("os.environ", {"MSK_PUBLIC_DEMO_READONLY": "1"}):
                    with self.assertRaises(HTTPError) as exc_ro:
                        urlopen(req_a, timeout=5)
                    self.assertEqual(exc_ro.exception.code, 403)

            finally:
                server.shutdown()
                server.server_close()
                t.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
