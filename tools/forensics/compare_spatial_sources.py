"""MSK-Therapy-OS - Forensics: Compare Spatial Sources.

Compares baked static JSON (acupuncture_3d.json) with AnatomicalSpatialResolver canonical positions,
measuring pairwise Euclidean discrepancy for all 362 points.
Generates authoritative CSV and JSON reconciliation matrices for Milestone P18.
Standard library only.
"""

import csv
import json
import math
import sqlite3
import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from msk_therapy_os.spatial_resolver import AnatomicalSpatialResolver, AUDITED_CANONICAL_POINTS


def compute_euclidean_distance_mm(p1, p2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2))) * 1000.0


def main():
    json_path = REPO_ROOT / "msk_therapy_os" / "static" / "atlas" / "data" / "acupuncture_3d.json"
    db_path = REPO_ROOT / "msk_therapy_os.sqlite3"
    out_csv = REPO_ROOT / "1docs" / "audits" / "P18" / "P18_ACUPOINT_RECONCILIATION.csv"
    out_json = REPO_ROOT / "1docs" / "audits" / "P18" / "P18_ACUPOINT_RECONCILIATION.json"

    if not json_path.exists():
        print(f"ERROR: Baked JSON not found at {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        baked_data = json.load(f)

    baked_points = baked_data.get("points", {})

    # Check SQLite overrides
    sqlite_overrides = {}
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reference_overrides'")
            if cur.fetchone():
                cur.execute("SELECT point_code, x, y, z, normal_x, normal_y, normal_z FROM reference_overrides")
                for row in cur.fetchall():
                    sqlite_overrides[row[0]] = {
                        "position": [row[1], row[2], row[3]],
                        "normal": [row[4], row[5], row[6]],
                    }
            conn.close()
        except Exception as e:
            print(f"Warning: Could not read SQLite overrides: {e}")

    resolver = AnatomicalSpatialResolver()

    records = []
    delta_ge_100 = 0
    delta_ge_50 = 0
    delta_ge_20 = 0

    for code, b_data in baked_points.items():
        baked_pos = b_data.get("position", [0.0, 0.0, 0.0])
        baked_norm = b_data.get("normal", [0.0, 0.0, 1.0])
        baked_status = b_data.get("registration_status", "UNKNOWN")
        baked_grade = b_data.get("evidence_grade", "D")

        # Resolve via spatial resolver
        res = resolver.resolve_point(code, "canonical", {}, {})
        canonical_pos = res.get("resolved_world_position", [0.0, 0.0, 0.0])
        canonical_norm = res.get("surface_normal", [0.0, 0.0, 1.0])
        canonical_quality = res.get("quality_class", "UNKNOWN")
        canonical_status = res.get("registration_status", "UNKNOWN")
        uncertainty = res.get("uncertainty_mm")
        fma_anchor = res.get("fma_id", "")
        who_ref = res.get("who_reference", "")
        mesh_id = res.get("mesh_id", "FJ2810")
        mesh_hash = res.get("mesh_hash", "")

        delta_mm = round(compute_euclidean_distance_mm(baked_pos, canonical_pos), 3)

        if delta_mm >= 100.0:
            delta_ge_100 += 1
        if delta_mm >= 50.0:
            delta_ge_50 += 1
        if delta_mm >= 20.0:
            delta_ge_20 += 1

        override_info = sqlite_overrides.get(code)
        override_pos = override_info["position"] if override_info else None

        records.append({
            "code": code,
            "name_zh": b_data.get("name_zh", res.get("name_zh", "")),
            "name_en": b_data.get("name_en", res.get("name_en", "")),
            "meridian_code": b_data.get("meridian_code", res.get("meridian_code", "")),
            "region": b_data.get("region", res.get("region", "")),
            "laterality": res.get("laterality", "right"),
            "baked_x": baked_pos[0],
            "baked_y": baked_pos[1],
            "baked_z": baked_pos[2],
            "baked_registration_status": baked_status,
            "baked_evidence_grade": baked_grade,
            "canonical_x": canonical_pos[0],
            "canonical_y": canonical_pos[1],
            "canonical_z": canonical_pos[2],
            "canonical_quality_class": canonical_quality,
            "canonical_registration_status": canonical_status,
            "delta_baked_canonical_mm": delta_mm,
            "sqlite_override_present": bool(override_info),
            "sqlite_override_position": override_pos,
            "uncertainty_mm": uncertainty,
            "who_reference": who_ref,
            "fma_anchor": fma_anchor,
            "mesh_id": mesh_id,
            "mesh_hash": mesh_hash,
        })

    # Sort records descending by delta
    records.sort(key=lambda r: r["delta_baked_canonical_mm"], reverse=True)

    # Write CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    csv_fields = [
        "code", "name_zh", "name_en", "meridian_code", "region", "laterality",
        "baked_x", "baked_y", "baked_z", "baked_registration_status", "baked_evidence_grade",
        "canonical_x", "canonical_y", "canonical_z", "canonical_quality_class", "canonical_registration_status",
        "delta_baked_canonical_mm", "sqlite_override_present", "uncertainty_mm",
        "who_reference", "fma_anchor", "mesh_id", "mesh_hash"
    ]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    # Write JSON
    summary = {
        "milestone": "P18",
        "total_points_evaluated": len(records),
        "divergence_metrics": {
            "delta_ge_100mm": delta_ge_100,
            "delta_ge_50mm": delta_ge_50,
            "delta_ge_20mm": delta_ge_20,
            "max_delta_mm": records[0]["delta_baked_canonical_mm"] if records else 0.0,
            "worst_divergent_point": records[0]["code"] if records else None,
        },
        "quality_class_breakdown": {
            "CLASS_A": sum(1 for r in records if r["canonical_quality_class"] == "CLASS_A"),
            "CLASS_B": sum(1 for r in records if r["canonical_quality_class"] == "CLASS_B"),
            "CLASS_D": sum(1 for r in records if r["canonical_quality_class"] == "CLASS_D"),
            "OTHER": sum(1 for r in records if r["canonical_quality_class"] not in ("CLASS_A", "CLASS_B", "CLASS_D")),
        },
        "top_15_divergences": records[:15],
        "all_records": records,
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("================================================================================")
    print("P18 FORENSIC SPATIAL RECONCILIATION SUMMARY")
    print("================================================================================")
    print(f"Total points evaluated: {len(records)}")
    print(f"Points with Delta >= 100 mm: {delta_ge_100} ({delta_ge_100/len(records)*100:.1f}%)")
    print(f"Points with Delta >=  50 mm: {delta_ge_50} ({delta_ge_50/len(records)*100:.1f}%)")
    print(f"Points with Delta >=  20 mm: {delta_ge_20} ({delta_ge_20/len(records)*100:.1f}%)")
    print(f"Max Delta: {records[0]['delta_baked_canonical_mm']:.2f} mm ({records[0]['code']} - {records[0]['name_zh']})")
    print("--------------------------------------------------------------------------------")
    print("Top 10 Divergent Points (Baked JSON vs Canonical Resolver):")
    for r in records[:10]:
        print(f"  {r['code']:<5} {r['name_zh']:<6} ({r['name_en']:<12}): Delta = {r['delta_baked_canonical_mm']:>7.2f} mm | Baked=[{r['baked_x']:.3f}, {r['baked_y']:.3f}, {r['baked_z']:.3f}] vs Canon=[{r['canonical_x']:.3f}, {r['canonical_y']:.3f}, {r['canonical_z']:.3f}]")
    print("================================================================================")
    print(f"CSV generated:  {out_csv}")
    print(f"JSON generated: {out_json}")


if __name__ == "__main__":
    main()
