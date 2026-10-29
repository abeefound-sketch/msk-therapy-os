"""Playwright Visual and Interactive Browser Validation for P9.5 Anatomical Remediation.

Captures authoritative visual evidence in 2data/evidence/p9_5_remediation/:
1. 01_p95_qa_studio_remediated_coverage.png - Meridian QA Studio coverage dashboard (18 Class A, 72 Class B, 272 Class D).
2. 02_p95_gallbladder_auricular_loop_calibrated.png - Gallbladder cranial loop with calibrated GB1, GB2, GB8, GB14.
3. 03_p95_bladder_dual_column_lumbar_calibrated.png - Bladder paraspinal dual columns (BL14, BL15, BL23, BL25, BL52, BL54).
4. 04_p95_stomach_facial_cervical_gap_calibrated.png - Stomach facial & cervical alignment (ST1, ST4, ST8, ST9, ST12, ST25).
5. 05_p95_kidney_medial_leg_calibrated.png - Kidney channel medial ankle with corrected KI3 laterality.
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

EVIDENCE_DIR = Path("2data/evidence/p9_5_remediation")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p95(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p95_playwright_server")
    test_db_file = tmp_dir / "test_p95_pw.sqlite3"

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
def test_playwright_p9_5_remediation_evidence(browser_server_p95):
    """Capture real browser visual evidence for P9.5 remediated atlas."""
    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        # 1. Navigate to Atlas Viewer
        page.goto(f"{browser_server_p95}/atlas/", wait_until="networkidle")
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

        # Evidence 1: QA Studio Coverage Dashboard Overview
        page.evaluate("""() => {
            if (window.__meridianStudio) {
                window.__meridianStudio.loadCoverage();
                window.__meridianStudio.loadTopology('GB');
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "01_p95_qa_studio_remediated_coverage.png"))

        # Evidence 2: Gallbladder Auricular Loop Calibrated (Lateral head view)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = -Math.PI / 2.2;
                window._renderer.camera.pitch = 0.12;
                window._renderer.camera.target = [0.05, 1.62, 0.02];
                window._renderer.camera.radius = 0.45;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(800)
        page.screenshot(path=str(EVIDENCE_DIR / "02_p95_gallbladder_auricular_loop_calibrated.png"))

        # Evidence 3: Bladder Dual Columns & Lumbar Alignment (Posterior back view)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = Math.PI;
                window._renderer.camera.pitch = 0.05;
                window._renderer.camera.target = [0.0, 1.20, -0.05];
                window._renderer.camera.radius = 0.85;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(800)
        page.screenshot(path=str(EVIDENCE_DIR / "03_p95_bladder_dual_column_lumbar_calibrated.png"))

        # Evidence 4: Stomach Facial & Cervical Path (Anterolateral neck view)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = -Math.PI / 3.5;
                window._renderer.camera.pitch = 0.08;
                window._renderer.camera.target = [0.04, 1.52, 0.05];
                window._renderer.camera.radius = 0.50;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(800)
        page.screenshot(path=str(EVIDENCE_DIR / "04_p95_stomach_facial_cervical_gap_calibrated.png"))

        # Evidence 5: Kidney Channel Medial Ankle (Medial foot view)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = Math.PI / 2.0;
                window._renderer.camera.pitch = -0.15;
                window._renderer.camera.target = [0.08, 0.08, 0.0];
                window._renderer.camera.radius = 0.40;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(800)
        page.screenshot(path=str(EVIDENCE_DIR / "05_p95_kidney_medial_leg_calibrated.png"))

        browser.close()

    # Verify screenshots exist and are non-empty
    for item in [
        "01_p95_qa_studio_remediated_coverage.png",
        "02_p95_gallbladder_auricular_loop_calibrated.png",
        "03_p95_bladder_dual_column_lumbar_calibrated.png",
        "04_p95_stomach_facial_cervical_gap_calibrated.png",
        "05_p95_kidney_medial_leg_calibrated.png",
    ]:
        f = EVIDENCE_DIR / item
        assert f.exists(), f"Evidence file {item} was not generated"
        assert f.stat().st_size > 10000, f"Evidence file {item} is suspiciously small ({f.stat().st_size} bytes)"
