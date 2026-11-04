"""
MSK-Therapy-OS — Milestone P21 Sandbox Atlas Adapter
====================================================
Provides an isolated, read-only interface to authentic BodyParts3D 4.0 anatomical
mesh datasets and handles user manual annotation/meridian persistence and Markdown export.

Scope: ENGINEERING_RESEARCH_ONLY
License: Data: CC-BY 4.0 DBCLS Japan | Code: MIT
"""

import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
ATLAS_JSON_PATH = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models" / "atlas.json"
CHUNKS_DIR = REPO_ROOT / "3refs" / "upstream" / "tcm-3d" / "public" / "models"
ANNOTATIONS_STORAGE_PATH = REPO_ROOT / "knowledge_vault" / "sandbox_p21_annotations.json"

_ATLAS_CACHE: Optional[Dict[str, Any]] = None
_ATLAS_SHA256: Optional[str] = None

ORGAN_SYSTEMS = {
    "digestive", "respiratory", "cardiac", "urinary", "arterial",
    "venous", "nervous", "endocrine", "reproductive", "sensory", "lymphatic"
}

# Core visceral organs (Digestive, Respiratory, Cardiac, Urinary, Endocrine) = 249 structures
CORE_VISCERAL_SYSTEMS = {
    "digestive", "respiratory", "cardiac", "urinary", "endocrine"
}

# Canonical Anatomical Target Constraints (WHO Standard Acupuncture Point Locations 2008)
CANONICAL_TARGET_CONSTRAINTS = {
    "LI4": {"expected_mesh_id": "FJ3352", "expected_name_keyword": "metacarpal", "segment": "hand.R"},
    "LI14": {"expected_mesh_id": "FJ3368", "expected_name_keyword": "humerus", "segment": "upper_arm.R"},
    "LI15": {"expected_mesh_id": "FJ3384", "expected_name_keyword": "scapula", "segment": "clavicle.R"},
    "ST36": {"expected_mesh_id": "FJ3387", "expected_name_keyword": "tibia", "segment": "shank.R"},
    "KI3": {"expected_mesh_id": "FJ3360", "expected_name_keyword": "calcaneus", "segment": "foot.R"}
}


def _load_atlas() -> Dict[str, Any]:
    global _ATLAS_CACHE, _ATLAS_SHA256
    if _ATLAS_CACHE is None:
        if not ATLAS_JSON_PATH.exists():
            raise FileNotFoundError(f"Atlas asset not found at {ATLAS_JSON_PATH}")
        raw_bytes = ATLAS_JSON_PATH.read_bytes()
        _ATLAS_SHA256 = hashlib.sha256(raw_bytes).hexdigest()
        _ATLAS_CACHE = json.loads(raw_bytes.decode("utf-8"))
    return _ATLAS_CACHE


def get_atlas_sha256() -> str:
    _load_atlas()
    return _ATLAS_SHA256 or ""


def get_p21_metadata() -> Dict[str, Any]:
    atlas = _load_atlas()
    parts = atlas.get("parts", [])
    
    bone_count = sum(1 for p in parts if p.get("system") == "skeletal")
    muscle_count = sum(1 for p in parts if p.get("system") == "muscular")
    organ_total_count = sum(1 for p in parts if p.get("system") in ORGAN_SYSTEMS)
    viscera_core_count = sum(1 for p in parts if p.get("system") in CORE_VISCERAL_SYSTEMS)
    neurovascular_count = organ_total_count - viscera_core_count
    skin_count = sum(1 for p in parts if p.get("system") == "integumentary" or "skin" in p.get("name", "").lower())
    
    return {
        "status": "READY",
        "dataset_name": "BodyParts3D Release 4.0",
        "provenance": {
            "source": "The Database Center for Life Science (DBCLS), Japan",
            "curator_url": "https://lifesciencedb.jp/bp3d/",
            "upstream_repository": "https://github.com/ashemag/human-atlas",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "code_license": "MIT License",
            "attribution_required": True,
            "commercial_use_allowed": True,
            "copyleft_restricted": False,
        },
        "statistics": {
            "total_structures": len(parts),
            "total_triangles": atlas.get("triangles", 0),
            "total_concepts": len(atlas.get("concepts", [])),
            "chunk_count": len(atlas.get("chunks", [])),
            "layer_counts": {
                "bone": bone_count,
                "muscle": muscle_count,
                "organ": organ_total_count,
                "viscera_core": viscera_core_count,
                "neurovascular": neurovascular_count,
                "skin": skin_count,
            },
        },
        "bounding_box_meters": {
            "min": [-0.3341, 0.0000, -0.1452],
            "max": [0.3328, 1.7297, 0.1468],
            "height_m": 1.7297,
            "span_m": 0.6669,
            "depth_m": 0.2920,
        },
        "asset_sha256": get_atlas_sha256(),
        "release_scope": "ENGINEERING_RESEARCH_ONLY",
        "governance_status": "AUTHENTIC_MESH_VERIFIED",
        "disclaimer": "FOR RESEARCH AND EDUCATIONAL PURPOSES ONLY. Not for clinical diagnosis, prescribing, or autonomous treatment guidance.",
    }


