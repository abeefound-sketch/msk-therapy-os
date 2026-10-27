"""End-to-End Geometric and API Integration Tests for P9.2 Dynamic Spatial Resolver.

Validates the full chain:
Upstream -> Canonical Registration -> Anatomical Anchors -> Cun Scaling -> Morphology -> Pose Transform -> Guarded Surface Projection -> WebGL/SVG Rendering
"""
from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
import threading
import urllib.request
import urllib.parse
from pathlib import Path
import pytest

from msk_therapy_os.spatial_resolver import (
    AnatomicalSpatialResolver,
    AUDITED_CANONICAL_POINTS,
    CANONICAL_MESH_ID,
    CANONICAL_MESH_HASH,
    ENGINE_VERSION,
)
from msk_therapy_os.server import MSKRequestHandler
from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables


@pytest.fixture(scope="module")
def live_server_p92(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port with an initialized temp db."""
    tmp_dir = tmp_path_factory.mktemp("p92_server_test")
    test_db_file = tmp_dir / "test_p92.sqlite3"

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


class TestAnatomicalSpatialResolverCore:
    """Core algorithmic tests for AnatomicalSpatialResolver."""

    def test_canonical_resolution_audited_points(self):
        resolver = AnatomicalSpatialResolver()
        res = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})

        assert res["status"] == "success"
        assert res["layer_mode"] == "canonical"
        assert res["mesh_id"] == CANONICAL_MESH_ID
        assert res["mesh_hash"] == CANONICAL_MESH_HASH
        assert res["engine_version"] == ENGINE_VERSION

        points = res["points"]
        assert len(points) >= 361

        # Check mandatory points: LI4, LU5, BL40, PC6, GB21, ST36
        test_codes = ["LI4", "LU5", "BL40", "PC6", "GB21", "ST36"]
        for code in test_codes:
            assert code in points, f"Missing point {code}"
            p = points[code]
            assert p["registration_status"] == "VERIFIED_ANATOMICAL_ANCHOR"
            assert p["registration_mode"] == "canonical"
            assert p["residual_error_mm"] is not None
            assert p["uncertainty_mm"] is not None
            assert p["residual_error_mm"] > 0.0  # Real computed displacement from legacy
            assert p["fma_id"] is not None
            assert p["skeletal_anchor"] is not None

            # Compare against audited ground truth
            gt = AUDITED_CANONICAL_POINTS[code]
            assert p["canonical_position"] == list(gt["canonical_position"])
            assert p["resolved_world_position"] == list(gt["canonical_position"])
            assert p["legacy_position"] == list(gt["legacy_position"])

    def test_layer_modes_produce_distinct_geometries(self):
        resolver = AnatomicalSpatialResolver()

        can_res = resolver.resolve_atlas_geometry({"layer_mode": "canonical", "point_ids": ["LI4"]})
        leg_res = resolver.resolve_atlas_geometry({"layer_mode": "legacy_raycast", "point_ids": ["LI4"]})
        ups_res = resolver.resolve_atlas_geometry({"layer_mode": "upstream_raw", "point_ids": ["LI4"]})

        pos_can = can_res["points"]["LI4"]["resolved_world_position"]
        pos_leg = leg_res["points"]["LI4"]["resolved_world_position"]
        pos_ups = ups_res["points"]["LI4"]["resolved_world_position"]

        # Ensure all 3 layers produce numerically distinct coordinates
        assert pos_can != pos_leg, f"Canonical {pos_can} and Legacy {pos_leg} must differ"
        assert pos_can != pos_ups, f"Canonical {pos_can} and Upstream {pos_ups} must differ"
        assert pos_leg != pos_ups, f"Legacy {pos_leg} and Upstream {pos_ups} must differ"

        assert leg_res["points"]["LI4"]["registration_status"] == "LEGACY_SURFACE_RAYCAST"
        assert ups_res["points"]["LI4"]["registration_status"] == "UPSTREAM_TRANSFORMED"

    def test_posture_sensitivity_and_uncertainty_emission(self):
        resolver = AnatomicalSpatialResolver()

        # Rest pose (neutral joints)
        neutral_res = resolver.resolve_atlas_geometry({
            "layer_mode": "pose_adjusted",
            "point_ids": ["LU5", "BL40", "LI4"],
            "pose": {"joint_angles": {"elbow_flexion_r": 0.0, "knee_flexion_r": 0.0}},
        })
        assert neutral_res["points"]["LU5"]["registration_status"] == "VERIFIED_ANATOMICAL_ANCHOR"
        assert neutral_res["points"]["LU5"]["pose_validity"]["is_valid"] is True
        assert neutral_res["points"]["BL40"]["pose_validity"]["is_valid"] is True

        # Articulated pose: Elbow flexed 35.0 deg (> 15 deg threshold) & Knee flexed 40.0 deg (> 15 deg threshold)
        flexed_res = resolver.resolve_atlas_geometry({
            "layer_mode": "pose_adjusted",
            "point_ids": ["LU5", "BL40", "LI4"],
            "pose": {"joint_angles": {"elbow_flexion_r": 35.0, "knee_flexion_r": 40.0}},
        })

        lu5 = flexed_res["points"]["LU5"]
        bl40 = flexed_res["points"]["BL40"]
        li4 = flexed_res["points"]["LI4"]

        # Posture-sensitive crease points MUST emit UNCERTAIN_POSTURE_OFFSET
        assert lu5["registration_status"] == "UNCERTAIN_POSTURE_OFFSET"
        assert lu5["pose_validity"]["is_valid"] is False
        assert lu5["rejection_reason"] is not None
        assert "exceeds posture calibration threshold" in lu5["rejection_reason"]

        assert bl40["registration_status"] == "UNCERTAIN_POSTURE_OFFSET"
        assert bl40["pose_validity"]["is_valid"] is False

        # Invariant bony landmark LI4 remains valid
        assert li4["registration_status"] == "VERIFIED_ANATOMICAL_ANCHOR"
        assert li4["pose_validity"]["is_valid"] is True

    def test_morphology_scaling(self):
        resolver = AnatomicalSpatialResolver()

        # Baseline height 172cm vs Tall stature 190cm
        base_res = resolver.resolve_atlas_geometry({
            "layer_mode": "pose_adjusted",
            "point_ids": ["GV14"],
            "morphology": {"height_cm": 172.0},
        })
        tall_res = resolver.resolve_atlas_geometry({
            "layer_mode": "pose_adjusted",
            "point_ids": ["GV14"],
            "morphology": {"height_cm": 190.0},
        })

        y_base = base_res["points"]["GV14"]["resolved_world_position"][1]
        y_tall = tall_res["points"]["GV14"]["resolved_world_position"][1]

        expected_ratio = 190.0 / 172.0
        assert y_tall == pytest.approx(y_base * expected_ratio, rel=1e-3)
        assert tall_res["points"]["GV14"]["morphology_validity"]["is_scaled"] is True

    def test_surface_conforming_meridians(self):
        resolver = AnatomicalSpatialResolver()

        # Resolve Lung Meridian (LU)
        res = resolver.resolve_atlas_geometry({
            "layer_mode": "canonical",
            "meridian_ids": ["LU"],
        })

        assert "LU" in res["meridians"]
        lu_m = res["meridians"]["LU"]
        assert len(lu_m["paths"]) >= 1
        for p in lu_m["paths"]:
            assert len(p["surface_vertices"]) > 0
            assert "Educational visualization approximation" in p["disclaimer"]

    def test_zero_fabricated_claims_on_unregistered_points(self):
        resolver = AnatomicalSpatialResolver()

        # Points not in the audited catalog must NOT claim VERIFIED_ANATOMICAL_ANCHOR or fake residuals
        res = resolver.resolve_atlas_geometry({
            "layer_mode": "canonical",
            "point_ids": ["LI2"],  # LI2 is an uncalibrated point (Class D)
        })

        if "LI2" in res["points"]:
            li2 = res["points"]["LI2"]
            assert li2["registration_status"] != "VERIFIED_ANATOMICAL_ANCHOR"
            assert li2["registration_status"] == "GEOMETRIC_SURFACE_APPROXIMATION"
            assert li2["residual_error_mm"] is None
            assert li2["uncertainty_mm"] is None


class TestAtlasSpatialResolutionAPI:
    """HTTP API integration tests for /api/atlas/geometry/resolve."""

    def test_post_resolve_geometry_success(self, live_server_p92):
        url = f"{live_server_p92}/api/atlas/geometry/resolve"
        payload = {
            "layer_mode": "canonical",
            "point_ids": ["LI4", "LU5", "BL40"],
            "morphology": {"height_cm": 175.0, "shoulder_width_cm": 44.0},
            "pose": {"joint_angles": {"elbow_flexion_r": 10.0}},
            "client_generation": 42,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "success"
            assert data["client_generation"] == 42
            assert data["layer_mode"] == "canonical"
            assert len(data["points"]) == 3
            assert "LI4" in data["points"]
            assert data["points"]["LI4"]["registration_status"] == "VERIFIED_ANATOMICAL_ANCHOR"

    def test_get_resolve_geometry_success(self, live_server_p92):
        url = f"{live_server_p92}/api/atlas/geometry/resolve?layer_mode=legacy_raycast"
        req = urllib.request.Request(url)

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "success"
            assert data["layer_mode"] == "legacy_raycast"
            assert data["summary"]["total_resolved_points"] >= 360

    def test_post_resolve_geometry_rejects_invalid_layer_mode(self, live_server_p92):
        url = f"{live_server_p92}/api/atlas/geometry/resolve"
        payload = {"layer_mode": "invalid_mode_xyz"}

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)
        assert exc_info.value.code == 400

    def test_post_resolve_geometry_rejects_non_dict_payload(self, live_server_p92):
        url = f"{live_server_p92}/api/atlas/geometry/resolve"
        payload = ["invalid", "array", "payload"]

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)
        assert exc_info.value.code == 400
