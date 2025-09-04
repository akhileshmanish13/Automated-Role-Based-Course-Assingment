@echo off
:: Change directory to the location of this script to ensure paths are correct
cd /d "%~dp0"

title Role Based Training Assignment Application

echo ===================================================
echo.
echo      Role Based Training Assignment Application
echo.
echo ===================================================
echo.

set VENV_DIR=.venv
set PYTHON_CMD=python

rem Check if the Python Launcher for Windows is available and prefer it.
where py >nul 2>nul
if %errorlevel% == 0 (
    set PYTHON_CMD=py -3
)

echo --- Checking for virtual environment ---
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Virtual environment not found. Please create it by running:
    echo %PYTHON_CMD% -m venv %VENV_DIR%
    pause
    exit /b 1
)

echo --- Activating virtual environment ---
call "%VENV_DIR%\Scripts\activate.bat"

echo --- Installing/updating dependencies ---
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies from requirements.txt.
    pause
    exit /b 1
)

echo --- Starting application with Waitress on http://127.0.0.1:5001 ---
echo If the server starts successfully, you will see a "Serving on..." message.
echo If it fails, an error will be displayed below.
echo.
waitress-serve --host 0.0.0.0 --port 5001 app:app

echo.
echo ---------------------------------------------------
echo Application server has stopped.
echo Press any key to close this window.
pause >nul