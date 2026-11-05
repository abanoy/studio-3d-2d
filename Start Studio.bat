@echo off
setlocal
set "project=%~f1"
cd /d "%~dp0"
if defined project (
  start "" pythonw.exe "%~dp0launch.pyw" "%project%"
) else (
  start "" pythonw.exe "%~dp0launch.pyw"
)
endlocal
