import json
from pathlib import Path

ACU_FILE = Path("D:/5Projects/msk-therapy-os/msk_therapy_os/static/atlas/data/acupuncture_3d.json")
REG_FILE = Path("D:/5Projects/msk-therapy-os/msk_therapy_os/data/medical_terminology_registry.json")

with open(ACU_FILE, "r", encoding="utf-8") as f:
    acu = json.load(f)

with open(REG_FILE, "r", encoding="utf-8") as f:
    reg = json.load(f)

reg_points = reg.get("points", {})
reg_dc = {d["code"]: d for d in reg.get("dien_chan", [])}
reg_thai = {t["id"]: t for t in reg.get("thai_sen_sib", [])}

# Enrich points with name_vi
count_pts = 0
for code, p in acu.get("points", {}).items():
    if code in reg_points:
        p["name_vi"] = reg_points[code]["name_vi"]
        count_pts += 1

# Enrich dien chan
count_dc = 0
for d in acu.get("dien_chan", []):
    code = d.get("code")
    if code in reg_dc:
        d["name_vi"] = reg_dc[code]["name_vi"]
        d["name_zh"] = reg_dc[code]["name_zh"]
        d["name_en"] = reg_dc[code]["name_en"]
        d["indications_i18n"] = reg_dc[code]["indications"]
        count_dc += 1

# Enrich thai lines
count_thai = 0
for t in acu.get("thai_lines", []):
    t_id = t.get("id")
    if t_id in reg_thai:
        t["name_vi"] = reg_thai[t_id]["name_vi"]
        t["name_zh"] = reg_thai[t_id]["name_zh"]
        t["name_en"] = reg_thai[t_id]["name_en"]
        count_thai += 1

with open(ACU_FILE, "w", encoding="utf-8") as f:
    json.dump(acu, f, ensure_ascii=False, indent=2)

print(f"Enriched {ACU_FILE}:")
print(f"  Points with name_vi: {count_pts}")
print(f"  Dien Chan points: {count_dc}")
print(f"  Thai Sen lines: {count_thai}")
