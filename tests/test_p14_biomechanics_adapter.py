"""MSK-Therapy-OS - Unit Tests for Milestone P14 Biomechanics & Kinematics Engine.

Validates:
- OpenSimFormatParser strict security checks (10MB limit, duplicate headers, monotonicity, NaN/Inf).
- Parsing of seth_shoulder_elevation.mot and seth_shoulder_elevation.sto.
- BiomechanicalScenarioManifest catalog and SHA-256 provenance tracking.
- Scientific corrections: Scapulohumeral rhythm disclaimer and posture index disclaimers.
- 8-stage educational curriculum structure, 4-question interactive quiz, EV-01..EV-08 register.
- HTTP API route handling for P14 curriculum and static asset serving.
"""

import hashlib
import json
import math
import unittest
import urllib.request
from pathlib import Path
from threading import Thread

from msk_therapy_os.biomechanics_adapter import (
    G14,
    CLINICAL_DEPTH_GUIDANCE_ALLOWED,
    RELEASE_SCOPE,
    CLINICAL_VALIDATION,
    MUSCLE_ACTIVATION_DATA_UNAVAILABLE,
    OpenSimFormatParser,
    OpenSimMotionData,
    ShoulderKinematicsValidator,
    get_scenario_catalog,
    get_shoulder_education_curriculum,
)
from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler


class TestP14OpenSimParserAndSecurity(unittest.TestCase):
    """Test security boundaries and strict format validation in OpenSimFormatParser."""

    def test_file_size_limit_rejection(self):
        """Verify parser rejects payload exceeding 10MB safety bound."""
        oversized = "time x y\n" + ("0.0 1.0 2.0\n" * 1000000)
        with self.assertRaises(ValueError) as ctx:
            OpenSimFormatParser.parse_text(oversized)
        self.assertIn("10MB", str(ctx.exception))

    def test_empty_or_missing_header_rejection(self):
        """Verify parser rejects empty or headerless file."""
        with self.assertRaises(ValueError):
            OpenSimFormatParser.parse_text("")
        with self.assertRaises(ValueError):
            OpenSimFormatParser.parse_text("1.0 2.0 3.0\n4.0 5.0 6.0")

    def test_duplicate_headers_rejection(self):
        """Verify parser rejects duplicate column identifiers."""
        dup_content = """Coordinates
version=1
nRows=2
nColumns=3
inDegrees=yes
endheader
time arm_elevation arm_elevation
0.0 10.0 10.0
1.0 20.0 20.0
"""
        with self.assertRaises(ValueError) as ctx:
            OpenSimFormatParser.parse_text(dup_content)
        self.assertIn("Duplicate column", str(ctx.exception))

    def test_non_monotonic_time_rejection(self):
        """Verify parser rejects non-increasing or decreasing timestamps."""
        non_mono = """Coordinates
version=1
nRows=3
nColumns=2
inDegrees=yes
endheader
time arm_elevation
0.0 10.0
1.0 20.0
0.5 15.0
"""
        with self.assertRaises(ValueError) as ctx:
            OpenSimFormatParser.parse_text(non_mono)
        self.assertIn("monotonically increasing", str(ctx.exception))

    def test_nan_or_inf_rejection(self):
        """Verify parser rejects NaN or Inf numeric tokens."""
        nan_content = """Coordinates
version=1
nRows=2
nColumns=2
inDegrees=yes
endheader
time arm_elevation
0.0 10.0
1.0 NaN
"""
        with self.assertRaises(ValueError) as ctx:
            OpenSimFormatParser.parse_text(nan_content)
        self.assertIn("Non-finite", str(ctx.exception))

    def test_parse_valid_seth_motion(self):
        """Verify parsing of actual seth_shoulder_elevation.mot dataset."""
        mot_path = Path("msk_therapy_os/data/biomechanics/seth_shoulder_elevation.mot")
        self.assertTrue(mot_path.is_file(), "seth_shoulder_elevation.mot must exist")

        motion = OpenSimFormatParser.parse_file(mot_path)
        self.assertEqual(motion.n_rows, 21)
        self.assertIn("arm_elevation", motion.headers)
        self.assertIn("scapula_upward_rot", motion.headers)
        self.assertIn("clavicle_elevation", motion.headers)
        self.assertEqual(motion.time[0], 0.0)
        self.assertEqual(motion.time[-1], 2.0)
        self.assertEqual(motion.data["arm_elevation"][0], 0.0)
        self.assertEqual(motion.data["arm_elevation"][-1], 120.0)

    def test_parse_valid_seth_muscle_activations(self):
        """Verify parsing of actual seth_shoulder_elevation.sto static optimization dataset."""
        sto_path = Path("msk_therapy_os/data/biomechanics/seth_shoulder_elevation.sto")
        self.assertTrue(sto_path.is_file(), "seth_shoulder_elevation.sto must exist")

        sto = OpenSimFormatParser.parse_file(sto_path)
        self.assertEqual(sto.n_rows, 21)
        self.assertIn("delt_l", sto.headers)
        self.assertIn("supra", sto.headers)
        self.assertIn("serratus_l", sto.headers)
        # All activations in [0.0, 1.0]
        for h in sto.headers:
            if h != "time":
                for val in sto.data[h]:
                    self.assertTrue(0.0 <= val <= 1.0, f"Activation {val} for {h} outside [0, 1]")


