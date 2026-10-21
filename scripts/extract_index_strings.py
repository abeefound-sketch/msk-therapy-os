from bs4 import BeautifulSoup
import json
import re

with open('msk_therapy_os/static/index.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

strings = set()

# Header & nav tabs
for t in soup.find_all(class_=re.compile(r'tab-btn')):
    s = t.get_text(strip=True)
    if s: strings.add(('tab', s))

# All buttons
for b in soup.find_all('button'):
    s = b.get_text(strip=True)
    if s and len(s) < 100: strings.add(('button', s))
    if b.get('title'): strings.add(('tooltip', b.get('title')))

# Headings
for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
    s = h.get_text(strip=True)
    if s and len(s) < 120: strings.add(('heading', s))

# Labels
for l in soup.find_all('label'):
    s = l.get_text(strip=True)
    if s and len(s) < 100: strings.add(('label', s))

# Badges and spans
for span in soup.find_all('span', class_=re.compile(r'badge|tag|label')):
    s = span.get_text(strip=True)
    if s and len(s) < 80: strings.add(('badge', s))

# Select options
for opt in soup.find_all('option'):
    s = opt.get_text(strip=True)
    if s and len(s) < 100: strings.add(('option', s))

print(f'Total unique UI strings extracted from index.html: {len(strings)}')
categories = {}
for cat, s in sorted(strings):
    categories.setdefault(cat, []).append(s)

for cat, items in categories.items():
    print(f'\n--- {cat.upper()} ({len(items)}) ---')
    for item in items[:10]:
        print(' ', repr(item))
    if len(items) > 10:
        print(f'  ... and {len(items)-10} more')
