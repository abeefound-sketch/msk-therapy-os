"""Adapter linking Knowledge Vault to 1docs/EVIDENCE.md without destructive modification."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from msk_therapy_os.knowledge_vault.vault import KnowledgeVault


class EvidenceCatalogAdapter:
    """Read-only bridge between 1docs/EVIDENCE.md and Knowledge Vault."""

    def __init__(self, evidence_md_path: str | Path, vault: KnowledgeVault):
        self.evidence_path = Path(evidence_md_path).resolve()
        self.vault = vault

    def parse_evidence_catalog(self) -> List[Dict[str, str]]:
        """Parse markdown table from 1docs/EVIDENCE.md without modifying it."""
        if not self.evidence_path.exists():
            return []

        lines = self.evidence_path.read_text(encoding="utf-8").splitlines()
        entries = []
        in_table = False

        for line in lines:
            line_str = line.strip()
            if line_str.startswith("| Evidence ID | Tier |"):
                in_table = True
                continue
            if in_table:
                if line_str.startswith("|---"):
                    continue
                if not line_str.startswith("|"):
                    in_table = False
                    continue

                cols = [c.strip() for c in line_str.strip("|").split("|")]
                if len(cols) >= 7:
                    # Strip backticks
                    ev_id = cols[0].strip("`").strip()
                    tier = cols[1].strip()
                    title_src = cols[2].strip()
                    org_year = cols[3].strip()
                    lic = cols[4].strip()
                    rev = cols[5].strip()
                    scope = cols[6].strip()

                    entries.append({
                        "evidence_id": ev_id,
                        "tier": tier,
                        "title_source": title_src,
                        "organization_year": org_year,
                        "license": lic,
                        "reviewer": rev,
                        "verified_scope": scope,
                    })

        return entries

    def sync_to_vault(self, actor: str = "evidence_adapter") -> int:
        """Import evidence catalog records into Knowledge Vault documents/claims idempotently."""
        entries = self.parse_evidence_catalog()
        imported_count = 0

        for entry in entries:
            ev_id = entry["evidence_id"]
            title = f"Evidence Catalog: {ev_id} - {entry['title_source']}"
            content = (
                f"# {ev_id}: {entry['title_source']}\n\n"
                f"- **Organization/Year:** {entry['organization_year']}\n"
                f"- **Tier:** {entry['tier']}\n"
                f"- **License:** {entry['license']}\n"
                f"- **Reviewer:** {entry['reviewer']}\n\n"
                f"## Verified Scope\n\n{entry['verified_scope']}\n"
            )

            # Namespace classification based on evidence ID prefix
            ns = "RESEARCH_NOTE"
            if ev_id.startswith("EVID-G"):
                ns = "CLINICAL_PROTOCOL"
            elif ev_id.startswith("EVID-A"):
                ns = "ANATOMY_EVIDENCE"
            elif ev_id.startswith("EVID-T"):
                ns = "TRADITIONAL_MERIDIAN"
            elif ev_id.startswith("EVID-D"):
                ns = "BIOMECHANICS"

            doc = self.vault.import_text(
                text=content,
                title=title,
                namespace=ns,
                author=entry["organization_year"],
                license_str=entry["license"],
                source_uri="1docs/EVIDENCE.md#" + ev_id,
                tags=["evidence_catalog", ev_id, f"tier_{entry['tier']}"],
                actor=actor,
            )

            # Add structured claim anchored to scope
            claim_text = entry["verified_scope"]
            source_quote = entry["verified_scope"]
            self.vault.add_claim(
                doc_id=doc.doc_id,
                claim_text=claim_text,
                source_quote=source_quote,
                claim_type="CONTRAINDICATION" if "Red flag" in claim_text or "contraindication" in claim_text else "ANATOMICAL_LOCATION",
                assertion_type="ASSERTION",
                status="SUPPORTED",
                evidence_tier=f"TIER_{entry['tier']}_EVIDENCE",
                actor=actor,
                uncertainty_notes=f"Reviewed by {entry['reviewer']}",
            )
            imported_count += 1

        return imported_count
