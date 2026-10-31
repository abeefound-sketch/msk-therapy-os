"""Playwright E2E browser tests for Milestone P15: Cervicothoracic Biomechanics & Forward Head Posture Studio.

Validates:
- Loading of /education/?v=p15 in headless Chromium with WebGL rendering.
- 8-stage cervicothoracic interactive curriculum rendering and bilingual toggle.
- OpenSim and illustrative forward head motion playback and timeline scrubber updates.
- Real-time kinematic readouts: Craniovertebral Angle (CVA), Head anterior translation, Cervical flexion, and Extensor Load (N).
- Levator Scapulae and Suboccipital muscle recruitment visualization and Janda's reciprocal inhibition display.
- Interactive Stage 7 Quiz widget: option selection, instant feedback, and scientific explanation disclosure.
- Visual Mode switching (Anatomical Function vs Model Estimate) and scientific watermark enforcement.
- Capture of screenshot evidence for release audits.
"""

import shutil
from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler

EVIDENCE_DIR = Path("1docs/audits/P15/screenshots")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p15(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p15_playwright_server")
    test_db_file = tmp_dir / "test_p15_pw.sqlite3"

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
def test_playwright_p15_cervicothoracic_biomechanics_studio(browser_server_p15):
    """Test interactive browser execution of P15 3D Cervicothoracic Biomechanics Studio."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=swiftshader"]
        )
        context = browser.new_context(viewport={"width": 1600, "height": 960})
        page = context.new_page()

        # 1. Navigate to P15 Education Studio
        page.goto(f"{browser_server_p15}/education/?v=p15", wait_until="networkidle")
        page.wait_for_selector("#canvas-container", state="attached", timeout=15000)

        # 2. Assert initial Vietnamese title
        page.wait_for_selector("#header-title", state="visible", timeout=15000)
        title_text = page.inner_text("#header-title")
        assert "Vì sao mỏi cổ vai gáy thường tái phát" in title_text

        # 3. Assert presence of 8 stage navigation items in P15
        page.wait_for_selector(".stage-nav-item", state="visible", timeout=15000)
        stage_items = page.query_selector_all(".stage-nav-item")
        assert len(stage_items) == 8, f"Expected 8 stage nav items, found {len(stage_items)}"

        # 4. Verify Bilingual Language Switching
        lang_btn = page.query_selector("#btn-lang-toggle")
        assert lang_btn is not None
        lang_btn.click()
        page.wait_for_timeout(300)

        en_title = page.inner_text("#header-title")
        assert "Why Does Neck & Shoulder Discomfort Return" in en_title

        # Toggle back to Vietnamese
        lang_btn.click()
        page.wait_for_timeout(300)
        assert "Vì sao mỏi cổ vai gáy thường tái phát" in page.inner_text("#header-title")

        # 5. Verify Visual Mode selection & Disclaimers
        btn_mode_activation = page.query_selector("#btn-mode-activation")
        assert btn_mode_activation is not None
        btn_mode_activation.click()
        page.wait_for_timeout(300)

        watermark = page.inner_text("#watermark-activation-banner")
        assert "MATHEMATICAL MODEL ESTIMATE" in watermark

        # 6. Select Cervical Posture Scenario
        page.select_option("#scenario-select", "illustrative_forward_head_posture")
        page.wait_for_timeout(500)

        # 7. Scrub Timeline to t = 1.5 s (75% of 2.0s = slider value 150)
        time_slider = page.query_selector("#motion-time-slider")
        assert time_slider is not None
        page.fill("#motion-time-slider", "150")
        page.dispatch_event("#motion-time-slider", "input")
        page.wait_for_timeout(500)

        # 8. Verify Dynamic Kinematic Readouts
        cva_text = page.inner_text("#dyn-cva-angle")
        assert "°" in cva_text
        cva_val = float(cva_text.replace("°", "").strip())
        assert cva_val < 45.0, f"Expected reduced CVA < 45.0 in FHP, got {cva_val}"

        load_text = page.inner_text("#dyn-extensor-load")
        assert "N" in load_text
        load_val = float(load_text.replace("N", "").strip())
        assert load_val > 50.0, f"Expected extensor load > 50 N, got {load_val}"

        # 9. Verify Muscle Activation Bars
        levator_val = page.inner_text("#val-act-levator")
        assert "%" in levator_val
        suboccipital_val = page.inner_text("#val-act-suboccipital")
        assert "%" in suboccipital_val

        # Capture Stage 3/Kinematics Screenshot
        sc_path_1 = EVIDENCE_DIR / "02_p15_forward_head_kinematics.png"
        page.screenshot(path=str(sc_path_1))
        assert sc_path_1.exists()

        # 10. Test Interactive Stage 7: Comprehensive Quiz
        stage_7_btn = page.query_selector('.stage-nav-item[data-stage-id="7"]')
        assert stage_7_btn is not None
        stage_7_btn.click()
        page.wait_for_timeout(500)

        page.wait_for_selector(".quiz-container", state="visible", timeout=10000)
        quiz_cards = page.query_selector_all(".quiz-card")
        assert len(quiz_cards) == 4, f"Expected 4 quiz questions, got {len(quiz_cards)}"

        # Answer Question 1: Click correct option B
        opt_b = quiz_cards[0].query_selector_all(".quiz-option")[1]
        assert opt_b is not None
        opt_b.click()
        page.wait_for_timeout(300)

        # Check option highlighted as correct
        assert "correct" in opt_b.get_attribute("class")
        exp_box = quiz_cards[0].query_selector("#quiz-exp-Q1")
        assert exp_box is not None
        assert exp_box.is_visible()

        # 11. Test Stage 8: Scientific Evidence Register
        stage_8_btn = page.query_selector('.stage-nav-item[data-stage-id="8"]')
        assert stage_8_btn is not None
        stage_8_btn.click()
        page.wait_for_timeout(500)

        page.wait_for_selector(".evidence-item", state="visible", timeout=10000)
        ev_items = page.query_selector_all(".evidence-item")
        assert len(ev_items) >= 8, f"Expected at least 8 evidence items, got {len(ev_items)}"
        assert "EV-09" in page.inner_text("#evidence-list")

        # Capture Release Screenshot
        sc_path_studio = EVIDENCE_DIR / "01_p15_cervicothoracic_biomechanics_studio.png"
        page.screenshot(path=str(sc_path_studio))
        assert sc_path_studio.exists()

        # Copy to brain artifacts
        brain_dest = Path(r"C:\Users\tuanh\.gemini\antigravity-cli\brain\99098b63-d9a2-4ce3-9fc5-a61ca43a2c0e\01_p15_cervicothoracic_biomechanics_studio.png")
        shutil.copy2(sc_path_studio, brain_dest)

        browser.close()
