# Windows convenience wrapper. The cross-platform setup logic lives in run.py.
$ErrorActionPreference = "Stop"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 "$PSScriptRoot\run.py" @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$PSScriptRoot\run.py" @args
} else {
    Write-Host "ERROR: Python 3.11 or newer is required." -ForegroundColor Red
    exit 1
}

exit $LASTEXITCODE
