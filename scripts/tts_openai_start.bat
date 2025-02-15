
@echo off
REM Starts the OpenAI-based Text-to-Speech (TTS) node

echo Starting OpenAI TTS node...
python ..\node_tts_openai.py ..\configs\config\config_tts.json

pause
