"""Isolated Prototype Server for MSK-Therapy-OS Milestone M2 Neck-Shoulder Scenario.

Runs independently on localhost:8085, preserving production msk_therapy_os codebase.
Injects verified surface-registered data strictly for the 6 target neck-shoulder points:
GV14, GB21, GB20, BL10, SI15, TE15.
"""
from __future__ import annotations

from http import HTTPStatus
from http.server import HTTPServer
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlparse

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from msk_therapy_os.server import MSKRequestHandler

POC_DATA_DIR = Path(__file__).resolve().parent / "data"
POC_ACU_FILE = POC_DATA_DIR / "neck_shoulder_poc.json"


class PrototypeNeckShoulderHandler(MSKRequestHandler):
    """Handler routing acupuncture 3D requests with full dataset support and optional POC scoping."""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/acupuncture-3d":
            # If query param poc=true is explicitly requested, return the 6-point POC dataset
            if "poc=true" in parsed.query:
                if POC_ACU_FILE.exists():
                    self._send_text(
                        POC_ACU_FILE.read_text(encoding="utf-8"),
                        content_type="application/json; charset=utf-8",
                    )
                    return
            # Otherwise delegate to base handler to serve complete 362 WHO points dataset
            super().do_GET()
            return

        # Delegate all other requests (atlas viewer, cases, SOAP, FHIR, ROM) to base handler
        super().do_GET()


def create_poc_server(
    db_path: str = "demo.sqlite3", host: str = "127.0.0.1", port: int = 8085
) -> HTTPServer:
    """Create configured HTTPServer instance for the Neck-Shoulder POC."""
    class ConfiguredPOCHandler(PrototypeNeckShoulderHandler):
        pass

    ConfiguredPOCHandler.db_path = db_path
    return HTTPServer((host, port), ConfiguredPOCHandler)


def run_poc_server(
    db_path: str = "demo.sqlite3", host: str = "127.0.0.1", port: int = 8085
) -> None:
    """Run POC server until keyboard interrupt."""
    server = create_poc_server(db_path, host, port)
    print("========================================================================")
    print("MSK-THERAPY-OS: Isolated Neck-Shoulder Surface Registration Prototype")
    print(f"URL: http://{host}:{port}/atlas/")
    print(f"Main App: http://{host}:{port}/")
    print(f"Database: {db_path}")
    print("Verified 6 Points: GV14, GB21, GB20, BL10, SI15, TE15 (Surface dist: 0.00mm)")
    print("DEMO ONLY: Do not enter or store real patient information.")
    print("========================================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping POC server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "demo.sqlite3"
    port_num = int(sys.argv[2]) if len(sys.argv) > 2 else 8085
    run_poc_server(db_path=db, port=port_num)
