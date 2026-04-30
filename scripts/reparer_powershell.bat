@echo off
title Reparation PowerShell - CUF Project
color 0A

echo ============================================
echo   REPARATION POWERSHELL 0xc0000142
echo ============================================
echo.

:: Verifier droits admin
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [ERREUR] Lance ce fichier en tant qu'ADMINISTRATEUR.
    echo Clic droit sur le fichier ^> "Executer en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

echo [1/4] Reparation des fichiers systeme (SFC)...
echo       Patiente, cela peut prendre 5-10 minutes.
echo.
sfc /scannow
echo.
echo [OK] SFC termine.
echo.

echo [2/4] Reparation de l'image Windows (DISM)...
echo       Patiente, cela peut prendre 10-15 minutes.
echo.
DISM /Online /Cleanup-Image /RestoreHealth
echo.
echo [OK] DISM termine.
echo.

echo [3/4] Deuxieme passe SFC apres DISM...
sfc /scannow
echo.
echo [OK] Deuxieme SFC termine.
echo.

echo [4/4] Reinstallation de PowerShell via winget...
winget install --id Microsoft.PowerShell --source winget --accept-package-agreements --accept-source-agreements
echo.
echo [OK] PowerShell reinstalle.
echo.

echo ============================================
echo   REPARATION TERMINEE
echo   Redemarre Windows maintenant.
echo ============================================
echo.
pause
shutdown /r /t 30 /c "Redemarrage apres reparation PowerShell"
