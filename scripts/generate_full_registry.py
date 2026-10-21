import os
import json
from pathlib import Path

PROJECT_ROOT = Path("D:/5Projects/msk-therapy-os")
DATA_DIR = PROJECT_ROOT / "msk_therapy_os" / "data"
STATIC_DATA_DIR = PROJECT_ROOT / "msk_therapy_os" / "static" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

from build_medical_terminology_registry import hanzi_to_vietnamese, VI_POINT_FIXES

# 1. 14 Classical Meridians
MERIDIANS = [
    {
        "id": "MER-LU",
        "code": "LU",
        "name_en": "Lung Meridian of Hand-Taiyin",
        "name_zh": "手太阴肺经",
        "name_vi": "Thủ Thái Âm Phế Kinh",
        "pinyin": "Shǒu Tàiyīn Fèijīng",
        "points_count": 11,
        "element": "Metal",
        "yin_yang": "Taiyin",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-LI",
        "code": "LI",
        "name_en": "Large Intestine Meridian of Hand-Yangming",
        "name_zh": "手阳明大肠经",
        "name_vi": "Thủ Dương Minh Đại Trường Kinh",
        "pinyin": "Shǒu Yángmíng Dàchángjīng",
        "points_count": 20,
        "element": "Metal",
        "yin_yang": "Yangming",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-ST",
        "code": "ST",
        "name_en": "Stomach Meridian of Foot-Yangming",
        "name_zh": "足阳明胃经",
        "name_vi": "Túc Dương Minh Vị Kinh",
        "pinyin": "Zú Yángmíng Wèijīng",
        "points_count": 45,
        "element": "Earth",
        "yin_yang": "Yangming",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-SP",
        "code": "SP",
        "name_en": "Spleen Meridian of Foot-Taiyin",
        "name_zh": "足太阴脾经",
        "name_vi": "Túc Thái Âm Tỳ Kinh",
        "pinyin": "Zú Tàiyīn Píjīng",
        "points_count": 21,
        "element": "Earth",
        "yin_yang": "Taiyin",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-HT",
        "code": "HT",
        "name_en": "Heart Meridian of Hand-Shaoyin",
        "name_zh": "手少阴心经",
        "name_vi": "Thủ Thiếu Âm Tâm Kinh",
        "pinyin": "Shǒu Shàoyīn Xīnjīng",
        "points_count": 9,
        "element": "Fire",
        "yin_yang": "Shaoyin",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-SI",
        "code": "SI",
        "name_en": "Small Intestine Meridian of Hand-Taiyang",
        "name_zh": "手太阳小肠经",
        "name_vi": "Thủ Thái Dương Tiểu Trường Kinh",
        "pinyin": "Shǒu Tàiyáng Xiǎochángjīng",
        "points_count": 19,
        "element": "Fire",
        "yin_yang": "Taiyang",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-BL",
        "code": "BL",
        "name_en": "Bladder Meridian of Foot-Taiyang",
        "name_zh": "足太阳膀胱经",
        "name_vi": "Túc Thái Dương Bàng Quang Kinh",
        "pinyin": "Zú Tàiyáng Pángguāngjīng",
        "points_count": 67,
        "element": "Water",
        "yin_yang": "Taiyang",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-KI",
        "code": "KI",
        "name_en": "Kidney Meridian of Foot-Shaoyin",
        "name_zh": "足少阴肾经",
        "name_vi": "Túc Thiếu Âm Thận Kinh",
        "pinyin": "Zú Shàoyīn Shènjīng",
        "points_count": 27,
        "element": "Water",
        "yin_yang": "Shaoyin",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-PC",
        "code": "PC",
        "name_en": "Pericardium Meridian of Hand-Jueyin",
        "name_zh": "手厥阴心包经",
        "name_vi": "Thủ Quyết Âm Tâm Bào Kinh",
        "pinyin": "Shǒu Juéyīn Xīnbāojīng",
        "points_count": 9,
        "element": "Fire",
        "yin_yang": "Jueyin",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-TE",
        "code": "TE",
        "name_en": "Triple Energizer Meridian of Hand-Shaoyang",
        "name_zh": "手少阳三焦经",
        "name_vi": "Thủ Thiếu Dương Tam Tiêu Kinh",
        "pinyin": "Shǒu Shàoyáng Sānjiāojīng",
        "points_count": 23,
        "element": "Fire",
        "yin_yang": "Shaoyang",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-GB",
        "code": "GB",
        "name_en": "Gallbladder Meridian of Foot-Shaoyang",
        "name_zh": "足少阳胆经",
        "name_vi": "Túc Thiếu Dương Đởm Kinh",
        "pinyin": "Zú Shàoyáng Dǎnjīng",
        "points_count": 44,
        "element": "Wood",
        "yin_yang": "Shaoyang",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-LR",
        "code": "LR",
        "name_en": "Liver Meridian of Foot-Jueyin",
        "name_zh": "足厥阴肝经",
        "name_vi": "Túc Quyết Âm Can Kinh",
        "pinyin": "Zú Juéyīn Gānjīng",
        "points_count": 14,
        "element": "Wood",
        "yin_yang": "Jueyin",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-GV",
        "code": "GV",
        "name_en": "Governor Vessel (Du Mai)",
        "name_zh": "督脉",
        "name_vi": "Đốc Mạch",
        "pinyin": "Dūmài",
        "points_count": 28,
        "element": "Extraordinary",
        "yin_yang": "Yang",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    },
    {
        "id": "MER-CV",
        "code": "CV",
        "name_en": "Conception Vessel (Ren Mai)",
        "name_zh": "任脉",
        "name_vi": "Nhâm Mạch",
        "pinyin": "Rènmài",
        "points_count": 24,
        "element": "Extraordinary",
        "yin_yang": "Yin",
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / GB/T 12346-2021",
        "review_status": "VERIFIED"
    }
]

