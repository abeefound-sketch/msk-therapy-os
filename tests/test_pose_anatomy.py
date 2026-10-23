"""Comprehensive tests for M2.11 Pose-to-Anatomy Explorer."""
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
from msk_therapy_os.pose_anatomy import (
    calculate_joint_angle,
    estimate_pose_actions,
    create_pose_study,
    get_pose_study,
    list_pose_studies,
    update_landmarks,
    record_pose_observation,
    list_pose_observations,
    CURATED_ACTION_MUSCLES,
)
from msk_therapy_os.server import create_server


class TestPoseAnatomyUnit(unittest.TestCase):
    def setUp(self):
        self.db = open_db(":memory:")
        init_db(self.db)
        seed_db(self.db)

    def tearDown(self):
        self.db.close()

    def test_calculate_joint_angle(self):
        # 90-degree right angle: (0, 1) -> (0, 0) -> (1, 0)
        deg = calculate_joint_angle((0.0, 1.0), (0.0, 0.0), (1.0, 0.0))
        self.assertIsNotNone(deg)
        self.assertAlmostEqual(deg, 90.0, places=2)

        # Straight line 180 degrees: (-1, 0) -> (0, 0) -> (1, 0)
        deg_straight = calculate_joint_angle((-1.0, 0.0), (0.0, 0.0), (1.0, 0.0))
        self.assertIsNotNone(deg_straight)
        self.assertAlmostEqual(deg_straight, 180.0, places=2)

        # Degenerate coincident points: returns None
        deg_degen = calculate_joint_angle((0.0, 0.0), (0.0, 0.0), (1.0, 0.0))
        self.assertIsNone(deg_degen)

    def test_estimate_pose_actions_and_abstention(self):
        # 1. Full high-confidence landmarks for left shoulder abduction
        valid_landmarks = {
            23: {"u": 0.5, "v": 0.8, "confidence": 0.9},   # left hip
            11: {"u": 0.5, "v": 0.3, "confidence": 0.95},  # left shoulder
            13: {"u": 0.2, "v": 0.3, "confidence": 0.9},   # left elbow (abducted ~90 deg)
            0:  {"u": 0.5, "v": 0.1, "confidence": 0.9},   # nose
            12: {"u": 0.6, "v": 0.3, "confidence": 0.9},   # right shoulder
        }
        estimates = estimate_pose_actions(valid_landmarks)
        left_shld = next((e for e in estimates if e["action"] == "shoulder_abduction" and e["side"] == "left"), None)
        self.assertIsNotNone(left_shld)
        self.assertEqual(left_shld["status"], "ESTIMATED_MODEL")
        self.assertGreater(left_shld["estimated_angle_deg"], 80.0)
        self.assertTrue(any(m["name"] == "Deltoid (middle)" for m in left_shld["candidate_muscles"]))

        # 2. Occluded / low-confidence landmark -> ABSTAIN
        occluded_landmarks = {
            23: {"u": 0.5, "v": 0.8, "confidence": 0.2},   # low confidence hip
            11: {"u": 0.5, "v": 0.3, "confidence": 0.95},
            13: {"u": 0.2, "v": 0.3, "confidence": 0.9},
        }
        occluded_estimates = estimate_pose_actions(occluded_landmarks)
        left_shld_occ = next((e for e in occluded_estimates if e["action"] == "shoulder_abduction" and e["side"] == "left"), None)
        self.assertIsNotNone(left_shld_occ)
        self.assertEqual(left_shld_occ["status"], "ABSTAIN")
        self.assertIsNone(left_shld_occ["estimated_angle_deg"])

    def test_pose_study_lifecycle_and_manual_override(self):
        raw_lms = [
            {"index": 0, "u": 0.5, "v": 0.1, "confidence": 0.9},
            {"index": 11, "u": 0.45, "v": 0.25, "confidence": 0.85},
            {"index": 12, "u": 0.55, "v": 0.25, "confidence": 0.85},
            {"index": 13, "u": 0.35, "v": 0.4, "confidence": 0.7},
            {"index": 23, "u": 0.47, "v": 0.6, "confidence": 0.9},
        ]
        study = create_pose_study(
            self.db,
            case_id="DEMO-NECK-001",
            title="Arm elevation drill Day 1",
            camera_view="front",
            image_asset="/data/demo_pose_01.png",
            image_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            raw_landmarks=raw_lms,
        )
        self.assertTrue(study["study_id"].startswith("PSTD-"))
        self.assertEqual(len(study["landmarks"]), 5)

        # Non-DEMO case rejected
        with self.assertRaises(ValueError):
            create_pose_study(
                self.db,
                case_id="PATIENT-REAL-001",
                title="Invalid",
                camera_view="front",
                image_asset="x",
                image_sha256="y",
                raw_landmarks=[],
            )

        # Coordinate out of bounds rejected
        with self.assertRaises(ValueError):
            create_pose_study(
                self.db,
                case_id="DEMO-NECK-001",
                title="Invalid coords",
                camera_view="front",
                image_asset="x",
                image_sha256="y",
                raw_landmarks=[{"index": 0, "u": 1.5, "v": 0.5, "confidence": 0.9}],
            )

        # Apply manual override to landmark 13 (elbow)
        updated = update_landmarks(
            self.db,
            study["study_id"],
            [{"index": 13, "u": 0.32, "v": 0.38, "confidence": 1.0}],
        )
        lm13 = next(lm for lm in updated["landmarks"] if lm["index"] == 13)
        self.assertEqual(lm13["u"], 0.32)
        self.assertEqual(lm13["v"], 0.38)
        self.assertTrue(lm13["is_manual_override"])

    def test_record_pose_symptom_observation(self):
        self.db.execute(
            """INSERT INTO visits (case_id, visit_date, region, pain, rom_deg, flag, note, disposition)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("DEMO-NECK-001", "2026-10-23", "neck", 4, 40.0, "none", "Observation test visit", "TREAT_WITH_PRECAUTIONS"),
        )
        visit_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        study = create_pose_study(
            self.db,
            case_id="DEMO-NECK-001",
            title="Posture assessment",
            camera_view="front",
            image_asset="pose.png",
            image_sha256="abc",
            raw_landmarks=[],
        )
        obs = record_pose_observation(
            self.db,
            study_id=study["study_id"],
            case_id="DEMO-NECK-001",
            visit_id=visit_id,
            symptom_zone="Left upper trapezius",
            pain_score=4,
            movement_phase="End-range abduction hold",
            reported_symptoms="Dull aching pull during isometric elevation",
            functional_limitation="Cannot sustain shoulder hold > 10s",
        )
        self.assertTrue(obs["observation_id"].startswith("POBS-"))
        obs_list = list_pose_observations(self.db, study["study_id"])
        self.assertEqual(len(obs_list), 1)
        self.assertEqual(obs_list[0]["symptom_zone"], "Left upper trapezius")


class TestPoseAnatomyHTTP(unittest.TestCase):
    def test_pose_endpoints_and_readonly(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = str(Path(tmp) / "demo.sqlite3")
            server = create_server(db_path, port=0)
            t = Thread(target=server.serve_forever, daemon=True)
            t.start()
            url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                # 1. Curated actions catalog
                with urlopen(f"{url}/api/pose/actions", timeout=5) as res:
                    actions = json.load(res)
                    self.assertIn("cervical_flexion", actions)
                    self.assertIn("shoulder_abduction", actions)

                # 2. List studies for DEMO-NECK-001
                with urlopen(f"{url}/api/pose/studies?case_id=DEMO-NECK-001", timeout=5) as res:
                    studies = json.load(res)
                    self.assertIsInstance(studies, list)

                # 3. Create study without auth -> 401
                req = Request(
                    f"{url}/api/pose/studies",
                    data=json.dumps({"case_id": "DEMO-NECK-001", "title": "Test Pose"}).encode(),
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
