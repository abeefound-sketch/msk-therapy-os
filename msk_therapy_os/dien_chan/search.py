"""Vietnamese Condition and Symptom Search Engine for Dien Chan Facial Reflexology.

Provides Unicode diacritics stripping, accent-insensitive search,
synonym expansion, source-backed protocol resolution, and strict evidence gating.
Pure-Python, zero external dependencies.
"""
from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from typing import Any, Dict, List, Optional, Tuple


# Vietnamese diacritic replacement table
VIETNAMESE_ACCENT_MAP = {
    'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
    'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
    'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
    'đ': 'd',
    'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
    'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
    'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
    'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
    'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
    'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
    'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
    'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
    'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
}


def normalize_vietnamese_text(text: str) -> str:
    """Normalize text by converting to lower-case and stripping Vietnamese diacritics.

    Handles both NFC (precomposed) and NFD (decomposed) Unicode forms.
    """
    if not text:
        return ""
    # Decompose to NFC first for consistent character matching
    text_nfc = unicodedata.normalize("NFC", text.lower().strip())
    # Replace known Vietnamese single characters
    chars = []
    for ch in text_nfc:
        chars.append(VIETNAMESE_ACCENT_MAP.get(ch, ch))
    unaccented = "".join(chars)
    # Further decompose remaining diacritical marks via NFD
    unaccented = unicodedata.normalize("NFD", unaccented)
    cleaned = "".join(ch for ch in unaccented if unicodedata.category(ch) != "Mn")
    # Clean whitespace and non-alphanumeric punctuation
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


# Common Vietnamese stop words to exclude from fuzzy token matching
VIETNAMESE_STOPWORDS = {
    "va", "la", "cua", "trong", "cho", "cac", "nhung", "khi", "bi", "do",
    "co", "o", "tai", "theo", "voi", "ve", "de", "tu", "den", "rat",
    "khong", "chua", "duoc", "nay", "nhu", "benh", "trieu", "chung"
}


