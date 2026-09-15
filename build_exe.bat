@echo off
setlocal

REM ============================================================
REM  DriverUpdater - Script de compilacion a EXE
REM ============================================================

REM Instala PyInstaller si no esta presente
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    python -m pip install pyinstaller
)

REM Limpia compilaciones anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist DriverUpdater.spec del /q DriverUpdater.spec

echo.
echo Compilando DriverUpdater.exe...
echo.

python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "DriverUpdater" ^
    --icon "icono.ico" ^
    main_gui.py

echo.
if exist "dist\DriverUpdater.exe" (
    echo Compilacion completada: dist\DriverUpdater.exe
) else (
    echo Ocurrio un error durante la compilacion.
)

pause
