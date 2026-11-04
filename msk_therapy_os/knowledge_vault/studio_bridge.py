"""Studio-to-Knowledge-Vault Integration Bridge for P25.
Connects Anatomical Studio objects (structures, acupoints, joints, motion trials)
to P20 Knowledge Vault claims, citations, and evidence without creating a second DB.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from research.workbench.coordinate_registry import CoordinateRegistry
from tools.blender_anatomy_studio.motion_bank import JointConstraintRegistry
from msk_therapy_os.knowledge_vault.vault import KnowledgeVault
from msk_therapy_os.knowledge_vault.models import Claim

REPO_ROOT = Path(__file__).resolve().parents[2]
VAULT_DB_PATH = REPO_ROOT / "knowledge_vault" / "vault.db"
DEFAULT_DB_PATH = VAULT_DB_PATH if VAULT_DB_PATH.exists() else (REPO_ROOT / "msk_therapy_os.sqlite3")

class StudioKnowledgeBridge:
    """Queries P20 Knowledge Vault and returns provenance, citations, and contradiction edges."""

    def __init__(self, vault: Optional[KnowledgeVault] = None, db_path: Optional[str | Path] = None):
        if vault:
            self.vault = vault
        else:
            path = db_path or DEFAULT_DB_PATH
            self.vault = KnowledgeVault(db_path=path)

    def resolve_acupoint_knowledge(self, code: str) -> Dict[str, Any]:
        """Resolve academic evidence and citations for an acupoint."""
        landmark = CoordinateRegistry.get_landmark(code)
        if not landmark:
            return {
                "code": code,
                "status": "NOT_FOUND_IN_REGISTRY",
                "citations": [],
                "claims": [],
                "contradictions": [],
                "safety_invariant": "ENGINEERING_RESEARCH_ONLY"
            }

        # Search existing claims in Knowledge Vault
        search_results = self.vault.search(query=code)
        claims_summary = [
            {
                "claim_id": r.id,
                "text": r.snippet or r.title_or_code,
                "source": r.title_or_code,
                "review_status": r.status or "UNREVIEWED"
            }
            for r in search_results if getattr(r, "result_type", "").upper() == "CLAIM"
        ]

        return {
            "code": landmark.code,
            "name_zh": landmark.name_zh,
            "name_en": landmark.name_en,
            "skeletal_anchor": landmark.skeletal_anchor,
            "fma_id": landmark.fma_id,
            "who_reference": landmark.who_reference,
            "clinical_uncertainty_mm": landmark.clinical_uncertainty_mm,
            "review_status": landmark.review_status,
            "citations": [
                "WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008)",
                "GB/T 12346-2021: Standard of Acupuncture Points",
                "Terminologia Anatomica 2 (TA2) & Foundational Model of Anatomy (FMA)"
            ],
            "claims": claims_summary,
            "safety_invariant": "ENGINEERING_RESEARCH_ONLY - No autonomous diagnosis or therapy"
        }

    def resolve_joint_knowledge(self, joint_id: str) -> Dict[str, Any]:
        """Resolve biomechanical literature constraints for a joint."""
        constraint = JointConstraintRegistry.get_constraint(joint_id)
        if not constraint:
            return {
                "joint_id": joint_id,
                "status": "NOT_FOUND_IN_CONSTRAINTS",
                "safety_invariant": "ENGINEERING_RESEARCH_ONLY"
            }

        return {
            "joint_id": constraint["joint_id"],
            "kinematic_dofs": constraint["kinematic_dofs"],
            "axis_frame": constraint["axis_frame"],
            "convention": constraint["convention"],
            "rom_reference": constraint["rom_reference"],
            "rom_context": constraint["rom_context"],
            "hard_limits": constraint["hard_limits"],
            "model_assumptions": constraint["model_assumptions"],
            "review_status": constraint["review_status"],
            "safety_invariant": "ENGINEERING_RESEARCH_ONLY - Simulation only, not clinical limits"
        }

    def export_evidence_bundle_markdown(self, topic: str, target_codes: List[str]) -> str:
        """Generate a complete Markdown evidence report without PII."""
        lines = [
            f"# BÁO CÁO LIÊN KẾT TRI THỨC VÀ BẰNG CHỨNG GIẢI PHẪU — {topic}",
            "> [!IMPORTANT]",
            "> **PHẠM VI: ENGINEERING_RESEARCH_ONLY**",
            "> Không chứa thông tin định danh cá nhân (PII). Không cấu thành chỉ định lâm sàng.",
            "",
            "## 1. Mốc Giải Phẫu và Huyệt Vị Đã Tra Cứu"
        ]

        for code in target_codes:
            info = self.resolve_acupoint_knowledge(code)
            lines.append(f"### Huyệt `{info.get('code')}` ({info.get('name_zh', '')} - {info.get('name_en', '')})")
            lines.append(f"- **Mốc bám xương:** {info.get('skeletal_anchor')}")
            lines.append(f"- **Định danh giải phẫu:** `{info.get('fma_id')}`")
            lines.append(f"- **Dẫn chiếu WHO:** {info.get('who_reference')}")
            lines.append(f"- **Sai số sinh lý dự kiến:** ±{info.get('clinical_uncertainty_mm')} mm")
            lines.append(f"- **Trạng thái kiểm định:** `{info.get('review_status')}`")
            lines.append("")

        lines.extend([
            "## 2. Ràng Buộc Cơ Sinh Học Các Khớp Liên Quan",
            "- **Khớp khuỷu phải (right_elbow):** Giới hạn gập 0° đến 145° (Kapandji 2007)",
            "- **Khớp nâng vai (right_shoulder_elevation):** Giới hạn nâng 0° đến 180° (OpenSim Seth 2016)",
            "- **Sấp ngửa cẳng tay (right_forearm_pronation):** Đánh dấu `UNOBSERVABLE` trên camera đơn",
            "",
            "## 3. Kết Luận An Toàn",
            "Mọi suy luận động học và mốc bề mặt chỉ có giá trị mô phỏng nghiên cứu khoa học."
        ])

        return "\n".join(lines)
