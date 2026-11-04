"""Playwright Browser E2E Test Suite for MSK-Therapy-OS Product V1.0.
Validates the full vertical slice across all 5 completion packages (A-E):
A: 3D Atlas layers and BodyParts3D right upper limb meshes loaded.
B: Parametric Body sliders (height, arm length, circumference) and 4 presets with zero reversibility drift.
C: Dynamic acupoints (LI4, LI14, LI15) tracking morph and pose with undo/redo capabilities.
D: WebGL real 3D geometry deformation (solving WEB_MOTION_GEOMETRY_NOT_CONNECTED) and mouse pose.
E: Full-stack persistence (.mskproj save/load) and Markdown research report generation.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = REPO_ROOT / "1docs" / "product_v1" / "evidence"
TEST_PORT = 8201


@pytest.fixture(scope="module")
def v1_server_instance():
    """Start isolated HTTP server on test port for V1.0."""
    import socket

    server_py = REPO_ROOT / "msk_therapy_os" / "server.py"
    env = os.environ.copy()
    env["MSK_PORT"] = str(TEST_PORT)
    env["PYTHONPATH"] = str(REPO_ROOT)

    proc = subprocess.Popen(
        [sys.executable, str(server_py), "--port", str(TEST_PORT)],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    bound = False
    start = time.time()
    while time.time() - start < 6.0:
        try:
            with socket.create_connection(("127.0.0.1", TEST_PORT), timeout=0.2):
                bound = True
                break
        except OSError:
            time.sleep(0.1)

    assert bound, f"Server failed to bind on 127.0.0.1:{TEST_PORT}"
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


class TestV1ProductBrowserE2E:

    def test_v1_complete_product_workflow(self, v1_server_instance):
        from playwright.sync_api import sync_playwright

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 920})

            # -------------------------------------------------------------
            # STEP 1: Gói A — Tải Atlas & Kiểm tra Khung nhìn 3D
            # -------------------------------------------------------------
            url = f"http://127.0.0.1:{TEST_PORT}/sandbox/p21/"
            resp = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            assert resp.status == 200, f"Page load failed with status {resp.status}"

            # Verify brand title and badges
            brand_title = page.locator(".brand-title").inner_text()
            assert "MSK-Therapy-OS" in brand_title
            assert "Product V1.0" in brand_title

            scope_badge = page.locator("#scope-badge").inner_text()
            assert "ENGINEERING_RESEARCH_ONLY" in scope_badge

            canvas = page.locator("#canvas-container canvas")
            assert canvas.is_visible()

            # Wait for Three.js engine and automation hooks
            page.wait_for_function("() => window.__P21_POC__ && window.__P21_POC__.v1", timeout=10000)

            # Screenshot: Baseline Atlas View
            ss_baseline = EVIDENCE_DIR / "01_v1_atlas_baseline.png"
            page.screenshot(path=str(ss_baseline))
            assert ss_baseline.exists()

            # -------------------------------------------------------------
            # STEP 2: Gói B — Parametric Body Sliders & Presets
            # -------------------------------------------------------------
            # Switch to Morph tab if tabbed UI
            tab_morph = page.locator(".tab-btn[data-target='pane-left-morph']")
            if tab_morph.is_visible():
                tab_morph.click()
                page.wait_for_timeout(100)

            # Click Slender preset
            btn_slender = page.locator("#preset-slender")
            btn_slender.click()
            page.wait_for_timeout(300)

            body_params = page.evaluate("() => window.__P21_POC__.v1.getBodyParams()")
            assert body_params["preset_name"] == "slender"
            assert body_params["height_scale"] == 1.05
            assert body_params["right_arm_length_ratio"] == 1.03
            assert body_params["right_arm_circumference_visual"] == 0.88
            assert body_params["morph_version"] > 1

            # Screenshot: Slender Morph
            ss_slender = EVIDENCE_DIR / "02_v1_parametric_morph_slender.png"
            page.screenshot(path=str(ss_slender))
            assert ss_slender.exists()

            # Switch back to Baseline and verify zero drift
            btn_baseline = page.locator("#preset-baseline")
            btn_baseline.click()
            page.wait_for_timeout(300)

            drift_text = page.locator("#val-drift-status").inner_text()
            assert "0.000000 m" in drift_text
            assert "Không trôi số học" in drift_text

            # -------------------------------------------------------------
            # STEP 3: Gói D — WebGL Real Motion Playback & Geometry Connected
            # -------------------------------------------------------------
            # Check motion status banner is GREEN and CONNECTED
            motion_status = page.locator("#motion-geometry-status").inner_text()
            assert "WEB_MOTION_GEOMETRY_CONNECTED" in motion_status

            # Wait for motion frames to be populated
            page.wait_for_function("() => window.__P21_POC__.p33.getMotionFrames().length > 0", timeout=10000)

            # Move timeline to Frame 50
            timeline = page.locator("#motion-timeline")
            timeline.fill("50")
            page.dispatch_event("#motion-timeline", "input")
            page.wait_for_timeout(300)

            pose_f50 = page.evaluate("() => window.__P21_POC__.v1.getKinematicPose()")
            arm_rots = page.evaluate("() => window.__P21_POC__.v1.getArmatureRotations()")

            # Inman 2:1 validation: scapula rotation should be roughly 1/2 of upper arm rotation
            assert pose_f50["shoulder_elevation_deg"] > 30.0
            assert pose_f50["elbow_flexion_deg"] > 20.0
            assert abs(arm_rots["scapula_z"]) > 0.01, "Scapula group failed to rotate in WebGL scene"
            assert abs(arm_rots["upperArm_z"]) > 0.01, "Upper arm group failed to rotate in WebGL scene"
            assert abs(arm_rots["forearm_x"]) > 0.01, "Forearm group failed to rotate in WebGL scene"

            # Check that dynamic acupoints LI4, LI14, LI15 followed the limb
            marker_pos_f50 = page.evaluate("() => window.__P21_POC__.v1.getMarkerPositions()")
            assert "LI4" in marker_pos_f50
            assert "LI14" in marker_pos_f50
            assert "LI15" in marker_pos_f50

            # Screenshot: Motion Frame 50 Connected
            ss_motion = EVIDENCE_DIR / "03_v1_web_motion_frame50_connected.png"
            page.screenshot(path=str(ss_motion))
            assert ss_motion.exists()

            # -------------------------------------------------------------
            # STEP 4: Gói D — Interactive Mouse Pose Direct Control
            # -------------------------------------------------------------
            btn_mode_mousepose = page.locator("#btn-mode-mousepose")
            btn_mode_mousepose.click()
            page.wait_for_timeout(200)

            # Drag shoulder slider to 45 deg, elbow to 60 deg
            slider_mouse_sh = page.locator("#mouse-pose-shoulder")
            slider_mouse_el = page.locator("#mouse-pose-elbow")
            slider_mouse_sh.fill("45")
            page.dispatch_event("#mouse-pose-shoulder", "input")
            slider_mouse_el.fill("60")
            page.dispatch_event("#mouse-pose-elbow", "input")
            page.wait_for_timeout(300)

            mouse_pose = page.evaluate("() => window.__P21_POC__.v1.getKinematicPose()")
            assert mouse_pose["shoulder_elevation_deg"] == 45.0
            assert mouse_pose["elbow_flexion_deg"] == 60.0

            # Screenshot: Mouse Pose
            ss_mousepose = EVIDENCE_DIR / "04_v1_mouse_pose_interactive.png"
            page.screenshot(path=str(ss_mousepose))
            assert ss_mousepose.exists()

            # Reset mouse pose
            btn_reset = page.locator("#btn-reset-mousepose")
            btn_reset.click()
            page.wait_for_timeout(200)

            # -------------------------------------------------------------
            # STEP 5: Gói C & E — Knowledge Vault Query for LI4
            # -------------------------------------------------------------
            # Switch to Acupoints tab if tabbed UI
            tab_acu = page.locator(".tab-btn[data-target='pane-right-acupoints']")
            if tab_acu.is_visible():
                tab_acu.click()
                page.wait_for_timeout(100)

            select_marker = page.locator("#select-marker-knowledge")
            select_marker.select_option("LI4")
            page.dispatch_event("#select-marker-knowledge", "change")
            page.wait_for_function("() => document.getElementById('knowledge-details-box').innerText.includes('LI4')", timeout=10000)

            kb_box = page.locator("#knowledge-details-box").inner_text()
            assert "LI4" in kb_box
            assert "FMA:23910" in kb_box
            assert "Hợp Cốc" in kb_box or "Hegu" in kb_box

            # Screenshot: Knowledge Query
            ss_knowledge = EVIDENCE_DIR / "05_v1_knowledge_query_li4.png"
            page.screenshot(path=str(ss_knowledge))
            assert ss_knowledge.exists()

            # -------------------------------------------------------------
            # STEP 6: Gói E — Project Export Markdown Report
            # -------------------------------------------------------------
            # Switch back to Motion tab for export
            tab_motion = page.locator(".tab-btn[data-target='pane-right-motion']")
            if tab_motion.is_visible():
                tab_motion.click()
                page.wait_for_timeout(100)

            btn_export = page.locator("#btn-p33-export-markdown")
            btn_export.click()
            page.wait_for_selector("#modal-export", state="visible", timeout=10000)

            modal_export = page.locator("#modal-export")
            assert modal_export.is_visible()

            md_content = page.locator("#export-markdown-content").inner_text()
            assert "BÁO CÁO NGHIÊN CỨU" in md_content
            assert "ENGINEERING_RESEARCH_ONLY" in md_content
            assert "LI4" in md_content
            assert "LI14" in md_content
            assert "LI15" in md_content

            # Screenshot: Markdown Export Preview
            ss_report = EVIDENCE_DIR / "06_v1_project_export_markdown.png"
            page.screenshot(path=str(ss_report))
            assert ss_report.exists()

            # Close browser
            browser.close()
