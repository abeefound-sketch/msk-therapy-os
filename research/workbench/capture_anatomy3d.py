import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil

ARTIFACTS_DIR = Path(r"C:\Users\tuanh\.gemini\antigravity-cli\brain\bb14e5bd-1e41-49cd-aad4-33cbc5844729")
LOCAL_ARTIFACTS = Path("D:/5Projects/msk-therapy-os/research/artifacts")
LOCAL_ARTIFACTS.mkdir(exist_ok=True, parents=True)

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

        print("Navigating to anatomy-3d on http://127.0.0.1:3018 ...")
        t0 = time.time()
        page.goto("http://127.0.0.1:3018", wait_until="networkidle")
        load_ms = round((time.time() - t0) * 1000)
        time.sleep(3)

        # Focus / search for GB21 or Neck-Shoulder
        page.evaluate("""() => {
            // Check if search input exists
            const inp = document.querySelector('input[placeholder*="搜索"], input[type="search"], #search');
            if (inp) {
                inp.value = 'GB21';
                inp.dispatchEvent(new Event('input'));
            }
        }""")
        time.sleep(2)

        p_img = LOCAL_ARTIFACTS / "evidence_bench_03_anatomy3d.png"
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
        print("Anatomy-3D Metrics:", json.dumps(perf, indent=2))

        # Save metrics to JSON
        with open(LOCAL_ARTIFACTS / "metrics_anatomy3d.json", "w", encoding="utf-8") as f:
            json.dump(perf, f, indent=2)

        browser.close()
        print("Anatomy-3D benchmark capture complete!")

if __name__ == '__main__':
    main()
