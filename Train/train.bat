@echo off
cd /d "%~dp0"

echo ============================================
echo   NTE Fishing Bot - AI Training
echo ============================================
echo.
echo Select your GPU type:
echo 1. NVIDIA (CUDA)
echo 2. AMD (DirectML)
echo.

choice /C 12 /M "Enter your choice: "
if errorlevel 2 goto SetupDML
if errorlevel 1 goto SetupCUDA

:SetupCUDA
set TRAIN_DEVICE=cuda
set VENV_DIR=..\venv
goto StartEnv

:SetupDML
set TRAIN_DEVICE=dml
set VENV_DIR=..\venv_dml
goto StartEnv

:StartEnv
echo.
echo ============================================
echo Using Environment: %VENV_DIR%
echo ============================================

:: Activate or create virtual environment
if exist "%VENV_DIR%\Scripts\activate.bat" goto ActivateEnv

echo.
if "%TRAIN_DEVICE%"=="dml" (
    echo [AMD SETUP] DirectML training requires Python 3.10 specifically.
    echo Searching for Python 3.10...
    py -3.10 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [!] Python 3.10 not found. 
        echo [!] Downloading portable Python 3.10 specifically for AMD training...
        if not exist "%VENV_DIR%" mkdir "%VENV_DIR%"
        
        powershell -Command "Write-Host '  >> Downloading...'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip' -OutFile '%VENV_DIR%\python.zip'"
        powershell -Command "Write-Host '  >> Extracting...'; Expand-Archive -Force -Path '%VENV_DIR%\python.zip' -DestinationPath '%VENV_DIR%'"
        del "%VENV_DIR%\python.zip"
        
        echo [!] Configuring portable environment...
        :: Enable site-packages by uncommenting 'import site' in the ._pth file
        powershell -Command "(Get-Content '%VENV_DIR%\python310._pth') -replace '#import site', 'import site' | Set-Content '%VENV_DIR%\python310._pth'"
        
        echo [!] Installing pip...
        powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%VENV_DIR%\get-pip.py'"
        "%VENV_DIR%\python.exe" "%VENV_DIR%\get-pip.py" --quiet
        del "%VENV_DIR%\get-pip.py"
        
        echo.
        echo [SUCCESS] Portable Python 3.10 is ready in %VENV_DIR%
    ) else (
        echo Python 3.10 found. Creating virtual environment...
        py -3.10 -m venv %VENV_DIR%
    )
) else (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

:: Activation logic for both venv and portable python
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    :: For portable python, we just set the path
    set PATH=%~dp0%VENV_DIR%;%~dp0%VENV_DIR%\Scripts;%PATH%
)

if "%TRAIN_DEVICE%"=="dml" goto InstallDML

:InstallCUDA
echo Installing PyTorch for CUDA (NVIDIA)...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130 -q
goto InstallCommon

:InstallDML
echo Installing torch-directml (AMD GPU)...
pip install torch-directml -q
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install torch-directml!
    echo Training requires an AMD GPU and Python 3.10.
    echo.
    pause
    exit /b 1
)
pip install torchvision -q 2>nul

:InstallCommon
echo Installing ONNX dependencies...
pip install onnx onnxruntime onnxscript -q

echo Installing base requirements...
pip install -r requirements_train.txt -q

echo.
echo Starting training...
echo.
python train.py

echo.
echo Done! Run run.bat to use the AI bot.
pause
