python3 -c "
for fname in ['SPEC.md', 'ENGINEERING_HANDOFF.md', 'README.md']:
    print(f'=== {fname} ===')
    with open(fname) as f:
        lines = f.readlines()
        print(''.join(lines[:60]))
"