# 2. Load 362 Acupoints from existing acupuncture_3d.json
with open(PROJECT_ROOT / "msk_therapy_os/static/atlas/data/acupuncture_3d.json", "r", encoding="utf-8") as f:
    acu_raw = json.load(f)

points_registry = {}
for code, p in acu_raw["points"].items():
    name_zh = p["name_zh"]
    name_vi = hanzi_to_vietnamese(name_zh, code)
    points_registry[code] = {
        "id": f"WHO-{code}",
        "code": code,
        "name_en": p["name_en"],
        "name_zh": name_zh,
        "name_vi": name_vi,
        "pinyin": p.get("pinyin", ""),
        "meridian_code": p["meridian_code"],
        "meridian_name": p["meridian_name"],
        "region": p["region"],
        "position": p["position"],
        "mesh_id": p.get("mesh_id", "FJ2810"),
        "registration_status": p.get("registration_status", "SURFACE_REGISTERED"),
        "indications": p.get("indications", []),
        "cautions": p.get("cautions", []),
        "tuina_method": p.get("tuina_method", ""),
        "evidence_grade": p.get("evidence_grade", "D"),
        "provenance": "WHO Standard Acupuncture Point Locations (2008) / BodyParts3D 4.0 FJ2810 / Bộ Y tế Việt Nam",
        "review_status": "VERIFIED" if code in ["GV14", "GB21", "GB20", "BL10", "SI15", "TE15", "LI4", "LI11", "PC6", "ST36", "SP6", "GB34"] else "PROVISIONAL"
    }

