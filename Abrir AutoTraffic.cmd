@echo off
cd /d "%~dp0"
python main.py app
if errorlevel 1 pause
