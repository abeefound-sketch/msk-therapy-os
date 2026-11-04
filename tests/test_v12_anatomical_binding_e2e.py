"""
MSK-Therapy-OS V1.2 — Anatomical Binding System (ABS) E2E Tests
===============================================================
Comprehensive automated audit verifying:
1. REST API endpoints for V1.2 metadata, skeleton contract, rigid bones, muscles, anchors, kinematics.
2. Playwright Chromium browser execution loading /character_v12/index.html.
3. Three.js SkinnedMesh (Skin), Skeleton (4 arm bones), 5 authentic bones, 6 authentic muscles.
4. Linear Blend Skinning: Elbow flexion from 0° -> 45° -> 90° with 0.0 mm joint gap.
5. Biomechanical Muscle Deformation:
   - Biceps brachii shortening (~23.17%) and isovolumetric radial bulge (factor ~1.14).
   - Triceps brachii stretch (~20.0%).
6. Display Mode switching: OVERLAY_MODE, ANATOMY_MODE, CHARACTER_MODE.
7. Dynamic Surface Anchors (LI4, LI11, LI14, LI15) tracking skeleton & bone movements.
8. Screenshot evidence capture for V1.2 release qualification.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = REPO_ROOT / "1docs" / "product_v12" / "evidence"
TEST_PORT = 8212


@pytest.fixture(scope="module")
def v12_character_server():
    """Start isolated live server on port 8212 for V1.2 Anatomical Binding audits."""
    server_py = REPO_ROOT / "msk_therapy_os" / "server.py"
    env = os.environ.copy()
    env["MSK_PORT"] = str(TEST_PORT)
    env["PYTHONPATH"] = str(REPO_ROOT)

    proc = subprocess.Popen(
        [sys.executable, str(server_py), "--port", str(TEST_PORT)],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2.5)
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=3.0)
    except Exception:
        proc.kill()


class TestV12AnatomicalBindingE2E:
    """Verifies the complete Anatomical Binding System, biomechanical deformation, and WebGL UI."""

    def test_v12_api_metadata(self, v12_character_server):
        url = f"http://127.0.0.1:{TEST_PORT}/api/character/v12/metadata"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))

        assert data["pipeline_version"] == "V1.2"
        assert data["system_name"] == "Anatomical Binding System (ABS)"
        assert data["scope"] == "ENGINEERING_RESEARCH_ONLY"
        assert data["clinical_validation"] == "NOT_ESTABLISHED"
        assert data["gate_g3"] == "PENDING"
        assert data["canonical_skeleton"]["bone_count"] == 53
        assert len(data["canonical_skeleton"]["arm_bones"]) == 4
        assert data["musculoskeletal_assets"]["rigid_bones_count"] == 5
        assert data["musculoskeletal_assets"]["muscles_count"] == 6
        assert data["musculoskeletal_assets"]["surface_anchors_count"] == 4
        assert data["kinematic_synchronization"]["joint_gap_tolerance_mm"] == 0.0

    def test_v12_api_skeleton_contract(self, v12_character_server):
        url = f"http://127.0.0.1:{TEST_PORT}/api/character/v12/skeleton"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))

        assert data["skeleton_name"] == "MakeHuman_GameEngine_53Bone_Canonical"
        assert data["bone_count"] == 53
        bones = data["bones"]
        assert "upperarm_r" in bones
        assert "lowerarm_r" in bones
        assert "hand_r" in bones
        assert "clavicle_r" in bones

        # Verify lowerarm kinematics definition
        low = bones["lowerarm_r"]
        assert low["parent_id"] == "upperarm_r"
        assert low["kinematics"]["flexion_axis"] == "X"
        assert low["kinematics"]["rom_deg"] == [0.0, 145.0]

    def test_v12_api_rigid_bones(self, v12_character_server):
        url = f"http://127.0.0.1:{TEST_PORT}/api/character/v12/bones"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))

        bones = {b["anatomy_id"]: b for b in data["rigid_bones"]}
        assert "FJ3368" in bones, "Humerus must be present"
        assert bones["FJ3368"]["canonical_bone_id"] == "upperarm_r"
        assert bones["FJ3368"]["registration_error_mm"] < 1.0

        assert "FJ3349" in bones, "Radius must be present"
        assert bones["FJ3349"]["canonical_bone_id"] == "lowerarm_r"

        assert "FJ3391" in bones, "Ulna must be present"
        assert bones["FJ3391"]["canonical_bone_id"] == "lowerarm_r"

        assert "FJ3352" in bones, "Metacarpal 2 must be present"
        assert bones["FJ3352"]["canonical_bone_id"] == "hand_r"

    def test_v12_api_muscles(self, v12_character_server):
        url = f"http://127.0.0.1:{TEST_PORT}/api/character/v12/muscles"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))

        muscles = {m["anatomy_id"]: m for m in data["muscles"]}
        assert "FJ1478" in muscles, "Biceps long head must exist"
        assert muscles["FJ1478"]["resting_length_m"] == 0.315
        assert muscles["FJ1478"]["flexed_length_90_m"] == 0.242

        assert "FJ1477" in muscles, "Triceps lateral head must exist"
        assert muscles["FJ1477"]["resting_length_m"] == 0.210
        assert muscles["FJ1477"]["flexed_length_90_m"] == 0.252

    def test_v12_api_evaluate_kinematics(self, v12_character_server):
        # 1. Neutral extension (0 deg)
        url_0 = f"http://127.0.0.1:{TEST_PORT}/api/character/v12/evaluate?elbow_flexion=0"
        with urllib.request.urlopen(url_0) as resp:
            assert resp.status == 200
            d0 = json.loads(resp.read().decode("utf-8"))
        assert d0["biceps_shortening_pct"] == 0.0
        assert d0["biceps_bulge_factor"] == 1.0
        assert d0["triceps_lengthening_pct"] == 0.0
        assert d0["joint_gap_mm"] == 0.0

        # 2. Full flexion (90 deg)
        url_90 = f"http://127.0.0.1:{TEST_PORT}/api/character/v12/evaluate?elbow_flexion=90"
        with urllib.request.urlopen(url_90) as resp:
            assert resp.status == 200
            d90 = json.loads(resp.read().decode("utf-8"))
        assert round(d90["biceps_shortening_pct"], 1) == 23.2
        assert d90["biceps_bulge_factor"] > 1.10
        assert round(d90["triceps_lengthening_pct"], 1) == 20.0
        assert d90["hand_elevation_delta_m"] > 0.20
        assert d90["verification_status"] == "SYNCHRONIZED_ACTIVE"

    def test_v12_playwright_arm_studio_e2e(self, v12_character_server):
        """Runs browser automated audit of 3D arm, skeleton, muscle deformation, and markers."""
        from playwright.sync_api import sync_playwright

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 900})

            # Navigate to Arm Studio
            url = f"http://127.0.0.1:{TEST_PORT}/character_v12/index.html"
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for 3D model to fully initialize
            page.wait_for_function("() => window.__CHARACTER_V12__ && window.__CHARACTER_V12__.isLoaded() === true", timeout=25000)

            # Check skeleton and mesh stats
            sk_info = page.evaluate("() => window.__CHARACTER_V12__.getSkeletonInfo()")
            assert sk_info["boneCount"] == 4, f"Expected 4 arm bones, got {sk_info['boneCount']}"
            assert "lowerarm_r" in sk_info["boneNames"]
            assert "upperarm_r" in sk_info["boneNames"]

            arm_stats = page.evaluate("() => window.__CHARACTER_V12__.getArmStats()")
            assert arm_stats["hasSkin"] is True
            assert arm_stats["boneMeshesCount"] >= 5
            assert arm_stats["muscleMeshesCount"] >= 6
            assert arm_stats["bicepsCount"] >= 2
            assert arm_stats["tricepsCount"] >= 3
            assert arm_stats["markersCount"] == 4

            # Helper for screenshot capture
            def take_shot(filename):
                target = EVIDENCE_DIR / filename
                page.screenshot(path=str(target), timeout=10000, animations="disabled")

            # 1. Screenshot: Rest Pose (0°) in OVERLAY_MODE
            page.wait_for_timeout(500)
            take_shot("v12_01_rest_pose_overlay.png")

            # 2. Test Elbow Flexion at 45°
            pos_rest = page.evaluate("() => window.__CHARACTER_V12__.getAcupointWorldPos('LI4')")
            page.evaluate("() => window.__CHARACTER_V12__.setJointAngle('lowerarm_r', 'x', 45)")
            page.wait_for_timeout(300)

            biceps_45 = page.evaluate("() => window.__CHARACTER_V12__.getBicepsDeformation()")
            assert biceps_45["shortening_pct"] > 10.0, "Biceps must shorten at 45 deg"
            assert biceps_45["bulge_factor"] > 1.05, "Biceps must bulge at 45 deg"
            take_shot("v12_02_elbow_flexion_45deg.png")

            # 3. Test Elbow Flexion at 90°
            page.evaluate("() => window.__CHARACTER_V12__.setJointAngle('lowerarm_r', 'x', 90)")
            page.wait_for_timeout(300)

            pos_flex90 = page.evaluate("() => window.__CHARACTER_V12__.getAcupointWorldPos('LI4')")
            biceps_90 = page.evaluate("() => window.__CHARACTER_V12__.getBicepsDeformation()")
            triceps_90 = page.evaluate("() => window.__CHARACTER_V12__.getTricepsDeformation()")

            assert round(biceps_90["shortening_pct"], 1) == 23.2, f"Expected 23.2% shortening, got {biceps_90['shortening_pct']}"
            assert biceps_90["bulge_factor"] > 1.12, "Biceps bulge factor must exceed 1.12"
            assert round(triceps_90["stretch_pct"], 1) == 20.0, f"Expected 20.0% stretch, got {triceps_90['stretch_pct']}"

            # Joint gap must remain exactly 0.0 mm
            gap = page.evaluate("() => window.__CHARACTER_V12__.getJointGapMm()")
            assert gap == 0.0, f"Expected 0.0 mm joint gap, got {gap}"

            # Hand elevation at 90 deg must be significantly higher than at rest
            assert pos_flex90["y"] > pos_rest["y"], "LI4 hand marker must elevate when elbow flexes"
            take_shot("v12_03_elbow_flexion_90deg.png")

            # 4. Test Display Modes: ANATOMY_MODE & CHARACTER_MODE
            # ANATOMY_MODE (Pure Musculoskeletal)
            page.evaluate("() => window.__CHARACTER_V12__.setMode('ANATOMY_MODE')")
            page.wait_for_timeout(300)
            assert page.evaluate("() => window.__CHARACTER_V12__.getMode()") == "ANATOMY_MODE"
            take_shot("v12_04_anatomy_mode_90deg.png")

            # CHARACTER_MODE (Living Skin)
            page.evaluate("() => window.__CHARACTER_V12__.setMode('CHARACTER_MODE')")
            page.wait_for_timeout(300)
            assert page.evaluate("() => window.__CHARACTER_V12__.getMode()") == "CHARACTER_MODE"
            take_shot("v12_05_character_skin_mode.png")

            # Return to OVERLAY_MODE
            page.evaluate("() => window.__CHARACTER_V12__.setMode('OVERLAY_MODE')")
            page.wait_for_timeout(200)

            # 5. Combined Shoulder Abduction (30°) + Elbow Flexion (90°)
            page.evaluate("() => window.__CHARACTER_V12__.setJointAngle('upperarm_r', 'z', 30)")
            page.wait_for_timeout(300)
            take_shot("v12_06_shoulder_abduction_combined.png")

            # 6. Reset Pose
            page.evaluate("() => window.__CHARACTER_V12__.resetPose()")
            page.wait_for_timeout(300)
            deg_reset = page.evaluate("() => window.__CHARACTER_V12__.getJointAngle('lowerarm_r', 'x')")
            assert round(deg_reset, 1) == 0.0, "Reset pose must return elbow to 0 deg"
            take_shot("v12_07_verified_rest_pose.png")

            browser.close()
