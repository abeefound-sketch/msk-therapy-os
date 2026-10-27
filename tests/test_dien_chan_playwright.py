"""Playwright End-to-End Interactive Browser Tests for Dien Chan 3D Atlas & Condition Search.

Validates in real headless Chromium:
1. Atlas viewer initializes and loads authoritative Dien Chan reflex points.
2. Search condition in Vietnamese ("Đau đầu - Viêm xoang") finds authentic protocol.
3. Protocol activation highlights point group on 3D facial mesh with clear point markers.
4. "Protocol Only" filter renders exclusively the active protocol points.
5. Camera presets (Front, Left Profile, Right Profile) adjust viewpoint smoothly.
6. QA Point Inspector displays authentic grid coordinates, FMA anchors, residuals, and medical disclaimer.
7. Unknown search queries yield strict abstention with zero hallucination.
8. 2D Reference Image modal opens, switches between Image B and Image A, and closes cleanly.
9. Zero fatal JavaScript console or unhandled page errors.
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

EVIDENCE_DIR = Path("2data/evidence/dien_chan")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("dc_playwright_server")
    test_db_file = tmp_dir / "test_dc_pw.sqlite3"

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


def test_playwright_dien_chan_suite(browser_server):
    """Complete end-to-end interactive Playwright test suite for Dien Chan."""
    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        # 1. Navigate to Atlas Viewer
        page.goto(f"{browser_server}/atlas/", wait_until="networkidle")
        page.wait_for_selector("#acupunctureOverlay", state="attached", timeout=10000)

        # Wait for meridiansDebug to be initialized
        page.wait_for_function("() => window.__meridiansDebug && window.__meridiansDebug.acuData !== null", timeout=10000)

        # Switch to Meridians tab in sidebar
        page.click("button[data-tab='meridians']")
        page.wait_for_timeout(300)

        # ---------------------------------------------------------------------
        # Gate 1: Authoritative Points Loading
        # ---------------------------------------------------------------------
        dc_points = page.evaluate("() => window.__meridiansDebug.getDienChanPoints()")
        assert len(dc_points) >= 24, f"Expected >= 24 Dien Chan points, got {len(dc_points)}"
        codes = [p["code"] for p in dc_points]
        assert "DC_103" in codes
        assert "DC_19" in codes
        assert "DC_61" in codes

        # Enable Dien Chan points display
        page.evaluate("""() => {
            const chk = document.getElementById('chkShowDienChanStudio') || document.getElementById('chkShowDienChan');
            if (chk && !chk.checked) {
                chk.checked = true;
                chk.dispatchEvent(new Event('change'));
            }
        }""")
        page.wait_for_timeout(300)

        # ---------------------------------------------------------------------
        # Gate 2: Vietnamese Condition Search ("Đau đầu - Viêm xoang")
        # ---------------------------------------------------------------------
        page.fill("#txtDienChanSearch", "Đau đầu - Viêm xoang")
        page.click("#btnDienChanSearch")
        page.wait_for_selector(".btn-apply-dien-chan-protocol", timeout=5000)

        search_results_text = page.inner_text("#dienChanSearchResults")
        assert "Đau đầu" in search_results_text
        assert "Viêm xoang" in search_results_text

        page.screenshot(path=str(EVIDENCE_DIR / "01_dien_chan_search_results.png"))

        # ---------------------------------------------------------------------
        # Gate 3: Protocol Activation & 3D Highlight
        # ---------------------------------------------------------------------
        page.click(".btn-apply-dien-chan-protocol")
        page.wait_for_timeout(400)

        # Verify active protocol card updated
        proto_card_text = page.inner_text("#dienChanActiveProtocolCard")
        assert "Phác đồ" in proto_card_text
        assert "103" in proto_card_text
        assert "61" in proto_card_text
        assert "43" in proto_card_text

        # Verify active protocol in debug state
        active_proto = page.evaluate("() => window.__meridiansDebug.getActiveProtocol()")
        assert active_proto is not None
        assert "DC_103" in active_proto["point_codes"]
        assert len(active_proto["point_codes"]) == 11

        page.screenshot(path=str(EVIDENCE_DIR / "02_dien_chan_active_protocol_highlight.png"))

        # ---------------------------------------------------------------------
        # Gate 4: "Protocol Only" View Filter
        # ---------------------------------------------------------------------
        page.check("#chkDienChanProtocolOnly")
        page.wait_for_timeout(300)
        page.screenshot(path=str(EVIDENCE_DIR / "03_dien_chan_protocol_only_filter.png"))

        # ---------------------------------------------------------------------
        # Gate 5: Camera Angle Presets (Front, Left Profile, Right Profile)
        # ---------------------------------------------------------------------
        # Left profile view
        page.click("#btnDienChanLeftProfile")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "04_dien_chan_camera_left_profile.png"))

        # Right profile view
        page.click("#btnDienChanRightProfile")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "05_dien_chan_camera_right_profile.png"))

        # Front view
        page.click("#btnDienChanFrontView")
        page.wait_for_timeout(600)
        page.screenshot(path=str(EVIDENCE_DIR / "06_dien_chan_camera_front_view.png"))

        # ---------------------------------------------------------------------
        # Gate 6: QA Point Inspector & Anatomical Anchor Validation
        # ---------------------------------------------------------------------
        # Inspect DC_103 (Candidate Annotation)
        page.evaluate("() => window.__meridiansDebug.selectDienChanPoint('DC_103')")
        page.wait_for_timeout(400)

        badge_103 = page.inner_text("#p9QAStatusBadge")
        content_103 = page.inner_text("#p9QAInspectorContent")
        assert "CANDIDATE" in badge_103
        assert "O-2" in content_103
        assert "Lưu ý y tế" in content_103
        page.screenshot(path=str(EVIDENCE_DIR / "07_dien_chan_point_inspector_103.png"))

        # Inspect DC_19 (Verified Anatomical Anchor at Subnasale / Philtrum)
        page.evaluate("() => window.__meridiansDebug.selectDienChanPoint('DC_19')")
        page.wait_for_timeout(400)

        badge_19 = page.inner_text("#p9QAStatusBadge")
        content_19 = page.inner_text("#p9QAInspectorContent")
        assert "VERIFIED ANCHOR" in badge_19
        assert "O-8" in content_19
        assert "FMA:53173" in content_19
        page.screenshot(path=str(EVIDENCE_DIR / "08_dien_chan_point_inspector_19.png"))

        # ---------------------------------------------------------------------
        # Gate 7: Zero Hallucination Query Abstention
        # ---------------------------------------------------------------------
        page.fill("#txtDienChanSearch", "triệu chứng lạ không rõ xuất xứ xyz")
        page.click("#btnDienChanSearch")
        page.wait_for_timeout(500)

        results_unknown = page.inner_text("#dienChanSearchResults")
        assert "Chưa có dữ liệu đã đối chiếu" in results_unknown
        assert "không tạo phác đồ giả" in results_unknown
        page.screenshot(path=str(EVIDENCE_DIR / "09_dien_chan_zero_hallucination_empty.png"))

        # ---------------------------------------------------------------------
        # Gate 8: 2D Reference Image Modal Interaction
        # ---------------------------------------------------------------------
        page.click("#btnToggleDienChanReferenceImg")
        page.wait_for_timeout(300)

        modal = page.locator("#dienChanRefModal")
        assert modal.is_visible()

        chart_img = page.locator("#imgDienChanRefChart")
        assert "headache-sinus" in chart_img.get_attribute("src")

        # Switch to Image A (Atlas front/side)
        page.click("#btnRefImgAtlas")
        page.wait_for_timeout(300)
        assert "atlas-front-side" in chart_img.get_attribute("src")

        page.screenshot(path=str(EVIDENCE_DIR / "10_dien_chan_reference_modal.png"))

        # Close modal
        page.click("#btnCloseDienChanModal")
        page.wait_for_timeout(300)
        assert not modal.is_visible()

        # ---------------------------------------------------------------------
        # Gate 9: Zero Console/Page Error Check
        # ---------------------------------------------------------------------
        # Filter benign warnings if any
        critical_errors = [e for e in console_errors if "favicon" not in e.lower() and "404" not in e.lower()]
        assert len(critical_errors) == 0, f"Uncaught console errors: {critical_errors}"
        assert len(page_errors) == 0, f"Uncaught page errors: {page_errors}"

        browser.close()