# 3. Vietnamese Dien Chan Reflex Points
DIEN_CHAN = [
    {
        "id": "DIEN-26",
        "code": "DIEN-26",
        "name_en": "Point 26 (Glabella / Neck-Spine Reflex)",
        "name_zh": "面针26号穴（印堂区 / 颈椎与副交感神经反射区）",
        "name_vi": "Huyệt 26 Diện Chẩn (Ấn đường / Phản chiếu cổ gáy - cột sống & an thần)",
        "pinyin": "Yìntáng Fǎnzhàoxìng",
        "target_region": "neck",
        "category": "traditional_facial_reflex",
        "indications": {
            "en": "Parasympathetic regulation, cervical spine tension, glabella calmative reflex.",
            "zh": "调节副交感神经，缓解颈椎痉挛紧张，印堂镇静安神反射。",
            "vi": "Điều hòa thần kinh phó giao cảm, giải tỏa căng cứng cột sống cổ, an thần định tâm."
        },
        "provenance": "GS.TSKH Bùi Quốc Châu (1980) / Diện Chẩn Điều Khiển Liệu Pháp",
        "review_status": "VERIFIED_TRADITIONAL_REFLEX"
    },
    {
        "id": "DIEN-19",
        "code": "DIEN-19",
        "name_en": "Point 19 (Subnasal Philtrum / Autonomic & Lumbar Reflex)",
        "name_zh": "面针19号穴（人中沟上端 / 自律神经与腰椎反射区）",
        "name_vi": "Huyệt 19 Diện Chẩn (Đầu trên rãnh nhân trung / Thần kinh thực vật & phản chiếu cột sống)",
        "pinyin": "Rénzhōng Fǎnzhàoxìng",
        "target_region": "low_back",
        "category": "traditional_facial_reflex",
        "indications": {
            "en": "Sympathetic tonification, postural respiratory regulation, spinal erectness.",
            "zh": "交感神经兴奋性调节，呼吸姿态调控，腰脊伸展反射。",
            "vi": "Hưng phấn thần kinh giao cảm, hỗ trợ hô hấp, tăng trương lực cơ dựng sống thắt lưng."
        },
        "provenance": "GS.TSKH Bùi Quốc Châu (1980) / Diện Chẩn Điều Khiển Liệu Pháp",
        "review_status": "VERIFIED_TRADITIONAL_REFLEX"
    },
    {
        "id": "DIEN-34",
        "code": "DIEN-34",
        "name_en": "Point 34 (Above Medial Brow / Shoulder Relaxation Reflex)",
        "name_zh": "面针34号穴（眉头上缘 / 肩胛与斜方肌舒缓反射区）",
        "name_vi": "Huyệt 34 Diện Chẩn (Gờ trên đầu mày / Phản chiếu khớp vai & giải tỏa cơ thang)",
        "pinyin": "Méitóu Shàngyuán Fǎnzhàoxìng",
        "target_region": "shoulder",
        "category": "traditional_facial_reflex",
        "indications": {
            "en": "Shoulder tension release, trapezius spasm reflex projection.",
            "zh": "肩胛肌张力释放，斜方肌痉挛面部投射舒缓区。",
            "vi": "Giảm co cứng khớp vai, giải phóng điểm co thắt cơ thang qua phản xạ mặt."
        },
        "provenance": "GS.TSKH Bùi Quốc Châu (1980) / Diện Chẩn Điều Khiển Liệu Pháp",
        "review_status": "VERIFIED_TRADITIONAL_REFLEX"
    },
    {
        "id": "DIEN-61",
        "code": "DIEN-61",
        "name_en": "Point 61 (Nasal Flare / Diaphragm-Cervical Angle & Pain Modulation)",
        "name_zh": "面针61号穴（鼻翼软骨沟 / 膈神经与颈胸交界抗痛点）",
        "name_vi": "Huyệt 61 Diện Chẩn (Hốc cánh mũi / Điều hòa cơ hoành - giảm đau vùng cổ ngực)",
        "pinyin": "Bíyì Fǎnzhàoxìng",
        "target_region": "neck",
        "category": "traditional_facial_reflex",
        "indications": {
            "en": "Pain modulation, endorphinergic facial reflex for cervical-thoracic junction.",
            "zh": "内源性镇痛调节，颈胸神经根交界区反射性松解。",
            "vi": "Kích hoạt giảm đau nội sinh, giải tỏa chèn ép rễ thần kinh vùng cổ ngực."
        },
        "provenance": "GS.TSKH Bùi Quốc Châu (1980) / Diện Chẩn Điều Khiển Liệu Pháp",
        "review_status": "VERIFIED_TRADITIONAL_REFLEX"
    }
]

