"""
Reproduce and measure the visual overcrowding in MSK-Therapy-OS Atlas
at full-body zoom with all 14 meridians and 362 WHO acupoints active.
Captures baseline "BEFORE" visual evidence.
"""
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = Path("D:/5Projects/msk-therapy-os/2data/artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:8085/"

def reproduce():
    print("=" * 80)
    print("REPRODUCING M2.6 VISUAL OVERCROWDING DEFECT AT FULL-BODY ZOOM")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1.0)
        page = context.new_page()

        print(f"Loading {BASE_URL}...")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Ensure Surface mode is active and full body view is selected
        page.click("#hostBtnModeSurface")
        page.wait_for_timeout(500)

        # Trigger Full Body camera
        page.evaluate("""() => {
            if (typeof atlasCommand === 'function') {
                atlasCommand('full_body_view');
            }
        }""")
        page.wait_for_timeout(1000)

        # Enable both Acupoints AND Meridians on host
        btn_pts = page.locator("#btnToggleAcupoints")
        if "active" not in (btn_pts.get_attribute("class") or ""):
            btn_pts.click()
            page.wait_for_timeout(500)

        btn_mer = page.locator("#btnToggleMeridians")
        if "active" not in (btn_mer.get_attribute("class") or ""):
            btn_mer.click()
            page.wait_for_timeout(500)

        # Set region to "all" (Full Body: 362 points)
        page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            if (frame && frame.contentWindow) {
                const doc = frame.contentDocument;
                const sel = doc.getElementById('selAcuRegion');
                if (sel) {
                    sel.value = 'all';
                    sel.dispatchEvent(new Event('change'));
                }
                const chkMer = doc.getElementById('chkShowMeridians');
                if (chkMer && !chkMer.checked) {
                    chkMer.checked = true;
                    chkMer.dispatchEvent(new Event('change'));
                }
                const chkPts = doc.getElementById('chkShowPoints');
                if (chkPts && !chkPts.checked) {
                    chkPts.checked = true;
                    chkPts.dispatchEvent(new Event('change'));
                }
            }
        }""")
        page.wait_for_timeout(1500)

        # Measure markers and lines inside iframe
        metrics = page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            if (!frame || !frame.contentWindow) return null;
            const doc = frame.contentDocument;
            const markers = Array.from(doc.querySelectorAll('.acu-marker'));
            const paths = Array.from(doc.querySelectorAll('#groupMeridians path'));
            const r = frame.contentWindow.__atlasDebug ? frame.contentWindow.__atlasDebug.renderer : null;
            
            let totalMarkerArea = 0;
            let radii = [];
            markers.forEach(m => {
                const rad = parseFloat(m.getAttribute('r') || 0);
                radii.push(rad);
                totalMarkerArea += Math.PI * rad * rad;
            });
            
            let strokeWidths = [];
            paths.forEach(p => {
                const sw = parseFloat(p.getAttribute('stroke-width') || 0);
                strokeWidths.push(sw);
            });

            // Calculate bounding box coverage of markers
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            markers.forEach(m => {
                const cx = parseFloat(m.getAttribute('cx') || 0);
                const cy = parseFloat(m.getAttribute('cy') || 0);
                if (cx < minX) minX = cx;
                if (cx > maxX) maxX = cx;
                if (cy < minY) minY = cy;
                if (cy > maxY) maxY = cy;
            });

            return {
                camera_dist: r ? r.camera.dist : null,
                camera_fov: r ? r.camera.fov : null,
                marker_count: markers.length,
                total_marker_area_px: Math.round(totalMarkerArea),
                avg_marker_radius: radii.length ? (radii.reduce((a, b) => a + b, 0) / radii.length).toFixed(2) : 0,
                min_marker_radius: radii.length ? Math.min(...radii) : 0,
                max_marker_radius: radii.length ? Math.max(...radii) : 0,
                path_count: paths.length,
                avg_stroke_width: strokeWidths.length ? (strokeWidths.reduce((a, b) => a + b, 0) / strokeWidths.length).toFixed(2) : 0,
                marker_bounds: { minX, maxX, minY, maxY, width: maxX - minX, height: maxY - minY }
            };
        }""")

        print("Atlas Full-Body Overlay Metrics (BEFORE):")
        for k, v in metrics.items():
            print(f"  {k}: {v}")

        # Capture Before screenshots
        print("\nCapturing baseline BEFORE screenshots...")
        page.screenshot(path=str(ARTIFACTS_DIR / "m26_before_full_body_overcrowded.png"), timeout=5000)
        
        # Capture Standalone Atlas view
        atlas_page = context.new_page()
        atlas_page.goto("http://127.0.0.1:8085/atlas/", wait_until="networkidle", timeout=30000)
        atlas_page.wait_for_timeout(1500)
        atlas_page.evaluate("""() => {
            const doc = document;
            const sel = doc.getElementById('selAcuRegion');
            if (sel) { sel.value = 'all'; sel.dispatchEvent(new Event('change')); }
            const chkMer = doc.getElementById('chkShowMeridians');
            if (chkMer) { chkMer.checked = true; chkMer.dispatchEvent(new Event('change')); }
            const chkPts = doc.getElementById('chkShowPoints');
            if (chkPts) { chkPts.checked = true; chkPts.dispatchEvent(new Event('change')); }
            const r = window.__atlasDebug ? window.__atlasDebug.renderer : null;
            if (r) {
                r.camera.dist = 2.4;
                r.camera.target = [0, 1.0, 0];
                if (typeof r._draw === 'function') r._draw();
            }
        }""")
        atlas_page.wait_for_timeout(1000)
        atlas_page.screenshot(path=str(ARTIFACTS_DIR / "m26_before_standalone_fullbody.png"), timeout=5000)
        
        browser.close()
        print("✓ Baseline reproduction complete. Artifacts saved.")

if __name__ == "__main__":
    reproduce()
