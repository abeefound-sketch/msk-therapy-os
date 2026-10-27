"""SQLite Database Schema and DAO for Vietnamese Dien Chan Facial Reflexology.

Part of MSK-Therapy-OS local-first architecture.
Strictly isolated from WHO acupuncture namespace.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional
from uuid import uuid4

from msk_therapy_os.dien_chan.facial_registration import (
    FacialRegistrationEngine,
    ResolvedDienChanPoint,
)


def init_dien_chan_tables(db: sqlite3.Connection) -> None:
    """Create all Dien Chan knowledge tables if they do not exist."""
    db.executescript("""
    CREATE TABLE IF NOT EXISTS dien_chan_sources (
        source_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        edition TEXT,
        year INTEGER,
        license_status TEXT NOT NULL,
        image_path TEXT,
        image_sha256 TEXT,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS dien_chan_points (
        point_code TEXT PRIMARY KEY,
        name_vi TEXT NOT NULL,
        name_en TEXT NOT NULL,
        name_zh TEXT NOT NULL,
        description_vi TEXT,
        description_en TEXT,
        grid_coordinate TEXT NOT NULL,
        anatomical_location_vi TEXT,
        anatomical_location_en TEXT,
        position_x REAL NOT NULL,
        position_y REAL NOT NULL,
        position_z REAL NOT NULL,
        normal_x REAL NOT NULL,
        normal_y REAL NOT NULL,
        normal_z REAL NOT NULL,
        laterality TEXT NOT NULL,
        anatomical_region TEXT NOT NULL,
        source_id TEXT REFERENCES dien_chan_sources(source_id),
        review_status TEXT NOT NULL,
        uncertainty_mm REAL NOT NULL DEFAULT 1.5,
        projection_residual_mm REAL,
        fma_anchor TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS dien_chan_conditions (
        condition_id TEXT PRIMARY KEY,
        name_vi TEXT NOT NULL,
        name_en TEXT NOT NULL,
        normalized_vi TEXT NOT NULL,
        synonyms_vi TEXT NOT NULL,   -- JSON array of strings
        description_vi TEXT,
        category TEXT NOT NULL DEFAULT 'general',
        clinical_red_flags TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_dc_conditions_normalized ON dien_chan_conditions(normalized_vi);

    CREATE TABLE IF NOT EXISTS dien_chan_protocols (
        protocol_id TEXT PRIMARY KEY,
        condition_id TEXT NOT NULL REFERENCES dien_chan_conditions(condition_id),
        source_id TEXT NOT NULL REFERENCES dien_chan_sources(source_id),
        title_vi TEXT NOT NULL,
        title_en TEXT NOT NULL,
        description_vi TEXT,
        therapeutic_intent TEXT,
        evidence_level TEXT NOT NULL DEFAULT 'TRADITIONAL_REFLEXOLOGY_REFERENCE',
        safety_disclaimer_vi TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS dien_chan_protocol_points (
        protocol_id TEXT NOT NULL REFERENCES dien_chan_protocols(protocol_id),
        point_code TEXT NOT NULL REFERENCES dien_chan_points(point_code),
        sequence_order INTEGER NOT NULL,
        technique TEXT NOT NULL DEFAULT 'ray_an', -- 'day_an', 'go_bua', 'ho_ngai'
        duration_notes TEXT,
        laterality_rule TEXT NOT NULL DEFAULT 'both',
        PRIMARY KEY (protocol_id, point_code)
    );
    CREATE INDEX IF NOT EXISTS idx_dc_proto_pts_seq ON dien_chan_protocol_points(protocol_id, sequence_order);

    CREATE TABLE IF NOT EXISTS dien_chan_evidence (
        evidence_id TEXT PRIMARY KEY,
        target_type TEXT NOT NULL,   -- 'PROTOCOL' or 'POINT'
        target_id TEXT NOT NULL,
        evidence_type TEXT NOT NULL, -- 'TRADITIONAL_LITERATURE', 'PRACTITIONER_OBSERVATION', 'CLINICAL_TRIAL'
        description TEXT NOT NULL,
        limitations TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'UNVERIFIED_EVIDENCE',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS dien_chan_reviews (
        review_id TEXT PRIMARY KEY,
        target_type TEXT NOT NULL,
        target_id TEXT NOT NULL,
        reviewer TEXT NOT NULL,
        action TEXT NOT NULL,        -- 'APPROVED', 'REJECTED', 'FLAGGED'
        notes TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)


def seed_dien_chan_database(db: sqlite3.Connection) -> None:
    """Populate database with authoritative reference sources, points, conditions and protocols."""
    init_dien_chan_tables(db)

    # 1. Sources
    sources = [
        (
            "SRC_IMG_DC_01",
            "Bản đồ Huyệt Diện Chẩn (Tài liệu nguồn Image A)",
            "GS.TSKH Bùi Quốc Châu",
            "Tái bản tổng hợp",
            1980,
            "EDUCATIONAL_FAIR_USE",
            "3refs/dien_chan/source_images/dien_chan_face_atlas_front_side.png",
            "af3cc92bafa448393df3bf780c94ae2b08085d76219b7e7b70070960deb1018f",
            "Sơ đồ hệ thống đồ hình phản chiếu mặt và tọa độ tuyến dọc L-K-H-G-E-D-C-B-A-O / tuyến ngang 0-12."
        ),
        (
            "SRC_BQC_1980",
            "Diện Chẩn – Điều Khiển Liệu Pháp (Tài liệu gốc)",
            "GS.TSKH Bùi Quốc Châu",
            "Tái bản tổng hợp",
            1980,
            "EDUCATIONAL_FAIR_USE",
            "3refs/dien_chan/source_images/dien_chan_face_atlas_front_side.png",
            "af3cc92bafa448393df3bf780c94ae2b08085d76219b7e7b70070960deb1018f",
            "Sơ đồ hệ thống đồ hình phản chiếu mặt và tọa độ tuyến dọc L-K-H-G-E-D-C-B-A-O / tuyến ngang 0-12."
        ),
        (
            "SRC_IMG_DC_02",
            "Đồ hình trị liệu: Đau Đầu – Viêm Xoang (Tài liệu nguồn Image B)",
            "Diện Chẩn Thực Hành",
            "Đồ hình chuyên khoa",
            2010,
            "EDUCATIONAL_FAIR_USE",
            "3refs/dien_chan/source_images/dien_chan_headache_sinus_example.png",
            "e5c169e62fc4fff94ee5fba6992adeeb8a65728f7a9f402375185cdd4e502c74",
            "Phác đồ phối hợp huyệt Diện Chẩn đặc hiệu cho chứng đau đầu và viêm mũi xoang."
        ),
    ]

    for s in sources:
        db.execute("""
            INSERT OR REPLACE INTO dien_chan_sources 
            (source_id, title, author, edition, year, license_status, image_path, image_sha256, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, s)

    # 2. Points (from FacialRegistrationEngine)
    engine = FacialRegistrationEngine()
    for pt in engine.list_points():
        db.execute("""
            INSERT OR REPLACE INTO dien_chan_points
            (point_code, name_vi, name_en, name_zh, description_vi, description_en,
             grid_coordinate, anatomical_location_vi, anatomical_location_en,
             position_x, position_y, position_z, normal_x, normal_y, normal_z,
             laterality, anatomical_region, source_id, review_status, uncertainty_mm,
             projection_residual_mm, fma_anchor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pt.point_code, pt.name_vi, pt.name_en, pt.name_zh,
            pt.name_vi, pt.name_en, pt.grid_coordinate,
            pt.anatomical_location_vi, pt.anatomical_location_en,
            pt.position_xyz[0], pt.position_xyz[1], pt.position_xyz[2],
            pt.surface_normal[0], pt.surface_normal[1], pt.surface_normal[2],
            pt.laterality.value, pt.anatomical_region, pt.source_image_id,
            pt.review_status, pt.uncertainty_mm, pt.projection_residual_mm, pt.fma_anchor
        ))

    # 3. Conditions
    conditions = [
        (
            "COND_HEADACHE_SINUS",
            "Đau đầu – Viêm xoang",
            "Headache & Sinusitis Reflex Protocol",
            "dau dau viem xoang",
            json.dumps([
                "đau đầu", "viêm xoang", "nhức đầu", "nghẹt mũi", "xoang trán",
                "xoang hàm", "sổ mũi", "viêm mũi dị ứng", "đau nửa đầu", "headache", "sinusitis"
            ], ensure_ascii=False),
            "Chứng nhức đầu vùng trán, thái dương kèm nghẹt mũi, chảy nước mũi hoặc căng tức các hốc xoang mặt.",
            "cranial_facial",
            "CẢNH BÁO NGUY HIỂM: Đau đầu dữ dội khởi phát đột ngột (như sét đánh), sốt cao kèm cứng gáy, nôn vọt, mờ mắt, rối loạn ý thức, co giật hoặc yếu liệt nửa người là dấu hiệu xuất huyết não/viêm màng não, cần chuyển cấp cứu y tế ngay lập tức."
        ),
        (
            "COND_NECK_SHOULDER",
            "Đau mỏi cổ vai gáy",
            "Cervical Spine & Shoulder Tension",
            "dau moi co vai gay",
            json.dumps([
                "đau cổ gáy", "mỏi vai gáy", "căng cứng cổ", "cổ vai gáy", "thoái hóa cổ", "neck pain", "shoulder tension"
            ], ensure_ascii=False),
            "Co thắt cơ thang, đau mỏi vùng cột sống cổ và hạn chế tầm vận động xoay nghiêng cổ.",
            "musculoskeletal",
            "CẢNH BÁO: Tê bì lan xuống tay kèm teo cơ, mất phản xạ gân xương hoặc bí tiểu tiện gợi ý chèn ép tủy cổ, cần khám chuyên khoa ngoại thần kinh."
        ),
        (
            "COND_LUMBAR_SPINE",
            "Đau cột sống thắt lưng",
            "Lumbar Spine & Low Back Tension",
            "dau cot song that lung",
            json.dumps([
                "đau lưng", "đau thắt lưng", "mỏi lưng", "thoái hóa thắt lưng", "thoát vị đĩa đệm", "low back pain"
            ], ensure_ascii=False),
            "Đau mỏi vùng thắt lưng, co cứng khối cơ cạnh sống và hạn chế cúi ngửa.",
            "musculoskeletal",
            "CẢNH BÁO: Rối loạn cơ tròn (tiểu tiện không tự chủ), mất cảm giác vùng yên ngựa (hội chứng chùm đuôi ngựa) cần phẫu thuật cấp cứu."
        ),
        (
            "COND_INSOMNIA",
            "Mất ngủ – Căng thẳng thần kinh",
            "Insomnia & Nervous Tension",
            "mat ngu",
            json.dumps([
                "mất ngủ", "khó ngủ", "ngủ không sâu giấc", "trằn trọc", "căng thẳng", "stress", "insomnia", "mat ngu"
            ], ensure_ascii=False),
            "Khó đi vào giấc ngủ, hay giật mình thức giấc, căng thẳng thần kinh lo âu.",
            "neurological",
            "CẢNH BÁO: Mất ngủ kéo dài kèm sút cân nhanh, thay đổi tính cách đột ngột hoặc ảo giác cần khám chuyên khoa tâm thần kinh."
        ),
    ]

    for c in conditions:
        db.execute("""
            INSERT OR REPLACE INTO dien_chan_conditions
            (condition_id, name_vi, name_en, normalized_vi, synonyms_vi, description_vi, category, clinical_red_flags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, c)

    # 4. Protocols
    protocols = [
        (
            "PROTO_HEADACHE_SINUS_01",
            "COND_HEADACHE_SINUS",
            "SRC_IMG_DC_02",
            "Phác đồ Đau Đầu – Viêm Xoang (Tài liệu nguồn Image B)",
            "Dien Chan Headache & Sinusitis Master Protocol",
            "Phác đồ kết hợp thông khiếu xoang mặt, tiêu viêm và an thần định tâm.",
            "Giảm căng thẳng nội sọ, thông đường thở và giải phóng phù nề niêm mạc mũi xoang.",
            "TRADITIONAL_REFLEXOLOGY_REFERENCE",
            "Phản xạ liệu pháp Diện Chẩn mang tính hỗ trợ điều hòa chức năng, không thay thế thuốc kháng sinh hay can thiệp ngoại khoa khi có nhiễm trùng nặng.",
            "ACTIVE"
        ),
        (
            "PROTO_NECK_SHOULDER_01",
            "COND_NECK_SHOULDER",
            "SRC_BQC_1980",
            "Phác đồ Thư Giãn Cổ Gáy & Khớp Vai",
            "Dien Chan Cervical Relaxation Protocol",
            "Phản chiếu vùng cơ thang và cột sống cổ trên trán và cung mày.",
            "Giải phóng co thắt cơ cổ gáy và điều hòa thần kinh giao cảm.",
            "TRADITIONAL_REFLEXOLOGY_REFERENCE",
            "Chống chỉ định day ấn mạnh khi có chấn thương cột sống cổ chưa loại trừ gãy xương.",
            "ACTIVE"
        ),
        (
            "PROTO_LUMBAR_SPINE_01",
            "COND_LUMBAR_SPINE",
            "SRC_BQC_1980",
            "Phác đồ Điều Hòa Cột Sống Thắt Lưng",
            "Dien Chan Lumbar Spine Balance Protocol",
            "Phản chiếu cột sống thắt lưng trên sống mũi (đồ hình phản chiếu ngoại vi).",
            "Kích hoạt tuần hoàn cơ dựng sống và tăng trương lực gân cơ.",
            "TRADITIONAL_REFLEXOLOGY_REFERENCE",
            "Không áp dụng thay thế cấp cứu khi có chèn ép rễ cấp.",
            "ACTIVE"
        ),
        (
            "PROTO_INSOMNIA_01",
            "COND_INSOMNIA",
            "SRC_BQC_1980",
            "Phác đồ An Thần & Điều Hòa Giấc Ngủ",
            "Dien Chan Sedation & Sleep Regulation Protocol",
            "Phản chiếu vỏ não và trung tâm điều hòa giấc ngủ trên trán và rãnh mang tai.",
            "Hạ hưng phấn thần kinh giao cảm, giúp thư giãn tâm trí để dễ đi vào giấc ngủ.",
            "TRADITIONAL_REFLEXOLOGY_REFERENCE",
            "Không tự ý ngưng các thuốc điều trị an thần đang được bác sĩ chuyên khoa kê đơn.",
            "ACTIVE"
        ),
    ]

    for p in protocols:
        db.execute("""
            INSERT OR REPLACE INTO dien_chan_protocols
            (protocol_id, condition_id, source_id, title_vi, title_en, description_vi,
             therapeutic_intent, evidence_level, safety_disclaimer_vi, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, p)

    # 5. Protocol Points (Ordered sequences)
    # Headache Sinusitis Protocol from Image B:
    headache_points = [
        ("PROTO_HEADACHE_SINUS_01", "DC_103", 1, "day_an", "Day ấn nhẹ nhàng 30 giây để an thần, định tâm, hạ áp lực nội sọ.", "midline"),
        ("PROTO_HEADACHE_SINUS_01", "DC_106", 2, "day_an", "Day ấn 30 giây hỗ trợ điều hòa trung khu thần kinh.", "midline"),
        ("PROTO_HEADACHE_SINUS_01", "DC_107", 3, "day_an", "Day ấn hai bên trán giải tỏa ứ trệ hốc xoang trán.", "both"),
        ("PROTO_HEADACHE_SINUS_01", "DC_300", 4, "day_an", "Day ấn thẳng con ngươi lên trán giúp bổ thận thủy, tiêu viêm.", "both"),
        ("PROTO_HEADACHE_SINUS_01", "DC_73",  5, "day_an", "Day nhẹ bờ dưới ổ mắt giải phóng áp lực xoang hàm.", "both"),
        ("PROTO_HEADACHE_SINUS_01", "DC_189", 6, "day_an", "Day vuốt dọc sống mũi kích hoạt thông khiếu hô hấp.", "midline"),
        ("PROTO_HEADACHE_SINUS_01", "DC_61",  7, "day_an", "Day ấn hốc cánh mũi có tác dụng chống viêm và giảm đau mạnh.", "both"),
        ("PROTO_HEADACHE_SINUS_01", "DC_19",  8, "day_an", "Ấn nhân trung kích thích lưu thông đường thở (không dùng cho người tăng huyết áp kịch phát).", "midline"),
        ("PROTO_HEADACHE_SINUS_01", "DC_127", 9, "day_an", "Day ấn hõm cằm làm ấm vùng bụng dưới và tăng cường kháng viêm.", "midline"),
        ("PROTO_HEADACHE_SINUS_01", "DC_96", 10, "day_an", "Day nhẹ hai thái dương giải tỏa co thắt mạch máu thái dương.", "both"),
        ("PROTO_HEADACHE_SINUS_01", "DC_43", 11, "day_an", "Chấm day đỉnh chóp mũi làm ấm và thông mũi tức thì.", "midline"),
    ]

    for pt_item in headache_points:
        db.execute("""
            INSERT OR REPLACE INTO dien_chan_protocol_points
            (protocol_id, point_code, sequence_order, technique, duration_notes, laterality_rule)
            VALUES (?, ?, ?, ?, ?, ?)
        """, pt_item)

    # Neck Shoulder Protocol:
    neck_points = [
        ("PROTO_NECK_SHOULDER_01", "DC_26", 1, "day_an", "Ấn đường giải tỏa căng thẳng thần kinh.", "midline"),
        ("PROTO_NECK_SHOULDER_01", "DC_34", 2, "day_an", "Phản chiếu khớp vai và cơ thang.", "both"),
        ("PROTO_NECK_SHOULDER_01", "DC_61", 3, "day_an", "Kháng viêm và giảm co thắt cơ.", "both"),
        ("PROTO_NECK_SHOULDER_01", "DC_15", 4, "day_an", "Phản xạ cơ cổ sau tai.", "both"),
        ("PROTO_NECK_SHOULDER_01", "DC_16", 5, "day_an", "Khai thông tuần hoàn đầu cổ.", "both"),
    ]

    for pt_item in neck_points:
        db.execute("""
            INSERT OR REPLACE INTO dien_chan_protocol_points
            (protocol_id, point_code, sequence_order, technique, duration_notes, laterality_rule)
            VALUES (?, ?, ?, ?, ?, ?)
        """, pt_item)

    # Lumbar Spine Protocol:
    lumbar_points = [
        ("PROTO_LUMBAR_SPINE_01", "DC_1",   1, "day_an", "Sống mũi phản chiếu đoạn thắt lưng.", "midline"),
        ("PROTO_LUMBAR_SPINE_01", "DC_19",  2, "day_an", "Tăng trương lực cơ dựng sống thắt lưng.", "midline"),
        ("PROTO_LUMBAR_SPINE_01", "DC_26",  3, "day_an", "An thần và giãn cơ lưng.", "midline"),
        ("PROTO_LUMBAR_SPINE_01", "DC_127", 4, "day_an", "Làm ấm cột sống và hành khí hoạt huyết.", "midline"),
    ]

    for pt_item in lumbar_points:
        db.execute("""
            INSERT OR REPLACE INTO dien_chan_protocol_points
            (protocol_id, point_code, sequence_order, technique, duration_notes, laterality_rule)
            VALUES (?, ?, ?, ?, ?, ?)
        """, pt_item)

    # Insomnia Protocol:
    insomnia_points = [
        ("PROTO_INSOMNIA_01", "DC_103", 1, "day_an", "Day ấn nhẹ 1 phút làm dịu đại não và an thần.", "midline"),
        ("PROTO_INSOMNIA_01", "DC_106", 2, "day_an", "Day ấn 30 giây điều hòa trung khu thần kinh.", "midline"),
        ("PROTO_INSOMNIA_01", "DC_26",  3, "day_an", "Day ấn huyệt 26 (Ấn đường) giúp thư giãn tinh thần.", "midline"),
        ("PROTO_INSOMNIA_01", "DC_0",   4, "day_an", "Day ấn hai bên huyệt 0 trước nắp tai ổn định huyết áp và nhịp tim.", "both"),
    ]

    for pt_item in insomnia_points:
        db.execute("""
            INSERT OR REPLACE INTO dien_chan_protocol_points
            (protocol_id, point_code, sequence_order, technique, duration_notes, laterality_rule)
            VALUES (?, ?, ?, ?, ?, ?)
        """, pt_item)

    db.commit()


# Database Access Functions
def list_dien_chan_points(db: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Return all Dien Chan points with 3D positions."""
    cursor = db.execute("""
        SELECT point_code, name_vi, name_en, name_zh, description_vi, description_en,
               grid_coordinate, anatomical_location_vi, anatomical_location_en,
               position_x, position_y, position_z, normal_x, normal_y, normal_z,
               laterality, anatomical_region, source_id, review_status, uncertainty_mm,
               projection_residual_mm, fma_anchor
        FROM dien_chan_points
        ORDER BY point_code
    """)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "point_code": r[0],
            "name_vi": r[1],
            "name_en": r[2],
            "name_zh": r[3],
            "description_vi": r[4],
            "description_en": r[5],
            "grid_coordinate": r[6],
            "anatomical_location_vi": r[7],
            "anatomical_location_en": r[8],
            "position": [r[9], r[10], r[11]],
            "resolved_world_position": [r[9], r[10], r[11]],
            "surface_normal": [r[12], r[13], r[14]],
            "laterality": r[15],
            "anatomical_region": r[16],
            "source_id": r[17],
            "review_status": r[18],
            "uncertainty_mm": r[19],
            "projection_residual_mm": r[20],
            "fma_anchor": r[21],
            "system": "lib_dien_chan",
            "domain": "VIETNAMESE_DIEN_CHAN",
        })
    return results


def get_dien_chan_point(db: sqlite3.Connection, point_code: str) -> Optional[Dict[str, Any]]:
    """Retrieve single Dien Chan point by point code."""
    cursor = db.execute("""
        SELECT point_code, name_vi, name_en, name_zh, description_vi, description_en,
               grid_coordinate, anatomical_location_vi, anatomical_location_en,
               position_x, position_y, position_z, normal_x, normal_y, normal_z,
               laterality, anatomical_region, source_id, review_status, uncertainty_mm,
               projection_residual_mm, fma_anchor
        FROM dien_chan_points
        WHERE point_code = ?
    """, (point_code,))
    r = cursor.fetchone()
    if not r:
        return None
    return {
        "point_code": r[0],
        "name_vi": r[1],
        "name_en": r[2],
        "name_zh": r[3],
        "description_vi": r[4],
        "description_en": r[5],
        "grid_coordinate": r[6],
        "anatomical_location_vi": r[7],
        "anatomical_location_en": r[8],
        "position": [r[9], r[10], r[11]],
        "resolved_world_position": [r[9], r[10], r[11]],
        "surface_normal": [r[12], r[13], r[14]],
        "laterality": r[15],
        "anatomical_region": r[16],
        "source_id": r[17],
        "review_status": r[18],
        "uncertainty_mm": r[19],
        "projection_residual_mm": r[20],
        "fma_anchor": r[21],
        "system": "lib_dien_chan",
        "domain": "VIETNAMESE_DIEN_CHAN",
    }


def get_protocol_with_points(db: sqlite3.Connection, protocol_id: str) -> Optional[Dict[str, Any]]:
    """Fetch complete protocol details and ordered point list."""
    cursor = db.execute("""
        SELECT p.protocol_id, p.condition_id, p.source_id, p.title_vi, p.title_en,
               p.description_vi, p.therapeutic_intent, p.evidence_level,
               p.safety_disclaimer_vi, p.status, s.title, s.author, s.year,
               c.name_vi, c.clinical_red_flags
        FROM dien_chan_protocols p
        JOIN dien_chan_sources s ON p.source_id = s.source_id
        JOIN dien_chan_conditions c ON p.condition_id = c.condition_id
        WHERE p.protocol_id = ?
    """, (protocol_id,))
    row = cursor.fetchone()
    if not row:
        return None

    proto_dict = {
        "protocol_id": row[0],
        "condition_id": row[1],
        "source_id": row[2],
        "title_vi": row[3],
        "title_en": row[4],
        "description_vi": row[5],
        "therapeutic_intent": row[6],
        "evidence_level": row[7],
        "safety_disclaimer_vi": row[8],
        "status": row[9],
        "source": {
            "title": row[10],
            "author": row[11],
            "year": row[12],
        },
        "condition_name_vi": row[13],
        "clinical_red_flags": row[14],
        "points": [],
    }

    # Fetch ordered points
    pt_cursor = db.execute("""
        SELECT pp.point_code, pp.sequence_order, pp.technique, pp.duration_notes, pp.laterality_rule,
               pt.name_vi, pt.grid_coordinate, pt.position_x, pt.position_y, pt.position_z,
               pt.normal_x, pt.normal_y, pt.normal_z, pt.review_status, pt.uncertainty_mm,
               pt.projection_residual_mm, pt.fma_anchor
        FROM dien_chan_protocol_points pp
        JOIN dien_chan_points pt ON pp.point_code = pt.point_code
        WHERE pp.protocol_id = ?
        ORDER BY pp.sequence_order ASC
    """, (protocol_id,))

    for pr in pt_cursor.fetchall():
        proto_dict["points"].append({
            "point_code": pr[0],
            "sequence_order": pr[1],
            "technique": pr[2],
            "duration_notes": pr[3],
            "laterality_rule": pr[4],
            "name_vi": pr[5],
            "grid_coordinate": pr[6],
            "position": [pr[7], pr[8], pr[9]],
            "surface_normal": [pr[10], pr[11], pr[12]],
            "review_status": pr[13],
            "uncertainty_mm": pr[14],
            "projection_residual_mm": pr[15],
            "fma_anchor": pr[16],
        })

    return proto_dict
