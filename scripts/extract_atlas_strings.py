from bs4 import BeautifulSoup
import re

with open('msk_therapy_os/static/atlas/index.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

strings = set()
for b in soup.find_all('button'):
    s = b.get_text(strip=True)
    if s: strings.add(('button', s))
    if b.get('title'): strings.add(('tooltip', b.get('title')))

for t in soup.find_all(class_=re.compile(r'tab')):
    s = t.get_text(strip=True)
    if s: strings.add(('tab', s))

for l in soup.find_all('label'):
    s = l.get_text(strip=True)
    if s: strings.add(('label', s))

for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'summary', 'span']):
    s = h.get_text(strip=True)
    if s and len(s) < 100: strings.add(('text', s))

print(f'Total atlas unique strings: {len(strings)}')
categories = {}
for cat, s in sorted(strings):
    categories.setdefault(cat, []).append(s)

for cat, items in categories.items():
    print(f'\n--- ATLAS {cat.upper()} ({len(items)}) ---')
    for item in items[:8]:
        print(' ', repr(item))
    if len(items) > 8:
        print(f'  ... and {len(items)-8} more')
