"""End-to-end tests for MSK-Therapy-OS command line actions."""
from __future__ import annotations

import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

from msk_therapy_os.__main__ import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_cli.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, args: list[str]) -> tuple[int, str]:
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        try:
            exit_code = main(args)
        finally:
            sys.stdout = old_stdout
        return exit_code, buffer.getvalue()

    def test_cli_lifecycle(self):
        # 1. Init
        code, out = self.run_cli(["init", "--db", self.db_path])
        self.assertEqual(code, 0)
        self.assertIn("Initialized synthetic-only demo database", out)

        # 2. Seed
        code, out = self.run_cli(["seed-demo", "--db", self.db_path])
        self.assertEqual(code, 0)
        self.assertIn("Seeded fictional cases", out)

        # 3. Cases
        code, out = self.run_cli(["cases", "--db", self.db_path])
        self.assertEqual(code, 0)
        self.assertIn("DEMO-NECK-001", out)
        self.assertIn("DEMO-LOWBACK-002", out)

        # 4. Add Visit (clean)
        code, out = self.run_cli([
            "add-visit",
            "--db", self.db_path,
            "--case", "DEMO-NECK-001",
            "--date", "2026-10-19",
            "--pain", "5",
            "--rom", "45",
            "--region", "neck",
            "--flag", "none",
            "--note", "CLI visit test",
        ])
        self.assertEqual(code, 0)
        self.assertIn("DOCUMENT_ONLY", out)

        # 5. Add Structured ROM
        code, out = self.run_cli([
            "add-rom",
            "--db", self.db_path,
            "--visit-id", "1",
            "--motion", "cervical_rotation",
            "--side", "left",
            "--angle", "45.0",
            "--method", "goniometer",
        ])
        self.assertEqual(code, 0)
        self.assertIn("Recorded ROM measurement", out)

        # 6. Add SOAP note
        code, out = self.run_cli([
            "add-soap",
            "--db", self.db_path,
            "--visit-id", "1",
            "--s", "Neck tightness",
            "--o", "Cervical ROM limited",
            "--a", "Postural neck strain hypothesis",
            "--p", "Posture education and gentle mobilization",
            "--role", "student",
        ])
        self.assertEqual(code, 0)
        self.assertIn("Created SOAP note", out)

        # 7. Review SOAP note
        code, out = self.run_cli([
            "review-soap",
            "--db", self.db_path,
            "--soap-id", "1",
            "--reviewer", "Clinical Instructor",
            "--decision", "APPROVED",
            "--feedback", "Good assessment",
        ])
        self.assertEqual(code, 0)
        self.assertIn("Decision = APPROVED", out)

        # 8. Timeline
        code, out = self.run_cli(["timeline", "--db", self.db_path, "--case", "DEMO-NECK-001"])
        self.assertEqual(code, 0)
        self.assertIn("2026-10-19", out)
        self.assertIn("pain=5/10", out)

        # 9. Offline Report
        rep_file = str(Path(self.temp_dir.name) / "case_report.md")
        code, out = self.run_cli(["report", "--db", self.db_path, "--case", "DEMO-NECK-001", "--out", rep_file])
        self.assertEqual(code, 0)
        self.assertTrue(Path(rep_file).exists())
        content = Path(rep_file).read_text(encoding="utf-8")
        self.assertIn("SYNTHETIC CLINICAL LEARNING REPORT", content)
        self.assertIn("DEMO-NECK-001", content)

        # 10. Evidence CLI
        code, out = self.run_cli(["evidence", "--db", self.db_path, "--tier", "1"])
        self.assertEqual(code, 0)
        self.assertIn("EVID-G-001", out)

        # 11. Anatomy CLI
        code, out = self.run_cli(["anatomy", "--db", self.db_path, "--region", "neck"])
        self.assertEqual(code, 0)
        self.assertIn("STR-CERV-001", out)

        # 12. Safety Screen CLI
        code, out = self.run_cli(["screen-safety", "--flag", "bowel_bladder_change"])
        self.assertEqual(code, 0)
        self.assertIn("DISPOSITION: STOP_AND_REFER", out)
        self.assertIn("Cauda Equina", out)

        # 13. Atlas
        code, out = self.run_cli(["atlas"])
        self.assertEqual(code, 0)
        self.assertIn("https://", out)


if __name__ == "__main__":
    unittest.main()
