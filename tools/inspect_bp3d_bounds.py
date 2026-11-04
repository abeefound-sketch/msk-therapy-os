import json
from pathlib import Path

atlas = json.load(open('3refs/upstream/tcm-3d/public/models/atlas.json', encoding='utf-8'))
pmap = {p['id']: p for p in atlas['parts']}

for tid in ['FJ3384', 'FJ3362', 'FJ3368', 'FJ3349', 'FJ3391', 'FJ3352', 'FJ3387', 'FJ3360']:
    p = pmap[tid]
    bounds = p['bounds']
    b_min = [round(x, 4) for x in bounds[0]]
    b_max = [round(x, 4) for x in bounds[1]]
    print(f"{tid} ({p['name']}): min={b_min}, max={b_max}")
