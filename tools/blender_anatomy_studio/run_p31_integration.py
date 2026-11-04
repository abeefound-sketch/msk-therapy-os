"""Runner script for Milestone P31: Cross-System Integration.
Exports CrossSystemExchangeBundle JSON and Markdown research report into evidence directory.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.blender_anatomy_studio.addon.web_atlas_adapter import WebAtlasAdapter

EVIDENCE_DIR = REPO_ROOT / "1docs" / "audits" / "P31" / "evidence"
BUNDLE_JSON_PATH = EVIDENCE_DIR / "p31_cross_system_bundle.json"
BUNDLE_MD_PATH = EVIDENCE_DIR / "p31_research_bundle.md"


def run_p31_integration():
    print("=" * 70)
    print("MSK-THERAPY-OS | MILESTONE P31: CROSS-SYSTEM INTEGRATION RUNNER")
    print("=" * 70)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    adapter = WebAtlasAdapter()

    print("[1/4] Building CrossSystemExchangeBundle...")
    bundle = adapter.build_exchange_bundle()

    print(f"  Bundle ID: {bundle.bundle_id}")
    print(f"  Release Scope: {bundle.release_scope}")
    print(f"  Assets count: {len(bundle.scene_assets)}")
    print(f"  Surface anchors count: {len(bundle.surface_anchors)}")
    print(f"  Motion frames count: {len(bundle.motion_sequence)}")
    print(f"  Knowledge links count: {len(bundle.knowledge_links)}")

    print("[2/4] Exporting bundle to JSON...")
    bundle.save(BUNDLE_JSON_PATH)
    json_bytes = BUNDLE_JSON_PATH.read_bytes()
    json_hash = hashlib.sha256(json_bytes).hexdigest()
    print(f"  Saved JSON: {BUNDLE_JSON_PATH} ({len(json_bytes):,} bytes)")
    print(f"  SHA-256: {json_hash}")

    print("[3/4] Generating and exporting Markdown research bundle...")
    md_content = adapter.export_research_bundle_markdown(bundle)
    BUNDLE_MD_PATH.write_text(md_content, encoding="utf-8")
    md_bytes = BUNDLE_MD_PATH.read_bytes()
    md_hash = hashlib.sha256(md_bytes).hexdigest()
    print(f"  Saved Markdown: {BUNDLE_MD_PATH} ({len(md_bytes):,} bytes)")
    print(f"  SHA-256: {md_hash}")

    print("[4/4] Validating bundle reload from disk...")
    reloaded_bundle = adapter.build_exchange_bundle().load(BUNDLE_JSON_PATH)
    assert reloaded_bundle.bundle_id == bundle.bundle_id
    assert reloaded_bundle.release_scope == "ENGINEERING_RESEARCH_ONLY"
    assert len(reloaded_bundle.surface_anchors) == len(bundle.surface_anchors)
    print("  Round-trip JSON serialization & verification: PASSED")

    print("=" * 70)
    print("P31 CROSS-SYSTEM INTEGRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_p31_integration()
