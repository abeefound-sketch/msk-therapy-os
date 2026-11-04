"""Test suite for Milestone P32: Final System Acceptance and Research Release.
Verifies all release artifacts, hardware benchmark criteria, database integrity,
and engineering research scope constraints.
"""
from __future__ import annotations

import json
import sqlite3
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
P32_EVIDENCE = REPO_ROOT / "1docs" / "audits" / "P32" / "evidence"


class TestP32SystemAcceptance:
    def test_p32_artifacts_exist_and_hashes(self):
        """Verify all P32 release evidence files exist with valid sizes."""
        release_blend = P32_EVIDENCE / "p32_final_release.blend"
        bundle_json = P32_EVIDENCE / "p32_acceptance_bundle.json"
        report_md = P32_EVIDENCE / "p32_final_acceptance_report.md"
        benchmark_json = P32_EVIDENCE / "p32_performance_benchmark.json"

        assert release_blend.exists(), "p32_final_release.blend missing"
        assert release_blend.stat().st_size > 1_000_000, "Blend file size too small"

        assert bundle_json.exists(), "p32_acceptance_bundle.json missing"
        assert bundle_json.stat().st_size > 10_000, "Bundle JSON too small"

        assert report_md.exists(), "p32_final_acceptance_report.md missing"
        assert report_md.stat().st_size > 2_000, "Markdown report too small"

        assert benchmark_json.exists(), "p32_performance_benchmark.json missing"
        data = json.loads(benchmark_json.read_text(encoding="utf-8"))
        assert "hardware_environment" in data
        assert "timings_and_throughput" in data

    def test_p32_performance_criteria(self):
        """Verify system performance on target hardware satisfies requirements."""
        benchmark_json = P32_EVIDENCE / "p32_performance_benchmark.json"
        data = json.loads(benchmark_json.read_text(encoding="utf-8"))
        timings = data["timings_and_throughput"]

        assert timings["blender_load_sec"] < 1.0, "Blender scene load exceeded 1.0 second"
        assert timings["blender_playback_fps"] > 30.0, "Viewport playback failed 30 FPS target"
        assert timings["bundle_json_export_ms"] < 200.0, "Bundle JSON export too slow"
        assert timings["markdown_export_ms"] < 100.0, "Markdown export too slow"

    def test_database_integrity_suite(self):
        """Verify SQLite integrity checks on all system databases."""
        dbs = [
            REPO_ROOT / "knowledge_vault" / "vault.db",
            REPO_ROOT / "msk_therapy_os.sqlite3",
            REPO_ROOT / "1docs" / "audits" / "P31" / "evidence" / "vault_backup_pre_p31.sqlite3"
        ]
        for db in dbs:
            assert db.exists(), f"Database not found: {db}"
            conn = sqlite3.connect(str(db))
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            res = cur.fetchone()[0]
            conn.close()
            assert res == "ok", f"Database {db.name} integrity failed: {res}"

    def test_security_gates_and_research_invariants(self):
        """Verify strict ENGINEERING_RESEARCH_ONLY scope and zero PII."""
        bundle_json = P32_EVIDENCE / "p32_acceptance_bundle.json"
        data = json.loads(bundle_json.read_text(encoding="utf-8"))

        assert data["release_scope"] == "ENGINEERING_RESEARCH_ONLY"
        assert "NO_AUTONOMOUS_DIAGNOSIS_OR_PRESCRIPTION" in data["clinical_safety_barrier"]

        # Assert no PII keys
        for forbidden in ["patient_name", "ssn", "dob", "mrn"]:
            assert forbidden not in str(data).lower()

    def test_blender_scene_structure_integrity(self):
        """Verify Blender release scene contains all required anatomical and marker entities."""
        blender_metrics_path = P32_EVIDENCE / "p32_blender_benchmark.json"
        assert blender_metrics_path.exists()
        metrics = json.loads(blender_metrics_path.read_text(encoding="utf-8"))

        assert metrics["armature_present"] is True
        assert metrics["humerus_present"] is True
        assert metrics["scapula_present"] is True
        assert metrics["li14_present"] is True
        assert metrics["li15_present"] is True
        assert metrics["total_frames_evaluated"] == 100
