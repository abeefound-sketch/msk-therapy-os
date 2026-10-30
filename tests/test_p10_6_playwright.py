"""Playwright E2E browser tests for P10.6 Partner Readiness & External Governance Dashboard.

Validates:
- Meridian Route QA Studio loading in headless Chromium.
- Interactive click of '#btnP106PartnerDashboard'.
- Asynchronous API call to '/api/atlas/validation/p10-6-dashboard'.
- Rendering of 6 distinct governance readiness state badges.
- Rendering of Gate G14 fail-closed badge.
- Rendering of 3 candidate partner cards with CANDIDATE_UNCONFIRMED status.
- Capture of full-page visual evidence screenshot.
"""

from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler

EVIDENCE_DIR = Path("2data/evidence/p10_6_validation")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p106(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p106_playwright_server")
    test_db_file = tmp_dir / "test_p106_pw.sqlite3"

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
def test_playwright_p10_6_partner_readiness_studio(browser_server_p106):
    """Test interactive browser execution of P10.6 partner readiness dashboard."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Navigate to Atlas Viewer
        page.goto(f"{browser_server_p106}/atlas/", wait_until="networkidle")
        page.wait_for_selector("#acupunctureOverlay", state="attached", timeout=10000)

        # 2. Switch to Meridians tab to reveal QA studio panel
        page.click('button[data-tab="meridians"]')
        page.wait_for_selector("#panelMeridians", state="visible", timeout=5000)

        # 3. Assert presence of P10.6 Partner Readiness button
        page.wait_for_selector("#btnP106PartnerDashboard", state="attached", timeout=5000)

        # 4. Click #btnP106PartnerDashboard
        page.click("#btnP106PartnerDashboard")

        # 5. Wait for result container to populate
        page.wait_for_function(
            "() => document.getElementById('p106PartnerDashboardContainer')?.textContent?.includes('P10.6 Quản Trị Sẵn Sàng Đối Tác')",
            timeout=15000
        )
        content = page.text_content("#p106PartnerDashboardContainer")

        # Verify all 6 readiness state badges
        assert "ENGINEERING_READY" in content
        assert "PROTOCOL_DRAFT_READY" in content
        assert "PARTNER_PACKAGE_PREPARED" in content
        assert "INSTITUTIONAL_APPROVAL_PENDING" in content
        assert "EMPIRICAL_DATA_UNAVAILABLE" in content
        assert "EMPIRICAL_VALIDATION_BLOCKED" in content

        # Verify Gate G14 status
        assert "BLOCKED_EXTERNAL_DATA" in content
        assert "ENGINEERING_RESEARCH_ONLY" in content

        # Verify candidate partner cards
        assert "Charité – Universitätsmedizin Berlin" in content
        assert "Massachusetts General Hospital / Harvard" in content
        assert "Seoul National University Hospital" in content
        assert "CANDIDATE_UNCONFIRMED" in content

        # Verify sizing recommendations
        assert "N=85" in content
        assert "N=115" in content

        # 6. Capture visual screenshot evidence
        screenshot_path = EVIDENCE_DIR / "01_p10_6_partner_readiness_studio.png"
        page.screenshot(path=str(screenshot_path))
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 1000

        browser.close()
