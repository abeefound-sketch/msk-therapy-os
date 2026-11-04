ls -la ~/.bash_aliases ~/.ai-aliases.sh ~/.bashrc
cat ~/.bash_aliases 2>/dev/null || true
echo "=== .ai-aliases.sh ==="
cat ~/.ai-aliases.sh 2>/dev/null || true
echo "=== check targets ==="
ls -ld /mnt/c/Users/tuanh/Downloads/msk-research-lab 2>/dev/null || echo "msk-research-lab not found on C"
ls -ld /mnt/d/5projects/msk-therapy-os 2>/dev/null || true
ls -ld /mnt/d/5Projects/msk-therapy-os 2>/dev/null || true
ls -ld /mnt/d/1docs 2>/dev/null || echo "no /mnt/d/1docs"
ls -ld /mnt/d/*/1docs 2>/dev/null || true
