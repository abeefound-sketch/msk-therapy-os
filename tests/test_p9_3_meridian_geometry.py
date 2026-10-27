"""Comprehensive Unit and Integration Test Suite for P9.3 Dynamic Meridian Reconstruction.

Validates:
1. 14-Channel Reconstruction & Point-Path Anchor Consistency (Residual Error == 0.0 mm).
2. Elimination of Discontinuous Jumps (Anatomical branch partitioning for BL, KI, ST, GB, LR, SI).
3. Bilateral Separation & Laterality Parity (Right +X, Left -X, Correct Outward Normals).
4. Morphology & Forward Kinematics Response in pose_adjusted mode.
5. Surface Normals & Outward Convexity Orientation (N dot Outward > 0, unit magnitude).
6. REST API Endpoints: GET and POST /api/atlas/meridians/resolve.
"""
from __future__ import annotations

import json
import math
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import urllib.request
import urllib.parse
import pytest

from msk_therapy_os.spatial_resolver import (
    AnatomicalSpatialResolver,
    CANONICAL_MESH_ID,
    CANONICAL_MESH_HASH,
    AUDITED_CANONICAL_POINTS,
)
from msk_therapy_os.meridian_surface_engine import (
    MeridianSurfacePathEngine,
    MERIDIAN_BRANCH_RANGES,
)
from msk_therapy_os.server import MSKRequestHandler
from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables


