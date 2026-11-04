"""BodyParts3D Lower Limb Asset Extractor for MSK-Therapy-OS V1.3.
Extracts authentic anatomical leg bones and muscles from body-1.bin and body-13.bin (CC BY 4.0 DBCLS Japan)
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

TARGET_STRUCTURES = {
    # Bones (Chunk 13)
    "FJ3365": {"name": "Femur_R", "fma": "FMA:9611", "type": "BONE", "canonical_bone": "thigh_r"},
    "FJ3387": {"name": "Tibia_R", "fma": "FMA:24476", "type": "BONE", "canonical_bone": "calf_r"},
    "FJ3366": {"name": "Fibula_R", "fma": "FMA:24479", "type": "BONE", "canonical_bone": "calf_r"},
    "FJ3381": {"name": "Patella_R", "fma": "FMA:24485", "type": "BONE", "canonical_bone": "thigh_r"},
    # Muscles (Chunk 1)
    "FJ1433": {"name": "Rectus_femoris_R", "fma": "FMA:22428", "type": "MUSCLE", "canonical_bone": "thigh_r", "group": "quadriceps"},
    "FJ1441": {"name": "Vastus_intermedius_R", "fma": "FMA:22432", "type": "MUSCLE", "canonical_bone": "thigh_r", "group": "quadriceps"},
    "FJ1442": {"name": "Vastus_lateralis_R", "fma": "FMA:22430", "type": "MUSCLE", "canonical_bone": "thigh_r", "group": "quadriceps"},
    "FJ1443": {"name": "Vastus_medialis_R", "fma": "FMA:22431", "type": "MUSCLE", "canonical_bone": "thigh_r", "group": "quadriceps"},
}


def extract_lower_limb():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(ATLAS_PATH, "r", encoding="utf-8") as f:
        atlas = json.load(f)

    parts_map = {p["id"]: p for p in atlas["parts"]}
    bin_cache = {}
    registry = {}

    for struct_id, meta in TARGET_STRUCTURES.items():
        if struct_id not in parts_map:
            print(f"WARNING: Structure ID {struct_id} not found in atlas.json")
            continue

        part = parts_map[struct_id]
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
            obj_f.write(f"# BodyParts3D Authentic Anatomical Asset: {part['name']} ({struct_id})\n")
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

        registry[struct_id] = {
            "asset_id": struct_id,
            "name": meta["name"],
            "canonical_name": part["name"],
            "fma_id": meta["fma"],
            "type": meta["type"],
            "canonical_bone": meta["canonical_bone"],
            "vertex_count": vc,
            "triangle_count": ic // 3,
            "sha256": mesh_sha256,
            "obj_file": obj_name,
        }
        print(f"Extracted {meta['name']}: {vc} vertices, {ic // 3} triangles -> {obj_name}")

    reg_path = OUT_DIR / "bp3d_lower_limb_registry.json"
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    print(f"Saved registry to {reg_path}")


if __name__ == "__main__":
    extract_lower_limb()
