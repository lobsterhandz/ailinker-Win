
@echo off
REM Starts the ASR (Automatic Speech Recognition) node

echo Starting ASR node...
python ..\node_asr.py ..\configs\config\config_asr.json

pause
