python3 -c "
import os, re

for root, _, files in os.walk('tests'):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p) as fh:
                content = fh.read()
                matches = re.findall(r'^\s*(?:import|from)\s+([a-zA-Z0-9_]+)', content, re.M)
                third = [m for m in matches if m not in ('unittest', 'sys', 'os', 'pathlib', 'tempfile', 'json', 'threading', 'time', 'urllib', 'sqlite3', 'dataclasses', 'typing', 'enum', 'math', 'shutil', 'hashlib', 'datetime', 're', 'copy', 'subprocess', 'msk_therapy_os')]
                if third:
                    print(f'{f}: {set(third)}')
"
