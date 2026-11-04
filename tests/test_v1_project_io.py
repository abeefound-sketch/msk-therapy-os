"""Unit tests for MSK-Therapy-OS V1.0 Project Persistence & Reports (Package E).
Verifies .mskproj JSON manifest persistence, atomic saves, schema integrity, and Markdown generation.
"""
import json
import pytest
from pathlib import Path
from msk_therapy_os.project_io.project_manager import ProjectManager


def test_create_default_project_schema():
    proj = ProjectManager.create_default_project("test_proj_001")
    assert proj["project_id"] == "test_proj_001"
    assert proj["schema_version"] == "1.0.0"
    assert proj["scope"] == "ENGINEERING_RESEARCH_ONLY"
    assert "body_parameters" in proj
    assert "current_pose" in proj
    assert "surface_anchors" in proj


def test_atomic_save_and_load_project(tmp_path: Path):
    target_file = tmp_path / "subfolder" / "my_project.mskproj"
    data = ProjectManager.create_default_project("proj_persist_test")
    data["body_parameters"]["preset_name"] = "slender"
    data["body_parameters"]["height_scale"] = 1.05

    saved_path = ProjectManager.save_project(target_file, data)
    assert Path(saved_path).exists()
    assert saved_path.endswith(".mskproj")

    loaded = ProjectManager.load_project(Path(saved_path))
    assert loaded["project_id"] == "proj_persist_test"
    assert loaded["body_parameters"]["preset_name"] == "slender"
    assert loaded["body_parameters"]["height_scale"] == 1.05


def test_load_non_existent_or_corrupted_file_raises_error(tmp_path: Path):
    non_existent = tmp_path / "missing.mskproj"
    with pytest.raises(FileNotFoundError):
        ProjectManager.load_project(non_existent)

    corrupted = tmp_path / "corrupted.mskproj"
    corrupted.write_text('{"bad_key": 123}', encoding="utf-8")
    with pytest.raises(ValueError, match="Corrupted or invalid"):
        ProjectManager.load_project(corrupted)


def test_export_markdown_report_contains_governance_disclaimers():
    data = ProjectManager.create_default_project("report_test")
    md = ProjectManager.export_markdown_report(data)

    assert "# MSK-Therapy-OS V1.0 — Báo Cáo Phiên Nghiên Cứu" in md
    assert "ENGINEERING_RESEARCH_ONLY" in md
    assert "LI4" in md
    assert "LI14" in md
    assert "LI15" in md
    assert "Creative Commons Attribution 4.0 International (CC BY 4.0)" in md
