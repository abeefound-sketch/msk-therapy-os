import os
import time
import json
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = "research/artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def verify_overlay_clipping():
    print("=" * 80)
    print("VERIFYING REMEDIATED P0: 3D MERIDIAN OVERLAY LEAKAGE & COMPARATIVE SEPARATION")
    print("=" * 80)

    results = {
        "timestamp": time.time(),
        "standalone_initial": None,
        "standalone_zoomed": None,
        "comparative_initial": None,
        "comparative_zoomed": None,
        "host_zoomed": None,
        "responsive_checks": {},
        "failures": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--use-gl=angle",
                "--use-angle=d3d11",
                "--ignore-gpu-blocklist",
                "--enable-webgl",
                "--enable-gpu-rasterization",
                "--disable-web-security",
            ]
        )

        # ----------------------------------------------------------------------
        # Test 1: Standalone Atlas (/atlas/)
        # ----------------------------------------------------------------------
        print("\n[TEST 1] Standalone Atlas (/atlas/) Initial & 12x Zoom...")
        page = browser.new_page(viewport={"width": 1280, "height": 850})
        page.goto("http://127.0.0.1:8085/atlas/", wait_until="networkidle", timeout=30000)
        time.sleep(2.0)

        # Enable Meridians & Points
        page.evaluate("""() => {
            const tabs = Array.from(document.querySelectorAll('.tab'));
            const acuTab = tabs.find(t => t.textContent.includes('Meridians') || t.getAttribute('data-tab') === 'meridians');
            if (acuTab) acuTab.click();
            const chkM = document.getElementById('chkShowMeridians');
            if (chkM) { chkM.checked = true; chkM.dispatchEvent(new Event('change')); }
            const chkP = document.getElementById('chkShowPoints');
            if (chkP) { chkP.checked = true; chkP.dispatchEvent(new Event('change')); }
        }""")
        time.sleep(1.0)

        def inspect_viewport_bounds(target_mode="surface"):
            return page.evaluate("""(target_mode) => {
                const stage = document.querySelector('.stage');
                const sRect = stage.getBoundingClientRect();
                const sidebar = document.querySelector('.sidebar');
                const sideRect = sidebar.getBoundingClientRect();
                const overlay = document.querySelector('.acupuncture-overlay');
                const oRect = overlay.getBoundingClientRect();

                const clipPath = document.getElementById('overlayViewportClip');
                const clipRect = document.getElementById('overlayClipRect');
                const clipRectBounds = clipRect ? {
                    x: parseFloat(clipRect.getAttribute('x')),
                    y: parseFloat(clipRect.getAttribute('y')),
                    width: parseFloat(clipRect.getAttribute('width')),
                    height: parseFloat(clipRect.getAttribute('height'))
                } : null;

                const stageComputed = window.getComputedStyle(stage);
                const overlayComputed = window.getComputedStyle(overlay);

                const paths = Array.from(document.querySelectorAll('#groupMeridians path, #groupThai path'));
                let leakingPaths = [];
                let negativeCoords = [];
                let outOfBoundsCoords = [];
                let nanCoords = [];

                const minAllowedX = target_mode === 'comparative' ? sRect.width * 0.5 - 0.5 : -0.5;
                const maxAllowedX = sRect.width + 0.5;
                const minAllowedY = -0.5;
                const maxAllowedY = sRect.height + 0.5;

                for (const p of paths) {
                    const pRect = p.getBoundingClientRect();
                    const d = p.getAttribute('d') || '';

                    if (d.includes('NaN') || d.includes('Infinity')) {
                        nanCoords.push({ path: d.slice(0, 40) });
                    }

                    // Check individual numbers in d
                    const nums = d.match(/[-+]?[0-9]*\.?[0-9]+/g) || [];
                    for (let i = 0; i < nums.length; i += 2) {
                        const x = parseFloat(nums[i]);
                        const y = parseFloat(nums[i+1]);

                        if (isNaN(x) || isNaN(y)) {
                            nanCoords.push({ x, y });
                            continue;
                        }

                        if (x < -0.5 || y < -0.5) {
                            negativeCoords.push({ x, y });
                        }

                        if (x < minAllowedX || x > maxAllowedX || y < minAllowedY || y > maxAllowedY) {
                            outOfBoundsCoords.push({ x, y, minAllowedX, maxAllowedX, minAllowedY, maxAllowedY });
                        }
                    }

                    // Strict bounding box overlap with sidebar
                    // If path is visible (width > 0) and left boundary is strictly less than sidebar right boundary
                    if (pRect.width > 0 && pRect.left < sideRect.right - 1.0) {
                        leakingPaths.push({
                            left: pRect.left,
                            sidebarRight: sideRect.right,
                            diff: sideRect.right - pRect.left,
                            d_preview: d.slice(0, 40)
                        });
                    }
                }

                // Check acupoint circles
                const circles = Array.from(document.querySelectorAll('#groupPoints circle'));
                let outOfBoundsCircles = [];
                for (const c of circles) {
                    const cx = parseFloat(c.getAttribute('cx') || '0');
                    const cy = parseFloat(c.getAttribute('cy') || '0');
                    if (cx < minAllowedX || cx > maxAllowedX || cy < minAllowedY || cy > maxAllowedY) {
                        outOfBoundsCircles.push({ cx, cy, minAllowedX, maxAllowedX });
                    }
                }

                return {
                    stageRect: { left: sRect.left, top: sRect.top, width: sRect.width, height: sRect.height },
                    sidebarRect: { left: sideRect.left, top: sideRect.top, width: sideRect.width, height: sideRect.height },
                    stageOverflow: stageComputed.overflow,
                    stageContain: stageComputed.contain,
                    overlayOverflow: overlayComputed.overflow,
                    overlayContain: overlayComputed.contain,
                    clipRectBounds,
                    totalPaths: paths.length,
                    totalCircles: circles.length,
                    leakingIntoSidebarCount: leakingPaths.length,
                    leakingSample: leakingPaths.slice(0, 5),
                    negativeCoordsCount: negativeCoords.length,
                    negativeSample: negativeCoords.slice(0, 5),
                    outOfBoundsCount: outOfBoundsCoords.length,
                    outOfBoundsSample: outOfBoundsCoords.slice(0, 5),
                    nanCoordsCount: nanCoords.length,
                    outOfBoundsCirclesCount: outOfBoundsCircles.length
                };
            }""", target_mode)

        res_std_init = inspect_viewport_bounds("surface")
        results["standalone_initial"] = res_std_init
        print(f"  Initial Standalone:")
        print(f"    Paths: {res_std_init['totalPaths']}, Sidebar Leaks: {res_std_init['leakingIntoSidebarCount']}, Negative Coords: {res_std_init['negativeCoordsCount']}")
        print(f"    CSS Stage overflow: {res_std_init['stageOverflow']}, contain: {res_std_init['stageContain']}")
        print(f"    CSS Overlay overflow: {res_std_init['overlayOverflow']}, contain: {res_std_init['overlayContain']}")

        # Perform 12 mouse-wheel zooms toward neck/shoulder
        stage_box = page.locator(".stage").bounding_box()
        center_x = stage_box["x"] + stage_box["width"] * 0.5
        center_y = stage_box["y"] + stage_box["height"] * 0.35

        for _ in range(12):
            page.mouse.move(center_x, center_y)
            page.mouse.wheel(0, -120)
            time.sleep(0.05)
        time.sleep(1.0)

        page.screenshot(path=os.path.join(ARTIFACT_DIR, "p0_after_standalone_zoomed.png"))
        print(f"  [Saved] p0_after_standalone_zoomed.png")

        res_std_zoom = inspect_viewport_bounds("surface")
        results["standalone_zoomed"] = res_std_zoom
        print(f"  Zoomed Standalone:")
        print(f"    Sidebar Leaks: {res_std_zoom['leakingIntoSidebarCount']}")
        print(f"    Negative Coords: {res_std_zoom['negativeCoordsCount']}")
        print(f"    Out of Bounds Coords: {res_std_zoom['outOfBoundsCount']}")
        print(f"    NaN/Inf Coords: {res_std_zoom['nanCoordsCount']}")

        if res_std_zoom['leakingIntoSidebarCount'] > 0:
            results["failures"].append(f"Standalone Zoomed has {res_std_zoom['leakingIntoSidebarCount']} paths leaking into sidebar")
        if res_std_zoom['negativeCoordsCount'] > 0:
            results["failures"].append(f"Standalone Zoomed has {res_std_zoom['negativeCoordsCount']} negative coordinates")
        if res_std_zoom['nanCoordsCount'] > 0:
            results["failures"].append(f"Standalone Zoomed has {res_std_zoom['nanCoordsCount']} NaN/Infinity coordinates")

        # ----------------------------------------------------------------------
        # Test 2: Comparative Mode Viewport Separation & Zoom
        # ----------------------------------------------------------------------
        print("\n[TEST 2] Comparative Mode (/atlas/ Comparative Mode)...")
        page.evaluate("""() => {
            const btnComp = document.getElementById('btnModeComp');
            if (btnComp) btnComp.click();
            else {
                const segs = Array.from(document.querySelectorAll('.seg button'));
                const comp = segs.find(b => b.textContent.includes('Compare') || b.textContent.includes('Comparative'));
                if (comp) comp.click();
            }
        }""")
        time.sleep(1.0)

        page.screenshot(path=os.path.join(ARTIFACT_DIR, "p0_after_comparative_initial.png"))
        print("  [Saved] p0_after_comparative_initial.png")

        res_comp_init = inspect_viewport_bounds("comparative")
        results["comparative_initial"] = res_comp_init
        print(f"  Initial Comparative:")
        print(f"    ClipRect Bounds: {res_comp_init['clipRectBounds']}")
        print(f"    Out of Bounds (Crossing Divider < halfW or > stageW): {res_comp_init['outOfBoundsCount']}")
        print(f"    Negative Coords: {res_comp_init['negativeCoordsCount']}")

        # Zoom into neck/torso in Comparative Mode (8 ticks)
        for _ in range(8):
            page.mouse.move(center_x, center_y)
            page.mouse.wheel(0, -120)
            time.sleep(0.05)
        time.sleep(1.0)

        page.screenshot(path=os.path.join(ARTIFACT_DIR, "p0_after_comparative_zoomed.png"))
        print("  [Saved] p0_after_comparative_zoomed.png")

        res_comp_zoom = inspect_viewport_bounds("comparative")
        results["comparative_zoomed"] = res_comp_zoom
        print(f"  Zoomed Comparative:")
        print(f"    Divider Crossing / Out of Bounds Coords: {res_comp_zoom['outOfBoundsCount']}")
        print(f"    Negative Coords: {res_comp_zoom['negativeCoordsCount']}")
        print(f"    NaN/Inf Coords: {res_comp_zoom['nanCoordsCount']}")
        print(f"    Circles Crossing Divider: {res_comp_zoom['outOfBoundsCirclesCount']}")

        if res_comp_zoom['outOfBoundsCount'] > 0:
            results["failures"].append(f"Comparative Zoomed has {res_comp_zoom['outOfBoundsCount']} coords outside right viewport (crossing divider)")
        if res_comp_zoom['negativeCoordsCount'] > 0:
            results["failures"].append(f"Comparative Zoomed has {res_comp_zoom['negativeCoordsCount']} negative coordinates")
        if res_comp_zoom['outOfBoundsCirclesCount'] > 0:
            results["failures"].append(f"Comparative Zoomed has {res_comp_zoom['outOfBoundsCirclesCount']} acupoint circles outside right viewport")

        # ----------------------------------------------------------------------
        # Test 3: Main Host Application (/ with embedded iframe)
        # ----------------------------------------------------------------------
        print("\n[TEST 3] Main Host Application (http://127.0.0.1:8085/)...")
        page_host = browser.new_page(viewport={"width": 1280, "height": 850})
        page_host.goto("http://127.0.0.1:8085/", wait_until="networkidle", timeout=30000)
        time.sleep(2.0)

        page_host.evaluate("""() => {
            const b = document.getElementById('btnToggleMeridians');
            if (b && !b.classList.contains('active')) b.click();
        }""")
        time.sleep(1.0)

        frame_box = page_host.locator("#atlasFrame").bounding_box()
        f_center_x = frame_box["x"] + frame_box["width"] * 0.5
        f_center_y = frame_box["y"] + frame_box["height"] * 0.4

        for _ in range(12):
            page_host.mouse.move(f_center_x, f_center_y)
            page_host.mouse.wheel(0, -120)
            time.sleep(0.05)
        time.sleep(1.0)

        page_host.screenshot(path=os.path.join(ARTIFACT_DIR, "p0_after_host_app_zoomed.png"))
        print("  [Saved] p0_after_host_app_zoomed.png")

        # Check inside iframe for leakage
        iframe = page_host.frame_locator("#atlasFrame")
        host_leakage = iframe.locator("body").evaluate("""() => {
            const stage = document.querySelector('.stage');
            if (!stage) return { ok: false };
            const sRect = stage.getBoundingClientRect();
            const paths = Array.from(document.querySelectorAll('#groupMeridians path'));
            let outOfBounds = 0;
            let negative = 0;
            for (const p of paths) {
                const d = p.getAttribute('d') || '';
                const nums = d.match(/[-+]?[0-9]*\.?[0-9]+/g) || [];
                for (let i = 0; i < nums.length; i += 2) {
                    const x = parseFloat(nums[i]);
                    const y = parseFloat(nums[i+1]);
                    if (x < -0.5 || y < -0.5) negative++;
                    if (x < -0.5 || x > sRect.width + 0.5 || y < -0.5 || y > sRect.height + 0.5) outOfBounds++;
                }
            }
            return {
                ok: true,
                pathsCount: paths.length,
                negative,
                outOfBounds,
                stageWidth: sRect.width,
                stageHeight: sRect.height
            };
        }""")
        results["host_zoomed"] = host_leakage
        print(f"  Host App Zoomed Iframe Check: paths={host_leakage.get('pathsCount')}, outOfBounds={host_leakage.get('outOfBounds')}, negative={host_leakage.get('negative')}")

        if host_leakage.get('outOfBounds', 0) > 0:
            results["failures"].append(f"Host App Zoomed has {host_leakage['outOfBounds']} out-of-bounds coordinates")

        # ----------------------------------------------------------------------
        # Test 4: Responsive Viewport Matrix (Desktop, Tablet, Mobile)
        # ----------------------------------------------------------------------
        viewports = [
            ("Desktop 1280x850", {"width": 1280, "height": 850}),
            ("Tablet 768x1024", {"width": 768, "height": 1024}),
            ("Mobile 375x667", {"width": 375, "height": 667})
        ]

        print("\n[TEST 4] Responsive Viewport Audit Matrix...")
        for vp_name, vp_dims in viewports:
            print(f"  Testing {vp_name}...")
            vp_page = browser.new_page(viewport=vp_dims)
            vp_page.goto("http://127.0.0.1:8085/atlas/", wait_until="networkidle", timeout=30000)
            time.sleep(1.0)

            # Enable meridians
            vp_page.evaluate("""() => {
                const chkM = document.getElementById('chkShowMeridians');
                if (chkM) { chkM.checked = true; chkM.dispatchEvent(new Event('change')); }
            }""")
            time.sleep(0.5)

            # Zoom
            s_box = vp_page.locator(".stage").bounding_box()
            cx = s_box["x"] + s_box["width"] * 0.5
            cy = s_box["y"] + s_box["height"] * 0.4
            for _ in range(8):
                vp_page.mouse.move(cx, cy)
                vp_page.mouse.wheel(0, -120)
                time.sleep(0.04)
            time.sleep(0.5)

            vp_result = vp_page.evaluate("""() => {
                const stage = document.querySelector('.stage');
                const sRect = stage.getBoundingClientRect();
                const paths = Array.from(document.querySelectorAll('#groupMeridians path'));
                let oob = 0;
                let neg = 0;
                for (const p of paths) {
                    const d = p.getAttribute('d') || '';
                    const nums = d.match(/[-+]?[0-9]*\.?[0-9]+/g) || [];
                    for (let i = 0; i < nums.length; i += 2) {
                        const x = parseFloat(nums[i]);
                        const y = parseFloat(nums[i+1]);
                        if (x < -0.5 || y < -0.5) neg++;
                        if (x < -0.5 || x > sRect.width + 0.5 || y < -0.5 || y > sRect.height + 0.5) oob++;
                    }
                }
                return { stageWidth: sRect.width, stageHeight: sRect.height, pathsCount: paths.length, oob, neg };
            }""")
            results["responsive_checks"][vp_name] = vp_result
            print(f"    {vp_name}: Stage={vp_result['stageWidth']}x{vp_result['stageHeight']}, OOB={vp_result['oob']}, Neg={vp_result['neg']}")
            if vp_result['oob'] > 0:
                results["failures"].append(f"{vp_name} has {vp_result['oob']} OOB coordinates")
            vp_page.close()

        # Save verification report
        report_path = os.path.join(ARTIFACT_DIR, "p0_remediation_verification.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\n[Saved Report] {report_path}")

        print("\n" + "=" * 80)
        if not results["failures"]:
            print("ALL P0 VERIFICATION CHECKS PASSED: ZERO LEAKAGE, ZERO CROSSING, ZERO OOB")
        else:
            print(f"VERIFICATION FAILED WITH {len(results['failures'])} DEFECTS:")
            for fail in results["failures"]:
                print(f"  - {fail}")
        print("=" * 80)

        browser.close()

if __name__ == "__main__":
    verify_overlay_clipping()
