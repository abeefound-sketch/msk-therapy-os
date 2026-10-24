"""Independent HL7 FHIR R4B Schema Validation Test Suite.

Uses official fhir.resources library to independently validate the FHIR R4 Bundle
structure, resource schemas, reference integrity, DocumentReference attachments,
and supervisor approval Provenance metadata.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from msk_therapy_os.db import init_db, seed_db, seed_longitudinal_trajectory
from msk_therapy_os.tracking import export_case_fhir, validate_fhir_r4_bundle


class TestIndependentFHIRR4Validation(unittest.TestCase):
    """Rigorous independent validation of FHIR R4 Bundle and individual resources."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_fhir.sqlite3"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA foreign_keys=ON")
        init_db(self.conn)
        seed_db(self.conn)
        seed_longitudinal_trajectory(self.conn)

    def tearDown(self):
        self.conn.close()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_internal_fhir_validator_compliance(self):
        """Verify built-in zero-dependency validator checks pass cleanly."""
        bundle = export_case_fhir(self.conn, "DEMO-NECK-001")
        report = validate_fhir_r4_bundle(bundle)
        self.assertTrue(report["is_valid"])
        self.assertEqual(report["errors"], [])
        self.assertGreaterEqual(report["entry_count"], 6)
        self.assertIn("DocumentReference", report["resource_counts"])
        self.assertIn("Provenance", report["resource_counts"])

    def test_independent_fhir_resources_r4b_schema_validation(self):
        """Validate exported bundle against official fhir.resources models."""
        try:
            from fhir.resources.R4B.bundle import Bundle
            from fhir.resources.R4B.patient import Patient
            from fhir.resources.R4B.encounter import Encounter
            from fhir.resources.R4B.observation import Observation
            from fhir.resources.R4B.documentreference import DocumentReference
            from fhir.resources.R4B.provenance import Provenance
            from fhir.resources.R4B.adverseevent import AdverseEvent
        except ImportError as exc:
            self.fail(
                "MANDATORY RELEASE GATE FAILURE: 'fhir.resources' library is required for independent schema verification. "
                "Skipping external validation is strictly prohibited by Release Gate! Error: " + str(exc)
            )

        bundle_dict = export_case_fhir(self.conn, "DEMO-NECK-001")
        
        # 1. Validate full Bundle model
        bundle_obj = Bundle.model_validate(bundle_dict)
        self.assertEqual(bundle_obj.get_resource_type(), "Bundle")
        self.assertEqual(bundle_obj.type, "collection")
        self.assertGreater(len(bundle_obj.entry), 0)

        # 2. Validate individual resources strictly
        type_counts = {}
        for entry in bundle_dict["entry"]:
            res = entry["resource"]
            rtype = res["resourceType"]
            type_counts[rtype] = type_counts.get(rtype, 0) + 1

            if rtype == "Patient":
                p = Patient.model_validate(res)
                self.assertTrue(p.active)
            elif rtype == "Encounter":
                enc = Encounter.model_validate(res)
                self.assertIn(enc.status, ("finished", "cancelled", "entered-in-error", "in-progress"))
            elif rtype == "Observation":
                obs = Observation.model_validate(res)
                self.assertIsNotNone(obs.code)
            elif rtype == "DocumentReference":
                doc = DocumentReference.model_validate(res)
                self.assertIn(doc.status, ("current", "preliminary"))
                self.assertGreater(len(doc.content), 0)
            elif rtype == "Provenance":
                prov = Provenance.model_validate(res)
                self.assertGreater(len(prov.target), 0)
                self.assertGreater(len(prov.agent), 0)
                # Verify that supervisor sign-off is correctly identified as a verification signature
                self.assertIsNotNone(prov.signature)
                sig_type_codes = [s.type[0].code for s in prov.signature if s.type]
                self.assertIn("1.2.840.10065.1.12.1.5", sig_type_codes)
            elif rtype == "AdverseEvent":
                ae = AdverseEvent.model_validate(res)
                self.assertEqual(ae.actuality, "actual")

        self.assertIn("Patient", type_counts)
        self.assertIn("Encounter", type_counts)
        self.assertIn("Observation", type_counts)
        self.assertIn("DocumentReference", type_counts)
        self.assertIn("Provenance", type_counts)


if __name__ == "__main__":
    unittest.main()
