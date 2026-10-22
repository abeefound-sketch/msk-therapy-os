python3 -c "
import zipfile, os, shutil
from pathlib import Path

slug = 'msk-therapy-os-m3-roadmap'
stage_dir = Path(f'/tmp/{slug}')
zip_path = Path(f'/tmp/{slug}-source.zip')

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(stage_dir):
        for f in files:
            full_p = Path(root) / f
            arc_p = full_p.relative_to(stage_dir.parent)
            zf.write(full_p, arc_p)

print('Zip created successfully:', zip_path, 'Size:', os.path.getsize(zip_path))

for dest in [Path('/mnt/c/Users/tuanh/Desktop'), Path('/home/tuan/Desktop')]:
    if dest.exists():
        shutil.copy2(zip_path, dest / f'{slug}-source.zip')
        print(f'Copied to {dest / f\"{slug}-source.zip\"}')
"
