"""Comprehensive tests for the Anatomical Research Workbench including negative corruption tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from research.workbench.adapters import (
    JICioAdapter,
    MeridianStudioAdapter,
    NormalizedPoint,
    TCMAcupointsAdapter,
    WaterCMYAdapter,
)
from research.workbench.benchmarker import Benchmarker
from research.workbench.bootstrap import BootstrapManager
from research.workbench.comparison_engine import ComparisonEngine
from research.workbench.coordinate_registry import CoordinateRegistry
from research.workbench.export_pipeline import ExportPipeline
from research.workbench.geometry_validator import GeometryValidator
from research.workbench.mesh_geometry import BodyPartsSkinMesh


class TestBootstrap:
    def test_bootstrap_reproducibility(self):
        bm = BootstrapManager()
        rep = bm.bootstrap_all(fetch_if_missing=False)
        assert rep["all_passed"] is True
        assert len(rep["upstreams"]) == 4
        for name, data in rep["upstreams"].items():
            assert data["status"] == "PASS"
            assert data["commit_match"] is True
            assert len(data["missing_licenses"]) == 0


class TestMeshGeometry:
    def test_mesh_loading(self):
        mesh = BodyPartsSkinMesh()
        assert mesh.num_faces == 44744
        assert len(mesh.vertices) == 22902
        assert mesh.bin_sha256 == BodyPartsSkinMesh.EXPECTED_BIN_SHA256

    def test_point_query(self):
        mesh = BodyPartsSkinMesh()
        # Query known surface point (LU1_R)
        res = mesh.query_point([0.129658, 1.347498, 0.068839], [0.60728, 0.41157, 0.67957])
        assert res["distance_mm"] < 1.0
        assert res["normal_alignment_dot"] > 0.95
        assert res["closest_face_index"] >= 0


class TestGeometryValidator:
    @pytest.fixture
    def validator(self):
        return GeometryValidator()

    def test_authentic_point_validation(self, validator):
        jicio = JICioAdapter()
        pts = jicio.extract_points()
        assert "GB21_R" in pts

        res = validator.validate_point(pts["GB21_R"])
        assert res.measured_surface_distance_mm < 1.0
        assert res.is_floating is False
        assert res.is_penetrating is False
        assert res.evidence_tag == "GEOMETRY_VERIFIED"

    def test_negative_deliberate_floating_corruption(self, validator):
        # Deliberately corrupt point: lift 50mm (0.05m) away from surface
        corrupted = NormalizedPoint(
            code="CORRUPT_FLOAT",
            name_zh="浮动测试",
            name_en="CorruptFloat",
            pinyin="test",
            meridian_code="GB",
            region="shoulder",
            raw_position=[0.083, 1.470, -0.061],
            canonical_position=[0.083, 1.470 + 0.050, -0.061],  # +50mm Y lift
            normal=[0.0, 1.0, 0.0],
            source="test",
        )
        res = validator.validate_point(corrupted)
        assert res.is_floating is True
        assert res.measured_surface_distance_mm > 20.0
        assert res.evidence_tag == "UNVERIFIED"
        assert "FLOATING" in res.details

    def test_negative_deliberate_subsurface_penetration(self, validator):
        # Deliberately corrupt point: push inside torso by -15mm along normal
        corrupted = NormalizedPoint(
            code="CORRUPT_PENETRATE",
            name_zh="穿透测试",
            name_en="CorruptPenetrate",
            pinyin="test",
            meridian_code="LU",
            region="chest",
            raw_position=[0.129, 1.347, 0.068],
            canonical_position=[0.129, 1.347, 0.068 - 0.020],  # -20mm inside along Z
            normal=[0.0, 0.0, 1.0],
            source="test",
        )
        res = validator.validate_point(corrupted)
        assert res.signed_distance_mm < -2.0
        assert res.is_penetrating is True
        assert res.evidence_tag == "UNVERIFIED"
        assert "PENETRATING" in res.details

    def test_negative_deliberate_inverted_normal(self, validator):
        # Deliberately invert normal vector (point inward toward body center)
        corrupted = NormalizedPoint(
            code="CORRUPT_NORMAL",
            name_zh="反相法线",
            name_en="CorruptNormal",
            pinyin="test",
            meridian_code="GB",
            region="shoulder",
            raw_position=[0.083, 1.470, -0.061],
            canonical_position=[0.08299, 1.47062, -0.06099],
            normal=[-0.492, -0.863, 0.110],  # Exactly negated normal
            source="test",
        )
        res = validator.validate_point(corrupted)
        assert res.is_normal_inverted is True
        assert res.normal_alignment_dot < -0.9
        assert res.evidence_tag == "UNVERIFIED"
        assert "INVERTED_NORMAL" in res.details

    def test_negative_deliberate_corrupted_face_index(self, validator):
        # Provide a known mismatched face index (e.g. face 100 on feet instead of shoulder)
        corrupted = NormalizedPoint(
            code="CORRUPT_FACE",
            name_zh="面索引错误",
            name_en="CorruptFace",
            pinyin="test",
            meridian_code="GB",
            region="shoulder",
            raw_position=[0.083, 1.470, -0.061],
            canonical_position=[0.08299, 1.47062, -0.06099],
            normal=[0.492, 0.863, -0.110],
            source="test",
            extra={"face_index": 100},
        )
        res = validator.validate_point(corrupted)
        assert res.recorded_face_match is False
        assert "FACE_INDEX_MISMATCH" in res.details


class TestAdapters:
    def test_jicio_bilateral_preservation(self):
        adapter = JICioAdapter()
        pts = adapter.extract_points()
        assert len(pts) == 670
        assert "GV14" in pts
        assert "GB21_R" in pts
        assert "GB21_L" in pts
        # Ensure right and left points are symmetrically mirrored across X
        assert abs(pts["GB21_R"].canonical_position[0] + pts["GB21_L"].canonical_position[0]) < 0.005

    def test_meridian_studio_adapter(self):
        adapter = MeridianStudioAdapter()
        pts = adapter.extract_points()
        assert len(pts) == 361
        assert "LU1" in pts
        assert "中府" == pts["LU1"].name_zh


class TestComparisonEngine:
    def test_neck_shoulder_scenario(self):
        adapters = [JICioAdapter(), WaterCMYAdapter(), TCMAcupointsAdapter()]
        engine = ComparisonEngine(adapters)
        report = engine.compare_scenario(CoordinateRegistry.get_neck_shoulder_scenario_codes())
        assert len(report.point_results) == 6
        assert len(report.source_rankings) == 3
        # WaterCMY has lowest mean error on GV14
        gv14_res = next(r for r in report.point_results if r.code == "GV14")
        assert gv14_res.distance_to_landmark_mm["WaterCMY/anatomy-3d"] < 10.0


class TestBenchmarker:
    def test_benchmarker_uses_telemetry(self):
        bench = Benchmarker()
        summary = bench.generate_summary()
        assert len(summary["metrics"]) == 4
        for m in summary["metrics"]:
            assert m["telemetry_file"] is not None
            assert m["js_heap_mb"] is not None
            assert m["load_time_ms"] is not None


class TestExportPipeline:
    def test_export_canonical_dataset(self, tmp_path):
        jicio = JICioAdapter()
        studio = MeridianStudioAdapter()
        mesh = BodyPartsSkinMesh()
        pipeline = ExportPipeline(out_dir=tmp_path, mesh=mesh)
        out_file = pipeline.export_canonical_dataset(jicio, studio, "test_canonical.json")

        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["format"] == "canonical-acupuncture-mesh"
        assert data["total_acupoints_instances"] == 670
        assert data["meridian_count"] == 14
        assert "GB21_R" in data["points"]
        assert "mesh_geometry_validation" in data["points"]["GB21_R"]
        assert "target_model_sha256" in data["points"]["GB21_R"]["mesh_geometry_validation"]
