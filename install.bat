@echo off
REM Install script for Windows - Sets up virtual environment, dependencies, and directories

echo Creating Python virtual environment 'ailinker'...
call conda create -y -n ailinker python=3.8

echo Activating virtual environment...
call conda activate ailinker

echo Installing required dependencies...
python -m pip install -r requirements.txt -i https://pypi.org/simple

echo Creating temporary directories...
if not exist ".\temp\asr" mkdir ".\temp\asr"
if not exist ".\deploy\temp\asr" mkdir ".\deploy\temp\asr"

echo Copying environment setup file...
copy /Y docs\example_env_setup.bat env_setup.bat

echo Installation completed successfully!
pause
