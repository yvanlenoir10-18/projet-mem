# wood_pilot
# Usage : clic droit sur start-local.ps1 > "Executer avec PowerShell"
# OU dans PowerShell : .\start-local.ps1
#
# Ce script ne fait ni git pull, ni pip install.
# Il sert a lancer l'application sans connexion internet,
# une fois l'installation initiale deja faite.

Write-Host "=== wood_pilot ===" -ForegroundColor Green

Set-Location $PSScriptRoot

if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host ""
    Write-Host "Environnement virtuel introuvable." -ForegroundColor Red
    Write-Host "Fais d'abord l'installation initiale avec internet :" -ForegroundColor Yellow
    Write-Host "  python -m venv venv"
    Write-Host "  .\venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

if (-not (Test-Path "instance")) {
    New-Item -ItemType Directory -Path "instance" | Out-Null
}

Write-Host "Activation de l'environnement virtuel..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

python -c "import flask, flask_sqlalchemy, flask_login, flask_wtf, openpyxl" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Des dependances Python manquent dans le venv." -ForegroundColor Red
    Write-Host "Reconnecte internet une seule fois puis lance :" -ForegroundColor Yellow
    Write-Host "  .\venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

Write-Host ""
Write-Host "Application prete sur http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Ouvre ce lien dans ton navigateur : http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "Appuie sur CTRL+C pour arreter." -ForegroundColor Gray

python run.py
