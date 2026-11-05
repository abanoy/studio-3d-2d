@echo off
setlocal
cd /d "%~dp0"
start "" pythonw.exe "%~dp0launch.pyw"
endlocal
