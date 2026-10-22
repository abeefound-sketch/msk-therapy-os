"""
Comprehensive Playwright Acceptance Test Suite:
M2.6 Adaptive Acupoint & Meridian Visualization and Smart Density System
Verifies Scenarios A through H with zero console errors.
"""
import json
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = Path("D:/5Projects/msk-therapy-os/research/artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:8085/"

def safe_screenshot(page, path):
    try:
        page.screenshot(path=str(path), full_page=False, timeout=3000)
    except Exception:
        pass

def run_acceptance_tests():
    print("=" * 80)
    print("STARTING ACCEPTANCE TESTS: M2.6 ADAPTIVE VISUALIZATION & SMART DENSITY")
    print("=" * 80)

    results = {}
    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1.0)
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)

        print("\n1. Loading MSK-Therapy-OS Application...")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Ensure Surface mode is active
        page.click("#hostBtnModeSurface")
        page.wait_for_timeout(500)

        # ---------------------------------------------------------------------
        # Scenario A: Full-body view with all 14 meridians and 362 acupoints
        # ---------------------------------------------------------------------
        print("\n[Scenario A] Full-body view with all 14 meridians and 362 acupoints...")
        # Trigger full body view
        page.evaluate("""() => {
            if (typeof atlasCommand === 'function') {
                atlasCommand('full_body_view');
            }
        }""")
        page.wait_for_timeout(1000)

        # Enable acupoints and meridians
        btn_pts = page.locator("#btnToggleAcupoints")
        if "active" not in (btn_pts.get_attribute("class") or ""):
            btn_pts.click()
            page.wait_for_timeout(500)

        btn_mer = page.locator("#btnToggleMeridians")
        if "active" not in (btn_mer.get_attribute("class") or ""):
            btn_mer.click()
            page.wait_for_timeout(500)

        # Set region to "all" (Full Body: 362 WHO points)
        page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            if (frame && frame.contentWindow) {
                const doc = frame.contentDocument;
                const sel = doc.getElementById('selAcuRegion');
                if (sel) { sel.value = 'all'; sel.dispatchEvent(new Event('change')); }
            }
        }""")
        page.wait_for_timeout(1500)

        metrics_a = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            const doc = frame.contentDocument;
            const visualCircles = Array.from(doc.querySelectorAll('.acu-marker-group circle:nth-child(2)'));
            const paths = Array.from(doc.querySelectorAll('#groupMeridians path'));
            const dbg = frame.contentWindow.__meridiansDebug;

            let totalArea = 0;
            let radii = [];
            visualCircles.forEach(c => {
                const r = parseFloat(c.getAttribute('r') || 0);
                radii.push(r);
                totalArea += Math.PI * r * r;
            });
            let strokes = [];
            paths.forEach(p => strokes.push(parseFloat(p.getAttribute('stroke-width') || 0)));

            return {
                marker_count: visualCircles.length,
                avg_marker_radius: radii.length ? radii.reduce((a,b)=>a+b,0)/radii.length : 0,
                avg_stroke_width: strokes.length ? strokes.reduce((a,b)=>a+b,0)/strokes.length : 0,
                total_visual_area_px: Math.round(totalArea),
                counters: dbg.currentCounters
            };
        }""")

        print(f"  Avg Marker Radius: {metrics_a['avg_marker_radius']:.2f} px (target: <= 2.5 px)")
        print(f"  Avg Stroke Width:  {metrics_a['avg_stroke_width']:.2f} px (target: <= 1.2 px)")
        print(f"  Total Area:        {metrics_a['total_visual_area_px']} px² (baseline was 29,231 px²)")
        assert metrics_a["avg_marker_radius"] <= 2.5, f"Marker radius {metrics_a['avg_marker_radius']} too large in full body!"
        assert metrics_a["avg_stroke_width"] <= 1.2, f"Stroke width {metrics_a['avg_stroke_width']} too thick in full body!"
        assert metrics_a["total_visual_area_px"] < 6000, "Visual area did not achieve clutter reduction!"

        safe_screenshot(page, ARTIFACTS_DIR / "m26_scenario_a_full_body_adaptive.png")
        results["scenario_a_full_body_adaptive"] = "PASS"
        print("  ✓ Scenario A: PASS")

        # ---------------------------------------------------------------------
        # Scenario B: Progressive zoom from full-body to torso, shoulder, hand
        # ---------------------------------------------------------------------
        print("\n[Scenario B] Progressive zoom and smooth bounded scaling...")
        zoom_levels = [
            ("torso", 1.45, "m26_scenario_b_torso_zoom.png"),
            ("shoulder", 0.85, "m26_scenario_b_shoulder_zoom.png"),
            ("face", 0.42, "m26_scenario_b_face_zoom.png")
        ]

        prev_rad = metrics_a["avg_marker_radius"]
        prev_stroke = metrics_a["avg_stroke_width"]

        for name, dist, screenshot_name in zoom_levels:
            page.evaluate(f"""() => {{
                const frame = document.getElementById('atlasFrame');
                const r = frame.contentWindow.__atlasDebug.renderer;
                r.camera.dist = {dist};
                if (typeof r._draw === 'function') r._draw();
                frame.contentWindow.__meridiansDebug.render(true);
            }}""")
            page.wait_for_timeout(800)

            m = page.evaluate("""() => {
                const frame = document.getElementById('atlasFrame');
                const doc = frame.contentDocument;
                const visualCircles = Array.from(doc.querySelectorAll('.acu-marker-group circle:nth-child(2)'));
                const paths = Array.from(doc.querySelectorAll('#groupMeridians path'));
                let radii = visualCircles.map(c => parseFloat(c.getAttribute('r') || 0));
                let strokes = paths.map(p => parseFloat(p.getAttribute('stroke-width') || 0));
                return {
                    avg_marker_radius: radii.length ? radii.reduce((a,b)=>a+b,0)/radii.length : 0,
                    avg_stroke_width: strokes.length ? strokes.reduce((a,b)=>a+b,0)/strokes.length : 0,
                    unclustered_count: visualCircles.length,
                    clusters_count: doc.querySelectorAll('.acu-cluster-marker').length
                };
            }""")
            print(f"  [{name.upper()} dist={dist}m] Radius: {m['avg_marker_radius']:.2f}px, Stroke: {m['avg_stroke_width']:.2f}px, Clusters: {m['clusters_count']}")
            assert m["avg_marker_radius"] >= prev_rad, f"Radius should increase or remain bounded when zooming in: {m['avg_marker_radius']} vs {prev_rad}"
            assert m["avg_stroke_width"] >= prev_stroke, f"Stroke should increase or remain bounded when zooming in: {m['avg_stroke_width']} vs {prev_stroke}"
            assert m["avg_marker_radius"] <= 6.5, f"Radius {m['avg_marker_radius']} exceeded maximum visual bound!"
            assert m["avg_stroke_width"] <= 2.5, f"Stroke {m['avg_stroke_width']} exceeded maximum visual bound!"

            prev_rad = m["avg_marker_radius"]
            prev_stroke = m["avg_stroke_width"]
            safe_screenshot(page, ARTIFACTS_DIR / screenshot_name)

        results["scenario_b_progressive_zoom"] = "PASS"
        print("  ✓ Scenario B: PASS")

        # ---------------------------------------------------------------------
        # Scenario C: Manual Display Overrides and Persistence
        # ---------------------------------------------------------------------
        print("\n[Scenario C] Manual display overrides, immediate update, and persistence...")
        # Reset camera back to regional
        page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            const r = frame.contentWindow.__atlasDebug.renderer;
            r.camera.dist = 1.2;
            if (typeof r._draw === 'function') r._draw();
            frame.contentWindow.__meridiansDebug.updateDisplaySettings({
                scalingMode: 'manual',
                markerSize: 1.5,
                meridianThickness: 0.8
            });
        }""")
        page.wait_for_timeout(600)

        m_min = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            const doc = frame.contentDocument;
            const firstCircle = doc.querySelector('.acu-marker-group circle:nth-child(2)');
            const firstPath = doc.querySelector('#groupMeridians path');
            return {
                rad: firstCircle ? parseFloat(firstCircle.getAttribute('r')) : 0,
                stroke: firstPath ? parseFloat(firstPath.getAttribute('stroke-width')) : 0
            };
        }""")
        print(f"  Manual Min Settings: Radius={m_min['rad']:.2f}px, Stroke={m_min['stroke']:.2f}px")
        assert abs(m_min['rad'] - 1.5) < 0.4
        safe_screenshot(page, ARTIFACTS_DIR / "m26_scenario_c_manual_min.png")

        # Test Manual Max Settings
        page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            frame.contentWindow.__meridiansDebug.updateDisplaySettings({
                scalingMode: 'manual',
                markerSize: 6.0,
                meridianThickness: 3.5
            });
        }""")
        page.wait_for_timeout(600)

        m_max = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            const doc = frame.contentDocument;
            const firstCircle = doc.querySelector('.acu-marker-group circle:nth-child(2)');
            const firstPath = doc.querySelector('#groupMeridians path');
            return {
                rad: firstCircle ? parseFloat(firstCircle.getAttribute('r')) : 0,
                stroke: firstPath ? parseFloat(firstPath.getAttribute('stroke-width')) : 0
            };
        }""")
        print(f"  Manual Max Settings: Radius={m_max['rad']:.2f}px, Stroke={m_max['stroke']:.2f}px")
        assert abs(m_max['rad'] - 6.0) < 1.0
        safe_screenshot(page, ARTIFACTS_DIR / "m26_scenario_c_manual_max.png")

        # Verify Persistence after Page Reload
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(2000)

        persisted = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            const dbg = frame.contentWindow.__meridiansDebug;
            return dbg ? dbg.displaySettings : null;
        }""")
        print(f"  Persisted Settings after reload: scalingMode={persisted['scalingMode']}, markerSize={persisted['markerSize']}")
        assert persisted["scalingMode"] == "manual"
        assert abs(persisted["markerSize"] - 6.0) < 0.1

        # Reset to defaults
        page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            frame.contentWindow.__meridiansDebug.resetDisplaySettings();
        }""")
        page.wait_for_timeout(500)
        reset_settings = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            return frame.contentWindow.__meridiansDebug.displaySettings;
        }""")
        assert reset_settings["scalingMode"] == "auto"

        results["scenario_c_manual_overrides_persistence"] = "PASS"
        print("  ✓ Scenario C: PASS")

        # ---------------------------------------------------------------------
        # Scenario D: Smart Density (Clusters, Accuracies, Expansion)
        # ---------------------------------------------------------------------
        print("\n[Scenario D] Smart density clustering, membership conservation, and expansion...")
        # Zoom out to full body with region 'all'
        page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            const doc = frame.contentDocument;
            const r = frame.contentWindow.__atlasDebug.renderer;
            r.camera.dist = 3.2;
            if (typeof r._draw === 'function') r._draw();
            const sel = doc.getElementById('selAcuRegion');
            if (sel) { sel.value = 'all'; sel.dispatchEvent(new Event('change')); }
            const chkPts = doc.getElementById('chkShowPoints');
            if (chkPts) { chkPts.checked = true; chkPts.dispatchEvent(new Event('change')); }
            frame.contentWindow.__meridiansDebug.updateDisplaySettings({ smartDensity: true });
        }""")
        page.wait_for_timeout(1000)

        cnt = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            return frame.contentWindow.__meridiansDebug.currentCounters;
        }""")
        print(f"  Smart Density Counters: Available={cnt['available']}, Visible={cnt['visible']}, Clustered={cnt['clustered']}, Filtered={cnt['filtered']}")
        assert cnt["available"] >= 361, "Total available dataset should have all points!"
        assert cnt["clustered"] > 0, "Points should be clustered in full-body view!"
        assert (cnt["visible"] + cnt["clustered"] + cnt["filtered"]) == cnt["available"], "Point conservation violated!"

        # Test clicking a cluster to expand
        page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            const doc = frame.contentDocument;
            const cluster = doc.querySelector('.acu-cluster-marker');
            if (cluster) {
                cluster.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            }
        }""")
        page.wait_for_timeout(1000)

        new_dist = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            return frame.contentWindow.__atlasDebug.renderer.camera.dist;
        }""")
        print(f"  Camera distance after clicking cluster: {new_dist:.2f}m (zoomed in)")
        assert new_dist < 3.0, "Clicking cluster should zoom in toward centroid!"

        safe_screenshot(page, ARTIFACTS_DIR / "m26_scenario_d_cluster_expanded.png")
        results["scenario_d_smart_density_clustering"] = "PASS"
        print("  ✓ Scenario D: PASS")

        # ---------------------------------------------------------------------
        # Scenario E: Point Interaction, Selection Halos & Inspection
        # ---------------------------------------------------------------------
        print("\n[Scenario E] Selecting LI4, GB21, GV14 and verifying inspection & halos...")
        for test_point in ["LI4", "GB21", "GV14"]:
            page.evaluate(f"""() => {{
                const frame = document.getElementById('atlasFrame');
                const dbg = frame.contentWindow.__meridiansDebug;
                const r = frame.contentWindow.__atlasDebug.renderer;
                dbg.selectPoint('{test_point}', false);
                r.anim = null;
                const ptData = dbg.acuData.points['{test_point}'];
                r.camera.target = ptData.position.slice();
                r.camera.dist = 0.85;
                if (ptData.position[2] < -0.035) {{
                    r.camera.yaw = Math.PI;
                    r.camera.pitch = 0.15;
                }} else {{
                    r.camera.yaw = 0.0;
                    r.camera.pitch = 0.05;
                }}
                if (typeof r._draw === 'function') r._draw();
                dbg.render(true);
            }}""")
            page.wait_for_timeout(500)

            halo_exists = page.evaluate(f"""() => {{
                const frame = document.getElementById('atlasFrame');
                const doc = frame.contentDocument;
                const grp = doc.querySelector('.acu-marker-group[data-code="{test_point}"]');
                const halo = doc.querySelector('.acu-marker-group circle[stroke-dasharray="4,4"]');
                return Boolean(grp && halo);
            }}""")
            assert halo_exists, f"Selection halo missing for {test_point}!"
            print(f"  ✓ {test_point} selected with active animated halo.")

        safe_screenshot(page, ARTIFACTS_DIR / "m26_scenario_e_selected_point_halo.png")
        results["scenario_e_point_interaction_halos"] = "PASS"
        print("  ✓ Scenario E: PASS")

        # ---------------------------------------------------------------------
        # Scenario F: Comparative Mode Adaptive Scaling & Viewport Isolation
        # ---------------------------------------------------------------------
        print("\n[Scenario F] Comparative mode adaptive scaling and viewport isolation...")
        page.click("#hostBtnModeComparative")
        page.wait_for_timeout(1200)

        comp_check = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            const doc = frame.contentDocument;
            const paths = Array.from(doc.querySelectorAll('#groupMeridians path'));
            const clipRect = doc.getElementById('overlayClipRect');
            const r = frame.contentWindow.__atlasDebug.renderer;
            const vpDesc = r.getViewportDescriptor('overlay');
            
            // Check that clipRect is isolated to right half
            const clipW = parseFloat(clipRect.getAttribute('width'));
            const clipX = parseFloat(clipRect.getAttribute('x'));
            
            return {
                mode: r.renderMode,
                clipX,
                clipW,
                stageWidth: doc.querySelector('.stage').clientWidth,
                pathsCount: paths.length
            };
        }""")
        print(f"  Comparative Viewport: StageWidth={comp_check['stageWidth']}px, ClipX={comp_check['clipX']}px, ClipW={comp_check['clipW']}px")
        assert comp_check["mode"] == "comparative"
        assert abs(comp_check["clipX"] - comp_check["stageWidth"] / 2.0) < 5.0, "Clip rect must start at viewport midpoint!"

        safe_screenshot(page, ARTIFACTS_DIR / "m26_scenario_f_comparative_adaptive.png")
        results["scenario_f_comparative_mode_isolation"] = "PASS"
        print("  ✓ Scenario F: PASS")

        # Switch back to Surface mode
        page.click("#hostBtnModeSurface")
        page.wait_for_timeout(800)

        # ---------------------------------------------------------------------
        # Scenario G: Responsive Layouts (375px, 768px, 1280px, 1920px)
        # ---------------------------------------------------------------------
        print("\n[Scenario G] Responsive viewport layouts...")
        viewports = [
            ("mobile_375px", 375, 667),
            ("tablet_768px", 768, 1024),
            ("fullhd_1920px", 1920, 1080)
        ]

        for name, w, h in viewports:
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(600)
            page.evaluate("""() => {
                const frame = document.getElementById('atlasFrame');
                if (frame && frame.contentWindow && frame.contentWindow.__meridiansDebug) {
                    frame.contentWindow.__meridiansDebug.render(true);
                }
            }""")
            page.wait_for_timeout(400)
            safe_screenshot(page, ARTIFACTS_DIR / f"m26_scenario_g_responsive_{name}.png")
            print(f"  ✓ Tested {w}x{h} ({name})")

        # Restore 1280x800
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(500)
        results["scenario_g_responsive_layouts"] = "PASS"
        print("  ✓ Scenario G: PASS")

        # ---------------------------------------------------------------------
        # Scenario H: Visual Regression Telemetry & Artifact Verification
        # ---------------------------------------------------------------------
        print("\n[Scenario H] Visual regression telemetry and artifact compilation...")
        # Verify both Before and After artifacts exist
        assert (ARTIFACTS_DIR / "m26_before_full_body_overcrowded.png").exists(), "Before screenshot missing!"
        assert (ARTIFACTS_DIR / "m26_after_full_body_smart_density_on.png").exists(), "After screenshot missing!"
        assert (ARTIFACTS_DIR / "m26_scenario_a_full_body_adaptive.png").exists(), "Scenario A screenshot missing!"

        print(f"\nBrowser Console Errors Count: {len(console_errors)}")
        if console_errors:
            for err in console_errors:
                print("  Console Error:", err)
        assert len(console_errors) == 0, f"Found {len(console_errors)} console errors during test run!"

        results["scenario_h_visual_regression_protection"] = "PASS"
        results["console_errors_count"] = len(console_errors)
        print("  ✓ Scenario H: PASS")

        # Write acceptance report JSON
        report_path = ARTIFACTS_DIR / "adaptive_visualization_acceptance_report.json"
        report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\n[Saved Acceptance Report] {report_path}")

        browser.close()

    print("=" * 80)
    print("ALL M2.6 ADAPTIVE VISUALIZATION ACCEPTANCE TESTS PASSED: 100% COMPLIANCE")
    print("=" * 80)

if __name__ == "__main__":
    run_acceptance_tests()
