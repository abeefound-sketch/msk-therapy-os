"""Tests for M2.1 (Acupuncture/Meridians) and M2.2 (Longitudinal Tracking, Observations, Sessions, FHIR)."""
from __future__ import annotations

import json
import sqlite3
import unittest

from msk_therapy_os.__main__ import add_visit
from msk_therapy_os.anatomy import list_anatomy
from msk_therapy_os.db import init_db, seed_db, seed_longitudinal_trajectory
from msk_therapy_os.models import KnowledgeNamespace
from msk_therapy_os.tracking import (
    export_case_fhir,
    get_patient_timeline,
    list_observations,
    list_sessions,
    record_observation,
    record_session,
)


class TestTrackingAndMeridians(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        init_db(self.db)
        seed_db(self.db)

    def tearDown(self):
        self.db.close()

    def _create_sample_visit(self, pain=5, rom=45.0, flag="none") -> int:
        add_visit(
            self.db,
            case="DEMO-NECK-001",
            when="2026-10-19",
            pain=pain,
            rom=rom,
            region="neck",
            flag=flag,
            note="Test visit",
        )
        return self.db.execute("SELECT MAX(id) FROM visits").fetchone()[0]

    def test_record_and_list_clinical_observations(self):
        v_id = self._create_sample_visit()

        # Valid observation on anatomical structure
        obs_id1 = record_observation(
            self.db,
            visit_id=v_id,
            structure_id="STR-CERV-002",
            structure_type="anatomy",
            observation_type="trigger_point",
            severity=7,
            finding="Taut band in right upper trapezius",
            interpretation="Myofascial trigger point",
        )
        self.assertGreater(obs_id1, 0)

        # Valid observation on acupuncture point
        obs_id2 = record_observation(
            self.db,
            visit_id=v_id,
            structure_id="ACU-GB21",
            structure_type="acupoint",
            observation_type="palpation",
            severity=6,
            finding="Local tenderness at GB21 landmark",
            interpretation="Gallbladder channel tension",
        )
        self.assertGreater(obs_id2, 0)

        # Query by visit
        obs_list = list_observations(self.db, visit_id=v_id)
        self.assertEqual(len(obs_list), 2)
        self.assertEqual(obs_list[0].structure_id, "STR-CERV-002")
        self.assertEqual(obs_list[0].severity, 7)
        self.assertEqual(obs_list[1].structure_id, "ACU-GB21")
        self.assertEqual(obs_list[1].severity, 6)

        # Query by structure
        struct_obs = list_observations(self.db, structure_id="STR-CERV-002")
        self.assertEqual(len(struct_obs), 1)
        self.assertEqual(struct_obs[0].id, obs_id1)

    def test_observation_validation_bounds(self):
        v_id = self._create_sample_visit()

        # Invalid severity > 10
        with self.assertRaises(ValueError):
            record_observation(self.db, v_id, "STR-CERV-002", "anatomy", "palpation", 11, "Too high")

        # Invalid severity < 0
        with self.assertRaises(ValueError):
            record_observation(self.db, v_id, "STR-CERV-002", "anatomy", "palpation", -1, "Negative")

        # Invalid structure type
        with self.assertRaises(ValueError):
            record_observation(self.db, v_id, "STR-CERV-002", "invalid_type", "palpation", 5, "Bad type")

        # Nonexistent structure ID
        with self.assertRaises(ValueError):
            record_observation(self.db, v_id, "NONEXISTENT-999", "anatomy", "palpation", 5, "Unknown")

    def test_record_and_list_therapy_sessions(self):
        v_id = self._create_sample_visit()

        sess_id = record_session(
            self.db,
            visit_id=v_id,
            modality="massage",
            duration_min=25,
            target_structures='["STR-CERV-002", "ACU-GB21"]',
            parameters="Gentle ischemic compression on trapezius",
            adverse_reactions="none",
            practitioner_role="student",
        )
        self.assertGreater(sess_id, 0)

        sessions = list_sessions(self.db, visit_id=v_id)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].modality, "massage")
        self.assertEqual(sessions[0].duration_min, 25)
        self.assertEqual(sessions[0].adverse_reactions, "none")

        # Invalid duration <= 0
        with self.assertRaises(ValueError):
            record_session(self.db, v_id, "massage", 0, "[]", "")

        # Invalid practitioner role
        with self.assertRaises(ValueError):
            record_session(self.db, v_id, "massage", 20, "[]", "", practitioner_role="unauthorized")

    def test_longitudinal_trajectory_and_timeline(self):
        # Seed Day 1, Day 3, Day 7
        seed_longitudinal_trajectory(self.db)

        timeline = get_patient_timeline(self.db, "DEMO-NECK-001")
        self.assertEqual(timeline["case_id"], "DEMO-NECK-001")
        self.assertEqual(len(timeline["visits"]), 3)

        # Check Day 1 vs Day 7 progression
        v1 = timeline["visits"][0]
        v3 = timeline["visits"][2]
        self.assertEqual(v1["pain"], 6)
        self.assertEqual(v1["rom_deg"], 45.0)
        self.assertEqual(v3["pain"], 2)
        self.assertEqual(v3["rom_deg"], 65.0)

        # Check trend calculations
        self.assertEqual(timeline["trends"]["pain_delta"], -4)
        self.assertEqual(timeline["trends"]["rom_delta"], 20.0)

        # Check structure-linked observations on Trapezius and Acupoints
        v1_struct_ids = [o["structure_id"] for o in v1["observations"]]
        self.assertIn("STR-CERV-002", v1_struct_ids)
        self.assertIn("ACU-GB21", v1_struct_ids)

        v3_struct_ids = [o["structure_id"] for o in v3["observations"]]
        self.assertIn("STR-CERV-002", v3_struct_ids)
        self.assertIn("ACU-GB20", v3_struct_ids)

    def test_fhir_r4_bundle_export(self):
        seed_longitudinal_trajectory(self.db)
        bundle = export_case_fhir(self.db, "DEMO-NECK-001")

        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "collection")

        # Find Patient resource
        patient_entries = [e for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient"]
        self.assertEqual(len(patient_entries), 1)
        self.assertEqual(patient_entries[0]["resource"]["id"], "patient-demo-neck-001")

        # Find Encounter resources
        encounters = [e for e in bundle["entry"] if e["resource"]["resourceType"] == "Encounter"]
        self.assertEqual(len(encounters), 3)

        # Find Observation resources (pain, rom, anatomical structures)
        observations = [e for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation"]
        self.assertGreater(len(observations), 6)

    def test_traditional_meridian_catalog_and_namespace_separation(self):
        # Verify modern anatomy structures
        modern = list_anatomy(self.db, namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value)
        self.assertGreater(len(modern), 0)
        for m in modern:
            self.assertEqual(m.namespace, KnowledgeNamespace.ANATOMY_EVIDENCE.value)
            self.assertTrue(m.structure_id.startswith("STR-"))

        # Verify traditional meridian structures
        meridians = list_anatomy(self.db, namespace=KnowledgeNamespace.TRADITIONAL_MERIDIAN.value)
        self.assertGreater(len(meridians), 0)
        acu_ids = [m.structure_id for m in meridians]
        self.assertIn("ACU-GB21", acu_ids)
        self.assertIn("ACU-GB20", acu_ids)
        self.assertIn("ACU-GV14", acu_ids)
        self.assertIn("TRAD-THAI-001", acu_ids)

        # Verify Dien Chan reflexology structures
        dien_chan = list_anatomy(self.db, namespace=KnowledgeNamespace.DIEN_CHAN_REFLEX.value)
        self.assertGreater(len(dien_chan), 0)
        dien_ids = [d.structure_id for d in dien_chan]
        self.assertIn("TRAD-DIEN-001", dien_ids)
        self.assertIn("TRAD-DIEN-002", dien_ids)
