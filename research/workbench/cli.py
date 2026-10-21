"""Unified CLI for Anatomical Research Workbench."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import (
    BaseAdapter,
    JICioAdapter,
    MeridianStudioAdapter,
    TCMAcupointsAdapter,
    WaterCMYAdapter,
)
from .benchmarker import Benchmarker
from .bootstrap import BootstrapManager
from .comparison_engine import ComparisonEngine
from .coordinate_registry import CoordinateRegistry
from .export_pipeline import ExportPipeline
from .geometry_validator import GeometryValidator
from .mesh_geometry import BodyPartsSkinMesh


def get_all_adapters() -> list[BaseAdapter]:
    return [
        JICioAdapter(),
        MeridianStudioAdapter(),
        WaterCMYAdapter(),
        TCMAcupointsAdapter(),
    ]


def cmd_bootstrap(args: argparse.Namespace) -> None:
    """Verify reproducible upstream repositories, git SHAs, licenses, and SHA256 hashes."""
    bm = BootstrapManager()
    rep = bm.bootstrap_all(fetch_if_missing=args.fetch)

    print("================================================================================")
    print("UPSTREAM BOOTSTRAP & REPRODUCIBILITY VERIFICATION")
    print("================================================================================")
    print(f"Overall Reproducibility Status: {'PASS' if rep['all_passed'] else 'FAIL / BLOCKED'}\n")

    for name, data in rep["upstreams"].items():
        print(f"[{name}]")
        print(f"  Target Commit : {data['target_commit']}")
        print(f"  Actual Commit : {data['actual_commit']} ({'MATCH' if data['commit_match'] else 'MISMATCH'})")
        print(f"  Licenses      : {', '.join(data['licenses_present'])}")
        if data["missing_licenses"]:
            print(f"  Missing Lic   : {', '.join(data['missing_licenses'])}")
        print("  Asset Integrity:")
        for asset, a_data in data["asset_checks"].items():
            h_str = a_data.get("actual_sha256", "N/A")[:16] + "..." if a_data.get("actual_sha256") else "MISSING"
            print(f"    - {asset:35}: {a_data['status']} ({h_str})")
        print(f"  Status        : {data['status']}\n")

    if args.json_out:
        out_p = Path(args.json_out)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2)
        print(f"Saved bootstrap report to {out_p}")


def cmd_audit(args: argparse.Namespace) -> None:
    """Audit all 4 upstream repositories."""
    adapters = get_all_adapters()
    print("================================================================================")
    print("UPSTREAM 3D ACUPUNCTURE / ANATOMY REPOSITORIES AUDIT")
    print("================================================================================")
    for ad in adapters:
        meta = ad.get_metadata()
        pts = ad.extract_points()
        mers = ad.extract_meridians()
        print(f"\n[Source] {meta['source']}")
        print(f"  Repository : {meta['repository']}")
        print(f"  Commit SHA : {meta['commit_sha']}")
        print(f"  License    : {meta['license']}")
        print(f"  Mesh Asset : {meta['mesh_source']}")
        print(f"  Algorithm  : {meta['algorithm']}")
        print(f"  Units/Axes : {meta['units']} | {meta['handedness']}")
        print(f"  Extracted  : {len(pts)} points, {len(mers)} meridians")
    print("\nAudit completed successfully.")


def cmd_compare(args: argparse.Namespace) -> None:
    """Compare coordinates across sources for specific scenario or all points."""
    adapters = get_all_adapters()
    engine = ComparisonEngine(adapters)

    scenario_codes = CoordinateRegistry.get_neck_shoulder_scenario_codes() if not args.points else args.points.split(",")
    scenario_codes = [c.strip().upper() for c in scenario_codes]

    report = engine.compare_scenario(scenario_codes, name="Neck-Shoulder Reference Scenario")
    print("================================================================================")
    print(f"COORDINATE COMPARISON REPORT: {report.scenario_name}")
    print("================================================================================")
    print(f"Overall Mean Error to Anatomical Landmarks: {report.overall_mean_error_mm} mm")
    print("\nSource Accuracy Rankings (Mean Distance to Landmark):")
    for src, err in report.source_rankings:
        print(f"  1. {src:32}: {err:6.2f} mm")

    print("\nDetailed Point Breakdown:")
    for pt_res in report.point_results:
        lm_str = f"[{', '.join(f'{c:.3f}' for c in pt_res.canonical_coords)}]" if pt_res.canonical_coords else "None"
        print(f"\n* Point {pt_res.code} ({pt_res.name_zh}) | Status: {pt_res.agreement_status}")
        print(f"  Landmark Coords : {lm_str}")
        print(f"  Mean Error      : {pt_res.mean_error_mm} mm | Max Error: {pt_res.max_error_mm} mm")
        for src, dist in pt_res.distance_to_landmark_mm.items():
            coords = pt_res.positions_by_source.get(src, [])
            coord_s = f"[{', '.join(f'{c:.3f}' for c in coords)}]" if coords else "None"
            print(f"    - {src:30}: dist={dist:5.1f}mm  coords={coord_s}")

    if args.json_out:
        out_p = Path(args.json_out)
        data = {
            "scenario": report.scenario_name,
            "overall_mean_error_mm": report.overall_mean_error_mm,
            "source_rankings": report.source_rankings,
            "points": [
                {
                    "code": r.code,
                    "name_zh": r.name_zh,
                    "mean_error_mm": r.mean_error_mm,
                    "max_error_mm": r.max_error_mm,
                    "status": r.agreement_status,
                    "distances_to_landmark": r.distance_to_landmark_mm,
                    "pairwise_distances": r.inter_source_pairwise_distances_mm,
                    "positions": r.positions_by_source,
                }
                for r in report.point_results
            ],
        }
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved report to {out_p}")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate real geometric surface adherence against authentic FJ2810 mesh."""
    mesh = BodyPartsSkinMesh()
    validator = GeometryValidator(mesh)
    adapters = get_all_adapters()

    print("================================================================================")
    print("REAL MESH GEOMETRY & EVIDENCE VALIDATION REPORT (BODYPARTS3D FJ2810)")
    print("================================================================================")
    print(f"Authentic Mesh SHA256: {mesh.bin_sha256}")
    print(f"Total Triangles Tested: {mesh.num_faces}\n")

    all_summaries = []
    for ad in adapters:
        summary = validator.validate_source(ad)
        all_summaries.append(summary)
        print(f"[Source] {summary.source_name}")
        print(f"  Total Points Tested : {summary.total_points}")
        print(f"  Geometry Verified   : {summary.geometry_verified_count}")
        print(f"  Anatomy Reviewed    : {summary.anatomy_reviewed_count} (Requires expert documentation)")
        print(f"  Unverified          : {summary.unverified_count}")
        print(f"  Floating (>5mm)     : {summary.floating_count}")
        print(f"  Penetrating (<-2mm) : {summary.penetrating_count}")
        print(f"  Mean Mesh Distance  : {summary.mean_measured_distance_mm} mm (Max: {summary.max_measured_distance_mm} mm)")
        if summary.path_discontinuities:
            print(f"  Discontinuities     : {len(summary.path_discontinuities)} step warnings along pathways\n")
        else:
            print("  Discontinuities     : None (continuous smooth paths)\n")

    if args.json_out:
        out_p = Path(args.json_out)
        out_data = [
            {
                "source": s.source_name,
                "total": s.total_points,
                "reviewed": s.anatomy_reviewed_count,
                "verified": s.geometry_verified_count,
                "unverified": s.unverified_count,
                "floating": s.floating_count,
                "penetrating": s.penetrating_count,
                "mean_distance_mm": s.mean_measured_distance_mm,
                "max_distance_mm": s.max_measured_distance_mm,
                "discontinuity_count": len(s.path_discontinuities),
            }
            for s in all_summaries
        ]
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)
        print(f"Saved validation summary to {out_p}")


