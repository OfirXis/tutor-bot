# run.ps1 — First-time setup and launcher for Course Tutor
# Double-click this file in PowerShell, or right-click → "Run with PowerShell"

Set-Location $PSScriptRoot

$venv = ".venv"

# Create virtual environment once
if (-not (Test-Path "$venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv $venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Could not create virtual environment. Is Python installed?" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate it
& "$venv\Scripts\Activate.ps1"

# Install / upgrade requirements quietly
Write-Host "Installing requirements (only downloads new packages)..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet --upgrade

# Build the retrieval index on first run
if (-not (Test-Path "db\index")) {
    Write-Host "Building course index (first run only)..." -ForegroundColor Cyan
    python build_index.py
}

# Launch the app
Write-Host "`nStarting Course Tutor — opening browser at http://localhost:8501`n" -ForegroundColor Green
streamlit run app.py
