python3 -c "
with open('tests/test_assessment_soap.py') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if line.strip().startswith('def test_'):
        print(f'{i}: {line.strip()}')
"
