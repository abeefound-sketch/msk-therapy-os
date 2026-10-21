import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil

ARTIFACTS_DIR = Path(r"C:\Users\tuanh\.gemini\antigravity-cli\brain\bb14e5bd-1e41-49cd-aad4-33cbc5844729")
LOCAL_ARTIFACTS = Path("D:/5Projects/msk-therapy-os/research/artifacts")

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

        print("Navigating to tcm-acupoints on http://127.0.0.1:5175 ...")
        t0 = time.time()
        page.goto("http://127.0.0.1:5175", wait_until="networkidle")
        load_ms = round((time.time() - t0) * 1000)
        time.sleep(3)

        # Wait for 3D body canvas
        page.wait_for_selector("canvas", timeout=10000)
        time.sleep(2)

        p_img = LOCAL_ARTIFACTS / "evidence_bench_04_tcmacupoints.png"
        page.screenshot(path=str(p_img))
        copy_to_artifacts(p_img)

        perf = page.evaluate("""() => {
            return {
                jsHeapSize: performance.memory ? Math.round(performance.memory.usedJSHeapSize / (1024 * 1024)) : 'N/A',
                domContentLoaded: Math.round(performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart),
                load: Math.round(performance.timing.loadEventEnd - performance.timing.navigationStart)
            };
        }""")
        perf['networkLoadMs'] = load_ms
        print("TCM-Acupoints Metrics:", json.dumps(perf, indent=2))

        with open(LOCAL_ARTIFACTS / "metrics_tcmacupoints.json", "w", encoding="utf-8") as f:
            json.dump(perf, f, indent=2)

        browser.close()
        print("TCM-Acupoints benchmark capture complete!")

if __name__ == '__main__':
    main()
