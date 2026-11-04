powershell.exe -NoProfile -Command "[Environment]::GetFolderPath('Desktop')" || true
powershell.exe -NoProfile -Command "Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders' | Select-Object Desktop" || true