def cmd_benchmark(args: argparse.Namespace) -> None:
    """Run performance benchmarks based strictly on authentic measured telemetry."""
    bench = Benchmarker()
    summary = bench.generate_summary()

    print("================================================================================")
    print("AUTHENTIC PERFORMANCE & RESOURCE BENCHMARK (MEASURED TELEMETRY)")
    print("================================================================================")
    print(f"Hardware Environment: {summary['target_hardware']}\n")

    for m in summary["metrics"]:
        print(f"[{m['source']}]")
        print(f"  Model Size      : {m['model_size_mb']} MB ({m['model_format']})")
        print(f"  GPU Renderer    : {m['gpu_renderer']}")
        print(f"  JS Heap Used    : {m['js_heap_mb']} MB")
        print(f"  Page Load Time  : {m['load_time_ms']} ms")
        print(f"  Framerate       : Idle {m['fps_idle']} FPS / Interaction {m['fps_interaction']} FPS")
        print(f"  Feasibility     : {m['feasibility']}")
        print(f"  Telemetry File  : {m['telemetry_file']}")
        print(f"  Notes           : {m['notes']}\n")

    print(f"Architecture Recommendation:\n{summary['recommendation']}")

    if args.json_out:
        out_p = Path(args.json_out)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\nSaved benchmark results to {out_p}")


