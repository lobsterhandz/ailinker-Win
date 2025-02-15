@echo off
REM Starts the TTS (Text-to-Speech) node for speech synthesis

echo Starting TTS node...
python ..\node_tts.py ..\configs\config\config_tts.json

pause