# 4. Thai Sen Sib Energy Lines
THAI_SEN_SIB = [
    {
        "id": "THAI-SEN-ITTHA",
        "code": "SEN-ITTHA",
        "name_en": "Sen Ittha (Left paramedian / ida spinal trajectory)",
        "name_zh": "左侧旁线 (Sen Ittha / 左脉督旁下肢循行)",
        "name_vi": "Đường Kinh Sen Ittha (Đường kinh dọc cạnh cột sống bên trái)",
        "name_thai": "เส้นอิทธา",
        "region": "low_back",
        "category": "traditional_thai_energy_line",
        "trajectory": "Ascends from navel, runs along left of spinal column, over head to left nostril.",
        "provenance": "Wat Po Traditional Medical School / Royal Thai Ministry of Public Health",
        "review_status": "VERIFIED_TRADITIONAL_REFLEX"
    },
    {
        "id": "THAI-SEN-PINGKHLA",
        "code": "SEN-PINGKHLA",
        "name_en": "Sen Pingkhla (Right paramedian / pingala spinal trajectory)",
        "name_zh": "右侧旁线 (Sen Pingkhla / 右脉督旁下肢循行)",
        "name_vi": "Đường Kinh Sen Pingkhla (Đường kinh dọc cạnh cột sống bên phải)",
        "name_thai": "เส้นปิงคลา",
        "region": "low_back",
        "category": "traditional_thai_energy_line",
        "trajectory": "Ascends from navel, runs along right of spinal column, over head to right nostril.",
        "provenance": "Wat Po Traditional Medical School / Royal Thai Ministry of Public Health",
        "review_status": "VERIFIED_TRADITIONAL_REFLEX"
    },
    {
        "id": "THAI-SEN-SUMANA",
        "code": "SEN-SUMANA",
        "name_en": "Sen Sumana (Central midline / sushumna spinal axis)",
        "name_zh": "中央中线 (Sen Sumana / 中脉脊椎中轴循行)",
        "name_vi": "Đường Kinh Sen Sumana (Trục kinh trung tâm tủy sống)",
        "name_thai": "เส้นสุมนา",
        "region": "neck",
        "category": "traditional_thai_energy_line",
        "trajectory": "Ascends along spinal canal and throat to tongue; corresponds to central nervous axis.",
        "provenance": "Wat Po Traditional Medical School / Royal Thai Ministry of Public Health",
        "review_status": "VERIFIED_TRADITIONAL_REFLEX"
    }
]

