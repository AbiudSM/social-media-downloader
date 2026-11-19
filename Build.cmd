@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" python -m venv --without-pip .venv
if errorlevel 1 goto :error
python -m pip --python ".venv\Scripts\python.exe" install --upgrade -r requirements.txt "pyinstaller>=6.16"
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean Downloader.spec
if errorlevel 1 goto :error
echo Built dist\Downloader\Downloader.exe
pause
exit /b 0
:error
echo The build failed. See the error above.
pause
exit /b 1
