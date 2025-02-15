@echo off
echo Stopping AiLinker service...

:: Kill all Python processes (ensures AiLinker stops)
taskkill /F /IM python.exe /T

:: Kill the log clearing process (if running)
taskkill /F /IM cmd.exe /FI "WINDOWTITLE eq auto_clear_log.bat*"

echo AiLinker service stopped.