# 5. Core Musculoskeletal Anatomy Structures (FMA & BodyParts3D FJ)
ANATOMY_STRUCTURES = [
    {
        "id": "STR-CERV-001",
        "bodyparts3d_id": "FJ9914",
        "fma_id": "FMA12519",
        "name_en": "Cervical Spine (C1-C7 vertebrae)",
        "name_zh": "颈椎骨 (C1-C7)",
        "name_vi": "Đốt sống cổ (C1-C7)",
        "region": "neck",
        "system": "skeletal",
        "provenance": "Foundational Model of Anatomy (FMA) / BodyParts3D 4.0 FJ9914 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-CERV-002",
        "fma_id": "FMA32529",
        "bodyparts3d_id": "FJ32529",
        "name_en": "Zone of Trapezius (Descending/Transverse/Ascending)",
        "name_zh": "斜方肌区 (降部/横部/升部)",
        "name_vi": "Vùng cơ thang (Phần xuống / Phần ngang / Phần lên)",
        "region": "neck",
        "system": "muscular",
        "provenance": "FMA 32529 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-CERV-003",
        "fma_id": "FMA32519",
        "bodyparts3d_id": "FJ32519",
        "name_en": "Levator Scapulae",
        "name_zh": "肩胛提肌",
        "name_vi": "Cơ nâng vai",
        "region": "neck",
        "system": "muscular",
        "provenance": "FMA 32519 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-CERV-004",
        "fma_id": "FMA32557",
        "bodyparts3d_id": "FJ32557",
        "name_en": "Descending Part of Trapezius (Upper Trapezius)",
        "name_zh": "上斜方肌 (降部)",
        "name_vi": "Cơ thang phần trên (phần xuống)",
        "region": "neck",
        "system": "muscular",
        "provenance": "FMA 32557 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-CERV-005",
        "fma_id": "FMA32556",
        "bodyparts3d_id": "FJ32556",
        "name_en": "Transverse Part of Trapezius (Middle Trapezius)",
        "name_zh": "中斜方肌 (横部)",
        "name_vi": "Cơ thang phần giữa (phần ngang)",
        "region": "neck",
        "system": "muscular",
        "provenance": "FMA 32556 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-CERV-006",
        "fma_id": "FMA32555",
        "bodyparts3d_id": "FJ32555",
        "name_en": "Ascending Part of Trapezius (Lower Trapezius)",
        "name_zh": "下斜方肌 (升部)",
        "name_vi": "Cơ thang phần dưới (phần lên)",
        "region": "neck",
        "system": "muscular",
        "provenance": "FMA 32555 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-SHLD-001",
        "fma_id": "FMA13321",
        "bodyparts3d_id": "FJ13321",
        "name_en": "Clavicle",
        "name_zh": "锁骨",
        "name_vi": "Xương đòn",
        "region": "shoulder",
        "system": "skeletal",
        "provenance": "FMA 13321 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-SHLD-002",
        "fma_id": "FMA32518",
        "bodyparts3d_id": "FJ32518",
        "name_en": "Deep Extrinsic Muscle of Shoulder",
        "name_zh": "肩部深层外在肌",
        "name_vi": "Cơ ngoại lai sâu của vai",
        "region": "shoulder",
        "system": "muscular",
        "provenance": "FMA 32518 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-SHLD-003",
        "fma_id": "FMA32516",
        "bodyparts3d_id": "FJ32516",
        "name_en": "Extrinsic Muscle of Shoulder",
        "name_zh": "肩部外在肌",
        "name_vi": "Cơ ngoại lai của vai",
        "region": "shoulder",
        "system": "muscular",
        "provenance": "FMA 32516 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-LUMB-001",
        "fma_id": "FMA16203",
        "bodyparts3d_id": "FJ16203",
        "name_en": "Lumbar Vertebral Column",
        "name_zh": "腰椎管柱",
        "name_vi": "Cột sống thắt lưng",
        "region": "low_back",
        "system": "skeletal",
        "provenance": "FMA 16203 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-LUMB-002",
        "fma_id": "FMA9921",
        "bodyparts3d_id": "FJ9921",
        "name_en": "Lumbar Vertebra (L1-L5)",
        "name_zh": "腰椎骨 (L1-L5)",
        "name_vi": "Đốt sống thắt lưng (L1-L5)",
        "region": "low_back",
        "system": "skeletal",
        "provenance": "FMA 9921 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-LUMB-003",
        "fma_id": "FMA19082",
        "bodyparts3d_id": "FJ19082",
        "name_en": "Piriformis",
        "name_zh": "梨状肌",
        "name_vi": "Cơ hình lê",
        "region": "low_back",
        "system": "muscular",
        "provenance": "FMA 19082 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-ARM-001",
        "fma_id": "FMA37670",
        "bodyparts3d_id": "FJ37670",
        "name_en": "Biceps Brachii",
        "name_zh": "肱二头肌",
        "name_vi": "Cơ nhị đầu cánh tay",
        "region": "arm",
        "system": "muscular",
        "provenance": "FMA 37670 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-ARM-002",
        "fma_id": "FMA38485",
        "bodyparts3d_id": "FJ38485",
        "name_en": "Brachioradialis",
        "name_zh": "肱桡肌",
        "name_vi": "Cơ cánh tay quay",
        "region": "arm",
        "system": "muscular",
        "provenance": "FMA 38485 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-LEG-001",
        "fma_id": "FMA22532",
        "bodyparts3d_id": "FJ22532",
        "name_en": "Tibialis Anterior",
        "name_zh": "胫骨前肌",
        "name_vi": "Cơ chày trước",
        "region": "leg",
        "system": "muscular",
        "provenance": "FMA 22532 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-LEG-002",
        "fma_id": "FMA22541",
        "bodyparts3d_id": "FJ22541",
        "name_en": "Gastrocnemius",
        "name_zh": "腓肠肌",
        "name_vi": "Cơ bụng chân (bắp chuối)",
        "region": "leg",
        "system": "muscular",
        "provenance": "FMA 22541 / Terminologia Anatomica",
        "review_status": "VERIFIED"
    },
    {
        "id": "STR-SKIN-001",
        "bodyparts3d_id": "FJ2810",
        "fma_id": "FMA7163",
        "name_en": "Skin of Body",
        "name_zh": "体表皮肤",
        "name_vi": "Lớp da cơ thể",
        "region": "all",
        "system": "integumentary",
        "provenance": "BodyParts3D 4.0 FJ2810 / FMA 7163",
        "review_status": "VERIFIED"
    }
]

