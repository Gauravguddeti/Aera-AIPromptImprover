# Aera - Start both Backend and Frontend
Write-Host "Starting Aera..." -ForegroundColor Cyan

# Start Backend
Write-Host "`nStarting Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; `$env:PYTHONPATH = `"`$PWD`"; & '$PSScriptRoot\.venv\Scripts\Activate.ps1'; python -m uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000"

# Wait a bit for backend to start
Start-Sleep -Seconds 2

# Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "Both servers starting in separate windows!" -ForegroundColor Green
Write-Host "Backend: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')