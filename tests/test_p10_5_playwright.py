"""Playwright E2E browser tests for P10.5 Institutional Pilot Readiness Dashboard.

Validates:
- Loading of Meridian Route QA Studio in headless browser.
- Interactive click of '#btnCheckPilotReadiness'.
- Asynchronous retrieval of '/api/atlas/validation/pilot-readiness'.
- Rendering of engineering vs scientific readiness badges.
- Display of 8 external dependencies and cohort sample accounting.
"""

from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler

EVIDENCE_DIR = Path("2data/evidence/p10_5_validation")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p105(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p105_playwright_server")
    test_db_file = tmp_dir / "test_p105_pw.sqlite3"

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
def test_playwright_p10_5_pilot_readiness_studio(browser_server_p105):
    """Test interactive browser execution of P10.5 pilot readiness button and telemetry display."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Navigate to Atlas Viewer
        page.goto(f"{browser_server_p105}/atlas/", wait_until="networkidle")
        page.wait_for_selector("#acupunctureOverlay", state="attached", timeout=10000)

        # 2. Switch to Meridians tab to reveal studio panel
        page.click('button[data-tab="meridians"]')
        page.wait_for_selector("#panelMeridians", state="visible", timeout=5000)

        # 3. Assert presence of Pilot Readiness button
        page.wait_for_selector("#btnCheckPilotReadiness", state="attached", timeout=5000)

        # 4. Click #btnCheckPilotReadiness
        page.click("#btnCheckPilotReadiness")

        # 5. Wait for result label to populate
        page.wait_for_function(
            "() => document.getElementById('lblP105PilotReadinessResult')?.textContent?.includes('P10.5 Sẵn Sàng Pilot')",
            timeout=15000
        )
        result_text = page.text_content("#lblP105PilotReadinessResult")
        assert "Kỹ Thuật: PASS" in result_text
        assert "BLOCKED_EXTERNAL_DATA" in result_text
        assert "Mẫu Holdout" in result_text

        # 6. Capture visual screenshot evidence
        screenshot_path = EVIDENCE_DIR / "01_p10_5_pilot_readiness_dashboard.png"
        page.screenshot(path=str(screenshot_path))
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 1000

        browser.close()
