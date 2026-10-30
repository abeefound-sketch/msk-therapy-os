"""Playwright E2E browser tests for Milestone P14: Evidence-Grounded Dynamic Biomechanics & MSK Education Studio.

Validates:
- Loading of /education/?v=p14 in headless Chromium with WebGL rendering.
- 8-stage interactive curriculum rendering and bilingual toggle.
- OpenSim dynamic motion playback and timeline scrubber updates.
- Real-time kinematic angle readouts (arm elevation, scapular upward rotation, clavicular elevation).
- Model-estimated muscle activations vs unavailable muscle flags.
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

EVIDENCE_DIR = Path("1docs/audits/P14/screenshots")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p14(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p14_playwright_server")
    test_db_file = tmp_dir / "test_p14_pw.sqlite3"

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
def test_playwright_p14_shoulder_biomechanics_studio(browser_server_p14):
    """Test interactive browser execution of P14 3D Dynamic Biomechanics Studio."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=swiftshader"]
        )
        context = browser.new_context(viewport={"width": 1600, "height": 960})
        page = context.new_page()

        # 1. Navigate to P14 Education Studio
        page.goto(f"{browser_server_p14}/education/?v=p14", wait_until="networkidle")
        page.wait_for_selector("#canvas-container", state="attached", timeout=15000)

        # 2. Assert initial Vietnamese title
        page.wait_for_selector("#header-title", state="visible", timeout=15000)
        title_text = page.inner_text("#header-title")
        assert "Điều gì xảy ra khi bạn giơ tay" in title_text

        # 3. Assert presence of 8 stage navigation items in P14
        page.wait_for_selector(".stage-nav-item", state="visible", timeout=15000)
        stage_items = page.query_selector_all(".stage-nav-item")
        assert len(stage_items) == 8, f"Expected 8 curriculum stages in P14, found {len(stage_items)}"

        # 4. Toggle Language to English and verify
        page.click("#btn-lang-toggle")
        page.wait_for_timeout(300)
        title_en = page.inner_text("#header-title")
        assert "What Happens When You Raise Your Arm" in title_en

        # Toggle back to Vietnamese
        page.click("#btn-lang-toggle")
        page.wait_for_timeout(300)

        # 5. Capture Initial Pose Screenshot (t = 0.0s)
        screenshot_t0 = EVIDENCE_DIR / "01_p14_shoulder_kinematics_t0.png"
        page.screenshot(path=str(screenshot_t0), full_page=True)
        assert screenshot_t0.is_file()

        # 6. Interact with Dynamic Motion Scrubber (Advance to t = 1.5s -> slider value 150)
        slider = page.query_selector("#motion-time-slider")
        assert slider is not None
        slider.fill("150")
        page.wait_for_timeout(500)

        # Assert dynamic kinematic angles updated
        arm_elev_text = page.inner_text("#dyn-arm-elev")
        arm_elev_val = float(arm_elev_text.replace("°", "").strip())
        assert arm_elev_val >= 80.0, f"Expected arm elevation >= 80 deg at t=1.5s, got {arm_elev_val}"

        scap_up_text = page.inner_text("#dyn-scap-up")
        scap_up_val = float(scap_up_text.replace("°", "").strip())
        assert scap_up_val >= 25.0, f"Expected scapular upward rotation >= 25 deg at t=1.5s, got {scap_up_val}"

        clav_elev_text = page.inner_text("#dyn-clav-elev")
        clav_elev_val = float(clav_elev_text.replace("°", "").strip())
        assert clav_elev_val >= 8.0, f"Expected clavicular elevation >= 8 deg at t=1.5s, got {clav_elev_val}"

        # 7. Check Muscle Recruitment Displays
        deltoid_val = page.inner_text("#val-act-deltoid-lateral")
        assert "%" in deltoid_val
        pec_minor_val = page.inner_text("#val-act-pec-minor")
        assert "%" in pec_minor_val
        rhomboid_val = page.inner_text("#val-act-rhomboid")
        assert "CHƯA CÓ TRONG MÔ HÌNH" in rhomboid_val or "DATA UNAVAILABLE" in rhomboid_val

        # 8. Test Visual Mode Switching
        page.click("#btn-mode-activation")
        page.wait_for_timeout(200)
        watermark = page.inner_text("#watermark-activation-banner")
        assert "MATHEMATICAL MODEL ESTIMATE" in watermark
        assert "NOT MEASURED EMG" in watermark

        page.click("#btn-mode-anatomy")
        page.wait_for_timeout(200)
        watermark_anatomy = page.inner_text("#watermark-activation-banner")
        assert "ANATOMICAL FUNCTION" in watermark_anatomy

        # 9. Test Interactive Quiz (Stage 7)
        stage_7_btn = page.query_selector('.stage-nav-item[data-stage-id="7"]')
        assert stage_7_btn is not None
        stage_7_btn.click()
        page.wait_for_timeout(400)

        page.wait_for_selector(".quiz-container", state="visible", timeout=5000)
        quiz_cards = page.query_selector_all(".quiz-card")
        assert len(quiz_cards) == 4, f"Expected 4 quiz questions, found {len(quiz_cards)}"

        # Answer Q1 (Option B is correct)
        q1_opts = page.query_selector_all("#quiz-opts-Q1 .quiz-option")
        assert len(q1_opts) == 3
        q1_opts[1].click()  # Click option B
        page.wait_for_timeout(200)

        # Assert correct styling and explanation disclosure
        assert "correct" in (q1_opts[1].get_attribute("class") or "")
        q1_exp = page.query_selector("#quiz-exp-Q1")
        assert q1_exp is not None and q1_exp.is_visible()

        # Answer Q2, Q3, Q4 with correct Option B
        for q_id in ["Q2", "Q3", "Q4"]:
            opts = page.query_selector_all(f"#quiz-opts-{q_id} .quiz-option")
            opts[1].click()
            page.wait_for_timeout(100)
            assert "correct" in (opts[1].get_attribute("class") or "")

        # 10. Test Stage 8 Evidence Register
        stage_8_btn = page.query_selector('.stage-nav-item[data-stage-id="8"]')
        assert stage_8_btn is not None
        stage_8_btn.click()
        page.wait_for_timeout(400)

        ev_cards = page.query_selector_all("#stage-dynamic-body .card")
        assert len(ev_cards) == 8, f"Expected 8 evidence cards in Stage 8, found {len(ev_cards)}"

        # 11. Capture Elevated Pose Screenshot (t = 1.5s with Quiz & Bio-readouts)
        screenshot_t15 = EVIDENCE_DIR / "02_p14_shoulder_kinematics_t15.png"
        page.screenshot(path=str(screenshot_t15), full_page=True)
        assert screenshot_t15.is_file()

        release_summary_png = EVIDENCE_DIR / "01_p14_shoulder_biomechanics_studio.png"
        shutil.copy2(str(screenshot_t15), str(release_summary_png))

        # Copy to brain artifact directory for user review
        brain_dir = Path(r"C:\Users\tuanh\.gemini\antigravity-cli\brain\99098b63-d9a2-4ce3-9fc5-a61ca43a2c0e")
        if brain_dir.exists():
            shutil.copy2(str(release_summary_png), str(brain_dir / "01_p14_shoulder_biomechanics_studio.png"))

        browser.close()
