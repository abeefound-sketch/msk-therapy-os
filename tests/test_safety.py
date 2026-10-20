"""Tests for MSK-Therapy-OS rule-based safety gating and contraindications."""
from __future__ import annotations

import unittest
from msk_therapy_os.models import Disposition
from msk_therapy_os.safety import RED_FLAGS, evaluate_safety


class TestSafetyEngine(unittest.TestCase):
    def test_all_red_flags_trigger_stop_and_refer(self):
        for flag in RED_FLAGS:
            if flag == "none":
                continue
            res = evaluate_safety(flag=flag)
            self.assertEqual(res.disposition, Disposition.STOP_AND_REFER)
            self.assertFalse(res.is_safe_to_proceed)
            self.assertIn("STOP", res.escalation_instructions)
            self.assertTrue(len(res.clinical_rationale) > 0)
            self.assertTrue(res.evidence_id.startswith("EVID-"))

    def test_clean_input_yields_document_only(self):
        res = evaluate_safety(flag="none")
        self.assertEqual(res.disposition, Disposition.DOCUMENT_ONLY)
        self.assertTrue(res.is_safe_to_proceed)
        self.assertEqual(len(res.flags_triggered), 0)

    def test_spinal_manipulation_is_strictly_forbidden(self):
        res = evaluate_safety(flag="none", modality="spinal_manipulation")
        self.assertEqual(res.disposition, Disposition.STOP_AND_REFER)
        self.assertFalse(res.is_safe_to_proceed)
        self.assertIn("PROHIBITED", res.escalation_instructions)

    def test_dds_device_contraindications(self):
        # Cardiac pacemaker with DDS device
        res = evaluate_safety(
            flag="none",
            modality="dds_device",
            contraindications=["cardiac_pacemaker"],
        )
        self.assertEqual(res.disposition, Disposition.STOP_AND_REFER)
        self.assertFalse(res.is_safe_to_proceed)
        self.assertTrue(any("pacemaker" in c for c in res.contraindications_triggered))

        # Missing DDS device specifications
        res_missing = evaluate_safety(
            flag="none",
            modality="dds_device",
            contraindications=["missing_device_specs"],
        )
        self.assertEqual(res_missing.disposition, Disposition.STOP_AND_REFER)
        self.assertFalse(res_missing.is_safe_to_proceed)

    def test_manual_massage_contraindications(self):
        res = evaluate_safety(
            flag="none",
            modality="manual_massage",
            contraindications=["active_dvt"],
        )
        self.assertEqual(res.disposition, Disposition.STOP_AND_REFER)
        self.assertFalse(res.is_safe_to_proceed)
        self.assertTrue(any("dvt" in c for c in res.contraindications_triggered))

    def test_invalid_flag_raises_value_error(self):
        with self.assertRaises(ValueError):
            evaluate_safety(flag="invalid_flag_name")


if __name__ == "__main__":
    unittest.main()