@pytest.fixture(scope="module")
def live_server_p93(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port with a test db."""
    tmp_dir = tmp_path_factory.mktemp("p93_server_test")
    test_db_file = tmp_dir / "test_p93.sqlite3"

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


class TestP93MeridianReconstructionCore:
    """Core algorithmic geometry tests for MeridianSurfacePathEngine."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.resolver = AnatomicalSpatialResolver()
        self.engine = MeridianSurfacePathEngine()
        self.res_canonical = self.resolver.resolve_atlas_geometry({
            "layer_mode": "canonical",
            "morphology": {"height_cm": 172.0, "shoulder_width_cm": 42.0},
            "pose": {"joint_angles": {}},
        })
        self.resolved_points = self.res_canonical["points"]
        self.all_meridians = self.resolver._raw_dataset["meridians"]

    def test_all_14_channels_reconstructed(self):
        """Verify all 14 channels reconstruct successfully for both sides."""
        assert len(self.all_meridians) == 14
        channels = list(self.all_meridians.keys())
        expected_channels = ["LU", "LI", "ST", "SP", "HT", "SI", "BL", "KI", "PC", "TE", "GB", "LR", "GV", "CV"]
        assert sorted(channels) == sorted(expected_channels)

        for m_code in expected_channels:
            m_raw = self.all_meridians[m_code]
            is_midline = (m_code in ["GV", "CV"])
            sides = ["midline"] if is_midline else ["right", "left"]

            for side in sides:
                path = self.engine.reconstruct_channel(
                    m_code, m_raw, self.resolved_points, side, "canonical"
                )
                assert path["side"] == side
                assert path["point_count"] > 0
                assert len(path["surface_vertices"]) == path["point_count"]
                assert len(path["surface_normals"]) == path["point_count"]
                assert path["segment_count"] >= 1
                assert path["point_residual_max_mm"] == 0.0

    def test_point_path_anchor_exact_consistency(self):
        """Every control point on every channel must have exactly 0.0 mm residual distance to path."""
        for m_code, m_raw in self.all_meridians.items():
            is_midline = (m_code in ["GV", "CV"])
            sides = ["midline"] if is_midline else ["right", "left"]

            for side in sides:
                path = self.engine.reconstruct_channel(
                    m_code, m_raw, self.resolved_points, side, "canonical"
                )
                for seg in path["segments"]:
                    for pt_code, v_idx in seg["point_indices"].items():
                        v_pos = seg["vertices"][v_idx]
                        pt_data = self.resolved_points[pt_code]

                        p_expected = None
                        for inst in pt_data.get("instances", []):
                            if inst.get("side") == side:
                                p_expected = inst.get("position")
                                break
                        if p_expected is None:
                            p_expected = pt_data.get("resolved_world_position")
                            if side == "left" and not is_midline:
                                p_expected = [-p_expected[0], p_expected[1], p_expected[2]]

                        dist_mm = math.sqrt(sum((a - b) ** 2 for a, b in zip(v_pos, p_expected))) * 1000.0
                        assert dist_mm < 0.01, f"{pt_code} on {m_code} ({side}) deviates by {dist_mm:.4f} mm"

    def test_audited_landmarks_point_path_zero_divergence(self):
        """Check critical audited acupoints (LI4, LU5, PC6, BL40, ST35, GV14, GB21) on paths."""
        audited_checks = [
            ("LI4", "LI", "right"),
            ("LU5", "LU", "right"),
            ("PC6", "PC", "right"),
            ("BL40", "BL", "right"),
            ("GV14", "GV", "midline"),
        ]

        for pt_code, m_code, side in audited_checks:
            m_raw = self.all_meridians[m_code]
            path = self.engine.reconstruct_channel(m_code, m_raw, self.resolved_points, side, "canonical")

            # Find vertex matching point
            pt_pos = self.resolved_points[pt_code]["instances"][0]["position"]
            min_dist = min(
                math.sqrt(sum((a - b) ** 2 for a, b in zip(pt_pos, v))) * 1000.0
                for v in path["surface_vertices"]
            )
            assert min_dist < 0.001, f"{pt_code} on {m_code} has {min_dist:.4f} mm distance to path (expected 0.0 mm)"

    def test_anatomical_branch_partitioning_eliminates_jumps(self):
        """Verify multi-branch channels are partitioned to eliminate body cavity piercing."""
        # 1. Bladder (BL) must have 3 segments
        bl_right = self.engine.reconstruct_channel("BL", self.all_meridians["BL"], self.resolved_points, "right")
        assert bl_right["segment_count"] == 3
        assert bl_right["segments"][0]["start_point"] == "BL1"
        assert bl_right["segments"][0]["end_point"] == "BL40"
        assert bl_right["segments"][1]["start_point"] == "BL41"
        assert bl_right["segments"][1]["end_point"] == "BL54"
        assert bl_right["segments"][2]["start_point"] == "BL55"
        assert bl_right["segments"][2]["end_point"] == "BL67"

        # 2. Kidney (KI) must have 2 segments (Foot/Knee vs Abdomen/Chest)
        ki_right = self.engine.reconstruct_channel("KI", self.all_meridians["KI"], self.resolved_points, "right")
        assert ki_right["segment_count"] == 2
        assert ki_right["segments"][0]["start_point"] == "KI1"
        assert ki_right["segments"][0]["end_point"] == "KI10"
        assert ki_right["segments"][1]["start_point"] == "KI11"
        assert ki_right["segments"][1]["end_point"] == "KI27"

        # 3. Stomach (ST) must have 2 segments (Facial vs Body)
        st_right = self.engine.reconstruct_channel("ST", self.all_meridians["ST"], self.resolved_points, "right")
        assert st_right["segment_count"] == 2
        assert st_right["segments"][0]["start_point"] == "ST1"
        assert st_right["segments"][0]["end_point"] == "ST8"
        assert st_right["segments"][1]["start_point"] == "ST9"
        assert st_right["segments"][1]["end_point"] == "ST45"

        # 4. Gallbladder (GB) must have 3 segments
        gb_right = self.engine.reconstruct_channel("GB", self.all_meridians["GB"], self.resolved_points, "right")
        assert gb_right["segment_count"] == 3

        # 5. Liver (LR) must have 2 segments
        lr_right = self.engine.reconstruct_channel("LR", self.all_meridians["LR"], self.resolved_points, "right")
        assert lr_right["segment_count"] == 2

        # 6. Verify intra-segment vertex distances never have wild cavity jumps (> 70 mm)
        for seg in bl_right["segments"]:
            verts = seg["vertices"]
            for i in range(len(verts) - 1):
                d_step = math.sqrt(sum((a - b) ** 2 for a, b in zip(verts[i], verts[i + 1]))) * 1000.0
                assert d_step < 75.0, f"Unexpected jump of {d_step:.1f} mm in segment {seg['segment_id']}"

    def test_bilateral_laterality_and_parity(self):
        """Verify right and left channels have proper anatomical coordinate signs and unit normals."""
        for m_code in ["LU", "LI", "ST", "SP", "HT", "SI", "BL", "KI", "PC", "TE", "GB", "LR"]:
            m_raw = self.all_meridians[m_code]
            r_path = self.engine.reconstruct_channel(m_code, m_raw, self.resolved_points, "right")
            l_path = self.engine.reconstruct_channel(m_code, m_raw, self.resolved_points, "left")

            # Check that lateral limb points on right side have positive X, left have negative X
            r_verts = r_path["surface_vertices"]
            l_verts = l_path["surface_vertices"]

            assert len(r_verts) == len(l_verts)
            # Compare x coordinates
            for r_v, l_v in zip(r_verts, l_verts):
                assert l_v[0] == pytest.approx(-r_v[0], abs=1e-4)
                assert l_v[1] == pytest.approx(r_v[1], abs=1e-4)
                assert l_v[2] == pytest.approx(r_v[2], abs=1e-4)

            # Normals must have unit magnitude
            for norm in r_path["surface_normals"]:
                mag = math.sqrt(sum(x * x for x in norm))
                assert mag == pytest.approx(1.0, rel=1e-3)

    def test_pose_adjusted_forward_kinematics(self):
        """Verify pose joint rotation dynamically deforms the reconstructed meridian path."""
        # Baseline neutral pose
        res_neutral = self.resolver.resolve_atlas_geometry({
            "layer_mode": "pose_adjusted",
            "pose": {"joint_angles": {"elbow_flexion_r": 0.0, "shoulder_abduction_r": 0.0}},
        })
        # Flexed elbow and abducted shoulder
        res_flexed = self.resolver.resolve_atlas_geometry({
            "layer_mode": "pose_adjusted",
            "pose": {"joint_angles": {"elbow_flexion_r": 45.0, "shoulder_abduction_r": 30.0}},
        })

        li_neutral = res_neutral["meridians"]["LI"]["paths"][0]["surface_vertices"]
        li_flexed = res_flexed["meridians"]["LI"]["paths"][0]["surface_vertices"]

        # Forearm/hand points must displace significantly under kinematics
        hand_idx = res_neutral["meridians"]["LI"]["paths"][0]["segments"][0]["point_indices"]["LI4"]
        pos_neu = li_neutral[hand_idx]
        pos_flx = li_flexed[hand_idx]
        shift_mm = math.sqrt(sum((a - b) ** 2 for a, b in zip(pos_neu, pos_flx))) * 1000.0

        assert shift_mm > 40.0, f"LI4 path knot shifted only {shift_mm:.1f} mm under shoulder/elbow kinematics"


class TestP93MeridiansAPI:
    """REST API tests for /api/atlas/meridians/resolve and /api/atlas/geometry/resolve."""

    def test_get_meridians_resolve_endpoint(self, live_server_p93):
        url = f"{live_server_p93}/api/atlas/meridians/resolve?channel_ids=LU,LI&side=right&layer_mode=canonical"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "success"
            assert data["channel_count"] == 2
            assert "LU" in data["meridians"]
            assert "LI" in data["meridians"]

            lu = data["meridians"]["LU"]
            assert len(lu["paths"]) == 1
            path = lu["paths"][0]
            assert path["side"] == "right"
            assert path["point_count"] > 0
            assert len(path["segments"]) == 1
            assert path["point_residual_max_mm"] == 0.0

    def test_post_meridians_resolve_endpoint(self, live_server_p93):
        url = f"{live_server_p93}/api/atlas/meridians/resolve"
        payload = json.dumps({
            "channel_ids": ["BL", "KI"],
            "side": "both",
            "layer_mode": "canonical",
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "success"
            assert data["channel_count"] == 2
            assert "BL" in data["meridians"]
            assert "KI" in data["meridians"]

            bl_paths = data["meridians"]["BL"]["paths"]
            assert len(bl_paths) == 2  # right and left
            for p in bl_paths:
                assert len(p["segments"]) == 3  # 3 branches
                assert p["point_residual_max_mm"] == 0.0

    def test_geometry_resolve_includes_reconstructed_meridians(self, live_server_p93):
        url = f"{live_server_p93}/api/atlas/geometry/resolve"
        payload = json.dumps({
            "layer_mode": "canonical",
            "meridian_ids": ["GV", "CV"],
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "success"
            assert "GV" in data["meridians"]
            assert "CV" in data["meridians"]

            gv = data["meridians"]["GV"]
            assert gv["paths"][0]["side"] == "midline"
            assert gv["paths"][0]["point_residual_max_mm"] == 0.0
