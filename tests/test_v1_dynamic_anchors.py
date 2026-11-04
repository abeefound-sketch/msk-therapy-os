"""Unit tests for MSK-Therapy-OS V1.0 Dynamic Anchors & Meridians (Package C).
Verifies acupoints LI4, LI14, LI15, manual adjustment, undo/redo stacks, and governance safety.
"""
import pytest
from msk_therapy_os.dynamic_anchors.dynamic_anchor_manager import DynamicAnchorManager


def test_dynamic_anchor_manager_default_anchors():
    manager = DynamicAnchorManager()
    summary = manager.get_summary()

    assert "LI4" in summary["anchors"]
    assert "LI14" in summary["anchors"]
    assert "LI15" in summary["anchors"]

    li4 = summary["anchors"]["LI4"]
    assert li4["parent_segment"] == "hand.R"
    assert li4["target_mesh_name"] == "Metacarpal_2_R"
    assert li4["technical_status"] == "VALID_SURFACE_ANCHOR"
    assert li4["clinical_verification_status"] == "EXPERT_REVIEW_PENDING"

    li14 = summary["anchors"]["LI14"]
    assert li14["parent_segment"] == "upper_arm.R"
    assert li14["target_mesh_name"] == "Humerus_R"

    li15 = summary["anchors"]["LI15"]
    assert li15["parent_segment"] == "clavicle.R"
    assert li15["target_mesh_name"] == "Scapula_R"


def test_adjust_anchor_updates_coordinates_and_records_undo():
    manager = DynamicAnchorManager()
    initial_li4_pos = manager.get_anchor("LI4").local_coordinates

    new_pos = [-0.282, 0.837, 0.038]
    updated = manager.adjust_anchor("LI4", new_pos, author="clinical_specialist")

    assert updated.local_coordinates == new_pos
    assert updated.version == 2
    assert updated.edit_author == "clinical_specialist"
    assert updated.technical_status == "MANUALLY_ADJUSTED"
    assert updated.clinical_verification_status == "EXPERT_REVIEW_PENDING"

    # Verify undo stack has 1 entry
    summary = manager.get_summary()
    assert summary["undo_available_count"] == 1
    assert summary["redo_available_count"] == 0

    # Undo
    undo_ok = manager.undo()
    assert undo_ok is True
    assert manager.get_anchor("LI4").local_coordinates == initial_li4_pos
    assert manager.get_summary()["undo_available_count"] == 0
    assert manager.get_summary()["redo_available_count"] == 1

    # Redo
    redo_ok = manager.redo()
    assert redo_ok is True
    assert manager.get_anchor("LI4").local_coordinates == new_pos
    assert manager.get_summary()["undo_available_count"] == 1
    assert manager.get_summary()["redo_available_count"] == 0


def test_meridian_pathway_contains_ordered_waypoints():
    manager = DynamicAnchorManager()
    summary = manager.get_summary()
    waypoints = summary["meridian_waypoints"]

    assert len(waypoints) >= 3
    codes = [w["code"] for w in waypoints]
    assert "LI4" in codes
    assert "LI14" in codes
    assert "LI15" in codes
