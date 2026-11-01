@echo off
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Installation completed. Run MO_UNG_DUNG.bat
pause
exit /b 0
:failed
echo Installation failed. Please send a screenshot of this window.
pause
exit /b 1
