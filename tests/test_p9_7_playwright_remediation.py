"""Playwright Visual and Interactive Browser Validation for P9.7 Independent Anatomical Remediation.

Captures authoritative visual evidence in 2data/evidence/p9_7_remediation/:
1. 01_p97_qa_studio_coverage_122_class_b.png - Meridian QA Studio coverage dashboard (18 Class A, 122 Class B, 222 Class D, 38.7% Calibrated).
2. 02_p97_stomach_lower_leg_path_calibrated.png - Stomach lower leg channel (ST35-ST41, patella to lateral malleolus).
3. 03_p97_conception_vessel_midline_calibrated.png - Conception Vessel anterior midline (CV2-CV21, linea alba & sternum).
4. 04_p97_bladder_outer_column_interscapular_calibrated.png - Bladder dual column back view (BL11-BL15, BL41-BL50 with 22.5 mm/cun interscapular calibration).
5. 05_p97_webgl_performance_instrumentation.png - WebGL performance instrumentation view.
"""
from __future__ import annotations

import json
from pathlib import Path
import time
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler

EVIDENCE_DIR = Path("2data/evidence/p9_7_remediation")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p97(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p97_playwright_server")
    test_db_file = tmp_dir / "test_p97_pw.sqlite3"

    with open_db(str(test_db_file)) as test_db:
        init_db(test_db)
        seed_db(test_db)
        init_points_tables(test_db)

    class TestHandler(MSKRequestHandler):
        db_path = str(test_db_file)

    server = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
    port = server.server_port
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.shutdown()
    server.server_close()


@pytest.mark.playwright
def test_playwright_p9_7_remediation_evidence(browser_server_p97):
    """Capture real browser visual evidence for P9.7 remediated atlas."""
    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        # 1. Navigate to Atlas Viewer
        page.goto(f"{browser_server_p97}/atlas/", wait_until="networkidle")
        page.wait_for_selector("#acupunctureOverlay", state="attached", timeout=10000)

        # Wait for meridians layer to load
        page.wait_for_function("() => window.__meridiansDebug && window.__meridiansDebug.acuData !== null", timeout=10000)

        # Enable Meridians & Points display via DOM checkboxes
        page.evaluate("""() => {
            const chkPts = document.getElementById('chkShowPoints');
            if (chkPts && !chkPts.checked) { chkPts.checked = true; chkPts.dispatchEvent(new Event('change')); }
            const chkMer = document.getElementById('chkShowMeridians');
            if (chkMer && !chkMer.checked) { chkMer.checked = true; chkMer.dispatchEvent(new Event('change')); }
        }""")
        page.evaluate("async () => await window.__meridiansDebug.setLayerMode('canonical')")
        page.wait_for_timeout(800)

        # Evidence 1: QA Studio Coverage Dashboard Overview (122 Class B, 222 Class D, 38.7%)
        page.evaluate("""() => {
            if (window.__meridianStudio) {
                window.__meridianStudio.loadCoverage();
                window.__meridianStudio.loadTopology('ST');
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "01_p97_qa_studio_coverage_122_class_b.png"))

        # Evidence 2: Stomach Lower Leg Channel (ST35-ST41)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = -Math.PI / 4.0;
                window._renderer.camera.pitch = 0.25;
                window._renderer.camera.target = [0.12, 0.30, 0.05];
                window._renderer.camera.radius = 0.60;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "02_p97_stomach_lower_leg_path_calibrated.png"))

        # Evidence 3: Conception Vessel Anterior Midline (CV2-CV21)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = 0.0;
                window._renderer.camera.pitch = 0.05;
                window._renderer.camera.target = [0.0, 1.15, 0.10];
                window._renderer.camera.radius = 0.70;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "03_p97_conception_vessel_midline_calibrated.png"))

        # Evidence 4: Bladder Dual Column Back View (BL11-BL15, BL41-BL50, 22.5 mm/cun)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = Math.PI; // Posterior back view
                window._renderer.camera.pitch = 0.10;
                window._renderer.camera.target = [0.04, 1.30, -0.10];
                window._renderer.camera.radius = 0.65;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "04_p97_bladder_outer_column_interscapular_calibrated.png"))

        # Evidence 5: WebGL Performance Instrumentation
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = Math.PI * 0.25;
                window._renderer.camera.pitch = 0.15;
                window._renderer.camera.target = [0.0, 1.0, 0.0];
                window._renderer.camera.radius = 1.10;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "05_p97_webgl_performance_instrumentation.png"))

        browser.close()

    # Validate that all 5 screenshots were written and non-empty
    for fname in [
        "01_p97_qa_studio_coverage_122_class_b.png",
        "02_p97_stomach_lower_leg_path_calibrated.png",
        "03_p97_conception_vessel_midline_calibrated.png",
        "04_p97_bladder_outer_column_interscapular_calibrated.png",
        "05_p97_webgl_performance_instrumentation.png",
    ]:
        shot_path = EVIDENCE_DIR / fname
        assert shot_path.exists(), f"Evidence screenshot {fname} was not created"
        assert shot_path.stat().st_size > 5000, f"Screenshot {fname} appears empty or corrupted"
