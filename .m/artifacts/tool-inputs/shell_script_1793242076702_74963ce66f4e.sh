python3 -c "
with open('1docs/audits/P9_4_FINAL_ENGINEERING_HANDOFF.md') as f:
    text = f.read()

import re
headers = re.findall(r'^(#+\s+.*)', text, re.M)
for h in headers:
    print(h)
"
