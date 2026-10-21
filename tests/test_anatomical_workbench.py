"""Tests for the Anatomical Research Workbench."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from research.workbench.adapters import (
    JICioAdapter,
    MeridianStudioAdapter,
    TCMAcupointsAdapter,
    WaterCMYAdapter,
)
from research.workbench.benchmarker import Benchmarker
from research.workbench.comparison_engine import ComparisonEngine
from research.workbench.coordinate_registry import CoordinateRegistry
from research.workbench.export_pipeline import ExportPipeline
from research.workbench.geometry_validator import GeometryValidator


class TestAdapters:
    def test_jicio_adapter(self):
        adapter = JICioAdapter()
        meta = adapter.get_metadata()
        assert meta["source"] == "JICio/tcm-3d"
        assert meta["commit_sha"] == "e8b9ad1c17e67a25e94406100e3fb5c296c24f7a"
        assert meta["license"] == "MIT"

        pts = adapter.extract_points()
        assert len(pts) >= 360
        assert "GV14" in pts
        assert "GB21" in pts
        assert pts["GV14"].status in ["ANATOMY_REVIEWED", "GEOMETRY_VERIFIED"]

        mers = adapter.extract_meridians()
        assert len(mers) >= 12
        assert "LU" in mers
        assert mers["LU"].vertex_count > 0

    def test_meridian_studio_adapter(self):
        adapter = MeridianStudioAdapter()
        meta = adapter.get_metadata()
        assert meta["source"] == "eb-barry/acupuncture-3d-authoring"
        assert meta["commit_sha"] == "cb7a41692276adcbf696538d30f2e3d8ecb4bbc6"

        pts = adapter.extract_points()
        assert len(pts) >= 360
        assert "LU1" in pts
        assert "中府" == pts["LU1"].name_zh
        assert len(pts["LU1"].indications) > 0

        mers = adapter.extract_meridians()
        assert len(mers) == 14

    def test_watercmy_adapter(self):
        adapter = WaterCMYAdapter()
        meta = adapter.get_metadata()
        assert meta["source"] == "WaterCMY/anatomy-3d"
        assert meta["commit_sha"] == "e8d40dca7b1f63f54567395df21d8b1b38a7e840"

        pts = adapter.extract_points()
        assert len(pts) >= 100
        assert "GV14" in pts

        hull = adapter.extract_hull()
        assert len(hull) > 0

    def test_tcm_acupoints_adapter(self):
        adapter = TCMAcupointsAdapter()
        meta = adapter.get_metadata()
        assert meta["source"] == "spacejohnlf/tcm-acupoints"
        assert meta["commit_sha"] == "04e35abb66585eb29c7250ea8ab5243c8c744f64"

        pts = adapter.extract_points()
        assert len(pts) >= 60
        assert "GB21" in pts
        # Ensure canonical Y transform was applied
        assert pts["GB21"].canonical_position[1] > 1.0


class TestCoordinateRegistry:
    def test_landmarks(self):
        landmarks = CoordinateRegistry.list_landmarks()
        assert "GV14" in landmarks
        assert "GB21" in landmarks
        assert "GB20" in landmarks

        gv14 = CoordinateRegistry.get_landmark("GV14")
        assert gv14 is not None
        assert gv14.canonical_coords[0] == 0.0
        assert "C7" in gv14.skeletal_anchor

    def test_euclidean_distance(self):
        d = CoordinateRegistry.euclidean_distance([0.0, 0.0, 0.0], [0.03, 0.04, 0.0])
        assert abs(d - 50.0) < 0.01  # 50mm


class TestComparisonEngine:
    def test_neck_shoulder_scenario(self):
        adapters = [JICioAdapter(), WaterCMYAdapter(), TCMAcupointsAdapter()]
        engine = ComparisonEngine(adapters)
        report = engine.compare_scenario(CoordinateRegistry.get_neck_shoulder_scenario_codes())

        assert report.scenario_name == "Neck-Shoulder Reference Scenario"
        assert len(report.point_results) == 6
        assert report.overall_mean_error_mm > 0.0
        assert len(report.source_rankings) == 3


class TestGeometryValidator:
    def test_validation(self):
        validator = GeometryValidator()
        jicio = JICioAdapter()
        summary = validator.validate_source(jicio)

        assert summary.total_points >= 360
        assert summary.geometry_verified_count + summary.anatomy_reviewed_count > 300
        assert summary.floating_count == 0  # Pre-baked within 3.5mm normal offset


class TestBenchmarker:
    def test_benchmarker_metrics(self):
        bench = Benchmarker()
        summary = bench.generate_summary()
        assert "metrics" in summary
        assert len(summary["metrics"]) == 4
        assert any(m["feasibility"] == "FEASIBLE" for m in summary["metrics"])


class TestExportPipeline:
    def test_export_canonical_dataset(self, tmp_path):
        jicio = JICioAdapter()
        studio = MeridianStudioAdapter()
        pipeline = ExportPipeline(out_dir=tmp_path)
        out_file = pipeline.export_canonical_dataset(jicio, studio, "test_canonical.json")

        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["format"] == "canonical-acupuncture-mesh"
        assert data["version"] == "2.0.0"
        assert data["point_count"] >= 360
        assert data["meridian_count"] == 14
        assert "GB21" in data["points"]