def search_dien_chan_conditions(db: sqlite3.Connection, query: str) -> Dict[str, Any]:
    """Search conditions, symptoms and return matching source-backed protocols.

    Pipeline:
    User Query -> Normalize Vietnamese -> Condition/Symptom Matching -> Source-Backed Protocol Lookup -> Point Group Resolution
    """
    if not query or not query.strip():
        return {
            "query": "",
            "total_matches": 0,
            "results": [],
            "message": "Vui lòng nhập từ khóa tìm kiếm triệu chứng hoặc tình trạng."
        }

    norm_query = normalize_vietnamese_text(query)
    # Filter stopwords and very short tokens for token overlap
    tokens = [t for t in norm_query.split() if len(t) >= 3 and t not in VIETNAMESE_STOPWORDS]

    cursor = db.execute("""
        SELECT condition_id, name_vi, name_en, normalized_vi, synonyms_vi, description_vi,
               category, clinical_red_flags
        FROM dien_chan_conditions
    """)
    conditions = cursor.fetchall()

    scored_matches: List[Tuple[float, Dict[str, Any]]] = []

    for row in conditions:
        cond_id, name_vi, name_en, norm_vi, syn_json, desc_vi, cat, red_flags = row
        synonyms = json.loads(syn_json) if syn_json else []

        score = 0.0
        match_reason = ""

        # 1. Exact query match on normalized condition name
        if norm_query == norm_vi:
            score = 1.0
            match_reason = "Khớp chính xác tên tình trạng"
        # 2. Exact match on normalized synonyms
        elif any(norm_query == normalize_vietnamese_text(s) for s in synonyms):
            score = 0.95
            match_reason = "Khớp chính xác từ đồng nghĩa"
        # 3. Substring match in normalized name (query length >= 3)
        elif len(norm_query) >= 3 and norm_query in norm_vi:
            score = 0.85
            match_reason = "Chứa cụm từ tìm kiếm trong tên tình trạng"
        # 4. Substring match in any synonym (query length >= 3)
        elif len(norm_query) >= 3 and any(norm_query in normalize_vietnamese_text(s) for s in synonyms):
            score = 0.80
            match_reason = "Chứa cụm từ tìm kiếm trong danh mục đồng nghĩa"
        # 5. Token overlap match (requires meaningful content tokens)
        elif tokens:
            norm_tokens_cond = set(t for t in norm_vi.split() if t not in VIETNAMESE_STOPWORDS)
            for s in synonyms:
                norm_tokens_cond.update(t for t in normalize_vietnamese_text(s).split() if t not in VIETNAMESE_STOPWORDS)
            overlap = [t for t in tokens if t in norm_tokens_cond]
            # Require at least 50% of user query content tokens to match
            if overlap and (len(overlap) / len(tokens)) >= 0.5:
                score = round(0.5 + 0.3 * (len(overlap) / len(tokens)), 2)
                match_reason = f"Trùng khớp từ khóa: {', '.join(overlap)}"

        if score > 0.4:
            # Fetch all protocols for this condition
            proto_cursor = db.execute("""
                SELECT p.protocol_id, p.title_vi, p.title_en, p.description_vi,
                       p.therapeutic_intent, p.evidence_level, p.safety_disclaimer_vi,
                       s.source_id, s.title, s.author, s.year
                FROM dien_chan_protocols p
                JOIN dien_chan_sources s ON p.source_id = s.source_id
                WHERE p.condition_id = ? AND p.status = 'ACTIVE'
            """, (cond_id,))
            protos = []
            for pr in proto_cursor.fetchall():
                pid = pr[0]
                # Fetch points for protocol
                pt_cur = db.execute("""
                    SELECT pp.point_code, pp.sequence_order, pp.technique, pp.duration_notes,
                           pt.name_vi, pt.grid_coordinate, pt.position_x, pt.position_y, pt.position_z,
                           pt.review_status, pt.uncertainty_mm
                    FROM dien_chan_protocol_points pp
                    JOIN dien_chan_points pt ON pp.point_code = pt.point_code
                    WHERE pp.protocol_id = ?
                    ORDER BY pp.sequence_order ASC
                """, (pid,))
                pts = []
                for pt_row in pt_cur.fetchall():
                    pts.append({
                        "point_code": pt_row[0],
                        "sequence_order": pt_row[1],
                        "technique": pt_row[2],
                        "duration_notes": pt_row[3],
                        "name_vi": pt_row[4],
                        "grid_coordinate": pt_row[5],
                        "position": [pt_row[6], pt_row[7], pt_row[8]],
                        "review_status": pt_row[9],
                        "uncertainty_mm": pt_row[10],
                    })

                protos.append({
                    "protocol_id": pid,
                    "title_vi": pr[1],
                    "title_en": pr[2],
                    "description_vi": pr[3],
                    "therapeutic_intent": pr[4],
                    "evidence_level": pr[5],
                    "safety_disclaimer_vi": pr[6],
                    "source": {
                        "source_id": pr[7],
                        "title": pr[8],
                        "author": pr[9],
                        "year": pr[10],
                    },
                    "point_codes": [pt["point_code"] for pt in pts],
                    "points": pts,
                })

            scored_matches.append((score, {
                "condition_id": cond_id,
                "name_vi": name_vi,
                "name_en": name_en,
                "description_vi": desc_vi,
                "category": cat,
                "clinical_red_flags": red_flags,
                "relevance_score": score,
                "match_reason": match_reason,
                "protocols": protos,
            }))

    # Sort descending by relevance score
    scored_matches.sort(key=lambda x: x[0], reverse=True)
    results = [m[1] for m in scored_matches]

    if not results:
        return {
            "query": query,
            "normalized_query": norm_query,
            "total_matches": 0,
            "results": [],
            "message": "Chưa có dữ liệu đã đối chiếu cho triệu chứng này.",
            "safety_note": "MSK-Therapy-OS chỉ hiển thị các nhóm huyệt có trong tài liệu đối chiếu đã xác minh, không tự động tạo phác đồ chưa qua kiểm chứng."
        }

    return {
        "query": query,
        "normalized_query": norm_query,
        "total_matches": len(results),
        "results": results,
        "message": f"Tìm thấy {len(results)} tình trạng phù hợp.",
    }
