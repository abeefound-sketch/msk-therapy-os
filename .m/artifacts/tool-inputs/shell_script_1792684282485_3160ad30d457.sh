python3 -c "
import unittest, os, sys

tests_to_run = [
    'test_assessment_soap',
    'test_cli',
    'test_evidence_anatomy',
    'test_mvp',
    'test_safety',
    'test_safe_sqlite_restore',
    'test_tracking_and_meridians',
    'test_auth_and_rbac'
]

for mod in tests_to_run:
    suite = unittest.defaultTestLoader.loadTestsFromName(f'tests.{mod}')
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=0)
    print(f'Testing {mod} ({suite.countTestCases()} tests)... ', end='', flush=True)
    res = runner.run(suite)
    if res.wasSuccessful():
        print('PASS')
    else:
        print(f'FAIL (errors={len(res.errors)}, failures={len(res.failures)})')
"
