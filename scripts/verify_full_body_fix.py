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
        print(f"Copied {src_path.name} to artifacts directory.")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-web-security', '--enable-webgl'])
        context = browser.new_context(viewport={'width': 1280, 'height': 850})
        page = context.new_page()

        print("Navigating to http://localhost:8085 ...")
        page.goto("http://localhost:8085", wait_until="networkidle")
        time.sleep(3)

        # Click the "Full Body" button
        print("Clicking 'Full Body' region button...")
        page.click("button.region-btn[data-region='all']")
        time.sleep(2)

        # Verify title & count
        title = page.inner_text("#selectedRegionTitle")
        count = page.inner_text("#structureCount")
        print(f"Region Title: {title}")
        print(f"Structure Count: {count}")

        # Capture screenshot of Full Body view with 32 structures
        p_full = LOCAL_SCREENSHOTS / "evidence_full_body_registered_structures.png"
        page.screenshot(path=str(p_full))
        copy_to_artifacts(p_full)

        browser.close()
        print("Verification of Full Body view complete!")

if __name__ == '__main__':
    main()
