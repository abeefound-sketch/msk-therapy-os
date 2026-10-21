import json
from pathlib import Path

I18N_DIR = Path("D:/5Projects/msk-therapy-os/msk_therapy_os/static/i18n")

extra = {
  "en": {
    "no_records": "No structured SOAP notes recorded for this case yet.",
    "status_supervised": "SUPERVISED",
    "feedback_placeholder": "Supervisor review comments..."
  },
  "zh": {
    "no_records": "此病例尚未记录任何结构化 SOAP 病历。",
    "status_supervised": "带教已复核",
    "feedback_placeholder": "带教医师审核意见..."
  },
  "vi": {
    "no_records": "Chưa có hồ sơ SOAP nào được ghi nhận cho ca bệnh này.",
    "status_supervised": "ĐÃ GIÁM SÁT",
    "feedback_placeholder": "Ý kiến nhận xét của giảng viên lâm sàng..."
  }
}

for lang in ["en", "zh", "vi"]:
    path = I18N_DIR / f"{lang}.json"
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    for k, v in extra[lang].items():
        d["soap"][k] = v
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

print("Updated SOAP extra keys in en, zh, vi dictionaries.")
