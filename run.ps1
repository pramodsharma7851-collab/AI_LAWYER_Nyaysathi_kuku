Write-Host "Starting NyayaSathi AI Legal Helper..." -ForegroundColor Cyan
if (Test-Path ".\venv\Scripts\streamlit.exe") {
    & .\venv\Scripts\streamlit.exe run app.py
} else {
    Write-Host "Python virtual environment not found in .\venv" -ForegroundColor Red
}
