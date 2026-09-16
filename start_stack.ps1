$env:PYTHONPATH='.'
$env:AI_PROVIDER='mock'
$env:ENABLE_AI_CACHE='true'
Start-Process "./backend/venv/Scripts/python.exe" -ArgumentList "-m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000" -RedirectStandardOutput "backend.log" -RedirectStandardError "backend_err.log" -NoNewWindow
Start-Process "npm.cmd" -ArgumentList "run web" -RedirectStandardOutput "frontend.log" -RedirectStandardError "frontend_err.log" -NoNewWindow
