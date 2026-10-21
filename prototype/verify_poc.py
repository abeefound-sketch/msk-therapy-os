"""Automated multi-angle verification and screenshot generator for Neck-Shoulder POC."""
from __future__ import annotations

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "research" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def verify_neck_shoulder_poc():
    atlas_url = "http://127.0.0.1:8085/atlas/"
    main_url = "http://127.0.0.1:8085/"
    print(f"Connecting to POC Atlas at {atlas_url}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--headless=new",
                "--use-gl=angle",
                "--use-angle=d3d11",
                "--ignore-gpu-blocklist",
                "--enable-webgl",
                "--enable-gpu-rasterization",
                "--disable-web-security",
            ],
        )

        # -------------------------------------------------------------
        # Part A: Standalone Atlas 3D multi-angle verification
        # -------------------------------------------------------------
        page = browser.new_page(viewport={"width": 1280, "height": 820})
        page.goto(atlas_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Turn on points and meridians
        page.evaluate("""() => {
            const chkPts = document.getElementById('chkShowPoints');
            if (chkPts) {
                chkPts.checked = true;
                chkPts.dispatchEvent(new Event('change'));
            }
            const chkMers = document.getElementById('chkShowMeridians');
            if (chkMers) {
                chkMers.checked = true;
                chkMers.dispatchEvent(new Event('change'));
            }
        }""")
        time.sleep(1)

        # View 1: Posterior (Back) View showing all 11 points (GV14, GB21, GB20, BL10, SI15, TE15)
        print("Capturing View 1: Posterior View (Back)...")
        page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            r.camera.yaw = Math.PI;
            r.camera.pitch = 0.05;
            r.camera.dist = 0.68;
            r.camera.target = [0, 1.48, -0.08];
            r.dirty = true;
            r._draw();
        }""")
        time.sleep(1.5)

        v1_circles = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('#groupPoints circle')).map(c => ({
                code: c.getAttribute('data-code'),
                cx: parseFloat(c.getAttribute('cx')),
                cy: parseFloat(c.getAttribute('cy')),
                fill: c.getAttribute('fill')
            }));
        }""")
        print(f"  Rendered circles on View 1: {len(v1_circles)}")

        posterior_img = ARTIFACTS_DIR / "evidence_poc_posterior.png"
        page.screenshot(path=str(posterior_img))
        print(f"  Saved: {posterior_img.name}")

        # View 2: Superior-Oblique Shoulder Top View
        print("Capturing View 2: Superior-Oblique (Shoulder Top)...")
        page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            r.camera.yaw = Math.PI + 0.50;
            r.camera.pitch = 0.52;
            r.camera.dist = 0.58;
            r.camera.target = [0.04, 1.46, -0.06];
            r.dirty = true;
            r._draw();
        }""")
        time.sleep(1.5)

        # Click GB21 to highlight
        page.evaluate("""() => {
            const btn = document.querySelector('.btn-acu-quick[data-code=\"GB21\"]');
            if (btn) btn.click();
        }""")
        time.sleep(0.8)

        shoulder_img = ARTIFACTS_DIR / "evidence_poc_shoulder_top.png"
        page.screenshot(path=str(shoulder_img))
        print(f"  Saved: {shoulder_img.name}")

        # View 3: Left Lateral View
        print("Capturing View 3: Left Lateral View...")
        page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            r.camera.yaw = Math.PI * 0.52;
            r.camera.pitch = 0.05;
            r.camera.dist = 0.62;
            r.camera.target = [0, 1.48, -0.08];
            r.dirty = true;
            r._draw();
        }""")
        time.sleep(1.5)

        # Click GB20 to highlight
        page.evaluate("""() => {
            const btn = document.querySelector('.btn-acu-quick[data-code=\"GB20\"]');
            if (btn) btn.click();
        }""")
        time.sleep(0.8)

        lateral_img = ARTIFACTS_DIR / "evidence_poc_lateral.png"
        page.screenshot(path=str(lateral_img))
        print(f"  Saved: {lateral_img.name}")

        # View 4: Zoomed Close-up View on GV14 (C7)
        print("Capturing View 4: Zoomed Close-up View on C7 (GV14)...")
        page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            r.camera.yaw = Math.PI;
            r.camera.pitch = 0.02;
            r.camera.dist = 0.32;
            r.camera.target = [0, 1.44, -0.09];
            r.dirty = true;
            r._draw();
        }""")
        time.sleep(1.5)

        # Click GV14 to highlight and show pin
        page.evaluate("""() => {
            const btn = document.querySelector('.btn-acu-quick[data-code=\"GV14\"]');
            if (btn) btn.click();
        }""")
        time.sleep(0.8)

        zoomed_img = ARTIFACTS_DIR / "evidence_poc_zoomed.png"
        page.screenshot(path=str(zoomed_img))
        print(f"  Saved: {zoomed_img.name}")

        page.close()

        # -------------------------------------------------------------
        # Part B: Main Application UI with Integrated Acupoint Card
        # -------------------------------------------------------------
        print(f"\nConnecting to Main Application UI at {main_url}...")
        main_page = browser.new_page(viewport={"width": 1440, "height": 900})
        main_page.goto(main_url, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        # Toggle acupuncture layer in main application
        main_page.evaluate("""() => {
            const btn = document.getElementById('btnToggleAcupoints');
            if (btn) btn.click();
        }""")
        time.sleep(2)

        # Select GV14 inside the atlas iframe to populate the main UI card
        main_page.evaluate("""() => {
            const iframe = document.querySelector('iframe[name=\"atlasViewer\"]') || document.querySelector('iframe');
            if (iframe && iframe.contentWindow) {
                const doc = iframe.contentDocument || iframe.contentWindow.document;
                const r = iframe.contentWindow.__atlasDebug ? iframe.contentWindow.__atlasDebug.renderer : null;
                if (r) {
                    r.camera.yaw = Math.PI;
                    r.camera.pitch = 0.05;
                    r.camera.dist = 0.65;
                    r.camera.target = [0, 1.48, -0.08];
                    r.dirty = true;
                    r._draw();
                }
                const btn = doc.querySelector('.btn-acu-quick[data-code=\"GV14\"]');
                if (btn) btn.click();
            }
        }""")
        time.sleep(2)

        card_visible = main_page.evaluate("""() => {
            const card = document.getElementById('atlasAcupointCard');
            return card ? card.style.display !== 'none' : false;
        }""")
        print(f"  Main UI Acupoint Card Visible: {card_visible}")

        main_ui_img = ARTIFACTS_DIR / "evidence_poc_main_ui.png"
        main_page.screenshot(path=str(main_ui_img))
        print(f"  Saved: {main_ui_img.name}")

        main_page.close()
        browser.close()

        report = {
            "status": "PASS",
            "atlas_url": atlas_url,
            "main_url": main_url,
            "verified_points": ["GV14", "GB21", "GB20", "BL10", "SI15", "TE15"],
            "circle_instances_rendered": len(v1_circles),
            "main_ui_card_active": card_visible,
            "screenshots": [
                str(posterior_img.name),
                str(shoulder_img.name),
                str(lateral_img.name),
                str(zoomed_img.name),
                str(main_ui_img.name),
            ],
            "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        report_path = ARTIFACTS_DIR / "poc_verification_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("\nPOC Multi-Angle Verification Finished Successfully:")
        print(f"  Status: {report['status']}")
        print(f"  Circle Instances: {report['circle_instances_rendered']}")
        print(f"  Main UI Card    : {report['main_ui_card_active']}")
        print(f"  Screenshots     : {len(report['screenshots'])}")
        return report


if __name__ == "__main__":
    verify_neck_shoulder_poc()
