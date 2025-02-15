@echo off
echo Starting AiLinker...

:: Set paths
set LOG_FILE=app.log

:: Activate virtual environment
call venv\Scripts\activate

:: Load environment variables
call env_setup.bat

:: Ensure log file exists
if not exist %LOG_FILE% (
    echo. > %LOG_FILE%
)

:: Start the AiLinker Flask app in a new console window
start /B python app.py >> %LOG_FILE% 2>&1

:: Run log clearing script in the background
start /B auto_clear_log.bat

echo AiLinker service started successfully.
