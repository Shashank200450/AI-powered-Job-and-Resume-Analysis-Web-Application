@echo off
title JOBSINLINE Server
echo ========================================================
echo               Starting JOBSINLINE Server
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    set "PYTHON_EXE=C:\Users\M.shashank\AppData\Local\Programs\Python\Python311\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Using Python: %PYTHON_EXE%
%PYTHON_EXE% --version

echo.
echo Starting Flask web application on http://127.0.0.1:5000 ...
echo.
%PYTHON_EXE% app.py
pause
