"""Tests for Clinical Intake, ROM Measurements, Structured SOAP, and Offline Reporting."""
from __future__ import annotations

import sqlite3
import unittest
from msk_therapy_os.__main__ import add_visit
from msk_therapy_os.assessment import (
    get_intake,
    get_visit_rom,
    list_questionnaires,
    record_intake,
    record_rom,
)
from msk_therapy_os.db import init_db, seed_db
from msk_therapy_os.reporting import generate_case_report
from msk_therapy_os.soap import (
    create_soap_note,
    get_soap_notes_for_visit,
    review_soap_note,
)


class TestAssessmentAndSOAP(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        init_db(self.db)
        seed_db(self.db)

    def tearDown(self):
        self.db.close()

    def test_record_and_get_intake(self):
        record_intake(
            self.db,
            case_id="DEMO-NECK-001",
            age_band="30-49",
            symptom_onset="subacute_3_weeks",
            primary_region="neck",
            functional_limits="difficulty checking blind spot while driving",
            prior_care="ibuprofen prn",
            operator_role="student",
        )
        rec = get_intake(self.db, "DEMO-NECK-001")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.case_id, "DEMO-NECK-001")
        self.assertEqual(rec.primary_region, "neck")
        self.assertEqual(rec.operator_role, "student")

    def test_intake_rejects_real_patient_identifier(self):
        with self.assertRaises(ValueError):
            record_intake(
                self.db,
                case_id="PATIENT-JOHN-DOE",
                age_band="30-49",
                symptom_onset="1_week",
                primary_region="neck",
                functional_limits="pain",
                prior_care="none",
            )

    def test_intake_rejects_invalid_age_or_region(self):
        with self.assertRaises(ValueError):
            record_intake(
                self.db,
                case_id="DEMO-NECK-001",
                age_band="invalid_age",
                symptom_onset="1_week",
                primary_region="neck",
                functional_limits="pain",
                prior_care="none",
            )
        with self.assertRaises(ValueError):
            record_intake(
                self.db,
                case_id="DEMO-NECK-001",
                age_band="30-49",
                symptom_onset="1_week",
                primary_region="invalid_region",
                functional_limits="pain",
                prior_care="none",
            )

    def test_record_structured_rom(self):
        add_visit(
            self.db,
            case="DEMO-NECK-001",
            when="2026-10-19",
            pain=5,
            rom=45.0,
            region="neck",
            flag="none",
            note="Visit 1",
        )
        rom_id = record_rom(
            self.db,
            visit_id=1,
            motion="cervical_rotation",
            side="left",
            angle_deg=45.0,
            method="goniometer",
        )
        self.assertGreater(rom_id, 0)
        measurements = get_visit_rom(self.db, 1)
        self.assertEqual(len(measurements), 1)
        self.assertEqual(measurements[0].motion, "cervical_rotation")
        self.assertEqual(measurements[0].side, "left")
        self.assertEqual(measurements[0].angle_deg, 45.0)
        self.assertEqual(measurements[0].method, "goniometer")

    def test_rom_validation_errors(self):
        with self.assertRaises(ValueError):
            record_rom(self.db, visit_id=999, motion="flexion", side="left", angle_deg=45, method="goniometer")
        with self.assertRaises(ValueError):
            record_rom(self.db, visit_id=1, motion="", side="left", angle_deg=45, method="goniometer")
        with self.assertRaises(ValueError):
            record_rom(self.db, visit_id=1, motion="flexion", side="upwards", angle_deg=45, method="goniometer")
        with self.assertRaises(ValueError):
            record_rom(self.db, visit_id=1, motion="flexion", side="left", angle_deg=400, method="goniometer")
        with self.assertRaises(ValueError):
            record_rom(self.db, visit_id=1, motion="flexion", side="left", angle_deg=45, method="magic_wand")

    def test_soap_note_student_draft_and_supervision_review(self):
        add_visit(
            self.db,
            case="DEMO-NECK-001",
            when="2026-10-19",
            pain=4,
            rom=50.0,
            region="neck",
            flag="none",
            note="Initial note",
        )
        # Student creates draft
        soap_id = create_soap_note(
            self.db,
            visit_id=1,
            subjective="Learner notes patient reports neck stiffness after screen work.",
            objective="Active cervical rotation restricted to 45 deg bilaterally.",
            assessment="Fictional learning hypothesis: mechanical postural neck discomfort.",
            plan="Gentle passive stretching and ergonomics education.",
            author_role="student",
        )
        notes = get_soap_notes_for_visit(self.db, 1)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].review_status, "DRAFT")
        self.assertIsNone(notes[0].reviewed_by)

        # Student cannot approve note (PermissionError)
        with self.assertRaises(PermissionError):
            review_soap_note(
                self.db,
                soap_id=soap_id,
                reviewer_name="Student Jane",
                reviewer_role="student",
                decision="APPROVED",
            )

        # Reviewer approves note
        review_soap_note(
            self.db,
            soap_id=soap_id,
            reviewer_name="Dr. Taylor (PT Reviewer)",
            reviewer_role="reviewer",
            decision="APPROVED",
            feedback="Appropriate educational reasoning and conservative plan.",
        )
        updated_notes = get_soap_notes_for_visit(self.db, 1)
        self.assertEqual(updated_notes[0].review_status, "APPROVED")
        self.assertEqual(updated_notes[0].reviewed_by, "Dr. Taylor (PT Reviewer)")

    def test_soap_safety_hard_stop_enforcement(self):
        # Visit with red flag
        add_visit(
            self.db,
            case="DEMO-NECK-001",
            when="2026-10-20",
            pain=8,
            rom=20.0,
            region="neck",
            flag="progressive_weakness",
            note="Safety drill",
        )
        # Plan that attempts massage instead of referral should be rejected
        with self.assertRaises(ValueError) as ctx:
            create_soap_note(
                self.db,
                visit_id=1,
                subjective="Patient reports worsening weakness.",
                objective="C5-C6 weakness.",
                assessment="Possible nerve compression.",
                plan="Proceed with deep tissue massage and electrical stimulation.",
                author_role="student",
            )
        self.assertIn("Safety Hard Stop", str(ctx.exception))

        # Plan that includes referral is permitted
        soap_id = create_soap_note(
            self.db,
            visit_id=1,
            subjective="Patient reports worsening weakness.",
            objective="C5-C6 weakness.",
            assessment="Possible cord or nerve root compression red flag.",
            plan="STOP physical interventions. Immediate medical referral to spine specialist.",
            author_role="student",
        )
        self.assertGreater(soap_id, 0)

    def test_offline_report_generation(self):
        add_visit(
            self.db,
            case="DEMO-NECK-001",
            when="2026-10-19",
            pain=6,
            rom=40.0,
            region="neck",
            flag="none",
            note="Visit 1",
        )
        record_rom(self.db, visit_id=1, motion="cervical_rotation", side="left", angle_deg=40.0, method="goniometer")

        add_visit(
            self.db,
            case="DEMO-NECK-001",
            when="2026-10-26",
            pain=3,
            rom=55.0,
            region="neck",
            flag="none",
            note="Visit 2",
        )
        record_rom(self.db, visit_id=2, motion="cervical_rotation", side="left", angle_deg=55.0, method="inclinometer")

        report = generate_case_report(self.db, "DEMO-NECK-001")
        self.assertIn("SYNTHETIC CLINICAL LEARNING REPORT", report)
        self.assertIn("DEMO-NECK-001", report)
        self.assertIn("METHOD COMPARABILITY ALERT", report)  # Goniometer vs Inclinometer
        self.assertIn("Gross Pain Trend", report)
        self.assertIn("Clinical Safety & Governance Sign-off", report)

    def test_questionnaires_catalog(self):
        qs = list_questionnaires(self.db)
        self.assertGreaterEqual(len(qs), 4)
        cerv_red = [q for q in qs if q.item_id == "Q-NECK-001"][0]
        self.assertTrue(cerv_red.safety_critical)
        self.assertEqual(cerv_red.region, "neck")


if __name__ == "__main__":
    unittest.main()
