"""Test suite for Milestone P25: Knowledge Vault Integration & Evidence Linking."""
import pytest
from msk_therapy_os.knowledge_vault.studio_bridge import StudioKnowledgeBridge
from msk_therapy_os.knowledge_vault.vault import KnowledgeVault

class TestP25KnowledgeIntegration:
    @pytest.fixture
    def bridge(self):
        return StudioKnowledgeBridge()

    def test_resolve_li4_knowledge(self, bridge):
        res = bridge.resolve_acupoint_knowledge("LI4")
        assert res["code"] == "LI4"
        assert "metacarpal" in res["skeletal_anchor"].lower()
        assert "WHO Standard 2008" in res["who_reference"]
        assert "FMA:23910" in res["fma_id"]
        assert res["review_status"] == "EXPERT_REVIEW_PENDING"
        assert "ENGINEERING_RESEARCH_ONLY" in res["safety_invariant"]

    def test_resolve_st36_and_ki3_knowledge(self, bridge):
        res_st36 = bridge.resolve_acupoint_knowledge("ST36")
        assert res_st36["code"] == "ST36"
        assert "tibia" in res_st36["skeletal_anchor"].lower()

        res_ki3 = bridge.resolve_acupoint_knowledge("KI3")
        assert res_ki3["code"] == "KI3"
        assert "medial malleolus" in res_ki3["skeletal_anchor"].lower()

    def test_resolve_joint_knowledge(self, bridge):
        res = bridge.resolve_joint_knowledge("right_elbow")
        assert res["joint_id"] == "right_elbow"
        assert "flexion_extension" in res["kinematic_dofs"]
        assert res["hard_limits"]["min"] == 0.0
        assert res["hard_limits"]["max"] == 145.0
        assert "Kapandji" in res["rom_reference"]

    def test_export_evidence_bundle_markdown_no_pii(self, bridge):
        md = bridge.export_evidence_bundle_markdown(
            topic="Chi Trên và Tuyến Kinh Dương Minh",
            target_codes=["LI4", "ST36"]
        )
        assert "ENGINEERING_RESEARCH_ONLY" in md
        assert "Huyệt `LI4`" in md
        assert "Huyệt `ST36`" in md
        assert "Khớp khuỷu phải" in md
        # Assert no patient identifiers
        for forbidden in ["patient_name", "ssn", "dob", "bệnh nhân", "hồ sơ bệnh án"]:
            assert forbidden not in md.lower()
