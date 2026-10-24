"""Integration tests for P9 REST API endpoints in server.py."""
import json
import sqlite3
import threading
from http.server import ThreadingHTTPServer
import urllib.request
import urllib.parse
from pathlib import Path
import pytest

from msk_therapy_os.server import MSKRequestHandler
from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port with an initialized temp db."""
    tmp_dir = tmp_path_factory.mktemp("p9_server_test")
    test_db_file = tmp_dir / "test_p9.sqlite3"

    with open_db(str(test_db_file)) as test_db:
        init_db(test_db)
        seed_db(test_db)
        init_points_tables(test_db)

    class TestHandler(MSKRequestHandler):
        db_path = str(test_db_file)

    server = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.shutdown()
    server.server_close()


def test_api_landmarks(live_server):
    """Verify GET /api/landmarks returns canonical landmarks catalog."""
    url = f"{live_server}/api/landmarks"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert len(data) >= 30
        c7 = next((x for x in data if x["landmark_id"] == "LM_C7_SPINE"), None)
        assert c7 is not None
        assert c7["fma_id"] == "FMA:13337"

    # Region filter
    url_filtered = f"{live_server}/api/landmarks?region=head_neck"
    req_filt = urllib.request.Request(url_filtered)
    with urllib.request.urlopen(req_filt) as resp:
        data_filt = json.loads(resp.read().decode("utf-8"))
        assert len(data_filt) > 0
        assert all(x["region"] == "head_neck" for x in data_filt)


def test_api_cun_rules(live_server):
    """Verify GET /api/cun-rules returns WHO B-cun segment definitions."""
    url = f"{live_server}/api/cun-rules"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert len(data) >= 11
        forearm = next((x for x in data if x["segment_id"] == "SEG_FOREARM_ELBOW_TO_WRIST_R"), None)
        assert forearm is not None
        assert forearm["standard_bcun_units"] == 12.0


def test_api_cun_metrics(live_server):
    """Verify GET /api/cun/metrics calculates physical mm per cun."""
    url = f"{live_server}/api/cun/metrics"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "SEG_FOREARM_ELBOW_TO_WRIST_R" in data
        metric = data["SEG_FOREARM_ELBOW_TO_WRIST_R"]
        assert metric["mm_per_cun"] > 15.0


def test_api_registration_align(live_server):
    """Verify POST /api/registration/align computes Umeyama registration transform."""
    url = f"{live_server}/api/registration/align"
    payload = {
        "source_name": "TestClient",
        "region": "head_neck",
        "source_landmarks": {
            "LM_VERTEX_CROWN": [0.0, 1.718, -0.015],
            "LM_GLABELLA": [0.0, 1.625, 0.089],
            "LM_INION": [0.0, 1.595, -0.098],
            "LM_MASTOID_R": [0.062, 1.574, -0.042],
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "VERIFIED_ANATOMICAL_ANCHOR"
        assert data["rms_error_mm"] == pytest.approx(0.0, abs=1e-3)


def test_api_cun_adapt(live_server):
    """Verify POST /api/cun/adapt scales cun segments based on patient morphology."""
    url = f"{live_server}/api/cun/adapt"
    payload = {
        "morphology_params": {
            "height_cm": 185.0,
            "shoulder_width_cm": 46.0,
            "arm_circ_cm": 32.0,
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "SEG_FOREARM_ELBOW_TO_WRIST_R" in data
        assert data["SEG_FOREARM_ELBOW_TO_WRIST_R"] > 21.0


def test_api_pose_evaluate(live_server):
    """Verify POST /api/pose/evaluate checks joint posture offsets."""
    url = f"{live_server}/api/pose/evaluate"
    payload = {
        "point_code": "LU5",
        "joint_angles": {
            "elbow_flexion_r": 45.0
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "UNCERTAIN_POSTURE_OFFSET"
        assert data["is_posture_sensitive"] is True
