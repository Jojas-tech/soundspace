@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3 was not found. Install it and enable Add Python to PATH.& pause & exit /b 1)
REM Keep the original origin so existing IndexedDB/localStorage remains available.
python launch_soundspace.py
if errorlevel 1 pause
endlocal
