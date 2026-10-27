"""Comprehensive Unit and Integration Test Suite for P9.4 Definitive Meridian Atlas Data Correction.

Validates:
1. WHO 2008 Acupoint Localization Rules & Geometric Resolution Engine.
2. Meridian Route Graph Topology, Multi-Branch Partitioning, and Intermediate Turning Waypoints.
3. SQLite Schema Migration, Seeding, Coverage Dashboard, and Audit Revision / Review Workflow.
4. End-to-End Dynamic Spatial Resolution & Knot Residual Verification (0.000 mm).
5. REST API Endpoints: Coverage, Route Graph, Revisions, Reviews, and Rollback.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import tempfile
import threading
import urllib.parse
import urllib.request
import pytest

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.landmark_registry import LandmarkRegistry, CANONICAL_LANDMARKS
from msk_therapy_os.cun_scaling import CunScalingEngine, WHO_BONE_SEGMENTS
from msk_therapy_os.point_localization_rules import (
    ACUPOINT_LOCALIZATION_RULES,
    AcupointLocalizationEngine,
    LocalizationMethod,
)
from msk_therapy_os.meridian_route_graph import (
    MeridianRouteGraph,
    RouteBranch,
    RouteWaypoint,
    WaypointType,
)
from msk_therapy_os.spatial_resolver import (
    AnatomicalSpatialResolver,
    AUDITED_CANONICAL_POINTS,
    CANONICAL_MESH_ID,
    CANONICAL_MESH_HASH,
)
from msk_therapy_os.meridian_surface_engine import MeridianSurfacePathEngine
from msk_therapy_os.points import (
    init_points_tables,
    get_meridian_atlas_coverage_dashboard,
    get_meridian_route_graph_data,
    create_meridian_route_revision,
    review_meridian_route_revision,
    rollback_meridian_route_revision,
)
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler


class TestP94LocalizationRulesEngine:
    """Validates the WHO 2008 Acupoint Localization Rules Engine."""

    def setup_method(self):
        self.engine = AcupointLocalizationEngine()

    def test_rules_catalog_coverage(self):
        """Ensure catalog contains rules across classical channels."""
        assert len(ACUPOINT_LOCALIZATION_RULES) >= 60
        channels = set(r.meridian_code for r in ACUPOINT_LOCALIZATION_RULES.values())
        assert len(channels) == 14
        for ch in ["LU", "LI", "ST", "SP", "HT", "SI", "BL", "KI", "PC", "TE", "GB", "LR", "GV", "CV"]:
            assert ch in channels

    def test_point_resolution_accuracy(self):
        """Test geometric coordinate computation from anatomical landmarks."""
        # Test LU1 (Parasagittal chest)
        lu1 = self.engine.resolve_point_location("LU1", side="right")
        assert lu1 is not None
        assert lu1["point_code"] == "LU1"
        assert lu1["quality_class"] == "CLASS_B"
        assert lu1["canonical_position"][0] > 0.05  # Right side +X
        assert lu1["canonical_position"][1] > 1.2   # Upper chest
        assert "FMA:24074" in lu1["fma_anchor"]

        # Test LU1 left laterality
        lu1_left = self.engine.resolve_point_location("LU1", side="left")
        assert lu1_left is not None
        assert lu1_left["canonical_position"][0] < -0.05  # Left side -X
        assert abs(lu1_left["canonical_position"][0] + lu1["canonical_position"][0]) < 1e-4

        # Test SP6 (3 cun proximal to medial malleolus)
        sp6 = self.engine.resolve_point_location("SP6", side="right")
        assert sp6 is not None
        assert sp6["canonical_position"][1] > 0.1  # Proximal to malleolus
        assert sp6["canonical_position"][1] < 0.35

        # Test GV20 (Vertex midline)
        gv20 = self.engine.resolve_point_location("GV20")
        assert gv20 is not None
        assert abs(gv20["canonical_position"][0]) < 1e-4  # Midline X == 0
        assert gv20["canonical_position"][1] > 1.65       # Vertex of head


class TestP94MeridianRouteGraph:
    """Validates multi-branch topologies, turning waypoints, and gap protection."""

    def setup_method(self):
        self.graph = MeridianRouteGraph()

    def test_all_14_channels_present(self):
        """Verify all 14 channels have defined branches."""
        branches = self.graph.get_all_branches()
        assert len(branches) >= 30
        channels = set(b.channel_code for b in branches)
        assert len(channels) == 14

    def test_gallbladder_auricular_looping_waypoints(self):
        """Verify Gallbladder Cranial branch has intermediate turning waypoints around the ear."""
        gb_branches = self.graph.get_channel_branches("GB", side="right")
        assert len(gb_branches) >= 3
        cranial = [b for b in gb_branches if "CRANIAL" in b.branch_id][0]
        wp_types = [w.waypoint_type for w in cranial.waypoints]
        assert WaypointType.TURNING_WAYPOINT in wp_types
        assert any(w.waypoint_code == "WP_GB_TEMPLE_CURVE" for w in cranial.waypoints)
        assert any(w.waypoint_code == "WP_GB_EAR_SUPERIOR" for w in cranial.waypoints)
        assert any(w.waypoint_code == "WP_GB_MASTOID_POSTERIOR" for w in cranial.waypoints)

    def test_bladder_dual_column_and_junction(self):
        """Verify Bladder has dual paravertebral columns and popliteal junction."""
        bl_branches = self.graph.get_channel_branches("BL", side="right")
        assert len(bl_branches) >= 3
        branch_ids = [b.branch_id for b in bl_branches]
        assert any("INNER" in b_id for b_id in branch_ids)
        assert any("OUTER" in b_id for b_id in branch_ids)
        assert any("CALF" in b_id for b_id in branch_ids)

        inner = [b for b in bl_branches if "INNER" in b.branch_id][0]
        assert any(w.waypoint_type == WaypointType.BRANCH_JUNCTION for w in inner.waypoints)

    def test_explicit_gaps_in_internal_trajectories(self):
        """Verify non-surface conceptual jumps have has_gaps=True."""
        st_branches = self.graph.get_channel_branches("ST", side="right")
        facial = [b for b in st_branches if "FACIAL" in b.branch_id][0]
        assert facial.has_gaps is True
        assert "ST8 to neck ST9" in facial.gap_description

        ki_branches = self.graph.get_channel_branches("KI", side="right")
        lower_ki = [b for b in ki_branches if "LOWER" in b.branch_id][0]
        assert lower_ki.has_gaps is True


class TestP94SQLitePersistenceAndWorkflow:
    """Validates SQLite schema migrations, coverage metrics, and audit revision workflow."""

    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        self.db_path = str(tmp_path / "test_p9_4.sqlite3")
        with open_db(self.db_path) as db:
            init_db(db)
            seed_db(db)
            init_points_tables(db)

    def test_tables_created_and_seeded(self):
        """Verify all 7 tables exist and are populated."""
        with open_db(self.db_path) as db:
            cur = db.cursor()
            cur.execute("SELECT COUNT(*) FROM acupoint_localization_rules")
            assert cur.fetchone()[0] >= 60

            cur.execute("SELECT COUNT(*) FROM anatomical_point_references")
            assert cur.fetchone()[0] == 362

            cur.execute("SELECT COUNT(*) FROM meridian_route_graphs")
            assert cur.fetchone()[0] == 14

            cur.execute("SELECT COUNT(*) FROM meridian_route_waypoints")
            assert cur.fetchone()[0] >= 100

            cur.execute("SELECT COUNT(*) FROM meridian_geometry_validation")
            assert cur.fetchone()[0] >= 14

    def test_coverage_dashboard_metrics(self):
        """Verify live coverage calculation from SQLite."""
        with open_db(self.db_path) as db:
            cov = get_meridian_atlas_coverage_dashboard(db)
            assert cov["status"] == "success"
            assert cov["total_points"] == 362
            dist = cov["class_distribution"]
            assert dist["CLASS_A"] == 18
            assert dist["CLASS_B"] >= 50
            assert dist["CLASS_D"] >= 200
            assert cov["verified_percentage"] >= 19.0
            assert len(cov["channels"]) == 14

    def test_revision_and_review_lifecycle(self):
        """Verify revision submission, peer review approval, and rollback state machine."""
        with open_db(self.db_path) as db:
            # 1. Propose revision
            rev_id = create_meridian_route_revision(
                db,
                channel_code="GB",
                branch_id="GB_R_B1_CRANIAL",
                revision_type="MOVE_WAYPOINT",
                target_id="WP_GB_R_01",
                old_state={"pos_x": 0.0650, "pos_y": 1.6250, "pos_z": 0.0750},
                new_state={"pos_x": 0.0655, "pos_y": 1.6252, "pos_z": 0.0752},
                clinical_justification="Calibrate outer canthus clearance on FJ2810 mesh",
                author="Dr. Lead Anatomist, MD",
            )
            assert rev_id > 0

            # 2. Review and approve
            res = review_meridian_route_revision(
                db,
                revision_id=rev_id,
                reviewer="Chief Medical Officer",
                decision="APPROVED",
                comments="Valid clinical calibration",
            )
            assert res["status"] == "APPROVED"
            assert res["applied"] is True

            # Verify waypoint updated
            cur = db.cursor()
            cur.execute("SELECT pos_x FROM meridian_route_waypoints WHERE waypoint_id = ?", ("WP_GB_R_01",))
            assert round(cur.fetchone()[0], 4) == 0.0655

            # 3. Rollback
            rb = rollback_meridian_route_revision(db, revision_id=rev_id, author="Dr. Lead Anatomist")
            assert rb["status"] == "ROLLED_BACK"

            # Verify historical coordinate restored
            cur.execute("SELECT pos_x FROM meridian_route_waypoints WHERE waypoint_id = ?", ("WP_GB_R_01",))
            assert round(cur.fetchone()[0], 4) == 0.0650


class TestP94SpatialResolverAndReconstruction:
    """Validates spatial resolver quality breakdown and spline reconstruction."""

    def setup_method(self):
        self.resolver = AnatomicalSpatialResolver()

    def test_canonical_resolution_and_quality_classes(self):
        """Test canonical layer mode returns quality classes breakdown."""
        geo = self.resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        summary = geo["summary"]
        assert summary["total_resolved_points"] == 362
        assert summary["verified_anchor_count"] == 18
        assert summary["landmark_derived_count"] >= 50
        assert summary["meridian_count"] == 14

        qcs = summary["quality_classes"]
        assert qcs["CLASS_A"] == 18
        assert qcs["CLASS_B"] >= 50
        assert qcs["CLASS_D"] >= 200

    def test_meridian_pass_through_residual(self):
        """Verify 0.0000 mm residual across all channels in canonical mode."""
        geo = self.resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        meridians = geo["meridians"]
        for c_code, m_data in meridians.items():
            for p in m_data["paths"]:
                assert p["point_residual_max_mm"] == 0.0
                assert p["point_residual_mean_mm"] == 0.0
                assert p["point_count"] > 0
                assert len(p["surface_vertices"]) == p["point_count"]
                assert len(p["surface_normals"]) == p["point_count"]


@pytest.fixture(scope="module")
def live_server_p94(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port with test database."""
    tmp_dir = tmp_path_factory.mktemp("p94_server_test")
    test_db_file = tmp_dir / "test_p94.sqlite3"

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


