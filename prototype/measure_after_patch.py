"""
Measure visual metrics AFTER M2.6 Adaptive Visualization & Smart Density patch.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = Path("D:/5Projects/msk-therapy-os/2data/artifacts")
BASE_URL = "http://127.0.0.1:8085/"

def measure_after():
    print("=" * 80)
    print("MEASURING M2.6 ADAPTIVE VISUALIZATION & SMART DENSITY (AFTER PATCH)")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1.0)
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)

        print(f"Loading {BASE_URL}...")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Ensure Surface mode is active and full body view
        page.click("#hostBtnModeSurface")
        page.wait_for_timeout(500)

        page.evaluate("""() => {
            if (typeof atlasCommand === 'function') {
                atlasCommand('full_body_view');
            }
        }""")
        page.wait_for_timeout(1000)

        # Enable both Acupoints and Meridians
        btn_pts = page.locator("#btnToggleAcupoints")
        if "active" not in (btn_pts.get_attribute("class") or ""):
            btn_pts.click()
            page.wait_for_timeout(500)

        btn_mer = page.locator("#btnToggleMeridians")
        if "active" not in (btn_mer.get_attribute("class") or ""):
            btn_mer.click()
            page.wait_for_timeout(500)

        # Set region to "all" (Full Body: all points)
        page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            if (frame && frame.contentWindow) {
                const doc = frame.contentDocument;
                const sel = doc.getElementById('selAcuRegion');
                if (sel) {
                    sel.value = 'all';
                    sel.dispatchEvent(new Event('change'));
                }
            }
        }""")
        page.wait_for_timeout(1500)

        # Measure markers and lines inside iframe with Smart Density ON
        metrics_smart_on = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            if (!frame || !frame.contentWindow) return null;
            const doc = frame.contentDocument;
            const markers = Array.from(doc.querySelectorAll('.acu-marker'));
            const clusters = Array.from(doc.querySelectorAll('.acu-cluster-marker'));
            const visualCircles = Array.from(doc.querySelectorAll('.acu-marker-group circle:nth-child(2)'));
            const paths = Array.from(doc.querySelectorAll('#groupMeridians path'));
            const r = frame.contentWindow.__atlasDebug ? frame.contentWindow.__atlasDebug.renderer : null;
            const dbg = frame.contentWindow.__meridiansDebug;
            
            let totalVisualArea = 0;
            let radii = [];
            visualCircles.forEach(c => {
                const rad = parseFloat(c.getAttribute('r') || 0);
                radii.push(rad);
                totalVisualArea += Math.PI * rad * rad;
            });
            clusters.forEach(cl => {
                const cCircle = cl.querySelector('circle:nth-child(2)');
                if (cCircle) {
                    const rad = parseFloat(cCircle.getAttribute('r') || 0);
                    totalVisualArea += Math.PI * rad * rad;
                }
            });
            
            let strokeWidths = [];
            paths.forEach(p => {
                const sw = parseFloat(p.getAttribute('stroke-width') || 0);
                strokeWidths.push(sw);
            });

            return {
                camera_dist: r ? r.camera.dist : null,
                camera_fov: r ? r.camera.fov : null,
                viewing_condition: dbg && dbg.displaySettings ? 'full_body' : 'unknown',
                smart_density: dbg ? dbg.displaySettings.smartDensity : null,
                unclustered_markers_count: visualCircles.length,
                clusters_count: clusters.length,
                total_visible_items: visualCircles.length + clusters.length,
                total_visual_area_px: Math.round(totalVisualArea),
                avg_marker_radius: radii.length ? (radii.reduce((a, b) => a + b, 0) / radii.length).toFixed(2) : 0,
                min_marker_radius: radii.length ? Math.min(...radii) : 0,
                max_marker_radius: radii.length ? Math.max(...radii) : 0,
                path_count: paths.length,
                avg_stroke_width: strokeWidths.length ? (strokeWidths.reduce((a, b) => a + b, 0) / strokeWidths.length).toFixed(2) : 0,
                counters: dbg ? dbg.currentCounters : null
            };
        }""")

        print("\n=== METRICS WITH SMART DENSITY ON (DEFAULT) ===")
        for k, v in metrics_smart_on.items():
            print(f"  {k}: {v}")

        # Capture After screenshot with Smart Density ON
        page.screenshot(path=str(ARTIFACTS_DIR / "m26_after_full_body_smart_density_on.png"), timeout=5000)

        # Now test turning Smart Density OFF to measure pure Auto-Scaling
        page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            if (frame && frame.contentWindow && frame.contentWindow.__meridiansDebug) {
                frame.contentWindow.__meridiansDebug.updateDisplaySettings({ smartDensity: false });
            }
        }""")
        page.wait_for_timeout(1000)

        metrics_smart_off = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            if (!frame || !frame.contentWindow) return null;
            const doc = frame.contentDocument;
            const visualCircles = Array.from(doc.querySelectorAll('.acu-marker-group circle:nth-child(2)'));
            const paths = Array.from(doc.querySelectorAll('#groupMeridians path'));
            const dbg = frame.contentWindow.__meridiansDebug;

            let totalVisualArea = 0;
            let radii = [];
            visualCircles.forEach(c => {
                const rad = parseFloat(c.getAttribute('r') || 0);
                radii.push(rad);
                totalVisualArea += Math.PI * rad * rad;
            });
            let strokeWidths = [];
            paths.forEach(p => {
                const sw = parseFloat(p.getAttribute('stroke-width') || 0);
                strokeWidths.push(sw);
            });

            return {
                smart_density: false,
                unclustered_markers_count: visualCircles.length,
                total_visual_area_px: Math.round(totalVisualArea),
                avg_marker_radius: radii.length ? (radii.reduce((a, b) => a + b, 0) / radii.length).toFixed(2) : 0,
                avg_stroke_width: strokeWidths.length ? (strokeWidths.reduce((a, b) => a + b, 0) / strokeWidths.length).toFixed(2) : 0,
                counters: dbg ? dbg.currentCounters : null
            };
        }""")

        print("\n=== METRICS WITH SMART DENSITY OFF (PURE AUTO-SCALING) ===")
        for k, v in metrics_smart_off.items():
            print(f"  {k}: {v}")

        page.screenshot(path=str(ARTIFACTS_DIR / "m26_after_full_body_smart_density_off.png"), timeout=5000)

        print(f"\nConsole errors logged during test: {len(console_errors)}")
        if console_errors:
            for ce in console_errors:
                print("  ", ce)
        assert len(console_errors) == 0

        browser.close()
        print("\n✓ Measurement completed successfully.")

if __name__ == "__main__":
    measure_after()
