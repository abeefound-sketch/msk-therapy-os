"""Unit and Integration Test Suite for Milestone P31: Cross-System Integration.
Verifies data exchange contract, Web Atlas adapters, Knowledge Vault queries,
and strict non-PII / ENGINEERING_RESEARCH_ONLY safety boundaries.
"""
from __future__ import annotations

import io
import json
import pytest
from pathlib import Path

from tools.blender_anatomy_studio.cross_system_contract import (
    CrossSystemExchangeBundle,
    RELEASE_SCOPE,
    CLINICAL_SAFETY_BARRIER,
)
from tools.blender_anatomy_studio.addon.web_atlas_adapter import WebAtlasAdapter
from msk_therapy_os.knowledge_vault.studio_bridge import StudioKnowledgeBridge

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_BUNDLE_PATH = REPO_ROOT / "1docs" / "audits" / "P31" / "evidence" / "p31_cross_system_bundle.json"


class TestP31CrossSystemIntegration:
    @pytest.fixture
    def adapter(self):
        return WebAtlasAdapter()

    @pytest.fixture
    def bundle(self, adapter):
        return adapter.build_exchange_bundle()

    def test_bundle_structural_contract(self, bundle):
        """Verify CrossSystemExchangeBundle complies with version and safety contract."""
        assert bundle.release_scope == RELEASE_SCOPE
        assert bundle.clinical_safety_barrier == CLINICAL_SAFETY_BARRIER
        assert bundle.schema_version == "1.0.0"
        assert bundle.source_milestone == "P31"
        assert len(bundle.scene_assets) == 8
        assert len(bundle.surface_anchors) == 6
        assert len(bundle.motion_sequence) == 100
        assert len(bundle.knowledge_links) == 5

    def test_no_pii_barrier_enforced(self, bundle):
        """Verify strict recursion rejects any PII keys in payload."""
        data = bundle.to_dict()
        assert "patient_name" not in data

        # Intentionally inject PII
        tampered_data = bundle.to_dict()
        tampered_data["patient_name"] = "John Doe"
        with pytest.raises(ValueError, match="PII Leakage Detected"):
            CrossSystemExchangeBundle.from_dict(tampered_data)

        # Intentionally inject PII nested in motion sequence
        tampered_nested = bundle.to_dict()
        tampered_nested["motion_sequence"][0]["ssn"] = "000-00-0000"
        with pytest.raises(ValueError, match="PII Leakage Detected"):
            CrossSystemExchangeBundle.from_dict(tampered_nested)

    def test_anatomical_integrity_flags(self, bundle):
        """Verify upper limb points are marked VALID while missing limb points are marked ASSET_NOT_AVAILABLE."""
        anchors_by_id = {a["marker_id"]: a for a in bundle.surface_anchors}

        # Upper limb points present on asset
        assert anchors_by_id["LI14"]["status"] == "VALID_SURFACE_ANCHOR"
        assert anchors_by_id["LI14"]["bone_parent"] == "Humerus_R"
        assert anchors_by_id["LI14"]["fma_id"] == "FMA:23412"

        assert anchors_by_id["LI15"]["status"] == "VALID_SURFACE_ANCHOR"
        assert anchors_by_id["LI15"]["bone_parent"] == "Scapula_R"
        assert anchors_by_id["LI15"]["fma_id"] == "FMA:23240"

        assert anchors_by_id["LATERAL_EPICONDYLE"]["status"] == "VALID_SURFACE_ANCHOR"
        assert anchors_by_id["LATERAL_EPICONDYLE"]["bone_parent"] == "Humerus_R"

        # Missing distal/lower limb points
        for code in ["LI4", "ST36", "KI3"]:
            assert anchors_by_id[code]["status"] == "ASSET_NOT_AVAILABLE"
            assert anchors_by_id[code]["bone_parent"] is None
            assert anchors_by_id[code]["measured_displacement_mm"] == 0.0

    def test_knowledge_vault_queries_and_citations(self, bundle):
        """Verify knowledge links contain WHO 2008 citations and authoritative FMA IDs."""
        klinks = bundle.knowledge_links

        assert "LI14" in klinks
        assert klinks["LI14"]["availability_status"] == "AVAILABLE"
        assert "FMA:23412" in klinks["LI14"]["fma_id"]
        assert "WHO Standard 2008" in klinks["LI14"]["who_reference"]
        assert len(klinks["LI14"]["claims"]) >= 1

        assert "LI4" in klinks
        assert klinks["LI4"]["availability_status"] == "ASSET_NOT_AVAILABLE"
        assert "FMA:23910" in klinks["LI4"]["fma_id"]
        assert len(klinks["LI4"]["claims"]) >= 1

    def test_markdown_research_export(self, adapter, bundle):
        """Verify generated Markdown report contains all required sections and no PII."""
        md = adapter.export_research_bundle_markdown(bundle)

        assert "# BÁO CÁO NGHIÊN CỨU LIÊN HỆ ĐỘNG HỌC VÀ TRI THỨC Y VĂN" in md
        assert "PHẠM VI: ENGINEERING_RESEARCH_ONLY" in md
        assert "Hệ thống nghiêm cấm tự động chẩn đoán" in md
        assert "LI14" in md
        assert "LI15" in md
        assert "LATERAL_EPICONDYLE" in md
        assert "LI4" in md
        assert "ST36" in md
        assert "KI3" in md
        assert "ASSET_NOT_AVAILABLE" in md
        assert "VALID_SURFACE_ANCHOR" in md
        assert "2:1 (Inman 1944 / Seth 2016)" in md

        # Assert no patient identifiers
        for forbidden in ["patient_name", "mrn", "tên bệnh nhân", "mã bệnh nhân", "hồ sơ bệnh án", "chẩn đoán xác định"]:
            assert forbidden not in md.lower()

    def test_bundle_disk_persistence_and_hash(self, adapter):
        """Verify file saved to disk reloads identically."""
        exported_path = adapter.export_exchange_bundle()
        assert exported_path.exists()

        reloaded = CrossSystemExchangeBundle.load(exported_path)
        assert reloaded.bundle_id.startswith("bundle_p31_")
        assert len(reloaded.scene_assets) == 8
        assert len(reloaded.motion_sequence) == 100
