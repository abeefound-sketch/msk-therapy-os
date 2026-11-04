"""BodyParts3D Mesh Extractor.
Extracts genuine anatomical bone meshes from body-13.bin (CC BY 4.0 DBCLS Japan)
and exports them as OBJ files with cryptographic checksums and anatomical metadata.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ATLAS_PATH = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models" / "atlas.json"
BIN_PATH = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models" / "body-13.bin"
OUT_DIR = REPO_ROOT / "tools" / "blender_anatomy_studio" / "assets" / "bp3d"

TARGET_BONES = {
    "FJ3368": {"name": "Humerus_R", "fma": "FMA:23130", "segment": "upper_arm.R"},
    "FJ3349": {"name": "Radius_R", "fma": "FMA:23464", "segment": "forearm.R"},
    "FJ3391": {"name": "Ulna_R", "fma": "FMA:23467", "segment": "forearm.R"},
    "FJ3352": {"name": "Metacarpal_2_R", "fma": "FMA:24466", "segment": "hand.R"},
    "FJ3384": {"name": "Scapula_R", "fma": "FMA:13395", "segment": "clavicle.R"},
    "FJ3362": {"name": "Clavicle_R", "fma": "FMA:13322", "segment": "clavicle.R"},
    "FJ3387": {"name": "Tibia_R", "fma": "FMA:24477", "segment": "shank.R"},
    "FJ3360": {"name": "Calcaneus_R", "fma": "FMA:24497", "segment": "foot.R"},
}


def extract_meshes():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(ATLAS_PATH, "r", encoding="utf-8") as f:
        atlas = json.load(f)

    parts_map = {p["id"]: p for p in atlas["parts"]}
    bin_buf = BIN_PATH.read_bytes()

    registry_metadata = {}

    for bone_id, meta in TARGET_BONES.items():
        part = parts_map[bone_id]
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
            obj_f.write(f"# BodyParts3D Mesh: {part['name']} ({bone_id})\n")
            obj_f.write(f"# FMA: {meta['fma']}, License: CC BY 4.0 DBCLS Japan\n")
            obj_f.write(f"# SHA256: {mesh_sha256}\n")
            obj_f.write(f"o {meta['name']}\n")

            # Write vertices: Note BodyParts3D coordinates are (X, Y, Z) in meters
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

        registry_metadata[bone_id] = {
            "asset_id": bone_id,
            "bone_name": meta["name"],
            "canonical_name": part["name"],
            "fma_id": meta["fma"],
            "parent_segment": meta["segment"],
            "vertex_count": vc,
            "triangle_count": ic // 3,
            "sha256": mesh_sha256,
            "obj_file": str(obj_path.relative_to(REPO_ROOT)),
            "bounds": part["bounds"],
            "license": "CC BY 4.0 DBCLS Japan",
            "source_chunk": "body-13.bin",
        }
        print(f"Extracted {meta['name']} ({bone_id}): {vc} verts, {ic//3} tris -> {obj_path.name} (SHA256: {mesh_sha256[:12]}...)")

    meta_json = OUT_DIR / "bp3d_extracted_assets.json"
    with open(meta_json, "w", encoding="utf-8") as f:
        json.dump(registry_metadata, f, indent=2)

    print(f"Saved registry metadata to {meta_json}")


if __name__ == "__main__":
    extract_meshes()
