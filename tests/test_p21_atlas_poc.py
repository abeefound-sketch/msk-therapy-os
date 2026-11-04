"""
MSK-Therapy-OS — Milestone P21 Automated Test Suite
===================================================
Tests authentic anatomical model assets, multi-layer coverage (bone, muscle, viscera, skin),
surface attachment contracts, safety governance, and sandbox server endpoints.
"""

import json
import os
import re
import socket
import struct
import threading
import time
from pathlib import Path
import urllib.request
import urllib.error
import pytest

from msk_therapy_os.sandbox_p21_adapter import (
    get_p21_metadata,
    get_p21_structures,
    get_representative_structures,
    get_p21_chunk_file,
    save_user_annotation,
    save_user_polyline,
    export_to_vault_markdown,
    get_atlas_sha256,
    ATLAS_JSON_PATH,
    CHUNKS_DIR,
)
from msk_therapy_os.server import create_server


@pytest.fixture(scope="module")
def repo_root():
    return Path(__file__).resolve().parent.parent


class TestP21AssetIntegrityAndCoverage:
    """Verifies that authentic BodyParts3D 4.0 data covers all 4 layers and is 100% offline."""

    def test_atlas_json_checksum_and_schema(self, repo_root):
        assert ATLAS_JSON_PATH.exists(), f"atlas.json must exist at {ATLAS_JSON_PATH}"
        raw = ATLAS_JSON_PATH.read_bytes()
        sha256 = get_atlas_sha256()
        assert sha256 == "c359f4bcd2cba90b7411d66d5e9fc04dc81294d46cd5c1e8b212c824f2e5bbee"

        atlas = json.loads(raw.decode("utf-8"))
        assert atlas["version"] == "BodyParts3D 4.0"
        assert len(atlas["parts"]) == 2234
        assert len(atlas["concepts"]) == 3432
        assert atlas["triangles"] == 2288268
        assert len(atlas["chunks"]) == 15

    def test_all_15_binary_chunks_exist_locally(self, repo_root):
        raw = ATLAS_JSON_PATH.read_bytes()
        atlas = json.loads(raw.decode("utf-8"))
        for c in atlas["chunks"]:
            fname = c["url"].split("/")[-1]
            cpath = CHUNKS_DIR / fname
            assert cpath.exists(), f"Binary chunk {fname} must be present locally"
            assert cpath.stat().st_size == c["bytes"], f"Chunk {fname} byte size mismatch"

    def test_four_layer_anatomical_coverage(self):
        meta = get_p21_metadata()
        counts = meta["statistics"]["layer_counts"]
        
        # 1. Skeletal (Bone)
        assert counts["bone"] == 296, "Must contain all 296 skeletal structures"
        # 2. Muscular (Muscle)
        assert counts["muscle"] == 402, "Must contain all 402 muscular structures"
        # 3. Viscera / Internal Organs
        assert counts["organ"] >= 200, "Must contain >= 200 visceral organ structures"
        # 4. Skin / Exterior
        assert counts["skin"] >= 1, "Must contain full exterior skin manifold"

    def test_body_bounding_box_meters_realistic(self):
        meta = get_p21_metadata()
        bb = meta["bounding_box_meters"]
        
        # Realistic adult male height (1.70 - 1.75 m)
        assert 1.70 <= bb["height_m"] <= 1.75, f"Body height {bb['height_m']} m out of human range"
        # Realistic shoulder span (0.60 - 0.70 m)
        assert 0.60 <= bb["span_m"] <= 0.70, f"Body span {bb['span_m']} m out of human range"
        # Realistic anterior-posterior depth (0.25 - 0.35 m)
        assert 0.25 <= bb["depth_m"] <= 0.35, f"Body depth {bb['depth_m']} m out of human range"

    def test_buffer_offsets_four_byte_aligned(self):
        raw = ATLAS_JSON_PATH.read_bytes()
        atlas = json.loads(raw.decode("utf-8"))
        for p in atlas["parts"]:
            assert p["positions"] % 4 == 0, f"{p['id']} positions offset not 4-byte aligned"
            assert p["indices"] % 4 == 0, f"{p['id']} indices offset not 4-byte aligned"
            assert p["normals"] % 2 == 0, f"{p['id']} normals offset not 2-byte aligned"