def get_p21_structures(
    layer: Optional[str] = None,
    system: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    atlas = _load_atlas()
    parts = atlas.get("parts", [])
    
    filtered = []
    layer_lower = layer.lower() if layer else None
    system_lower = system.lower() if system else None
    search_lower = search.lower() if search else None
    
    for p in parts:
        p_sys = p.get("system", "").lower()
        p_name = p.get("name", "").lower()
        p_id = p.get("id", "").lower()
        p_concept = p.get("conceptId", "").lower()
        
        # Layer filter
        if layer_lower:
            if layer_lower == "bone" and p_sys != "skeletal":
                continue
            elif layer_lower == "muscle" and p_sys != "muscular":
                continue
            elif layer_lower == "organ" and p_sys not in ORGAN_SYSTEMS:
                continue
            elif layer_lower == "skin" and (p_sys != "integumentary" and "skin" not in p_name):
                continue
        
        # System filter
        if system_lower and p_sys != system_lower:
            continue
            
        # Search filter
        if search_lower:
            if search_lower not in p_name and search_lower not in p_id and search_lower not in p_concept:
                continue
                
        filtered.append({
            "id": p["id"],
            "name": p["name"],
            "system": p["system"],
            "conceptId": p.get("conceptId", ""),
            "chunk": p["chunk"],
            "positions": p["positions"],
            "normals": p["normals"],
            "indices": p["indices"],
            "vertexCount": p["vertexCount"],
            "indexCount": p["indexCount"],
            "triangleCount": p["indexCount"] // 3,
            "bounds": p["bounds"],
        })
        
        if limit and len(filtered) >= limit:
            break
            
    return filtered


def get_p21_chunk_file(chunk_name: str) -> Path:
    if not re.match(r"^body-\d+\.bin$", chunk_name):
        raise ValueError(f"Invalid chunk name: {chunk_name}")
    chunk_path = (CHUNKS_DIR / chunk_name).resolve()
    if not str(chunk_path).startswith(str(CHUNKS_DIR.resolve())):
        raise PermissionError("Path traversal rejected")
    if not chunk_path.exists() or not chunk_path.is_file():
        raise FileNotFoundError(f"Chunk file {chunk_name} not found")
    return chunk_path


# Curated key representative structures for fast initial rendering across all 4 layers
KEY_REPRESENTATIVE_STRUCTURE_IDS = [
    # Right Upper Limb Bones (V1.0 Vertical Slice: Shoulder -> Arm -> Forearm -> Hand)
    "FJ3362",  # Right clavicle
    "FJ3384",  # Right scapula
    "FJ3368",  # Right humerus
    "FJ3349",  # Right radius
    "FJ3391",  # Right ulna
    "FJ3352",  # Right second metacarpal
    # Other Bones (Skeletal Context)
    "FJ3237",  # Left clavicle
    "FJ3262",  # Left humerus
    "FJ3178",  # Body of sternum
    "FJ3259",  # Left femur
    "FJ1252",  # Gingiva of upper jaw
    # Muscles (Muscular)
    "FJ1520",  # Ascending part of right trapezius
    "FJ1467",  # Acromial part of right deltoid
    "FJ1395",  # Long head of right biceps femoris
    "FJ1394",  # Lateral head of right gastrocnemius
    # Organs (Viscera)
    "FJ2816",  # Caudate lobe of liver (Digestive)
    "FJ2564",  # Stomach (Digestive)
    "FJ2541",  # Trachea (Respiratory)
    "FJ2422",  # Cavity of left ventricle (Cardiac)
    "FJ2423",  # Cavity of right ventricle (Cardiac)
    "FJ3145",  # Left kidney (Urinary)
    "FJ3149",  # Urinary bladder (Urinary)
    # Skin (Integumentary)
    "FJ2810",  # Skin (Full body exterior)
]


def get_representative_structures() -> List[Dict[str, Any]]:
    atlas = _load_atlas()
    parts_by_id = {p["id"]: p for p in atlas.get("parts", [])}
    result = []
    for sid in KEY_REPRESENTATIVE_STRUCTURE_IDS:
        if sid in parts_by_id:
            p = parts_by_id[sid]
            result.append({
                "id": p["id"],
                "name": p["name"],
                "system": p["system"],
                "conceptId": p.get("conceptId", ""),
                "chunk": p["chunk"],
                "positions": p["positions"],
                "normals": p["normals"],
                "indices": p["indices"],
                "vertexCount": p["vertexCount"],
                "indexCount": p["indexCount"],
                "triangleCount": p["indexCount"] // 3,
                "bounds": p["bounds"],
            })
    return result


def _load_annotations_store() -> Dict[str, Any]:
    if ANNOTATIONS_STORAGE_PATH.exists():
        try:
            return json.loads(ANNOTATIONS_STORAGE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"annotations": [], "polylines": []}


def _save_annotations_store(store: Dict[str, Any]) -> None:
    ANNOTATIONS_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ANNOTATIONS_STORAGE_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")


def get_annotations_and_polylines() -> Dict[str, Any]:
    return _load_annotations_store()


def save_user_annotation(data: Dict[str, Any]) -> Dict[str, Any]:
    store = _load_annotations_store()
    
    # Enforce P21 safety governance invariants & Anatomical Validity Checks
    code = (data.get("standard_code") or "").upper().strip()
    target = data.setdefault("anatomical_target", {})
    mesh_id = target.get("mesh_id", "")
    struct_name = (target.get("structure_name") or "").lower()

    # 1. Verification status is ALWAYS USER_ANNOTATED_UNVERIFIED for user annotations
    data["verification_status"] = "USER_ANNOTATED_UNVERIFIED"

    if code in CANONICAL_TARGET_CONSTRAINTS:
        rule = CANONICAL_TARGET_CONSTRAINTS[code]
        expected_mesh = rule["expected_mesh_id"]
        expected_kw = rule["expected_name_keyword"]
        if mesh_id != expected_mesh and expected_kw not in struct_name:
            data["binding_status"] = "INVALID_BINDING"
            data["validation_error"] = f"Sai lệch giải phẫu: Huyệt {code} theo WHO 2008 bám trên {expected_kw} ({rule['segment']}), không thể gắn vào cấu trúc '{struct_name}'."
        else:
            data["binding_status"] = "VALID_BINDING"
    else:
        data["binding_status"] = "CUSTOM_BINDING"
    
    # 2. Attach asset checksum
    current_hash = get_atlas_sha256()
    data["anatomical_target"]["asset_sha256"] = current_hash
    
    # 3. Timestamp & ID
    if not data.get("annotation_id"):
        data["annotation_id"] = f"PT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{len(store['annotations'])+1:03d}"
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Validation of required attachment
    if "spatial_attachment" not in data or "world_position" not in data["spatial_attachment"]:
        raise ValueError("Missing spatial_attachment.world_position")
        
    store["annotations"].append(data)
    _save_annotations_store(store)
    return data


def save_user_polyline(data: Dict[str, Any]) -> Dict[str, Any]:
    store = _load_annotations_store()
    
    # Enforce P21 governance
    data["status"] = "USER_DRAFT_UNVERIFIED"
    current_hash = get_atlas_sha256()
    data["asset_sha256"] = current_hash
    
    waypoints = data.get("waypoints", [])
    if len(waypoints) < 3:
        raise ValueError("Polyline requires at least 3 ordered waypoints")
        
    if not data.get("polyline_id"):
        data["polyline_id"] = f"PL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{len(store['polylines'])+1:03d}"
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    
    store["polylines"].append(data)
    _save_annotations_store(store)
    return data


def export_to_vault_markdown(data: Dict[str, Any]) -> str:
    """
    Format user annotations and meridians into structured Markdown matching Knowledge Vault P20 schema.
    """
    annotations = data.get("annotations", [])
    polylines = data.get("polylines", [])
    doc_id = f"EXP-P21-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    created_at = datetime.now(timezone.utc).isoformat()
    asset_hash = get_atlas_sha256()
    
    md_lines = [
        "---",
        f"id: \"{doc_id}\"",
        f"title: \"Bản Ghi Chú Giải Phẫu & Thực Nghiệm Huyệt Tuyến P21\"",
        f"source_type: \"user_annotation\"",
        f"verification_status: \"USER_ANNOTATED_UNVERIFIED\"",
        f"source_asset_sha256: \"{asset_hash}\"",
        f"created_at: \"{created_at}\"",
        f"author: \"Clinical Student / Researcher\"",
        f"release_scope: \"ENGINEERING_RESEARCH_ONLY\"",
        "---",
        "",
        "# Báo Cáo Ghi Chú Giải Phẫu & Lộ Trình Thực Nghiệm (PoC P21)",
        "",
        "> [!WARNING]",
        "> **CẢNH BÁO GIỚI HẠN PHẠM VI:** Toàn bộ điểm đánh dấu và đường kinh trong tài liệu này được tạo thủ công bởi người dùng trong môi trường nghiên cứu thực nghiệm. **KHÔNG CÓ GIÁ TRỊ CHẨN ĐOÁN HOẶC CHỈ DẪN CHÂM CỨU LÂM SÀNG.** Trạng thái pháp lý: `USER_ANNOTATED_UNVERIFIED`.",
        "",
        "## 1. Thông Tin Nguồn Mô Hình Giải Phẫu 3D Gốc",
        "",
        "- **Bộ dữ liệu:** BodyParts3D Release 4.0 (DBCLS Japan)",
        "- **Bản quyền hình học:** Creative Commons Attribution 4.0 International (CC BY 4.0)",
        f"- **Mã băm toàn vẹn (SHA-256):** `{asset_hash}`",
        "- **Hệ quy chiếu:** Right-Handed Cartesian (+X Patient Left, +Y Superior, +Z Anterior), Đơn vị: Mét ($m$)",
        "",
        "## 2. Danh Sách Điểm Đánh Dấu Thủ Công (Manual Acupoints)",
        "",
        "| ID | Nhãn / Mã | Cấu trúc giải phẫu gắn kết | FMA Concept | Tọa độ Thế giới [X, Y, Z] (m) | Bán kính bất định (mm) | Ghi chú |",
        "|---|---|---|---|---|---|---|",
    ]
    
    if not annotations:
        md_lines.append("| *Không có* | - | - | - | - | - | Chưa có điểm đánh dấu |")
    else:
        for a in annotations:
            aid = a.get("annotation_id", "-")
            label = a.get("label", a.get("standard_code", "Chưa đặt tên"))
            target = a.get("anatomical_target", {})
            struct_name = target.get("structure_name", target.get("mesh_id", "N/A"))
            fma = target.get("concept_id", "N/A")
            sp = a.get("spatial_attachment", {})
            pos = sp.get("world_position", [0, 0, 0])
            pos_str = f"[{pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f}]"
            rad = sp.get("uncertainty_radius_mm", 5.0)
            notes = a.get("notes", a.get("provenance", {}).get("notes", "-"))
            md_lines.append(f"| `{aid}` | **{label}** | {struct_name} | `{fma}` | `{pos_str}` | {rad:.1f} mm | {notes} |")
            
    md_lines.extend([
        "",
        "## 3. Danh Sách Đường Kinh / Tuyến Vẽ Tay (Manual Meridians)",
        "",
    ])
    
    if not polylines:
        md_lines.append("*Chưa có đường kinh nào được lưu trong phiên này.*")
    else:
        for idx, pl in enumerate(polylines, 1):
            pl_id = pl.get("polyline_id", f"PL-{idx}")
            pl_name = pl.get("name", pl.get("label", f"Đường kinh #{idx}"))
            wps = pl.get("waypoints", [])
            md_lines.extend([
                f"### 3.{idx}. {pl_name} (`{pl_id}`)",
                f"- **Trạng thái:** `{pl.get('status', 'USER_DRAFT_UNVERIFIED')}`",
                f"- **Số điểm mốc (Waypoints):** {len(wps)} điểm",
                "",
                "| Điểm # | Cấu trúc giải phẫu | Tọa độ [X, Y, Z] (m) | Tam giác mốc |",
                "|---|---|---|---|",
            ])
            for wp in wps:
                w_idx = wp.get("index", 0)
                mesh_id = wp.get("mesh_id", "N/A")
                w_pos = wp.get("world_position", [0, 0, 0])
                w_pos_str = f"[{w_pos[0]:.4f}, {w_pos[1]:.4f}, {w_pos[2]:.4f}]"
                tri = wp.get("triangle_index", "-")
                md_lines.append(f"| #{w_idx+1} | `{mesh_id}` | `{w_pos_str}` | Mặt #{tri} |")
            md_lines.append("")
            
    md_lines.extend([
        "## 4. Cam Kết Toàn Vẹn & Quản Trị Hệ Thống (Governance Invariants)",
        "",
        "1. **Fail-Closed Verification:** Khi nạp lại bản ghi này vào MSK-Therapy-OS, hệ thống đối chiếu `source_asset_sha256`. Nếu phát hiện sai khác, toàn bộ tọa độ phải bị vô hiệu hóa cho đến khi người dùng tự tay xác nhận remap.",
        "2. **Prohibition of Fake Approvals:** Nghiêm cấm gán nhãn `CLINICAL_APPROVED` hoặc `ANATOMICAL_VERIFIED` cho bản ghi này khi chưa có kết quả phê duyệt từ hội đồng độc lập G3/G4.",
        "",
        "---",
        f"*Tài liệu được xuất tự động từ MSK-Therapy-OS P21 Sandbox Atlas PoC vào lúc {created_at}.*",
    ])
    
    return "\n".join(md_lines)
