# JOBSINLINE PowerShell Startup Script
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "              Starting JOBSINLINE Server                " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    $pythonExe = "C:\Users\M.shashank\AppData\Local\Programs\Python\Python311\python.exe"
}

Write-Host "Using Python: $pythonExe" -ForegroundColor Green
& $pythonExe --version

Write-Host "`nStarting server on http://127.0.0.1:5000 ..." -ForegroundColor Yellow
& $pythonExe app.py