class TestP14ScenarioManifest(unittest.TestCase):
    """Test scenario manifest registration, hashes, and validation levels."""

    def test_scenario_catalog_integrity(self):
        """Verify get_scenario_catalog returns expected scenarios."""
        catalog = get_scenario_catalog()
        self.assertGreaterEqual(len(catalog), 2)

        ids = [s.scenario_id for s in catalog]
        self.assertIn("SCEN_SETH_2019_ARM_ELEVATION", ids)
        self.assertIn("SCEN_ILLUSTRATIVE_ROUNDED_ELEVATION", ids)

    def test_scenario_checksums_match_files(self):
        """Verify scenario manifest SHA-256 hashes match on-disk files."""
        catalog = get_scenario_catalog()
        for s in catalog:
            if s.source_motion_file.endswith(".mot"):
                motion_path = Path("msk_therapy_os/data/biomechanics") / s.source_motion_file
                self.assertTrue(motion_path.is_file())
                content = motion_path.read_bytes()
                expected_hash = hashlib.sha256(content).hexdigest()
                self.assertEqual(s.motion_file_hash, expected_hash)

    def test_scenario_validation_levels(self):
        """Verify validation levels are not exaggerated."""
        catalog = get_scenario_catalog()
        for s in catalog:
            if s.scenario_id == "SCENARIO-SETH-ELEVATION-01":
                self.assertEqual(s.validation_level, "OPENSIM_MODEL_GENERATED")
                self.assertEqual(s.muscle_output_type, "ESTIMATED_ACTIVATION")
                self.assertFalse(s.subject_specific)
            elif s.scenario_id == "SCENARIO-ILLUSTRATIVE-ROUNDED-02":
                self.assertEqual(s.validation_level, "ILLUSTRATIVE")
                self.assertEqual(s.muscle_output_type, "UNAVAILABLE")


