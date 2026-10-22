python3 -c "
import os
total = 0
for root, dirs, files in os.walk('msk_therapy_os'):
    for f in files:
        p = os.path.join(root, f)
        total += os.path.getsize(p)
print(f'msk_therapy_os size: {total / 1024 / 1024:.2f} MB')

docs_total = 0
for root, dirs, files in os.walk('docs'):
    for f in files:
        p = os.path.join(root, f)
        docs_total += os.path.getsize(p)
print(f'docs size: {docs_total / 1024 / 1024:.2f} MB')

tests_total = 0
for root, dirs, files in os.walk('tests'):
    for f in files:
        p = os.path.join(root, f)
        tests_total += os.path.getsize(p)
print(f'tests size: {tests_total / 1024 / 1024:.2f} MB')
"
