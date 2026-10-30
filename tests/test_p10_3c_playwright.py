"""Playwright End-to-End Browser Validation for P10.3C Independent Validation Studio.

Milestone: P10.3C
Verifies:
- Live browser interaction with Independent Ground-Truth Validation Governance Panel
- Verification of visual badges: [SYNTHETIC], [HOLDOUT LOCKED], [G14 FAIL-CLOSED]
- Real execution of studio buttons:
  - #btnCheckGateStatus -> Live query to /api/atlas/validation/scientific-gate/status
  - #btnRunValidationDryRun -> Live execution of synthetic dry run
  - #btnRunPilotHarness -> Live execution of 3-cohort pilot harness
  - #btnRunBootstrapCI -> Live execution of non-parametric cluster bootstrap
- Zero unhandled JavaScript exceptions, zero console errors
"""
from __future__ import annotations

import os
from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler

EVIDENCE_DIR = Path("2data/evidence/p10_3c_validation")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p103c(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p103c_playwright_server")
    test_db_file = tmp_dir / "test_p103c_pw.sqlite3"

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
def test_playwright_p10_3c_validation_studio(browser_server_p103c):
    """Test interactive browser execution of P10.3C validation studio buttons and badges."""
    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        # 1. Navigate to Atlas Viewer
        page.goto(f"{browser_server_p103c}/atlas/", wait_until="networkidle")
        page.wait_for_selector("#acupunctureOverlay", state="attached", timeout=10000)

        # 1b. Switch to Meridians tab to reveal panelMeridians
        page.click('button[data-tab="meridians"]')
        page.wait_for_selector("#panelMeridians", state="visible", timeout=5000)

        # 2. Assert Presence of Scientific Governance Badges
        page.wait_for_selector("#lblEmpiricalStatus", state="attached", timeout=5000)
        emp_status = page.text_content("#lblEmpiricalStatus")
        assert "BLOCKED_EXTERNAL_DATA" in emp_status

        page.wait_for_selector("#badgeSynthetic", state="attached", timeout=5000)
        assert "[SYNTHETIC]" in page.text_content("#badgeSynthetic")

        page.wait_for_selector("#badgeHoldoutLocked", state="attached", timeout=5000)
        assert "[HOLDOUT LOCKED]" in page.text_content("#badgeHoldoutLocked")

        page.wait_for_selector("#badgeG14FailClosed", state="attached", timeout=5000)
        assert "[G14 FAIL-CLOSED]" in page.text_content("#badgeG14FailClosed")

        # 3. Test Gate G14 Button
        page.click("#btnCheckGateStatus")
        page.wait_for_selector("#lblP103GateStatusResult", state="visible", timeout=5000)
        gate_text = page.text_content("#lblP103GateStatusResult")
        assert "BLOCKED_EXTERNAL_DATA" in gate_text

        # 4. Test Dry Run Action
        page.click("#btnRunValidationDryRun")
        page.wait_for_selector("#lblP102DryRunResult", state="visible", timeout=10000)
        dry_text = page.text_content("#lblP102DryRunResult")
        assert "PIPELINE_OPERATIONAL" in dry_text or "SYNTHETIC_TEST_SUCCESS" in dry_text

        # 5. Test Pilot Harness Action
        page.click("#btnRunPilotHarness")
        page.wait_for_selector("#lblP102DryRunResult", state="visible", timeout=10000)
        harness_text = page.text_content("#lblP102DryRunResult")
        assert "Pilot Harness" in harness_text or "PILOT_HARNESS_COMPLETED" in harness_text

        # 6. Test Bootstrap Action
        page.click("#btnRunBootstrapCI")
        page.wait_for_selector("#lblP103BootstrapResult", state="visible", timeout=10000)
        boot_text = page.text_content("#lblP103BootstrapResult")
        assert "Bootstrap CI" in boot_text

        # 7. Capture Visual Evidence Screenshot
        screenshot_path = EVIDENCE_DIR / "01_validation_studio_badges_and_actions.png"
        page.screenshot(path=str(screenshot_path))
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 1000

        # 8. Assert Zero Console or Page Errors
        assert len(console_errors) == 0, f"Unexpected browser console errors: {console_errors}"
        assert len(page_errors) == 0, f"Unexpected page errors: {page_errors}"

        browser.close()
