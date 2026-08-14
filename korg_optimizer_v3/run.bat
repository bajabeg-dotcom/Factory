@echo off
echo ==========================================
echo   Korg MIDI Optimizer - Pokretanje
echo ==========================================
echo.

if "%1"=="" (
    echo Upotreba: run.bat ^<komanda^> [opcije]
    echo.
    echo Komande:
    echo   analyze ^<folder^> [-o rules.json]  - Analiziraj DNA
    echo   optimize ^<input.mid^> [-o output.mid] - Optimizuj fajl
    echo   batch ^<input_folder^> ^<output_folder^> - Batch optimizacija
    echo   test - Pokreni testove
    echo.
    echo Primjeri:
    echo   run.bat analyze data\gold -o rules.json
    echo   run.bat optimize input\song.mid -o output\song_opt.mid
    echo   run.bat batch input output -d
    echo   run.bat test
    echo.
    pause
    exit /b 0
)

if "%1"=="test" (
    echo Pokrecem testove...
    python -m pytest tests/ -v
    pause
    exit /b 0
)

if "%1"=="analyze" (
    shift
    python main.py analyze %*
    pause
    exit /b 0
)

if "%1"=="optimize" (
    shift
    python main.py optimize %*
    pause
    exit /b 0
)

if "%1"=="batch" (
    shift
    python main.py batch %*
    pause
    exit /b 0
)

echo Nepoznata komanda: %1
echo.
run.bat
exit /b 1