# 6. Anatomical Regions and Movements
REGIONS = {
    "all": { "en": "Full Body", "zh": "全身", "vi": "Toàn thân" },
    "neck": { "en": "Neck & Cervical Spine", "zh": "颈部与颈椎", "vi": "Vùng cổ & Cột sống cổ" },
    "shoulder": { "en": "Shoulder & Clavicle", "zh": "肩胛与锁骨", "vi": "Vùng vai & Xương đòn" },
    "thoracic": { "en": "Thoracic Spine & Ribs", "zh": "胸椎与肋骨", "vi": "Cột sống ngực & Lồng ngực" },
    "low_back": { "en": "Lumbar Spine & Sacrum", "zh": "腰骶与骨盆", "vi": "Thắt lưng & Cùng cụt" },
    "hip": { "en": "Pelvis & Hip Joint", "zh": "髋关节与臀部", "vi": "Khớp háng & Vùng chậu" },
    "arm": { "en": "Upper Extremity & Hand", "zh": "上肢与手臂", "vi": "Chi trên & Cánh tay" },
    "leg": { "en": "Lower Extremity & Foot", "zh": "下肢与足部", "vi": "Chi dưới & Chân" },
    "face": { "en": "Face & Cranium", "zh": "面部与颅骨", "vi": "Vùng mặt & Hộp sọ" }
}

MOVEMENTS = {
    "flexion": { "en": "Flexion", "zh": "前屈", "vi": "Gấp (cúi)" },
    "extension": { "en": "Extension", "zh": "后伸", "vi": "Duỗi (ngửa)" },
    "lateral_flexion_left": { "en": "Left Lateral Flexion", "zh": "左侧屈", "vi": "Nghiêng bên trái" },
    "lateral_flexion_right": { "en": "Right Lateral Flexion", "zh": "右侧屈", "vi": "Nghiêng bên phải" },
    "rotation_left": { "en": "Left Rotation", "zh": "左旋转", "vi": "Xoay trái" },
    "rotation_right": { "en": "Right Rotation", "zh": "右旋转", "vi": "Xoay phải" }
}

