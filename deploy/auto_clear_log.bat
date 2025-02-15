@echo off
:: Set log file path
set LOG_FILE=app.log
set MAXSIZE=100000000  :: 100MB

:loop
:: Get the file size
for %%A in (%LOG_FILE%) do set SIZE=%%~zA

:: Check if file size exceeds limit
if %SIZE% GTR %MAXSIZE% (
    echo Clearing %LOG_FILE%, as it exceeded 100MB.
    echo. > %LOG_FILE%
)

:: Wait for 600 seconds before checking again
timeout /t 600 /nobreak >nul
goto loop
