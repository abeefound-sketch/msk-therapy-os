python3 -c "
import unittest, os, sys

test_files = sorted([f[:-3] for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')])
for mod_name in test_files:
    suite = unittest.defaultTestLoader.loadTestsFromName(f'tests.{mod_name}')
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=0)
    print(f'Testing {mod_name} ({suite.countTestCases()} tests)... ', end='', flush=True)
    res = runner.run(suite)
    if res.wasSuccessful():
        print('PASS')
    else:
        print(f'FAIL (errors={len(res.errors)}, failures={len(res.failures)})')
"
