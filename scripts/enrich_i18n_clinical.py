import json
from pathlib import Path

I18N_DIR = Path("D:/5Projects/msk-therapy-os/msk_therapy_os/static/i18n")

SAFETY_FLAGS = {
  "en": {
    "none": "None (Safe / Normal Presentation)",
    "progressive_weakness": "Progressive Muscular Weakness",
    "bowel_bladder_change": "Bowel / Bladder Sphincter Incontinence",
    "saddle_numbness": "Saddle Area Anesthesia / Numbness",
    "fever_with_spinal_pain": "Fever >38.5°C with Spinal Pain",
    "major_trauma": "Major Trauma / Violent Impact",
    "unexplained_weight_loss_history_cancer": "Unexplained Weight Loss & History of Cancer",
    "severe_unremitting_night_pain": "Severe Unremitting Night Pain",
    "acute_cervical_myelopathy": "Acute Cervical Myelopathy Signs",
    "vascular_stroke_signs": "Vascular / Stroke Signs (5 Ds)",
    "dvt_thrombosis_signs": "Deep Vein Thrombosis (DVT) Signs",
    "suspected_fracture": "Suspected Spinal or Bone Fracture"
  },
  "zh": {
    "none": "无红旗征 (安全 / 正常体征)",
    "progressive_weakness": "进行性肌无力 (神经根损伤)",
    "bowel_bladder_change": "大小便括约肌失禁",
    "saddle_numbness": "鞍区感觉丧失 / 麻木",
    "fever_with_spinal_pain": "发热 >38.5°C 伴脊柱剧痛",
    "major_trauma": "严重创伤 / 暴力撞击史",
    "unexplained_weight_loss_history_cancer": "不明原因消瘦伴恶性肿瘤史",
    "severe_unremitting_night_pain": "夜间剧痛无法缓解",
    "acute_cervical_myelopathy": "急性颈脊髓压迫症候",
    "vascular_stroke_signs": "血管源性中风征象 (5D征)",
    "dvt_thrombosis_signs": "下肢深静脉血栓征象",
    "suspected_fracture": "疑似骨折"
  },
  "vi": {
    "none": "Không có (Bình thường / An toàn)",
    "progressive_weakness": "Yếu cơ tiến triển (Tổn thương rễ thần kinh)",
    "bowel_bladder_change": "Rối loạn cơ vòng đại tiểu tiện",
    "saddle_numbness": "Tê bì mất cảm giác vùng yên ngựa",
    "fever_with_spinal_pain": "Sốt >38.5°C kèm đau cột sống dữ dội",
    "major_trauma": "Chấn thương mạnh / Va chạm bạo lực",
    "unexplained_weight_loss_history_cancer": "Sụt cân không rõ nguyên nhân & Tiền sử ung thư",
    "severe_unremitting_night_pain": "Đau buốt dữ dội về đêm không thuyên giảm",
    "acute_cervical_myelopathy": "Dấu hiệu chèn ép tủy cổ cấp tính",
    "vascular_stroke_signs": "Dấu hiệu mạch máu não / Đột quỵ (Hội chứng 5D)",
    "dvt_thrombosis_signs": "Dấu hiệu huyết khối tĩnh mạch sâu (DVT)",
    "suspected_fracture": "Nghi ngờ gãy xương hoặc vỡ thân đốt sống"
  }
}

MODALITIES = {
  "en": {
    "manual_tuina": "Manual Therapy / Tuina",
    "acupressure": "Acupressure",
    "dds_electric": "DDS / Electrical Stimulation Device",
    "active_mobilization": "Active Mobilization & Ergonomics"
  },
  "zh": {
    "manual_tuina": "推拿手法 / 软组织松解",
    "acupressure": "穴位按压 / 点穴疗法",
    "dds_electric": "DDS 生物电理疗仪",
    "active_mobilization": "主动关节松动与姿态训练"
  },
  "vi": {
    "manual_tuina": "Xoa bóp bấm huyệt / Trị liệu cơ học",
    "acupressure": "Bấm huyệt điều trị",
    "dds_electric": "Trị liệu điện sinh học DDS",
    "active_mobilization": "Vận động khớp chủ động & Công thái học"
  }
}

for lang in ["en", "zh", "vi"]:
    path = I18N_DIR / f"{lang}.json"
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    d["safety_flags"] = SAFETY_FLAGS[lang]
    d["modalities"] = MODALITIES[lang]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

print("Enriched host i18n dictionaries with safety_flags and modalities.")
