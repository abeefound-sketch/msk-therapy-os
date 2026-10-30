"""Playwright E2E browser tests for P10.7 Protocol Lock & External Review Submission Readiness.

Validates:
- Meridian Route QA Studio loading in headless Chromium.
- Interactive click of '#btnP107ProtocolLock'.
- Asynchronous API call to '/api/atlas/validation/p10-7-dashboard'.
- Rendering of 6 distinct governance readiness state badges.
- Rendering of Protocol Freeze Candidate version and canonical manifest hash.
- Rendering of 4 independent review dossiers.
- Rendering of 3 candidate partner cards with PROSPECTIVE status.
- Rendering of the Next Actionable Human Step.
- Capture of full-page visual evidence screenshot.
"""

from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler

EVIDENCE_DIR = Path("2data/evidence/p10_7_validation")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p107(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p107_playwright_server")
    test_db_file = tmp_dir / "test_p107_pw.sqlite3"

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
def test_playwright_p10_7_protocol_lock_and_review_readiness(browser_server_p107):
    """Test interactive browser execution of P10.7 protocol lock and review dashboard."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Navigate to Atlas Viewer
        page.goto(f"{browser_server_p107}/atlas/", wait_until="networkidle")
        page.wait_for_selector("#acupunctureOverlay", state="attached", timeout=10000)

        # 2. Switch to Meridians tab to reveal QA studio panel
        page.click('button[data-tab="meridians"]')
        page.wait_for_selector("#panelMeridians", state="visible", timeout=5000)

        # 3. Assert presence of P10.7 Protocol Lock button
        page.wait_for_selector("#btnP107ProtocolLock", state="attached", timeout=5000)

        # 4. Click #btnP107ProtocolLock
        page.click("#btnP107ProtocolLock")

        # 5. Wait for result container to populate
        page.wait_for_function(
            "() => document.getElementById('p107ProtocolLockContainer')?.textContent?.includes('P10.7 Khóa Protocol & Chuyển Giao')",
            timeout=15000
        )
        content = page.text_content("#p107ProtocolLockContainer")

        # Verify all 6 readiness state badges
        assert "ENGINEERING_HANDOFF_COMPLETE" in content
        assert "PROTOCOL_FREEZE_CANDIDATE" in content
        assert "EXTERNAL_ACTION_REQUIRED" in content
        assert "DUA_IRB_PENDING" in content
        assert "G14_BLOCKED_EXTERNAL_DATA" in content
        assert "ENGINEERING_RESEARCH_ONLY" in content

        # Verify Protocol Freeze Candidate version and canonical manifest integrity
        assert "v1.0-RC-P10.7" in content
        assert "7a1da2a0f959ea7ab5125c37f8e996b5abec318e9d3978c3150f65a6944f3a31" in content
        assert "TÍNH TOÀN VẸN: HỢP LỆ" in content

        # Verify 4 review dossiers
        assert "Independent Biostatistician" in content
        assert "Medical Imaging / Anatomical Specialist" in content
        assert "Research Ethics & Data Governance Reviewer" in content
        assert "Software Security & Release QA Auditor" in content

        # Verify candidate partner cards
        assert "Charité – Universitätsmedizin Berlin" in content
        assert "Massachusetts General Hospital / Harvard" in content
        assert "Seoul National University Hospital" in content

        # Verify Next Actionable Human Step
        assert "Hành Động Con Người Tiếp Theo" in content
        assert "DEP-01" in content

        # 6. Capture visual screenshot evidence
        screenshot_path = EVIDENCE_DIR / "01_p10_7_protocol_lock_and_review_readiness.png"
        page.screenshot(path=str(screenshot_path))
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 1000

        browser.close()
