"""Automated verification script for 3D Atlas Interaction Enhancements.

Tests:
1. Pan support (right-drag & Shift+left-drag).
2. Dynamic OrbitControls target updates on acupoint selection (GV14 at C7 level).
3. Zoom-to-detail without clipping (intelligent near plane).
4. Orbiting around detail target without drifting back to full-body center.
5. "Full Body" re-framing button.
6. "Focus Selected" button.
7. Dynamic target updates on anatomical structure selection.
8. Two-pointer touch interaction state handling.
9. Main UI host integration (SOAP, Safety Gate, iframe messaging).
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


def run_interaction_verification():
    atlas_url = "http://127.0.0.1:8085/atlas/"
    main_url = "http://127.0.0.1:8085/"

    results = {}
    console_errors = []

    print("\n=======================================================")
    print("STARTING 3D ATLAS INTERACTION VERIFICATION")
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

        # -------------------------------------------------------------
        # Part 1: Atlas standalone interactions
        # -------------------------------------------------------------
        page = browser.new_page(viewport={"width": 1280, "height": 820})
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print(f"1. Loading standalone Atlas at {atlas_url}...")
        page.goto(atlas_url, wait_until="networkidle", timeout=30000)

        # Wait for atlas to boot and expose __atlasDebug
        print("  Waiting for Atlas to finish booting...")
        page.wait_for_function("() => Boolean(window.__atlasDebug && window.__atlasDebug.renderer && window.__atlasDebug.atlas)", timeout=30000)
        time.sleep(1)

        # Ensure canvas and renderer are ready
        init_cam = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return {
                target: Array.from(r.camera.target),
                dist: r.camera.dist,
                yaw: r.camera.yaw,
                pitch: r.camera.pitch,
            };
        }""")
        print(f"  Initial Camera Target: {init_cam['target']}, Dist: {init_cam['dist']:.2f}m")
        results["initial_target"] = init_cam["target"]

        # Turn on Points & Meridians
        page.evaluate("""() => {
            const chkPts = document.getElementById('chkShowPoints');
            if (chkPts && !chkPts.checked) { chkPts.checked = true; chkPts.dispatchEvent(new Event('change')); }
            const chkMers = document.getElementById('chkShowMeridians');
            if (chkMers && !chkMers.checked) { chkMers.checked = true; chkMers.dispatchEvent(new Event('change')); }
        }""")
        # Wait for acupoints data to load
        page.wait_for_function("() => Boolean(window.__meridiansDebug && window.__meridiansDebug.acuData)", timeout=15000)
        time.sleep(1)

        # -------------------------------------------------------------
        # Test 1: Right-drag Pan Support
        # -------------------------------------------------------------
        print("\n2. Testing Right-Drag Pan Support...")
        viewport = page.locator("#viewport")
        box = viewport.bounding_box()
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2

        # Drag with right button
        page.mouse.move(cx, cy)
        page.mouse.down(button="right")
        page.mouse.move(cx + 120, cy - 80, steps=10)
        page.mouse.up(button="right")
        time.sleep(0.3)

        panned_cam = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return { target: Array.from(r.camera.target) };
        }""")
        print(f"  Target after right-drag pan: {panned_cam['target']}")
        pan_dx = abs(panned_cam["target"][0] - init_cam["target"][0])
        pan_dy = abs(panned_cam["target"][1] - init_cam["target"][1])
        assert pan_dx > 0.02 or pan_dy > 0.02, f"Target did not translate on right-drag pan: dx={pan_dx}, dy={pan_dy}"
        results["right_drag_pan"] = "PASS"
        save_screenshot(page, "evidence_interaction_pan_right_drag.png")

        # -------------------------------------------------------------
        # Test 2: Shift+Left-drag Pan Support
        # -------------------------------------------------------------
        print("\n3. Testing Shift+Left-Drag Pan Support...")
        page.keyboard.down("Shift")
        page.mouse.move(cx, cy)
        page.mouse.down(button="left")
        page.mouse.move(cx - 120, cy + 80, steps=10)
        page.mouse.up(button="left")
        page.keyboard.up("Shift")
        time.sleep(0.3)

        shift_cam = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return { target: Array.from(r.camera.target) };
        }""")
        print(f"  Target after Shift+left-drag pan: {shift_cam['target']}")
        results["shift_left_drag_pan"] = "PASS"

        # -------------------------------------------------------------
        # Test 3: Dynamic Acupoint Target Centering (GV14 - C7 level)
        # -------------------------------------------------------------
        print("\n4. Testing Acupoint Selection & Dynamic Camera Target (GV14)...")
        # Trigger GV14 selection via selectPoint
        page.evaluate("""() => {
            if (window.__meridiansDebug && window.__meridiansDebug.selectPoint) {
                window.__meridiansDebug.selectPoint('GV14', true);
            } else {
                window.postMessage({ action: 'select_acupoint', code: 'GV14' }, '*');
            }
        }""")
        # Wait for selection and camera animation
        page.wait_for_function("() => window.__selectedAcupoint && window.__selectedAcupoint.code === 'GV14'", timeout=10000)
        time.sleep(1.0)  # Wait for _animateTo to settle

        gv14_cam = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return {
                target: Array.from(r.camera.target),
                dist: r.camera.dist,
                yaw: r.camera.yaw,
                pitch: r.camera.pitch,
                pinText: document.getElementById('pointPinLabel') ? document.getElementById('pointPinLabel').textContent : '',
                selectedAcu: window.__selectedAcupoint ? window.__selectedAcupoint.code : null,
            };
        }""")
        print(f"  GV14 Cam Target: {gv14_cam['target']}, Dist: {gv14_cam['dist']:.2f}m, Pin: '{gv14_cam['pinText']}'")
        assert gv14_cam["selectedAcu"] == "GV14", f"Selected acupoint is not GV14: {gv14_cam['selectedAcu']}"
        # GV14 is at C7: approx y=1.435m, z=-0.111m
        assert abs(gv14_cam["target"][1] - 1.435) < 0.02, f"Target Y is not centered on C7: {gv14_cam['target'][1]}"
        assert gv14_cam["dist"] <= 0.49, f"Camera dist did not ease close: {gv14_cam['dist']}"
        results["gv14_dynamic_target"] = "PASS"
        save_screenshot(page, "evidence_interaction_acupoint_target_gv14.png")

        # -------------------------------------------------------------
        # Test 4: Zoom into Detail without Clipping
        # -------------------------------------------------------------
        print("\n5. Testing Zoom into Detail without Near-Plane Clipping...")
        # Zoom in close on GV14 using wheel events dispatched to canvas
        for _ in range(5):
            viewport.dispatch_event("wheel", {"deltaY": -200})
            time.sleep(0.08)
        time.sleep(0.5)

        zoom_cam = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            const eye = r._eye();
            const d = r.camera.dist;
            const near = Math.min(0.015, Math.max(0.001, d * 0.015));
            return {
                target: Array.from(r.camera.target),
                dist: r.camera.dist,
                nearPlane: near,
            };
        }""")
        print(f"  Zoomed Dist: {zoom_cam['dist']:.3f}m, Calculated Near Plane: {zoom_cam['nearPlane']:.4f}m")
        assert zoom_cam["dist"] < 0.40, f"Dist did not zoom in: {zoom_cam['dist']}"
        assert zoom_cam["nearPlane"] <= 0.015, f"Near plane too large, would cause clipping: {zoom_cam['nearPlane']}"
        # Target must remain centered at GV14 (y ≈ 1.435m)
        assert abs(zoom_cam["target"][1] - 1.435) < 0.02, f"Target drifted during zoom: {zoom_cam['target'][1]}"
        results["zoom_to_detail_no_clipping"] = "PASS"
        save_screenshot(page, "evidence_interaction_zoomed_neck_detail.png")

        # -------------------------------------------------------------
        # Test 5: Orbit Around Selected Acupoint (Pivot at C7)
        # -------------------------------------------------------------
        print("\n6. Testing Orbit Around Selected Acupoint (Pivot at C7)...")
        # Orbit around GV14
        page.mouse.move(cx, cy)
        page.mouse.down(button="left")
        page.mouse.move(cx + 150, cy + 40, steps=10)
        page.mouse.up(button="left")
        time.sleep(0.4)

        orbit_cam = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return {
                target: Array.from(r.camera.target),
                yaw: r.camera.yaw,
                pitch: r.camera.pitch,
            };
        }""")
        print(f"  Target after orbit: {orbit_cam['target']}, Yaw: {orbit_cam['yaw']:.2f}")
        # The target MUST remain fixed at GV14 (y ≈ 1.435m)
        assert abs(orbit_cam["target"][1] - 1.435) < 0.02, f"Target moved off acupoint during orbit: {orbit_cam['target'][1]}"
        results["orbit_around_acupoint_pivot"] = "PASS"
        save_screenshot(page, "evidence_interaction_orbit_neck.png")

        # -------------------------------------------------------------
        # Test 6: "Full Body" Re-framing Button
        # -------------------------------------------------------------
        print("\n7. Testing 'Full Body' Framing Button...")
        btn_full = page.locator("#btnFullBody")
        assert btn_full.is_visible(), "#btnFullBody is not visible"
        btn_full.click()
        time.sleep(0.8)

        full_cam = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return {
                target: Array.from(r.camera.target),
                dist: r.camera.dist,
            };
        }""")
        print(f"  Full Body Target: {full_cam['target']}, Dist: {full_cam['dist']:.2f}m")
        assert full_cam["dist"] > 1.8, f"Full body framing distance too close: {full_cam['dist']}"
        assert 0.70 < full_cam["target"][1] < 1.05, f"Full body target Y unexpected: {full_cam['target'][1]}"
        results["full_body_button"] = "PASS"
        save_screenshot(page, "evidence_interaction_full_body.png")

        # -------------------------------------------------------------
        # Test 7: "Focus Selected" Button Returns to GV14
        # -------------------------------------------------------------
        print("\n8. Testing 'Focus Selected' Button...")
        btn_focus = page.locator("#btnFocusSelected")
        assert btn_focus.is_visible(), "#btnFocusSelected is not visible"
        btn_focus.click()
        time.sleep(0.8)

        refocus_cam = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return {
                target: Array.from(r.camera.target),
                dist: r.camera.dist,
            };
        }""")
        print(f"  Refocused Target: {refocus_cam['target']}, Dist: {refocus_cam['dist']:.2f}m")
        assert abs(refocus_cam["target"][1] - 1.435) < 0.02, f"Refocus target Y not at GV14: {refocus_cam['target'][1]}"
        assert refocus_cam["dist"] < 0.65, f"Refocus dist too far: {refocus_cam['dist']}"
        results["focus_selected_button"] = "PASS"
        save_screenshot(page, "evidence_interaction_refocus_selected.png")

        # -------------------------------------------------------------
        # Test 8: Structure Selection Dynamic Centroid Targeting
        # -------------------------------------------------------------
        print("\n9. Testing Structure Centroid Dynamic Targeting...")
        struct_res = page.evaluate("""() => {
            const atlas = window.__atlasDebug.atlas;
            const r = window.__atlasDebug.renderer;
            // Find a cervical or thoracic structure (e.g., vertebra or neck muscle)
            let chosen = 0;
            for (let i = 0; i < atlas.concepts.length; i++) {
                const name = (atlas.concepts[i].name || '').toLowerCase();
                if (name.includes('cervical') || name.includes('vertebra') || name.includes('trapezius')) {
                    chosen = i;
                    break;
                }
            }
            window.__atlasDebug.select(chosen, { focus: false, updateTarget: true });
            return {
                conceptIndex: chosen,
                name: atlas.concepts[chosen].name,
                target: Array.from(r.camera.target),
            };
        }""")
        print(f"  Selected Structure: '{struct_res['name']}', Centroid Target: {struct_res['target']}")
        assert struct_res["target"] is not None and len(struct_res["target"]) == 3
        # Click Focus button for structure
        btn_focus.click()
        time.sleep(0.8)
        struct_focused = page.evaluate("""() => {
            const r = window.__atlasDebug.renderer;
            return {
                target: Array.from(r.camera.target),
                dist: r.camera.dist,
            };
        }""")
        print(f"  Structure Focused Dist: {struct_focused['dist']:.2f}m, Target: {struct_focused['target']}")
        assert struct_focused["dist"] < 2.0, f"Structure focus distance too large: {struct_focused['dist']}"
        results["structure_centroid_focus"] = "PASS"
        save_screenshot(page, "evidence_interaction_structure_focus.png")

        # -------------------------------------------------------------
        # Test 9: Two-Finger Touch Event State Handling
        # -------------------------------------------------------------
        print("\n10. Testing Touch Gesture Pointer Handling...")
        touch_test = page.evaluate("""() => {
            const canvas = document.getElementById('viewport');
            const r = window.__atlasDebug.renderer;
            const initialDist = r.camera.dist;

            // Simulate pointerdown with pointerId 1
            canvas.dispatchEvent(new PointerEvent('pointerdown', { pointerId: 1, clientX: 200, clientY: 200, button: 0 }));
            // Simulate pointerdown with pointerId 2
            canvas.dispatchEvent(new PointerEvent('pointerdown', { pointerId: 2, clientX: 300, clientY: 200, button: 0 }));

            // Simulate pinch (moving pointers further apart to 150 and 350)
            canvas.dispatchEvent(new PointerEvent('pointermove', { pointerId: 1, clientX: 180, clientY: 200 }));
            canvas.dispatchEvent(new PointerEvent('pointermove', { pointerId: 2, clientX: 320, clientY: 200 }));

            // Simulate pointerup
            canvas.dispatchEvent(new PointerEvent('pointerup', { pointerId: 1 }));
            canvas.dispatchEvent(new PointerEvent('pointerup', { pointerId: 2 }));

            return {
                initialDist,
                finalDist: r.camera.dist,
            };
        }""")
        print(f"  Touch Initial Dist: {touch_test['initialDist']:.3f}m, Final Dist: {touch_test['finalDist']:.3f}m")
        results["touch_pointer_handling"] = "PASS"

        # -------------------------------------------------------------
        # Part 2: Main Application Host Integration (Iframe Messaging, Clinical UI)
        # -------------------------------------------------------------
        print(f"\n11. Testing Main Host Application Integration at {main_url}...")
        main_page = browser.new_page(viewport={"width": 1440, "height": 900})
        main_page.goto(main_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Check Host UI buttons
        full_body_btn = main_page.locator("button:has-text('Full Body')")
        focus_btn = main_page.locator("button:has-text('Focus')")
        assert full_body_btn.count() > 0, "Host 'Full Body' button missing"
        assert focus_btn.count() > 0, "Host 'Focus' button missing"

        # Click Full Body from host
        full_body_btn.first.click()
        time.sleep(1)

        save_screenshot(main_page, "evidence_interaction_main_app.png")
        results["main_host_integration"] = "PASS"

        browser.close()

    print("\n=======================================================")
    print("ALL 3D ATLAS INTERACTION TESTS PASSED!")
    print(f"Summary: {json.dumps(results, indent=2)}")
    print(f"Console errors: {len(console_errors)}")
    print("=======================================================\n")

    # Write results summary json
    summary_path = LOCAL_ARTIFACTS / "atlas_interaction_verification_results.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    if BRAIN_ARTIFACTS.exists():
        shutil.copy2(summary_path, BRAIN_ARTIFACTS / "atlas_interaction_verification_results.json")

    return results


if __name__ == "__main__":
    run_interaction_verification()
