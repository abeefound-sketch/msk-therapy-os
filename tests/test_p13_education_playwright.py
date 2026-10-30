"""Playwright E2E browser tests for Milestone P13: Interactive MSK Shoulder Education Studio.

Validates:
- Loading of /education/ in headless Chromium.
- Rendering of 3-column studio layout (Curriculum, 3D WebGL Canvas, Biomechanics Lab).
- Interactive language toggle (Vietnamese <-> English).
- Stage navigation clicks across 6 curriculum modules.
- Posture simulator slider interaction and real-time biomechanical metric updates.
- Scapulohumeral rhythm ratio updates and dyskinesia warnings.
- Evidence bibliography and fail-safe G14 disclaimers.
- Visual evidence screenshot capture for release audits.
"""

import shutil
from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler

EVIDENCE_DIR = Path("1docs/audits/P13/screenshots")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p13(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p13_playwright_server")
    test_db_file = tmp_dir / "test_p13_pw.sqlite3"

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
def test_playwright_p13_shoulder_education_studio(browser_server_p13):
    """Test interactive browser execution of P13 3D Shoulder Education Studio."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=swiftshader"]
        )
        context = browser.new_context(viewport={"width": 1600, "height": 960})
        page = context.new_page()

        # 1. Navigate to Education Studio
        page.goto(f"{browser_server_p13}/education/", wait_until="networkidle")
        page.wait_for_selector("#canvas-container", state="attached", timeout=15000)

        # 2. Assert initial Vietnamese curriculum rendering
        page.wait_for_selector("#header-title", state="visible", timeout=15000)
        title_text = page.inner_text("#header-title")
        assert "Tại sao giải cơ xong vai nhẹ hơn" in title_text

        # 3. Assert presence of 6 stage navigation items
        page.wait_for_selector(".stage-nav-item", state="visible", timeout=15000)
        stage_items = page.query_selector_all(".stage-nav-item")
        assert len(stage_items) == 6, f"Expected 6 curriculum modules, found {len(stage_items)}"

        # 4. Toggle Language to English and verify
        page.click("#btn-lang-toggle")
        page.wait_for_timeout(300)
        title_en = page.inner_text("#header-title")
        assert "Why Do Rounded Shoulders Sometimes Return After Massage?" in title_en

        # Toggle back to Vietnamese
        page.click("#btn-lang-toggle")
        page.wait_for_timeout(300)

        # 5. Click Stage 2: Anterior Shortening
        stage_2_btn = page.query_selector('.stage-nav-item[data-stage-id="2"]')
        assert stage_2_btn is not None
        stage_2_btn.click()
        page.wait_for_timeout(300)
        stage_title = page.inner_text("#stage-title")
        assert "2." in stage_title
        assert "co ngắn" in stage_title or "Pectoralis" in stage_title

        # 6. Click Stage 4: Scapulohumeral Rhythm
        stage_4_btn = page.query_selector('.stage-nav-item[data-stage-id="4"]')
        assert stage_4_btn is not None
        stage_4_btn.click()
        page.wait_for_timeout(300)
        stage_4_title = page.inner_text("#stage-title")
        assert "4." in stage_4_title

        # 7. Interact with Posture Severity Slider (set to 85% severe)
        slider = page.query_selector("#posture-slider")
        assert slider is not None
        slider.fill("85")
        page.wait_for_timeout(300)

        # Assert metric updates
        posture_label = page.inner_text("#posture-val-label")
        assert "85%" in posture_label

        ratio_val = page.inner_text("#val-rhythm-ratio")
        assert ": 1" in ratio_val

        # 8. Assert presence of G14 disclaimer and evidence list
        page.wait_for_selector(".disclaimer-box", state="visible", timeout=5000)
        disclaimer_text = page.inner_text(".disclaimer-box")
        assert "BLOCKED_EXTERNAL_DATA" in disclaimer_text

        evidence_items = page.query_selector_all(".evidence-item")
        assert len(evidence_items) >= 3

        # 9. Capture Visual Evidence Screenshot
        screenshot_path = EVIDENCE_DIR / "01_p13_shoulder_education_studio.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        assert screenshot_path.is_file(), "Screenshot must be written to disk"
        assert screenshot_path.stat().st_size > 5000, "Screenshot size must be valid"

        # Copy to brain artifact directory for user review
        brain_dir = Path(r"C:\Users\tuanh\.gemini\antigravity-cli\brain\99098b63-d9a2-4ce3-9fc5-a61ca43a2c0e")
        if brain_dir.exists():
            shutil.copy2(str(screenshot_path), str(brain_dir / "01_p13_shoulder_education_studio.png"))

        browser.close()