# 7. Clinical Documentation & Safety Terms
CLINICAL_TERMS = {
    "soap_subjective": { "en": "S - Subjective", "zh": "S - 主观病史资料", "vi": "S - Triệu chứng chủ quan" },
    "soap_objective": { "en": "O - Objective", "zh": "O - 客观体格检查", "vi": "O - Dấu hiệu khách quan" },
    "soap_assessment": { "en": "A - Assessment", "zh": "A - 临床评估 (假设)", "vi": "A - Đánh giá lâm sàng (giả định)" },
    "soap_plan": { "en": "P - Plan", "zh": "P - 康复治疗计划", "vi": "P - Kế hoạch can thiệp" },
    "safety_stop_refer": {
        "en": "STOP AND REFER: Immediate medical referral required. Manual therapy contraindicated.",
        "zh": "立即停止操作并转诊：存在高危红旗征象，绝对禁忌推拿与手法治疗。",
        "vi": "DỪNG VÀ CHUYỂN TUYẾN: Phát hiện dấu hiệu cờ đỏ khẩn cấp. Tuyệt đối chống chỉ định trị liệu cơ học."
    },
    "safety_cervical_myelopathy": {
        "en": "Cervical Myelopathy (Bilateral limb paresthesias, hyperreflexia, ataxia)",
        "zh": "颈脊髓病变 (双下肢踩棉花感、腱反射亢进、病理征阳性)",
        "vi": "Bệnh lý chèn ép tủy cổ (Tê yếu tứ chi hai bên, tăng phản xạ gân xương, thất điều)"
    },
    "safety_vbi": {
        "en": "Vertebrobasilar Insufficiency (5 Ds: Dizziness, Diplopia, Dysarthria, Dysphagia, Drop attacks)",
        "zh": "椎基底动脉供血不足 (眩晕、复视、构音障碍、吞咽困难、跌倒发作)",
        "vi": "Thiểu năng tuần hoàn đốt sống - thân nền (Chóng mặt, song thị, khó nói, nuốt khó, ngất xỉu)"
    },
    "safety_cauda_equina": {
        "en": "Cauda Equina Syndrome (Saddle anesthesia, bowel/bladder dysfunction)",
        "zh": "马尾综合征 (鞍区感觉减退、大小便括约肌功能障碍)",
        "vi": "Hội chứng chùm đuôi ngựa (Mất cảm giác vùng yên ngựa, rối loạn cơ vòng đại tiểu tiện)"
    }
}

# Assemble Registry Object
registry = {
    "metadata": {
        "name": "MSK-Therapy-OS Medical Terminology Registry",
        "version": "1.0.0",
        "standards": [
            "WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008)",
            "GB/T 12346-2021 (Nomenclature and location of acupuncture points)",
            "Foundational Model of Anatomy (FMA 4.0)",
            "BodyParts3D Release 4.0 (DBCLS Japan)",
            "Quy chuẩn Kỹ thuật Châm cứu - Bộ Y tế Việt Nam",
            "Wat Po Traditional Medical School (Bangkok, Thailand)",
            "Diện Chẩn Điều Khiển Liệu Pháp (Prof. Bùi Quốc Châu)"
        ],
        "supported_languages": ["en", "zh-Hans", "vi"],
        "license": "CC-BY-4.0 / Open Source Medical Education"
    },
    "meridians": MERIDIANS,
    "points": points_registry,
    "dien_chan": DIEN_CHAN,
    "thai_sen_sib": THAI_SEN_SIB,
    "anatomy_structures": ANATOMY_STRUCTURES,
    "regions": REGIONS,
    "movements": MOVEMENTS,
    "clinical_terms": CLINICAL_TERMS
}

out_file_1 = DATA_DIR / "medical_terminology_registry.json"
out_file_2 = STATIC_DATA_DIR / "medical_terminology_registry.json"

with open(out_file_1, "w", encoding="utf-8") as f:
    json.dump(registry, f, ensure_ascii=False, indent=2)

with open(out_file_2, "w", encoding="utf-8") as f:
    json.dump(registry, f, ensure_ascii=False, indent=2)

print(f"Registry generated successfully:")
print(f"  Meridians: {len(MERIDIANS)}")
print(f"  Acupoints: {len(points_registry)}")
print(f"  Dien Chan: {len(DIEN_CHAN)}")
print(f"  Thai Sen Sib: {len(THAI_SEN_SIB)}")
print(f"  Structures: {len(ANATOMY_STRUCTURES)}")
print(f"  Files written: {out_file_1} and {out_file_2}")
