python3 -c "
with open('msk_therapy_os/server.py') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '/api/atlas/status' in line or 'def _handle_atlas' in line or 'ready' in line:
        print(f'{i}: {line.strip()}')
"
