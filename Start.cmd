@echo off
setlocal
cd /d "%~dp0"
if exist "dist\Downloader\Downloader.exe" (
    start "" "dist\Downloader\Downloader.exe"
    exit /b 0
)
if not exist ".venv\Scripts\python.exe" (
    python -m venv --without-pip .venv
    if errorlevel 1 goto :error
)
".venv\Scripts\python.exe" -c "import customtkinter, yt_dlp, yt_dlp_ejs, imageio_ffmpeg" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies. An internet connection is required...
    python -m pip --python ".venv\Scripts\python.exe" install -r requirements.txt
    if errorlevel 1 goto :error
)
start "" ".venv\Scripts\pythonw.exe" app.py
exit /b 0
:error
echo Could not set up Downloader. Install Python 3.10 or later with pip.
pause
exit /b 1
