@echo off
REM Starts the Bridge node, handling communication between components

echo Starting Bridge node...
python ..\node_bridge.py ..\configs\config\config_bridge.json

pause
