@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creation de l'environnement Python...
    py -3.12 -m venv .venv
    if errorlevel 1 goto error
)

".venv\Scripts\python.exe" -m pip --disable-pip-version-check install -q -r requirements.txt
if errorlevel 1 goto error

set "DB_ENGINE=sqlite"
set "DATABASE=instance/jobboard.db"
set "UPLOAD_FOLDER=instance/cvs"
set "PORT=8001"

".venv\Scripts\python.exe" -m scripts.start_local --open-browser
if errorlevel 1 goto error
exit /b 0

:error
echo.
echo Le demarrage a echoue. Le message ci-dessus indique la cause.
pause
exit /b 1
