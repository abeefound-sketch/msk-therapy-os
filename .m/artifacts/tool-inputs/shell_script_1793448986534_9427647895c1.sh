python3 -c "
import zipfile, os, shutil
from pathlib import Path

slug = 'msk-therapy-os-p17-roadmap'
stage_dir = Path(f'/tmp/{slug}')
zip_path = Path(f'/tmp/{slug}-source.zip')

if stage_dir.exists():
    shutil.rmtree(stage_dir)
stage_dir.mkdir(parents=True)

# Copy core msk_therapy_os package
dst_pkg = stage_dir / 'msk_therapy_os'
shutil.copytree('msk_therapy_os', dst_pkg, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

# Copy tests
dst_tests = stage_dir / 'tests'
shutil.copytree('tests', dst_tests, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

# Copy key 1docs audits and specs (P13-P17 and foundational)
dst_docs = stage_dir / '1docs'
dst_docs.mkdir(parents=True)

# Foundational specs in 1docs
for f in os.listdir('1docs'):
    p = os.path.join('1docs', f)
    if os.path.isfile(p):
        shutil.copy2(p, dst_docs / f)

# Copy audits/P13-P17 and specs
for sub in ['specs', 'audits/P13', 'audits/P14', 'audits/P15', 'audits/P16', 'audits/P17']:
    src_sub = Path('1docs') / sub
    if src_sub.exists():
        dst_sub = dst_docs / sub
        shutil.copytree(src_sub, dst_sub, ignore=shutil.ignore_patterns('*.png', '*.zip'))

# Copy root scripts and reports
for f in ['README.md', 'Dockerfile', 'pytest.ini', 'start_app.py', 'start_studio.bat', 'create_desktop_shortcut.py', 'p10_0_milestone_delivery_report.md']:
    if os.path.exists(f):
        shutil.copy2(f, stage_dir / f)

# Create zip archive
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(stage_dir):
        for f in files:
            full_p = Path(root) / f
            arc_p = full_p.relative_to(stage_dir.parent)
            zf.write(full_p, arc_p)

size_mb = os.path.getsize(zip_path) / (1024 * 1024)
print(f'Zip created: {zip_path} ({size_mb:.2f} MB)')

for d in ['/mnt/c/Users/tuanh/Desktop', '/home/tuan/Desktop']:
    dest = Path(d)
    if dest.exists():
        shutil.copy2(zip_path, dest / f'{slug}-source.zip')
        print(f'Copied to {dest / f\"{slug}-source.zip\"}')
"
