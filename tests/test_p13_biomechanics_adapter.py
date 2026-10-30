"""Unit tests for Milestone P13: Open-Source Anatomy & Functional Biomechanics Integration.

Tests cover:
1. OpenSim .mot file parsing & error handling
2. Scapulohumeral rhythm & coordinate range validation
3. Piecewise linear interpolation
4. Educational curriculum data structure & bilingual content
5. Model asset integrity & SHA-256 fingerprint verification
6. HTTP server endpoints for /education/ and /api/education/shoulder-lesson
"""

import hashlib
import json
import math
import tempfile
import unittest
import urllib.request
from pathlib import Path

from msk_therapy_os.biomechanics_adapter import (
    CLINICAL_DEPTH_GUIDANCE_ALLOWED,
    G14,
    PHYSIOLOGICAL_RANGES_DEG,
    SHOULDER_MOTION_STATUS_UNAVAILABLE,
    OpenSimFormatParser,
    OpenSimMotionData,
    ShoulderKinematicsValidator,
    get_shoulder_education_curriculum,
)
from msk_therapy_os.server import create_server


class TestOpenSimBiomechanicsAdapter(unittest.TestCase):
    """Test suite for OpenSim motion parser and shoulder kinematics validator."""

    def setUp(self):
        self.sample_mot_content = """Coordinates
version=1
nRows=5
nColumns=4
inDegrees=yes
endheader
time arm_elevation scapula_upward_rot scapula_anterior_tilt
0.00 0.00 0.00 10.00
0.25 45.00 15.00 12.50
0.50 90.00 30.00 15.00
0.75 135.00 45.00 17.50
1.00 180.00 60.00 20.00
"""

    def test_invariants_preserved(self):
        """Verify strict non-negotiable boundaries."""
        self.assertEqual(G14, "BLOCKED_EXTERNAL_DATA")
        self.assertFalse(CLINICAL_DEPTH_GUIDANCE_ALLOWED)
        self.assertEqual(SHOULDER_MOTION_STATUS_UNAVAILABLE, "SHOULDER_MOTION_DATA_UNAVAILABLE")

    def test_parse_valid_opensim_mot_text(self):
        """Verify parsing valid OpenSim ASCII text."""
        data = OpenSimFormatParser.parse_text(self.sample_mot_content, filename_hint="elevation.mot")
        self.assertEqual(data.n_rows, 5)
        self.assertEqual(data.n_columns, 4)
        self.assertTrue(data.in_degrees)
        self.assertEqual(data.headers, ["time", "arm_elevation", "scapula_upward_rot", "scapula_anterior_tilt"])
        self.assertEqual(data.time, [0.0, 0.25, 0.50, 0.75, 1.00])
        self.assertEqual(len(data.data["arm_elevation"]), 5)
        self.assertEqual(data.data["arm_elevation"][2], 90.0)

    def test_parse_opensim_from_file(self):
        """Verify parsing standard motion file on disk."""
        mot_path = Path("msk_therapy_os/data/biomechanics/sample_shoulder_elevation.mot")
        if mot_path.exists():
            data = OpenSimFormatParser.parse_file(mot_path)
            self.assertEqual(data.n_rows, 11)
            self.assertEqual(data.headers[0], "time")
            self.assertIn("arm_elevation", data.headers)
            self.assertIn("scapula_upward_rot", data.headers)

    def test_parse_rejects_empty_or_malformed_text(self):
        """Verify fail-closed parser on corrupted OpenSim data."""
        with self.assertRaises(ValueError):
            OpenSimFormatParser.parse_text("")

        with self.assertRaises(ValueError):
            OpenSimFormatParser.parse_text("some random header without time")

        corrupt_data = "endheader\ntime arm_elevation\n0.00 not_a_number\n"
        with self.assertRaises(ValueError):
            OpenSimFormatParser.parse_text(corrupt_data)

    def test_piecewise_linear_interpolation(self):
        """Verify deterministic linear interpolation across time."""
        data = OpenSimFormatParser.parse_text(self.sample_mot_content)
        
        # Exact timestamp hits
        self.assertAlmostEqual(data.interpolate("arm_elevation", 0.0), 0.0)
        self.assertAlmostEqual(data.interpolate("arm_elevation", 0.5), 90.0)
        self.assertAlmostEqual(data.interpolate("arm_elevation", 1.0), 180.0)

        # Midpoint interpolation (t = 0.125 -> halfway between 0 and 45 = 22.5)
        self.assertAlmostEqual(data.interpolate("arm_elevation", 0.125), 22.5)

        # Clamping out-of-bounds
        self.assertAlmostEqual(data.interpolate("arm_elevation", -1.0), 0.0)
        self.assertAlmostEqual(data.interpolate("arm_elevation", 5.0), 180.0)

    def test_unit_conversions(self):
        """Verify accurate deg to rad conversions."""
        self.assertAlmostEqual(ShoulderKinematicsValidator.convert_units(180.0, to_radians=True), math.pi)
        self.assertAlmostEqual(ShoulderKinematicsValidator.convert_units(math.pi / 2, to_radians=False), 90.0)

    def test_validate_coordinate_ranges(self):
        """Verify physiological coordinate bounds."""
        res_valid = ShoulderKinematicsValidator.validate_coordinate_range("arm_elevation", 90.0)
        self.assertTrue(res_valid["valid"])
        self.assertIsNone(res_valid["warning"])

        res_invalid = ShoulderKinematicsValidator.validate_coordinate_range("arm_elevation", 220.0)
        self.assertFalse(res_invalid["valid"])
        self.assertIn("Exceeds physiological bounds", res_invalid["warning"])

    def test_scapulohumeral_rhythm_calculation(self):
        """Verify scapulohumeral rhythm classifications."""
        # 1. Normal 2:1 ratio (60 deg GH, 30 deg ST)
        normal = ShoulderKinematicsValidator.compute_scapulohumeral_rhythm(60.0, 30.0)
        self.assertEqual(normal["ratio"], 2.0)
        self.assertEqual(normal["classification"], "PHYSIOLOGICAL_NORMAL_2_TO_1")

        # 2. Scapular hypomobility dyskinesia (60 deg GH, 18 deg ST -> 3.33 ratio)
        hypomobile = ShoulderKinematicsValidator.compute_scapulohumeral_rhythm(60.0, 18.0)
        self.assertGreater(hypomobile["ratio"], 2.4)
        self.assertEqual(hypomobile["classification"], "SCAPULAR_HYPOMOBILITY_DYSKINESIA")

        # 3. Early shrug compensation (40 deg GH, 35 deg ST -> 1.14 ratio)
        shrug = ShoulderKinematicsValidator.compute_scapulohumeral_rhythm(40.0, 35.0)
        self.assertLess(shrug["ratio"], 1.6)
        self.assertEqual(shrug["classification"], "COMPENSATORY_EARLY_SHRUG")

    def test_rounded_shoulder_posture_evaluation(self):
        """Verify posture index grading."""
        eval_neutral = ShoulderKinematicsValidator.evaluate_rounded_shoulder_posture(15.0, 10.0, 0.05)
        self.assertEqual(eval_neutral["postural_level"], "NEUTRAL_BALANCED")

        eval_severe = ShoulderKinematicsValidator.evaluate_rounded_shoulder_posture(42.0, 32.0, 0.90)
        self.assertEqual(eval_severe["postural_level"], "MARKED_ROUNDED_SHOULDER")
        self.assertEqual(eval_severe["motion_status"], SHOULDER_MOTION_STATUS_UNAVAILABLE)

    def test_curriculum_structure_and_bilingual_integrity(self):
        """Verify educational curriculum contains all 6 modules and evidence citations."""
        curr = get_shoulder_education_curriculum()
        self.assertEqual(curr["curriculum_id"], "P13_SHOULDER_POSTURE_MECHANICS")
        self.assertEqual(len(curr["stages"]), 6)
        self.assertTrue(len(curr["evidence_register"]) >= 4)
        self.assertIn("G14 = BLOCKED_EXTERNAL_DATA", curr["disclaimers"])

        for stage in curr["stages"]:
            self.assertIn("name_en", stage)
            self.assertIn("name_vi", stage)
            self.assertIn("summary_en", stage)
            self.assertIn("summary_vi", stage)
            self.assertTrue(len(stage["focus_muscles"]) > 0)


