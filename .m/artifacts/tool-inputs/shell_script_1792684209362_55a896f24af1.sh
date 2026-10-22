find /mnt/c/Users/tuanh/AppData/Roaming/open-anatomy-atlas -maxdepth 3 2>/dev/null || true
find /mnt/d -maxdepth 3 -name "*open-anatomy*" 2>/dev/null || true
find ~/.config ~/.local -maxdepth 3 -name "*open-anatomy*" 2>/dev/null || true
