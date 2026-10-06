@echo off
setlocal

cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"
set "DIST_DIR=dist\GPS Analyst"
set "WORK_DIR=build\pyinstaller-work"
set "SPEC_DIR=build\pyinstaller-spec"
set "ICON_PATH=%CD%\assets\gps-analyst.ico"
set "VERSION_FILE=%CD%\assets\windows-version-info.txt"

echo ===== GPS ANALYST WINDOWS BUILD =====
echo.

if not exist "%PYTHON%" (
    echo [ERROR] No existe .venv\Scripts\python.exe
    echo Crea el entorno virtual e instala requirements-build.txt.
    exit /b 1
)

echo ===== PYTHON =====
"%PYTHON%" --version
if errorlevel 1 exit /b 1

echo.
echo ===== PYINSTALLER =====
"%PYTHON%" -m PyInstaller --version
if errorlevel 1 (
    echo [ERROR] PyInstaller no esta instalado.
    echo Ejecuta:
    echo "%PYTHON%" -m pip install -r requirements-build.txt
    exit /b 1
)

echo.
echo ===== TESTS =====
set GPS_ANALYST_TEST_DATA=
"%PYTHON%" -m pytest -q
if errorlevel 1 (
    echo [ERROR] Los tests han fallado. Build cancelado.
    exit /b 1
)

echo.
echo ===== LIMPIAR BUILD ANTERIOR =====
if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%"
if exist "%SPEC_DIR%" rmdir /s /q "%SPEC_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"

echo.
echo ===== PYINSTALLER =====
"%PYTHON%" -m PyInstaller ^
 --noconfirm ^
 --clean ^
 --windowed ^
 --onedir ^
 --name "GPS Analyst" ^
 --icon "%ICON_PATH%" ^
 --add-data "%ICON_PATH%;assets" ^
 --version-file "%VERSION_FILE%" ^
 --distpath dist ^
 --workpath "%WORK_DIR%" ^
 --specpath "%SPEC_DIR%" ^
 gps_analyst\app.py

if errorlevel 1 (
    echo [ERROR] PyInstaller ha fallado.
    exit /b 1
)

echo.
echo ===== VERIFICAR EJECUTABLE =====
if not exist "%DIST_DIR%\GPS Analyst.exe" (
    echo [ERROR] No se ha generado GPS Analyst.exe
    exit /b 1
)

echo [OK] Ejecutable generado.

echo.
echo ===== AUDITORIA XLSX =====
set "FOUND_XLSX="

for /r "%DIST_DIR%" %%F in (*.xlsx) do (
    echo [ERROR] XLSX incluido: %%F
    set "FOUND_XLSX=1"
)

if defined FOUND_XLSX (
    exit /b 1
)

echo [OK] Ningun XLSX incluido.

echo.
echo ===== AUDITORIA PRIVATE =====
if exist "%DIST_DIR%\data\private" (
    echo [ERROR] Se ha incluido data\private.
    exit /b 1
)

echo [OK] No existe data\private.

echo.
echo ===== RESULTADO =====
echo [OK] BUILD COMPLETADO
echo.
echo Ejecutable:
echo "%CD%\%DIST_DIR%\GPS Analyst.exe"
echo.
echo IMPORTANTE:
echo Distribuir la carpeta completa "dist\GPS Analyst".
echo No copiar solamente GPS Analyst.exe.

endlocal
exit /b 0