$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment belum ada. Jalankan: python -m venv .venv"
}

& $Python -m streamlit run app.py --server.headless true --server.port 8501 --server.address localhost
