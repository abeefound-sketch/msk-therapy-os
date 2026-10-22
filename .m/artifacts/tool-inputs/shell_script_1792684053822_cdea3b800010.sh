python3 -u -c "
import unittest, os, sys, time

for fname in sorted(os.listdir('tests')):
    if fname.startswith('test_') and fname.endswith('.py'):
        print('Checking', fname, flush=True)
"
