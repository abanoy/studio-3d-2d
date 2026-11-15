@echo off
setlocal
set "HYBRID_PYTHON=C:\Program Files\Python313\python.exe"
set "HYBRID_GODOT=C:\a\tools\Godot\Godot_v4.6-stable_win64.exe"
set "HYBRID_FFMPEG=C:\Program Files\ffmpeg\bin\ffmpeg.exe"
set "HYBRID_SOURCEIO=%~dp0Dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
start "" "C:\Program Files\Python313\pythonw.exe" "%~dp0Studio\launch.pyw" "%~dp0Street.has"
