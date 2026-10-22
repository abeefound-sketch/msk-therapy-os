for f in tests/test_*.py; do
    mod=$(basename "$f" .py)
    if [ "$mod" = "test_anatomical_workbench" ]; then continue; fi
    echo "=== Running $mod ==="
    timeout 5 python3 -m unittest "tests.$mod" 2>&1 | tail -n 2
done
