ps aux | grep python | grep -v grep || true
python3 -c "
with open('tests/test_server.py') as f:
    print(''.join(f.readlines()[:50]))
"
