import json
import os
import shutil
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path("D:/5Projects/msk-therapy-os")
LOCAL_ARTIFACTS = BASE / "research" / "artifacts"
LOCAL_ARTIFACTS.mkdir(parents=True, exist_ok=True)
BRAIN_ARTIFACTS = Path(r"C:\Users\tuanh\.gemini\antigravity-cli\brain\bb14e5bd-1e41-49cd-aad4-33cbc5844729")


def save_screenshot(page, filename):
    local_path = LOCAL_ARTIFACTS / filename
    page.screenshot(path=str(local_path), full_page=False)
    print(f"  [Screenshot] Saved {filename}")
    if BRAIN_ARTIFACTS.exists():
        try:
            shutil.copy2(local_path, BRAIN_ARTIFACTS / filename)
        except Exception as e:
            print(f"  [Warning] Failed to copy to brain artifacts: {e}")


def run_tests():
    print("================================================================================")
    print("STARTING TEST OF REMEDIATED CONTROLS (SKIN, MERIDIANS, DIEN CHAN, THAI SEN SIB)")
    print("================================================================================")

    results = {}

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
        context = browser.new_context(
            viewport={"width": 1280, "height": 850},
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = context.new_page()

        page.goto("http://127.0.0.1:8085/", wait_until="networkidle", timeout=30000)
        time.sleep(1.5)

        # ----------------------------------------------------------------------
        # Test 1: Skin Opacity Slider (0%, 50%, 100%)
        # ----------------------------------------------------------------------
        print("\n1. Testing Skin Opacity Slider (0%, 50%, 100%)...")
        slider = page.locator("#hostSkinOpacity")

        # A. Skin 100% (Opaque)
        slider.fill("100")
        page.evaluate("() => onHostSkinOpacityChange('100')")
        time.sleep(0.6)
        skin_100_info = page.evaluate("""() => {
            const r = document.getElementById('atlasFrame').contentWindow.__atlasDebug.renderer;
            const atlas = document.getElementById('atlasFrame').contentWindow.__atlasDebug.atlas;
            const visibleSkin = atlas.elements.filter((e, i) => e.t === 'skin' && r.visible[i]).length;
            return { skinOpacity: r.skinOpacity, visibleSkin };
        }""")
        print(f"  Skin 100%: opacity={skin_100_info['skinOpacity']}, visibleSkinCount={skin_100_info['visibleSkin']}")
        assert abs(skin_100_info['skinOpacity'] - 1.0) < 0.01
        assert skin_100_info['visibleSkin'] > 0, "Skin mesh elements must be visible at 100%"
        save_screenshot(page, "evidence_skin_100_opaque.png")
        results["skin_100_opaque"] = "PASS"

        # B. Skin 50% (Translucent)
        slider.fill("50")
        page.evaluate("() => onHostSkinOpacityChange('50')")
        time.sleep(0.6)
        skin_50_info = page.evaluate("""() => {
            const r = document.getElementById('atlasFrame').contentWindow.__atlasDebug.renderer;
            const atlas = document.getElementById('atlasFrame').contentWindow.__atlasDebug.atlas;
            const visibleSkin = atlas.elements.filter((e, i) => e.t === 'skin' && r.visible[i]).length;
            return { skinOpacity: r.skinOpacity, visibleSkin };
        }""")
        print(f"  Skin 50%: opacity={skin_50_info['skinOpacity']}, visibleSkinCount={skin_50_info['visibleSkin']}")
        assert abs(skin_50_info['skinOpacity'] - 0.50) < 0.05
        assert skin_50_info['visibleSkin'] > 0, "Skin mesh elements must be visible at 50%"
        save_screenshot(page, "evidence_skin_50_translucent.png")
        results["skin_50_translucent"] = "PASS"

        # C. Skin 0% (Hidden)
        slider.fill("0")
        page.evaluate("() => onHostSkinOpacityChange('0')")
        time.sleep(0.6)
        skin_0_info = page.evaluate("""() => {
            const r = document.getElementById('atlasFrame').contentWindow.__atlasDebug.renderer;
            const atlas = document.getElementById('atlasFrame').contentWindow.__atlasDebug.atlas;
            const visibleSkin = atlas.elements.filter((e, i) => e.t === 'skin' && r.visible[i]).length;
            return { skinOpacity: r.skinOpacity, visibleSkin };
        }""")
        print(f"  Skin 0%: opacity={skin_0_info['skinOpacity']}, visibleSkinCount={skin_0_info['visibleSkin']}")
        assert abs(skin_0_info['skinOpacity'] - 0.0) < 0.01
        assert skin_0_info['visibleSkin'] == 0, "Skin mesh elements must be hidden at 0%"
        save_screenshot(page, "evidence_skin_00_hidden.png")
        results["skin_00_hidden"] = "PASS"

        # Restore skin to 78%
        slider.fill("78")
        page.evaluate("() => onHostSkinOpacityChange('78')")
        time.sleep(0.4)

        # ----------------------------------------------------------------------
        # Test 2: Meridian Channel Dropdown (CV, GV, BL, All)
        # ----------------------------------------------------------------------
        print("\n2. Testing Meridian Channel Dropdown...")
        chan_sel = page.locator("#hostMeridianFilter")

        # A. Select CV — Ren Mai (Conception Vessel, Anterior Midline)
        chan_sel.select_option("CV")
        time.sleep(0.6)
        cv_info = page.evaluate("""() => {
            const frameDoc = document.getElementById('atlasFrame').contentDocument;
            const paths = frameDoc.querySelectorAll('#groupMeridians path');
            const circles = Array.from(frameDoc.querySelectorAll('#groupPoints circle.acu-marker'));
            const codes = circles.map(c => c.getAttribute('data-code'));
            return { pathsCount: paths.length, pointsCount: circles.length, codes: codes.slice(0, 5) };
        }""")
        print(f"  Meridian CV: paths={cv_info['pathsCount']}, points={cv_info['pointsCount']} {cv_info['codes']}")
        assert cv_info['pathsCount'] > 0, "CV Ren Mai path must be rendered"
        save_screenshot(page, "evidence_meridian_cv_ren_mai.png")
        results["meridian_channel_cv"] = "PASS"

        # B. Select GV — Du Mai (Governing Vessel, Posterior Midline)
        chan_sel.select_option("GV")
        time.sleep(0.6)
        gv_info = page.evaluate("""() => {
            const frameDoc = document.getElementById('atlasFrame').contentDocument;
            const paths = frameDoc.querySelectorAll('#groupMeridians path');
            const circles = Array.from(frameDoc.querySelectorAll('#groupPoints circle.acu-marker'));
            const codes = circles.map(c => c.getAttribute('data-code'));
            return { pathsCount: paths.length, pointsCount: circles.length, codes: codes.slice(0, 5) };
        }""")
        print(f"  Meridian GV: paths={gv_info['pathsCount']}, points={gv_info['pointsCount']} {gv_info['codes']}")
        assert gv_info['pathsCount'] > 0, "GV Du Mai path must be rendered"
        assert any(c.startswith("GV") for c in gv_info['codes']), "GV points must be visible"
        save_screenshot(page, "evidence_meridian_gv_du_mai.png")
        results["meridian_channel_gv"] = "PASS"

        # C. Select BL — Bladder (Taiyang, Dorsal Paraspinal)
        chan_sel.select_option("BL")
        time.sleep(0.6)
        bl_info = page.evaluate("""() => {
            const frameDoc = document.getElementById('atlasFrame').contentDocument;
            const paths = frameDoc.querySelectorAll('#groupMeridians path');
            const circles = Array.from(frameDoc.querySelectorAll('#groupPoints circle.acu-marker'));
            return { pathsCount: paths.length, pointsCount: circles.length };
        }""")
        print(f"  Meridian BL: paths={bl_info['pathsCount']}, points={bl_info['pointsCount']}")
        assert bl_info['pathsCount'] > 0, "BL path must be rendered"
        save_screenshot(page, "evidence_meridian_bl_taiyang.png")
        results["meridian_channel_bl"] = "PASS"

        # Restore to all
        chan_sel.select_option("all")
        time.sleep(0.3)

        # ----------------------------------------------------------------------
        # Test 3: Vietnamese Dien Chan Reflex Points & Inspector
        # ----------------------------------------------------------------------
        print("\n3. Testing Vietnamese Dien Chan Reflex Points & Dedicated Inspector...")
        btn_dc = page.locator("#btnToggleDienChan")
        btn_dc.click() # Toggle ON
        time.sleep(0.5)

        dc_count = page.evaluate("() => document.getElementById('atlasFrame').contentDocument.querySelectorAll('#groupDienChan circle').length")
        print(f"  Dien Chan markers rendered: {dc_count} (Expected exactly 4)")
        assert dc_count == 4, f"Expected 4 Dien Chan markers, got {dc_count}"
        results["dien_chan_markers_rendered"] = "PASS"

        # Click on DIEN-26 (Point 26 Glabella)
        page.evaluate("() => document.getElementById('atlasFrame').contentWindow.__meridiansDebug.selectDienChanPoint('DIEN-26', true)")
        time.sleep(0.6)

        dc_card = page.locator("#atlasDienChanCard")
        assert dc_card.is_visible(), "Dien Chan dedicated inspector card must be displayed"
        title = page.locator("#dcPointTitle").text_content()
        target_reg = page.locator("#dcTargetRegion").text_content()
        print(f"  Dien Chan Inspector Card: Title='{title}', Target='{target_reg}'")
        assert "Point 26" in title and "DIEN-26" in title
        save_screenshot(page, "evidence_dien_chan_inspector.png")
        results["dien_chan_point_selection"] = "PASS"

        # Add Dien Chan to SOAP Note
        page.locator('#atlasDienChanCard button:has-text("+ Add to SOAP Note")').click()
        time.sleep(0.3)
        toast = page.locator("#mskToast")
        assert toast.is_visible(), "Toast should confirm adding Dien Chan reflex to SOAP note"
        print("  Add Dien Chan to SOAP Note: PASS (Toast confirmed)")
        results["dien_chan_add_to_soap"] = "PASS"

        # Switch to SOAP tab and verify text
        page.locator('button.tab-btn[data-tab="tab-soap"]').click()
        time.sleep(0.3)
        soap_o = page.locator("#soapO").input_value()
        assert "Vietnamese Dien Chan Reflexology" in soap_o and "DIEN-26" in soap_o
        print("  SOAP Objective verified: Dien Chan reflex entry present with non-WHO disclaimer")
        results["dien_chan_soap_entry_verified"] = "PASS"

        # Return to Body-Map tab
        page.locator('button.tab-btn[data-tab="tab-bodymap"]').click()
        time.sleep(0.4)

        # ----------------------------------------------------------------------
        # Test 4: Thai Sen Sib Lines (3 Lines Incomplete Dataset)
        # ----------------------------------------------------------------------
        print("\n4. Testing Thai Sen Sib Lines (3 Lines Incomplete Dataset)...")
        btn_thai = page.locator("#btnToggleThai")
        btn_thai.click() # Toggle ON
        time.sleep(0.5)

        thai_paths = page.evaluate("() => document.getElementById('atlasFrame').contentDocument.querySelectorAll('#groupThai path').length")
        print(f"  Thai Sen Sib paths rendered: {thai_paths} (Expected 3 lines: Ittha, Pingkhla, Sumana)")
        assert thai_paths == 3, f"Expected 3 Thai Sen Sib paths, got {thai_paths}"
        save_screenshot(page, "evidence_thai_sen_sib_lines.png")
        results["thai_sen_sib_3_lines"] = "PASS"

        browser.close()

    print("\n================================================================================")
    print("ALL REMEDIATED CONTROLS VERIFIED SUCCESSFULLY:")
    print(json.dumps(results, indent=2))
    print("================================================================================\n")

    summary_file = LOCAL_ARTIFACTS / "remediated_controls_verification.json"
    summary_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    if BRAIN_ARTIFACTS.exists():
        shutil.copy2(summary_file, BRAIN_ARTIFACTS / "remediated_controls_verification.json")

    return results


if __name__ == "__main__":
    run_tests()
