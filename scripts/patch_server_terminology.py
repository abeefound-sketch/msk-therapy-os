with open('msk_therapy_os/server.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''                elif path == "/api/acupuncture-3d":
                    acu_file = ATLAS_UI_DIR / "data" / "acupuncture_3d.json"
                    if acu_file.exists():
                        self._send_text(acu_file.read_text(encoding="utf-8"), content_type="application/json")
                    else:
                        self._send_json({"error": "Acupuncture 3D dataset not found"}, status=HTTPStatus.NOT_FOUND)'''

replacement = '''                elif path == "/api/acupuncture-3d":
                    acu_file = ATLAS_UI_DIR / "data" / "acupuncture_3d.json"
                    if acu_file.exists():
                        self._send_text(acu_file.read_text(encoding="utf-8"), content_type="application/json")
                    else:
                        self._send_json({"error": "Acupuncture 3D dataset not found"}, status=HTTPStatus.NOT_FOUND)

                elif path == "/api/terminology":
                    from msk_therapy_os.terminology import MedicalTerminologyRegistry
                    reg = MedicalTerminologyRegistry.get_instance()
                    category = query.get("category", [None])[0]
                    lang = query.get("lang", ["en"])[0]
                    if category == "meridians":
                        self._send_json(list(reg.meridians.values()))
                    elif category == "points":
                        self._send_json(reg.points)
                    elif category == "dien_chan":
                        self._send_json(list(reg.dien_chan.values()))
                    elif category == "thai":
                        self._send_json(list(reg.thai_sen_sib.values()))
                    elif category == "structures":
                        self._send_json(list(reg.structures.values()))
                    else:
                        self._send_json(reg.data)'''

text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

assert target_norm in text_norm, "Target not found in server.py"
text_norm = text_norm.replace(target_norm, replacement_norm, 1)

with open('msk_therapy_os/server.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text_norm)

print("server.py updated with /api/terminology successfully.")
