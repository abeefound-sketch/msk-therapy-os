python3 -c "
import subprocess

commits = ['854a722', '4cb3d30', 'c41a8bb', 'e9ac11d', 'ea58f38', '287b58b', '877450c']
for c in commits:
    out = subprocess.check_output(['git', 'show', '--stat', '--oneline', c]).decode('utf-8')
    lines = out.splitlines()
    print(lines[0])
    for l in lines[1:]:
        if 'file' in l or 'insertion' in l or 'deletion' in l or '.py' in l or '.js' in l or '.html' in l or '.md' in l:
            print('  ', l.strip())
"
