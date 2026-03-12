@echo off
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py %1
) else (
    python main.py %1
)
if %errorlevel% neq 0 pause