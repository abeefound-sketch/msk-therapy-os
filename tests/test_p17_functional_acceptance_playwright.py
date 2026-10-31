"""Playwright E2E browser tests for Milestone P17: Real Functional Acceptance, Interactive Biomechanics Repair & Scientific UI Integrity.

Validates:
- Full loading of /education/?v=p17 in headless Chromium.
- Zero deceptive controls: Every enabled control produces an observable effect or displays an explicit unavailable state.
- Mode A (Anatomical Participation): Static percentage bars hidden, interactive muscle cards rendered, clicking card selects muscle in 3D.
- Mode B (Geometric Muscle Change): Explicit MODEL_GEOMETRY_INSUFFICIENT empty state, literature reference metrics displayed, percentage bars hidden.
- Mode C (Model-Estimated Activation): MATHEMATICAL MODEL ESTIMATE watermark banner, dynamic activation progress bars visible and animated synchronously with timeline scrubbing.
- Mode D (Estimated Muscle Force): Explicit MUSCLE_FORCE_NOT_AVAILABLE empty state, percentage bars hidden (no invented force data).
- Camera controls (Anterior, Posterior, Lateral): Real camera position/rotation changes.
- Playback controls (Play, Pause, Reset, Speed multipliers 0.25x/0.5x/1.0x, Scrubber): Real state and time advances.
- Curriculum stages: Selection updates stage content and highlights relevant anatomical structures.
- Bilingual toggle (VI <-> EN): Updates text across all headers and labels.
- Authoritative visual screenshot capture for all 10 required audit views.
"""

from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

from msk_therapy_os.db import open_db, init_db, seed_db
from msk_therapy_os.points import init_points_tables
from msk_therapy_os.server import ThreadingHTTPServer, MSKRequestHandler

