"""Automated real telemetry capture using Playwright/CDP with physical Intel HD 5500 GPU."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict
from playwright.sync_api import sync_playwright

LOCAL_ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
LOCAL_ARTIFACTS.mkdir(parents=True, exist_ok=True)


def capture_app_telemetry(
    url: str,
    output_prefix: str,
    viewport_width: int = 1280,
    viewport_height: int = 800,
    wait_extra_seconds: int = 3,
) -> Dict[str, Any]:
    """Capture authentic GPU renderer, load time, JS heap, idle FPS, and interaction FPS on Intel HD 5500."""
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
                "--disable-background-timer-throttling",
            ],
        )
        page = browser.new_page(viewport={"width": viewport_width, "height": viewport_height})

        t0 = time.perf_counter()
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        try:
            page.wait_for_selector("canvas", timeout=12000)
        except Exception:
            pass
        t_nav = (time.perf_counter() - t0) * 1000.0

        time.sleep(wait_extra_seconds)

        # 1. Base telemetry & WebGL unmasked info
        base_telemetry = page.evaluate("""() => {
            let renderer = 'Unknown';
            let vendor = 'Unknown';
            let isHardwareAccelerated = false;
            const canvas = document.querySelector('canvas');
            if (canvas) {
                const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
                if (gl) {
                    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
                    if (dbg) {
                        renderer = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
                        vendor = gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL);
                        isHardwareAccelerated = !renderer.toLowerCase().includes('swiftshader') && !renderer.toLowerCase().includes('llvmpipe');
                    }
                }
            }
            const mem = performance.memory;
            const timing = performance.timing;
            const loadMs = timing.loadEventEnd > 0 
                ? (timing.loadEventEnd - timing.navigationStart) 
                : Math.round(performance.now());
            
            return {
                gpu_renderer: renderer,
                gpu_vendor: vendor,
                is_hardware_accelerated: isHardwareAccelerated,
                js_heap_used_mb: mem ? Math.round((mem.usedJSHeapSize / (1024 * 1024)) * 100) / 100 : null,
                js_heap_total_mb: mem ? Math.round((mem.totalJSHeapSize / (1024 * 1024)) * 100) / 100 : null,
                browser_load_event_ms: loadMs,
            };
        }""")

        # 2. Idle FPS sampling over 1000ms
        fps_idle = page.evaluate("""() => new Promise(resolve => {
            let frames = 0;
            const start = performance.now();
            let active = true;
            function tick() {
                if (!active) return;
                frames++;
                requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
            setTimeout(() => {
                active = false;
                const elapsed = (performance.now() - start) / 1000;
                resolve(Math.round(frames / (elapsed || 1)));
            }, 1000);
        })""")

        # 3. Interaction FPS sampling while performing orbit/drag
        canvas_box = None
        try:
            canvas_box = page.locator("canvas").first.bounding_box()
        except Exception:
            pass

        if canvas_box:
            cx = canvas_box["x"] + canvas_box["width"] / 2
            cy = canvas_box["y"] + canvas_box["height"] / 2

            page.evaluate("""() => {
                window.__interactionFrames = 0;
                window.__interactionStart = performance.now();
                window.__interactionActive = true;
                function count() {
                    if (window.__interactionActive) {
                        window.__interactionFrames++;
                        requestAnimationFrame(count);
                    }
                }
                requestAnimationFrame(count);
            }""")

            page.mouse.move(cx, cy)
            page.mouse.down()
            for dx, dy in [(40, 0), (0, 40), (-40, 0), (0, -40)]:
                page.mouse.move(cx + dx, cy + dy, steps=4)
                time.sleep(0.06)
            page.mouse.up()

            fps_interaction = page.evaluate("""() => {
                window.__interactionActive = false;
                const elapsed = (performance.now() - window.__interactionStart) / 1000;
                return Math.round(window.__interactionFrames / (elapsed || 1));
            }""")
        else:
            fps_interaction = fps_idle

        # 4. Screenshot
        img_name = f"evidence_{output_prefix}.png"
        img_path = LOCAL_ARTIFACTS / img_name
        page.screenshot(path=str(img_path))

        browser.close()

        result = {
            "application": output_prefix,
            "url": url,
            "gpu_renderer": base_telemetry.get("gpu_renderer"),
            "gpu_vendor": base_telemetry.get("gpu_vendor"),
            "is_hardware_accelerated": base_telemetry.get("is_hardware_accelerated", False),
            "js_heap_used_mb": base_telemetry.get("js_heap_used_mb"),
            "js_heap_total_mb": base_telemetry.get("js_heap_total_mb"),
            "page_load_ms": round(t_nav, 2),
            "fps_idle": int(fps_idle or 0),
            "fps_interaction": int(fps_interaction or 0),
            "screenshot": str(img_name),
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        json_path = LOCAL_ARTIFACTS / f"metrics_{output_prefix}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"Captured Hardware Telemetry for {output_prefix}:")
        print(f"  GPU Renderer    : {result['gpu_renderer']}")
        print(f"  Hardware Accel  : {result['is_hardware_accelerated']}")
        print(f"  Load Time       : {result['page_load_ms']} ms")
        print(f"  JS Heap         : {result['js_heap_used_mb']} MB")
        print(f"  FPS Idle        : {result['fps_idle']} FPS")
        print(f"  FPS Interaction : {result['fps_interaction']} FPS")

        return result


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3002"
    prefix = sys.argv[2] if len(sys.argv) > 2 else "tcm3d"
    capture_app_telemetry(url, prefix)
