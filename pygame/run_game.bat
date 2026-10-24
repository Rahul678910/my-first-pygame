@echo off
title CHROMA-STRAND: HARMONIC VOID
echo Launching Chroma-Strand: Harmonic Void...
cd /d "%~dp0"
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" main.py
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    python main.py
)
pause
