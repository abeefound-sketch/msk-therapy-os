"""Headless CLI Runner for Blender Anatomical Studio.
Automates Blender execution, headless pipeline runs, roundtrip verifications, and evidence generation.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
WORKSPACE_DIR = Path(__file__).resolve().parents[2]

def find_blender() -> str:
    """Find Blender 3.6 executable on the system."""
    if Path(BLENDER_EXE).exists():
        return BLENDER_EXE
    # Check PATH
    import shutil
    p = shutil.which("blender")
    if p:
        return p
    raise FileNotFoundError("Blender executable not found at standard path or on PATH.")

def run_blender_script(script_path: str, script_args: list = None) -> Tuple[int, str]:
    """Execute a python script inside Blender in headless mode."""
    blender = find_blender()
    cmd = [blender, "--background", "--python", script_path]
    if script_args:
        cmd.append("--")
        cmd.extend(script_args)
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    return proc.returncode, proc.stdout

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MSK Blender Anatomical Studio CLI Runner")
    parser.add_argument("--action", choices=["verify-blender", "run-poc"], default="verify-blender")
    args = parser.parse_args()

    if args.action == "verify-blender":
        blender = find_blender()
        print(f"Blender found at: {blender}")
        res = subprocess.run([blender, "--version"], capture_output=True, text=True)
        print(res.stdout)
