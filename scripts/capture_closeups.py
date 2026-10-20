import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil

ARTIFACTS_DIR = Path(r"C:\Users\tuanh\.gemini\antigravity-cli\brain\bb14e5bd-1e41-49cd-aad4-33cbc5844729")
LOCAL_SCREENSHOTS = Path("D:/5Projects/msk-therapy-os/screenshots")

def copy_to_artifacts(src_path: Path):
    if ARTIFACTS_DIR.exists():
        dst = ARTIFACTS_DIR / src_path.name
        shutil.copy2(src_path, dst)
        print(f"Copied {src_path.name} to artifacts.")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-web-security', '--enable-webgl'])
        context = browser.new_context(viewport={'width': 1280, 'height': 850})
        page = context.new_page()

        page.goto("http://localhost:8085", wait_until="networkidle")
        time.sleep(3)

        # Enable points & meridians
        page.evaluate("() => { toggleAtlasLayer('points'); toggleAtlasLayer('meridians'); if (layerStates.verified_only) toggleAtlasLayer('verified_only'); }")
        time.sleep(1.5)

        # 1. Close-up Head (Front)
        page.evaluate("""() => {
            atlasCommand('set_region', { region: 'head' });
            const r = document.getElementById('atlasFrame').contentWindow.__atlasDebug.renderer;
            r.camera.target = [0, 1.62, 0];
            r.camera.dist = 0.65;
            r.camera.pitch = 0.05;
            r.camera.yaw = 0.0;
            r._draw();
        }""")
        time.sleep(1.5)
        p1 = LOCAL_SCREENSHOTS / "evidence_surface_09_closeup_head_front.png"
        page.screenshot(path=str(p1))
        copy_to_artifacts(p1)

        # 2. Close-up Neck & Shoulder (Back)
        page.evaluate("""() => {
            atlasCommand('set_region', { region: 'neck_shoulder' });
            const r = document.getElementById('atlasFrame').contentWindow.__atlasDebug.renderer;
            r.camera.target = [0, 1.45, -0.05];
            r.camera.dist = 0.75;
            r.camera.pitch = 0.15;
            r.camera.yaw = Math.PI;
            r._draw();
        }""")
        time.sleep(1.5)
        p2 = LOCAL_SCREENSHOTS / "evidence_surface_10_closeup_neck_back.png"
        page.screenshot(path=str(p2))
        copy_to_artifacts(p2)

        # 3. Close-up Arm & Hand (LI4, LI11)
        page.evaluate("""() => {
            atlasCommand('set_region', { region: 'arm' });
            const r = document.getElementById('atlasFrame').contentWindow.__atlasDebug.renderer;
            r.camera.target = [0.28, 0.95, 0.0];
            r.camera.dist = 0.70;
            r.camera.pitch = 0.10;
            r.camera.yaw = -0.3;
            r._draw();
        }""")
        time.sleep(1.5)
        p3 = LOCAL_SCREENSHOTS / "evidence_surface_11_closeup_arm_hand.png"
        page.screenshot(path=str(p3))
        copy_to_artifacts(p3)

        # 4. Close-up Knee & Leg (ST36, SP6)
        page.evaluate("""() => {
            atlasCommand('set_region', { region: 'leg' });
            const r = document.getElementById('atlasFrame').contentWindow.__atlasDebug.renderer;
            r.camera.target = [0.10, 0.45, 0.0];
            r.camera.dist = 0.85;
            r.camera.pitch = 0.05;
            r.camera.yaw = 0.2;
            r._draw();
        }""")
        time.sleep(1.5)
        p4 = LOCAL_SCREENSHOTS / "evidence_surface_12_closeup_knee_leg.png"
        page.screenshot(path=str(p4))
        copy_to_artifacts(p4)

        browser.close()
        print("Updated close-up captures complete!")

if __name__ == '__main__':
    main()
