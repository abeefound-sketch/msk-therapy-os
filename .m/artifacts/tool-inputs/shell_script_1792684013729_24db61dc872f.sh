python3 -c "
import unittest, os, sys, time

test_files = sorted([f[:-3] for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')])
for mod_name in test_files:
    if mod_name == 'test_anatomical_workbench':
        continue
    t0 = time.time()
    try:
        suite = unittest.defaultTestLoader.loadTestsFromName(f'tests.{mod_name}')
        runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=0)
        res = runner.run(suite)
        elapsed = time.time() - t0
        print(f'{mod_name}: count={suite.countTestCases()} time={elapsed:.2f}s success={res.wasSuccessful()}')
    except Exception as e:
        print(f'{mod_name}: EXCEPTION {e}')
"
