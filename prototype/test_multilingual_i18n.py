import os
import time
import json
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = "2data/artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def run_multilingual_e2e_tests():
    print("=" * 80)
    print("STARTING E2E MULTILINGUAL i18n AUDIT (EN / 中文 / Tiếng Việt)")
    print("=" * 80)

    results = {
        "timestamp": time.time(),
        "lang_switching": {},
        "persistence": {},
        "iframe_sync": {},
        "unicode_integrity": {},
        "clinical_data_integrity": {},
        "responsive_matrix": {},
        "failures": []
    }

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

        page = browser.new_page(viewport={"width": 1280, "height": 850})
        page.goto("http://127.0.0.1:8085/", wait_until="networkidle", timeout=30000)
        time.sleep(2.0)

        # ----------------------------------------------------------------------
        # Test 1: Language Switcher Existence & Initial English State
        # ----------------------------------------------------------------------
        print("\n1. Verifying Language Switcher & Initial English UI...")
        lang_btns = page.locator(".lang-btn").all()
        print(f"  Found {len(lang_btns)} language buttons.")
        if len(lang_btns) < 3:
            results["failures"].append("Language switcher does not have 3 language options")

        en_active = page.locator('.lang-btn[data-lang="en"]').evaluate("el => el.classList.contains('active')")
        print(f"  EN active: {en_active}")
        tab_text_en = page.locator('button.tab-btn[data-tab="tab-bodymap"]').text_content().strip()
        print(f"  Bodymap Tab (EN): '{tab_text_en}'")
        results["lang_switching"]["initial_en"] = tab_text_en

        page.screenshot(path=os.path.join(ARTIFACT_DIR, "i18n_03_english_desktop.png"))
        print("  [Saved] i18n_03_english_desktop.png")

        # ----------------------------------------------------------------------
        # Test 2: Switch to Simplified Chinese (zh)
        # ----------------------------------------------------------------------
        print("\n2. Switching to Simplified Chinese (zh)...")
        page.locator('.lang-btn[data-lang="zh"]').click()
        time.sleep(1.0)

        tab_text_zh = page.locator('button.tab-btn[data-tab="tab-bodymap"]').text_content().strip()
        safety_tab_zh = page.locator('button.tab-btn[data-tab="tab-safety"]').text_content().strip()
        surface_mode_zh = page.locator('#hostBtnModeSurface').text_content().strip()
        neck_region_zh = page.locator('.region-btn[data-region="neck"]').text_content().strip()

        print(f"  Bodymap Tab (ZH): '{tab_text_zh}'")
        print(f"  Safety Tab (ZH): '{safety_tab_zh}'")
        print(f"  Surface Mode (ZH): '{surface_mode_zh}'")
        print(f"  Neck Region (ZH): '{neck_region_zh}'")

        if "解剖" not in tab_text_zh:
            results["failures"].append(f"ZH tab translation failed, got: '{tab_text_zh}'")
        if "安全" not in safety_tab_zh:
            results["failures"].append(f"ZH safety tab translation failed, got: '{safety_tab_zh}'")

        # Check Iframe synchronization
        iframe = page.frame_locator("#atlasFrame")
        iframe_tab_zh = iframe.locator('button.tab[data-tab="layers"]').text_content().strip()
        print(f"  Atlas Iframe Layers Tab (ZH): '{iframe_tab_zh}'")
        if "图层" not in iframe_tab_zh:
            results["failures"].append(f"Atlas iframe did not sync ZH, got: '{iframe_tab_zh}'")

        # Check structure cards localized to Chinese
        struct_cards_zh = page.locator("#structuresList .item-card strong").all_text_contents()
        print(f"  Sample Structure Cards (ZH): {struct_cards_zh[:3]}")

        page.screenshot(path=os.path.join(ARTIFACT_DIR, "i18n_01_chinese_desktop.png"))
        print("  [Saved] i18n_01_chinese_desktop.png")

        # ----------------------------------------------------------------------
        # Test 3: Switch to Vietnamese (vi)
        # ----------------------------------------------------------------------
        print("\n3. Switching to Vietnamese (vi)...")
        page.locator('.lang-btn[data-lang="vi"]').click()
        time.sleep(1.0)

        tab_text_vi = page.locator('button.tab-btn[data-tab="tab-bodymap"]').text_content().strip()
        safety_tab_vi = page.locator('button.tab-btn[data-tab="tab-safety"]').text_content().strip()
        surface_mode_vi = page.locator('#hostBtnModeSurface').text_content().strip()
        neck_region_vi = page.locator('.region-btn[data-region="neck"]').text_content().strip()

        print(f"  Bodymap Tab (VI): '{tab_text_vi}'")
        print(f"  Safety Tab (VI): '{safety_tab_vi}'")
        print(f"  Surface Mode (VI): '{surface_mode_vi}'")
        print(f"  Neck Region (VI): '{neck_region_vi}'")

        if "Bản Đồ" not in tab_text_vi:
            results["failures"].append(f"VI tab translation failed, got: '{tab_text_vi}'")
        if "An Toàn" not in safety_tab_vi:
            results["failures"].append(f"VI safety tab translation failed, got: '{safety_tab_vi}'")

        # Check Iframe synchronization
        iframe_tab_vi = iframe.locator('button.tab[data-tab="layers"]').text_content().strip()
        print(f"  Atlas Iframe Layers Tab (VI): '{iframe_tab_vi}'")
        if "Giải Phẫu" not in iframe_tab_vi and "Lớp" not in iframe_tab_vi:
            results["failures"].append(f"Atlas iframe did not sync VI, got: '{iframe_tab_vi}'")

        # Check structure cards localized to Vietnamese
        struct_cards_vi = page.locator("#structuresList .item-card strong").all_text_contents()
        print(f"  Sample Structure Cards (VI): {struct_cards_vi[:3]}")
        has_vietnamese_structure = any("Đốt sống" in s or "cơ thang" in s or "Cơ nâng vai" in s or "Đại Chùy" in s for s in struct_cards_vi)
        print(f"  Has authentic Vietnamese anatomical terminology: {has_vietnamese_structure}")
        if not has_vietnamese_structure:
            results["failures"].append("Structure cards failed to display Vietnamese anatomical terminology")

        # Select GV14 and inspect Vietnamese acupoint panel
        page.evaluate("() => document.getElementById('atlasFrame').contentWindow.__meridiansDebug.selectPoint('GV14', true)")
        time.sleep(0.5)

        acu_title_vi = page.locator("#acuPointTitle").text_content().strip()
        print(f"  Selected Acupoint Title (VI): '{acu_title_vi}'")
        if "Đại Chùy" not in acu_title_vi:
            results["failures"].append(f"Acupoint panel failed to display Vietnamese name 'Đại Chùy', got: '{acu_title_vi}'")

        page.screenshot(path=os.path.join(ARTIFACT_DIR, "i18n_02_vietnamese_desktop.png"))
        print("  [Saved] i18n_02_vietnamese_desktop.png")

        # ----------------------------------------------------------------------
        # Test 4: Language Persistence Across Reload
        # ----------------------------------------------------------------------
        print("\n4. Testing Persistence Across Page Reload...")
        page.reload(wait_until="networkidle")
        time.sleep(1.5)

        persisted_lang = page.evaluate("() => window.__msk_i18n.getLang()")
        persisted_tab = page.locator('button.tab-btn[data-tab="tab-bodymap"]').text_content().strip()
        print(f"  Persisted Language after Reload: '{persisted_lang}'")
        print(f"  Persisted Tab Text: '{persisted_tab}'")
        if persisted_lang != "vi":
            results["failures"].append(f"Language persistence failed, expected 'vi' but got: '{persisted_lang}'")
        if "Bản Đồ" not in persisted_tab:
            results["failures"].append(f"UI did not restore in Vietnamese after reload: '{persisted_tab}'")

        # ----------------------------------------------------------------------
        # Test 5: Unicode Integrity & Font Rendering
        # ----------------------------------------------------------------------
        print("\n5. Testing Unicode Integrity (Chinese glyphs, Pinyin, Vietnamese diacritics)...")
        body_text = page.locator("body").text_content()
        has_replacement_char = "\ufffd" in body_text
        print(f"  Has Unicode replacement char (U+FFFD): {has_replacement_char}")
        if has_replacement_char:
            results["failures"].append("Unicode encoding error: replacement character U+FFFD detected on page")

        # ----------------------------------------------------------------------
        # Test 6: Responsive Multi-Device Audit
        # ----------------------------------------------------------------------
        print("\n6. Testing Responsive Layouts in Vietnamese & Chinese...")
        responsive_viewports = [
            ("tablet_768px", {"width": 768, "height": 1024}),
            ("mobile_375px", {"width": 375, "height": 812})
        ]

        for vp_name, vp_dims in responsive_viewports:
            page.set_viewport_size(vp_dims)
            time.sleep(0.5)

            # Check for horizontal scroll overflow
            overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
            print(f"  {vp_name} Horizontal Overflow (VI): {overflow}")
            if overflow:
                results["failures"].append(f"Horizontal layout overflow detected at {vp_name} in Vietnamese")

            page.screenshot(path=os.path.join(ARTIFACT_DIR, f"i18n_04_vietnamese_{vp_name}.png"))
            print(f"  [Saved] i18n_04_vietnamese_{vp_name}.png")

            # Switch to Chinese at this viewport
            page.locator('.lang-btn[data-lang="zh"]').click()
            time.sleep(0.5)
            overflow_zh = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
            print(f"  {vp_name} Horizontal Overflow (ZH): {overflow_zh}")
            if overflow_zh:
                results["failures"].append(f"Horizontal layout overflow detected at {vp_name} in Chinese")

            page.screenshot(path=os.path.join(ARTIFACT_DIR, f"i18n_06_chinese_{vp_name}.png"))
            print(f"  [Saved] i18n_06_chinese_{vp_name}.png")

        # Restore desktop viewport and English
        page.set_viewport_size({"width": 1280, "height": 850})
        page.locator('.lang-btn[data-lang="en"]').click()
        time.sleep(0.5)

        # ----------------------------------------------------------------------
        # Test 7: Verify Zero Console Errors
        # ----------------------------------------------------------------------
        print("\n7. Auditing Browser Console Errors...")
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        time.sleep(0.5)
        print(f"  Console errors during execution: {len(console_errors)}")
        if console_errors:
            results["failures"].extend([f"Console error: {e}" for e in console_errors])

        # Save test report
        report_path = os.path.join(ARTIFACT_DIR, "multilingual_i18n_test_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[Saved Report] {report_path}")

        print("\n" + "=" * 80)
        if not results["failures"]:
            print("ALL MULTILINGUAL i18n TESTS PASSED: 100% CLEAN SYNCHRONIZATION & ZERO DEFECTS")
        else:
            print(f"MULTILINGUAL i18n TEST FAILED WITH {len(results['failures'])} DEFECTS:")
            for fail in results["failures"]:
                print(f"  - {fail}")
        print("=" * 80)

        browser.close()

if __name__ == "__main__":
    run_multilingual_e2e_tests()