class TestP21AnnotationAndGovernanceContract:
    """Verifies safety invariants, attachment schemas, and fail-closed Markdown export."""

    def test_user_annotation_defaults_to_unverified(self):
        annot = {
            "label": "Test LI4 Marker",
            "standard_code": "LI4",
            "anatomical_target": {
                "mesh_id": "FJ3237",
                "structure_name": "Left clavicle",
                "system": "skeletal"
            },
            "spatial_attachment": {
                "world_position": [0.045, 1.412, 0.021],
                "uncertainty_radius_mm": 5.0
            }
        }
        saved = save_user_annotation(annot)
        assert saved["verification_status"] == "USER_ANNOTATED_UNVERIFIED"
        assert saved["anatomical_target"]["asset_sha256"] == get_atlas_sha256()

    def test_polyline_requires_at_least_three_waypoints(self):
        # 2 waypoints must fail
        with pytest.raises(ValueError, match="at least 3 ordered waypoints"):
            save_user_polyline({
                "name": "Invalid Short Polyline",
                "waypoints": [
                    {"index": 0, "world_position": [0.0, 1.0, 0.0]},
                    {"index": 1, "world_position": [0.1, 1.1, 0.0]}
                ]
            })

        # 3 waypoints succeeds
        saved = save_user_polyline({
            "name": "Valid 3-Waypoint Polyline",
            "waypoints": [
                {"index": 0, "world_position": [0.0, 1.0, 0.0]},
                {"index": 1, "world_position": [0.1, 1.1, 0.0]},
                {"index": 2, "world_position": [0.2, 1.2, 0.0]}
            ]
        })
        assert saved["status"] == "USER_DRAFT_UNVERIFIED"
        assert len(saved["waypoints"]) == 3

    def test_markdown_export_includes_provenance_and_unverified_watermark(self):
        md = export_to_vault_markdown({
            "annotations": [{
                "annotation_id": "PT-AUTOTEST-01",
                "label": "Huyệt Hợp Cốc (LI4)",
                "standard_code": "LI4",
                "anatomical_target": {
                    "structure_name": "Left clavicle",
                    "concept_id": "FMA13323",
                    "mesh_id": "FJ3237"
                },
                "spatial_attachment": {
                    "world_position": [0.0452, 1.4120, 0.0210],
                    "uncertainty_radius_mm": 5.0
                },
                "notes": "Mốc quan sát trực tiếp trên xương đòn"
            }],
            "polylines": [{
                "polyline_id": "PL-AUTOTEST-01",
                "name": "Kinh Phế Đoạn Cổ Tay",
                "status": "USER_DRAFT_UNVERIFIED",
                "waypoints": [
                    {"index": 0, "mesh_id": "FJ3237", "world_position": [0.04, 1.41, 0.02], "triangle_index": 10},
                    {"index": 1, "mesh_id": "FJ3262", "world_position": [0.15, 1.35, -0.01], "triangle_index": 20},
                    {"index": 2, "mesh_id": "FJ3262", "world_position": [0.18, 1.21, -0.02], "triangle_index": 30}
                ]
            }]
        })

        assert 'verification_status: "USER_ANNOTATED_UNVERIFIED"' in md
        assert f'source_asset_sha256: "{get_atlas_sha256()}"' in md
        assert "Left clavicle" in md
        assert "FMA13323" in md
        assert "Kinh Phế Đoạn Cổ Tay" in md
        assert "Fail-Closed Verification" in md


class TestP21ServerIntegrationAndRouteIsolation:
    """Tests the HTTP server endpoints for P21 and verifies isolation from P18-P20 routes."""

    @pytest.fixture(scope="class")
    def live_server(self, tmp_path_factory):
        # Find free port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()

        db_path = str(tmp_path_factory.mktemp("p21_srv") / "p21_test.sqlite3")
        server = create_server(db_path=db_path, host="127.0.0.1", port=port)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        base_url = f"http://127.0.0.1:{port}"

        # Wait for server ready
        time.sleep(0.3)
        yield base_url
        server.shutdown()
        server.server_close()

    def test_sandbox_p21_html_route_serves_ok(self, live_server):
        req = urllib.request.Request(f"{live_server}/sandbox/p21/")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "MSK-Therapy-OS · 3D Atlas PoC" in html
            assert "BodyParts3D 4.0" in html

    def test_api_sandbox_metadata(self, live_server):
        req = urllib.request.Request(f"{live_server}/api/sandbox/p21/metadata")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "READY"
            assert data["dataset_name"] == "BodyParts3D Release 4.0"
            assert data["statistics"]["total_structures"] == 2234

    def test_api_sandbox_structures_filter(self, live_server):
        req = urllib.request.Request(f"{live_server}/api/sandbox/p21/structures?layer=bone&limit=5")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            items = json.loads(resp.read().decode("utf-8"))
            assert len(items) == 5
            for it in items:
                assert it["system"] == "skeletal"

    def test_api_sandbox_chunk_streaming(self, live_server):
        req = urllib.request.Request(f"{live_server}/api/sandbox/p21/chunk?name=body-12.bin")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            chunk_data = resp.read()
            assert len(chunk_data) == 4000292

    def test_api_sandbox_chunk_path_traversal_rejected(self, live_server):
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"{live_server}/api/sandbox/p21/chunk?name=../../etc/passwd")
        assert exc_info.value.code == 400

    def test_api_sandbox_post_annotation_and_export_markdown(self, live_server):
        # 1. Post Annotation
        payload = {
            "label": "ST36 Test Point",
            "standard_code": "ST36",
            "anatomical_target": {"mesh_id": "FJ3259", "structure_name": "Left femur", "system": "skeletal"},
            "spatial_attachment": {"world_position": [0.08, 0.65, -0.02], "uncertainty_radius_mm": 5.0}
        }
        req = urllib.request.Request(
            f"{live_server}/api/sandbox/p21/annotation",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 201
            saved = json.loads(resp.read().decode("utf-8"))
            assert saved["verification_status"] == "USER_ANNOTATED_UNVERIFIED"

        # 2. Export Markdown
        exp_payload = {"annotations": [saved], "polylines": []}
        exp_req = urllib.request.Request(
            f"{live_server}/api/sandbox/p21/export-markdown",
            data=json.dumps(exp_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(exp_req) as resp:
            assert resp.status == 200
            res = json.loads(resp.read().decode("utf-8"))
            assert "ST36 Test Point" in res["markdown"]
            assert "Left femur" in res["markdown"]

    def test_route_isolation_atlas_and_education_unaffected(self, live_server):
        # Original /education route remains untouched
        edu_req = urllib.request.Request(f"{live_server}/education/")
        with urllib.request.urlopen(edu_req) as resp:
            assert resp.status == 200
            text = resp.read().decode("utf-8")
            assert "Biomechanics Education Studio" in text

        # Original /atlas route remains untouched
        atlas_req = urllib.request.Request(f"{live_server}/atlas/")
        with urllib.request.urlopen(atlas_req) as resp:
            assert resp.status == 200
