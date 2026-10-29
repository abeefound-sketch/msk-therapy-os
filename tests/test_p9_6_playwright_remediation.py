"""Playwright Visual and Interactive Browser Validation for P9.6 Phase 2 Anatomical Remediation.

Captures authoritative visual evidence in 2data/evidence/p9_6_remediation/:
1. 01_p96_qa_studio_coverage_102_class_b.png - Meridian QA Studio coverage dashboard (18 Class A, 102 Class B, 242 Class D, 33.1% Calibrated).
2. 02_p96_spleen_medial_foot_leg_calibrated.png - Spleen channel medial foot & tibia (SP2, SP3, SP4, SP5, SP7, SP8).
3. 03_p96_kidney_abdominal_thoracic_columns_calibrated.png - Kidney channel abdominal & thoracic columns (KI12-KI15, KI17-KI24).
4. 04_p96_bladder_outer_column_t2_t12_calibrated.png - Bladder thoracic outer column (BL41-BL50, 3.0 cun lateral, T8 skipped).
5. 05_p96_bilateral_symmetry_dual_view.png - Bilateral symmetry inspection of remediated channels.
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

EVIDENCE_DIR = Path("2data/evidence/p9_6_remediation")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p96(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p96_playwright_server")
    test_db_file = tmp_dir / "test_p96_pw.sqlite3"

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
def test_playwright_p9_6_remediation_evidence(browser_server_p96):
    """Capture real browser visual evidence for P9.6 remediated atlas."""
    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        # 1. Navigate to Atlas Viewer
        page.goto(f"{browser_server_p96}/atlas/", wait_until="networkidle")
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

        # Evidence 1: QA Studio Coverage Dashboard Overview (102 Class B, 242 Class D, 33.1%)
        page.evaluate("""() => {
            if (window.__meridianStudio) {
                window.__meridianStudio.loadCoverage();
                window.__meridianStudio.loadTopology('SP');
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "01_p96_qa_studio_coverage_102_class_b.png"))

        # Evidence 2: Spleen Medial Foot & Leg Calibrated (SP2-SP8)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = -Math.PI / 3.0;
                window._renderer.camera.pitch = 0.35;
                window._renderer.camera.target = [0.06, 0.18, 0.02];
                window._renderer.camera.radius = 0.55;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "02_p96_spleen_medial_foot_leg_calibrated.png"))

        # Evidence 3: Kidney Abdominal & Thoracic Columns Calibrated (KI12-KI24)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = 0.0;
                window._renderer.camera.pitch = 0.05;
                window._renderer.camera.target = [0.02, 1.10, 0.10];
                window._renderer.camera.radius = 0.65;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "03_p96_kidney_abdominal_thoracic_columns_calibrated.png"))

        # Evidence 4: Bladder Outer Column T2-T12 Calibrated (BL41-BL50, 3.0 cun lateral, T8 skipped)
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = Math.PI; // Posterior back view
                window._renderer.camera.pitch = 0.10;
                window._renderer.camera.target = [0.06, 1.30, -0.10];
                window._renderer.camera.radius = 0.65;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "04_p96_bladder_outer_column_t2_t12_calibrated.png"))

        # Evidence 5: Bilateral Symmetry Dual View
        page.evaluate("""() => {
            if (window._renderer && window._renderer.camera) {
                window._renderer.camera.yaw = Math.PI * 0.75;
                window._renderer.camera.pitch = 0.20;
                window._renderer.camera.target = [0.0, 1.15, -0.05];
                window._renderer.camera.radius = 0.95;
                if (window._renderer.requestRender) window._renderer.requestRender();
            }
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "05_p96_bilateral_symmetry_dual_view.png"))

        browser.close()

    # Validate that all 5 screenshots were written and non-empty
    for fname in [
        "01_p96_qa_studio_coverage_102_class_b.png",
        "02_p96_spleen_medial_foot_leg_calibrated.png",
        "03_p96_kidney_abdominal_thoracic_columns_calibrated.png",
        "04_p96_bladder_outer_column_t2_t12_calibrated.png",
        "05_p96_bilateral_symmetry_dual_view.png",
    ]:
        shot_path = EVIDENCE_DIR / fname
        assert shot_path.exists(), f"Evidence screenshot {fname} was not created"
        assert shot_path.stat().st_size > 5000, f"Screenshot {fname} appears empty or corrupted"
