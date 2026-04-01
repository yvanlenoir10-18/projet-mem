@echo off
title Fix WSL2 Memory - OOM Antigravity
color 0A

net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [ERREUR] Lance en tant qu'ADMINISTRATEUR.
    pause
    exit /b 1
)

echo ============================================
echo   CORRECTION MEMOIRE WSL2 (OOM Antigravity)
echo ============================================
echo.

:: Detecter RAM totale en MB
for /f "tokens=2 delims==" %%a in ('wmic computersystem get TotalPhysicalMemory /value') do set RAM_BYTES=%%a
set /a RAM_GB=%RAM_BYTES:~0,-9%
echo RAM totale detectee : environ %RAM_GB% GB
echo.

:: Creer .wslconfig avec limite memoire (50% de la RAM)
set /a WSL_MEM=%RAM_GB% / 2
if %WSL_MEM% LSS 2 set WSL_MEM=2
if %WSL_MEM% GTR 8 set WSL_MEM=8

echo [1/3] Creation de %USERPROFILE%\.wslconfig...
(
echo [wsl2]
echo memory=%WSL_MEM%GB
echo processors=4
echo swap=4GB
echo localhostForwarding=true
echo kernelCommandLine=sysctl.vm.vfs_cache_pressure=50
) > "%USERPROFILE%\.wslconfig"

echo       Memoire WSL2 limitee a %WSL_MEM%GB
echo [OK] .wslconfig cree.
echo.

:: Augmenter la memoire virtuelle Windows (pagefile)
echo [2/3] Augmentation de la memoire virtuelle Windows...
wmic pagefile delete >nul 2>&1
wmic pagefileset create name="C:\pagefile.sys" >nul 2>&1
wmic pagefileset where name="C:\\pagefile.sys" set InitialSize=4096,MaximumSize=8192 >nul 2>&1
echo [OK] Pagefile configure : 4 Go initial, 8 Go maximum.
echo.

:: Redemarrer WSL2
echo [3/3] Redemarrage de WSL2...
wsl --shutdown
echo [OK] WSL2 arrete. Il redemarrera automatiquement.
echo.

echo ============================================
echo   TERMINE. Contenu de .wslconfig :
echo ============================================
type "%USERPROFILE%\.wslconfig"
echo.
echo Redemarre Windows pour appliquer le pagefile.
echo.
pause
shutdown /r /t 30 /c "Redemarrage apres config memoire WSL2"
