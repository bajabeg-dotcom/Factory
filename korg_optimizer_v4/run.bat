@echo off
setlocal enabledelayedexpansion

REM Aktivacija virtualnog okruzenja
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [UPOZORENJE] Virtualno okruzenje nije pronadjeno!
    echo Pokreni prvo install.bat
    pause
    exit /b 1
)

REM Provera da li ima argumenata
if "%~1"=="" (
    echo.
    echo ==========================================
    echo   Korg MIDI Optimizer
    echo ==========================================
    echo.
    echo Upotreba:
    echo   run.bat analyze ^<direktorijum^> [-o output.json]
    echo   run.bat optimize ^<ulazni_fajl^> [-o izlazni_fajl] [--detailed]
    echo   run.bat batch ^<ulaz_dir^> ^<izlaz_dir^> [-r rules.json]
    echo.
    echo Primeri:
    echo   run.bat analyze ./data/gold --output rules.json
    echo   run.bat optimize song.mid -o song_optimized.mid --detailed
    echo   run.bat batch ./input ./output --rules rules.json
    echo   run.bat test  (pokrece testove)
    echo.
    python main.py --help
    pause
    exit /b 0
)

REM Poseban slucaj za testove
if /i "%~1"=="test" (
    echo Pokrecem testove...
    echo.
    python -m pytest tests/ -v
    pause
    exit /b %errorlevel%
)

REM Pokretanje glavne aplikacije sa argumentima
python main.py %*

pause
