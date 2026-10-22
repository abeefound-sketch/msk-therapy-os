which pytest || true
find /mnt/d/5projects/msk-therapy-os -maxdepth 3 -name "pytest" -o -name "activate" 2>/dev/null || true
find /home/tuan/.local /home/tuan/.cache /home/tuan -maxdepth 3 -name "pytest" 2>/dev/null || true
