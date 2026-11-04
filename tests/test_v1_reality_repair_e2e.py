"""MSK-Therapy-OS V1.0 — Reality Repair Playwright E2E Verification Suite.

Audits:
1. Direct DOM & Canvas audit against V1.0 reality claims.
2. Acupoint LI4 binding integrity (Metacarpal II vs Clavicle guardrail).
3. Zero Double Transform in Three.js armature hierarchy.
4. Seamless joint pivot connectivity across kinematics.
5. Parametric body reversibility and zero numerical drift.
6. Viscera count classification (249 core viscera vs 1,230 neurovascular).
7. Dynamic meridian trajectory (LI4 -> LI11 -> LI14 -> LI15).
8. Viewport toolbar actions & Tabbed panel navigation.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = REPO_ROOT / "1docs" / "product_v1" / "reality_repair" / "evidence"
TEST_PORT = 8202


@pytest.fixture(scope="module")
def reality_repair_server():
    """Start isolated live server on port 8202 for Reality Repair audits."""
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


class TestV1RealityRepairE2E:
    """Comprehensive reality audit of the V1.0 Web Atlas interface."""

    def test_reality_repair_full_audit(self, reality_repair_server):
        from playwright.sync_api import sync_playwright

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 920})

            # -------------------------------------------------------------
            # AUDIT 1: DOM, Badges & Research Safety Barrier
            # -------------------------------------------------------------
            url = f"http://127.0.0.1:{TEST_PORT}/sandbox/p21/"
            resp = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            assert resp.status == 200

            # Scope & Safety notices
            scope_badge = page.locator("#scope-badge").inner_text()
            assert "ENGINEERING_RESEARCH_ONLY" in scope_badge

            banner = page.locator(".research-banner").inner_text()
            assert "KHÔNG DÙNG ĐỂ CHẨN ĐOÁN" in banner

            # Viewport canvas
            canvas = page.locator("#canvas-container canvas")
            assert canvas.is_visible()

            # Wait for Three.js engine and reality repair hooks
            page.wait_for_function("() => window.__P21_POC__ && window.__P21_POC__.realityRepair", timeout=10000)
            page.wait_for_function("() => window.__P21_POC__.p33 && window.__P21_POC__.p33.getMotionFrames().length > 0", timeout=10000)

            # Screenshot: Initial Layout with Toolbar and Tabs
            ss_init = EVIDENCE_DIR / "repair_01_initial_layout.png"
            page.screenshot(path=str(ss_init))
            assert ss_init.exists()

            # -------------------------------------------------------------
            # AUDIT 2: LI4 Binding Integrity & Invalid Binding Guardrail
            # -------------------------------------------------------------
            # Set to canonical rest pose (0 deg) to measure unrotated coordinates
            page.evaluate("() => window.__P21_POC__.v1.setMousePose(0.0, 0.0)")
            page.wait_for_timeout(100)

            markers = page.evaluate("() => window.__P21_POC__.v1.getMarkerPositions()")
            assert "LI4" in markers, "Canonical LI4 marker missing from 3D scene"
            pos_li4 = markers["LI4"]
            # LI4 must be situated near Metacarpal II: X in [-0.29, -0.26], Y in [0.80, 0.86], Z in [0.01, 0.06]
            assert -0.30 <= pos_li4[0] <= -0.25, f"LI4 X coordinate abnormal: {pos_li4[0]}"
            assert 0.80 <= pos_li4[1] <= 0.88, f"LI4 Y coordinate abnormal: {pos_li4[1]}"
            assert 0.00 <= pos_li4[2] <= 0.06, f"LI4 Z coordinate abnormal: {pos_li4[2]}"

            # Attempt invalid binding of LI4 to Clavicle (FJ3237) via API
            import urllib.request
            invalid_payload = {
                "label": "Accidental Clavicle LI4",
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
            req = urllib.request.Request(
                f"http://127.0.0.1:{TEST_PORT}/api/sandbox/p21/annotation",
                data=json.dumps(invalid_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as api_resp:
                assert api_resp.status == 201
                annot_saved = json.loads(api_resp.read().decode("utf-8"))
                assert annot_saved["verification_status"] == "USER_ANNOTATED_UNVERIFIED"
                assert annot_saved["binding_status"] == "INVALID_BINDING"
                assert "Sai lệch giải phẫu" in annot_saved["validation_error"]

            # -------------------------------------------------------------
            # AUDIT 3: Zero Double Transform in Three.js Armature Hierarchy
            # -------------------------------------------------------------
            # Set to canonical rest pose (0 deg) to measure pure structural offsets
            page.evaluate("() => window.__P21_POC__.v1.setMousePose(0.0, 0.0)")
            page.wait_for_timeout(100)

            # Switch to Morph tab
            page.locator(".tab-btn[data-target='pane-left-morph']").click()
            page.wait_for_timeout(150)

            # Set arm length ratio to 1.15, circumference to 1.20
            page.evaluate("() => window.__P21_POC__.v1.setParametricSliders(1.0, 1.15, 1.20)")
            page.wait_for_timeout(200)

            scales = page.evaluate("() => window.__P21_POC__.realityRepair.getLimbScales()")
            # Joint nodes MUST remain strictly scale (1, 1, 1)
            for j_group in ["upperArmGroup_scale", "forearmGroup_scale", "handGroup_scale"]:
                assert scales[j_group] == [1.0, 1.0, 1.0], f"{j_group} has non-unit scale: {scales[j_group]}"

            # Visual containers MUST have EXACTLY (1.20, 1.15, 1.20)
            for v_cont in ["upperArm_worldScale", "forearm_worldScale", "hand_worldScale"]:
                ws = scales[v_cont]
                assert abs(ws[0] - 1.20) < 1e-4, f"{v_cont} X scale error (double transform): {ws[0]}"
                assert abs(ws[1] - 1.15) < 1e-4, f"{v_cont} Y scale error (double transform): {ws[1]}"
                assert abs(ws[2] - 1.20) < 1e-4, f"{v_cont} Z scale error (double transform): {ws[2]}"

            # Screenshot: Scaled Armature with Zero Double Transform
            ss_scales = EVIDENCE_DIR / "repair_02_zero_double_transform.png"
            page.screenshot(path=str(ss_scales))
            assert ss_scales.exists()

            # -------------------------------------------------------------
            # AUDIT 4: Joint Connectivity & Gap Analysis
            # -------------------------------------------------------------
            joints = page.evaluate("() => window.__P21_POC__.realityRepair.getJointWorldPositions()")
            # Verify contact joint coordinates
            assert abs(joints["scapula"][0] - (-0.010)) < 2e-3
            assert abs(joints["shoulder"][0] - (-0.190)) < 2e-3
            # Elbow should have moved down with upper arm length: -0.273 * 1.15 = -0.31395
            expected_elbow_y = 1.395 - (0.273 * 1.15)
            assert abs(joints["elbow"][1] - expected_elbow_y) < 2e-3, f"Elbow joint disconnected: {joints['elbow'][1]} vs {expected_elbow_y}"

            # -------------------------------------------------------------
            # AUDIT 5: Parametric Reversibility & Zero Numerical Drift
            # -------------------------------------------------------------
            page.evaluate("() => window.__P21_POC__.v1.applyPreset('baseline')")
            page.wait_for_timeout(200)

            drift_text = page.locator("#val-drift-status").inner_text()
            assert "0.000000 m" in drift_text
            assert "Không trôi số học" in drift_text

            joints_rest = page.evaluate("() => window.__P21_POC__.realityRepair.getJointWorldPositions()")
            assert abs(joints_rest["shoulder"][1] - 1.395) < 1e-4
            assert abs(joints_rest["elbow"][1] - 1.122) < 1e-4

            # -------------------------------------------------------------
            # AUDIT 6: Dynamic Shou Yangming Meridian Trajectory
            # -------------------------------------------------------------
            # Switch to Motion tab
            page.locator(".tab-btn[data-target='pane-right-motion']").click()
            page.wait_for_timeout(150)

            pts_rest = page.evaluate("() => window.__P21_POC__.realityRepair.getDynamicMeridianPoints()")
            assert len(pts_rest) == 4, f"Meridian trajectory must have 4 waypoints (LI4, LI11, LI14, LI15), got {len(pts_rest)}"

            # Elevate shoulder to 60 deg, elbow to 45 deg
            page.evaluate("() => window.__P21_POC__.v1.setMousePose(60.0, 45.0)")
            page.wait_for_timeout(300)

            pts_flexed = page.evaluate("() => window.__P21_POC__.realityRepair.getDynamicMeridianPoints()")
            # Verify that points moved in 3D space
            assert pts_flexed[0] != pts_rest[0], "LI4 waypoint failed to move during kinematics"
            assert pts_flexed[1] != pts_rest[1], "LI11 waypoint failed to move during kinematics"
            assert pts_flexed[2] != pts_rest[2], "LI14 waypoint failed to move during kinematics"

            # Screenshot: Flexed Kinematics with Active Meridian Line
            ss_kinematics = EVIDENCE_DIR / "repair_03_flexed_meridian_kinematics.png"
            page.screenshot(path=str(ss_kinematics))
            assert ss_kinematics.exists()

            # -------------------------------------------------------------
            # AUDIT 7: Viewport Navigation Toolbar Actions
            # -------------------------------------------------------------
            # Focus on Right Arm
            btn_arm = page.locator("#btn-cam-arm")
            btn_arm.click()
            page.wait_for_timeout(300)

            ss_focus_arm = EVIDENCE_DIR / "repair_04_viewport_focus_arm.png"
            page.screenshot(path=str(ss_focus_arm))
            assert ss_focus_arm.exists()

            # Toggle Skin Kinematics (Hide Skin)
            btn_skin = page.locator("#btn-toggle-skin-kinematics")
            assert "Ẩn Da Khi Vận Động" in btn_skin.inner_text()
            btn_skin.click()
            page.wait_for_timeout(200)

            skin_vis = page.evaluate("() => window.__P21_POC__.realityRepair.isSkinVisible()")
            assert skin_vis is False, "Skin layer failed to hide on toggle"
            assert "Hiện Lớp Da" in btn_skin.inner_text()

            ss_skin_hidden = EVIDENCE_DIR / "repair_05_skin_hidden_for_kinematics.png"
            page.screenshot(path=str(ss_skin_hidden))
            assert ss_skin_hidden.exists()

            # Restore skin
            btn_skin.click()
            page.wait_for_timeout(150)
            assert page.evaluate("() => window.__P21_POC__.realityRepair.isSkinVisible()") is True

            # Fit whole body
            btn_fit = page.locator("#btn-cam-fit")
            btn_fit.click()
            page.wait_for_timeout(300)

            # Reset pose
            page.evaluate("() => window.__P21_POC__.v1.setMousePose(0.0, 0.0)")
            page.wait_for_timeout(200)

            # -------------------------------------------------------------
            # AUDIT 8: Viscera Metadata Distinction (249 Core vs 1,242 Neurovascular)
            # -------------------------------------------------------------
            with urllib.request.urlopen(f"http://127.0.0.1:{TEST_PORT}/api/sandbox/p21/metadata") as m_resp:
                meta = json.loads(m_resp.read().decode("utf-8"))
                stats = meta["statistics"]["layer_counts"]
                assert stats["viscera_core"] == 249
                assert stats["neurovascular"] == 1242
                assert stats["organ"] == 1491
                assert stats["bone"] == 296
                assert stats["muscle"] == 402
                assert stats["skin"] == 5

            # Final clean screenshot: Full Reality Repaired State
            ss_final = EVIDENCE_DIR / "repair_06_final_verified_state.png"
            page.screenshot(path=str(ss_final))
            assert ss_final.exists()

            browser.close()
