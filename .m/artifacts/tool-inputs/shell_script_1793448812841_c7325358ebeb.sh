ls -la p*.md 1docs/audits/P1*.md 1docs/specs/P1*.md 2>/dev/null || true
python3 -c "
import os
for f in os.listdir('.'):
    if f.endswith('.md') and ('report' in f or 'p1' in f or 'p9' in f):
        print(f'File: {f} ({os.path.getsize(f)} bytes)')
"