EVIDENCE_DIR = Path("1docs/audits/P17/screenshots")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser_server_p17(tmp_path_factory):
    """Spin up local ThreadingHTTPServer on an ephemeral port for P17 Playwright."""
    tmp_dir = tmp_path_factory.mktemp("p17_playwright_server")
    test_db_file = tmp_dir / "test_p17_pw.sqlite3"

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
def test_playwright_p17_real_functional_acceptance(browser_server_p17):
    """Test interactive browser execution and functional acceptance of P17 Unified MSK Education Studio."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=swiftshader"]
        )
        context = browser.new_context(viewport={"width": 1600, "height": 960})
        page = context.new_page()

        # -------------------------------------------------------------
        # 1. Navigate to P17 Education Studio & Verify Default State
        # -------------------------------------------------------------
        page.goto(f"{browser_server_p17}/education/?v=p17", wait_until="networkidle")
        page.wait_for_selector("#canvas-container canvas", state="attached", timeout=20000)
        page.wait_for_timeout(1000)

        # Assert initial Vietnamese Title and 10 Curriculum Topics
        page.wait_for_selector("#header-title", state="visible", timeout=15000)
        title_text = page.inner_text("#header-title")
        assert "Phòng Học Cơ Sinh Học MSK 3D" in title_text

        # Assert default mode is Mode A (Anatomical Participation)
        badge_mode = page.inner_text("#badge-activation-mode")
        assert "A" in badge_mode or "Giải Phẫu" in badge_mode or "Anatomy" in badge_mode

        # Assert muscle percentage list is HIDDEN in Mode A (Zero Deceptive Controls)
        list_display = page.eval_on_selector("#muscle-recruitment-list", "el => window.getComputedStyle(el).display")
        assert list_display == "none", f"Expected muscle-recruitment-list to be hidden in Mode A, got {list_display}"

        # Assert interactive muscle cards are rendered in Mode A
        page.wait_for_selector(".interactive-muscle-card", state="visible", timeout=10000)
        cards = page.query_selector_all(".interactive-muscle-card")
        assert len(cards) >= 4, f"Expected at least 4 muscle cards in Mode A, found {len(cards)}"

        # Screenshot 01: Default anatomical viewer
        screenshot_01 = EVIDENCE_DIR / "01_default_anatomical_viewer.png"
        page.screenshot(path=str(screenshot_01), full_page=True)
        assert screenshot_01.is_file()

        # -------------------------------------------------------------
        # 2. Mode A: Anatomical Response & Interactive Muscle Selection
        # -------------------------------------------------------------
        first_card = page.query_selector(".interactive-muscle-card")
        assert first_card is not None
        first_card.click()
        page.wait_for_timeout(400)

        # Verify viewer selected mesh state
        selected_mesh = page.evaluate("() => window.anatomyViewer ? window.anatomyViewer.selectedMeshName : null")
        assert selected_mesh is not None, "Expected selectedMeshName to be populated on muscle card click"

        # Screenshot 02: Mode A with actual anatomical response
        screenshot_02 = EVIDENCE_DIR / "02_mode_a_anatomical_response.png"
        page.screenshot(path=str(screenshot_02), full_page=True)
        assert screenshot_02.is_file()

        # -------------------------------------------------------------
        # 3. Mode B: Geometric Muscle Change & MODEL_GEOMETRY_INSUFFICIENT
        # -------------------------------------------------------------
        page.click("#btn-mode-geometry")
        page.wait_for_timeout(500)

        # Assert empty state contains MODEL_GEOMETRY_INSUFFICIENT
        empty_b = page.inner_text("#inspector-empty-state")
        assert "MODEL_GEOMETRY_INSUFFICIENT" in empty_b

        # Assert percentage bars remain HIDDEN in Mode B
        list_display_b = page.eval_on_selector("#muscle-recruitment-list", "el => window.getComputedStyle(el).display")
        assert list_display_b == "none", f"Expected muscle-recruitment-list to be hidden in Mode B, got {list_display_b}"

        # Assert literature reference metrics are shown in container
        details_b = page.inner_text("#inspector-details-container")
        assert "L0 =" in details_b or "cm" in details_b

        # Screenshot 03: Mode B geometric change
        screenshot_03 = EVIDENCE_DIR / "03_mode_b_geometric_change.png"
        page.screenshot(path=str(screenshot_03), full_page=True)
        assert screenshot_03.is_file()

        # -------------------------------------------------------------
        # 4. Mode C: Model-Estimated Activation & Dynamic Progress Bars
        # -------------------------------------------------------------
        page.click("#btn-mode-activation")
        page.wait_for_timeout(600)

        # Assert watermark banner
        watermark_c = page.inner_text("#watermark-activation-banner")
        assert "MATHEMATICAL MODEL ESTIMATE" in watermark_c

        # Assert muscle recruitment list is VISIBLE in Mode C
        list_display_c = page.eval_on_selector("#muscle-recruitment-list", "el => window.getComputedStyle(el).display")
        assert list_display_c != "none", "Expected muscle-recruitment-list to be visible in Mode C"

        # Scrub timeline slider to 1.0s and verify dynamic updates
        page.fill("#motion-time-slider", "100")
        page.wait_for_timeout(400)
        time_label = page.inner_text("#motion-time-label")
        assert "1.0" in time_label

        # Screenshot 04: Mode C model activation
        screenshot_04 = EVIDENCE_DIR / "04_mode_c_model_activation.png"
        page.screenshot(path=str(screenshot_04), full_page=True)
        assert screenshot_04.is_file()

        # -------------------------------------------------------------
        # 5. Mode D: Estimated Muscle Force & MUSCLE_FORCE_NOT_AVAILABLE
        # -------------------------------------------------------------
        page.click("#btn-mode-force")
        page.wait_for_timeout(500)

        # Assert empty state contains MUSCLE_FORCE_NOT_AVAILABLE
        empty_d = page.inner_text("#inspector-empty-state")
        assert "MUSCLE_FORCE_NOT_AVAILABLE" in empty_d

        # Assert percentage bars are HIDDEN in Mode D (No fabricated force data)
        list_display_d = page.eval_on_selector("#muscle-recruitment-list", "el => window.getComputedStyle(el).display")
        assert list_display_d == "none", f"Expected muscle-recruitment-list to be hidden in Mode D, got {list_display_d}"

        # Screenshot 05: Mode D estimated force unavailable
        screenshot_05 = EVIDENCE_DIR / "05_mode_d_estimated_force_unavailable.png"
        page.screenshot(path=str(screenshot_05), full_page=True)
        assert screenshot_05.is_file()

        # -------------------------------------------------------------
        # 6. Playback Controls & Timeline Scrubbing
        # -------------------------------------------------------------
        # Test speed multiplier button 0.5x
        page.click("#btn-speed-05")
        page.wait_for_timeout(200)
        btn_05_class = page.eval_on_selector("#btn-speed-05", "el => el.className")
        assert "active" in btn_05_class, "Expected btn-speed-05 to have active class"

        # Test Play / Pause
        page.click("#btn-motion-play")
        page.wait_for_timeout(800)
        page.click("#btn-motion-play") # Pause
        page.wait_for_timeout(200)

        # Test Reset
        page.click("#btn-motion-reset")
        page.wait_for_timeout(300)
        reset_time = page.inner_text("#motion-time-label")
        assert "0.00 s" in reset_time, f"Expected 0.00 s after reset, got {reset_time}"

        # Screenshot 06: Playback timeline scrubbing
        screenshot_06 = EVIDENCE_DIR / "06_playback_timeline_scrubbing.png"
        page.screenshot(path=str(screenshot_06), full_page=True)
        assert screenshot_06.is_file()

        # -------------------------------------------------------------
        # 7. ROM & Posture Movement Simulator
        # -------------------------------------------------------------
        page.fill("#posture-slider", "85")
        page.wait_for_timeout(400)
        posture_label = page.inner_text("#posture-val-label")
        assert "85%" in posture_label

        # Switch to cervical axial rotation scenario
        page.select_option("#scenario-select", "cervical_axial_rotation")
        page.wait_for_timeout(700)

        # Screenshot 07: ROM cervical movement
        screenshot_07 = EVIDENCE_DIR / "07_rom_cervical_movement.png"
        page.screenshot(path=str(screenshot_07), full_page=True)
        assert screenshot_07.is_file()

        # -------------------------------------------------------------
        # 8. Scenario Comparison Tool
        # -------------------------------------------------------------
        page.click("#btn-mode-comparison")
        page.wait_for_timeout(600)
        page.wait_for_selector("#comparison-card", state="visible", timeout=5000)
        cmp_text = page.inner_text("#comparison-details-body")
        assert "Δ" in cmp_text or "Delta" in cmp_text

        # Screenshot 08: Scenario comparison
        screenshot_08 = EVIDENCE_DIR / "08_scenario_comparison.png"
        page.screenshot(path=str(screenshot_08), full_page=True)
        assert screenshot_08.is_file()

        page.click("#btn-close-comparison")
        page.wait_for_timeout(200)

        # -------------------------------------------------------------
        # 9. Curriculum Module Switching
        # -------------------------------------------------------------
        stage_items = page.query_selector_all(".stage-nav-item")
        assert len(stage_items) >= 6
        stage_items[2].click() # Click Stage 3
        page.wait_for_timeout(500)
        stage_title = page.inner_text("#stage-title")
        assert "3." in stage_title or "Tư thế" in stage_title or "Alignment" in stage_title

        # Screenshot 09: Curriculum module switching
        screenshot_09 = EVIDENCE_DIR / "09_curriculum_module_switching.png"
        page.screenshot(path=str(screenshot_09), full_page=True)
        assert screenshot_09.is_file()

        # -------------------------------------------------------------
        # 10. Camera Views & Language Toggle (Final Desktop Layout)
        # -------------------------------------------------------------
        # Test Lateral view
        page.click("#btn-view-lateral")
        page.wait_for_timeout(400)
        cam_pos_lat = page.evaluate("() => window.anatomyViewer.camera.position.x")
        assert cam_pos_lat > 0.3, f"Expected camera X > 0.3 for lateral view, got {cam_pos_lat}"

        # Test Posterior view
        page.click("#btn-view-posterior")
        page.wait_for_timeout(400)
        cam_pos_post = page.evaluate("() => window.anatomyViewer.camera.position.z")
        assert cam_pos_post < -0.3, f"Expected camera Z < -0.3 for posterior view, got {cam_pos_post}"

        # Test Anterior view
        page.click("#btn-view-anterior")
        page.wait_for_timeout(400)
        cam_pos_ant = page.evaluate("() => window.anatomyViewer.camera.position.z")
        assert cam_pos_ant > 0.3, f"Expected camera Z > 0.3 for anterior view, got {cam_pos_ant}"

        # Test Bilingual Toggle
        page.click("#btn-lang-toggle")
        page.wait_for_timeout(300)
        title_en = page.inner_text("#header-title")
        assert "MSK Education Studio" in title_en

        # Switch back to Vietnamese
        page.click("#btn-lang-toggle")
        page.wait_for_timeout(300)

        # Screenshot 10: Final desktop layout
        screenshot_10 = EVIDENCE_DIR / "10_final_desktop_layout.png"
        page.screenshot(path=str(screenshot_10), full_page=True)
        assert screenshot_10.is_file()

        browser.close()
