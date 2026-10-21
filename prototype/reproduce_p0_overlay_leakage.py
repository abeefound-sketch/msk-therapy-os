import os
import time
import json
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = "research/artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def run_reproduction():
    print("=" * 80)
    print("REPRODUCING P0: 3D MERIDIAN OVERLAY LEAKAGE & COMPARATIVE VIEWPORT MISALIGNMENT")
    print("=" * 80)

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
        # Scenario 1: Standalone Atlas at /atlas/ with Aggressive Zoom
        # Check if SVG meridian paths leak outside .stage into .sidebar or .topbar
        # ----------------------------------------------------------------------
        print("\n1. Testing Standalone Atlas (/atlas/) with Zoom...")
        page = browser.new_page(viewport={"width": 1280, "height": 850})
        page.goto("http://127.0.0.1:8085/atlas/", wait_until="networkidle", timeout=30000)
        time.sleep(2.0)

        # Switch to Meridians tab in sidebar and enable Meridians
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

        # Capture initial state
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "p0_before_standalone_initial.png"))
        print("  [Saved] p0_before_standalone_initial.png")

        # Now perform repeated mouse-wheel zoom (12 ticks forward toward neck/shoulder)
        stage_elem = page.locator(".stage")
        stage_box = stage_elem.bounding_box()
        sidebar_box = page.locator(".sidebar").bounding_box()
        print(f"  Stage bounding box: {stage_box}")
        print(f"  Sidebar bounding box: {sidebar_box}")

        center_x = stage_box["x"] + stage_box["width"] * 0.5
        center_y = stage_box["y"] + stage_box["height"] * 0.35

        for _ in range(12):
            page.mouse.move(center_x, center_y)
            page.mouse.wheel(0, -120)
            time.sleep(0.05)
        time.sleep(1.0)

        page.screenshot(path=os.path.join(ARTIFACT_DIR, "p0_before_standalone_zoomed.png"))
        print("  [Saved] p0_before_standalone_zoomed.png")

        # Inspect SVG bounds vs Stage bounds vs Sidebar bounds
        standalone_leakage = page.evaluate("""() => {
            const stage = document.querySelector('.stage');
            const sRect = stage.getBoundingClientRect();
            const sidebar = document.querySelector('.sidebar');
            const sideRect = sidebar.getBoundingClientRect();
            const overlay = document.querySelector('.acupuncture-overlay');
            const oRect = overlay.getBoundingClientRect();

            const paths = Array.from(document.querySelectorAll('#groupMeridians path'));
            let leakingPaths = [];
            let negativeXCoords = [];
            let extremeCoords = [];

            for (const p of paths) {
                const pRect = p.getBoundingClientRect();
                const d = p.getAttribute('d') || '';
                // Parse coordinates in d
                const nums = d.match(/[-+]?[0-9]*\.?[0-9]+/g) || [];
                for (let i = 0; i < nums.length; i += 2) {
                    const x = parseFloat(nums[i]);
                    const y = parseFloat(nums[i+1]);
                    if (x < 0) negativeXCoords.push({ x, y, path: d.slice(0, 30) });
                    if (x < -50 || x > sRect.width + 50 || y < -50 || y > sRect.height + 50) {
                        extremeCoords.push({ x, y });
                    }
                }

                // Check if path visual rect extends into sidebar (pRect.left < sideRect.right)
                if (pRect.left < sideRect.right && pRect.width > 0) {
                    leakingPaths.push({
                        left: pRect.left,
                        right: pRect.right,
                        sidebarRight: sideRect.right,
                        d_preview: d.slice(0, 40)
                    });
                }
            }

            return {
                stageRect: { left: sRect.left, top: sRect.top, width: sRect.width, height: sRect.height },
                sidebarRect: { left: sideRect.left, top: sideRect.top, width: sideRect.width, height: sideRect.height },
                pathsCount: paths.length,
                leakingCount: leakingPaths.length,
                leakingSample: leakingPaths.slice(0, 5),
                negativeXCount: negativeXCoords.length,
                negativeXSample: negativeXCoords.slice(0, 5),
                extremeCoordsCount: extremeCoords.length
            };
        }""")

        print(f"  Standalone Leakage Analysis:")
        print(f"    Paths Count: {standalone_leakage['pathsCount']}")
        print(f"    Leaking into Sidebar: {standalone_leakage['leakingCount']}")
        print(f"    Negative X coords in d: {standalone_leakage['negativeXCount']}")
        print(f"    Sample leaking: {standalone_leakage['leakingSample']}")

        # ----------------------------------------------------------------------
        # Scenario 2: Comparative Mode Viewport Separation & Zoom
        # Check if right-half meridian paths cross divider into left anatomy half
        # ----------------------------------------------------------------------
        print("\n2. Testing Comparative Viewport (/atlas/ Comparative Mode)...")
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

        page.screenshot(path=os.path.join(ARTIFACT_DIR, "p0_before_comparative_initial.png"))
        print("  [Saved] p0_before_comparative_initial.png")

        # Zoom into neck/torso in Comparative Mode
        for _ in range(8):
            page.mouse.move(center_x, center_y)
            page.mouse.wheel(0, -120)
            time.sleep(0.05)
        time.sleep(1.0)

        page.screenshot(path=os.path.join(ARTIFACT_DIR, "p0_before_comparative_zoomed.png"))
        print("  [Saved] p0_before_comparative_zoomed.png")

        # Check for paths crossing divider (X < stage.width / 2)
        comp_leakage = page.evaluate("""() => {
            const stage = document.querySelector('.stage');
            const sRect = stage.getBoundingClientRect();
            const halfW = sRect.width * 0.5;

            const paths = Array.from(document.querySelectorAll('#groupMeridians path'));
            let crossingDividerPaths = [];
            let negativeXPaths = [];

            for (const p of paths) {
                const pRect = p.getBoundingClientRect();
                const d = p.getAttribute('d') || '';
                const nums = d.match(/[-+]?[0-9]*\.?[0-9]+/g) || [];
                for (let i = 0; i < nums.length; i += 2) {
                    const x = parseFloat(nums[i]);
                    const y = parseFloat(nums[i+1]);
                    if (x < halfW) {
                        crossingDividerPaths.push({ x, y, halfW });
                    }
                    if (x < 0) {
                        negativeXPaths.push({ x, y });
                    }
                }
            }

            return {
                halfW,
                crossingDividerCount: crossingDividerPaths.length,
                crossingDividerSample: crossingDividerPaths.slice(0, 5),
                negativeXCount: negativeXPaths.length,
                negativeXSample: negativeXPaths.slice(0, 5)
            };
        }""")

        print(f"  Comparative Mode Leakage Analysis:")
        print(f"    Divider Half-Width: {comp_leakage['halfW']}")
        print(f"    Coords Crossing into Left (Anatomy) Viewport: {comp_leakage['crossingDividerCount']}")
        print(f"    Sample Crossing: {comp_leakage['crossingDividerSample']}")
        print(f"    Negative X coords: {comp_leakage['negativeXCount']}")

        # ----------------------------------------------------------------------
        # Scenario 3: Main Host Application at / (embedded atlas)
        # ----------------------------------------------------------------------
        print("\n3. Testing Embedded Main App (http://127.0.0.1:8085/)...")
        page_host = browser.new_page(viewport={"width": 1280, "height": 850})
        page_host.goto("http://127.0.0.1:8085/", wait_until="networkidle", timeout=30000)
        time.sleep(2.0)

        # Enable Meridians on Host Toolbar
        page_host.evaluate("""() => {
            const b = document.getElementById('btnToggleMeridians');
            if (b && !b.classList.contains('active')) b.click();
        }""")
        time.sleep(1.0)

        # Zoom inside iframe
        frame_box = page_host.locator("#atlasFrame").bounding_box()
        f_center_x = frame_box["x"] + frame_box["width"] * 0.5
        f_center_y = frame_box["y"] + frame_box["height"] * 0.4

        for _ in range(12):
            page_host.mouse.move(f_center_x, f_center_y)
            page_host.mouse.wheel(0, -120)
            time.sleep(0.05)
        time.sleep(1.0)

        page_host.screenshot(path=os.path.join(ARTIFACT_DIR, "p0_before_host_app_zoomed.png"))
        print("  [Saved] p0_before_host_app_zoomed.png")

        # Save analysis report
        report = {
            "standalone_leakage": standalone_leakage,
            "comparative_leakage": comp_leakage,
            "timestamp": time.time(),
            "status": "REPRODUCED_CONFIRMED" if (standalone_leakage["leakingCount"] > 0 or comp_leakage["crossingDividerCount"] > 0) else "NOT_REPRODUCED"
        }
        with open(os.path.join(ARTIFACT_DIR, "p0_defect_reproduction.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("\n" + "=" * 80)
        print(f"P0 DEFECT REPRODUCTION STATUS: {report['status']}")
        print("=" * 80)

        browser.close()

if __name__ == "__main__":
    run_reproduction()
