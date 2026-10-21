"""Medical Terminology Registry for MSK-Therapy-OS.

Provides multi-lingual lookup (English, Simplified Chinese, Vietnamese)
with standardized anatomical and traditional medicine identifiers:
FMA, BodyParts3D FJ, WHO Acupuncture standard, Vietnamese Dien Chan,
and Thai Sen Sib.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REGISTRY_PATH = Path(__file__).resolve().parent / "data" / "medical_terminology_registry.json"


class MedicalTerminologyRegistry:
    """Versioned singleton registry for anatomical & traditional clinical terms."""

    _instance: Optional[MedicalTerminologyRegistry] = None

    def __init__(self, data_path: Optional[Path] = None) -> None:
        path = data_path or REGISTRY_PATH
        if not path.exists():
            raise FileNotFoundError(f"Terminology registry not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            self.data: Dict[str, Any] = json.load(f)

        self.metadata = self.data.get("metadata", {})
        self.meridians = {m["code"]: m for m in self.data.get("meridians", [])}
        self.points = self.data.get("points", {})
        self.dien_chan = {d["code"]: d for d in self.data.get("dien_chan", [])}
        self.thai_sen_sib = {s["code"]: s for s in self.data.get("thai_sen_sib", [])}
        self.structures = {s["id"]: s for s in self.data.get("anatomy_structures", [])}
        self.regions = self.data.get("regions", {})
        self.movements = self.data.get("movements", {})
        self.clinical_terms = self.data.get("clinical_terms", {})

    @classmethod
    def get_instance(cls) -> MedicalTerminologyRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_term(self, term_id: str, lang: str = "en") -> Optional[Dict[str, Any]]:
        """Lookup term across all categories with localized fields."""
        # Check points
        if term_id in self.points:
            pt = self.points[term_id]
            return {
                "id": pt["id"],
                "code": pt["code"],
                "name": pt[f"name_{lang}"] if f"name_{lang}" in pt else pt["name_en"],
                "name_en": pt["name_en"],
                "name_zh": pt["name_zh"],
                "name_vi": pt.get("name_vi", pt["name_en"]),
                "pinyin": pt.get("pinyin", ""),
                "category": "acupuncture_point",
                "review_status": pt.get("review_status", "PROVISIONAL"),
                "provenance": pt.get("provenance", "")
            }
        # Check structures
        if term_id in self.structures:
            st = self.structures[term_id]
            return {
                "id": st["id"],
                "name": st[f"name_{lang}"] if f"name_{lang}" in st else st["name_en"],
                "name_en": st["name_en"],
                "name_zh": st["name_zh"],
                "name_vi": st["name_vi"],
                "category": "musculoskeletal_structure",
                "review_status": st.get("review_status", "VERIFIED"),
                "provenance": st.get("provenance", "")
            }
        # Check Dien Chan
        if term_id in self.dien_chan:
            dc = self.dien_chan[term_id]
            return {
                "id": dc["id"],
                "code": dc["code"],
                "name": dc[f"name_{lang}"] if f"name_{lang}" in dc else dc["name_en"],
                "category": "dien_chan_reflex",
                "review_status": dc.get("review_status", "VERIFIED_TRADITIONAL_REFLEX"),
                "provenance": dc.get("provenance", "")
            }
        return None

    def get_localized_structure_name(self, structure_id: str, raw_name: str, lang: str = "en") -> str:
        """Resolve localized name for a structure card in UI."""
        # 1. Match by structure_id
        if structure_id in self.structures:
            st = self.structures[structure_id]
            return st.get(f"name_{lang}", st["name_en"])

        # 2. Match by ACU-code
        if structure_id.startswith("ACU-"):
            code = structure_id[4:]
            if code in self.points:
                pt = self.points[code]
                if lang == "zh":
                    return f"{pt['name_zh']} ({pt['code']} / {pt['pinyin']})"
                elif lang == "vi":
                    return f"{pt['name_vi']} ({pt['code']} / {pt['name_zh']})"
                else:
                    return f"{pt['name_en']} ({pt['code']} / {pt['name_zh']})"

        # 3. Match by TRAD-THAI
        if "THAI" in structure_id:
            for s in self.thai_sen_sib.values():
                if s["id"] == structure_id or structure_id.endswith(s["code"].split("-")[-1]):
                    return s.get(f"name_{lang}", s["name_en"])

        # 4. Match by TRAD-DIEN
        if "DIEN" in structure_id:
            for d in self.dien_chan.values():
                if d["id"] == structure_id or structure_id.endswith(d["code"].split("-")[-1]):
                    return d.get(f"name_{lang}", d["name_en"])

        return raw_name
