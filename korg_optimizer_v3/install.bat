@echo off
echo ==========================================
echo   Korg MIDI Optimizer - Instalacija
echo ==========================================
echo.

[1/3] Provjera Python verzije...
python --version
if errorlevel 1 (
    echo GRESKA: Python nije instaliran ili nije u PATH-u
    pause
    exit /b 1
)
echo.

[2/3] Instalacija potrebnih biblioteka...
echo Instaliram mido i pytest...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo GRESKA: Instalacija biblioteka nije uspjela
    pause
    exit /b 1
)
echo.

[3/3] Provjera aplikacije...
python -c "from rxoptimizer import optimize, analyze_dna; print('rxoptimizer - OK')"
if errorlevel 1 (
    echo GRESKA: Provjera aplikacije nije uspjela
    pause
    exit /b 1
)
echo.

echo ==========================================
echo   INSTALACIJA USPESNA!
echo ==========================================
echo.
echo Upotreba:
echo   python main.py analyze ^<folder^> -o rules.json
echo   python main.py optimize ^<input.mid^> -o ^<output.mid^>
echo   python main.py batch ^<input_folder^> ^<output_folder^>
echo.
echo   python -m pytest tests/ -v
echo.
pause
