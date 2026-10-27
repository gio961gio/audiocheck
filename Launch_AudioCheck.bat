@echo off
title AudioCheck - Batch Audio Quality Control Engine
cd /d "%~dp0"
echo ========================================================
echo        AUDIOCHECK - BATCH AUDIO QUALITY CONTROL
echo ========================================================
echo Launching Dark Studio Web Dashboard in default browser...
python -m streamlit run app.py
pause
