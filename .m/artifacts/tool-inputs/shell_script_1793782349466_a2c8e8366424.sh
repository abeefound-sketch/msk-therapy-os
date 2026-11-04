grep -n -E '^(alias\s+)?(0|1|2|3|4|5|6|7|8)\(\)|^(alias\s+)?(0|1|2|3|4|5|6|7|8)=' ~/.bashrc ~/.bash_aliases ~/.profile ~/.ai-aliases.sh /mnt/d/1docs/* 2>/dev/null || true
echo "=== check .bashrc ==="
grep -E 'source|\.ai-aliases' ~/.bashrc