class TestP94RestApiEndpoints:
    """Validates HTTP REST endpoints for coverage, route-graph, and revisions."""

    def test_get_coverage_endpoint(self, live_server_p94):
        req = urllib.request.urlopen(f"{live_server_p94}/api/atlas/meridians/coverage")
        assert req.status == 200
        data = json.loads(req.read().decode())
        assert data["status"] == "success"
        assert data["total_points"] == 362
        assert data["verified_percentage"] >= 19.0
        assert len(data["channels"]) == 14

    def test_get_route_graph_endpoint(self, live_server_p94):
        req = urllib.request.urlopen(f"{live_server_p94}/api/atlas/meridians/route-graph?channel_code=GB")
        assert req.status == 200
        data = json.loads(req.read().decode())
        assert data["status"] == "success"
        assert data["channel_count"] == 1
        g = data["route_graphs"][0]
        assert g["channel_code"] == "GB"
        assert len(g["waypoints"]) >= 20

    def test_revision_and_review_rest_workflow(self, live_server_p94):
        # 1. POST revision
        rev_payload = json.dumps({
            "channel_code": "BL",
            "branch_id": "BL_R_B1_INNER",
            "revision_type": "MOVE_WAYPOINT",
            "target_id": "WP_BL_R_40",
            "old_state": {"pos_x": 0.1180, "pos_y": 0.4450, "pos_z": -0.0780},
            "new_state": {"pos_x": 0.1182, "pos_y": 0.4451, "pos_z": -0.0781},
            "clinical_justification": "Popliteal junction fine realignment",
            "author": "Dr. Anatomist, PT",
        }).encode()
        req = urllib.request.Request(
            f"{live_server_p94}/api/atlas/meridians/revisions",
            data=rev_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        res = json.loads(urllib.request.urlopen(req).read().decode())
        assert res["status"] == "success"
        rev_id = res["revision_id"]

        # 2. POST review
        review_payload = json.dumps({
            "reviewer": "Director of Anatomy",
            "decision": "APPROVED",
            "comments": "Anatomically sound adjustment",
        }).encode()
        req_review = urllib.request.Request(
            f"{live_server_p94}/api/atlas/meridians/revisions/{rev_id}/review",
            data=review_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        res_review = json.loads(urllib.request.urlopen(req_review).read().decode())
        assert res_review["status"] == "success"
        assert res_review["review"]["status"] == "APPROVED"

        # 3. POST rollback
        rollback_payload = json.dumps({"author": "Director of Anatomy"}).encode()
        req_rollback = urllib.request.Request(
            f"{live_server_p94}/api/atlas/meridians/revisions/{rev_id}/rollback",
            data=rollback_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        res_rollback = json.loads(urllib.request.urlopen(req_rollback).read().decode())
        assert res_rollback["status"] == "success"
        assert res_rollback["rollback"]["status"] == "ROLLED_BACK"
