python3 -c "
import unittest, os, sys

passed = []
failed = []
skipped = []

test_files = sorted([f[:-3] for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')])
for mod in test_files:
    try:
        suite = unittest.defaultTestLoader.loadTestsFromName(f'tests.{mod}')
        runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=0)
        res = runner.run(suite)
        if res.wasSuccessful():
            passed.append((mod, suite.countTestCases()))
        else:
            failed.append((mod, len(res.failures), len(res.errors)))
    except Exception as e:
        skipped.append((mod, str(e)))

print('=== PASSED ===')
for m, c in passed:
    print(f'  {m}: {c} tests')
print('=== FAILED ===')
for m, f, e in failed:
    print(f'  {m}: failures={f}, errors={e}')
print('=== SKIPPED/ERROR LOADING ===')
for m, err in skipped:
    print(f'  {m}: {err}')
"
