"""M2.9: relationship type/provenance controls and conservative no-claim semantics."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

from msk_therapy_os.db import init_db, seed_db
from msk_therapy_os.relationship_catalog import get_entity, find_entities, get_relations
from msk_therapy_os.server import create_server


class RelationshipCatalogTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute('PRAGMA foreign_keys=ON')
        init_db(self.db)
        seed_db(self.db)

    def tearDown(self):
        self.db.close()

    def test_organs_are_not_traditional_channels(self):
        found = find_entities(self.db, 'stomach')
        self.assertIn('ANAT:STOMACH', {v['entity_id'] for v in found})
        self.assertIn('TCM:STOMACH_CHANNEL', {v['entity_id'] for v in found})
        self.assertEqual(get_entity(self.db, 'ANAT:STOMACH')['kind'], 'organ')
        self.assertEqual(get_entity(self.db, 'TCM:STOMACH_CHANNEL')['kind'], 'channel')
        self.assertEqual(get_entity(self.db, 'ANAT:STOMACH')['atlas_focus_available'], False)

    def test_unicode_search_source_review(self):
        self.assertEqual(find_entities(self.db, 'tuc tam ly')[0]['entity_id'], 'TCM:ST36')
        rel = get_relations(self.db, 'TCM:STOMACH_CHANNEL')
        self.assertEqual(len(rel), 1)
        self.assertEqual(rel[0]['other_entity_id'], 'TCM:ST36')
        self.assertEqual(rel[0]['relation_class'], 'traditional_association')
        self.assertEqual(rel[0]['status'], 'awaiting_source_review')
        self.assertFalse(rel[0]['clinical_efficacy_established'])

    def test_missing_mapping_never_promoted(self):
        self.assertIsNone(get_entity(self.db, 'FMA:MADE_UP'))
        self.assertFalse(get_entity(self.db, 'TCM:GB21')['atlas_focus_available'])
        self.assertEqual(get_relations(self.db, 'TCM:GB21'), [])

    def test_constraints_and_validation(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO knowledge_entities (entity_id,kind,name,namespace,source_id) VALUES ('X','invalid','X','X','SPEC:RELATIONSHIP_V1')")
        with self.assertRaises(ValueError):
            find_entities(self.db,'x',kind='invalid')
        with self.assertRaises(ValueError):
            get_relations(self.db,'TCM:ST36',relation_class='effectiveness')
        with self.assertRaises(ValueError):
            find_entities(self.db,'x'*121)

    def test_migrations_are_repeatable(self):
        init_db(self.db); seed_db(self.db)
        self.assertEqual(len(find_entities(self.db, 'ST36')), 1)
        self.assertEqual(len(get_relations(self.db, 'TCM:ST36')), 1)


class RelationshipHTTPTest(unittest.TestCase):
    def test_readonly_endpoints(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            server = create_server(str(Path(folder)/'test.sqlite3'), port=0)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            root = f'http://127.0.0.1:{server.server_address[1]}'
            try:
                with urlopen(root + '/api/explore/search?q=stomach',timeout=5) as res:
                    self.assertGreaterEqual(len(json.load(res)['results']), 2)
                with urlopen(root + '/api/explore/relations?entity_id=TCM%3AST36',timeout=5) as res:
                    self.assertEqual(json.load(res)['relations'][0]['relation_class'], 'traditional_association')
                with self.assertRaises(HTTPError) as e:
                    urlopen(root + '/api/explore/entities/DOES_NOT_EXIST',timeout=5)
                self.assertEqual(e.exception.code, 404)
                with urlopen(root + '/',timeout=5) as res:
                    self.assertIn(b'tab-explore',res.read())
                with urlopen(root + '/relationshipExplorer.js',timeout=5) as res:
                    self.assertIn(b'Atlas 3D Focus UNAVAILABLE',res.read())
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)


if __name__ == '__main__':
    unittest.main()