def cmd_export(args: argparse.Namespace) -> None:
    """Export canonical dataset and validation summary."""
    jicio = JICioAdapter()
    studio = MeridianStudioAdapter()
    mesh = BodyPartsSkinMesh()
    pipeline = ExportPipeline(mesh=mesh)

    out_file = args.out or "canonical_acupuncture_v2.json"
    exported_path = pipeline.export_canonical_dataset(jicio, studio, output_filename=out_file)

    print("================================================================================")
    print("EXPORT CANONICAL ACUPUNCTURE DATASET (REAL MESH VALIDATED)")
    print("================================================================================")
    print(f"Successfully generated canonical dataset at:")
    print(f"  {exported_path}")
    print(f"File size: {exported_path.stat().st_size / 1024:.1f} KB")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="research.workbench",
        description="Anatomical Research Workbench for 3D Acupuncture & Meridian Analysis",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: bootstrap
    p_boot = subparsers.add_parser("bootstrap", help="Verify upstream commits, licenses, and asset hashes")
    p_boot.add_argument("--fetch", action="store_true", help="Fetch/clone upstream if missing")
    p_boot.add_argument("--json-out", help="Path to write JSON bootstrap summary")

    # Subcommand: audit
    subparsers.add_parser("audit", help="Audit all 4 upstream repositories")

    # Subcommand: compare
    p_comp = subparsers.add_parser("compare", help="Compare acupoint coordinates across sources")
    p_comp.add_argument("--points", help="Comma-separated list of acupoint codes (e.g. GB21,GV14)")
    p_comp.add_argument("--json-out", help="Path to write JSON comparison output")

    # Subcommand: validate
    p_val = subparsers.add_parser("validate", help="Validate surface adherence against authentic mesh")
    p_val.add_argument("--json-out", help="Path to write JSON validation summary")

    # Subcommand: benchmark
    p_bm = subparsers.add_parser("benchmark", help="Benchmark performance using measured telemetry")
    p_bm.add_argument("--json-out", help="Path to write JSON benchmark summary")

    # Subcommand: export
    p_exp = subparsers.add_parser("export", help="Export canonical acupuncture dataset")
    p_exp.add_argument("--out", help="Output filename in research/artifacts")

    args = parser.parse_args()

    if args.command == "bootstrap":
        cmd_bootstrap(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "compare":
        cmd_compare(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "export":
        cmd_export(args)


if __name__ == "__main__":
    main()
