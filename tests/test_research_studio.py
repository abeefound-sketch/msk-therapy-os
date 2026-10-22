"""Synthetic M2.10 point-set and dynamic observation isolation tests."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from threading import Thread
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from msk_therapy_os.db import init_db,seed_db
from msk_therapy_os.__main__ import add_visit
from msk_therapy_os.research_studio import (create_research_set,create_definition,create_reactive_observation,
    list_definitions,case_research_timeline,validate_geometry)
from msk_therapy_os.server import create_server

P = {'space':'image_normalized_v1','type':'point','coordinates':[0.4,0.5]}


class ResearchStudioTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('PRAGMA foreign_keys=ON')
        seed_db(self.db)
        self.study = create_research_set(self.db,title='Synthetic face research',framework='custom',owner='USR-ADMIN-01')
        self.front = next(d for d in self.study['diagrams'] if d['view']=='front')
        add_visit(self.db,case='DEMO-NECK-001',when='2026-10-20',pain=7,rom=45,region='neck',flag='none',note='synthetic')
        self.visit_id = self.db.execute('SELECT id FROM visits WHERE case_id=?',('DEMO-NECK-001',)).fetchone()[0]

    def tearDown(self):
        self.db.close()

    def test_definitions_are_distinct_from_encounter_findings(self):
        d = create_definition(self.db,{'diagram_id':self.front['diagram_id'],'local_code':'26','label':'Unreviewed study point',
            'geometry':P,'source_note':'Original schematic user-defined location'},'USR-ADMIN-01')
        self.assertEqual(d['review_state'],'draft')
        o = create_reactive_observation(self.db,{'case_id':'DEMO-NECK-001','visit_id':self.visit_id,
            'diagram_id':self.front['diagram_id'],'definition_id':d['definition_id'],
            'geometry':P,'finding_state':'observed_positive','tenderness':7,'method':'synthetic palpation'},'USR-ADMIN-01')
        self.assertEqual(o['finding_state'],'observed_positive')
        timeline = case_research_timeline(self.db,'DEMO-NECK-001','USR-ADMIN-01')
        self.assertEqual(len(timeline),1)
        self.assertEqual(timeline[0]['geometry']['coordinates'],[0.4,0.5])
        self.assertEqual(list_definitions(self.db,diagram_id=self.front['diagram_id'])[0]['geometry'],P)

    def test_cross_case_denied(self):
        with self.assertRaises(ValueError):
            create_reactive_observation(self.db,{'case_id':'DEMO-LOWBACK-002','visit_id':self.visit_id,
            'diagram_id':self.front['diagram_id'],'geometry':P,'finding_state':'not_assessed',
            'method':'synthetic'},'USR-ADMIN-01')
        with self.assertRaises(ValueError):
            create_reactive_observation(self.db,{'case_id':'PAT-REAL-001','visit_id':self.visit_id,
            'diagram_id':self.front['diagram_id'],'geometry':P,'finding_state':'not_assessed',
            'method':'synthetic'},'USR-ADMIN-01')

    def test_owner_duplicate_and_diagram_mismatch(self):
        template={'diagram_id':self.front['diagram_id'],'local_code':'26','label':'Research point',
                  'geometry':P,'source_note':'Unverified local study'}
        with self.assertRaises(PermissionError):
            create_definition(self.db,template,'OTHER_USER')
        create_definition(self.db,template,'USR-ADMIN-01')
        with self.assertRaises(sqlite3.IntegrityError):
            create_definition(self.db,template,'USR-ADMIN-01')

    def test_geometry_rejects_nan_and_out_of_bounds(self):
        for coords in ([float('nan'),0.5],[1.1,0.5],[-0.1,0.2],[True,0.5],['0.4',0.5]):
            with self.assertRaises(ValueError):
                validate_geometry({**P,'coordinates':coords})
        self.assertEqual(validate_geometry(P),P)
        self.assertEqual(validate_geometry({'space':'image_normalized_v1','type':'polygon',
            'coordinates':[[.1,.2],[.9,.2],[.8,.9]]})['type'],'polygon')

    def test_states_not_assessed_distinct(self):
        data={'case_id':'DEMO-NECK-001','visit_id':self.visit_id,'diagram_id':self.front['diagram_id'],
          'geometry':P,'finding_state':'not_assessed','method':'not examined'}
        create_reactive_observation(self.db,data,'USR-ADMIN-01')
        with self.assertRaises(ValueError):
            create_reactive_observation(self.db,{**data,'tenderness':0},'USR-ADMIN-01')
        create_reactive_observation(self.db,{**data,'finding_state':'assessed_negative','tenderness':0},'USR-ADMIN-01')
        self.assertEqual([r['finding_state'] for r in case_research_timeline(self.db,'DEMO-NECK-001','USR-ADMIN-01')],
                         ['not_assessed','assessed_negative'])


class ResearchHTTPTest(unittest.TestCase):
    def test_nonlocal_bind_requires_readonly(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            with patch.dict('os.environ',{'MSK_PUBLIC_DEMO_READONLY':'0'}):
                with self.assertRaises(PermissionError):
                    create_server(str(Path(tmp)/'demo.sqlite3'),host='0.0.0.0',port=0)

    def test_auth_needed_and_public_readonly(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            server=create_server(str(Path(tmp)/'demo.sqlite3'),port=0)
            server_thread=Thread(target=server.serve_forever,daemon=True);server_thread.start()
            url=f'http://127.0.0.1:{server.server_address[1]}'
            try:
                with urlopen(url+'/api/research/sets') as res: self.assertEqual(len(json.load(res)),1)
                req=Request(url+'/api/research/sets',data=json.dumps({'title':'X'}).encode(),headers={'Content-Type':'application/json'})
                with self.assertRaises(HTTPError) as exc: urlopen(req)
                self.assertEqual(exc.exception.code,401)
                with patch.dict('os.environ',{'MSK_PUBLIC_DEMO_READONLY':'1'}):
                    with self.assertRaises(HTTPError) as exc: urlopen(req)
                    self.assertEqual(exc.exception.code,403)
                    with urlopen(url+'/api/explore/search?q=stomach') as res: self.assertGreater(len(json.load(res)['results']),0)
            finally:
                server.shutdown();server.server_close();server_thread.join(timeout=5)

if __name__=='__main__': unittest.main()
