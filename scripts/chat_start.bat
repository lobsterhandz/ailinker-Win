@echo off
REM Starts the Chat node, handling LLM-based interactions

echo Starting Chat node...
python ..\node_chat.py ..\configs\config\config_chat.json

pause
