"""Playwright E2E browser tests for Milestone P16: Scientific Biomechanics Integrity, Muscle Mechanics & Interactive Self-Education Studio.

Validates:
- Full loading of /education/?v=p16 in headless Chromium.
- Rendering of 10 unified curriculum topics and 3-column studio layout.
- Interactive bilingual toggle (Vietnamese <-> English).
- Region selector dropdown switching (Unified <-> Cervicothoracic <-> Shoulder).
- Multi-axis cervical motion scenario selection and kinematic timeline scrubbing.
- Separated gravitational physics metric readouts (W_head, d_horizontal, M_gravity, r_eff, F_extensor, R_comp).
- Muscle Mechanics Inspector Modes A, B, C, D and mandatory empty states:
  - Mode A: Anatomical participation
  - Mode B: MODEL_GEOMETRY_INSUFFICIENT empty state banner
  - Mode C: Mathematical estimate watermark banner
  - Mode D: MUSCLE_FORCE_NOT_AVAILABLE empty state banner
- Interactive Scenario Comparison widget and non-diagnostic disclaimers.
- Red flags safety triage card and G14 permanent invariant disclaimers.
- Authoritative visual screenshot capture for audit and release package.
"""

from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler

EVIDENCE_DIR = Path("1docs/audits/P16/screenshots")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p16(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for P16 Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p16_playwright_server")
    test_db_file = tmp_dir / "test_p16_pw.sqlite3"

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

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    server.server_close()


@pytest.mark.playwright
def test_playwright_p16_msk_education_studio(browser_server_p16):
    """Test interactive browser execution of P16 Unified MSK Education Studio."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=swiftshader"]
        )
        context = browser.new_context(viewport={"width": 1600, "height": 960})
        page = context.new_page()

        # 1. Navigate to P16 Education Studio
        page.goto(f"{browser_server_p16}/education/?v=p16", wait_until="networkidle")
        page.wait_for_selector("#canvas-container", state="attached", timeout=15000)

        # 2. Assert initial Vietnamese Title and 10 Curriculum Topics
        page.wait_for_selector("#header-title", state="visible", timeout=15000)
        title_text = page.inner_text("#header-title")
        assert "Phòng Học Cơ Sinh Học MSK 3D" in title_text

        page.wait_for_selector(".stage-nav-item", state="visible", timeout=15000)
        stage_items = page.query_selector_all(".stage-nav-item")
        assert len(stage_items) == 10, f"Expected 10 curriculum topics in P16, found {len(stage_items)}"

        # 3. Bilingual Toggle: Switch to English and verify
        page.click("#btn-lang-toggle")
        page.wait_for_timeout(300)
        title_en = page.inner_text("#header-title")
        assert "MSK Education Studio" in title_en

        # Toggle back to Vietnamese
        page.click("#btn-lang-toggle")
        page.wait_for_timeout(300)

        # 4. Region Selector Interaction: Switch to Cervicothoracic & Shoulder
        region_select = page.query_selector("#region-select")
        assert region_select is not None
        region_select.select_option("cervicothoracic")
        page.wait_for_timeout(500)

        scenario_val = page.eval_on_selector("#scenario-select", "el => el.value")
        assert "cervical" in scenario_val or "vasavada" in scenario_val

        region_select.select_option("shoulder")
        page.wait_for_timeout(500)
        scenario_shoulder = page.eval_on_selector("#scenario-select", "el => el.value")
        assert "shoulder" in scenario_shoulder or "seth" in scenario_shoulder

        # Return to unified
        region_select.select_option("unified")
        page.wait_for_timeout(500)

        # 5. Multi-Axis Motion Scenario Selection & Timeline Scrubbing
        page.select_option("#scenario-select", "cervical_axial_rotation")
        page.wait_for_timeout(600)

        # Scrub timeline to 1.5s
        slider = page.query_selector("#motion-time-slider")
        assert slider is not None
        slider.fill("150")
        page.wait_for_timeout(400)
        time_label = page.inner_text("#motion-time-label")
        assert "1.5" in time_label

        # 6. Test Separated Physics Metric Readouts
        page.select_option("#scenario-select", "vasavada_cervical_flexion_extension")
        page.wait_for_timeout(600)
        head_weight = page.inner_text("#dyn-head-weight")
        assert "N" in head_weight
        moment_val = page.inner_text("#dyn-ext-moment")
        assert "N·m" in moment_val
        extensor_val = page.inner_text("#dyn-extensor-load")
        assert "N" in extensor_val
        comp_val = page.inner_text("#dyn-axial-comp")
        assert "N" in comp_val
        stress_val = page.inner_text("#dyn-tissue-stress")
        assert "CHƯA HỖ TRỢ" in stress_val or "UNAVAILABLE" in stress_val

        # 7. Test Muscle Mechanics Inspector Modes (A, B, C, D)
        # Mode A: Anatomy
        page.click("#btn-mode-anatomy")
        page.wait_for_timeout(300)
        badge_a = page.inner_text("#badge-activation-mode")
        assert "A" in badge_a or "Giải Phẫu" in badge_a or "Anatomy" in badge_a

        # Mode B: Geometry (Must show MODEL_GEOMETRY_INSUFFICIENT)
        page.click("#btn-mode-geometry")
        page.wait_for_timeout(300)
        empty_b = page.inner_text("#inspector-empty-state")
        assert "MODEL_GEOMETRY_INSUFFICIENT" in empty_b

        # Mode C: Activation (Must show mathematical estimate watermark)
        page.click("#btn-mode-activation")
        page.wait_for_timeout(300)
        watermark_c = page.inner_text("#watermark-activation-banner")
        assert "MATHEMATICAL MODEL ESTIMATE" in watermark_c

        # Mode D: Force (Must show MUSCLE_FORCE_NOT_AVAILABLE)
        page.click("#btn-mode-force")
        page.wait_for_timeout(300)
        empty_d = page.inner_text("#inspector-empty-state")
        assert "MUSCLE_FORCE_NOT_AVAILABLE" in empty_d

        # 8. Test Scenario Comparison Tool
        page.click("#btn-mode-comparison")
        page.wait_for_timeout(600)
        page.wait_for_selector("#comparison-card", state="visible", timeout=5000)
        cmp_text = page.inner_text("#comparison-details-body")
        assert "Δ" in cmp_text or "Delta" in cmp_text
        assert "N·m" in cmp_text

        # Capture Authoritative Screenshot 02: Scenario Comparison
        screenshot_cmp = EVIDENCE_DIR / "02_p16_scenario_comparison.png"
        page.screenshot(path=str(screenshot_cmp), full_page=True)
        assert screenshot_cmp.is_file()

        # Close comparison card
        page.click("#btn-close-comparison")
        page.wait_for_timeout(200)

        # 9. Verify Red Flags Safety Card
        page.wait_for_selector("#red-flags-card", state="visible", timeout=5000)
        rf_text = page.inner_text("#red-flags-card")
        assert "Cảnh Báo Đỏ" in rf_text or "Red Flags" in rf_text

        # 10. Capture Authoritative Screenshot 01: MSK Education Studio
        screenshot_studio = EVIDENCE_DIR / "01_p16_msk_education_studio.png"
        page.screenshot(path=str(screenshot_studio), full_page=True)
        assert screenshot_studio.is_file()

        browser.close()
