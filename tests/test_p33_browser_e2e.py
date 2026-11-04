"""Playwright Browser E2E Test Suite for Milestone P33.
Launches the live MSK-Therapy-OS server, drives a real Chromium browser,
tests 3D Atlas UI, Motion Replay, Knowledge Vault query, and Markdown export,
and captures browser screenshots as audit evidence.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = REPO_ROOT / "1docs" / "audits" / "P33" / "screenshots"
TEST_PORT = 8199


@pytest.fixture(scope="module")
def server_instance():
    """Start isolated HTTP server on test port."""
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

    # Wait for port to become active
    bound = False
    start = time.time()
    while time.time() - start < 5.0:
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


class TestP33BrowserE2E:

    def test_browser_e2e_full_workflow(self, server_instance):
        from playwright.sync_api import sync_playwright

        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 900})

            # 1. Open Atlas Sandbox (use domcontentloaded so we don't wait for all 15 background binary chunks)
            url = f"http://127.0.0.1:{TEST_PORT}/sandbox/p21/"
            resp = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            assert resp.status == 200, f"Page load failed with status {resp.status}"

            # 2. Check header badges and safety banner
            scope_badge = page.locator("#scope-badge")
            assert scope_badge.is_visible()
            assert "ENGINEERING_RESEARCH_ONLY" in scope_badge.inner_text()

            banner = page.locator(".research-banner")
            assert banner.is_visible()
            assert "KHÔNG DÙNG ĐỂ CHẨN ĐOÁN" in banner.inner_text()

            # Verify Canvas exists for 3D Viewport
            canvas = page.locator("#canvas-container canvas")
            assert canvas.is_visible()

            # Save initial view screenshot
            ss_atlas = SCREENSHOT_DIR / "p33_browser_e2e_atlas_loaded.png"
            page.screenshot(path=str(ss_atlas))
            assert ss_atlas.exists()

            # 3. Test Motion Timeline & Joint Display
            timeline = page.locator("#motion-timeline")
            assert timeline.is_visible()

            # Wait for P31 bundle to populate motion sequence
            page.wait_for_function("() => window.__P21_POC__ && window.__P21_POC__.p33 && window.__P21_POC__.p33.getMotionFrames().length > 0", timeout=10000)

            # Move slider to frame 50
            timeline.fill("50")
            page.dispatch_event("#motion-timeline", "input")

            val_shoulder = page.locator("#val-shoulder-elevation").inner_text()
            val_elbow = page.locator("#val-elbow-flexion").inner_text()
            frame_disp = page.locator("#motion-frame-display").inner_text()

            assert "50" in frame_disp
            assert "98" in val_shoulder or float(val_shoulder.replace("°", "")) > 50.0

            # 4. Verify initial Knowledge Query for LI14 (available mesh on initial load)
            page.wait_for_function("() => document.getElementById('knowledge-details-box').innerText.includes('LI14') && document.getElementById('knowledge-details-box').innerText.includes('CÓ MESH 3D')", timeout=10000)

            kb_box = page.locator("#knowledge-details-box")
            kb_text = kb_box.inner_text()

            assert "LI14" in kb_text
            assert "FMA:23412" in kb_text
            assert "WHO Standard 2008" in kb_text
            assert "CÓ MESH 3D" in kb_text

            # Switch to Acupoints tab if tabbed UI
            tab_acu = page.locator(".tab-btn[data-target='pane-right-acupoints']")
            if tab_acu.is_visible():
                tab_acu.click()
                page.wait_for_timeout(100)

            # Switch to LI15
            select_marker = page.locator("#select-marker-knowledge")
            select_marker.select_option("LI15")
            page.dispatch_event("#select-marker-knowledge", "change")
            page.wait_for_function("() => document.getElementById('knowledge-details-box').innerText.includes('LI15')", timeout=10000)
            assert "LI15" in kb_box.inner_text()

            # 5. Test Knowledge Query for LI4 (missing asset)
            select_marker.select_option("LI4")
            page.dispatch_event("#select-marker-knowledge", "change")
            page.wait_for_function("() => document.getElementById('knowledge-details-box').innerText.includes('LI4') && document.getElementById('knowledge-details-box').innerText.includes('ASSET_NOT_AVAILABLE')", timeout=10000)

            kb_text_li4 = kb_box.inner_text()
            assert "LI4" in kb_text_li4
            assert "FMA:23910" in kb_text_li4
            assert "ASSET_NOT_AVAILABLE" in kb_text_li4
            assert "CẢNH BÁO" in kb_text_li4

            ss_knowledge = SCREENSHOT_DIR / "p33_browser_e2e_knowledge_active.png"
            page.screenshot(path=str(ss_knowledge))
            assert ss_knowledge.exists()

            # 6. Test Markdown Export Modal (switch back to Motion tab if needed)
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
            assert "# BÁO CÁO NGHIÊN CỨU LIÊN HỆ ĐỘNG HỌC VÀ TRI THỨC Y VĂN" in md_content
            assert "PHẠM VI: ENGINEERING_RESEARCH_ONLY" in md_content
            assert "LI14" in md_content
            assert "ASSET_NOT_AVAILABLE" in md_content

            # Assert zero PII
            for forbidden in ["patient_name", "mrn", "tên bệnh nhân", "hồ sơ bệnh án"]:
                assert forbidden not in md_content.lower()

            ss_modal = SCREENSHOT_DIR / "p33_browser_e2e_markdown_modal.png"
            page.screenshot(path=str(ss_modal))
            assert ss_modal.exists()

            browser.close()