class TestP14CurriculumAndQuiz(unittest.TestCase):
    """Test 8-stage educational curriculum, interactive quiz, and evidence register."""

    def test_p14_curriculum_eight_stages(self):
        """Verify get_shoulder_education_curriculum('P14') delivers 8 stages."""
        curr = get_shoulder_education_curriculum(version="P14")
        self.assertEqual(curr["curriculum_id"], "P14_SHOULDER_BIOMECHANICS_STUDIO")
        self.assertEqual(len(curr["stages"]), 8)
        self.assertEqual(curr["scientific_gate_status"], G14)
        self.assertEqual(curr["clinical_depth_guidance_allowed"], CLINICAL_DEPTH_GUIDANCE_ALLOWED)

        for s in curr["stages"]:
            self.assertIn("name_en", s)
            self.assertIn("name_vi", s)
            self.assertIn("summary_en", s)
            self.assertIn("summary_vi", s)

    def test_p14_interactive_quiz(self):
        """Verify 4-question interactive quiz structure and correct options."""
        curr = get_shoulder_education_curriculum(version="P14")
        self.assertIn("quiz", curr)
        quiz = curr["quiz"]
        self.assertEqual(len(quiz), 4)

        for q in quiz:
            self.assertIn("question_id", q)
            self.assertIn("question_en", q)
            self.assertIn("question_vi", q)
            self.assertEqual(len(q["options_en"]), 3)
            self.assertEqual(len(q["options_vi"]), 3)
            self.assertIn(q["correct_option"], ["A", "B", "C"])
            self.assertTrue(len(q["explanation_en"]) > 20)
            self.assertTrue(len(q["explanation_vi"]) > 20)

    def test_p14_evidence_register_ev01_to_ev08(self):
        """Verify all 8 evidence items are cataloged with peer-reviewed provenance."""
        curr = get_shoulder_education_curriculum(version="P14")
        ev_list = curr["evidence_register"]
        self.assertEqual(len(ev_list), 8)

        ev_ids = [e["evidence_id"] for e in ev_list]
        for expected in ["EV-01", "EV-02", "EV-03", "EV-04", "EV-05", "EV-06", "EV-07", "EV-08"]:
            self.assertIn(expected, ev_ids)

        for e in ev_list:
            self.assertIn("doi_or_url", e)
            self.assertIn("research_design", e)
            self.assertIn("limitations", e)
            self.assertIn("claims_supported", e)


class TestP14ScientificNuances(unittest.TestCase):
    """Test scientific disclaimers on rhythm and posture evaluation."""

    def test_scapulohumeral_rhythm_disclaimers(self):
        """Verify rhythm ratio return dictionary contains educational disclaimers."""
        res = ShoulderKinematicsValidator.compute_scapulohumeral_rhythm(60.0, 30.0)
        self.assertIn("scientific_label", res)
        self.assertIn("IDEALIZED EDUCATIONAL EXAMPLE", res["scientific_label"])
        self.assertIn("clinical_disclaimer", res)

    def test_posture_evaluation_disclaimers(self):
        """Verify posture evaluation disclaims clinical diagnosis."""
        res = ShoulderKinematicsValidator.evaluate_rounded_shoulder_posture(25.0, 20.0, 0.5)
        self.assertIn("disclaimer", res)
        self.assertIn("POSTURE_VARIATION != CLINICAL_DIAGNOSIS", res["disclaimer"])


class TestP14HTTPServerRoutes(unittest.TestCase):
    """Test HTTP routes serving P14 curriculum and static biomechanics files."""

    @classmethod
    def setUpClass(cls):
        tmp_dir = Path("scratch/test_p14_http_server")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        cls.db_file = tmp_dir / "test_p14_srv.sqlite3"

        with open_db(str(cls.db_file)) as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)

        class P14TestHandler(MSKRequestHandler):
            db_path = str(cls.db_file)

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), P14TestHandler)
        cls.port = cls.server.server_port
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_p14_curriculum_query_param(self):
        """Verify GET /api/education/shoulder-lesson?v=p14 returns P14 curriculum."""
        req = urllib.request.Request(f"{self.base_url}/api/education/shoulder-lesson?v=p14")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["curriculum_id"], "P14_SHOULDER_BIOMECHANICS_STUDIO")
            self.assertEqual(len(data["stages"]), 8)
            self.assertEqual(len(data["quiz"]), 4)

    def test_serve_static_motion_files(self):
        """Verify static serving of .mot and .sto files."""
        req_mot = urllib.request.Request(f"{self.base_url}/education/data/seth_shoulder_elevation.mot")
        with urllib.request.urlopen(req_mot) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/plain", resp.headers.get_content_type())
            content = resp.read().decode("utf-8")
            self.assertIn("endheader", content)

        req_sto = urllib.request.Request(f"{self.base_url}/education/data/seth_shoulder_elevation.sto")
        with urllib.request.urlopen(req_sto) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("delt_l", content)

    def test_serve_shoulder_skeleton_glb(self):
        """Verify static serving of shoulder_skeleton.glb."""
        req = urllib.request.Request(f"{self.base_url}/education/models/shoulder_skeleton.glb")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get_content_type(), "model/gltf-binary")
            data = resp.read()
            self.assertTrue(data.startswith(b"glTF"))
            self.assertGreater(len(data), 300000)


if __name__ == "__main__":
    unittest.main()
