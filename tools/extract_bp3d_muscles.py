"""BodyParts3D Muscle Mesh Extractor for MSK-Therapy-OS V1.2.
Extracts authentic anatomical arm muscle meshes from body-3.bin and body-4.bin (CC BY 4.0 DBCLS Japan)
and exports them as OBJ files with cryptographic checksums and anatomical metadata.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

REPO_ROOT = Path(r"D:\5Projects\msk-therapy-os")
ATLAS_PATH = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models" / "atlas.json"
MODELS_DIR = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models"
OUT_DIR = REPO_ROOT / "tools" / "blender_anatomy_studio" / "assets" / "bp3d"

TARGET_MUSCLES = {
    "FJ1478": {"name": "Biceps_brachii_long_R", "fma": "FMA:37670", "muscle_group": "biceps", "action": "elbow_flexion_supination"},
    "FJ1512": {"name": "Biceps_brachii_short_R", "fma": "FMA:37671", "muscle_group": "biceps", "action": "elbow_flexion_adduction"},
    "FJ1477": {"name": "Triceps_brachii_lateral_R", "fma": "FMA:37689", "muscle_group": "triceps", "action": "elbow_extension"},
    "FJ1479": {"name": "Triceps_brachii_long_R", "fma": "FMA:37688", "muscle_group": "triceps", "action": "elbow_extension_shoulder_adduction"},
    "FJ1480": {"name": "Triceps_brachii_medial_R", "fma": "FMA:37690", "muscle_group": "triceps", "action": "elbow_extension"},
    "FJ1486": {"name": "Brachialis_R", "fma": "FMA:37667", "muscle_group": "brachialis", "action": "pure_elbow_flexion"},
    "FJ1488": {"name": "Coracobrachialis_R", "fma": "FMA:37664", "muscle_group": "coracobrachialis", "action": "shoulder_flexion_adduction"},
}


def extract_muscles():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(ATLAS_PATH, "r", encoding="utf-8") as f:
        atlas = json.load(f)

    parts_map = {p["id"]: p for p in atlas["parts"]}
    bin_cache = {}
    muscle_registry = {}

    for muscle_id, meta in TARGET_MUSCLES.items():
        if muscle_id not in parts_map:
            print(f"WARNING: Muscle ID {muscle_id} not found in atlas.json")
            continue

        part = parts_map[muscle_id]
        chunk = part["chunk"]

        if chunk not in bin_cache:
            bin_path = MODELS_DIR / f"body-{chunk}.bin"
            print(f"Loading binary chunk body-{chunk}.bin ({bin_path.stat().st_size} bytes)...")
            bin_cache[chunk] = bin_path.read_bytes()

        bin_buf = bin_cache[chunk]
        vc = part["vertexCount"]
        ic = part["indexCount"]

        pos_start = part["positions"]
        v_bytes = bin_buf[pos_start : pos_start + vc * 12]

        idx_start = part["indices"]
        i_bytes = bin_buf[idx_start : idx_start + ic * 4]

        # Calculate SHA-256
        mesh_sha256 = hashlib.sha256(v_bytes + i_bytes).hexdigest()

        # Unpack
        verts = struct.unpack(f"<{vc * 3}f", v_bytes)
        indices = struct.unpack(f"<{ic}I", i_bytes)

        # Write OBJ file
        obj_name = f"{meta['name']}.obj"
        obj_path = OUT_DIR / obj_name

        with open(obj_path, "w", encoding="utf-8") as obj_f:
            obj_f.write(f"# BodyParts3D Authentic Anatomical Muscle: {part['name']} ({muscle_id})\n")
            obj_f.write(f"# FMA: {meta['fma']}, License: CC BY 4.0 DBCLS Japan\n")
            obj_f.write(f"# SHA256: {mesh_sha256}\n")
            obj_f.write(f"o {meta['name']}\n")

            # Write vertices in meters
            for i in range(vc):
                x = verts[i * 3]
                y = verts[i * 3 + 1]
                z = verts[i * 3 + 2]
                obj_f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")

            # Write faces (1-indexed for OBJ)
            for j in range(0, ic, 3):
                v1 = indices[j] + 1
                v2 = indices[j + 1] + 1
                v3 = indices[j + 2] + 1
                obj_f.write(f"f {v1} {v2} {v3}\n")

        muscle_registry[muscle_id] = {
            "asset_id": muscle_id,
            "muscle_name": meta["name"],
            "canonical_name": part["name"],
            "fma_id": meta["fma"],
            "muscle_group": meta["muscle_group"],
            "action": meta["action"],
            "vertex_count": vc,
            "triangle_count": ic // 3,
            "sha256": mesh_sha256,
            "obj_file": str(obj_path.relative_to(REPO_ROOT)),
            "bounds": part["bounds"],
            "license": "CC BY 4.0 DBCLS Japan",
            "source_chunk": f"body-{chunk}.bin",
        }
        print(f"Extracted {meta['name']} ({muscle_id}): {vc} verts, {ic//3} tris -> {obj_path.name} (SHA256: {mesh_sha256[:12]}...)")

    registry_path = OUT_DIR / "bp3d_extracted_muscles.json"
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(muscle_registry, f, indent=2)

    print(f"SUCCESS: Saved muscle registry metadata to {registry_path}")


if __name__ == "__main__":
    extract_muscles()
