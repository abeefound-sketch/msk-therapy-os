python3 -c "
import os
files = sorted([f for f in os.listdir('tests') if f.endswith('.py')])
print(f'Total test files: {len(files)}')
for f in files:
    print(f' - {f} ({os.path.getsize(os.path.join(\"tests\", f))} bytes)')
"
