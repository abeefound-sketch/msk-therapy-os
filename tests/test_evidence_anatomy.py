"""Tests for Evidence Library and Anatomy Adapter with namespace segregation."""
from __future__ import annotations

import sqlite3
import unittest
from msk_therapy_os.anatomy import get_anatomy_by_id, list_anatomy
from msk_therapy_os.db import init_db, seed_db
from msk_therapy_os.evidence import get_evidence_by_id, list_evidence
from msk_therapy_os.models import EvidenceTier, KnowledgeNamespace


class TestEvidenceAndAnatomy(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        init_db(self.db)
        seed_db(self.db)

    def tearDown(self):
        self.db.close()

    def test_evidence_catalog_tiers(self):
        all_ev = list_evidence(self.db)
        self.assertGreaterEqual(len(all_ev), 8)

        # Check all 4 tiers are present
        tiers_found = set(e.tier for e in all_ev)
        self.assertEqual(tiers_found, {1, 2, 3, 4})

        # Check Tier 1 filtering
        t1 = list_evidence(self.db, tier=EvidenceTier.TIER_1_CLINICAL_GUIDELINE.value)
        self.assertTrue(all(e.tier == 1 for e in t1))
        self.assertGreaterEqual(len(t1), 3)

    def test_evidence_provenance_fields(self):
        item = get_evidence_by_id(self.db, "EVID-G-001")
        self.assertIsNotNone(item)
        self.assertEqual(item.evidence_id, "EVID-G-001")
        self.assertTrue(len(item.title) > 0)
        self.assertTrue(item.url.startswith("http"))
        self.assertTrue(len(item.organization) > 0)
        self.assertIsInstance(item.year, int)
        self.assertTrue(len(item.license) > 0)
        self.assertTrue(len(item.reviewed_on) > 0)
        self.assertTrue(len(item.reviewer) > 0)

    def test_anatomy_adapter_modern_structures(self):
        neck_structs = list_anatomy(self.db, region="neck")
        self.assertGreaterEqual(len(neck_structs), 2)
        cerv_spine = get_anatomy_by_id(self.db, "STR-CERV-001")
        self.assertIsNotNone(cerv_spine)
        self.assertEqual(cerv_spine.namespace, KnowledgeNamespace.ANATOMY_EVIDENCE.value)
        self.assertEqual(cerv_spine.bodyparts3d_id, "FJ9914")
        self.assertIn("FJ9914", cerv_spine.atlas_url)

    def test_traditional_constructs_namespace_separation(self):
        thai = get_anatomy_by_id(self.db, "TRAD-THAI-001")
        self.assertIsNotNone(thai)
        self.assertEqual(thai.namespace, KnowledgeNamespace.TRADITIONAL_MERIDIAN.value)
        self.assertIsNone(thai.bodyparts3d_id)
        self.assertEqual(thai.evidence_id, "EVID-T-001")

        dien_chan = get_anatomy_by_id(self.db, "TRAD-DIEN-001")
        self.assertIsNotNone(dien_chan)
        self.assertEqual(dien_chan.namespace, KnowledgeNamespace.DIEN_CHAN_REFLEX.value)
        self.assertIsNone(dien_chan.bodyparts3d_id)
        self.assertEqual(dien_chan.evidence_id, "EVID-T-002")

    def test_anatomy_filtering_by_namespace(self):
        evidence_only = list_anatomy(self.db, namespace=KnowledgeNamespace.ANATOMY_EVIDENCE.value)
        self.assertTrue(all(s.namespace == KnowledgeNamespace.ANATOMY_EVIDENCE.value for s in evidence_only))
        self.assertGreaterEqual(len(evidence_only), 5)


if __name__ == "__main__":
    unittest.main()
