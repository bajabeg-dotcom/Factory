@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Korg MIDI Optimizer - Instalacija
echo ==========================================
echo.

REM Provera Python verzije
python --version >nul 2>&1
if errorlevel 1 (
    echo [GRESKA] Python nije instaliran ili nije u PATH!
    echo Preuzmi Python sa: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Python verzija:
python --version
echo.

REM Provera pip-a
echo [2/4] Provera pip-a...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [GRESKA] pip nije dostupan!
    pause
    exit /b 1
)
echo pip je dostupan - OK
echo.

REM Kreiranje virtualnog okruzenja ako ne postoji
if not exist "venv" (
    echo [3/4] Kreiranje virtualnog okruzenja...
    python -m venv venv
    if errorlevel 1 (
        echo [GRESKA] Neuspesno kreiranje virtualnog okruzenja!
        pause
        exit /b 1
    )
    echo Virtualno okruzenje kreirano - OK
) else (
    echo [3/4] Virtualno okruzenje vec postoji - preskace se
)
echo.

REM Aktivacija virtualnog okruzenja i instalacija zavisnosti
echo [4/4] Instalacija zavisnosti...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [GRESKA] Instalacija zavisnosti nije uspela!
    pause
    exit /b 1
)
echo Zavisnosti instalirane - OK
echo.

REM Verifikacija instalacije
echo [5/5] Verifikacija instalacije...
python -c "from rxoptimizer import optimize, analyze_dna; print('Import uspesan!')" 2>nul
if errorlevel 1 (
    echo [UPOZORENJE] Import nije uspeo, ali nastavljamo...
) else (
    echo Modul uspesno ucitan - OK
)
echo.

echo ==========================================
echo   INSTALACIJA USPESNA!
echo ==========================================
echo.
echo Sledeci koraci:
echo 1. Koristi run.bat za pokretanje aplikacije
echo 2. Primeri:
echo    run.bat analyze ./data/gold --output rules.json
echo    run.bat optimize song.mid -o song_opt.mid
echo    run.bat batch ./input ./output
echo.
pause
