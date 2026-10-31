"""MSK-Therapy-OS - 1-Click Interactive Launcher.

Starts the local MSK-Therapy-OS server and automatically launches the default web browser
directly into the 3D Musculoskeletal Education Studio.
"""

import sys
import os
import socket
import webbrowser
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from msk_therapy_os.server import create_server, DEFAULT_DB


def find_free_port(preferred_port: int = 8080) -> int:
    """Find an available TCP port, starting with preferred_port."""
    for port in range(preferred_port, preferred_port + 50):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError("Could not find an open port in range 8080-8130.")


def print_banner(host: str, port: int) -> None:
    print(r"""
========================================================================
   __  __ ____  _  __       _____ _                               
  |  \/  / ___|| |/ /      |_   _| |__   ___ _ __ __ _ _ __  _   _ 
  | |\/| \___ \| ' / _____   | | | '_ \ / _ \ '__/ _` | '_ \| | | |
  | |  | |___) | . \|_____|  | | | | | |  __/ | | (_| | |_) | |_| |
  |_|  |_|____/|_|\_\        |_| |_| |_|\___|_|  \__,_| .__/ \__, |
                                                      |_|    |___/ 
                     MSK-THERAPY-OS · STUDIO
========================================================================
    """)
    print(f"  * 3D Education Studio: http://{host}:{port}/education/?v=p16")
    print(f"  * 3D Meridian Atlas:   http://{host}:{port}/atlas/")
    print(f"  * Clinical Dashboard:  http://{host}:{port}/")
    print("------------------------------------------------------------------------")
    print("  Status: RUNNING (Offline, Zero-CDN, Full 3D WebGL2 Support)")
    print("  Closing this window will stop the application server.")
    print("========================================================================")
    print("")


def main() -> None:
    host = "127.0.0.1"
    port = find_free_port(8080)
    db_file = PROJECT_ROOT / "msk_therapy_os.sqlite3"

    server = create_server(db_path=str(db_file), host=host, port=port)
    print_banner(host, port)

    target_url = f"http://{host}:{port}/education/?v=p16"
    print(f"[i] Đang mở trình duyệt vào: {target_url} ...")

    # Launch browser after a short pause
    try:
        webbrowser.open(target_url)
    except Exception as e:
        print(f"[!] Không thể tự mở trình duyệt ({e}). Vui lòng truy cập thủ công {target_url}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[i] Đang đóng máy chủ MSK-Therapy-OS...")
    finally:
        server.server_close()
        print("[v] Đã dừng hoàn toàn.")


if __name__ == "__main__":
    main()