class TestEducationStudioAssetIntegrity(unittest.TestCase):
    """Test suite ensuring anatomical 3D assets and localized Three.js files are intact."""

    def test_anatomy_glb_file_and_checksum(self):
        """Verify anatomy.glb exists and matches canonical SHA-256."""
        model_path = Path("msk_therapy_os/static/education/models/anatomy.glb")
        self.assertTrue(model_path.is_file(), "anatomy.glb must be present in static/education/models/")
        
        hasher = hashlib.sha256()
        with model_path.open("rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        canonical_hash = "318347f91e4989da0c271e9662df536943df1149b413fef01cf21586073ea73e"
        self.assertEqual(hasher.hexdigest(), canonical_hash, "anatomy.glb SHA-256 fingerprint mismatch")

    def test_localized_three_js_vendor_files(self):
        """Verify Three.js r160 modules are fully localized."""
        vendor_dir = Path("msk_therapy_os/static/education/vendor/three")
        self.assertTrue(vendor_dir.is_dir())
        self.assertTrue((vendor_dir / "three.module.js").is_file())
        self.assertTrue((vendor_dir / "OrbitControls.js").is_file())
        self.assertTrue((vendor_dir / "loaders/GLTFLoader.js").is_file())
        self.assertTrue((vendor_dir / "LICENSE").is_file())


class TestEducationStudioHTTPServer(unittest.TestCase):
    """Integration test verifying server HTTP routes for the Education Studio."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = str(Path(cls.temp_dir.name) / "test_edu.sqlite3")
        cls.server = create_server(cls.db_path, host="127.0.0.1", port=0)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        import threading
        import time
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1.0)
        try:
            cls.temp_dir.cleanup()
        except Exception:
            pass

    def test_get_education_index_html(self):
        """Verify GET /education/ serves the studio HTML."""
        req = urllib.request.Request(f"{self.base_url}/education/")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get_content_type(), "text/html")
            body = resp.read().decode("utf-8")
            self.assertIn("Tại sao giải cơ xong vai nhẹ hơn", body)
            self.assertIn("canvas-container", body)
            self.assertIn("G14: BLOCKED_EXTERNAL_DATA", body)

    def test_get_education_shoulder_lesson_api(self):
        """Verify GET /api/education/shoulder-lesson returns structured curriculum."""
        req = urllib.request.Request(f"{self.base_url}/api/education/shoulder-lesson")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get_content_type(), "application/json")
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["curriculum_id"], "P13_SHOULDER_POSTURE_MECHANICS")
            self.assertEqual(len(data["stages"]), 6)
            self.assertEqual(data["scientific_gate_status"], "BLOCKED_EXTERNAL_DATA")

    def test_get_model_gltf_mime_type(self):
        """Verify anatomy.glb is served with model/gltf-binary MIME type."""
        req = urllib.request.Request(f"{self.base_url}/education/models/anatomy.glb")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get_content_type(), "model/gltf-binary")
            data = resp.read()
            self.assertTrue(data.startswith(b"glTF"), "Must start with glTF binary magic bytes")
            self.assertEqual(len(data), 9291204)


if __name__ == "__main__":
    unittest.main()
