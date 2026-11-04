"""Test suite for Milestone P22: Anatomical Source-of-Truth Registry, LI4/ST36/KI3 Lineage & Negative Tests."""
import pytest
from research.workbench.coordinate_registry import (
    CoordinateRegistry,
    ScaleDivergenceError,
    LateralityInversionConflictError,
    MeshChecksumMismatchError,
    IncompletePathwayError,
)

class TestP22CoreAcupointLineage:
    def test_li4_provenance_and_contract(self):
        li4 = CoordinateRegistry.get_landmark("LI4")
        assert li4 is not None
        assert li4.code == "LI4"
        assert li4.name_zh == "合谷"
        assert "Second metacarpal bone" in li4.skeletal_anchor or "metacarpal" in li4.skeletal_anchor.lower()
        assert "WHO Standard 2008" in li4.who_reference
        assert "FMA:23910" in li4.fma_id
        assert li4.review_status == "EXPERT_REVIEW_PENDING"
        assert li4.side == "RIGHT"

    def test_st36_provenance_and_contract(self):
        st36 = CoordinateRegistry.get_landmark("ST36")
        assert st36 is not None
        assert st36.code == "ST36"
        assert st36.name_zh == "足三里"
        assert "tibia" in st36.skeletal_anchor.lower()
        assert "tibialis anterior" in st36.skeletal_anchor.lower()
        assert "WHO Standard 2008" in st36.who_reference
        assert "FMA:24476" in st36.fma_id
        assert st36.review_status == "EXPERT_REVIEW_PENDING"

    def test_ki3_provenance_and_contract(self):
        ki3 = CoordinateRegistry.get_landmark("KI3")
        assert ki3 is not None
        assert ki3.code == "KI3"
        assert ki3.name_zh == "太溪"
        assert "medial malleolus" in ki3.skeletal_anchor.lower()
        assert "calcaneal" in ki3.skeletal_anchor.lower() or "achilles" in ki3.description.lower()
        assert "WHO Standard 2008" in ki3.who_reference
        assert "FMA:51111" in ki3.fma_id
        assert ki3.review_status == "EXPERT_REVIEW_PENDING"


class TestP22CoordinateTransformDeterminism:
    def test_canonical_blender_roundtrip(self):
        for code in ["LI4", "ST36", "KI3"]:
            landmark = CoordinateRegistry.get_landmark(code)
            orig = landmark.canonical_coords
            blender_coords = CoordinateRegistry.canonical_to_blender(orig)
            reconstructed = CoordinateRegistry.blender_to_canonical(blender_coords)

            for i in range(3):
                assert abs(orig[i] - reconstructed[i]) < 1e-12, f"Roundtrip error on {code} axis {i}"

    def test_raw_bp3d_mm_to_canonical(self):
        # Sample raw millimeter coordinate on vertex
        raw_mm = [245.0, -225.0, 814.0] # in mm, Z-up
        canonical = CoordinateRegistry.raw_bp3d_mm_to_canonical(raw_mm)
        assert abs(canonical[0] - 0.245) < 1e-6
        # Expected Y: z*0.001 + 0.0781112 = 0.814 + 0.0781112 = 0.8921112
        assert abs(canonical[1] - 0.8921112) < 1e-6
        # Expected Z: -y*0.001 - 0.1 = 0.225 - 0.1 = 0.125
        assert abs(canonical[2] - 0.125) < 1e-6


class TestP22NegativeTestsFailClosed:
    def test_scale_divergence_fails_closed(self):
        # Millimeter values passed where meters expected
        mm_coords = [245.0, 892.0, 125.0]
        with pytest.raises(ScaleDivergenceError):
            CoordinateRegistry.validate_coordinate_scale(mm_coords, expected_units="meters")

    def test_laterality_inversion_fails_closed(self):
        # Point declared RIGHT but with negative X (left side)
        inverted_right = [-0.245, 0.892, 0.125]
        with pytest.raises(LateralityInversionConflictError):
            CoordinateRegistry.validate_laterality_sign("LI4", "RIGHT", inverted_right)

        # Point declared LEFT but with positive X (right side)
        inverted_left = [0.245, 0.892, 0.125]
        with pytest.raises(LateralityInversionConflictError):
            CoordinateRegistry.validate_laterality_sign("LI4", "LEFT", inverted_left)

    def test_mesh_checksum_mismatch_fails_closed(self):
        expected_hash = "3828b519f7a4ec1a98a560e58101e1289eb07a85ce8dfdd151c6dc3cda9327b4"
        mutated_hash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        with pytest.raises(MeshChecksumMismatchError):
            CoordinateRegistry.validate_mesh_checksum(expected_hash, mutated_hash, "Humerus_R")

    def test_incomplete_meridian_pathway_fails_closed(self):
        # Pathway with only 2 waypoints (minimum required is 4)
        short_wps = [[0.1, 0.2, 0.3], [0.15, 0.25, 0.35]]
        with pytest.raises(IncompletePathwayError):
            CoordinateRegistry.validate_waypoint_completeness(short_wps, min_count=4)
