python3 -c "
for fname in ['docs/M282_FINAL_ACCEPTANCE_MATRIX.md', 'docs/M3_IMPLEMENTATION_READINESS.md']:
    print(f'=== {fname} ===')
    try:
        with open(fname) as f:
            print(''.join(f.readlines()[:50]))
    except Exception as e:
        print(f'Error reading {fname}: {e}')
"
