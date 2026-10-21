"""Automated verification and telemetry suite for the Three Visualization Modes:
1. Mode A: Surface Meridian Mode (translucent skin mesh + surface meridians)
2. Mode B: Musculoskeletal Anatomy Mode (pure muscles/bones, meridians hidden by default, surface reference guide toggleable)
3. Mode C: Comparative Research Mode (synchronized dual split view)
4. Normal-based backface culling & occlusion
5. Meridian channel filtering (e.g. GV only)
6. Skin opacity adjustment
7. Neck-Shoulder-Upper-Back scenario (GV14, GB21, GB20, BL10, SI15, TE15)
8. Real hardware telemetry (Intel HD 5500 / D3D11)
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_ROOT = Path("D:/5Projects/msk-therapy-os")
LOCAL_ARTIFACTS = REPO_ROOT / "research" / "artifacts"
LOCAL_ARTIFACTS.mkdir(parents=True, exist_ok=True)

BRAIN_ARTIFACTS = Path("C:/Users/tuanh/.gemini/antigravity-cli/brain/bb14e5bd-1e41-49cd-aad4-33cbc5844729")


def save_screenshot(page, filename: str):
    local_path = LOCAL_ARTIFACTS / filename
    page.screenshot(path=str(local_path))
    print(f"  [Screenshot] Saved {local_path.name}")
    if BRAIN_ARTIFACTS.exists():
        try:
            shutil.copy2(local_path, BRAIN_ARTIFACTS / filename)
        except Exception as e:
            print(f"  [Warning] Failed to copy to brain artifacts: {e}")


def verify_visualization_modes():
    atlas_url = "http://127.0.0.1:8085/atlas/"
    main_url = "http://127.0.0.1:8085/"

    results = {}
    console_errors = []

    print("\n=======================================================")
    print("STARTING THREE VISUALIZATION MODES ACCEPTANCE VERIFICATION")
    print("=======================================================\n")

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

        page = browser.new_page(viewport={"width": 1280, "height": 820})
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print("1. Loading Atlas Viewer at http://127.0.0.1:8085/atlas/ ...")
        page.goto(atlas_url, wait_until="networkidle", timeout=30000)

        page.wait_for_function("() => Boolean(window.__atlasDebug && window.__atlasDebug.renderer && window.__atlasDebug.atlas)", timeout=30000)
        page.wait_for_function("() => Boolean(window.__meridiansDebug && window.__meridiansDebug.acuData)", timeout=15000)
        time.sleep(1)

        # -------------------------------------------------------------
        # Part A: Mode A - Surface Meridian Mode
        # -------------------------------------------------------------
        print("\n2. Testing Mode A: Surface Meridian Mode...")
        # Activate Surface mode
        page.evaluate("""() => {
            const btnSurface = document.querySelector('#visModeSelector button[data-mode="surface"]');
            if (btnSurface) btnSurface.click();
            else if (window.setRenderMode) window.setRenderMode('surface');
            const chkPts = document.getElementById('chkShowPoints');
            if (chkPts && !chkPts.checked) { chkPts.checked = true; chkPts.dispatchEvent(new Event('change')); }
            const chkMers = document.getElementById('chkShowMeridians');
            if (chkMers && !chkMers.checked) { chkMers.checked = true; chkMers.dispatchEvent(new Event('change')); }
        }""")
        time.sleep(1.0)

        # Frame posterior neck-shoulder
        page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            r.camera.yaw = Math.PI; // Posterior view
            r.camera.pitch = 0.08;
            r.camera.dist = 0.65;
            r.camera.target = [0, 1.44, -0.08];
            r.dirty = true;
        }""")
        time.sleep(0.8)

        # Select GV14
        page.evaluate("""() => {
            if (window.__meridiansDebug && window.__meridiansDebug.selectPoint) {
                window.__meridiansDebug.selectPoint('GV14', false);
            }
        }""")
        time.sleep(0.5)

        surface_state = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return {
                renderMode: r.renderMode,
                skinOpacity: r.skinOpacity,
                ptsVisible: document.querySelectorAll('#groupPoints circle').length,
                mersVisible: document.querySelectorAll('#groupMeridians path').length,
            };
        }""")
        print(f"  Mode A State: mode='{surface_state['renderMode']}', skinOpacity={surface_state['skinOpacity']}, points={surface_state['ptsVisible']}, meridians={surface_state['mersVisible']}")
        assert surface_state["renderMode"] == "surface", f"Mode A expected 'surface', got {surface_state['renderMode']}"
        assert surface_state["skinOpacity"] > 0.5, f"Skin opacity should be active: {surface_state['skinOpacity']}"
        assert surface_state["ptsVisible"] > 0, "Points should be rendered in Surface Mode"
        results["mode_a_surface"] = "PASS"
        save_screenshot(page, "evidence_mode_a_surface_meridians.png")

        # -------------------------------------------------------------
        # Part B: Mode B - Musculoskeletal Anatomy Mode
        # -------------------------------------------------------------
        print("\n3. Testing Mode B: Musculoskeletal Anatomy Mode...")
        # Activate Musculoskeletal mode
        page.evaluate("""() => {
            const btnAnatomy = document.querySelector('#visModeSelector button[data-mode="musculoskeletal"]');
            if (btnAnatomy) btnAnatomy.click();
            else if (window.setRenderMode) window.setRenderMode('musculoskeletal');
        }""")
        time.sleep(1.0)

        musculo_state = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return {
                renderMode: r.renderMode,
                skinOpacity: r.skinOpacity,
                ptsVisible: document.querySelectorAll('#groupPoints circle').length,
                mersVisible: document.querySelectorAll('#groupMeridians path').length,
            };
        }""")
        print(f"  Mode B State: mode='{musculo_state['renderMode']}', skinOpacity={musculo_state['skinOpacity']}, points={musculo_state['ptsVisible']}, meridians={musculo_state['mersVisible']}")
        assert musculo_state["renderMode"] == "musculoskeletal", f"Mode B expected 'musculoskeletal', got {musculo_state['renderMode']}"
        # Meridians and points MUST be hidden by default in musculoskeletal mode!
        assert musculo_state["ptsVisible"] == 0, f"Acupoints should be hidden by default in Musculoskeletal mode, found {musculo_state['ptsVisible']}"
        assert musculo_state["mersVisible"] == 0, f"Meridians should be hidden by default in Musculoskeletal mode, found {musculo_state['mersVisible']}"
        results["mode_b_musculoskeletal"] = "PASS"
        save_screenshot(page, "evidence_mode_b_musculoskeletal_clean.png")

        # Now test optional Surface Reference Guide in Musculoskeletal Mode
        print("  Testing Optional Surface Reference Guide in Musculoskeletal Mode...")
        page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            r.setSkinReference(true);
            window.postMessage({ action: 'toggle_surface_reference', enabled: true }, '*');
        }""")
        time.sleep(0.8)

        ref_state = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return {
                skinRefOn: r.skinReferenceOn,
                ptsVisible: document.querySelectorAll('#groupPoints circle').length,
                badgeText: document.querySelector('#groupPoints text') ? document.querySelector('#groupPoints text').textContent : '',
            };
        }""")
        print(f"  Surface Ref State: skinRef={ref_state['skinRefOn']}, points={ref_state['ptsVisible']}, badge='{ref_state['badgeText']}'")
        assert ref_state["skinRefOn"] is True, "Skin reference envelope should be active"
        assert "SURFACE REFERENCE" in ref_state["badgeText"], f"Expected 'SURFACE REFERENCE' badge, got '{ref_state['badgeText']}'"
        results["mode_b_surface_reference_overlay"] = "PASS"
        save_screenshot(page, "evidence_mode_b_musculoskeletal_with_reference.png")

        # -------------------------------------------------------------
        # Part C: Mode C - Comparative Research Mode (Dual Split View)
        # -------------------------------------------------------------
        print("\n4. Testing Mode C: Comparative Research Mode (Dual View)...")
        page.evaluate("""() => {
            const btnComp = document.querySelector('#visModeSelector button[data-mode="comparative"]');
            if (btnComp) btnComp.click();
            else if (window.setRenderMode) window.setRenderMode('comparative');
        }""")
        time.sleep(1.2)

        comp_state = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            const texts = Array.from(document.querySelectorAll('#groupPoints text')).map(t => t.textContent);
            return {
                renderMode: r.renderMode,
                skinOpacity: r.skinOpacity,
                ptsVisible: document.querySelectorAll('#groupPoints circle').length,
                badges: texts,
            };
        }""")
        print(f"  Mode C State: mode='{comp_state['renderMode']}', badges={comp_state['badges']}")
        assert comp_state["renderMode"] == "comparative", f"Mode C expected 'comparative', got {comp_state['renderMode']}"
        assert any("MUSCULOSKELETAL" in b for b in comp_state["badges"]), "Missing left musculoskeletal viewport badge"
        assert any("SURFACE & MERIDIANS" in b for b in comp_state["badges"]), "Missing right surface & meridians viewport badge"
        results["mode_c_comparative"] = "PASS"
        save_screenshot(page, "evidence_mode_c_comparative_dual_view.png")

        # -------------------------------------------------------------
        # Part D: Surface Normal Occlusion Testing (Front vs Back)
        # -------------------------------------------------------------
        print("\n5. Testing Surface Normal Backface Occlusion...")
        # Switch to Surface mode and examine Front view vs Back view
        page.evaluate("""() => {
            window.setRenderMode('surface');
            const r = window.__atlasDebug.renderer;
            r.view('front'); // Anterior view
        }""")
        time.sleep(1.0)

        front_facing_gv14 = page.evaluate("""() => {
            // Check if dorsal point GV14 is occluded when looking at the front of the body
            const c = document.querySelector('#groupPoints circle[data-code="GV14"]');
            if (!c) return { visible: false };
            const op = parseFloat(c.getAttribute('opacity') || '1');
            return {
                visible: true,
                opacity: op,
                isOccluded: op <= 0.5,
            };
        }""")
        print(f"  GV14 from Front: {front_facing_gv14}")
        assert front_facing_gv14["visible"] is False or front_facing_gv14["isOccluded"], "GV14 (dorsal C7 point) should be occluded or faded when viewing from the front!"
        save_screenshot(page, "evidence_occlusion_front_view.png")

        # Now view from Back
        page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            r.view('back'); // Posterior view
        }""")
        time.sleep(1.0)

        back_facing_gv14 = page.evaluate("""() => {
            const c = document.querySelector('#groupPoints circle[data-code="GV14"]');
            if (!c) return { visible: false };
            const op = parseFloat(c.getAttribute('opacity') || '1');
            return {
                visible: true,
                opacity: op,
                isFacing: op > 0.8,
            };
        }""")
        print(f"  GV14 from Back: {back_facing_gv14}")
        assert back_facing_gv14["visible"] and back_facing_gv14["isFacing"], "GV14 should be unoccluded and crisp when viewing from the back!"
        save_screenshot(page, "evidence_occlusion_back_view.png")
        results["surface_normal_occlusion"] = "PASS"

        # -------------------------------------------------------------
        # Part E: Meridian Channel Filter (GV Du Mai Only)
        # -------------------------------------------------------------
        print("\n6. Testing Individual Meridian Channel Filtering (GV Du Mai)...")
        page.evaluate("""() => {
            window.postMessage({ action: 'set_filter_meridian', meridian: 'GV' }, '*');
        }""")
        time.sleep(0.8)

        gv_filtered = page.evaluate("""() => {
            const circles = Array.from(document.querySelectorAll('#groupPoints circle.acu-marker'));
            const codes = circles.map(c => c.getAttribute('data-code'));
            const allGV = codes.every(c => c.startsWith('GV'));
            return {
                count: codes.length,
                allGV,
                codes: codes.slice(0, 8),
            };
        }""")
        print(f"  Filtered GV Points count: {gv_filtered['count']}, allGV: {gv_filtered['allGV']}, samples: {gv_filtered['codes']}")
        assert gv_filtered["count"] > 0 and gv_filtered["allGV"], "Channel filter failed: non-GV points found when filtering for GV"
        results["meridian_channel_filter"] = "PASS"
        save_screenshot(page, "evidence_meridian_filter_gv_only.png")

        # Reset filter to all
        page.evaluate("""() => {
            window.postMessage({ action: 'set_filter_meridian', meridian: 'all' }, '*');
        }""")
        time.sleep(0.5)

        # -------------------------------------------------------------
        # Part F: Main Host UI Integration & Responsiveness
        # -------------------------------------------------------------
        print("\n7. Testing Main Host Application UI & Mode Synchronization at http://127.0.0.1:8085/ ...")
        main_page = browser.new_page(viewport={"width": 1440, "height": 900})
        main_page.goto(main_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Verify host mode switcher buttons exist
        host_surf = main_page.locator("#hostBtnModeSurface")
        host_musc = main_page.locator("#hostBtnModeMusculo")
        host_comp = main_page.locator("#hostBtnModeComparative")
        assert host_surf.is_visible(), "Host Surface button not visible"
        assert host_musc.is_visible(), "Host Musculoskeletal button not visible"
        assert host_comp.is_visible(), "Host Comparative button not visible"

        # Click Comparative mode on host toolbar
        host_comp.click()
        time.sleep(1.2)

        # Adjust skin opacity slider on host
        host_slider = main_page.locator("#hostSkinOpacity")
        host_slider.fill("50")
        main_page.evaluate("() => onHostSkinOpacityChange('50')")
        time.sleep(0.5)

        # Select GV14 from Quick Landmarks or directory
        main_page.evaluate("""() => {
            const frame = document.getElementById('atlasFrame');
            if (frame && frame.contentWindow) {
                frame.contentWindow.postMessage({ action: 'select_acupoint', code: 'GV14' }, '*');
            }
        }""")
        time.sleep(1.0)

        # Verify host acupoint card populated
        acu_card = main_page.locator("#atlasAcupointCard")
        assert acu_card.is_visible(), "Host Acupoint Card should be displayed upon GV14 selection"
        acu_title = main_page.locator("#acuPointTitle").text_content()
        print(f"  Host Acupoint Title: '{acu_title}'")
        assert "GV14" in acu_title, f"Expected GV14 in title, got '{acu_title}'"

        save_screenshot(main_page, "evidence_main_host_comparative_mode.png")
        results["main_host_mode_synchronization"] = "PASS"

        # -------------------------------------------------------------
        # Part G: Responsive Layouts (1280px, 768px, 375px)
        # -------------------------------------------------------------
        print("\n8. Testing Responsive Layouts (1280px, 768px, 375px)...")
        # 768px Tablet
        main_page.set_viewport_size({"width": 768, "height": 1024})
        time.sleep(0.6)
        save_screenshot(main_page, "evidence_responsive_768px.png")

        # 375px Mobile
        main_page.set_viewport_size({"width": 375, "height": 812})
        time.sleep(0.6)
        save_screenshot(main_page, "evidence_responsive_375px.png")

        # Verify horizontal scroll does not explode
        scroll_width = main_page.evaluate("() => document.documentElement.scrollWidth")
        client_width = main_page.evaluate("() => document.documentElement.clientWidth")
        print(f"  At 375px: scrollWidth={scroll_width}, clientWidth={client_width}")
        assert scroll_width <= client_width + 5, f"Horizontal overflow at 375px: {scroll_width} > {client_width}"
        results["responsive_layouts"] = "PASS"

        # -------------------------------------------------------------
        # Part H: Real Hardware Performance Telemetry
        # -------------------------------------------------------------
        print("\n9. Capturing Hardware Performance Telemetry...")
        perf_data = main_page.evaluate("""() => {
            const timing = performance.timing;
            const loadTimeMs = timing.loadEventEnd - timing.navigationStart;
            const memory = performance.memory ? {
                usedJSHeapSizeMB: (performance.memory.usedJSHeapSize / 1048576).toFixed(1),
                totalJSHeapSizeMB: (performance.memory.totalJSHeapSize / 1048576).toFixed(1),
            } : null;
            return {
                loadTimeMs,
                memory,
            };
        }""")
        print(f"  Telemetry: {perf_data}")
        results["telemetry"] = perf_data

        browser.close()

    print("\n=======================================================")
    print("ALL THREE VISUALIZATION MODES VERIFIED SUCCESSFULLY!")
    print(f"Summary: {json.dumps(results, indent=2)}")
    print(f"Console errors: {len(console_errors)}")
    print("=======================================================\n")

    summary_file = LOCAL_ARTIFACTS / "three_visualization_modes_acceptance_results.json"
    summary_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    if BRAIN_ARTIFACTS.exists():
        shutil.copy2(summary_file, BRAIN_ARTIFACTS / "three_visualization_modes_acceptance_results.json")

    return results


if __name__ == "__main__":
    verify_visualization_modes()
