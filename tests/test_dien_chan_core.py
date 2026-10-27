"""Unit and integration tests for Dien Chan Facial Reflexology 3D Atlas and Search."""
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
from msk_therapy_os.dien_chan.annotations import (
    PointAnnotation2D,
    AnnotationView,
    AnnotationConfidence,
    Laterality,
    CANONICAL_2D_ANNOTATIONS,
    get_annotations_for_point,
    get_annotations_for_source,
)
from msk_therapy_os.dien_chan.facial_registration import (
    FacialRegistrationEngine,
    ResolvedDienChanPoint,
)
from msk_therapy_os.dien_chan.db import (
    init_dien_chan_tables,
    seed_dien_chan_database,
    list_dien_chan_points,
    get_dien_chan_point,
    get_protocol_with_points,
)
from msk_therapy_os.dien_chan.search import (
    normalize_vietnamese_text,
    search_dien_chan_conditions,
)


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port with an initialized temp db."""
    tmp_dir = tmp_path_factory.mktemp("dc_server_test")
    test_db_file = tmp_dir / "test_dc.sqlite3"

    with open_db(str(test_db_file)) as test_db:
        init_db(test_db)
        seed_db(test_db)

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


# ============================================================================
# 1. 2D Annotation Model Tests
# ============================================================================

def test_annotation_2d_validation():
    """Verify 2D annotation coordinate constraints and methods."""
    anno = PointAnnotation2D(
        annotation_id="ANN_TEST_103",
        source_image_id="SRC_IMG_DC_02",
        point_code="DC_103",
        view=AnnotationView.FRONTAL,
        pixel_x=202.0,
        pixel_y=125.0,
        image_width=800,
        image_height=578,
        grid_vertical="O",
        grid_horizontal="2",
        laterality=Laterality.MIDLINE,
        confidence=AnnotationConfidence.HIGH,
    )
    assert anno.norm_u == round(202.0 / 800.0, 4)
    assert anno.norm_v == round(125.0 / 578.0, 4)
    assert anno.laterality == Laterality.MIDLINE

    d = anno.to_dict()
    assert d["point_code"] == "DC_103"
    assert d["grid_vertical"] == "O"
    assert d["grid_horizontal"] == "2"


def test_canonical_annotations_catalog():
    """Verify CANONICAL_2D_ANNOTATIONS catalog has valid entries."""
    assert len(CANONICAL_2D_ANNOTATIONS) >= 20
    # Check that all 11 Headache/Sinus points are present
    expected_b = ["DC_103", "DC_106", "DC_107", "DC_300", "DC_73", "DC_189", "DC_61", "DC_19", "DC_127", "DC_96", "DC_43"]
    annotated_codes = set(a.point_code for a in CANONICAL_2D_ANNOTATIONS)
    for code in expected_b:
        assert code in annotated_codes, f"Missing annotation for {code}"

    # Verify helper lookups
    p103_annos = get_annotations_for_point("DC_103")
    assert len(p103_annos) >= 2  # Frontal and profile views

    src_annos = get_annotations_for_source("SRC_IMG_DC_02")
    assert len(src_annos) >= 15


# ============================================================================
# 2. 3D Facial Registration Engine Tests
# ============================================================================

def test_facial_registration_engine_resolution():
    """Verify FacialRegistrationEngine registers points in BodyParts3D FJ2810 coordinate frame."""
    engine = FacialRegistrationEngine()

    # Point 103 (Midline forehead, Line 2 - Candidate annotation)
    p103 = engine.get_point("DC_103")
    assert p103 is not None
    assert p103.point_code == "DC_103"
    assert p103.grid_coordinate == "O-2"
    assert abs(p103.position_xyz[0]) < 1e-4  # Midline X ~ 0
    assert 1.62 < p103.position_xyz[1] < 1.69  # Forehead Y
    assert p103.position_xyz[2] > 0.05  # Face anterior Z
    assert p103.surface_normal[2] > 0.5  # Normal points anteriorly
    assert p103.review_status == "CANDIDATE_ANNOTATION"
    assert p103.projection_residual_mm is not None
    assert p103.projection_residual_mm < 2.0

    # Point 61 (Alar-facial groove, bilateral - Verified anatomical anchor)
    p61 = engine.get_point("DC_61")
    assert p61 is not None
    assert p61.grid_coordinate == "B-8"
    assert p61.surface_normal[2] > 0.3
    assert p61.fma_anchor == "FMA:53051"  # Alar base / groove anchor
    assert p61.review_status == "VERIFIED_ANATOMICAL_ANCHOR"

    # Point 19 (Philtrum apex, under nose - Verified anatomical anchor)
    p19 = engine.get_point("DC_19")
    assert p19 is not None
    assert p19.grid_coordinate == "O-8"
    assert p19.fma_anchor == "FMA:53173"  # Philtrum anchor
    assert abs(p19.position_xyz[0]) < 1e-4
    assert p19.review_status == "VERIFIED_ANATOMICAL_ANCHOR"

    # Point 127 (Mentolabial sulcus - Verified anatomical anchor)
    p127 = engine.get_point("DC_127")
    assert p127 is not None
    assert p127.grid_coordinate == "O-11"
    assert p127.position_xyz[1] < p19.position_xyz[1]  # Below philtrum
    assert p127.review_status == "VERIFIED_ANATOMICAL_ANCHOR"


def test_atlas_points_bilateral_splitting():
    """Verify resolve_points_for_atlas creates distinct left and right instances for bilateral points."""
    engine = FacialRegistrationEngine()
    atlas_map = engine.resolve_points_for_atlas()
    assert len(atlas_map) >= 24

    assert "DC_103" in atlas_map
    assert "DC_61" in atlas_map

    p103 = atlas_map["DC_103"]
    assert len(p103["instances"]) == 1
    assert p103["instances"][0]["side"] == "midline"

    p61 = atlas_map["DC_61"]
    assert len(p61["instances"]) == 2
    left_inst = next(i for i in p61["instances"] if i["side"] == "left")
    right_inst = next(i for i in p61["instances"] if i["side"] == "right")
    assert left_inst["position"][0] > 0  # Anatomical left (patient +X)
    assert right_inst["position"][0] < 0  # Anatomical right (patient -X)
    assert abs(left_inst["position"][0] + right_inst["position"][0]) < 1e-4  # Symmetric offset


# ============================================================================
# 3. Knowledge Database Schema & Seeding Tests
# ============================================================================

def test_database_seeding_and_integrity():
    """Verify SQLite database seeding creates tables and authentic protocol records."""
    conn = sqlite3.connect(":memory:")
    init_dien_chan_tables(conn)
    seed_dien_chan_database(conn)

    points = list_dien_chan_points(conn)
    assert len(points) >= 24

    p103 = get_dien_chan_point(conn, "DC_103")
    assert p103 is not None
    assert p103["grid_coordinate"] == "O-2"
    assert p103["review_status"] == "CANDIDATE_ANNOTATION"

    p19 = get_dien_chan_point(conn, "DC_19")
    assert p19 is not None
    assert p19["review_status"] == "VERIFIED_ANATOMICAL_ANCHOR"

    # Verify headache protocol
    proto = get_protocol_with_points(conn, "PROTO_HEADACHE_SINUS_01")
    assert proto is not None
    assert proto["protocol_id"] == "PROTO_HEADACHE_SINUS_01"
    assert len(proto["points"]) == 11
    pt_codes = [p["point_code"] for p in proto["points"]]
    assert "DC_103" in pt_codes
    assert "DC_43" in pt_codes

    conn.close()


# ============================================================================
# 4. Vietnamese Diacritics Normalization & Search Engine Tests
# ============================================================================

def test_vietnamese_text_normalization():
    """Verify normalize_vietnamese_text properly strips diacritics and converts d/D."""
    assert normalize_vietnamese_text("Đau Đầu") == "dau dau"
    assert normalize_vietnamese_text("Viêm Xoang Mũi Dị Ứng") == "viem xoang mui di ung"
    assert normalize_vietnamese_text("Mất Ngủ, Khó Ngủ") == "mat ngu kho ngu"
    assert normalize_vietnamese_text("Đau Cổ Vai Gáy") == "dau co vai gay"
    assert normalize_vietnamese_text("  Kho  Ngu  ") == "kho ngu"


def test_condition_search_engine():
    """Verify search_dien_chan_conditions finds authentic matches without hallucination."""
    conn = sqlite3.connect(":memory:")
    init_dien_chan_tables(conn)
    seed_dien_chan_database(conn)

    # 1. Exact / primary match
    res_exact = search_dien_chan_conditions(conn, "Đau đầu - Viêm xoang")
    assert res_exact["total_matches"] >= 1
    assert res_exact["results"][0]["condition_id"] == "COND_HEADACHE_SINUS"

    # 2. Synonym match
    res_syn = search_dien_chan_conditions(conn, "nhức nửa đầu")
    assert res_syn["total_matches"] >= 1
    assert res_syn["results"][0]["condition_id"] == "COND_HEADACHE_SINUS"

    # 3. Unaccented match
    res_unacc = search_dien_chan_conditions(conn, "viem xoang")
    assert res_unacc["total_matches"] >= 1
    assert res_unacc["results"][0]["condition_id"] == "COND_HEADACHE_SINUS"

    # 4. Insomnia match
    res_ins = search_dien_chan_conditions(conn, "mat ngu")
    assert res_ins["total_matches"] >= 1
    assert res_ins["results"][0]["condition_id"] == "COND_INSOMNIA"

    # 5. Stopword rejection test: "bệnh lạ không có" should NOT match "cổ vai gáy"
    res_stopword = search_dien_chan_conditions(conn, "bệnh lạ không có")
    assert res_stopword["total_matches"] == 0
    assert len(res_stopword["results"]) == 0

    # 6. Completely unknown condition: zero hallucination guarantee
    res_unknown = search_dien_chan_conditions(conn, "hội chứng lupus ban đỏ XYZ")
    assert res_unknown["total_matches"] == 0
    assert len(res_unknown["results"]) == 0

    conn.close()


# ============================================================================
# 5. REST API Integration Tests
# ============================================================================

def test_api_dien_chan_points(live_server):
    """Verify GET /api/dien-chan/points returns authoritative Dien Chan catalog."""
    url = f"{live_server}/api/dien-chan/points"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "points" in data
        assert len(data["points"]) >= 24

        pt103 = next((p for p in data["points"] if p["point_code"] == "DC_103"), None)
        assert pt103 is not None
        assert pt103["grid_coordinate"] == "O-2"
        assert len(pt103["position"]) == 3
        assert len(pt103["surface_normal"]) == 3


def test_api_dien_chan_point_by_code(live_server):
    """Verify GET /api/dien-chan/points/{id} returns single point and 404 on missing."""
    url = f"{live_server}/api/dien-chan/points/DC_103"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["point_code"] == "DC_103"

    # Non-existent point returns 404
    url_404 = f"{live_server}/api/dien-chan/points/DC_INVALID_999"
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(url_404)
    assert excinfo.value.code == 404


def test_api_dien_chan_condition_search(live_server):
    """Verify GET /api/dien-chan/conditions/search?q= searches conditions."""
    url = f"{live_server}/api/dien-chan/conditions/search?q={urllib.parse.quote('đau đầu')}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "results" in data
        assert len(data["results"]) >= 1
        r0 = data["results"][0]
        assert r0["condition_id"] == "COND_HEADACHE_SINUS"
        assert len(r0["protocols"]) >= 1
        assert "DC_103" in r0["protocols"][0]["point_codes"]

    # Unknown query returns 200 with empty list
    url_empty = f"{live_server}/api/dien-chan/conditions/search?q={urllib.parse.quote('triệu chứng lạ lẫm')}"
    req_empty = urllib.request.Request(url_empty)
    with urllib.request.urlopen(req_empty) as resp:
        assert resp.status == 200
        data_empty = json.loads(resp.read().decode("utf-8"))
        assert data_empty["results"] == []


def test_api_dien_chan_protocols(live_server):
    """Verify protocol retrieval endpoints."""
    url_cond_proto = f"{live_server}/api/dien-chan/conditions/COND_HEADACHE_SINUS/protocols"
    req = urllib.request.Request(url_cond_proto)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "protocols" in data
        assert len(data["protocols"]) >= 1
        assert data["protocols"][0]["protocol_id"] == "PROTO_HEADACHE_SINUS_01"

    url_proto = f"{live_server}/api/dien-chan/protocols/PROTO_HEADACHE_SINUS_01"
    req_p = urllib.request.Request(url_proto)
    with urllib.request.urlopen(req_p) as resp:
        assert resp.status == 200
        proto = json.loads(resp.read().decode("utf-8"))
        assert proto["protocol_id"] == "PROTO_HEADACHE_SINUS_01"
        assert len(proto["points"]) == 11


def test_api_dien_chan_images_serving(live_server):
    """Verify GET /api/dien-chan/images/{name} serves authentic local charts securely."""
    url_img_b = f"{live_server}/api/dien-chan/images/headache-sinus"
    req = urllib.request.Request(url_img_b)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "image/png"
        data = resp.read()
        assert len(data) > 10000  # Non-empty PNG bytes

    url_img_a = f"{live_server}/api/dien-chan/images/atlas-front-side"
    req_a = urllib.request.Request(url_img_a)
    with urllib.request.urlopen(req_a) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "image/png"
        data_a = resp.read()
        assert len(data_a) > 10000

    # Path traversal and invalid image returns 404
    url_invalid = f"{live_server}/api/dien-chan/images/something-else"
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(url_invalid)
    assert excinfo.value.code == 404


def test_api_dien_chan_geometry_resolve(live_server):
    """Verify POST /api/dien-chan/geometry/resolve resolves points with metadata."""
    url = f"{live_server}/api/dien-chan/geometry/resolve"
    payload = json.dumps({"point_codes": ["DC_103", "DC_61", "DC_19"]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "points" in data
        assert len(data["points"]) >= 3
        p103 = data["points"]["DC_103"]
        assert p103["grid_coordinate"] == "O-2"
        assert p103["review_status"] == "CANDIDATE_ANNOTATION"
        p19 = data["points"]["DC_19"]
        assert p19["review_status"] == "VERIFIED_ANATOMICAL_ANCHOR"


# ============================================================================
# 6. Namespace Isolation and Immutable Reference Invariance
# ============================================================================

def test_who_and_dien_chan_namespace_isolation():
    """Verify WHO acupuncture points and Dien Chan reflexology points remain strictly isolated."""
    engine = FacialRegistrationEngine()
    dc_pts = engine.resolve_points_for_atlas()

    # WHO standard 361 meridian points prefix patterns
    who_prefixes = ("LU", "LI", "ST", "SP", "HT", "SI", "BL", "KI", "PC", "TE", "GB", "LR", "GV", "CV")
    for dc_code in dc_pts.keys():
        assert dc_code.startswith("DC_"), f"Dien Chan code {dc_code} must have DC_ prefix"
        for prefix in who_prefixes:
            # Check not matching e.g. "LI4" or "ST36"
            assert not dc_code.startswith(prefix + "_"), f"Dien Chan code {dc_code} collides with WHO prefix {prefix}"
