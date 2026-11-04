"""Test suite for Milestone P33: Independent Reality Acceptance & Hardening.
Verifies fresh MediaPipe inference, corrected benchmark metrics,
data governance, browser E2E evidence, and release blend integrity.
"""
from __future__ import annotations

import json
import sqlite3
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
P33_EVIDENCE = REPO_ROOT / "1docs" / "audits" / "P33" / "evidence"
P33_SCREENSHOTS = REPO_ROOT / "1docs" / "audits" / "P33" / "screenshots"


class TestP33RealityAcceptance:
    def test_p33_fresh_inference_evidence(self):
        """Verify fresh MediaPipe inference run outputs authentic telemetry and debug frames."""
        inf_json = P33_EVIDENCE / "p33_fresh_inference_run.json"
        assert inf_json.exists(), "p33_fresh_inference_run.json missing"
        data = json.loads(inf_json.read_text(encoding="utf-8"))

        # Verify video and model hashes
        assert data["video_asset"]["sha256"] == "cf4f2816c86bea4bfbea255333d8626ff32a3ecabdab8b0fb147cea9167fde3a"
        assert data["model_asset"]["sha256"] == "4eaa5eb7a98365221087693fcc286334cf0858e2eb6e15b506aa4a7ecdcec4ad"

        # Verify performance metrics on real CPU
        perf = data["performance"]
        assert perf["total_frames_processed"] == 100
        assert 30.0 < perf["avg_inference_latency_ms"] < 150.0  # Realistic CPU range
        assert perf["inference_throughput_fps"] > 5.0
        assert perf["peak_process_ram_mb"] > 150.0  # Real working set RAM

        # Verify debug frame screenshots exist
        for f in [0, 50, 99]:
            img = P33_SCREENSHOTS / f"p33_mediapipe_frame_{f:03d}.png"
            assert img.exists(), f"Debug frame missing: {img.name}"
            assert img.stat().st_size > 500_000

    def test_p33_corrected_benchmarks(self):
        """Verify corrected benchmarks distinguish headless eval rate from viewport display FPS."""
        bench_json = P33_EVIDENCE / "p33_corrected_benchmarks.json"
        assert bench_json.exists(), "p33_corrected_benchmarks.json missing"
        data = json.loads(bench_json.read_text(encoding="utf-8"))

        cb = data["corrected_benchmarks"]
        assert cb["cold_start_and_exec_duration_ms"] > 1000.0  # Real cold start takes seconds
        assert cb["headless_computational_throughput_fps"] > 1000.0
        assert "NOT_APPLICABLE_IN_HEADLESS_CLI" in cb["display_viewport_fps_status"]
        assert cb["blender_process_peak_ram_mb"] > 150.0
        assert cb["sidecar_process_peak_ram_mb"] > 150.0

        # Verify kinematics and drift
        m = data["motion_and_rig_verification"]
        assert m["kinematic_mode"] == "FK"
        assert m["ik_constraint_influence"] == 0.0
        assert m["humerus_displacement_f1_to_f60_mm"] > 500.0
        assert m["surface_attachment_drift_mm"] < 0.001

        # Verify rendered frames exist
        for f in [1, 50, 100]:
            img = P33_SCREENSHOTS / f"p33_blender_render_frame_{f:03d}.png"
            assert img.exists(), f"Rendered frame missing: {img.name}"
            assert img.stat().st_size > 100_000

    def test_p33_data_governance_and_backup(self):
        """Verify data governance audit, prohibition of fake approvals, and isolated backup test."""
        gov_json = P33_EVIDENCE / "p33_data_governance_audit.json"
        assert gov_json.exists(), "p33_data_governance_audit.json missing"
        data = json.loads(gov_json.read_text(encoding="utf-8"))

        assert data["database_audits"]["vault_db"]["integrity"] == "ok"
        assert data["database_audits"]["msk_db"]["integrity"] == "ok"
        assert data["claims_governance"]["prohibited_status_check"].startswith("PASSED")
        assert data["isolated_backup_restore_test"]["status"] == "PASSED"
        assert data["isolated_backup_restore_test"]["bit_exact_verification"] is True

    def test_p33_browser_e2e_screenshots_exist(self):
        """Verify all browser E2E screenshots are present and valid."""
        for ss_name in [
            "p33_browser_e2e_atlas_loaded.png",
            "p33_browser_e2e_knowledge_active.png",
            "p33_browser_e2e_markdown_modal.png"
        ]:
            img = P33_SCREENSHOTS / ss_name
            assert img.exists(), f"Browser E2E screenshot missing: {ss_name}"
            assert img.stat().st_size > 50_000

    def test_p33_hardened_release_blend_integrity(self):
        """Verify p33_hardened_release.blend exists and has valid size."""
        blend = P33_EVIDENCE / "p33_hardened_release.blend"
        assert blend.exists()
        assert blend.stat().st_size > 2_000_000
