"""Comprehensive tests for M5 Reference Anatomy Layering and Discrete Slicing."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.tissue_layers import (
    TISSUE_LAYERS,
    LAYER_DISCLAIMER,
    get_layer_catalog,
    get_user_layer_config,
    update_layer_config,
)
from msk_therapy_os.server import create_server


class TestTissueLayersUnit(unittest.TestCase):
    def setUp(self):
        self.db = open_db(":memory:")
        init_db(self.db)
        seed_db(self.db)

    def tearDown(self):
        self.db.close()

    def test_layer_catalog_contents(self):
        catalog = get_layer_catalog()
        self.assertIn("layers", catalog)
        self.assertIn("disclaimer", catalog)
        self.assertIn("skin", catalog["layers"])
        self.assertIn("superficial_fascia", catalog["layers"])
        self.assertIn("deep_fascia", catalog["layers"])
        self.assertIn("muscle_superficial", catalog["layers"])
        self.assertIn("muscle_deep", catalog["layers"])
        self.assertIn("skeletal_bone", catalog["layers"])
        self.assertIn("neurovascular", catalog["layers"])
        self.assertIn("axial", catalog["slice_planes"])
        self.assertIn("sagittal", catalog["slice_planes"])
        self.assertIn("coronal", catalog["slice_planes"])

    def test_get_default_config(self):
        defaults = get_user_layer_config(self.db, "user_new")
        self.assertEqual(len(defaults), len(TISSUE_LAYERS))
        skin_cfg = next(c for c in defaults if c["layer_name"] == "skin")
        self.assertEqual(skin_cfg["opacity"], 0.5)
        self.assertEqual(skin_cfg["is_visible"], 1)

    def test_update_layer_config(self):
        res = update_layer_config(
            self.db,
            user_id="clinician_1",
            layer_name="muscle_superficial",
            opacity=0.45,
            is_visible=True,
            slice_plane="axial",
            slice_offset=0.25,
        )
        self.assertEqual(res["layer_name"], "muscle_superficial")
        self.assertEqual(res["opacity"], 0.45)
        self.assertTrue(res["is_visible"])
        self.assertEqual(res["slice_plane"], "axial")
        self.assertEqual(res["slice_offset"], 0.25)
        self.assertIn("REFERENCE TISSUE LAYERS ONLY", res["disclaimer"])

        # Fetch and verify persistence
        cfg = get_user_layer_config(self.db, "clinician_1")
        item = next(c for c in cfg if c["layer_name"] == "muscle_superficial")
        self.assertEqual(item["opacity"], 0.45)
        self.assertEqual(item["slice_plane"], "axial")
        self.assertEqual(item["slice_offset"], 0.25)

    def test_update_layer_validation_errors(self):
        with self.assertRaises(ValueError):
            update_layer_config(self.db, user_id="u1", layer_name="alien_tissue", opacity=0.5, is_visible=True)

        with self.assertRaises(ValueError):
            update_layer_config(self.db, user_id="u1", layer_name="skin", opacity=1.5, is_visible=True)

        with self.assertRaises(ValueError):
            update_layer_config(self.db, user_id="u1", layer_name="skin", opacity=0.5, is_visible=True, slice_plane="oblique")

        with self.assertRaises(ValueError):
            update_layer_config(self.db, user_id="u1", layer_name="skin", opacity=0.5, is_visible=True, slice_offset=2.0)


class TestTissueLayersAPI(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.tmp_dir.name) / "test_m5.sqlite3"
        with open_db(self.db_path) as db:
            init_db(db)
            seed_db(db)
        self.server = create_server(self.db_path, port=0)
        self.port = self.server.server_address[1]
        self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp_dir.cleanup()

    def test_api_layers_catalog_get(self):
        req = Request(f"http://127.0.0.1:{self.port}/api/anatomy/layers")
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertIn("layers", data)
            self.assertIn("disclaimer", data)
            self.assertIn("skin", data["layers"])

    def test_api_layers_config_get_and_put(self):
        # 1. GET defaults
        req = Request(f"http://127.0.0.1:{self.port}/api/anatomy/layers/config?user_id=dr_smith")
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(len(data), len(TISSUE_LAYERS))

        # 2. PUT update
        update_payload = json.dumps({
            "user_id": "dr_smith",
            "layer_name": "skeletal_bone",
            "opacity": 0.7,
            "is_visible": True,
            "slice_plane": "coronal",
            "slice_offset": -0.3,
        }).encode("utf-8")
        put_req = Request(
            f"http://127.0.0.1:{self.port}/api/anatomy/layers/config",
            data=update_payload,
            headers={"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{self.port}"},
            method="PUT",
        )
        with urlopen(put_req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["status"], "updated")
            self.assertEqual(data["config"]["layer_name"], "skeletal_bone")
            self.assertEqual(data["config"]["opacity"], 0.7)

        # 3. GET verify persistence
        req = Request(f"http://127.0.0.1:{self.port}/api/anatomy/layers/config?user_id=dr_smith")
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            bone = next(c for c in data if c["layer_name"] == "skeletal_bone")
            self.assertEqual(bone["opacity"], 0.7)
            self.assertEqual(bone["slice_plane"], "coronal")
            self.assertEqual(bone["slice_offset"], -0.3)


if __name__ == "__main__":
    unittest.main()
