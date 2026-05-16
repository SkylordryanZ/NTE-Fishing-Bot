@echo off

:: Request Administrator privileges for Game Input/Hooks
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting Administrator privileges for game input...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Python is not installed or not in your PATH!
        echo Please download and install Python from: https://www.python.org/
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
)

:: Check if model exists
if not exist "model\state_classifier.onnx" (
    echo.
    echo [ERROR] model\state_classifier.onnx not found!
    echo Run Train\train.bat first to train the AI model.
    echo.
    pause
    exit /b 1
)

:: Activate or create virtual environment
if exist "venv\Scripts\activate.bat" goto ActivateEnv

echo.
echo Virtual environment not found. Creating it now...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)

:ActivateEnv
call venv\Scripts\activate.bat

echo Installing/Updating bot dependencies...
pip install -r requirements.txt -q

echo.
echo ============================================
echo   NTE Fishing Bot (AI Vision)
echo   Using: model\state_classifier.onnx
echo ============================================
echo.
python src/bot.py

call venv\Scripts\deactivate.bat
echo.
echo Bot stopped.
pause
