# MSK-Therapy-OS V1.0 - PowerShell 1-Click Runtime Launcher
# Scope: ENGINEERING_RESEARCH_ONLY
[CmdletBinding()]
param(
    [int]$Port = 8000
)

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot
$env:PYTHONPATH = $RepoRoot

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "           MSK-Therapy-OS V1.0 - Desktop 1-Click Runtime Launcher              " -ForegroundColor Cyan
Write-Host "                Scope: ENGINEERING_RESEARCH_ONLY                               " -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# Verify Python
Write-Host "[1/3] Kiểm tra môi trường Python..." -ForegroundColor Green
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "Không tìm thấy Python. Vui lòng cài đặt Python 3.10+."
    exit 1
}

# Open browser after a short delay in background
Start-Job -ScriptBlock {
    param($p)
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:$p/sandbox/p21/index.html"
} -ArgumentList $Port | Out-Null

Write-Host "[2/3] Mở giao diện Web Atlas V1.0 tại http://127.0.0.1:$Port/sandbox/p21/index.html" -ForegroundColor Green
Write-Host "[3/3] Đang khởi động HTTP server trên cổng $Port (Nhấn Ctrl+C để thoát)..." -ForegroundColor Green

python -m msk_therapy_os.server --port $Port
