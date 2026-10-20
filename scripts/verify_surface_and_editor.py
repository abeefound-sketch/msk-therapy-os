import json
import os
import shutil
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = Path(r"C:\Users\tuanh\.gemini\antigravity-cli\brain\bb14e5bd-1e41-49cd-aad4-33cbc5844729")
LOCAL_SCREENSHOTS = Path("D:/5Projects/msk-therapy-os/screenshots")
LOCAL_SCREENSHOTS.mkdir(exist_ok=True, parents=True)

def copy_to_artifacts(src_path: Path):
    if ARTIFACTS_DIR.exists():
        dst = ARTIFACTS_DIR / src_path.name
        shutil.copy2(src_path, dst)
        print(f"Copied {src_path.name} to artifacts directory.")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-web-security', '--enable-webgl'])
        context = browser.new_context(viewport={'width': 1280, 'height': 850})
        page = context.new_page()

        print("Navigating to MSK-Therapy-OS on http://localhost:8085 ...")
        page.goto("http://localhost:8085", wait_until="networkidle")
        time.sleep(3)

        # Wait for iframe to load
        iframe_element = page.wait_for_selector("#atlasFrame")
        iframe = iframe_element.content_frame()
        print("Atlas iframe found, waiting for WebGL initialization...")
        time.sleep(3)

        # Enable Acupoints and Meridians overlays
        page.evaluate("() => { if (typeof toggleAtlasLayer === 'function') { toggleAtlasLayer('points'); toggleAtlasLayer('meridians'); } }")
        time.sleep(1.5)

        # Ensure verified_only is false so all 5 regions and 362 points can be viewed
        page.evaluate("() => { if (layerStates.verified_only) toggleAtlasLayer('verified_only'); }")
        time.sleep(1.5)

        # -------------------------------------------------------------
        # 1. Head & Neck Region (Front View)
        # -------------------------------------------------------------
        print("Capturing 1: Head & Neck Front View...")
        page.evaluate("() => { atlasCommand('set_view', { preset: 'front' }); atlasCommand('set_region', { region: 'head' }); }")
        time.sleep(1.5)
        path1 = LOCAL_SCREENSHOTS / "evidence_surface_01_head_front.png"
        page.screenshot(path=str(path1))
        copy_to_artifacts(path1)

        # -------------------------------------------------------------
        # 2. Head & Neck Region (Back View)
        # -------------------------------------------------------------
        print("Capturing 2: Head & Neck Back View (GV14, GB20, BL10)...")
        page.evaluate("() => { atlasCommand('set_view', { preset: 'back' }); atlasCommand('set_region', { region: 'neck' }); }")
        time.sleep(1.5)
        path2 = LOCAL_SCREENSHOTS / "evidence_surface_02_neck_back.png"
        page.screenshot(path=str(path2))
        copy_to_artifacts(path2)

        # -------------------------------------------------------------
        # 3. Shoulder & Upper Back (Posterior / Oblique View)
        # -------------------------------------------------------------
        print("Capturing 3: Shoulder & Upper Back (GB21, SI15, TE15)...")
        page.evaluate("() => { atlasCommand('set_view', { preset: 'back' }); atlasCommand('set_region', { region: 'shoulder' }); }")
        time.sleep(1.5)
        path3 = LOCAL_SCREENSHOTS / "evidence_surface_03_shoulder_back.png"
        page.screenshot(path=str(path3))
        copy_to_artifacts(path3)

        # -------------------------------------------------------------
        # 4. Arm & Hand Region (Front View with LI4, LI11, PC6)
        # -------------------------------------------------------------
        print("Capturing 4: Arm & Hand Surface Registration (LI4, LI11)...")
        page.evaluate("() => { atlasCommand('set_view', { preset: 'front' }); atlasCommand('set_region', { region: 'arm' }); }")
        time.sleep(1.5)
        # Select LI4
        page.evaluate("() => { atlasCommand('select_acupoint', { code: 'LI4' }); }")
        time.sleep(1.5)
        path4 = LOCAL_SCREENSHOTS / "evidence_surface_04_arm_hand_li4.png"
        page.screenshot(path=str(path4))
        copy_to_artifacts(path4)

        # -------------------------------------------------------------
        # 5. Leg & Foot Region (Anterolateral View with ST36, SP6)
        # -------------------------------------------------------------
        print("Capturing 5: Leg & Foot Surface Registration (ST36, SP6)...")
        page.evaluate("() => { atlasCommand('set_view', { preset: 'front' }); atlasCommand('set_region', { region: 'leg' }); }")
        time.sleep(1.5)
        # Select ST36
        page.evaluate("() => { atlasCommand('select_acupoint', { code: 'ST36' }); }")
        time.sleep(1.5)
        path5 = LOCAL_SCREENSHOTS / "evidence_surface_05_leg_foot_st36.png"
        page.screenshot(path=str(path5))
        copy_to_artifacts(path5)

        # -------------------------------------------------------------
        # 6. Full Body Continuous Surface Meridians (All 14 Meridians)
        # -------------------------------------------------------------
        print("Capturing 6: Full Body Continuous Surface Meridians (10,762 Vertices)...")
        page.evaluate("() => { atlasCommand('set_view', { preset: 'front' }); atlasCommand('set_region', { region: 'all' }); }")
        time.sleep(1.5)
        path6 = LOCAL_SCREENSHOTS / "evidence_surface_06_full_body_meridians.png"
        page.screenshot(path=str(path6))
        copy_to_artifacts(path6)

        # -------------------------------------------------------------
        # 7. Acupoint & Meridian Calibration Studio Modal Open
        # -------------------------------------------------------------
        print("Capturing 7: 3D Calibration Studio Modal...")
        page.evaluate("() => { openStudioEditorModal({ code: 'LI4' }); }")
        time.sleep(1.5)
        path7 = LOCAL_SCREENSHOTS / "evidence_surface_07_calibration_studio_modal.png"
        page.screenshot(path=str(path7))
        copy_to_artifacts(path7)

        # -------------------------------------------------------------
        # 8. Interactive Nudge Controls Live Test
        # -------------------------------------------------------------
        print("Capturing 8: Studio Live Nudge Calibration & Apply...")
        # Click +5mm on X axis
        page.click("button.btn-nudge[data-axis='x'][data-delta='0.005']")
        time.sleep(1.0)
        # Click +3mm on normal
        page.click("button.btn-nudge-norm[data-delta='0.003']")
        time.sleep(1.0)
        path8 = LOCAL_SCREENSHOTS / "evidence_surface_08_studio_nudged.png"
        page.screenshot(path=str(path8))
        copy_to_artifacts(path8)

        # Performance Metrics
        perf = page.evaluate("""() => {
            return {
                jsHeapSize: performance.memory ? Math.round(performance.memory.usedJSHeapSize / (1024 * 1024)) : 'N/A',
                timing: {
                    domContentLoaded: Math.round(performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart),
                    load: Math.round(performance.timing.loadEventEnd - performance.timing.navigationStart)
                }
            };
        }""")
        print("Performance Metrics:", json.dumps(perf, indent=2))

        browser.close()
        print("Surface registration and editor verification complete!")

if __name__ == '__main__':
    main()
