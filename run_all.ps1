$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvPath = Join-Path $root ".venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "Creating virtual environment..."
    py -3 -m venv $venvPath
}

Write-Host "Installing dependencies..."
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r requirements.txt

Write-Host "Initializing database..."
& $pythonExe -c "from app import create_app; app = create_app(); app.app_context().push(); from app.models import init_db; init_db(); print('Database ready')"

Write-Host "Starting AgriConnect ZW..."
& $pythonExe app.py
