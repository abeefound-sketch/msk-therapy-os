from pathlib import Path

index_path = Path("D:/5Projects/msk-therapy-os/msk_therapy_os/static/index.html")
text = index_path.read_text(encoding="utf-8")

target = """        document.getElementById("selectedRegionTitle").textContent = activeRegion;
        loadRegionAnatomy(activeRegion);
        loadRegionQuestionnaires(activeRegion);
        atlasCommand('set_region', { region: activeRegion });"""

replacement = """        document.getElementById("selectedRegionTitle").textContent = activeRegion === "all" ? "Full Body (All Regions)" : activeRegion;
        loadRegionAnatomy(activeRegion);
        loadRegionQuestionnaires(activeRegion);
        if (activeRegion === "all") {
          if (!layerStates.meridians) {
            toggleAtlasLayer('meridians');
          }
        }
        atlasCommand('set_region', { region: activeRegion });"""

text_crlf = '\r\n' in text
target_norm = target.replace('\n', '\r\n') if text_crlf else target
replacement_norm = replacement.replace('\n', '\r\n') if text_crlf else replacement

assert target_norm in text, 'target not found in index.html'
text = text.replace(target_norm, replacement_norm, 1)
index_path.write_text(text, encoding="utf-8")
print("Updated region button handler in index.html!")
