import os
from pathlib import Path
import subprocess

desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
bat_path = Path("D:/5Projects/msk-therapy-os/start_studio.bat").resolve()

ps_command = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop}\\MSK-Therapy-Studio.lnk")
$Shortcut.TargetPath = "{bat_path}"
$Shortcut.WorkingDirectory = "{bat_path.parent}"
$Shortcut.Description = "Khoi dong MSK-Therapy-OS 3D Education Studio"
$Shortcut.Save()
"""

subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], check=True)

lnk_file = desktop / "MSK-Therapy-Studio.lnk"
print("Desktop shortcut exists:", lnk_file.exists(), lnk_file)
