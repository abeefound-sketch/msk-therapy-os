"""Audit script to inspect annotations, polylines, and layer counts in atlas.json and sandbox_p21_annotations.json."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 1. Audit sandbox_p21_annotations.json
annot_path = REPO_ROOT / "knowledge_vault" / "sandbox_p21_annotations.json"
if annot_path.exists():
    data = json.loads(annot_path.read_text(encoding="utf-8"))
    annots = data.get("annotations", [])
    polys = data.get("polylines", [])
    print(f"=== ANNOTATIONS AUDIT ({len(annots)} items) ===")
    for i, a in enumerate(annots):
        target = a.get("anatomical_target", {})
        print(f"[{i+1}] ID: {a.get('annotation_id')} | Code: {a.get('standard_code')} | Label: {a.get('label')} | Struct: {target.get('structure_name')} ({target.get('mesh_id')}) | Status: {a.get('verification_status')}")

    print(f"\n=== POLYLINES AUDIT ({len(polys)} items) ===")
    for i, p in enumerate(polys):
        wps = p.get("waypoints", [])
        print(f"[{i+1}] ID: {p.get('polyline_id')} | Name: {p.get('name')} | Label: {p.get('label')} | Waypoints: {len(wps)} | Status: {p.get('status')}")

# 2. Audit atlas.json layer counts
atlas_path = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models" / "atlas.json"
if atlas_path.exists():
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    parts = atlas.get("parts", [])
    print(f"\n=== ATLAS.JSON LAYER AUDIT (Total: {len(parts)} parts) ===")
    systems = {}
    for p in parts:
        s = p.get("system", "unknown")
        systems[s] = systems.get(s, 0) + 1
    for s, c in sorted(systems.items()):
        print(f"  System '{s}': {c} parts")
